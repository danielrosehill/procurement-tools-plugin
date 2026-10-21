# Buyer Profiles

Pre-built purchasing archetypes. Use them as a **fallback reference** when you don't have standing preferences in memory yet, or as a **shortcut** when you want the agent to bias research and recommendations toward a particular pattern without hand-writing the priority list.

## Why these exist

`spec.md` captures what you're buying. Standing preferences (in memory or the fallback file) capture *how* you shop in general. But sometimes you want a **named pattern** — "this is a BIFL purchase", "this is the budget-optimised one", "treat this like a power-user purchase" — without re-specifying every priority from scratch.

Profiles are that named pattern. They ship with the template so a fresh repo is usable even with zero memory configured.

## The nine profiles

| Profile | One-line summary |
|---------|------------------|
| [`bifl-buyer`](bifl-buyer.md) | Optimises for manufacturers with a reputation for unusually durable, long-lasting products. "Buy it for life." |
| [`budget-buyer`](budget-buyer.md) | Maximises value per currency unit inside a tight budget. Accepts trade-offs on prestige/features for price. |
| [`feature-maximiser`](feature-maximiser.md) | Wants the most features / spec / capability per dollar, even at the cost of polish or longevity. |
| [`reliability-buyer`](reliability-buyer.md) | Wants dependable, boring, proven products. Not interested in glamour, hype, or cutting-edge spec. |
| [`power-user`](power-user.md) | Wants products that can be modified, serviced, scripted against, or extended — hackable, open, repairable. |
| [`minimalist`](minimalist.md) | Fewest features that meet the must-haves. Simplicity as a virtue. Opposite of Feature Maximiser. |
| [`ethical-buyer`](ethical-buyer.md) | Supply-chain ethics, labour, environmental footprint, Right to Repair. Willing to pay for a defensible production story. |
| [`early-adopter`](early-adopter.md) | Newest, first-to-market, cutting-edge. Accepts first-gen quirks and novelty premium as cost of access. |
| [`premium-aesthete`](premium-aesthete.md) | Design, materials, fit-and-finish, brand design heritage. The product lives in the space, so how it looks matters. |

## Using a profile

Run `/apply-profile` from a freshly-intook repo (or one where you want to reframe the recommendation). Pick one profile, or combine two or three. The command writes the resulting priorities and heuristics into `spec.md`'s **Buyer profile** section.

```
/apply-profile bifl
/apply-profile budget+reliability
/apply-profile bifl+power-user
/apply-profile           # interactive picker
```

## Combining profiles

Profiles blend additively:

- **Priorities are merged** with a preference for the earlier-listed profile when they conflict (first profile dominates).
- **Red flags are unioned** — anything flagged by any of the included profiles is flagged.
- **Preferred signals are unioned** — anything preferred by any profile is preferred.
- **Weight adjustments** are averaged across profiles, with the first profile weighted 1.5×.

Each profile lists its own "Combines well with" and "Conflicts with" in its file. When a conflicting combination is requested, the agent surfaces the tension during `/apply-profile` rather than refusing it.

## How a profile affects research

When a profile is applied, the agent does three things during `/research` and `/recommend`:

1. **Re-weights evaluation axes.** A BIFL profile uplifts build quality and manufacturer track record; a budget profile uplifts price-per-capability.
2. **Promotes profile-specific signals.** "Repair documentation available", "metal chassis", "10-year parts availability", etc. become actively sought rather than nice-to-have.
3. **Demotes or disqualifies anti-signals.** A BIFL profile will demote products with documented built-in obsolescence patterns; a power-user profile will disqualify heavily DRM-locked products.

Profiles **do not** override standing preferences or hard nos in `spec.md` — those always win. The profile is a bias layer on top.

## Editing / adding profiles

Each profile is a self-contained markdown file with a fixed front-matter schema. To add a new one, copy an existing profile and fill in:

- `priorities` — ordered list
- `weight-adjustments` — numeric multipliers on evaluation axes
- `preferred-signals` — what to actively look for
- `red-flags` — what to demote or disqualify
- `typical-brands` — illustrative examples (not prescriptive)
- `typical-anti-brands` — archetypes to avoid for this profile

Profiles are **archetypes, not brand lists** — avoid baking specific brand names into a profile's rules. Brand attitudes belong in standing preferences.
