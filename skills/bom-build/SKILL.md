---
name: bom-build
description: Build a bill of materials — a shopping list written as requirements rather than as products, with stable line ids, quantities, substitution rules and optional references to a spec. Use when a purchase is several items rather than one, when kitting out a space or a job, when a list needs to go to suppliers before every item has been chosen, or when a shopping list needs to survive long enough to be revised. Lines can be described-but-unidentified and still be quotable.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(python3 *), Bash(ls *), Bash(cat *), Bash(mkdir *)
---

# BOM build

A shopping list where each line says **what it has to be** rather than what to
buy. That is the difference between a list you can send to a supplier and a list
you can only send to a shop.

Output: `bom.yaml` at the repo root, conforming to
`${CLAUDE_PLUGIN_ROOT}/schema/bom.schema.json`.
Worked example: `${CLAUDE_PLUGIN_ROOT}/examples/bom.example.yaml`.

## Why lines are descriptions

A line that names a product can only be priced. A line that describes a
requirement can be **quoted** — the supplier can say "we don't carry that, but
we carry this, and here is why it meets what you described". That answer is
often the most valuable thing an RFQ returns, and a list of part numbers makes
it impossible to give.

So a line is quotable at either stage:

- **Described** — no `identified` block. The description carries the whole
  requirement. This is a legitimate, finished state, not a to-do.
- **Identified** — an `identified` block with manufacturer, part number and
  region, once research has settled the choice.

Lines move from described to identified as evaluation resolves them. Nothing
forces them all to arrive before the BOM is useful.

## Writing a line

**Description.** Vendor-neutral, and self-contained: written so a supplier who
has never seen the spec can quote it. Include the constraints that actually
matter and omit the ones that do not — every over-specified attribute is a
supplier who cannot help you. If a `spec.yaml` exists, the description is the
prose rendering of the referenced requirements, not a second set of
requirements. Do not let the two drift.

**`spec_ref`.** Points at the spec, optionally at specific requirements:
`laser-measure-2026-08#REQ-001,REQ-004`. This is what makes "equivalent" mean
something. `validate-bom --spec` checks the ids still resolve.

**`quantity` and `unit`.** Suppliers quote per unit and per pack, and the
difference is a common source of a quote that looks cheap.

**`substitution`.** The field that tells a supplier what latitude they have:

| Value | Means |
|---|---|
| `allowed` | Propose anything meeting the description. Use when the description is the requirement. |
| `equivalent-only` | Must meet every referenced requirement. The default. Needs a `spec_ref` to mean anything. |
| `none` | This exact part number. Reserve it for genuine cases — interoperating with something already owned, matching an existing installation, a near-sibling trap in the family. |

Default to `equivalent-only`. Reflexive `none` is how a BOM ends up unquotable
by every supplier who does not happen to stock one brand.

**`criticality`.** `required`, `optional` (price it separately), or `contingent`
(only needed if another line resolves a particular way — say which in `notes`).
Contingent lines are dropped from generated RFQs, so they cost nothing to keep.

**`target_price`.** Per unit, for internal planning. It is carried into an RFQ
only when explicitly requested, because it anchors the supplier — see
`rfq-package`.

## Groups

Group lines by subsystem, or by which supplier is likely to carry them. A group
is the natural unit of one RFQ: `spec_tools.py rfq --group <name>` quotes just
that group, so a BOM spanning three trades becomes three focused RFQs rather
than one nobody can answer in full.

## Revisions

Line ids are stable and never reused, for the same reason requirement ids are: a
supplier who quoted against revision 2 has to remain matchable when the BOM
reaches revision 4. Bump `revision`, add a `history` entry, and never renumber.
To drop a line, delete it — but do not reissue its id.

## Validate

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec_tools.py" validate-bom bom.yaml --spec spec.yaml
```

Catches a reused line id, a dangling `spec_ref`, a group pointing at a line that
does not exist, and `substitution: none` on a line with no part number. It warns
on a part number with no region — the same product carries different numbers per
market, and a supplier will quote whichever one they stock.

## Where a BOM is not the right shape

A single-item purchase does not need one; use `spec.yaml` and the ordinary
purchase flow. A BOM earns its keep at three or more lines, or at one line that
will be quoted by several suppliers.

## Hands off to

- `rfq-package` — projects the BOM, or one group of it, onto a supplier request.
- `price-scan` — prices the identified lines across configured marketplaces once part numbers exist. The two answer different questions: a BOM is what you need, a price scan is what it costs to get it here.
- `spec-as-code` — the requirements `spec_ref` points at.
