# Candidates

One dossier per option that earns depth: `<vendor>-<model>.md`.

**Not every entry in the field gets one.** Dossiers come after the sweep is broad enough, and only for options that survive the spec or are instructive in how they fail. A field of forty entries might have six dossiers.

Suggested shape:

```markdown
# <Vendor> <Model>

**Segment**: [from segments.md]
**Status**: live / excluded / discontinued
**Indicative price**: [band] · **RRP**: [official figure + source]
**Verified**: YYYY-MM-DD against [primary source]

## What it is
[Two lines]

## Against the spec
| Requirement | Meets? | Evidence |
|---|---|---|
| [Must-have 1] | yes / no / ? | [Source + date] |

## What it optimises for
[The design intent — what the vendor was trying to build]

## Compromises
[What it gives up]

## Unknowns
[What couldn't be verified, and what would resolve it]

## Sources
[URLs with dates — mirrored into ../sources/index.md]
```

Mark unverifiable claims `?`. A dossier full of confident numbers from retailer listings is worse than a sparse one built from a spec sheet.
