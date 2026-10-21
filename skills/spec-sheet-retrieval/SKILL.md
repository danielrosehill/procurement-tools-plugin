---
name: spec-sheet-retrieval
description: Find the manufacturer's own documentation for a specific product — datasheet, technical data, operating manual, declaration of conformity — and extract the published values with the document and revision they came from. Use when a spec claim has to be settled rather than repeated, when retailer listings disagree with each other, when a parameter is not on the product page, or before treating any number as a fact in a comparison. Records what the manufacturer does not publish as well as what it does.
allowed-tools: Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Bash(python3 *), Bash(ls *), Bash(cat *), Bash(mkdir *), Bash(curl *), Bash(sha256sum *), Bash(pdftotext *)
---

# Spec sheet retrieval

Retail listings are the worst available source for a technical specification and
the easiest to reach, which is why nearly every wrong purchase decision traces
back to one. The maker publishes the real numbers, usually as a PDF, usually
several clicks off the product page, often only in one region's site. This skill
goes and gets it.

Output: one record per part number at `data/datasheets/<manufacturer>-<part-number>.json`,
conforming to `${CLAUDE_PLUGIN_ROOT}/schema/datasheet.schema.json`.

## The rule that makes the record worth having

**A value with no document behind it is not a value.** It goes in
`not_published`, or it does not go in the file. The temptation is always to fill
a field from a retail bullet because the number is *probably* right — and a
probably-right number is indistinguishable, downstream, from a verified one.

## 1. Pin the part number first

Get the exact part number, spelled as the manufacturer spells it, before
searching for documents. Half of all failed datasheet hunts are a hunt for a
retailer's SKU, or for a part number from a different region.

Record every spelling you see in `aliases`: spacing variants (`GLM 165-27C` /
`GLM165-27C`), retailer SKUs, distributor order codes, EAN/UPC. They are the
search terms that find the document when the canonical one does not.

If the part number is ambiguous, or the user has one from another market, run
`part-number-equivalence` first. Fetching the wrong region's datasheet returns a
real document, with real numbers, for a product they cannot buy — and nothing on
the page says so.

## 2. Work down the document ladder

Stop at the first source that answers the question, but know what you gave up:

| Rank | Source | Notes |
|---|---|---|
| 1 | Manufacturer product page → "Downloads" / "Technical data" / "Service" | The canonical set. Often a separate tab, often not linked from the marketing page. |
| 2 | Operating manual | Carries what the datasheet omits: function lists, modes, conditions, limits. Usually the only place indirect functions, protocols and app behaviour are named. |
| 3 | Declaration of conformity / certification filing | Radio type, frequency, power, and the regulatory identity that links regional siblings. Excellent evidence and almost never consulted. |
| 4 | Manufacturer's regional site for another market | Often a fuller PDF, sometimes in another language. Note the region on the record. |
| 5 | Trade distributor's document mirror | Grainger, RS, Farnell, Mouser and their regional equivalents host manufacturer PDFs. Genuine documents, but check the revision — mirrors go stale. |
| 6 | Archived copy of a dead manufacturer page | For discontinued products this is often all that exists. Mark it as archived and date it. |

Everything below that line — retailer listings, roundups, spec-aggregator sites —
is not a document. Aggregators in particular are dangerous because they look
structured: they are usually one original error copied across twenty sites, which
then reads as corroboration.

## 3. Fetch it, escalating only when blocked

Start with `WebFetch`. It is the fastest route and it works for most
manufacturer sites.

Escalate on an actual failure, not pre-emptively:

1. `WebFetch` — default.
2. `claude-in-chrome` (`mcp__claude-in-chrome__*`) — when the download list renders under JavaScript (common on manufacturer support portals), when the site blocks a plain fetch, or when the document sits behind a login or a professional-account wall. It is the user's real browser on their own machine, so it also serves the document for the user's own country.
3. `curl` via Bash — for headers, redirects and raw PDF downloads.
4. `mcp__gateway__playwright__*` — last fallback only, when the routes above genuinely cannot do it.

**There is no route that makes a fetch appear to come from another country**
(the geo-egress server was retired on 2026-09-02). Every route above leaves
from the user's own location or from the cloud. When you need a **regional** document — the US
datasheet rather than the EU one — look for it by direct URL or region selector
on the manufacturer's site, or on a regional distributor's mirror; do not
assume the document you were served is the one for the market you asked about.
If you cannot get the regional version, say so and record the region you
actually got.

Record which route worked in `documents[].accessed_via`, and the egress country
in `egress`. Where region changed the document, that field is the only thing
that lets a later reader know which market's numbers these are.

For a PDF: save it into the repo when it is load-bearing, hash it, and record
the hash. Manufacturers replace documents at the same URL without renaming them,
so a URL alone does not identify what you read. `pdftotext -layout` is usually
enough to read one; specification tables often survive better with `-layout`
than without.

## 4. Extract values, not impressions

Copy values as printed. Keep the manufacturer's units. For each one, record the
document, the page, and — for anything load-bearing — the verbatim line.

**Capture the condition attached to the number.** This is where headline specs
lie without being false:

- Range is quoted "under favourable conditions", or with a target plate.
- Accuracy holds to a stated distance and is worse beyond it.
- Battery life is at a stated temperature and duty cycle.
- IP ratings apply to the product, not to the product with the port cover open.
- "Up to" is a ceiling, not a value.

A number recorded without its condition will later be compared against another
maker's number quoted under a different condition, and the comparison will be
confidently wrong.

## 5. Record the absences

`not_published` is not a consolation prize; it is a finding. When the maker does
not publish a parameter:

- The next agent does not repeat the search.
- If the whole field omits it, the buyer learns they cannot compare on it before
  buying — which is a real, actionable conclusion, and one `evaluation-matrix`
  surfaces automatically.

Say where you looked. "Not in the datasheet or the manual, and the DoC covers
only the radio" is useful; "not found" is not.

## 6. Record the contradictions

When two manufacturer documents disagree, or when a widely-repeated retail
figure differs from the datasheet, put **both** in `contradictions` with their
sources. Do not resolve it by picking the more plausible one. A contested spec
is exactly the thing a buyer needs warning about, and the newer document is not
automatically right — makers reprint old figures.

## 7. Wire it back to the spec

If the repo has a `spec.yaml`, drive the retrieval from it: every requirement
with `verify: datasheet` or `verify: manual` names a parameter to go and find,
and its `evidence` line says what settles it. Tag each extracted spec with its
`req` id so `evaluation-matrix` can pick it up without re-reading the PDF.

## Reporting back

Say what you found, from which document and revision, and what is genuinely not
published. Distinguish clearly between the two, and never present an inference
in the same voice as a printed value.

## Hands off to

- `evaluation-matrix` — turns these values into `pass` / `fail` / `unknown` against the spec.
- `part-number-equivalence` — when the document you found is for a sibling part number, or when regional variants appeared during the search.
