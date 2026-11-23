---
name: seller-shortlist
description: Shortlist sellers to ask for quotes: keep reputable shops, drop aggregators, dropshippers and excluded sellers, dedupe the contact log
allowed-tools: Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Bash(cat *), Bash(ls *), Bash(date *)
---

# Seller shortlist

Turns a pile of candidate sellers (from research, a price-comparison site, a
`price-scan`, or names the user gives) into a short list of sellers worth
contacting, with the channel to reach each one. Step 2 of the `quote-loop`.

The rule underneath: **a cheap price at a seller you would not buy from is not
an option.** Filter before contacting, not after the quotes come back.

## Inputs

- Candidate sellers: name, site, and the product/price that surfaced them.
- The purchase workspace's contact log (default `docs/sellers-contacted.md`, or
  `quote_loop.contact_log_path` from the overlay). Create it from
  `${CLAUDE_PLUGIN_ROOT}/template/quote-loop/contact-log.md` if absent.
- Constraints, in this precedence: what the user said for this purchase, then
  the workspace's `CLAUDE.md`, then the overlay's `quote_loop.default_constraints`
  and `quote_loop.excluded_sellers`, then the defaults (`reputable_only: true`,
  `new_only: true`, no exclusions).
- Locale profile: `${CLAUDE_PLUGIN_ROOT}/locales/<locale>.json`, where `<locale>`
  is the one the user names, else the overlay's `default_locale`, else `default`.

## User overlay

Read `${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/procurement-tools/config.json`
and take its `quote_loop` section (schema in the README, example in
`${CLAUDE_PLUGIN_ROOT}/examples/config/quote-loop.config.example.json`). If the
file or section is missing, use the defaults above and say once that no overlay
was found.

## Steps

1. **Apply the reputation filter** (skip only if `reputable_only` is false). A
   seller qualifies with at least one, ideally several, of the locale's
   `reputable_signals`:
   - the manufacturer, or the official importer / distributor for the country;
   - a recognised retail chain;
   - an established specialist in the category, with a showroom or workshop;
   - company registration number and physical address on the site;
   - reviews beyond the price-comparison site (e.g. Google Maps).

   Exclude generic multi-category aggregator storefronts and dropshippers (the
   locale's `aggregator_signals`: unrelated categories, no company details,
   listing text copied from the importer or from another storefront). Mark a
   seller **borderline** when the signals conflict, and keep it off the
   shortlist unless nothing better exists.
2. **Apply the condition filter.** With `new_only`, drop sellers that only offer
   display, open-box, outlet, returned or refurbished stock (the locale's
   `condition_terms.exclude`). A seller with both new and outlet stock stays;
   the enquiry asks about condition.
3. **Apply exclusions.** Drop every seller in the user's excluded list, matching
   on brand, operator and domain, not just the display name.
4. **Dedupe against the contact log.** For each survivor, decide which
   *operator* is behind it: same company number, same address or phone, same
   WhatsApp number, sister brand of the same importer, or storefronts with
   identical listing text. One operator counts once. Drop any seller whose
   operator already has a first-contact row on **any** channel. A new question
   in an existing thread is fine; a second cold message is not. Also check any
   other seller lists the workspace keeps (`docs/suppliers.md` and the like).
5. **Vet with the locale's reputation skill.** If the profile names one (Israel:
   `israel-shopping:store-reputation`), run it on any seller you are not sure of
   and record its verdict. With no reputation skill, check the reviews yourself
   and say the check was manual.
6. **Find the channel** for each shortlisted seller, in the locale's
   `channel_order`, using its `find` hints (e.g. Israel: a `wa.me` link, then a
   05x mobile, then a WhatsApp Business landline; then email; then site chat;
   then a phone script).
7. **Write it down.** Add every dropped seller to the log's "Excluded or skipped"
   table with the reason, so the next research pass doesn't re-find it. Return
   the shortlist as a table: seller, operator, why reputable, product and listed
   price, channel and address.

## Data storage

Reads the user overlay (read-only) and the locale profiles in the plugin. Writes
only the contact log inside the user's purchase workspace. Nothing is stored in
plugin data.

## Notes

- When a cheap price only appears at an excluded seller, shortlist the same
  model from the importer or a chain instead, and say what the premium is.
- Typical sizes: 3-6 sellers per round. More than that and the replies stop
  being comparable within one business day.
- This skill does not contact anyone. `contact-sellers` does.
