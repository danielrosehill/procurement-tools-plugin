---
name: market-evaluator
description: Rank the candidates that survived conformance evaluation and produce a purchase recommendation — a top three in order, each with product, price and where to actually buy it, followed by category picks such as best budget, best overall and best for features. Use once conformance records exist and the question has moved from "which of these qualify" to "which should I buy", when someone asks for a recommendation or a shortlist ranked, or when a matrix has narrowed the field and a decision is now needed. Ranks only candidates that clear every disqualifying requirement, and states its weighting rather than hiding it in a score.
allowed-tools: Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Agent, Bash(python3 *), Bash(ls *), Bash(cat *), Bash(mkdir *)
---

# Market evaluator

The step after the conformance matrix. The matrix answers *who qualifies* and
deliberately refuses to rank — no scores, no weighted totals, no ordering,
because a weighted total buries the trade-offs the matrix exists to expose.

This skill is where ranking is allowed to happen, precisely because it is
separate and explicit about what it weighted.

**Inputs:** `spec.yaml` (or `spec-<variant>.yaml`), `evaluation/conformance/*.json`,
and price/availability data if `price-scan` has run.
**Output:** `evaluation/recommendation.md`.

Run `evaluation-matrix` first. Without conformance records this skill has nothing
to rank and must not improvise one from listings.

## The gate: who is even rankable

Before ranking anything, partition the candidates. This is not a formality — it
is the step that stops a cheap non-compliant product topping the list.

- **Rankable** — every `must` is `pass` and every `must-not` is clear.
- **Blocked** — a disqualifying requirement is `unknown`. **Not a low rank; not
  rankable at all.** Listed separately with the specific evidence that would
  unblock it. An `unknown` on a `must` is missing information, and burying it as
  a slightly-lower position presents ignorance as judgement.
- **Excluded** — a confirmed `fail` on a disqualifying requirement. One line each,
  naming the requirement. They are in the matrix; do not re-argue them.

`nice` requirements never gate. They are tie-breakers, and they are most of what
distinguishes the rankable set from one another.

If **nothing** is rankable, say so plainly and stop. The output is then the
blocked list and what would unblock it. Do not relax the spec to produce a
recommendation — if the bar is wrong, that is a spec revision the user makes
knowingly, via `update-spec` or `spec-as-code`.

## Output shape

Write `evaluation/recommendation.md` in this order, always.

### 1. Top three, in order — always first

Even where the field is larger. Three ranked picks, best first, each carrying:

| Field | Requirement |
| --- | --- |
| **Product** | Manufacturer, model, and the exact part number **for the user's region**. A part number that cannot be bought where they are is not a recommendation. |
| **Price** | Landed cost where known — unit price, shipping, duty and tax — in the user's currency, with the date and source. Say "unit price only, landed cost not established" rather than presenting a bare figure as if it were the total. |
| **Sourcing** | Where to actually buy it: named vendors, stock state, lead time. At least one concrete route per pick, or an explicit "no source found in region", which is itself a finding. |
| **Why this position** | One or two sentences. What it clears that the one below it does not, or what it trades. |
| **What it costs you** | The trade-off accepted. Every pick has one; a pick presented with no downside has not been examined. |

If fewer than three qualify, give what there is and say why the list is short.
Do not pad the third slot with a candidate that is blocked or excluded.

Sourcing is the half most often skipped, and it is the half that makes the
recommendation actionable. If price and availability have not been established,
run `price-scan`, or say explicitly that the ranking is on specification alone
and the prices are indicative.

### 2. Category picks

After the top three, and only where the category is genuinely distinct — say so
when one candidate wins several, rather than manufacturing a different name for
each slot:

- **Best overall** — the balanced pick. Usually but not always #1; where it
  differs, that is interesting and should be explained.
- **Best budget** — cheapest that still clears every `must`. Never a
  non-compliant product, however cheap.
- **Best for features** — most `nice` requirements met, cost secondary.
- **Best value** — the knee in the curve: where the next increment of money stops
  buying a proportionate increment of capability.
- **Add others when the spec justifies them** — best for availability when lead
  time is the binding constraint, best for support where that was a requirement.

One line of justification each, referencing requirement ids.

### 3. What decided it

State the weighting **as a sentence, not a score**: "ranked on setpoint accuracy
first (REQ-002), then landed cost, then warranty; transient response was not
separating them."

If the spec gives priorities, use them and say so. If it does not, say which
weighting you applied and that the user can reorder it. Weighting is a judgement
and must be visible enough to argue with — a number in a column is not.

### 4. Blocked and excluded

Both lists, as above. The blocked list is the actionable one: each entry names
the requirement, why it is unresolved, and the specific evidence that would
settle it.

### 5. Provenance

Spec identity (`id@variant rN`), how many conformance records were read, and
the date. If any record was evaluated against an older revision, name it — its
verdicts may predate the current bar.

## With variants

One recommendation **per variant**, not one merged ranking. Budget's winner and
premium's winner are answers to different questions, and averaging them answers
neither.

Write `evaluation/recommendation-<variant>.md` per variant, then a short
comparison at the end of each: what the extra money actually buys, and whether
the premium bar turned out to be reachable at all. That comparison is usually the
most useful output of running variants, and it is the input to converging them.

## Discipline

**Never rank on evidence the matrix rejected.** If a `must` needed a datasheet
and only a retail listing exists, the cell is `unknown` and the candidate is
blocked. Do not let a plausible review promote it.

**Price does not override conformance.** A cheaper non-compliant product is not
a budget option; it is excluded. The budget pick is the cheapest *compliant* one.

**Say when it is close.** Where the top two are separated by one `nice`
requirement or a small price delta, say so. A confidently-ordered list that is
actually a coin toss is worse than a stated tie, because the user cannot tell
which they are being handed.

**Do not re-research.** This step reads conformance records; it does not
re-litigate cells. If a cell looks wrong, fix it in the record and regenerate the
matrix — a recommendation that quietly contradicts the matrix it cites makes both
untrustworthy.

**Carry marketplace caveats through.** A delivery date that was conditional, a
price excluding a coupon, a stock figure from a signed-in session — each changes
the comparison and each disappears if only the number is recorded. See
`marketplace-handoff`.
