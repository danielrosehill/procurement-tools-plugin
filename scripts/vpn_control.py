#!/usr/bin/env python3
"""VPN egress control for the price scanner.

Marketplace prices, shipping quotes and stock are geo-dependent. A scan run from
the wrong exit country returns numbers that look fine and are wrong, so the
scanner needs to (a) know where it is currently egressing from and (b) be able
to move.

**This is the fork point.** Windscribe is the reference implementation because
that's what the author runs. Every other client is reached the same way: declare
its command lines in `marketplaces.yaml` under `vpn.commands`. No code change is
needed for any VPN whose CLI can connect by country string — see BUILTIN below
for four already written out, and `provider: custom` for anything else.

Two-sided verification is the whole point of this module. A VPN CLI reporting
"connected" is a claim about the tunnel, not about routing: the client can be up
before routes settle, split-tunnelling can exclude the very process doing the
fetch, and a location label like "Montreal - Expo 67" doesn't name a country at
all. So the CLI is used to *set* the exit and an independent IP lookup is used
to *confirm* it. Neither is trusted alone.

Usable as a library (the scanner imports it) or standalone:

    ./vpn_control.py where            # current exit country, via IP lookup
    ./vpn_control.py status           # what the VPN client claims
    ./vpn_control.py ensure US        # switch to US only if not already there
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Where am I actually egressing from?
# ---------------------------------------------------------------------------

# Independent of the VPN client. Each returns a 2-letter country code.
# Several, because any one of them can be down, rate-limited, or blocked by the
# exit node itself.
GEO_ENDPOINTS: list[tuple[str, Callable[[dict[str, Any]], str | None]]] = [
    ("https://ipinfo.io/json", lambda d: d.get("country")),
    ("https://ifconfig.co/json", lambda d: d.get("country_iso")),
    ("https://api.country.is/", lambda d: d.get("country")),
]

USER_AGENT = "procurement-tools-price-scan/1.0 (+https://github.com/danielrosehill/procurement-tools-plugin)"


@dataclass
class Egress:
    """Observed exit, as seen from outside this machine."""

    country: str | None
    ip: str | None
    city: str | None = None
    source: str | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.country is not None

    def describe(self) -> str:
        if not self.ok:
            return f"egress unknown ({self.error or 'no endpoint answered'})"
        where = ", ".join(p for p in (self.city, self.country) if p)
        return f"{where} [{self.ip}] via {self.source}"


def observe_egress(timeout: float = 8.0) -> Egress:
    """Ask the internet where this machine appears to be.

    Sends a request to a public IP-geolocation endpoint, which necessarily
    reveals this machine's exit IP to that endpoint. Nothing else is sent.
    """
    last_error = None
    for url, extract in GEO_ENDPOINTS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8", "replace"))
            country = extract(data)
            if country:
                return Egress(
                    country=country.upper(),
                    ip=data.get("ip"),
                    city=data.get("city"),
                    source=urllib.parse.urlsplit(url).netloc,
                )
            last_error = f"{url} returned no country field"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            last_error = f"{url}: {exc}"
    return Egress(country=None, ip=None, error=last_error)


# ---------------------------------------------------------------------------
# VPN providers
# ---------------------------------------------------------------------------


@dataclass
class Provider:
    """A VPN client, described entirely as command lines.

    `{location}` in a connect command is substituted with the location string
    for the wanted country (see `Provider.locations`, overridable in config).
    """

    name: str
    binary: str
    status: list[str]
    connect: list[str]
    disconnect: list[str] = field(default_factory=list)
    # ISO country code -> whatever string this client's `connect` expects.
    locations: dict[str, str] = field(default_factory=dict)
    # Lines matching this are the client's own logging, not output for humans.
    noise: str | None = None
    # Seconds to allow for routes to settle after connecting.
    settle_seconds: float = 8.0


BUILTIN: dict[str, Provider] = {
    # Reference implementation. v2.19.7 interleaves JSON log lines with the
    # human-readable block on stdout, hence `noise`. `status` reports a city
    # label ("Montreal - Expo 67"), never a country code — which is exactly why
    # country is resolved by IP lookup instead.
    "windscribe": Provider(
        name="windscribe",
        binary="windscribe-cli",
        status=["windscribe-cli", "status"],
        connect=["windscribe-cli", "connect", "{location}"],
        disconnect=["windscribe-cli", "disconnect"],
        locations={"US": "US", "IL": "IL", "GB": "GB", "DE": "DE", "CA": "CA"},
        noise=r'^\s*\{"tm"',
        settle_seconds=8.0,
    ),
    "mullvad": Provider(
        name="mullvad",
        binary="mullvad",
        status=["mullvad", "status"],
        connect=["mullvad", "relay", "set", "location", "{location}"],
        disconnect=["mullvad", "disconnect"],
        locations={"US": "us", "IL": "il", "GB": "gb", "DE": "de", "CA": "ca"},
        settle_seconds=6.0,
    ),
    "nordvpn": Provider(
        name="nordvpn",
        binary="nordvpn",
        status=["nordvpn", "status"],
        connect=["nordvpn", "connect", "{location}"],
        disconnect=["nordvpn", "disconnect"],
        locations={"US": "United_States", "IL": "Israel", "GB": "United_Kingdom", "DE": "Germany"},
        settle_seconds=6.0,
    ),
    "protonvpn": Provider(
        name="protonvpn",
        binary="protonvpn-cli",
        status=["protonvpn-cli", "status"],
        connect=["protonvpn-cli", "connect", "--cc", "{location}"],
        disconnect=["protonvpn-cli", "disconnect"],
        locations={"US": "US", "IL": "IL", "GB": "UK", "DE": "DE"},
        settle_seconds=8.0,
    ),
}


def provider_from_config(cfg: dict[str, Any] | None) -> Provider | None:
    """Build a Provider from the `vpn:` block of marketplaces.yaml.

    Start from a built-in if one is named, then apply any overrides. A fork
    targeting a different client needs only to supply `commands` — no code.
    """
    if not cfg or cfg.get("provider") in (None, "none", "manual"):
        return None

    name = str(cfg["provider"])
    base = BUILTIN.get(name)
    if base is None:
        base = Provider(name=name, binary="", status=[], connect=[])

    commands = cfg.get("commands") or {}
    status = commands.get("status", base.status)
    connect = commands.get("connect", base.connect)
    disconnect = commands.get("disconnect", base.disconnect)

    if not status or not connect:
        raise ValueError(
            f"vpn.provider '{name}' is not built in, so vpn.commands must define at least "
            f"'status' and 'connect' (each a list of argv items, with {{location}} in connect)."
        )

    return Provider(
        name=name,
        binary=(commands.get("binary") or base.binary or status[0]),
        status=list(status),
        connect=list(connect),
        disconnect=list(disconnect or []),
        locations={**base.locations, **(cfg.get("locations") or {})},
        noise=cfg.get("noise", base.noise),
        settle_seconds=float(cfg.get("settle_seconds", base.settle_seconds)),
    )


@dataclass
class SwitchResult:
    """What `ensure_geo` did and what the world looked like afterwards."""

    wanted: str
    egress: Egress
    switched: bool
    action: str
    ok: bool
    detail: str = ""


class VPNControl:
    def __init__(self, provider: Provider | None, auto_switch: bool = False, dry_run: bool = False):
        self.provider = provider
        self.auto_switch = auto_switch
        self.dry_run = dry_run

    @property
    def available(self) -> bool:
        return self.provider is not None and shutil.which(self.provider.binary) is not None

    def _run(self, argv: list[str], timeout: float = 90.0) -> tuple[int, str]:
        if self.dry_run:
            return 0, f"[dry-run] would run: {' '.join(argv)}"
        try:
            proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            return 1, str(exc)
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, self._strip_noise(out)

    def _strip_noise(self, text: str) -> str:
        if not self.provider or not self.provider.noise:
            return text.strip()
        pattern = re.compile(self.provider.noise)
        return "\n".join(l for l in text.splitlines() if not pattern.search(l)).strip()

    def client_status(self) -> str:
        """What the VPN client claims. A claim, not a verified fact."""
        if not self.available:
            return "no VPN client available"
        _, out = self._run(self.provider.status, timeout=30.0)
        return out or "(no output)"

    def ensure_geo(self, wanted: str | None, timeout: float = 8.0) -> SwitchResult:
        """Make the exit country `wanted`, or explain why it isn't.

        Never reports success on the client's say-so — the exit is re-observed
        by IP lookup after any switch, and that observation is what decides.
        """
        egress = observe_egress(timeout=timeout)

        if not wanted:
            return SwitchResult(wanted="", egress=egress, switched=False, action="none", ok=True,
                                detail="no geo requirement")

        wanted = wanted.upper()

        if egress.ok and egress.country == wanted:
            return SwitchResult(wanted=wanted, egress=egress, switched=False, action="none", ok=True,
                                detail=f"already exiting from {wanted}")

        observed = egress.country or "unknown"

        if not self.available:
            return SwitchResult(
                wanted=wanted, egress=egress, switched=False, action="none", ok=False,
                detail=(f"exit is {observed}, need {wanted}, and no VPN client is configured. "
                        f"Switch manually, then re-run."))

        if not self.auto_switch:
            return SwitchResult(
                wanted=wanted, egress=egress, switched=False, action="none", ok=False,
                detail=(f"exit is {observed}, need {wanted}. vpn.auto_switch is off, so nothing was "
                        f"changed. Run: {' '.join(self._connect_argv(wanted))}"))

        argv = self._connect_argv(wanted)
        if argv is None:
            return SwitchResult(
                wanted=wanted, egress=egress, switched=False, action="none", ok=False,
                detail=(f"no location string mapped for {wanted}. Add it under vpn.locations in "
                        f"marketplaces.yaml."))

        if self.dry_run:
            return SwitchResult(
                wanted=wanted, egress=egress, switched=False, action=" ".join(argv), ok=False,
                detail=(f"[dry-run] exit is {observed}, would run `{' '.join(argv)}` to reach "
                        f"{wanted}; nothing changed"))

        code, out = self._run(argv)
        if code != 0:
            return SwitchResult(wanted=wanted, egress=egress, switched=False, action=" ".join(argv),
                                ok=False, detail=f"connect failed: {out[:400]}")

        # Routes do not come up the instant the client returns.
        time.sleep(self.provider.settle_seconds)

        after = observe_egress(timeout=timeout)
        ok = after.ok and after.country == wanted
        return SwitchResult(
            wanted=wanted, egress=after, switched=True, action=" ".join(argv), ok=ok,
            detail=(f"switched {observed} -> {after.country}" if ok else
                    f"connect ran but exit is {after.country or 'unknown'}, wanted {wanted}"))

    def _connect_argv(self, country: str) -> list[str] | None:
        location = self.provider.locations.get(country.upper())
        if location is None:
            return None
        return [a.replace("{location}", location) for a in self.provider.connect]


# ---------------------------------------------------------------------------
# Standalone CLI
# ---------------------------------------------------------------------------


def _load_vpn_config() -> dict[str, Any] | None:
    try:
        from price_scan import load_marketplaces  # type: ignore
    except ImportError:
        sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
        try:
            from price_scan import load_marketplaces  # type: ignore
        except ImportError:
            return None
    try:
        return (load_marketplaces() or {}).get("vpn")
    except Exception:
        return None


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    cmd = argv[0]
    cfg = _load_vpn_config()
    provider = provider_from_config(cfg) if cfg else BUILTIN["windscribe"]
    ctl = VPNControl(provider, auto_switch=bool((cfg or {}).get("auto_switch", True)))

    if cmd == "where":
        eg = observe_egress()
        print(eg.describe())
        return 0 if eg.ok else 1

    if cmd == "status":
        print(f"provider: {provider.name if provider else 'none'} "
              f"({'found' if ctl.available else 'NOT on PATH'})")
        print(ctl.client_status())
        eg = observe_egress()
        print(f"observed egress: {eg.describe()}")
        return 0

    if cmd == "ensure":
        if len(argv) < 2:
            print("usage: vpn_control.py ensure <ISO country code>", file=sys.stderr)
            return 2
        res = ctl.ensure_geo(argv[1])
        print(f"{'OK  ' if res.ok else 'FAIL'} {res.detail}")
        print(f"     egress now: {res.egress.describe()}")
        return 0 if res.ok else 1

    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
