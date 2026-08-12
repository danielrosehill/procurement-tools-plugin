---
description: Sweep the market and enumerate the full field against the survey spec — breadth first, everything logged and dated
argument-hint: [segment or category to sweep, optional — defaults to a full sweep]
---

# Market Sweep

Enumerate what exists. Writes `landscape/field.md`.

If `$ARGUMENTS` names a segment, category or vendor, sweep only that and append. Otherwise run a full sweep.

## Prerequisites

`spec.md` Status must be "Configured" — if not, run `/purchasing:mkt-spec` first. Read the requirement, the must-haves, the hard nos, the **survey scope table** and the **adjacent categories** before starting. The scope table is what stops the sweep; the adjacent categories are what stop it being wrong.

## The rule that governs this command

**Breadth before depth.** Get names into the field before any option gets analysed. A half-swept market analysed in detail produces confident conclusions about the wrong field — the most expensive failure mode in this workspace, because the output looks finished.

Concretely: no dossier in `candidates/` until the sweep log shows the ground has been covered. If you find something excellent in the first ten minutes, log it and keep sweeping.

## Where to sweep

Work outward, and record each pass in the sweep log:

1. **The named category, directly** — manufacturer sites, category pages at the retailers in scope, spec databases where the category has one.
2. **Recall sources** — roundups, "best of" articles, subreddit and forum recommendation threads, YouTube channel back-catalogues. These are for *finding names only*. Note when several recycle the same handful of products; that is itself a finding about the market's thinness.
3. **The adjacent categories from `spec.md`** — each one, explicitly, ticking the box in the field's adjacent-category table. Do not skip these because the primary sweep went well.
4. **Sideways** — who else does the vendors in the field consider a competitor? Comparison pages and "alternatives to X" queries surface the long tail.
5. **Backwards** — what used to exist? Discontinued products, dead brands, categories that have emptied out. Search for the category with a date qualifier, check archived vendor pages.

## Logging rules

Every entry in `landscape/field.md` needs a **status**, a **verified date** and a **source**.

- `live` — available, and clears the must-haves and hard nos.
- `excluded` — fails a specific must-have or hard no. **Name which one.** Excluded entries stay in the table permanently; "the obvious answer doesn't work, and here's exactly why" is a headline finding.
- `discontinued` — existed, no longer sold. Record roughly when, and what replaced it.
- `announced` — not shipping. Record the claimed date and your confidence: firm, soft, or vapourware.
- `unverified` — a name from a secondary source, not yet confirmed. These must all be resolved before the sweep can be declared complete.

**Verification means a primary source**: manufacturer page, spec sheet, manual, regulatory filing. A retailer listing is not a spec. Log every source read into `sources/index.md` with its date and type as you go, not afterwards.

## Prices

Indicative bands only here (`$180–260 street`), and labelled as indicative. They exist to segment the market, nothing more.

Real prices are geo-dependent and cloud fetchers return real-looking numbers for the wrong market. Any actual shop price comes from the `price-scan` skill running on the user's own machine through the right VPN exit. A manufacturer's published RRP is fine from any fetcher — it's single-currency and not geo-varying.

## Collapse the duplicates

Before reporting a count, collapse rebadges and OEM overlap: the same hardware sold under three brands is one option, not three. Note the relationship rather than deleting the rows — a field that looks like twelve products and is really four is one of the most useful things a survey can establish.

## Deciding you're done

Check the **termination condition** in `spec.md`. Also require:

- Every adjacent category ticked off.
- The unverified-leads section empty — each promoted or explained.
- At least two independent sweep passes that surfaced no new names.

If the condition is met, set sweep status to Complete with the date and the condition that was satisfied. If it isn't, say what's still open and stop — don't pad the field to look finished.

## Output

Update `landscape/field.md`: the tables, the entry counts, the sweep log row for this pass, the adjacent-category ticks. Append to `sources/index.md`.

Then print: how many entries by status, what the sweep added beyond the user's known starting points, anything surprising (an empty segment, a dead category, a rebadge cluster), and what's still unswept.

Next: `/purchasing:mkt-segment`.
