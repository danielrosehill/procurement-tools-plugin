[![Claude Code Repos Index](https://img.shields.io/badge/Claude%20Code%20Repos-Index-blue?style=flat-square&logo=github)](https://github.com/danielrosehill/Claude-Code-Repos-Index)

# Claude Purchasing Assistant

![Claude Space](https://img.shields.io/badge/Claude-Space-purple?style=flat-square)
![Template](https://img.shields.io/badge/Template-green?style=flat-square)

A Claude Code workspace template for a **single purchasing decision**. One repo = one purchase. Spin up a fresh copy per thing you're buying (laptop, car, drill, chair) and take it from spec to PDF report.

## Two-tier preferences model (+ optional buyer-profile bias)

- **Standing preferences** (country, currency, trusted/avoided brands, markup ceiling, risk tolerance) live in **memory** via the [Mem0 MCP](https://mem0.ai). One-time setup, applied to every future purchase workspace.
- **Per-purchase spec** (`spec.md` at repo root) holds only this decision: what you're buying, must-haves, hard nos, budget, timeline, priorities.
- **Buyer profiles** (`buyer-profiles/`) are optional named archetypes — BIFL, budget, minimalist, power-user, etc. — that the user can apply to this purchase via `/apply-profile`. Works as a fallback for users without Mem0, or as a shortcut for reframing a purchase. Combines dynamically (e.g. `bifl+power-user`).

This split is deliberate. Your preferences don't belong in each new repo — they belong in memory. Profiles are a lightweight way to add named bias on top without permanent commitments.

## The workflow

```
/save-preferences   → one-time setup (or update) — writes standing prefs to Mem0
/load-preferences   → pull standing prefs into this workspace
/intake             → build spec.md (per-purchase only)
/apply-profile      → (optional) bias toward a named buyer archetype
/research           → evaluate candidates against spec + prefs + profile
/recommend          → generate PDF report
```

## What makes this template useful

- **Preferences persist across repos.** With Mem0 MCP, your standing prefs are loaded into every new purchase workspace — no re-interviewing yourself.
- **Must-haves and hard nos are distinct.** "Must have X" and "must not have Y" are different kinds of constraints; both disqualify, and the spec captures them separately.
- **Single-use per purchase.** No nested `purchases/active/` folders — the repo itself is the purchase.
- **Decisive PDF deliverable.** Top 3 ranked, clear #1 pick, spec-adherence matrices for must-haves and hard nos.

## Setup (first time only)

### Option A — Recommended: Mem0 MCP

Install a Mem0 MCP server. Example (the exact installation varies by Mem0 MCP implementation):

```
/plugin install mem0@...
```

Then in any purchasing template repo:

```
/save-preferences
```

Walk through standing prefs once. From then on, every new purchasing workspace auto-loads them via `/load-preferences`.

### Option B — Local fallback

Without Mem0 MCP, the commands save to `<plugin-data-dir>/shopping-preferences.md` (resolved via `$CLAUDE_USER_DATA/procurement-tools/` — see the `meta-tools:plugin-data-storage` canonical skill) instead. Works within a single machine but doesn't sync. Install Mem0 MCP for cross-device persistence.

### Option C — No persistence

Skip `/save-preferences` entirely. `/intake` will ask you the standing questions inline, every time. Not recommended if you shop frequently.

## Per-purchase flow

### 1. Create your repo from the template

Via the `new-repo-from-template@danielrosehill` plugin, or:

```bash
gh repo create --template danielrosehill/Claude-Purchasing-Assistant my-new-laptop
cd my-new-laptop
```

### 2. Run intake

```
/intake
```

Intake calls `/load-preferences` first — your standing prefs come in automatically. Then it asks only the per-purchase questions: what you're buying, must-haves, hard nos, budget, timeline.

### 3. (Optional) Drop sources

If you've already found candidates, drop screenshots / PDFs / link notes into `for-ai/`.

### 4. Research and recommend

```
/research    # Evaluate candidates against spec + standing prefs
/recommend   # Generate the PDF report
```

Outputs land in `from-ai/`. If your standing prefs include an email and Resend MCP is configured, the PDF gets sent.

## Repository layout

```
├── CLAUDE.md              # Agent instructions
├── spec.md                # THE per-purchase spec — populated via /intake
├── buyer-profiles/        # Named archetypes (BIFL, budget, minimalist, etc.)
├── for-ai/                # INPUT: drop sources here
├── from-ai/               # OUTPUT: research.md, recommendation.md, report.pdf
├── data/
│   ├── products/          # Cached product specs + pricing
│   └── extracted/         # CSV extractions from screenshots
└── .claude/commands/      # Slash commands
```

## Slash commands

Core flow:

| Command | Purpose |
|---------|---------|
| `/load-preferences` | Pull standing prefs from Mem0 (or fallback file) |
| `/save-preferences` | Persist standing prefs to Mem0 — one-time or when updating |
| `/intake` | Populate `spec.md` — per-purchase only, must-haves and hard nos distinctly |
| `/apply-profile` | Apply a buyer archetype (single or combined) to bias research. Optional. |
| `/research` | Evaluate candidate products against the spec + standing prefs + profile |
| `/recommend` | Generate the final PDF recommendation report |
| `/compare` | Side-by-side comparison of specific products |
| `/extract` | Extract products from screenshots/catalogs to CSV |

Iterative / quick checks:

| Command | Purpose |
|---------|---------|
| `/evaluate <product>` | Quick inline check of a single product against the current spec |
| `/market-check [models]` | Compare local vs international pricing with import-cost realism |
| `/recompare` | Re-run the shortlist after spec or pricing changes (dated output, preserves history) |
| `/update-spec <change>` | Targeted edit to `spec.md` — diff-only, flags downstream impact |

Sub-agents (auto-invoked): `manufacturer-research`, `product-extraction`, `price-comparison`, `review-aggregation`, `spec-verification`.

## Buyer profiles (optional)

If you don't want to set up Mem0 yet, or you want a quick shortcut for the evaluation bias on this one purchase, the template ships nine named archetypes in `buyer-profiles/`:

- **BIFL** — durability and brand reputation for long service life
- **Budget** — best value per currency unit inside a tight budget
- **Feature Maximiser** — most spec and capability per dollar
- **Reliability** — proven, boring, works every time
- **Power User** — hackable, serviceable, no vendor lock-in
- **Minimalist** — fewest features that meet the need
- **Ethical** — supply chain, labour, environmental footprint
- **Early Adopter** — newest, first-to-market
- **Premium / Aesthete** — design, materials, fit-and-finish

Apply one, or combine:

```
/apply-profile bifl
/apply-profile bifl+power-user
/apply-profile budget+reliability+minimalist
```

Combinations blend additively — first-listed profile dominates on conflicts, and tensions between profiles are surfaced rather than silently resolved. Profiles do not override must-haves, hard nos, or standing prefs — they're a bias layer on top. See `buyer-profiles/README.md` for the blending rules and per-profile details.

## What lives where

### In Mem0 memory (standing preferences)

- Country, currency, VAT rate, VAT status
- Trusted brands (general)
- Avoided brands (general) — with reasons
- Preferred / avoided vendors (general)
- Default markup threshold, review score floor
- Risk tolerance
- International shipping tolerance
- Email for PDF delivery

### In `spec.md` (per-purchase)

- What you're buying + category + primary use case
- Must-haves (this purchase)
- Hard nos / Dealbreakers (this purchase — augments standing avoided brands)
- Nice-to-haves
- Budget (this purchase)
- Timeline + deal-hunting posture
- Priorities (this decision)
- Per-purchase overrides to standing prefs (e.g. "accept higher markup this time")
- Context / history
- Standing preferences snapshot (auto-populated audit trail)

## Example flow

```
# First time only
1. /save-preferences
   → Country, currency, local tax rate
   → Trusted brands (your call)
   → Avoided brands (with reasons)
   → Markup threshold
   → International shipping stance
   → Email for PDF delivery

# For each purchase
2. gh repo create --template … my-new-purchase
3. /intake
   → /load-preferences runs automatically, loads from Mem0
   → Describe what you're buying
   → Must-haves (hard positive requirements)
   → Hard nos (disqualifying characteristics)
   → Budget + timeline
4. (Optional) drop candidate screenshots into for-ai/
5. /research
   → Agent evaluates against must-haves, hard nos, standing avoided brands,
     standing markup threshold. Disqualified candidates are documented with reasons.
6. /recommend
   → Generates report.pdf with top 3 ranked picks
   → Emails PDF if email is in standing prefs
```

---

For more Claude Code projects, visit my [Claude Code Repos Index](https://github.com/danielrosehill/Claude-Code-Repos-Index).
