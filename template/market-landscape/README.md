[![Claude Code Repos Index](https://img.shields.io/badge/Claude%20Code%20Repos-Index-blue?style=flat-square&logo=github)](https://github.com/danielrosehill/Claude-Code-Repos-Index)

# Market Landscape

![Claude Space](https://img.shields.io/badge/Claude-Space-purple?style=flat-square)
![Template](https://img.shields.io/badge/Template-green?style=flat-square)

A Claude Code workspace for **surveying a market against a spec**. You have a requirement; you want to know what exists that meets it, how the market divides, and where the gaps are. The deliverable is a map, not a purchase.

Provisioned by the [purchasing plugin](https://github.com/danielrosehill/Claude-Purchasing-Plugin):

```
/procurement-tools:new-workspace <name> --variant=market-landscape --private
```

## Landscape vs purchase

| | `market-landscape` | `general-purchasing` |
|---|---|---|
| Starts from | a spec / capability need | a thing you've decided to buy |
| Question | what's out there that meets this? | which of these should I get? |
| Output | a survey of the field + gaps | a ranked recommendation + PDF |
| Ranking | deliberately avoided | the whole point |
| Lifespan | durable; refreshed periodically | disposable; closed when you buy |
| Ends when | the field is mapped | the decision is made |

They chain: survey the landscape here, then spin up a purchase repo for the actual buy.

## The workflow

```
/procurement-tools:mkt-spec       → requirement envelope + survey scope
/procurement-tools:mkt-survey     → sweep the market, enumerate the field
/procurement-tools:mkt-segment    → segments + the axes the market really varies on
/procurement-tools:mkt-matrix     → conformance matrix over the whole field
/procurement-tools:mkt-gaps       → unmet / over-served requirements, compromise axes
/procurement-tools:mkt-report     → the landscape report (markdown + PDF)
/procurement-tools:mkt-refresh    → months later: what changed
```

Survey → segment → matrix is a loop. Segmenting almost always exposes a corner of the market the first sweep missed.

## What makes this template useful

- **It refuses to pick.** No #1, no runner-up. Where the field does narrow, it narrows *conditionally* — "if you weight battery life, it's these two" — leaving the weighting to you.
- **The whole field is the artefact**, including what was ruled out and why, and options that are discontinued or region-locked. Knowing a category died is a finding.
- **Segments are derived, not assumed.** The axes a market varies along are usually not the axes your spec was written in; discovering that mismatch is the most valuable output.
- **Unknowns stay unknown.** Matrix cells you couldn't verify are marked `?` with a note on what would resolve them, never filled with a plausible guess.
- **It survives.** Every entry is dated and sourced, so `/procurement-tools:mkt-refresh` can tell you six months later what actually changed.

## Layout

```
├── CLAUDE.md              # Agent instructions
├── spec.md                # Requirement envelope + survey scope
├── landscape/
│   ├── field.md           # Every option found, with status and date
│   ├── segments.md        # How the market divides
│   ├── matrix.md          # Requirements × options, unknowns kept unknown
│   └── gaps.md            # Unmet, over-served, compromise axes
├── candidates/            # One dossier per serious option
├── sources/               # Logged sources with dates
├── outputs/               # Dated landscape reports
└── notes/                 # Scratch, dead ends, open questions
```

## Prices

Indicative bands only in the field table — enough to segment the market, labelled as such. Real prices are geo-dependent, so any actual shop price comes from the `price-scan` skill running on your own machine through the right VPN exit (`/procurement-tools:shop-setup`). Manufacturer RRP from an official page is fine from anywhere.

## Public or private?

Private by default — the spec says what you're planning. A survey of a generic category with nothing personal in it is often worth publishing, and is the more reusable half of the work. Pass `--private` (default for this variant) or drop it to publish.

---

For more Claude Code projects, visit my [Claude Code Repos Index](https://github.com/danielrosehill/Claude-Code-Repos-Index).
