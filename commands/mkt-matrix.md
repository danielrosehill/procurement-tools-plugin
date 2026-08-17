---
description: Build the spec-conformance matrix across the whole field — every requirement against every live option, unknowns marked as unknown
---

# Conformance Matrix

Score the field against the spec. Writes `landscape/matrix.md`.

## Scope

Every **live** option in `landscape/field.md`, against every must-have and hard no in `spec.md`. Nice-to-haves get their own smaller matrix underneath — they're cluster detectors here, not scoring criteria.

Excluded options don't need a full row; `landscape/field.md` already records which requirement they failed. Include one if it's instructive — an option that fails a single must-have and clears everything else is the nearest-miss that `/procurement-tools:mkt-gaps` will want.

## Cell values

| Value | Means |
|---|---|
| `yes` | Verified against a primary source, with the source and date |
| `no` | Verified as not meeting it |
| `partial` | Meets it conditionally — the condition must be stated in the note |
| `?` | Couldn't be verified |

**`?` is a real answer and must never be replaced with a guess.** A plausible wrong value is worse than a blank, because it propagates into the report and then into a purchase. Every `?` carries a note on what would resolve it: a spec sheet that doesn't exist, a figure no vendor publishes, a claim that needs hands-on testing.

The **pattern** of unknowns is a finding in itself. If one requirement is `?` across the entire field, no vendor treats it as a published spec — which tells the buyer they will not be able to compare on it before buying, and that is worth stating explicitly.

## Evidence discipline

Each `yes` / `no` needs a source and a date. Retailer listings and roundups don't settle a spec; manufacturer pages, spec sheets, manuals and filings do. Where sources conflict, record both and mark the cell `?` with the conflict noted — a contested spec is exactly the kind of thing a buyer needs warned about.

Use the `spec-verification` sub-agent for load-bearing claims, i.e. any requirement that eliminates options. Use `manufacturer-research` where the requirement is about the vendor rather than the product (support, warranty, regional presence, longevity).

## Layout

```markdown
## Must-haves

| Option | Segment | [MH1] | [MH2] | [MH3] | Clears all? |
|---|---|---|---|---|---|

## Hard nos

| Option | [HN1] | [HN2] | Clear? |
|---|---|---|---|
```

For hard nos, `yes` means the disqualifying characteristic is **present** — read the column header as the characteristic, not as compliance. State this above the table; it's the commonest way these matrices get misread.

Follow each table with a notes section: one line per non-obvious cell, giving the source, the date, and any condition attached to a `partial`.

## Read the matrix back

Close with what the matrix says about the field, not about individual options:

- **Rows that clear everything** — how many, and in which segments. If it's zero, say so prominently; that's the survey's headline.
- **Columns nothing clears** — an unmet requirement, straight into `landscape/gaps.md`.
- **Columns everything clears** — an over-served requirement that isn't separating anything.
- **Columns that are mostly `?`** — an unpublishable spec; the buyer can't compare on it in advance.
- **Correlated columns** — two requirements that always travel together, meaning the field offers fewer independent choices than the spec implies.

## Don't rank

No scores, no weighted totals, no ordering. A weighted total requires weights the user hasn't given and buries the trade-offs the matrix exists to expose. Where the field narrows under some weighting, that belongs in `/procurement-tools:mkt-gaps` as a conditional narrowing, stated with its condition.

Next: `/procurement-tools:mkt-gaps`.
