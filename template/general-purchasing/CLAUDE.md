# Claude Purchasing Assistant

## Purpose

This workspace runs **one purchase decision** from spec to PDF report. One repo = one purchase. When the user is shopping for a new thing (car, laptop, chair, drill…), they spin up a fresh copy of this template and use it end-to-end.

## Two-tier preferences model (+ optional buyer-profile bias)

**Standing preferences** live in **memory** (via Mem0 MCP — recommended). Per-purchase details live in **`spec.md`** at the repo root. This separation is deliberate: the things that *always* apply to the user (their country, trusted brands, markup ceiling) don't belong in each new repo — they belong in memory, loaded fresh into every new purchase workspace.

- **Memory (Mem0)** — country, currency, VAT status, trusted brands, avoided brands, preferred vendors, avoided vendors, markup threshold, review score floor, risk tolerance, international shipping tolerance, email for PDF
- **`spec.md` (this repo)** — what's being bought, must-haves, hard nos, nice-to-haves, budget, timeline, this-purchase priorities, this-purchase overrides to standing prefs, context/history
- **`buyer-profiles/` (optional)** — named purchasing archetypes (BIFL, budget, minimalist, etc.) that the user can apply to this purchase via `/apply-profile`. Works as a fallback for users without Mem0, or as a shortcut for users who want to reframe a purchase quickly. Profile content is additive over standing prefs and `spec.md` — must-haves and hard nos always win.

## The workflow

```
/load-preferences   → pull standing prefs from Mem0 memory
/save-preferences   → (one-time or when updating) persist standing prefs to memory
/intake             → build spec.md (per-purchase only; skips standing fields)
/research           → evaluate candidates against spec + standing prefs
/recommend          → generate PDF report
```

Four phases in order: **intake → spec → research → report.** Preference management is a sidecar workflow, not a phase.

## Mem0 MCP integration

