# The technical-sourcing artefact chain

Normative reference for the files the technical-sourcing skills read and write.
An agent opening a purchase repo cold should be able to work out what state the
investigation is in from this page and a directory listing.

Everything here is composable by design: each artefact is produced by one skill,
consumed by others, and joined to the rest by **ids that are never reused**.

## Files

| Path | Written by | Schema | Purpose |
|---|---|---|---|
| `procurement.json` | `new-workspace`, `workspace-folder`, `scripts/workspace.py` | `schema/workspace.schema.json` | Workspace identity: stable `PW-` id, variant, mode, status, spec revision, report trail. Present in every workspace, repo or folder. |
| `spec.md` | `/procurement-tools:define-spec`, `:intake` | — | Prose spec: context, rationale, history. For a person. |
| `search-terms.md` | `/procurement-tools:define-spec` | — | Search vocabulary by register. |
| `spec.yaml` | `spec-as-code` | `schema/spec.schema.json` | Requirements with stable `REQ-nnn` ids. For a machine. |
| `spec-<variant>.yaml` | `spec-variants` | `schema/spec.schema.json` | Parallel either/or bars for the same purchase. Replaces `spec.yaml` once branched. |
| `spec-variants.md` | `spec_tools.py variant-diff` | — | **Generated.** What actually differs between the variants. |
| `data/datasheets/<mfr>-<pn>.json` | `spec-sheet-retrieval` | `schema/datasheet.schema.json` | Published values with the document and revision behind them. |
| `data/equivalence/<family>.json` | `part-number-equivalence` | `schema/equivalence.schema.json` | Which part numbers name the same product, with confidence. |
| `evaluation/criteria.md` | `spec_tools.py criteria` | — | **Generated.** The brief handed to research subagents. |
| `evaluation/conformance/<candidate>.json` | `evaluation-matrix` | `schema/conformance.schema.json` | One candidate judged against one revision of one variant. With variants, nested under `conformance/<variant>/`. |
| `evaluation/matrix.md` | `spec_tools.py matrix` | — | **Generated.** The conformance matrix and what it says about the field. One per variant. |
| `evaluation/recommendation.md` | `market-evaluator` | — | The ranked call: top three with price and sourcing, then category picks. One per variant. |
| `bom.yaml` | `bom-build` | `schema/bom.schema.json` | Line items with stable `LINE-nnn` ids. |
| `rfq/RFQ-YYYY-NNN.json` | `rfq-package` | *external — see below* | Supplier request, in the `dsrholdings-rfq` renderer's input shape. |
| `price-watchlist.yaml`, `data/price-scans/` | `price-scan` | `examples/price-watchlist.example.yaml` | What it costs delivered, today. |
| `reports/<kind>-YYYY-MM-DD.{md,typ,pdf}` | `procurement-report` | — | The dated deliverable. Never overwritten. Markdown twin always exists; PDF only if Typst is present. |
| `reports/base.typ` | `procurement-report` | — | Copy of the shared styling, so the workspace recompiles without the plugin. |

Two files are **generated and must not be hand-edited**: `evaluation/criteria.md`
and `evaluation/matrix.md`. Edit `spec.yaml` or the conformance records and
regenerate. A hand-edited criteria file produces conformance records that
validate cleanly and answer the wrong question.

## Join keys

```
procurement.json     PW-20260902-A1B2C3 ─▶ identifies the workspace itself; survives
                                          renames, moves and folder→repo promotion.
                                          The key any later index or database uses.

spec.yaml            REQ-001 ─┬─▶ conformance.cells[].req
                              ├─▶ bom.lines[].spec_ref  ("spec-id@variant#REQ-001,REQ-004")
                              └─▶ datasheet.specs[].req

spec identity        id + variant + revision ──▶ conformance.spec.{id,variant,revision}

bom.yaml             LINE-001 ──▶ supplier quotes, RFQ line order

conformance.json     candidate.datasheet_ref    ──▶ data/datasheets/*.json
                     candidate.equivalence_ref  ──▶ data/equivalence/*.json
```

Ids are allocated sequentially and **never reused**, including after a
requirement is retired or a line is dropped. A conformance record from six weeks
ago cites `REQ-004`; if `REQ-004` later means something else, that record
silently becomes a false statement about a product.

