# Apply Profile — Bias This Purchase Toward a Buyer Archetype

Apply one or more **buyer profiles** from `buyer-profiles/` to `spec.md` so the `/research` and `/recommend` phases bias toward a named purchasing pattern (BIFL, budget, minimalist, etc.).

Profiles are a **fallback reference** for users without standing preferences in memory, and a **shortcut** for users who want to reframe a purchase without hand-writing priorities. Profiles do not override must-haves or hard nos — they're a bias layer on top.

## Argument forms

| Form | Behaviour |
|------|-----------|
| `/apply-profile` | Interactive picker: list the 9 profiles, ask which one(s) to apply |
| `/apply-profile bifl` | Apply a single profile |
| `/apply-profile bifl+power-user` | Apply a blend (first profile dominates) |
| `/apply-profile none` | Clear the buyer-profile section of `spec.md` |

Valid profile slugs: `bifl`, `budget`, `feature-maximiser`, `reliability`, `power-user`, `minimalist`, `ethical`, `early-adopter`, `premium-aesthete`. Accept common aliases (`bifl-buyer` → `bifl`, `budget-buyer` → `budget`, `feature-max` → `feature-maximiser`, `reliability-buyer` → `reliability`, `aesthete` → `premium-aesthete`).

## Step 1: Resolve profiles

1. Parse the argument. Split on `+` for combinations.
2. Normalise each slug (accept aliases).
3. Read each resolved profile file from `buyer-profiles/<slug>.md` (or `<slug>-buyer.md` where applicable).
4. If a slug doesn't resolve, list available profiles and ask.

## Step 2: Check for conflicts

Read each profile's **Conflicts with** section. If the requested combination includes a conflicting pair, surface the tension before applying:

> "Heads up: `feature-maximiser+minimalist` is a direct contradiction. I'll apply both but the recommendation will have to pick a side. Proceed?"

Don't refuse — the user may have a reason. Just flag it.

## Step 3: Blend (if multiple profiles)

Blend rule (also documented in `buyer-profiles/README.md`):

- **Priorities:** merge the ordered priority lists. When the same axis appears in both, use the higher position from the first-listed profile. De-duplicate.
- **Preferred signals:** union of all listed profiles.
- **Red flags:** union of all listed profiles.
- **Weight adjustments:** average each axis across profiles, with the first profile weighted ×1.5. Any axis listed by only one profile is kept at that profile's multiplier.
- **Typical-archetype brands:** union, noted as examples (not recommendations).
- **Typical anti-archetypes:** union.

If single profile: no blending — just lift that profile's sections directly.

## Step 4: Write to `spec.md`

Populate the **Buyer profile** section of `spec.md` with:

```markdown
## Buyer profile

**Applied profile(s)**: [e.g. "BIFL + Power User"]
**Applied at**: [YYYY-MM-DD]

**Priorities from profile** (applied as tie-breakers *after* the this-purchase priorities already in spec.md):
1. [Top merged priority]
2. [Next]
...

**Preferred signals** (actively sought during research):
- [Signal]
- [Signal]

**Red flags** (demoted or disqualified during research):
- [Flag]
- [Flag]

**Weight adjustments** (applied to the default evaluation axes):
| Axis | Multiplier |
|------|-----------|
| ... | ×N.N |

**Typical-archetype brands** (examples only — standing brand prefs always win):
[short list]

**Tensions flagged**: [only if conflicting profiles were combined — one-line description]
```

If the section doesn't exist yet (fresh `spec.md` from before this feature), add it under "Priorities (this purchase)".

## Step 5: Report

Report in 3–5 lines:

- Which profile(s) applied
- Top 3 priorities that resulted
- Any flagged tensions
- Next step ("Run `/research` — it will honour the profile bias.")

## Step 6: Tell downstream commands

No code change needed — `/research`, `/recommend`, and `/recompare` all read `spec.md` and will pick up the **Buyer profile** section automatically. But the user should know:

> Profile applied. `/research` and `/recommend` will now weight the evaluation accordingly. Standing prefs from memory still take precedence over profile suggestions; must-haves and hard nos in `spec.md` always win.

## Interactive picker (when `/apply-profile` called with no argument)

Use `AskUserQuestion` with the 9 profiles as options + a "Combine two or more" option. If the user picks Combine, ask which ones (free-text or multi-select), then flow into Step 2.

## Using without standing preferences

If the user has no standing preferences in memory and no `<plugin-data-dir>/shopping-preferences.md` (resolved via `$CLAUDE_USER_DATA` — see `/load-preferences`), a buyer profile is the fastest way to give the agent *some* shopping posture for this purchase. Flow:

1. `/intake` (fills in per-purchase fields — what you're buying, must-haves, hard nos, budget)
2. `/apply-profile` (picks a named archetype as a shortcut for priorities + heuristics)
3. `/research`
4. `/recommend`

This path is documented for users who don't want to set up standing preferences but do want more signal than raw `/intake` gives on its own.

## What NOT to do

- Don't write profile content into standing preferences / memory. Profiles are per-purchase biases; standing prefs are the user's permanent shopping personality.
- Don't overwrite must-haves, hard nos, budget, or other `spec.md` sections. The Buyer profile section is additive only.
- Don't invent new profiles on the fly. If the user wants a custom archetype, help them edit `spec.md`'s priorities directly or add a new file under `buyer-profiles/`.
- Don't treat profile typical-brands as prescriptive. They're examples of the archetype, not a shopping list.
