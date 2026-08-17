---
description: Identify unmet and over-served requirements, the compromise axes, and where the market is thin — the payload of a landscape survey
---

# Gaps and Compromises

Read `spec.md`, `landscape/field.md`, `landscape/segments.md` and `landscape/matrix.md`. Write `landscape/gaps.md`.

This is where a landscape survey earns its keep. Everything upstream is enumeration; this is the analysis.

## Unmet requirements

Requirements met by nothing in the field. For each: the nearest miss and how close it gets, and — where you can establish one — the **structural reason** nothing meets it. "No consumer vendor pursues that certification", "the two features are physically in tension", "the segment that would carry it died in 2023" are far more useful than "nothing has it".

**If a must-have is unmet, that is the headline of the report and goes at the top.** *This does not exist yet* is a complete, valuable answer to a survey. Do not soften it into a nearest-fit suggestion; the user asked what's on the market, and the answer is nothing.

## Over-served requirements

Requirements met by everything. These aren't choosing criteria — carrying them makes the spec look more constrained than it is and can hide the requirements that actually bind. Say which ones to drop from the decision.

## Compromise axes

Where the field forces a trade: no option is strong at both ends. For each axis, name the trade, list who's strong on each side, answer whether anything does both and what that costs, and say which side the spec leans — or state plainly that the spec doesn't say and the user needs to decide.

Derive these from `landscape/segments.md`. A compromise axis is usually a segment boundary seen from the buyer's side.

## Where the market is thin

Describe the holes: the combination of attributes nobody sells. For each, what would fill it, and a plausible reason it's empty — a feature that only appears above a price tier, a certification cost, a market too small to serve. A hole with an explanation is a finding; a hole without one is a note to check the sweep covered that corner.

## Conditional narrowings

Not a ranking. "If you weight X, the field narrows to A and B, ruling out C" — the condition stated, the cost of that weighting stated, the choice left to the user. Give two or three across the axes that actually divide the field.

Resist collapsing these into a recommendation. If asked directly for a pick, give the conditional and say what weighting would have to be true — then offer to open a purchase workspace where picking is the job.

## Candidates worth a decision

The short unranked list that survives the spec. For each: segment, which requirements it clears that others don't, and the open question to settle before buying — a price to confirm, availability to check, a `?` from the matrix to resolve.

Keep it short. If more than five or six options survive, the spec is under-constrained and the more useful output is saying so: the user has more freedom than they thought, and should decide what else they care about.

## Unresolved

Every `?` from the matrix that still matters, why it couldn't be closed, and what would close it. Being explicit here is what makes the survey honest and what makes `/procurement-tools:mkt-refresh` useful later.

## Then

Print the unmet requirements, the real trade-off, and the surviving candidate count. Next: `/procurement-tools:mkt-report`.
