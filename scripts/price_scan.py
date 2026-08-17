#!/usr/bin/env python3
"""Scan a shortlist of product URLs for current price, stock and delivery cost.

Run inside a purchase-research repo. Reads a watchlist of candidate products
(`price-watchlist.yaml` in the repo), prices each one against the marketplaces
and address profile in your private config, and writes a timestamped scan plus
an appended history row so price movement accumulates over time.

    ./price_scan.py                          # scan ./price-watchlist.yaml
    ./price_scan.py --address storrs         # price for a specific destination
    ./price_scan.py --marketplace newegg     # only one shop
    ./price_scan.py --check-egress           # preflight only, scan nothing
    ./price_scan.py --no-vpn                 # never touch the VPN

What it will not do: invent a number. Any candidate it cannot fetch or parse
comes back with a status (`blocked`, `not_found`, `no_price`, `error`) and a
null price. Bot protection on the big marketplaces means `blocked` is a normal
outcome, not a bug — those rows are meant to be finished off in a real browser,
and the accompanying skill explains that handoff.

Exit codes: 0 every candidate priced; 1 some or all unresolved (the report is
still written — this means "needs a browser pass", not "crashed"); 2 config or
watchlist missing; 3 PyYAML missing.

Config lives outside this repo. See `examples/config/` for the shape and
`/procurement-tools:shop-setup` to generate it.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import html
import io
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request
import zlib
from dataclasses import asdict, dataclass, field
from typing import Any

try:
    import yaml
except ImportError:
    print("price_scan.py needs PyYAML (pip install pyyaml, or: uv pip install pyyaml)", file=sys.stderr)
    raise SystemExit(3)

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from vpn_control import VPNControl, observe_egress, provider_from_config  # noqa: E402

# ---------------------------------------------------------------------------
# Config location — private by design
# ---------------------------------------------------------------------------

MARKETPLACES_FILE = "marketplaces.yaml"
ADDRESSES_FILE = "addresses.yaml"


def plugin_data_dir() -> pathlib.Path:
    """Same resolution order the plugin's other commands use.

    Deliberately outside the plugin repo: the plugin is public, the shipping
    addresses and account details are not.
    """
    if os.environ.get("CLAUDE_USER_DATA"):
        base = pathlib.Path(os.environ["CLAUDE_USER_DATA"]) / "procurement-tools"
    elif os.environ.get("XDG_DATA_HOME"):
        base = pathlib.Path(os.environ["XDG_DATA_HOME"]) / "claude-plugins" / "procurement-tools"
    else:
        base = pathlib.Path.home() / ".local" / "share" / "claude-plugins" / "procurement-tools"
    return base


def _load_yaml(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_marketplaces() -> dict[str, Any]:
    return _load_yaml(plugin_data_dir() / MARKETPLACES_FILE)


def load_addresses() -> dict[str, Any]:
    return _load_yaml(plugin_data_dir() / ADDRESSES_FILE)


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

BROWSERISH_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/128.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "close",
    "Upgrade-Insecure-Requests": "1",
}

# Pages that load but are really a challenge wall. Cheap to detect, and much
# better than parsing a price of 0 off a captcha page.
BOT_WALL_MARKERS = (
    "captcha",
    "are you a human",
    "enter the characters you see",
    "automated access",
    "unusual traffic",
    "access denied",
    "request blocked",
    "px-captcha",
    "cf-browser-verification",
    "checking your browser",
)


def fetch(url: str, timeout: float = 25.0) -> tuple[str | None, str, int | None]:
    """Return (body, status, http_code). Never raises for network reasons."""
    req = urllib.request.Request(url, headers=BROWSERISH_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            encoding = (resp.headers.get("Content-Encoding") or "").lower()
            if encoding == "gzip":
                raw = gzip.decompress(raw)
            elif encoding == "deflate":
                raw = zlib.decompress(raw, -zlib.MAX_WBITS)
            body = raw.decode(resp.headers.get_content_charset() or "utf-8", "replace")
            code = resp.status
    except urllib.error.HTTPError as exc:
        # 403/429 from these sites is nearly always bot protection, not a dead
        # product page — worth distinguishing so the browser fallback kicks in.
        status = "blocked" if exc.code in (401, 403, 429, 503) else (
            "not_found" if exc.code == 404 else "error")
        return None, f"{status} (HTTP {exc.code})", exc.code
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, f"error ({exc})", None

    lowered = body[:200_000].lower()
    if any(m in lowered for m in BOT_WALL_MARKERS):
        return body, "blocked (challenge page)", code
    return body, "ok", code


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

JSONLD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)

META_PRICE_RES = [
    re.compile(r'<meta[^>]+(?:property|name)=["\'](?:og:price:amount|product:price:amount)["\'][^>]+content=["\']([\d.,]+)["\']', re.I),
    re.compile(r'<meta[^>]+itemprop=["\']price["\'][^>]+content=["\']([\d.,]+)["\']', re.I),
    re.compile(r'itemprop=["\']price["\'][^>]*content=["\']([\d.,]+)["\']', re.I),
]

# Site-specific, ordered most to least trustworthy. Kept small on purpose:
# these are the shapes that survive minor redesigns.
SITE_PRICE_RES = {
    "amazon": [
        re.compile(r'"priceAmount"\s*:\s*([\d.]+)'),
        re.compile(r'id=["\']corePrice_feature_div["\'].*?<span class=["\']a-offscreen["\']>\s*[^\d]*([\d.,]+)', re.S),
        re.compile(r'<span class=["\']a-offscreen["\']>\s*[^\d]*([\d.,]+)\s*</span>'),
    ],
    "newegg": [
        re.compile(r'"finalPrice"\s*:\s*([\d.]+)'),
        re.compile(r'"price"\s*:\s*"?([\d.,]+)"?\s*,\s*"priceCurrency"', re.I),
        re.compile(r'class=["\']price-current["\'][^>]*>[^\d]*([\d,]+)\s*<sup>(\d{2})</sup>', re.S),
    ],
}

AVAILABILITY_RES = [
    (re.compile(r'"availability"\s*:\s*"[^"]*?(InStock|OutOfStock|PreOrder|BackOrder)', re.I), None),
    (re.compile(r'\b(out of stock|sold out|currently unavailable)\b', re.I), "out of stock"),
    (re.compile(r'\b(in stock|add to cart|add to basket)\b', re.I), "in stock"),
]

# schema.org spellings and page text both end up in the same column of the
# report, so they have to mean the same thing when they say the same thing.
AVAILABILITY_NORMAL = {
    "instock": "in stock",
    "outofstock": "out of stock",
    "preorder": "pre-order",
    "backorder": "backorder",
    "limitedavailability": "limited",
    "soldout": "out of stock",
    "currentlyunavailable": "out of stock",
}


def normalise_availability(value: str | None) -> str | None:
    if not value:
        return None
    key = re.sub(r'[^a-z]', '', value.lower())
    return AVAILABILITY_NORMAL.get(key, value.strip().lower())

SHIPPING_RES = [
    re.compile(r'\b(FREE (?:Prime )?(?:Returns? )?(?:delivery|shipping))\b', re.I),
    re.compile(r'\b(free shipping)\b', re.I),
    re.compile(r'(?:shipping|delivery)[^.<>]{0,40}?[$€£₪]\s?([\d.,]+)', re.I),
]


def _to_float(text: str) -> float | None:
    text = text.strip().replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def extract_from_jsonld(body: str) -> tuple[float | None, str | None, str | None]:
    """Structured data first — it's the only source the sites actually promise."""
    for match in JSONLD_RE.finditer(body):
        raw = match.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for node in _walk_jsonld(data):
            if not isinstance(node, dict):
                continue
            types = node.get("@type")
            types = [types] if isinstance(types, str) else (types or [])
            if not any(str(t).lower() == "product" for t in types):
                continue
            offers = node.get("offers")
            offers = offers[0] if isinstance(offers, list) and offers else offers
            if not isinstance(offers, dict):
                continue
            price = offers.get("price") or offers.get("lowPrice")
            currency = offers.get("priceCurrency")
            availability = offers.get("availability")
            if price is not None:
                value = _to_float(str(price))
                if value:
                    avail = normalise_availability(
                        str(availability).rsplit("/", 1)[-1]) if availability else None
                    return value, (str(currency).upper() if currency else None), avail
    return None, None, None


