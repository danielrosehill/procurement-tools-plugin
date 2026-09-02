---
name: procurement-report
description: Render a dated, never-overwritten report (markdown + PDF) from whichever spec, conformance and pricing artefacts a workspace holds.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(python3 *), Bash(typst *), Bash(ls *), Bash(cat *), Bash(cp *), Bash(mkdir *), Bash(date *)
---

# Procurement report

One report step for every track in this plugin. It reads what the workspace
actually has rather than demanding a fixed set of inputs, and it always writes
a **dated file that never overwrites a previous one**.

Output: `reports/<kind>-YYYY-MM-DD.md`, plus `.typ` and `.pdf` unless
`--md-only`. Shared styling: `${CLAUDE_PLUGIN_ROOT}/assets/report/base.typ`.

## Why dating is not cosmetic

A procurement report is a claim about a market at a moment. Prices move, stock
moves, manufacturers revise datasheets, and the spec itself gets revised as
research teaches you what to ask for. A report that overwrites its predecessor
destroys the only evidence of what you believed when you decided — which is
exactly what you need when the thing arrives and does not fit.

So: dated filename, spec revision recorded in the header, and an append-only
record in `procurement.json`. Never `report.pdf`.

## Kinds

Pick from the artefacts present, or take the kind the caller passed.

| Kind | Answers | Wants |
| --- | --- | --- |
| `recommendation` | Which should I buy | `evaluation/recommendation.md`, or research plus a spec |
| `conformance` | Which qualify, and on what evidence | `evaluation/matrix.md`, `evaluation/conformance/*.json` |
| `landscape` | What exists in this market | `landscape/`, `candidates/` |
| `estimate` | What will this cost | BOM or rig components with prices |
| `rfq` | What am I asking suppliers to quote | `bom.yaml` |

A `conformance` report is a legitimate final deliverable. If nothing cleared
the spec, that **is** the finding — report it as the headline rather than
promoting the nearest miss into a recommendation.

## Procedure

### 1. Survey what exists

Do not assume a track. Look:

```bash
ls spec.yaml spec.md spec-*.yaml bom.yaml 2>/dev/null
ls evaluation/ evaluation/conformance/ 2>/dev/null
ls from-ai/ landscape/ candidates/ outputs/ 2>/dev/null
cat procurement.json 2>/dev/null
```

Then say which kind you are producing and on what basis. If the workspace holds
enough for two kinds, ask — a conformance report and a recommendation answer
different questions and the caller usually wants one specific one.

### 2. Establish the spec revision you are judging against

From `spec.yaml` `revision`, or `procurement.json` `spec.revision`. It goes in
the header. A reader must be able to tell a current report from one written
against a bar that has since moved.

If conformance records reference a **superseded** revision, say so in the
report rather than silently reporting them as current. `spec_tools.py
validate-conformance` flags this; run it before rendering:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec_tools.py" validate-conformance \
  evaluation/conformance/*.json --spec spec.yaml
```

### 3. Write the markdown first

`reports/<kind>-YYYY-MM-DD.md` is the source of truth and always exists —
Typst may be missing, and a missing PDF must never mean a missing report.

Structure, adapted to kind:

1. **Headline** — the answer in one or two sentences. The pick, or the finding
   that nothing qualified. Decisive.
2. **What was judged and against what** — spec revision, candidate count, dates
   the evidence was gathered.
3. **The finding** — ranked picks, or the conformance matrix, or the field.
4. **Evidence per claim** — requirement ids (`REQ-001`) against verdicts, each
   citing a source. Reference `evaluation/matrix.md` rather than re-deriving it.
5. **What is not known** — every `unknown` that mattered, and what would settle
   it. Never quietly resolved.
6. **What was not covered** — regions, categories, source types out of scope.

**Carry ids, not just prose.** `REQ-001` in the report and `REQ-001` in the spec
are the same string, so a reader can walk from a sentence in a PDF back to the
requirement and the datasheet that settled it. That traceability is the whole
point of the artefact chain; a report that paraphrases requirements breaks it.

**Unknowns survive.** A `?` in the matrix is a `?` in the report. Use the
`unknown-box` helper so it is visually distinct from a finding.

### 4. Render the PDF

Copy the shared styling next to the report, so the workspace can recompile
years later without this plugin installed:

```bash
mkdir -p reports
cp "${CLAUDE_PLUGIN_ROOT}/assets/report/base.typ" reports/base.typ
```

Write `reports/<kind>-YYYY-MM-DD.typ` opening with:

```typst
#import "base.typ": *
#show: report.with(
  title: "<what was bought or surveyed>",
  kind: "Recommendation",
  date: "2026-09-02",
  meta: (("Spec", "spec.yaml rev 3"), ("Candidates", "7"), ("Workspace", "PW-...")),
  footer-note: "<workspace id>",
)
```

Helpers available: `verdict("pass"|"fail"|"partial"|"unknown")`,
`conformance-table(rows, candidate: "...")`, `unknown-box[...]`, `finding[...]`.

```bash
cd reports && typst compile <kind>-YYYY-MM-DD.typ <kind>-YYYY-MM-DD.pdf
```

`typst` warns `unknown font family` for whichever families the machine lacks.
That is the fallback chain working as designed, not an error — the compile
still succeeds. Only a non-zero exit is a failure.

If `typst` is absent, say so, keep the markdown and the `.typ`, and tell the
user `apt install typst`. Do not treat it as a failed report.

### 5. Record it

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" add-report . \
  --kind recommendation \
  --path reports/recommendation-2026-09-02.md \
  --pdf reports/recommendation-2026-09-02.pdf \
  --headline "<the answer in one line>" \
  --candidates 7
```

This appends to `procurement.json` and stamps the spec revision. A report that
is not recorded there is invisible to `workspace.py index`, which is how any
later index or database finds it.

If there is no `procurement.json`, the workspace predates the manifest. Offer
to run `workspace.py init`; do not fail the report over it.

### 6. Never overwrite

If `reports/<kind>-YYYY-MM-DD.*` already exists, a report was already written
today. Do not clobber it. Either append a suffix (`-b`) or ask — the previous
one may be the version that was sent to somebody.

## Anti-patterns

**Do not resolve an unknown to make the report tidier.** A `pass` inferred from
a retail bullet point is indistinguishable from a verified one two steps later,
and this document is where that becomes permanent.

**Do not rank in a `conformance` report.** The matrix answers who qualifies;
`market-evaluator` is where ranking is allowed. Mixing them buries the
trade-off the matrix exists to expose.

**Do not quote a price without its source and date.** Shop prices come from
`price-scan` on the user's own egress; a price fetched from the wrong country
is a real number for the wrong market.