Retirement, not deletion: a requirement gets `retired: true` and stays in the
file. `validate-conformance` stops demanding a cell for it, and old records
remain readable.

## Revisions

`spec.yaml` and `bom.yaml` both carry an integer `revision` and an append-only
`history`. Conformance records pin the spec revision they were judged against.

That pinning is the whole point: `validate-conformance` reports a record
evaluated against a superseded revision of the **same variant** as **stale**. The correct response is to
re-check the cells the revision actually touched and then bump the record — not
to bump the record, which converts a stale answer into a fresh-looking one.

## Variants: the second axis

A spec's identity is the triple **`id` + `variant` + `revision`**.

- **`id`** names the purchase. Shared by every variant of it.
- **`variant`** is a parallel, either/or branch — `budget` against `premium`.
  Optional, and **absent for the ordinary case** of one spec with iterative
  revisions, which is unchanged by any of this.
- **`revision`** moves linearly *within* one variant, independently of siblings.
  `budget r3` and `premium r1` are both current.

A revision supersedes what came before it. A variant supersedes nothing — it
stands beside its siblings until one is chosen.

```
spec.yaml                    no variants: one spec, iterative revisions
spec-budget.yaml   r3   ─┐
spec-premium.yaml  r1   ─┴─  same id, parallel bars, independent revisions
```

Once branched, a bare `spec.yaml` must not survive alongside variant files —
which spec is in force would be undefined. `validate-variants` errors on it.

**Requirement ids name the same subject in every variant.** `REQ-002` is setpoint
accuracy in both; only the threshold moves. This is what lets one candidate be
judged against several variants without re-researching it, and what makes
`variant-diff` readable. Reusing an id for a different `parameter` across
variants is an **error**: every cross-variant comparison downstream would
silently become meaningless. A requirement needed by only one variant gets a new
id and is simply absent from the others.

Conformance records therefore pin the variant as well as the revision, and a
record naming a different variant is an **error rather than a staleness warning** —
the same datasheet value can be a `pass` under one bar and a `fail` under
another, so the record belongs in a different matrix, not lower down this one.

```bash
python3 scripts/spec_tools.py validate-variants .
python3 scripts/spec_tools.py variant-diff . -o spec-variants.md
```

See the `spec-variants` skill for branching, diffing and converging.

## Validation gates

Run at each artefact boundary. Each catches a class of error that is invisible
downstream, because a dangling reference reads as a completed check.

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/spec_tools.py"

python3 "$S" validate-spec spec.yaml
python3 "$S" criteria spec.yaml -o evaluation/criteria.md
python3 "$S" validate-conformance evaluation/conformance/*.json --spec spec.yaml
python3 "$S" matrix spec.yaml evaluation/conformance -o evaluation/matrix.md
python3 "$S" validate-bom bom.yaml --spec spec.yaml
python3 "$S" rfq bom.yaml --vendor "Name" --number RFQ-2026-001 -o rfq/RFQ-2026-001.json
```

Exit codes: `0` clean, `1` problems found (all reported, not just the first),
`2` file missing or bad argument, `3` PyYAML missing.

The script checks structure and cross-references and renders. It never decides
whether a product meets a requirement — a script that guessed at that would
launder a guess into a table.

## Why one file per candidate

`evaluation/conformance/` holds one JSON file per candidate rather than one
shared table, and `data/datasheets/` one per part number. Candidates are
independent, so these steps fan out to concurrent subagents — and concurrent
agents writing to one shared file collide. The per-candidate layout is what
makes parallel evaluation safe without coordination.

`spec_tools.py matrix` assembles the shared view at read time, which is also why
`matrix.md` is generated rather than maintained.

## External coupling: the RFQ schema

`spec_tools.py rfq` emits JSON conforming to
[`dsrholdings-rfq`](https://github.com/danielrosehill/dsrholdings-rfq-plugin)'s
`schema/rfq.schema.json`, so the output can be rendered to a branded PDF without
a translation step.

That schema is `additionalProperties: false`. Nothing procurement-tools specific
can travel inside the document — no line ids, no spec references, no
provenance — so those stay in `bom.yaml`. **Adding a field to the generated JSON
requires adding it to the renderer's schema first**, or the document is
rejected. `tests/test_spec_tools.py` pins the permitted key sets; if the
upstream schema changes, that test is what has to move.

Verified against `dsrholdings-rfq` schema as of 2026-09-01.
