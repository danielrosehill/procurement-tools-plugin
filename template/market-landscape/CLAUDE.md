# Market Landscape Workspace

## Purpose

This workspace answers **"what's on the market that meets this spec, and what does that market look like?"** — not "which one should I buy".

One repo = one spec. The spec is a **requirement**, not a product: "a Bluetooth headset that survives an 8-hour day, works on Linux, and has a hardware mute button" — not "which of these three headsets is best". The deliverable is a **survey of the field**, not a recommendation.

**This is the deliberate opposite of the `general-purchasing` variant.** That one narrows to a decision; this one maps the territory. If the user already knows they are buying one of a known handful of products, they're in the wrong workspace — point them at `/purchasing:new-workspace <name> --variant=general-purchasing`.

## What "done" looks like

A landscape survey is complete when someone who has never seen the market can read `outputs/` and know:

1. **What exists** that meets the spec — the whole field, named, with the date each entry was verified.
2. **How the market divides** — the segments, and the axes the market actually varies along (which are rarely the axes the spec was written in).
3. **Which requirements are met by whom** — a conformance matrix over the full field, with unknowns marked as unknown.
4. **Where the gaps are** — requirements nothing supplies, requirements everything supplies (i.e. not worth specifying), and the compromise axes where the buyer will have to give something up.
5. **What was ruled out and why** — the excluded options are part of the map, not waste.

A landscape survey is **not** complete because a good option was found. Finding a good option early is the most common way these go wrong: it collapses into a purchase decision and the rest of the field never gets mapped.

## The workflow

```
/purchasing:mkt-spec       → define the requirement envelope + survey scope (spec.md)
/purchasing:mkt-survey     → sweep the market; enumerate the field (landscape/field.md)
/purchasing:mkt-segment    → derive segments + the real variation axes (landscape/segments.md)
/purchasing:mkt-matrix     → spec-conformance matrix over the whole field
/purchasing:mkt-gaps       → unmet requirements, over-served requirements, compromise axes
/purchasing:mkt-report     → the landscape report (markdown + PDF)
/purchasing:mkt-refresh    → months later: what changed since the last survey
```

`mkt-survey` → `mkt-segment` → `mkt-matrix` is a loop, not a line. Segmenting usually reveals a category the sweep missed; go back and sweep it.

## Repository structure

```
├── CLAUDE.md              # Agent instructions (this file)
├── spec.md                # The requirement envelope + survey scope
├── landscape/
│   ├── field.md           # The enumerated field — every option found
│   ├── segments.md        # How the market divides + the real variation axes
│   ├── matrix.md          # Conformance matrix over the full field
│   └── gaps.md            # Unmet / over-served requirements, compromise axes
├── candidates/            # One dossier per option: <slug>.md
├── sources/               # Logged sources, with the date each was read
├── outputs/               # Dated landscape reports (.md / .typ / .pdf)
└── notes/                 # Scratch thinking, dead ends, open questions
```

## The spec (`spec.md`)

Capability-framed, not product-framed. Populated by `/purchasing:mkt-spec`.

It carries two things the purchase spec doesn't:

- **Survey scope** — the boundary of the sweep. Geography, price band, form factors, new/used, categories explicitly in and out. Without this the sweep never terminates.
- **Adjacent categories** — things that solve the same problem a different way. A landscape survey that only looks at the category the user named will miss the answer whenever the answer sits one category over. Name them in the spec and sweep them.

Budget and timeline appear as **scope filters**, not as decision constraints. "Nothing over $400" bounds the sweep; it isn't a ceiling to negotiate against.

## Rules for the sweep

**Breadth before depth.** Get the field enumerated before any option gets a dossier. A half-swept market that has been analysed in detail is worse than an unanalysed complete one — it produces confident conclusions about the wrong field.

**Log everything, including the misses.** Discontinued products, vapourware, region-locked options, things that used to meet the spec and no longer do — all of it goes in `landscape/field.md` with a status. "This category used to exist and died" is a finding.

**Date every claim.** Every entry in the field and every dossier carries the date it was verified and the source. Markets move; an undated survey is unusable six months later, which is exactly when `mkt-refresh` wants to run.

**Unknown is a valid value.** Never fill a matrix cell with a guess. `?` with a note on what would resolve it is more useful than a plausible wrong answer — and the pattern of unknowns is itself a finding about how opaque the market is.

**Don't rank.** Resist producing a #1. Where the survey does point somewhere, say so as "if you weight X, the field narrows to A and B" — conditional on a weighting the user hasn't given yet.

## Prices and geography

Prices are geo-dependent and any cloud fetch returns real-looking numbers for the wrong market. In this workspace:

- Prices in the field table are **indicative band only** (e.g. "$180–260 street") for segmenting the market, and must be labelled as such.
- Manufacturer RRP from an official source is fine from any fetcher — it's a published single-currency figure.
- Any **actual shop price** must come from the `price-scan` skill, which egresses from the user's own machine through the right VPN exit. See `/purchasing:shop-setup`.
- `/purchasing:market-check` is available if a specific option needs local-vs-import realism — but that's a purchase question, and answering it here usually means the survey has drifted into a decision.

## Sources

Every source read goes into `sources/` as a line in `sources/index.md`: URL, what it was used for, date read, and whether it's a primary source (manufacturer, spec sheet, standards body) or secondary (review, roundup, forum).

Vendor roundups and "best X of 2026" listicles are useful for **recall** — finding options you didn't know existed — and worthless for **evaluation**. Use them to populate the field, then verify each entry against a primary source before it earns a dossier.

## Reuse from the plugin

These `/purchasing:*` primitives work here unchanged:

- `/purchasing:extract` — pull options out of screenshots, PDFs and vendor catalogues into the field
- `/purchasing:evaluate <product>` — quick check of one option against the spec
- `/purchasing:update-spec <change>` — targeted spec edit, flags downstream impact
- `price-scan` skill — live pricing through your own egress
- Sub-agents `manufacturer-research`, `spec-verification`, `review-aggregation`, `product-extraction`

Not applicable here: `/purchasing:intake`, `/purchasing:research`, `/purchasing:recommend`, `/purchasing:recompare`, `/purchasing:apply-profile`. Those drive toward a pick. Buyer profiles in particular are a **bias layer** — deliberately absent from this variant, because biasing a survey defeats its purpose. Apply a profile later, in a purchase repo, once the landscape is known.

## Visibility

Landscape surveys are usually **private by default** — the spec reveals what the user is planning. A survey of a generic category with no personal context in it is fine to publish, and is often the more useful artefact of the two. Decide per repo; the default is private.

## Handing off to a purchase

When the survey is done and the user wants to actually buy something:

```
/purchasing:new-workspace <thing>-purchase-MMDD --variant=general-purchasing --private
```

Carry across the shortlist from `landscape/gaps.md` (the "candidates worth a decision" section) and the requirement list from `spec.md`. Leave this repo as the standing map of the market; the purchase repo is a separate, disposable thing.
