# Research — Evaluate Candidates Against the Spec

Evaluate all candidate products against the spec and produce `from-ai/research.md`.

## Pre-research checklist

1. **Read `spec.md`** at the repo root. Verify Status is "Configured".
2. **Verify the Standing preferences snapshot** in `spec.md` is populated — if empty, run `/load-preferences` first.
3. If `spec.md` is unconfigured or missing must-haves / hard nos, stop and suggest `/intake`.
4. **Check `for-ai/`** — user-provided sources (screenshots, PDFs, links, notes).
5. If `for-ai/` has images/PDFs, consider running `/extract` first to structure them into CSV.

## Inputs

Apply two sources of constraint throughout evaluation:

- **Per-purchase** (from `spec.md`): must-haves, hard nos, nice-to-haves, this-purchase priorities, per-purchase overrides
- **Standing** (from the snapshot in `spec.md`, originally loaded from memory): country/currency, standing avoided brands, default markup threshold, review score floor, international shipping tolerance

Per-purchase overrides beat standing defaults. If `spec.md` overrides markup threshold to 60%, use 60% instead of the standing default.

## Candidate selection

Sources of candidates, in priority order:

1. **User-provided** — anything in `for-ai/` is a candidate (extract names, models, prices)
2. **Spec-directed search** — if the spec mentions specific brands/models to consider
3. **Discovery** — if the user's timeline allows expanded search, research the market to find candidates that match the spec

If the user explicitly said "only evaluate my sources", skip step 3.

## For each candidate

### 1. Identify

- Exact model name/number
- Manufacturer
- Current price + vendor
- Cache lookup: check `data/products/[brand]-[model-slug].json` — reuse if <7 days old

### 2. Must-haves check

From `spec.md` → Must-haves section. For each must-have, record: satisfied / partial / not satisfied.

If any must-have is NOT satisfied → **DISQUALIFIED (missing must-have: X)**.

### 3. Hard nos check

Two sources:

- **Per-purchase hard nos** from `spec.md` → Hard nos / Dealbreakers section
- **Standing avoided brands** from the Standing preferences snapshot

For each, record: clear / triggered. Any TRIGGERED → **DISQUALIFIED (hard no triggered: X, or avoided brand: Y)**.

### 4. Foundational disqualification

Apply these regardless of spec (unless the spec explicitly overrides):

- Manufacturer red flags — documented fraud, safety recalls, defunct, regulatory bans
- Product red flags — safety hazards, aggregate rating <2.5/5, widespread defect patterns, counterfeit-prone
- Vendor red flags — grey market / unauthorised, no returns on high-value, fraud reports

### 5. Manufacturer assessment

- Company reputation + history
- Support / warranty track record
- Presence in user's market (from spec's geographic context)

Spawn `manufacturer-research` sub-agent for unfamiliar brands.

### 6. Product assessment

- Build quality + materials
- Review aggregate (multiple sources — never rely on one platform)
- Known issues or failure modes
- Longevity / durability reports

### 7. Value assessment

- Price in local currency (from spec)
- Equivalent in international reference currency (USD / EUR)
- Comparison to international RRP
- Markup %
- Shipping / import costs if international
- Apply the spec's markup threshold — if exceeded without justification, flag

### 8. Verdict

- **CONSIDER** — passes all gates, proceeds to `/recommend`
- **DISQUALIFIED** — record the specific reason (which must-have missed, which hard no triggered, which foundational rule tripped)

## Output: `from-ai/research.md`

```markdown
# [Category from spec] Research

**Date**: [YYYY-MM-DD]
**Budget**: [from spec]
**Location**: [from spec]
**Spec summary**: [1-line]

## Candidates Evaluated

### [Product name]

**Verdict**: CONSIDER / DISQUALIFIED ([specific reason])

- **Price**: [Amount + currency] ([international equivalent])
- **vs RRP**: +X% over international
- **Manufacturer**: [Name] — [reputation summary]
- **Reviews**: X.X/5 from [sources]

**Must-haves satisfied**:
- [Must-have 1]: ✓ / partial / ✗
- [Must-have 2]: ✓ / partial / ✗

**Hard nos**:
- [Hard no 1]: clear / TRIGGERED
- [Hard no 2]: clear / TRIGGERED

**Nice-to-haves met**: [list]
**Strengths**: [bullets]
**Concerns**: [bullets]

[Repeat for each candidate]

## Summary

- Evaluated: X products
- Considered: X
- Disqualified: X (breakdown: must-haves, hard nos, foundational)
- Ready for `/recommend`: yes/no
```

## After research

Tell the user:

- How many candidates evaluated
- How many passed (CONSIDER)
- Top 2–3 by quick assessment
- Any important gaps or caveats
- Prompt: "Research saved to `from-ai/research.md`. Run `/recommend` to generate the PDF report, or ask me to dig deeper on any candidate first."