def _walk_jsonld(node: Any):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk_jsonld(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_jsonld(item)


def extract_price(body: str, marketplace_id: str) -> tuple[float | None, str | None, str | None, str]:
    """Return (price, currency, availability, how_it_was_found)."""
    price, currency, avail = extract_from_jsonld(body)
    if price:
        return price, currency, avail, "json-ld"

    for key, patterns in SITE_PRICE_RES.items():
        if key not in marketplace_id.lower():
            continue
        for pattern in patterns:
            m = pattern.search(body)
            if not m:
                continue
            if len(m.groups()) == 2:  # split dollars/cents markup
                value = _to_float(f"{m.group(1)}.{m.group(2)}")
            else:
                value = _to_float(m.group(1))
            if value:
                return value, None, extract_availability(body), f"site-pattern:{key}"

    for pattern in META_PRICE_RES:
        m = pattern.search(body)
        if m:
            value = _to_float(m.group(1))
            if value:
                return value, None, extract_availability(body), "meta-tag"

    return None, None, extract_availability(body), "none"


def extract_availability(body: str) -> str | None:
    for pattern, label in AVAILABILITY_RES:
        m = pattern.search(body)
        if m:
            return normalise_availability(label or m.group(1))
    return None


def extract_shipping(body: str) -> tuple[float | None, str | None]:
    """Best-effort only. Real shipping cost is usually behind the cart."""
    for pattern in SHIPPING_RES:
        m = pattern.search(body)
        if not m:
            continue
        token = m.group(1)
        if token and re.match(r'^[\d.,]+$', token):
            return _to_float(token), f"quoted {token}"
        return 0.0, html.unescape(token)
    return None, None


# ---------------------------------------------------------------------------
# Landed cost
# ---------------------------------------------------------------------------


def landed_cost(price: float | None, shipping: float | None, marketplace: dict, address: dict
                ) -> tuple[float | None, str]:
    """Item + shipping + tax, per the destination's rule.

    Returns (total, explanation). Anything uncertain stays out of the number and
    goes into the explanation instead.
    """
    if price is None:
        return None, "no price"

    ship = shipping if shipping is not None else 0.0
    ship_note = "shipping unknown, treated as 0" if shipping is None else f"shipping {ship:.2f}"

    rule = (marketplace.get("tax") or "none").lower()
    tax_cfg = (address.get("tax") or {})

    if rule == "destination_sales_tax":
        pct = tax_cfg.get("sales_tax_pct")
        if pct is None:
            return price + ship, f"{ship_note}; no sales-tax rate configured, tax excluded"
        tax = (price + ship) * float(pct) / 100.0
        confirmed = "" if tax_cfg.get("confirmed") else " (rate unconfirmed)"
        return price + ship + tax, f"{ship_note}; +{pct}% sales tax{confirmed}"

    if rule == "vat_added":
        pct = tax_cfg.get("vat_pct")
        if pct is None:
            return price + ship, f"{ship_note}; no VAT rate configured, VAT excluded"
        tax = (price + ship) * float(pct) / 100.0
        return price + ship + tax, f"{ship_note}; +{pct}% VAT"

    if rule == "vat_inclusive":
        return price + ship, f"{ship_note}; VAT already in price"

    return price + ship, f"{ship_note}; no tax rule"


# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------


@dataclass
class Row:
    name: str
    marketplace: str
    url: str
    status: str
    price: float | None = None
    currency: str | None = None
    availability: str | None = None
    shipping_cost: float | None = None
    shipping_note: str | None = None
    landed: float | None = None
    landed_note: str = ""
    found_via: str = ""
    egress_country: str | None = None
    fetched_at: str = ""
    note: str = ""


def scan(watchlist: dict, marketplaces: dict, addresses: dict, address_id: str,
         only_marketplace: str | None, vpn: VPNControl, timeout: float,
         verbose: bool) -> tuple[list[Row], list[str]]:
    log: list[str] = []
    shops = {m["id"]: m for m in (marketplaces.get("marketplaces") or [])}
    addr_map = {a["id"]: a for a in (addresses.get("addresses") or [])}
    address = addr_map.get(address_id) or {}
    if not address:
        log.append(f"! address profile '{address_id}' not found — tax and delivery rules skipped")

    candidates = watchlist.get("candidates") or []
    if only_marketplace:
        candidates = [c for c in candidates if c.get("marketplace") == only_marketplace]

    # Group by required geo so the VPN flips once per country, not once per
    # candidate. With a kill-switch enabled every flip drops connectivity, so
    # interleaving would be both slow and fragile.
    by_geo: dict[str | None, list[dict]] = {}
    for cand in candidates:
        shop = shops.get(cand.get("marketplace"), {})
        if shop and not shop.get("in_scope", True):
            log.append(f"- skipped {cand.get('name')}: marketplace '{cand.get('marketplace')}' is out of scope")
            continue
        by_geo.setdefault(shop.get("requires_geo"), []).append(cand)

    rows: list[Row] = []
    for geo, group in sorted(by_geo.items(), key=lambda kv: (kv[0] or "")):
        egress_country = None
        if geo:
            result = vpn.ensure_geo(geo, timeout=timeout)
            egress_country = result.egress.country
            log.append(f"{'✓' if result.ok else '✗'} egress for {geo}: {result.detail}")
            if not result.ok:
                for cand in group:
                    rows.append(Row(
                        name=cand.get("name", "?"), marketplace=cand.get("marketplace", "?"),
                        url=cand.get("url", ""), status="skipped_wrong_geo",
                        egress_country=egress_country, fetched_at=_now(),
                        note=f"needs {geo} exit; {result.detail}"))
                continue
        else:
            egress_country = observe_egress(timeout=timeout).country

        for cand in group:
            rows.append(_scan_one(cand, shops, address, egress_country, timeout, verbose, log))

    return rows, log


def _scan_one(cand: dict, shops: dict, address: dict, egress_country: str | None,
              timeout: float, verbose: bool, log: list[str]) -> Row:
    name = cand.get("name", "?")
    market_id = cand.get("marketplace", "?")
    url = cand.get("url", "")
    shop = shops.get(market_id, {})

    if not url:
        return Row(name=name, marketplace=market_id, url="", status="error",
                   egress_country=egress_country, fetched_at=_now(), note="no url in watchlist")

    body, status, _ = fetch(url, timeout=timeout)
    row = Row(name=name, marketplace=market_id, url=url, status=status.split(" ")[0],
              egress_country=egress_country, fetched_at=_now(),
              note="" if status == "ok" else status)

    if body is None or not status.startswith("ok"):
        if row.status == "blocked":
            row.note = f"{status} — re-check in a browser session"
        if verbose:
            log.append(f"  {name}: {status}")
        return row

    price, currency, avail, how = extract_price(body, market_id)
    ship, ship_note = extract_shipping(body)

    row.price = price
    row.currency = currency or shop.get("currency")
    row.availability = avail
    row.shipping_cost = ship
    row.shipping_note = ship_note
    row.found_via = how

    if price is None:
        row.status = "no_price"
        row.note = "page fetched but no price found — layout may have changed, or price is behind the cart"
    else:
        row.landed, row.landed_note = landed_cost(price, ship, shop, address)

    if verbose:
        log.append(f"  {name}: {row.status} price={price} via {how}")
    return row


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_outputs(rows: list[Row], out_dir: pathlib.Path, watchlist: dict, address_id: str,
                  log: list[str]) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d-%H%M")

    json_path = out_dir / f"{stamp}-scan.json"
    payload = {
        "item": watchlist.get("item"),
        "address_profile": address_id,
        "scanned_at": _now(),
        "log": log,
        "rows": [asdict(r) for r in rows],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md_path = out_dir / f"{stamp}-scan.md"
    md_path.write_text(render_markdown(rows, watchlist, address_id, log), encoding="utf-8")

    # One row per candidate per run, appended forever — this is what makes
    # "has it dropped since last week?" answerable.
    history = out_dir / "price-history.csv"
    exists = history.exists()
    with history.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if not exists:
            writer.writerow(["scanned_at", "item", "name", "marketplace", "status",
                             "price", "currency", "shipping_cost", "landed", "address_profile", "url"])
        for r in rows:
            writer.writerow([r.fetched_at, watchlist.get("item", ""), r.name, r.marketplace,
                             r.status, r.price if r.price is not None else "",
                             r.currency or "", r.shipping_cost if r.shipping_cost is not None else "",
                             r.landed if r.landed is not None else "", address_id, r.url])

    return json_path, md_path, history


def render_markdown(rows: list[Row], watchlist: dict, address_id: str, log: list[str]) -> str:
    out = io.StringIO()
    out.write(f"# Price scan — {watchlist.get('item', 'shortlist')}\n\n")
    out.write(f"- Scanned: {_now()}\n- Delivering to: `{address_id}`\n\n")

    out.write("| Candidate | Shop | Status | Price | Shipping | Landed | Stock |\n")
    out.write("|---|---|---|---|---|---|---|\n")
    for r in sorted(rows, key=lambda r: (r.landed is None, r.landed or 0)):
        price = f"{r.currency or ''} {r.price:,.2f}".strip() if r.price is not None else "—"
        ship = (r.shipping_note or (f"{r.shipping_cost:,.2f}" if r.shipping_cost is not None else "—"))
        landed = f"{r.landed:,.2f}" if r.landed is not None else "—"
        out.write(f"| {r.name} | {r.marketplace} | {r.status} | {price} | {ship} | "
                  f"{landed} | {r.availability or '—'} |\n")

    unresolved = [r for r in rows if r.price is None]
    if unresolved:
        out.write("\n## Needs a browser\n\n")
        out.write("Scripted fetch could not price these. Open each in a real session "
                  "(same VPN exit) and fill the row in by hand:\n\n")
        for r in unresolved:
            out.write(f"- **{r.name}** ({r.marketplace}) — {r.status}: {r.note}\n  {r.url}\n")

    priced = [r for r in rows if r.landed is not None]
    if priced:
        out.write("\n## Landed cost notes\n\n")
        for r in priced:
            out.write(f"- **{r.name}**: {r.landed_note} (price found via {r.found_via})\n")

    if log:
        out.write("\n## Run log\n\n")
        for line in log:
            out.write(f"- {line}\n")

    out.write("\n> Figures are what the page showed at scan time from the exit country listed. "
              "Anything marked unconfirmed, or any row above without a price, is not a quote.\n")
    return out.getvalue()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--watchlist", default="price-watchlist.yaml")
    ap.add_argument("--out-dir", default="data/price-scans")
    ap.add_argument("--address", default=None, help="address profile id (default: config default_address)")
    ap.add_argument("--marketplace", default=None, help="restrict to one marketplace id")
    ap.add_argument("--check-egress", action="store_true", help="report egress and exit")
    ap.add_argument("--no-vpn", action="store_true", help="never invoke the VPN client")
    ap.add_argument("--dry-run", action="store_true", help="print VPN actions instead of running them")
    ap.add_argument("--timeout", type=float, default=25.0)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    marketplaces = load_marketplaces()
    addresses = load_addresses()

    if not marketplaces:
        print(f"No config at {plugin_data_dir() / MARKETPLACES_FILE}\n"
              f"Run /procurement-tools:shop-setup, or copy examples/config/*.example.yaml there.",
              file=sys.stderr)
        return 2

    vpn_cfg = marketplaces.get("vpn") or {}
    provider = provider_from_config(vpn_cfg) if not args.no_vpn else None
    vpn = VPNControl(provider,
                     auto_switch=bool(vpn_cfg.get("auto_switch", False)) and not args.no_vpn,
                     dry_run=args.dry_run)

    if args.check_egress:
        egress = observe_egress(timeout=args.timeout)
        print(f"observed egress : {egress.describe()}")
        print(f"vpn provider    : {provider.name if provider else 'none'}"
              f"{'' if not provider else (' (found)' if vpn.available else ' (NOT on PATH)')}")
        if provider and vpn.available:
            # Print the whole block: clients pad their status with version nags
            # and account chatter, and picking one line guesses wrong.
            status_lines = [l for l in vpn.client_status().splitlines() if l.strip()]
            print(f"client says     : {status_lines[0] if status_lines else '?'}")
            for line in status_lines[1:]:
                print(f"                  {line}")
        needed = sorted({m.get("requires_geo") for m in (marketplaces.get("marketplaces") or [])
                         if m.get("in_scope", True) and m.get("requires_geo")})
        print(f"in-scope shops need exits: {', '.join(needed) or 'none'}")
        return 0 if egress.ok else 1

    watchlist_path = pathlib.Path(args.watchlist)
    if not watchlist_path.exists():
        print(f"No watchlist at {watchlist_path}. Create one (see examples/price-watchlist.example.yaml) "
              f"or pass --watchlist.", file=sys.stderr)
        return 2
    watchlist = _load_yaml(watchlist_path)

    address_id = args.address or watchlist.get("address") or marketplaces.get("default_address")
    if not address_id:
        print("No address profile: pass --address, set `address:` in the watchlist, or "
              "`default_address:` in marketplaces.yaml.", file=sys.stderr)
        return 2

    rows, log = scan(watchlist, marketplaces, addresses, address_id, args.marketplace,
                     vpn, args.timeout, verbose=not args.quiet)

    if not rows:
        print("Nothing to scan — watchlist has no candidates matching the filters.", file=sys.stderr)
        return 1

    json_path, md_path, history = write_outputs(rows, pathlib.Path(args.out_dir), watchlist,
                                                address_id, log)

    if not args.quiet:
        for line in log:
            print(line)
        print()
        priced = sum(1 for r in rows if r.price is not None)
        print(f"{priced}/{len(rows)} candidates priced.")
        for r in sorted(rows, key=lambda r: (r.landed is None, r.landed or 0)):
            landed = f"{r.landed:,.2f}" if r.landed is not None else "—"
            print(f"  {r.status:<18} {landed:>12}  {r.name} ({r.marketplace})")
        print(f"\nwrote {md_path}\n      {json_path}\n      {history}")

    # 0 = every candidate priced, 1 = some or all unresolved (blocked, wrong
    # geo, no price). The report is written either way; 1 means it still needs
    # a browser pass, which is a normal outcome rather than a crash.
    return 0 if all(r.price is not None for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
