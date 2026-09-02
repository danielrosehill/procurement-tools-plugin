# Roadmap

Opened 2026-09-02. Status values: `planned`, `in progress`, `done`, `deferred`.

## Done in v2.3.0 — workspace identity and the report layer

Two related gaps found in the 2026-09-02 audit of end-to-end coverage. The
plugin covers spec definition, spec updates, market research, ranking against
spec and workspace provisioning well. Reporting and workspace identity are the
weak links.

### Workspace manifest — `done`

`schema/workspace.schema.json` written 2026-09-02. Defines `procurement.json`,
written to the root of every workspace whether it is a standalone repo or a
folder inside a parent repo, carrying a stable `PW-YYYYMMDD-XXXXXX` id.

The id is the point. It is what makes a later index or database possible: one
scan for `procurement.json` across a tree enumerates every procurement exercise
ever run, regardless of which skill provisioned it or where it landed.

Shipped: `scripts/workspace.py` with `init`, `validate`, `set`, `add-report`,
`purchase` and `index`; manifest writing in both `new-workspace` and
`workspace-folder`; private as the default visibility for every variant; 28
checks in `tests/test_workspace.py`.

`purchase` was added after a defect found in testing: the schema refuses a
`purchased` workspace with no `outcome`, and `set --status purchased` had no way
to supply one, so that status was unreachable. Status, closed date and outcome
now move together and `set` redirects.

### Unified dated reporting — `done`

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

## Fixed in v2.3.0 — defects found 2026-09-02

All four resolved; diagnosis retained in `debugging.md`. A fifth was found and
fixed along the way: `assets/report/base.typ` uses a font fallback chain, where
the old inline Typst hard-coded `Linux Libertine` and would fail outright on a
machine without it.

## Deferred

**Procurement index / database.** The manifest is being built to support it, but
nothing consumes it yet. `scripts/workspace.py index` emitting JSON is the
seam — deliberately a flat scan rather than a service, until there is enough
volume to justify one.

**GitHub template repo for the workspace scaffold.** Considered 2026-09-02 and
rejected for now; see `decisions.md`.
