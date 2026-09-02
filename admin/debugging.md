# Known defects and debugging notes

Open defects first. Each entry states the symptom, the actual cause, and where
it was verified — so the next person does not repay the diagnosis cost.

## Open

### `/recommend` writes an undated path its own template forbids

**Symptom.** Re-running `/recommend` silently destroys the previous report.

**Cause.** `commands/recommend.md:3` and `:174` write `from-ai/report.typ` and
`from-ai/report.pdf`. But `template/general-purchasing/CLAUDE.md:332` documents
the convention as `from-ai/reports/report-YYYY-MM-DD.{typ,pdf,md}`. The command
contradicts the workspace it runs inside.

**Compounding.** `/recompare` does it correctly — it writes dated files to
`from-ai/recommendations/` and explicitly says "never overwrite an existing
dated file — history matters" — and then, at `commands/recompare.md:36`, offers
to hand off to `/recommend`, which overwrites. Verified 2026-09-02.

### `market-evaluator` is not wired into `technical-sourcing`

**Symptom.** The ranking step added in v2.2.0 never runs as part of the pipeline
it was built for.

**Cause.** `grep -rn market-evaluator` finds it in `README.md`,
`docs/artefact-chain.md` and its own `SKILL.md` — and **nowhere in**
`skills/technical-sourcing/SKILL.md`. Step 7 of that skill routes straight to
`/procurement-tools:recommend` instead. Verified 2026-09-02.

### `technical-sourcing` step 7 hands to a command that cannot run there

**Symptom.** Following the pipeline to its end fails on a missing input.

**Cause.** `/recommend` declares preconditions `spec.md` at repo root **and**
`from-ai/research.md`. A spec-as-code workspace has `spec.yaml` and
`evaluation/conformance/*.json`, and no `from-ai/` tree at all.

The failure is unusually confusing because it **half** resolves: `define-spec`
does produce `spec.md`, so the first precondition passes and only the second
fails. That reads as "research hasn't been run yet" rather than "this command
belongs to a different track". Verified 2026-09-02.

### Typst preamble duplicated three times

`commands/recommend.md`, `commands/mkt-report.md` and
`template/general-purchasing/CLAUDE.md:162` each inline their own. They will
drift, and the three report kinds will stop looking like one family.

## Resolved

*(none yet)*

## Ruled out — do not re-investigate

**`spec.md` → `spec.yaml` has no bridge.** It does. The handoff is documented in
`skills/spec-as-code/SKILL.md` at lines 33, 40 and 133: `define-spec` produces
the prose `spec.md`, `spec-as-code` reads it, and both are committed side by
side. Checked 2026-09-02 while auditing the spec track; the two formats are
deliberate, not an accident.

**`__pycache__` and `.pytest_cache` are untracked but absent from `git status`.**
Not a repo misconfiguration — there is no root `.gitignore` and none is needed.
`git check-ignore -v` traces both to `/home/daniel/.gitignore_global:4`. The
same global file also ignores anything named `private` or `*private*/`, in every
repo, which is why a gitignored scratch area needs no per-repo setup. Confirmed
2026-09-02.
