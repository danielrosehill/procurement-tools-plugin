---
name: spec-variants
description: Run several parallel either/or versions of one spec — a budget bar and a premium bar for the same purchase — each independently versioned, and diff what actually differs between them. Use when the answer is "it depends how much we want to spend", when a requirement could reasonably be set at two levels and you want to see what each level finds on the market, when someone asks for a cheap option and a nice option, or when converging variants back to one after the market has answered. Not needed for the ordinary case of one spec with iterative revisions.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(python3 *), Bash(ls *), Bash(cat *), Bash(cp *), Bash(git mv *), Bash(mv *)
---

# Spec variants

Most purchases need one spec that gets revised as research proceeds. That is the
default and this skill is not involved in it — `spec-as-code` covers it.

Sometimes the requirement genuinely forks. "Here is a budget one, here is one
that would be nicer but more expensive" is not indecision; it is two real
questions, and the market answers them differently. Running both and comparing
what each surfaces is the point.

## The two axes

Identity is the triple **`id` + `variant` + `revision`**, and the axes are
independent:

- **`id`** names the purchase. Every variant of one purchase shares it.
- **`variant`** is a parallel, either/or branch — `budget`, `premium`. Siblings,
  never a chain.
- **`revision`** moves linearly *within* one variant. Budget can be at r3 while
  premium is at r1; neither is ahead of the other.

Written out: `bench-psu-2026-09@budget r3`. With no variants it is just
`bench-psu-2026-09 r3`, exactly as before.

**Both axes matter and they are not interchangeable.** A revision supersedes
what came before it. A variant does not supersede anything — it stands beside
its siblings until one is chosen.

## The rule that makes variants work

**A requirement id names the same subject in every variant.** `REQ-002` is
setpoint accuracy in budget and in premium; what differs is the threshold —
`≤ 0.5%` against `≤ 0.1%`.

This is what makes the diff readable, and what lets one candidate be judged
against several variants without researching it twice: the evidence is the same,
only the bar moves.

`validate-variants` enforces it. Reusing an id for a different `parameter` across
variants is an **error**, not a warning, because every cross-variant comparison
downstream silently becomes meaningless. If a variant needs a requirement its
siblings do not have, allocate a **new id** and simply omit it from the others —
`REQ-007` existing only in premium is normal and reads correctly in the diff.

## Files

With no variants:

```
spec.yaml
```

Once branched, **every** spec file names its variant and the bare `spec.yaml`
must not survive:

```
spec-budget.yaml
spec-premium.yaml
```

A leftover `spec.yaml` beside variant files is ambiguous about which spec is in
force, so branching *moves* the original rather than copying it. `validate-variants`
errors if it finds a file with no variant sitting alongside files that have one.

## 1. Branch an existing spec

```bash
git mv spec.yaml spec-budget.yaml
cp spec-budget.yaml spec-premium.yaml
```

Then in **each** file set:

- `variant:` — the slug (`budget`, `premium`)
- `variant_label:` — how it should read as a column header
- `variant_rationale:` — **the trade-off this variant takes, in one sentence.**
  This is the only thing a reader compares variants on, so it carries the weight.
  "Cheapest unit that still clears the safety floor; accept slower transient
  response" is useful. "The cheap one" is not.
- `variant_of:` — on the new sibling only, naming what it branched from. Provenance
  only; nothing walks it.

Reset `revision` to 1 on the new sibling, and start it a fresh `history`. It has
its own life from here: the original's revision history describes a spec that no
longer exists under that name.

On each requirement whose bar you move, set **`variant_note`** — why this variant
sets it differently. That note is what you read when converging later, and it is
the difference between a diff you can act on and a diff that just shows two
numbers.

## 2. Validate the family

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec_tools.py" validate-variants .
```

Takes files or a directory. Validates each variant on its own, then checks the
family: shared `id`, no duplicate variant slugs, every file carries a variant,
and requirement ids naming a consistent subject throughout.

## 3. Diff them

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec_tools.py" variant-diff . -o spec-variants.md
```

Produces three groups: requirements **identical** across variants, requirements
where the **bar differs**, and requirements **present in some variants only** —
plus the `variant_note` for each divergence.

The diff deliberately ignores prose. Two variants wording a `statement`
differently is expected and flagging it would bury the differences that actually
change a verdict. Only `kind`, `parameter`, `operator`, `value`, `unit` and
`verify` count as divergence.

Regenerate it after any change. It is generated — never hand-edit it.

## 4. Evaluate against each variant separately

**One conformance record per candidate per variant.** The record's
`spec.variant` field pins which bar it was judged against, and
`validate-conformance` **errors** if it does not match the spec it is being
validated against — deliberately, not as a staleness warning. A verdict reached
against the budget bar says nothing about the premium bar; the same datasheet
value can be a `pass` under one and a `fail` under the other.

```
evaluation/
  conformance/budget/<candidate-id>.json
  conformance/premium/<candidate-id>.json
  matrix-budget.md
  matrix-premium.md
```

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec_tools.py" \
  criteria spec-budget.yaml -o evaluation/criteria-budget.md
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec_tools.py" \
  matrix spec-budget.yaml evaluation/conformance/budget -o evaluation/matrix-budget.md
```

Each matrix states in its header which variant it judges, so a matrix cannot be
read as clearing a candidate generally.

The cost is real: N candidates against M variants is N×M records. Keep the
variant count to two or three. If you find yourself wanting five, the thing that
actually varies is probably a budget ceiling, which belongs in `context`, not a
branch.

## 5. Converge

Variants exist to be resolved. Once the market has answered — usually because
one variant's bar turns out to be unreachable at any sane price, or because two
variants surface the same product — pick one and stop maintaining the others.

To converge:

1. Choose the surviving variant.
2. Read every `variant_note` on the losing variants before discarding them. They
   record why a bar was set where it was, which is the expensive knowledge here.
3. Set the losing specs' `status: superseded` and name the survivor in
   `supersedes_note`. Do not delete them — conformance records referencing them
   stay interpretable only while they exist.
4. `git mv spec-<survivor>.yaml spec.yaml`, drop the `variant*` fields, bump the
   revision, and record the convergence in `history` with the reason.

A converged spec is back to the ordinary single-spec case, which is where most
purchases should end up.

## What this is not

**Not a budget ceiling.** If the only difference is how much you will spend, use
`context.budget_ceiling` on one spec. Variants are for when the *requirements*
differ, not the price you will pay for the same requirements.

**Not a shortlist.** Variants are specs, not candidates. Two products under
consideration is a conformance matrix, not a branch.

**Not a revision.** If the new version replaces the old one, it is a revision —
bump it. Branch only when both versions stay live and you genuinely want to see
what each finds.
