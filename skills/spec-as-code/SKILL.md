---
name: spec-as-code
description: Turn a purchase requirement into a versioned, machine-readable spec.yaml with stable requirement ids, so that evaluation, BOM lines and RFQs all reference the same requirements instead of restating them in prose. Use when a purchase has enough requirements that a paragraph stops being enough, when requirements are changing as research proceeds and the changes need a record, or when subagents will be judging candidates and need something unambiguous to judge against. Also use to amend an existing spec — bumping a revision, retiring a requirement, relaxing a threshold.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(python3 *), Bash(ls *), Bash(cat *), Bash(mkdir *), Bash(git log *), Bash(git diff *)
---

# Spec as code

`spec.md` is prose for a person. `spec.yaml` is the same requirements in a form
a subagent can be handed, a script can validate, and a diff can show the change
in. This skill produces and maintains the second one.

The reason to bother is not tidiness. It is that a purchase spec **moves** —
research turns up a distinction you did not know existed, a threshold turns out
to exclude the whole market, a requirement you thought was one requirement is
two. When that happens without a version, every judgement already made becomes
uninterpretable: you cannot tell whether a candidate was rejected under the old
rule or the new one. Requirement ids and revisions fix that, and cost almost
nothing.

Schema: `${CLAUDE_PLUGIN_ROOT}/schema/spec.schema.json`.
Worked example: `${CLAUDE_PLUGIN_ROOT}/examples/spec.example.yaml`.

## When this is the wrong tool

If the user knows exactly what they are buying and just wants a price, skip it —
this is overhead on a decision that does not need it. It earns its keep when
requirements are genuinely contested, when candidates will be evaluated by
someone other than the person who set the requirements, or when the purchase is
one line of a larger BOM.

If the user does not yet know what the thing is *called*, run
`/procurement-tools:define-spec` first. That produces `spec.md` and the search
vocabulary; this converts what it settled into the machine-readable form.

## Writing a new spec

### 1. Take the requirements from wherever they already are

`spec.md` in the repo, an intake conversation, a `define-spec` output, or the
user talking. Do not re-interview if the answers already exist on disk.

### 2. Split every requirement until each one has a single answer

The commonest defect is a compound requirement — "Bluetooth that works with my
app" — which cannot be answered `pass` or `fail` because it is two questions
with different evidence. Split it: the radio exists (datasheet), and the app
speaks its protocol (the app's compatibility list). Splitting is not pedantry;
compound requirements are how a candidate gets a `pass` on the half that was
easy to check.

### 3. Classify each one

| `kind` | Meaning | Effect |
|---|---|---|
| `must` | Required. | A `fail` disqualifies. |
| `must-not` | Disqualifying if present. | A confirmed presence disqualifies. |
| `nice` | Preference. | Never disqualifies, never scores, breaks ties. |

Push back on an over-populated `must` list. Every `must` is a slice of the
market removed, and users routinely promote incidental attributes of the example
they were shown. Ask, per requirement: *if this were absent and everything else
were right, would you refuse to buy it?* If the answer is "no, but I'd prefer",
it is `nice`.

### 4. Give each requirement a `verify` class and an `evidence` line

This is the field that makes the spec usable by someone who was not in the
conversation. `verify` names the evidence class that **settles** the
requirement; `evidence` says what specifically to look for. Anything weaker
leaves the cell `unknown` rather than passing it.

| `verify` | Settled by |
|---|---|
| `datasheet` | The manufacturer's published technical data. |
| `manual` | The operating manual — function lists, modes, limits the datasheet omits. |
| `standard` | A named standard and clause the product claims conformity to. |
| `vendor-confirmation` | A direct answer from the maker or an authorised distributor. |
| `third-party-test` | An independent measurement, or a compatibility list maintained by the other side of an integration. |
| `hands-on` | Only answerable by using it. Say so — it means the purchase carries this risk. |
| `review-consensus` | Multiple independent users agreeing. Weak; acceptable only for `nice`. |
| `inspection` | Visible in photographs or the product itself. |

Where a requirement has a known trap, fill `rejects` with the evidence that
looks sufficient and is not. That field is what stops the next agent — or the
next you — passing a requirement off a retail bullet point.

### 5. Fill `out_of_scope` before you gather candidates

Everything the example product had that is not required. Written afterwards it
is useless, because by then the frontrunner's incidental features feel like
requirements. This is the single highest-value field in the file and the one
most often left empty.

### 6. Validate

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec_tools.py" validate-spec spec.yaml
```

Fix the errors. Read the warnings and decide — a missing rationale on a
disqualifying requirement is a warning because it is sometimes fine and often
the sign of a requirement nobody can justify.

## Amending an existing spec

Requirements are **retired, never deleted**, and ids are **never reused**. A
conformance record written months ago cites `REQ-004`; if `REQ-004` later means
something else, that record silently becomes a lie.

To change a spec:

1. Bump `revision`.
2. Add a `history` entry with the change **and the reason** — the reason is what
   you will want in three weeks when deciding whether to relax it again.
3. To remove a requirement, set `retired: true`, `retired_in`, and
   `retired_reason`. Leave everything else in place.
4. To change a threshold, edit it in place. The revision bump is what records it.
5. Re-run `validate-spec`, then re-run `criteria`.

Then say plainly which existing conformance records the change invalidates.
`validate-conformance` will flag them as stale, but the user should hear it from
you at the moment of the edit, not two steps later.

**Relaxing a requirement is a decision, not an edit.** When research shows a
`must` excludes the entire field, do not quietly lower it. Report the finding —
"nothing on the market does this at this price" — and let the user decide
whether to relax, raise the budget, or stop. A silently relaxed spec produces a
recommendation that answers a question nobody asked.

## Where the file lives

`spec.yaml` at the repo root, alongside the prose `spec.md`. Both are committed;
the YAML is the one other artefacts reference by id, the prose is the one a
person reads. Do not maintain requirements in both — keep the prose to context,
rationale and history, and let it point at the YAML for the requirement list.

## Hands off to

- `evaluation-matrix` — generates the criteria brief from this file and judges candidates against it.
- `bom-build` — BOM lines reference this spec by id and requirement ids.
- `spec-sheet-retrieval` — a spec with `verify: datasheet` requirements tells that skill exactly which parameters to go and find.
