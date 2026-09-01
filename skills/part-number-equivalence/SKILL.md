---
name: part-number-equivalence
description: Work out which part numbers name the same product across regions, brands and channels — and which look identical but are not. Use when a product found in one market has to be sourced in another, when a manufacturer's model numbers differ between the US and Europe, when the same object is sold under an OEM or private-label brand, when a supplier offers something "equivalent", or when a suspiciously cheap listing may be a different variant. Produces an equivalence record with per-member confidence and the evidence behind it.
allowed-tools: Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Bash(python3 *), Bash(ls *), Bash(cat *), Bash(mkdir *), Bash(curl *)
---

# Part-number equivalence

The product you found is not the product you can buy. A tool sold in the US as
one model number is sold in Europe as another; the same object appears under a
trade brand at a trade price; and — the expensive case — a near-sibling differs
by two characters in the part number and lacks the one feature the purchase
exists for.

This skill maps the family and says, per member, how confident the link is and
what it rests on. Output: `data/equivalence/<family>.json`, conforming to
`${CLAUDE_PLUGIN_ROOT}/schema/equivalence.schema.json`.

## Decode the naming scheme first

Before hunting individual numbers, work out how the manufacturer builds them.
This is the reusable finding — it usually generalises to the maker's whole
catalogue, and it turns every later lookup from a search into a read.

Patterns that recur across manufacturers:

- **Unit-system encoding.** A number in the model name is the range in feet in
  the US catalogue and in metres in the metric one. The same tool then appears
  under two numbers that share no digits, which is why searching the US number
  in a European catalogue returns nothing and reads as "not sold here".
- **Feature suffixes.** A trailing letter or two-digit group encodes the
  connected variant, the green-beam variant, the battery chemistry, the kit
  contents. These are the traps: the variants sit at similar prices, look
  identical in photographs, and differ in exactly the capability being bought.
- **Kit vs bare.** The same core product with and without battery, charger, or
  case, often distinguished only by a suffix.
- **Generation digits.** A digit bumped for a revision that changed the
  firmware or the radio and nothing visible.
- **Regional certification variants.** Same product, different radio
  certification and mains plug, different number.

Write what you worked out into `naming_scheme` in plain language. It is the
field a later reader will actually use.

## Establish links with evidence, not resemblance

Confidence is a required field per member, and the bar for each level is:

| Confidence | Requires |
|---|---|
| `confirmed` | A source that **states** the link: a manufacturer cross-reference or regional selector, one declaration of conformity covering both numbers, a shared manual listing both, identical datasheets published under each. |
| `probable` | Strong convergent evidence with no statement: identical published specs from both regions' own datasheets, a distributor cross-reference table, the same accessory list. |
| `unverified` | It looks right. Two retailers say so. The numbers follow the pattern you decoded. Keep it, mark it, do not act on it. |
| `refuted` | Checked and they are not the same. Worth recording — it stops the next search re-proposing it. |

A shared product photograph is not evidence: manufacturers reuse renders across
a family, and retailers reuse them across manufacturers.

**Two retailers agreeing is one source.** Retail listings copy each other and
copy the same feed. Convergence across listings is not corroboration.

## Record the decoys

A `relation: decoy` member is a part number that looks like the anchor and is
materially different. These are frequently the most valuable rows in the file,
because they are what a hurried search actually returns and what a marketplace
suggests as "similar".

For every decoy, state the difference in `differences` and — if a `spec.yaml`
exists — which requirement it breaks in `spec_impact`. "Same family, same price
band, no radio, fails REQ-001" is the sentence that prevents the wrong purchase.

## Regional fetching is where this goes silently wrong

Manufacturer and distributor catalogues serve different content per country. A
lookup for a US part number that egresses from Israel returns the European
catalogue, finds nothing, and reads as "not sold in the US".

So: `WebFetch` first, and when the answer depends on which market you are
looking at, use `mcp__gateway__geo-egress__fetch_markdown` with `egress` passed
**explicitly** — `"us"` for the US catalogue, `"il"` for the Israeli one.
`egress` defaults to `"il"`, and a wrong-country result here is an HTTP 200 with
plausible content. Run `mcp__gateway__geo-egress__verify_egress()` before
drawing an availability conclusion.

Record which market each finding came from. `availability.sold_in` is a claim
about a market, and it is only as good as the exit it was observed from.

## Differences that matter more than they look

For anything not `identical`, `differences` must be filled. The ones that
routinely turn an "equivalent" into a wrong purchase:

- **Radio certification.** A regional variant may carry a different radio
  approval, which is what the maker's own app checks against.
- **Firmware and protocol.** Same hardware, different protocol, so a third-party
  integration lists one number and not the other.
- **Mains plug and voltage.** Trivially solvable, or not, depending on whether
  the supply is internal.
- **Warranty.** Regional warranties are usually not honoured outside the region.
  A grey-imported sibling is cheaper because it is uninsured, and that is a real
  cost, not a technicality.
- **Bundled contents.** Kit variants explain price gaps that otherwise look like
  a bargain.
- **Support and spares.** Whether consumables and spares exist in the
  destination market at all.

## Finish with buy implications

`buy_implications` is what the user actually reads. Turn the mapping into
instructions:

- Which number to search in which market.
- What the cheaper sibling costs you, concretely.
- Which variant the third-party integration supports.
- What will not be honoured under warranty on an import.
- Which number to put on an RFQ so a supplier quotes the right thing.

Leave anything you could not settle in `unresolved`, phrased as the question a
distributor could answer in one email.

## Relationship to the rest of the plugin

- `spec-sheet-retrieval` gets the documents; matching datasheets under two numbers is `probable`-grade evidence here, and a shared declaration of conformity is `confirmed`-grade.
- `evaluation-matrix` treats a regional sibling as a **separate candidate** unless this skill has confirmed them identical. Merging them early is how a conformance record ends up describing a product the user cannot buy.
- `bom-build` lines carry `equivalence_ref` so an RFQ can name the number the supplier's own market uses.
- For consumer-to-industrial *category* mapping — "what is the professional version of this thing" rather than "what is this thing called elsewhere" — that is a different question; see the Industrial-Equivalents notebook rather than this skill.
