#!/usr/bin/env python3
"""Self-checks for price extraction and landed-cost maths.

Deterministic and offline: fixtures are synthetic pages in the shapes the real
marketplaces emit. Run directly:

    python3 tests/test_price_scan.py
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from price_scan import (  # noqa: E402
    BOT_WALL_MARKERS,
    extract_availability,
    extract_price,
    extract_shipping,
    landed_cost,
)

FAILURES: list[str] = []


def check(label: str, got, want) -> None:
    if got != want:
        FAILURES.append(f"{label}: got {got!r}, wanted {want!r}")


JSONLD_PAGE = """
<html><head>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Product","name":"Widget",
 "offers":{"@type":"Offer","price":"249.99","priceCurrency":"USD",
 "availability":"https://schema.org/InStock"}}
</script>
</head><body>FREE delivery Tuesday</body></html>
"""

AMAZON_PAGE = """
<html><body>
<div id="corePrice_feature_div"><span class="a-offscreen">$1,299.00</span></div>
<span>In Stock</span>
<div>FREE Prime delivery</div>
</body></html>
"""

NEWEGG_PAGE = """
<html><body>
<script>window.__INITIAL__ = {"finalPrice":179.99,"currency":"USD"};</script>
<div class="price-current">$179<sup>99</sup></div>
<div>Add to cart</div>
</body></html>
"""

NEWEGG_SPLIT_PAGE = """
<html><body>
<div class="price-current">$1,049<sup>50</sup></div>
<div>Out of stock</div>
</body></html>
"""

BOT_WALL_PAGE = """
<html><body><h1>Enter the characters you see below</h1>
<p>Sorry, we just need to make sure you're not a robot.</p></body></html>
"""

NO_PRICE_PAGE = "<html><body><h1>Widget</h1><p>Currently unavailable</p></body></html>"


def test_jsonld_wins() -> None:
    price, currency, avail, how = extract_price(JSONLD_PAGE, "amazon-us")
    check("jsonld price", price, 249.99)
    check("jsonld currency", currency, "USD")
    check("jsonld availability", avail, "in stock")  # normalised, not schema.org spelling
    check("jsonld source", how, "json-ld")


def test_amazon_offscreen() -> None:
    price, _, avail, how = extract_price(AMAZON_PAGE, "amazon-us")
    check("amazon price", price, 1299.00)
    check("amazon availability", avail, "in stock")
    check("amazon source", how, "site-pattern:amazon")


def test_newegg_embedded_json() -> None:
    price, _, _, how = extract_price(NEWEGG_PAGE, "newegg")
    check("newegg price", price, 179.99)
    check("newegg source", how, "site-pattern:newegg")


def test_newegg_split_dollars_cents() -> None:
    # The dollars/cents <sup> split is the one that silently returns 1049
    # instead of 1049.50 if the two-group branch is broken.
    price, _, avail, _ = extract_price(NEWEGG_SPLIT_PAGE, "newegg")
    check("newegg split price", price, 1049.50)
    check("newegg split availability", avail, "out of stock")


def test_bot_wall_markers_present() -> None:
    lowered = BOT_WALL_PAGE.lower()
    check("bot wall detected", any(m in lowered for m in BOT_WALL_MARKERS), True)


def test_no_price_page() -> None:
    price, _, avail, how = extract_price(NO_PRICE_PAGE, "newegg")
    check("no price", price, None)
    check("no price source", how, "none")
    check("no price availability", avail, "out of stock")


def test_shipping() -> None:
    cost, note = extract_shipping(AMAZON_PAGE)
    check("free shipping cost", cost, 0.0)
    check("free shipping note", note, "FREE Prime delivery")

    cost, _ = extract_shipping('<div>Shipping: $12.50 to your address</div>')
    check("quoted shipping", cost, 12.50)

    cost, note = extract_shipping("<div>nothing relevant</div>")
    check("unknown shipping", (cost, note), (None, None))


def test_landed_sales_tax() -> None:
    shop = {"tax": "destination_sales_tax"}
    addr = {"tax": {"sales_tax_pct": 6.35, "confirmed": False}}
    total, note = landed_cost(100.0, 10.0, shop, addr)
    check("sales tax total", round(total, 3), 116.985)  # (100+10) * 1.0635
    check("unconfirmed rate flagged", "unconfirmed" in note, True)


def test_landed_unknown_shipping_is_stated() -> None:
    shop = {"tax": "none"}
    total, note = landed_cost(50.0, None, shop, {})
    check("unknown shipping total", total, 50.0)
    check("unknown shipping stated", "shipping unknown" in note, True)


def test_landed_missing_rate_excludes_tax() -> None:
    shop = {"tax": "destination_sales_tax"}
    total, note = landed_cost(200.0, 0.0, shop, {"tax": {}})
    check("no rate total", total, 200.0)
    check("no rate stated", "tax excluded" in note, True)


def test_landed_no_price_is_none() -> None:
    total, note = landed_cost(None, 10.0, {"tax": "none"}, {})
    check("no price landed", total, None)
    check("no price note", note, "no price")


def test_landed_vat() -> None:
    shop = {"tax": "vat_added"}
    addr = {"tax": {"vat_pct": 18}}
    total, _ = landed_cost(100.0, 0.0, shop, addr)
    check("vat added", round(total, 2), 118.0)

    total, note = landed_cost(100.0, 5.0, {"tax": "vat_inclusive"}, addr)
    check("vat inclusive", total, 105.0)
    check("vat inclusive note", "already in price" in note, True)


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for test in tests:
        test()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)} of {len(tests)} checks failed):")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print(f"ok — {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
