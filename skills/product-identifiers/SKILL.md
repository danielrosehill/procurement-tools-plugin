---
name: product-identifiers
description: Find the UPC, EAN, JAN, GTIN and MPN for a product from a trading name, marketing description or listing, verified by variant.
allowed-tools: Read, Write, Edit, Grep, WebSearch, WebFetch, Bash(python3 *), Bash(curl *), Bash(mkdir *)
---

# Product identifiers: from a trading name to a barcode

Goes from what the user calls a product to the codes that comparison sites and
shops index. Run it before comparing prices across shops or countries.

## Inputs

A trading name, description, photo or listing URL. Optionally the target market.

## Steps

1. **Pin the variant.** Find the exact manufacturer part number (MPN) and list its
   siblings (connector, colour, kit, revision). Ask only if the description fits
   more than one sibling that the user would care about.
2. **Collect codes, strongest source first.** Manufacturer regional pages and PDF
   catalogues or price lists (Japan calls it JAN); packaging photos; large
   retailers' specification blocks and JSON-LD (`gtin13`, `gtin12`, `gtin`,
   `mpn`); marketplace item specifics. Use barcode databases for leads only.
3. **Expect several codes for one product.** Makers may issue different codes by
   region. Collect them all and record the market each was seen in.
4. **Collect the siblings' codes too.** They expose listings that mix variants.
5. **Validate:** `python3 ${PLUGIN_ROOT}/scripts/gtin.py <code> [<code> ...]`.
   A valid check digit does not prove that the code belongs to the product.
6. **Grade each code.** `confirmed`: the manufacturer states it for this MPN, or
   it was read off the packaging. `probable`: two or more independent large
   retailers state it for this MPN. `unverified`: anything else. `refuted`:
   belongs to a sibling. Shops that share a feed count as one source.
7. **Search each code and the MPN, separately.** Compare each hit's code, MPN and
   described features. If they disagree, mark it `conflict` and ask the shop.

## Output

Table and JSON: `name`, `mpn`, `codes` (`code`, `type`, `market`, `grade`,
`sources` with URL and date), `siblings`, `conflicts`, `unresolved`. Save to
`data/identifiers/<mpn>.json` in the purchase workspace if there is one.

## Traps

- **Truncated EAN shown as a UPC.** A 12-digit "UPC" can be an EAN-13 with its
  last digit cut off. It can even pass the UPC check by chance. `gtin.py` prints
  the EAN-13 it would be; look for that code too.
- **Padding.** A 14-digit code with a leading 0 may be the same as an EAN-13;
  an EAN-13 with a leading 0 is a UPC-A. Compare as GTIN-14.
- **Shop and marketplace codes** (ASIN, SKU) are not global. One marketplace
  page can hold several sellers.
- **Bundles and refurbished units** have their own codes and MPN suffixes.
- **Never guess a code** from a sibling's number, even when they run in sequence.

## Worked example (observed 2026-11-24)

"Audio-Technica streaming headset, USB" resolves to MPN `ATH-M50xSTS-USB`.

| Code | Product | Source | Grade |
|---|---|---|---|
| 4961310159665 | USB | Manufacturer's Japanese page (JAN); also Polish and French shops | confirmed |
| 4961310159672 | USB | Target, Best Buy, another US shop; Amazon Brazil as 04961310159672 | probable |
| 496131015967 | USB, as "UPC" on Amazon | EAN-13 above without its last digit | truncated |
| 4961310159641 | XLR sibling | Manufacturer's Japanese page (JAN) | confirmed, sibling |
| 4961310159658 | XLR sibling | Manufacturer's Latin America catalogue | confirmed, sibling |

Conflict found: one shop's page described an XLR connection but carried the USB
MPN and the USB code. The description alone would have bought the wrong variant.

## Related

`part-number-equivalence` for different MPNs across regions; `price-scan` after
the codes are known.
