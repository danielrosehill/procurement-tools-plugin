# Roadmap

Opened 2026-09-02. Status values: `planned`, `in progress`, `done`, `deferred`.

## In progress — workspace identity and the report layer

Two related gaps found in the 2026-09-02 audit of end-to-end coverage. The
plugin covers spec definition, spec updates, market research, ranking against
spec and workspace provisioning well. Reporting and workspace identity are the
weak links.

### Workspace manifest — `in progress`

`schema/workspace.schema.json` written 2026-09-02. Defines `procurement.json`,
written to the root of every workspace whether it is a standalone repo or a
folder inside a parent repo, carrying a stable `PW-YYYYMMDD-XXXXXX` id.

The id is the point. It is what makes a later index or database possible: one
scan for `procurement.json` across a tree enumerates every procurement exercise
ever run, regardless of which skill provisioned it or where it landed.

Remaining:

- `scripts/workspace.py` — `init`, `validate`, `set`, `add-report`, and `index`.
  `index` is the scan a future database would ingest.
- `new-workspace` writes the manifest; flip its GitHub default to **private for
  every variant** (currently public except `market-landscape`). A procurement
  workspace states what someone plans to buy and what they will pay.
- `workspace-folder` writes the same manifest with `mode: folder` and a `parent`
  block, so folder-mode decisions are enumerable on the same footing as repos.
- Tests in `tests/test_workspace.py`.

### Unified dated reporting — `planned`

Three tracks end three different ways today, and only one of them does what a
dated report should:

| Track | Ends at | Dated? |
| --- | --- | --- |
| market-landscape | `/mkt-report` → `outputs/landscape-YYYY-MM-DD.{md,typ,pdf}` | Yes — this is the model |
| general-purchasing | `/recommend` → `from-ai/report.{typ,pdf}` | **No** — overwritten each run |
| spec-conformance | `market-evaluator` → `evaluation/recommendation.md` | **No PDF at all** |

Planned: one `procurement-report` skill that takes whichever artefacts exist,
renders `reports/<kind>-YYYY-MM-DD.{md,typ,pdf}`, never overwrites, appends a
record to `procurement.json`, and carries requirement ids plus datasheet
revisions into the document so a claim in a PDF traces back to its source.

Also: extract the Typst preamble, currently duplicated three times, into a
shared asset so the three report kinds look like one family.

## Planned — defects found 2026-09-02

Recorded in full in `debugging.md`. Summary:

- `/recommend` writes an undated path that contradicts the convention its own
  workspace template documents.
- `market-evaluator` is not referenced by `technical-sourcing` at all, so the
  pipeline skill routes past the ranking step added in v2.2.0.
- `technical-sourcing` step 7 hands to `/recommend`, whose preconditions cannot
  be satisfied in a spec-as-code workspace.

## Deferred

**Procurement index / database.** The manifest is being built to support it, but
nothing consumes it yet. `scripts/workspace.py index` emitting JSON is the
seam — deliberately a flat scan rather than a service, until there is enough
volume to justify one.

**GitHub template repo for the workspace scaffold.** Considered 2026-09-02 and
rejected for now; see `decisions.md`.
