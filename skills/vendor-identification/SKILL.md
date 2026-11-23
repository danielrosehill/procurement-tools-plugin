---
name: vendor-identification
description: Find and identify new vendors for a need: discover suppliers, sellers, importers, workshops and local makers (Israel and other locales)
allowed-tools: Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Agent, Bash(cat *), Bash(ls *), Bash(date *)
---

# Vendor identification

The quote loop's discovery step: turns a need into a list of **prospective
vendors** to ask. Shops, importers and distributors, chains, category
specialists, and local makers or workshops for made-to-order jobs ("custom steel
desk frame", "cut-to-size worktop"). Step 1 (research) of `quote-loop`; its
output is the input of `seller-shortlist`, which filters and dedupes it.

**Vendor-first, not product-first.** When the exact model is known and the
question is "where is it sold and at what price", a product finder is the better
tool (Israel: `israel-shopping:find-product`, which runs Zap vendor tables,
trusted vendors and import options). This skill asks "who could supply this",
which also covers trades with no retail listing at all.

## Inputs

- The need: item or job, the spec or its key constraints (`spec.yaml` /
  `define-spec` output if there is one), the user's city, and whether it is
  off-the-shelf or made to order.
- The purchase workspace's contact log (default `docs/sellers-contacted.md`, or
  `quote_loop.contact_log_path` from the overlay) and any other seller lists it
  keeps (`docs/suppliers.md` and the like).
- Locale: the one the user names, else the overlay's `default_locale`, else
  `default`. Profile: `${CLAUDE_PLUGIN_ROOT}/locales/<locale>.json`, block
  `vendor_identification` (channels, query idiom, directories, warnings), plus
  `search` and `reputation_skill`.

## User overlay

Read `${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/procurement-tools/config.json`,
section `quote_loop`, for `default_locale`, `contact_log_path` and
`excluded_sellers`. Without it, use the defaults and say once that no overlay
was found. The user's city comes from the purchase spec or the workspace's
`CLAUDE.md`; ask only if neither has it and the need is local (workshops,
showrooms, pickup).

## Steps

1. **Frame the need as search vocabulary.** Write down, in the locale's
   language:
   - generic category nouns (and a synonym or two);
   - the brands and models that satisfy the spec, if it is off-the-shelf;
   - the trade that makes or fits it, if it is made to order or needs
     installation (the profile's `trade_nouns` give examples: metal workshop,
     carpentry, upholsterer, sign maker).
   Keep brand and model names in Latin script.
2. **Read the contact log first.** List every operator already contacted or
   excluded, with sister brands and shared operators (same company number,
   address, phone or messaging number, same importer, identical listing text).
   Add the overlay's `excluded_sellers`. These are filtered out of every result
   below; one company under two names counts once.
3. **Fan out over the channels in parallel.** Run the profile's channels at the
   same time: independent tool calls in one message, or one subagent per channel
   on a small model (sonnet or haiku) for the slow ones. Each subagent gets the
   vocabulary, the exclusion list and the output fields from step 4, and returns
   JSON rows. A channel that fails is reported with the route tried, never
   dropped silently.
   - **(a) Locale-restricted web search** with a commercial word:
     `vendor_identification.web_search.first_query`, swapping the commercial
     word in the profile's `commercial_word_ladder` order when results are thin.
     Follow its `engine_notes`: if the built-in web search ignores `site:` or is
     region-biased, run the query in Google in a real browser or through a
     semantic search API.
   - **(b) Price aggregators and marketplaces** (`aggregators`): model pages
     list every vendor; store cards carry reviews. Also the big chains' own
     search (`chains`).
   - **(c) Business directories** (`directories`), queried with the trade or
     category noun plus the city.
   - **(d) Brand to official importer or distributor**
     (`importer_lookup.query`) for every brand from step 1. The importer either
     sells direct or names its authorised dealers.
   - **(e) Maps and local search** (`maps`) for showrooms and workshops near the
     user's city; widen the radius only if fewer than three turn up.
4. **Record each vendor** once, merged across channels:
   - name (and the operator behind it, if known), city;
   - type: importer/distributor, chain, specialist, workshop/maker, general shop;
   - why it might be reputable: years trading, review count and rating,
     showroom or workshop, importer status, company number on the site;
   - what fits: the model, the service, or "makes to order";
   - contacts: messaging, phone, email, site contact form; mark landlines per
     the profile's `warnings` (e.g. "call or email", not "WhatsApp");
   - URL;
   - provenance for each detail: `vendor_page` (read on the vendor's own site)
     or `snippet` (from a search result, aggregator or directory, unconfirmed);
   - flags: any profile `warnings` that apply (e.g. multi-category
     dropshipper storefront), and the channels that found it.
   Read the vendor's own page for at least the top candidates; never invent a
   phone number, address or rating.
5. **Rank and hand off.** Rank by fit first (does it supply this, new, in
   range), then reputation signals, then proximity for local trades. Output:

   ```
   ## Vendors for <need> (<locale>, checked <YYYY-MM-DD>)
   Vocabulary: <queries used>
   Excluded up front: <n> already in the contact log / exclusions

   | # | Vendor | Type | City | Why reputable | Fits | Contacts | URL | Source | Flags |
   |---|---|---|---|---|---|---|---|---|---|

   Channels run: web ✓ (n) · aggregators ✓ (n) · directories ✓ (n) · importer lookup ✓ (n) · maps ✗ (route tried, how it failed)
   ```

   Then pass the table to `seller-shortlist`, which applies the reputation and
   condition filters, runs the locale's reputation skill
   (`reputation_skill`, Israel: `israel-shopping:store-reputation`) and picks
   the contact channel. Vendors that carry a warning flag stay in the table so
   the shortlist can record why it dropped them.

## Data storage

Reads the user overlay (read-only), the plugin's locale profiles and the
contact log in the user's purchase workspace. Writes nothing by default; if the
user asks to keep the candidate list, write it to the purchase workspace (e.g.
`docs/vendor-candidates.md`). Nothing is stored in plugin data.

## Notes

- Makes web requests and, with a browser route, opens sites in the user's
  browser. Contacts nobody: `contact-sellers` does that.
- Typical yield: 8-15 candidates, so that `seller-shortlist` can cut to 3-6.
  If a round finds fewer than five, widen the vocabulary (synonyms, the trade
  instead of the product, a neighbouring city) before widening the channels.
- Adding a locale is a data change: fill in a `vendor_identification` block in
  its `locales/<locale>.json`, following `locales/default.json`.
