# Recommend — Generate the dated recommendation report

Produce the final recommendation as a dated report at `reports/recommendation-YYYY-MM-DD.{md,typ,pdf}`, rendered by the `procurement-report` skill.

## Pre-conditions

- `spec.md` at repo root — configured
- `from-ai/research.md` — exists, with at least one CONSIDER candidate

If either is missing, say what's missing and offer to run the relevant command.

## Process

### 1. Read inputs

- `spec.md` — priorities, must-haves, hard nos, nice-to-haves, budget, geography
- `from-ai/research.md` — all CONSIDER candidates with their assessments

### 2. Rank the CONSIDER candidates

Apply the spec's priority order. Typical defaults if priorities are sparse:

- Must-haves satisfied fully > partially
- Hard nos fully clear (no triggers)
- Manufacturer reputation + support
- Value (landed cost vs international RRP)
- Review aggregate
- Nice-to-have coverage (tie-breaker)

### 3. Pick top 3

- **#1 RECOMMENDED** — clear best fit
- **#2 Runner-up** — strong alternative, typically with a meaningful tradeoff
- **#3 Budget alternative** — only if there's a materially cheaper option that still passes screening

Be decisive. The user wants a clear #1.


### 4. Render the report

Hand rendering to the `procurement-report` skill rather than writing Typst here.
It owns the dated filename, the shared styling and the manifest record, so every
report this plugin produces looks like the others and none of them overwrite a
predecessor.

Kind: `recommendation`. Inputs: `spec.md` (and `spec.yaml` if present),
`from-ai/research.md`, plus any `evaluation/` records the workspace holds.

Output: `reports/recommendation-YYYY-MM-DD.{md,typ,pdf}`.

**Never `from-ai/report.pdf`.** That path overwrote the previous report on every
run and contradicted the convention this workspace documents. Dated files
accumulate; `/procurement-tools:recompare` diffs against them.

Content of the report body, in this order:

1. **Headline** — the pick, in one or two sentences. Decisive.
2. **What was judged** — spec revision, candidate count, date the prices and
   availability were gathered.
3. **Top three** — #1 recommended, #2 runner-up, #3 budget alternative if a
   materially cheaper option still passes screening. Each with price and where
   to actually buy it, key specs, and why it placed there.
4. **Must-haves adherence** — each must-have against each finalist.
5. **Hard nos clearance** — each hard no, per-purchase and standing.
6. **What is not known** — every unknown that mattered to the ranking, and what
   would settle it. Use `unknown-box`; do not quietly resolve one.
7. **Also considered** — and why not.

### 5. Record it in the manifest

The skill does this, but confirm it happened:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" add-report . \
  --kind recommendation --path reports/recommendation-YYYY-MM-DD.md \
  --pdf reports/recommendation-YYYY-MM-DD.pdf --headline "<the pick>"
```

A report missing from `procurement.json` is invisible to `workspace.py index`.

### 6. Email if configured

If `spec.md` contains an email AND the Resend MCP is available:

- Attach the dated PDF
- Subject: "[Category] Recommendation Ready"
- Body: short summary with top pick + price + purchase link
- Send to the email in `spec.md`
- Confirm: "Report sent to [email]"

Sending mail reaches somebody else, so confirm before the first send in a
session even when an address is configured.

## Communication style

Be confident: "My recommendation is X." Not "You might consider X." Own the pick — that's what the user is here for.

## After recommendation

Offer next steps:

- "Report and links ready. Ready to buy?"
- "Want me to search for better pricing or monitor for sales?"
- "Want deeper research on any runner-up?"