The recommended memory backend is [Mem0](https://mem0.ai) exposed as an MCP server. With Mem0:

- Preferences persist across repos, machines, sessions
- Update once (via `/save-preferences`), applied to all future purchases automatically
- Each new template instance `/load-preferences` → snapshot copied into `spec.md` for audit

If Mem0 MCP isn't available, the commands fall back to:

1. A local file: `<plugin-data-dir>/shopping-preferences.md` — resolved via `$CLAUDE_USER_DATA/procurement-tools/` (see the `meta-tools:plugin-data-storage` canonical skill)
2. Inline prompting during `/intake` (last resort — user will be re-asked each time)

The templates degrade gracefully. Mem0 is the "power user" path.

## Repository Structure

```
├── CLAUDE.md                 # Agent instructions (this file)
├── spec.md                   # THE per-purchase spec — populated via /intake
├── buyer-profiles/           # Named purchasing archetypes (BIFL, budget, minimalist, etc.)
├── for-ai/                   # INPUT: user drops sources here (screenshots, PDFs, links)
├── from-ai/                  # OUTPUT: research.md, recommendation.md, report.pdf
├── data/
│   ├── products/             # Cached product specs (JSON per product)
│   └── extracted/            # CSV extractions from screenshots (if /extract used)
└── .claude/commands/         # Slash commands
```

No `purchases/active|completed/` nesting. No per-repo `buyer-profile.md`. The repo *is* the purchase.

## The spec file (`spec.md`)

`spec.md` contains only per-purchase details:

- **What I'm buying** — category + primary use case
- **Must-haves** — hard positive requirements
- **Hard nos / Dealbreakers** — disqualifying characteristics (distinct from must-haves; adds to the standing avoided-brands list from memory)
- **Nice-to-haves** — tie-breakers
- **Budget** — target + ceiling + flexibility
- **Timeline** — urgency + deal-hunting posture
- **Priorities (this purchase)** — ranked factors for this decision
- **Per-purchase overrides to standing preferences** — e.g. accept higher markup for a niche item this time
- **Context / history** — replacing what, past experience, compatibility constraints
- **Standing preferences snapshot** — read-only audit of what `/load-preferences` pulled in

**Must-haves vs Hard nos are distinct categories.** Must-haves are positive requirements the product must satisfy. Hard nos are disqualifying characteristics the product must *not* have. Both trigger automatic disqualification, but they're captured separately because they represent different kinds of constraints.

## Workflow phases

### Phase 0: Preferences (once per user/machine)

- Run `/save-preferences` the first time the user uses any purchasing template.
- Re-run to update when standing preferences change.

### Phase 1: Load + Intake — `/load-preferences` then `/intake`

`/intake` should call `/load-preferences` automatically as step 0. Combined behaviour:

1. Load standing preferences from Mem0 (or fallback file)
2. Snapshot them into the "Standing preferences snapshot" section of `spec.md`
3. Ask only the per-purchase questions — **never re-ask standing fields**
4. Explicitly capture **must-haves** and **hard nos / dealbreakers** as distinct sections
5. Save to `spec.md`; set Status to "Configured"

### Phase 2: Research — `/research`

1. Read `spec.md` + the standing preferences snapshot + the **Buyer profile** section (if populated)
2. Apply the profile's weight adjustments on top of the default evaluation weights; include the profile's preferred-signals and red-flags alongside spec-level must-haves and hard nos
3. Process any sources in `for-ai/` (run `/extract` first if screenshots/PDFs)
4. If the spec allows expanded search or no sources were provided, discover candidates via web research
5. For each candidate, evaluate:
   - **Must-haves satisfied?** — if not, disqualify
   - **Hard nos triggered?** — if yes, disqualify (both per-purchase hard nos from spec AND standing avoided brands from prefs)
   - **Manufacturer reputation** — reliability, support, warranty
   - **Build quality + reviews** — aggregated across multiple sources
   - **Value** — local price vs international RRP, markup %
   - **Foundational disqualifications** — safety hazards, sub-2.5/5 ratings, counterfeit-prone items, defunct vendors (these apply even if not in the spec)
6. Apply the **per-purchase overrides** from `spec.md` before applying standing thresholds (e.g. if spec overrides markup to 60%, use that instead of the standing 30%)
7. Mark each candidate **CONSIDER** or **DISQUALIFIED** with reason
8. Write `from-ai/research.md`

### Phase 3: Recommend — `/recommend`

1. Read `spec.md` + `from-ai/research.md`
2. Rank CONSIDER candidates using the spec's priority order; apply the **Buyer profile** priorities as tie-breakers if the section is populated; fall back to standing priorities from memory if neither has any
3. Pick #1 (recommended), #2 (runner-up), #3 (budget alternative, if one makes sense)
4. Render via `procurement-report` to `reports/recommendation-YYYY-MM-DD.{md,typ,pdf}` — dated, never overwriting
5. Record it: `workspace.py add-report . --kind recommendation --path ...`
6. If the Resend MCP is available and an email is in standing prefs → confirm, then send the PDF
7. Report the location, the workspace id, and the top pick

## Agent guidelines

### Before any research

1. Verify `spec.md` status is "Configured" — if not, run `/intake` first
2. Verify the standing preferences snapshot is populated — if not, run `/load-preferences`
3. Make sure **must-haves** AND **hard nos** are both populated — don't start research with an incomplete spec
4. Check `for-ai/` for user-provided sources

### Foundational disqualification (always applied)

Regardless of spec, automatically disqualify or strongly flag:

- **Manufacturer red flags** — documented fraud, safety recalls, defunct/unreachable companies, regulatory bans
- **Product red flags** — safety hazards, aggregate rating <2.5/5, widespread defect patterns, counterfeit-prone items where authenticity can't be verified
- **Vendor red flags** — grey-market sellers with no authorization, no return policy on high-value items, fraud reports

Plus standing avoided brands from memory (unless the spec's per-purchase overrides relax them).

Deprioritise (don't auto-disqualify) if:

- Rating between standing review floor (default 3.5/5) and 2.5/5 — flag for explicit acknowledgment
- Manufacturer with mixed reputation — include warning
- Limited warranty / international-only support
- New or unproven products (<6 months on market, <50 reviews)

### Sub-agent context passing

When spawning sub-agents (manufacturer-research, product-extraction, price-comparison, review-aggregation, currency-conversion), always pass:

- Geography + currency (from standing prefs snapshot)
- Must-haves + hard nos (from spec)
- Standing avoided brands (from prefs)
- Effective markup threshold (spec override if present, else standing default)
- Risk tolerance (spec override if present, else standing default)
- **Applied buyer profile** (if any) — so sub-agents know which evaluation axes to uplift and what profile-specific signals / red flags to surface
- Specific product/brand being researched

## Deliverable: dated PDF report

Generated by the `procurement-report` skill at
`reports/recommendation-YYYY-MM-DD.{md,typ,pdf}`.

**Never `from-ai/report.pdf`.** Reports are dated and never overwrite a
predecessor: a report is a claim about a market at a moment, and prices, stock,
datasheets and the spec itself all move. Overwriting destroys the only record of
what was believed when the decision was made.

The skill owns the layout. It copies shared styling to `reports/base.typ` so the
workspace can recompile years later without the plugin installed, and records
the report in `procurement.json` so `workspace.py index` can find it.

Report body, in order: headline; what was judged and against which spec
revision; top three with prices and where to buy; must-haves adherence;
hard-nos clearance; what is not known; what was not covered.

Unknowns stay unknown — use the `unknown-box` helper rather than resolving a
`?` to make the document read better.

## Intermediate outputs

### `from-ai/research.md`

```markdown
# [Category] Research

**Date**: [Date]
**Spec priorities**: [From spec.md]
**Standing prefs applied**: [1-line summary]

## Candidates Evaluated

### [Product name]
- **Price**: [Amount + currency]
- **vs RRP**: +X% over international
- **Manufacturer**: [Name] — [reputation summary]
- **Reviews**: X.X/5 from [sources]
- **Must-haves satisfied**: [list or "all"]
- **Hard nos triggered**: [none / list] (spec) + [none / list] (standing)
- **Build quality**: [assessment]
- **Verdict**: CONSIDER / DISQUALIFIED ([reason])

[Repeat for each]

## Summary
- Evaluated: X
- Considered: X
- Disqualified: X
```

## Product data caching

Cache fetched product data in `data/products/[brand]-[model-slug].json`:

```json
{
  "brand": "Sony",
  "model": "WH-1000XM5",
  "category": "headphones",
  "fetched": "2026-04-16",
  "specs": {...},
  "pricing": [
    {"vendor": "Amazon", "price": 349.99, "currency": "USD", "url": "...", "checked": "2026-04-16"}
  ],
  "reviews": {...}
}
```

Cache behaviour: check before fetching; if <7 days old reuse; always refresh pricing.

## Slash commands

Core flow:

| Command | Purpose |
|---------|---------|
| `/load-preferences` | Pull standing shopping prefs from Mem0 memory (or fallback file) |
| `/save-preferences` | Persist standing prefs to Mem0 — one-time or when updating |
| `/intake` | Populate `spec.md` — per-purchase only (must-haves + hard nos distinctly) |
| `/apply-profile [profile(s)]` | Bias this purchase toward a named buyer archetype (BIFL, budget, minimalist, etc.). Single or combined (e.g. `bifl+power-user`). Optional. |
| `/research` | Evaluate candidates against the spec + standing prefs + profile (if applied) |
| `/recommend` | Generate the final PDF recommendation report |
| `/compare` | Side-by-side comparison of specific products |
| `/extract` | Extract products from screenshots/catalogs to CSV |

Iterative / quick checks (usable anytime after `/intake`):

| Command | Purpose |
|---------|---------|
| `/evaluate <product>` | Quick inline check of a single product against the current spec + latest recommendation |
| `/market-check [models]` | Compare local prices vs international RRP with import-cost realism — writes `from-ai/research/market-check-YYYY-MM-DD.md` |
| `/recompare` | Re-run the shortlist against the current spec; writes a new dated `from-ai/recommendations/recommendations-YYYY-MM-DD.md` without overwriting history |
| `/update-spec <change>` | Targeted edit to `spec.md` (addition / edit / removal) — diff-only response, flags downstream impact |

## Sub-agent architecture

Sub-agents live in `.claude/agents/` and are invoked by the main agent as needed.

| Agent | Purpose | When to use |
|-------|---------|-------------|
| `manufacturer-research` | Reputation, history, support quality, regional presence | Before recommending an unfamiliar brand |
| `product-extraction` | Extract products from screenshots / PDFs into structured CSV | When user drops images in `for-ai/` |
| `price-comparison` | Compare prices across vendors + import-cost realism | When evaluating value across multiple sources or buy-local vs import |
| `review-aggregation` | Synthesise reviews across platforms into a weighted score | During `/research` for each serious candidate |
| `spec-verification` | Confirm/refute a load-bearing spec claim against authoritative sources | When a must-have depends on a specific spec that retailers often misstate |

All sub-agents must: read `spec.md` + standing preferences snapshot first; apply disqualification criteria (spec + standing); document sources (URLs, dates); return structured data; flag uncertainties rather than guess.

## Dated outputs (history preserved)

For iterative purchases, outputs are dated and never overwritten:

- `from-ai/research/[topic]-YYYY-MM-DD.md` — topical research notes (e.g. `brand-reputation-X-2026-04-16.md`, `market-check-2026-04-16.md`). Maintain `from-ai/research/index.md` as a pointer list.
- `from-ai/recommendations/recommendations-YYYY-MM-DD.md` — written by `/recommend` and `/recompare`. Each run writes a new dated file with a "Changes vs. previous" section.
- `reports/recommendation-YYYY-MM-DD.{md,typ,pdf}` — written by `procurement-report`. Markdown twin always exists; the PDF may not if Typst is absent.

Simple single-shot outputs (e.g. `from-ai/research.md` written by `/research`, `from-ai/compare.md` written by `/compare`) live at the top level of `from-ai/` and are rewritten each run.

## Success criteria

A recommendation succeeds when:

1. **Single PDF deliverable** — one professional report
2. **Decisive** — clear #1 pick with runner-ups
3. **Must-haves explicitly checked** — adherence matrix shows each
4. **Hard nos explicitly checked** — clearance matrix shows each (per-purchase + standing)
5. **Preferences traced** — reasoning references both the spec and the standing preferences snapshot
6. **Foundational rules applied** — no disqualified products recommended
7. **Data cached** — product specs saved for potential re-runs
8. **Report delivered** — PDF emailed if Resend MCP is configured
