# The technical-sourcing artefact chain

Normative reference for the files the technical-sourcing skills read and write.
An agent opening a purchase repo cold should be able to work out what state the
investigation is in from this page and a directory listing.

Everything here is composable by design: each artefact is produced by one skill,
consumed by others, and joined to the rest by **ids that are never reused**.

## Files

| Path | Written by | Schema | Purpose |
|---|---|---|---|
| `spec.md` | `/procurement-tools:define-spec`, `:intake` | — | Prose spec: context, rationale, history. For a person. |
| `search-terms.md` | `/procurement-tools:define-spec` | — | Search vocabulary by register. |
| `spec.yaml` | `spec-as-code` | `schema/spec.schema.json` | Requirements with stable `REQ-nnn` ids. For a machine. |
| `data/datasheets/<mfr>-<pn>.json` | `spec-sheet-retrieval` | `schema/datasheet.schema.json` | Published values with the document and revision behind them. |
| `data/equivalence/<family>.json` | `part-number-equivalence` | `schema/equivalence.schema.json` | Which part numbers name the same product, with confidence. |
| `evaluation/criteria.md` | `spec_tools.py criteria` | — | **Generated.** The brief handed to research subagents. |
| `evaluation/conformance/<candidate>.json` | `evaluation-matrix` | `schema/conformance.schema.json` | One candidate judged against one spec revision. |
| `evaluation/matrix.md` | `spec_tools.py matrix` | — | **Generated.** The conformance matrix and what it says about the field. |
| `bom.yaml` | `bom-build` | `schema/bom.schema.json` | Line items with stable `LINE-nnn` ids. |
| `rfq/RFQ-YYYY-NNN.json` | `rfq-package` | *external — see below* | Supplier request, in the `dsrholdings-rfq` renderer's input shape. |
| `price-watchlist.yaml`, `data/price-scans/` | `price-scan` | `examples/price-watchlist.example.yaml` | What it costs delivered, today. |

Two files are **generated and must not be hand-edited**: `evaluation/criteria.md`
and `evaluation/matrix.md`. Edit `spec.yaml` or the conformance records and
regenerate. A hand-edited criteria file produces conformance records that
validate cleanly and answer the wrong question.

## Join keys

```
spec.yaml            REQ-001 ─┬─▶ conformance.cells[].req
                              ├─▶ bom.lines[].spec_ref  ("spec-id#REQ-001,REQ-004")
                              └─▶ datasheet.specs[].req

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
evaluated against a superseded revision as **stale**. The correct response is to
re-check the cells the revision actually touched and then bump the record — not
to bump the record, which converts a stale answer into a fresh-looking one.

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
