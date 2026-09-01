---
name: evaluation-matrix
description: Generate the evaluation-criteria brief from a spec, judge candidates against it one requirement at a time, and render the conformance matrix. Use when candidates have to be checked against a defined requirement set rather than ranked, when several candidates need evaluating in parallel by subagents, when a shortlist needs auditing for what it actually rests on, or when the question is "does this meet A, B and C" rather than "which is best". Answers pass, fail, partial or unknown per requirement and never produces a score.
allowed-tools: Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Agent, Bash(python3 *), Bash(ls *), Bash(cat *), Bash(mkdir *)
---

# Evaluation matrix

Conformance checking, not ranking. Each candidate is judged against each
requirement independently and answered `pass`, `fail`, `partial` or `unknown`.
Nothing is weighted, nothing is totalled, and there is no winner column.

The reason is not squeamishness about recommending. It is that a weighted total
requires weights the user has not given, and once a total exists it is the only
thing anyone reads — which buries the one `fail` that actually decides the
purchase. The recommendation step comes afterwards, from a human looking at an
honest matrix. `/procurement-tools:recommend` is where a recommendation belongs.

Requires a `spec.yaml` — see the `spec-as-code` skill.

## 1. Generate the criteria brief

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec_tools.py" criteria spec.yaml -o evaluation/criteria.md
```

This is the backing document handed to whoever does the research. It restates
each requirement with the evidence class that settles it, what counts, what does
not, and the verdict rules. It is generated, not written — edit `spec.yaml` and
regenerate, never edit `criteria.md` directly.

Regenerate it after every spec revision. A subagent briefed from a stale
criteria file will produce records that validate cleanly and answer the previous
version of the question.

## 2. Evaluate candidates — in parallel

**One JSON record per candidate**, at `evaluation/conformance/<candidate-id>.json`,
conforming to `${CLAUDE_PLUGIN_ROOT}/schema/conformance.schema.json`.

The file-per-candidate layout exists so this step can fan out. Candidates do not
depend on one another, so launch a subagent per candidate — in a single message,
not one at a time — each briefed with `evaluation/criteria.md`, the candidate,
and the path to write. They never touch the same file, so there is nothing to
coordinate.

Brief each one with:

- The full text of `evaluation/criteria.md` — it is self-contained by design.
- The candidate: name, manufacturer, part number, **region**.
- The instruction to check the `must` and `must-not` requirements first and stop
  on a confirmed `fail`. There is no point researching the remaining fifteen
  requirements of a disqualified candidate.
- The schema path, and the reminder that `unknown` is an acceptable answer and a
  guess is not.

Treat what comes back as a report to be checked, not as fact. Spot-check the
load-bearing cells — the ones that disqualify a candidate or clear a
frontrunner — against the source the record cites. A subagent can be confidently
wrong in exactly the way a retail listing is.

## 3. Verdict discipline

| Verdict | Bar |
|---|---|
| `pass` | The evidence class named in the requirement, plus the source in the record. |
| `fail` | The same bar, negative. |
| `partial` | Met under a condition, **and the condition is written in the note**. A `partial` with no stated condition is an `unknown`. |
| `unknown` | Not established to that standard. `resolves_to` says what would settle it. |

Three rules that the validator enforces, because all three have produced wrong
shortlists:

- **A disqualifying requirement cannot be settled on a retail listing, a review,
  or an inference.** If that is all you have, the cell is `unknown`. The
  validator errors on this rather than warning.
- **Sources that disagree produce `unknown`, with both sources kept** in
  `conflicting_sources`. Never resolve a conflict by taking the number that
  suits the candidate you like.
- **A `pass` carries its observed value**, not just the verdict. The number is
  what a later reader re-checks; a bare `pass` is unauditable.

Where a datasheet was retrieved by `spec-sheet-retrieval`, cite the document and
its `doc_revision`, and point `candidate.datasheet_ref` at the record. The
validator warns on a datasheet citation with no revision, because makers replace
documents at the same URL.

## 4. Validate before rendering

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec_tools.py" validate-conformance evaluation/conformance/*.json --spec spec.yaml
```

Catches: a missing cell, a cell for a requirement that does not exist, a bare
`partial`, a sourceless `pass`, a weak source on a disqualifying requirement,
and a record evaluated against a superseded spec revision.

A stale record is a **warning**, not an error, and it is a warning you must act
on rather than pass over: re-check the cells the revision actually touched, then
bump `spec.revision` in the record. Do not bump it without re-checking; that
converts a stale answer into a fresh-looking one.

## 5. Render

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec_tools.py" matrix spec.yaml evaluation/conformance -o evaluation/matrix.md
```

The rendered matrix reads the field as well as the rows, which is the part
people miss:

- **A column that is `unknown` everywhere** — no maker publishes it. The buyer
  cannot compare on it in advance. Either drop the requirement or resolve it by
  asking vendors.
- **A column nothing clears** — an unmet requirement. The market does not serve
  it. That is a finding, not a failed search.
- **A column everything clears** — not a requirement, a property of the
  category. It is filtering nothing.
- **No candidate clearing everything** — reported as the headline. Note the
  difference between *every candidate has a confirmed failure* and *no candidate
  has been confirmed yet*; the renderer distinguishes them and so should you.

Column-level readings only appear once there are at least three candidates. Two
rows are not a field, and a pattern read off two rows is noise.

## 6. Report

Lead with: how many candidates clear every disqualifying requirement, which
requirements are doing the eliminating, and what remains open. Point at
`evaluation/matrix.md` rather than pasting it.

If nothing clears, say so plainly and do not soften it into a nearest-fit
recommendation. "Nothing on the market meets this" is a complete answer, and it
is usually the most valuable one the process produces.

## Relationship to `mkt-matrix`

`/procurement-tools:mkt-matrix` is the same discipline applied to a **market
survey** — a whole field, in prose, in a landscape repo, deliberately without a
purchase attached. This skill is the machine-readable version for a **specific
purchase**: fewer candidates, more evidence per cell, structured output that
BOM lines and RFQs can reference by id. Use `mkt-matrix` to map a market, this
to settle a buy. They do not share a file format and should not be mixed inside
one repo.
