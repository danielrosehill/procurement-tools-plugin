---
description: Derive how the market divides — segments and the axes it actually varies along — from the enumerated field
---

# Segment the Market

Read `landscape/field.md` and write `landscape/segments.md`.

## Derive, don't assume

Segments come **out of the field**, not out of prior expectations about the category. Group by observed behaviour — what an option optimises for, what it costs, who makes it, what it structurally gives up — not by the marketing tiers vendors use. Vendor tiers ("pro", "prosumer", "entry") describe a price ladder within one brand; they rarely survive contact with the whole field.

A segment is real if two of its members are **substitutes** — someone choosing one would seriously consider the other — and a member of another segment is not.

## Find the variation axes first

Before naming segments, list the dimensions the field actually varies along. For each: the range across the field, and whether `spec.md` says anything about it.

Then extract the two findings that matter most in the whole survey:

- **Axes the market varies on that the spec doesn't mention.** These are what will surprise the buyer after purchase. If the field splits hard on something the spec is silent about, the spec has an unstated preference that needs stating.
- **Axes the spec cares about that the market doesn't differentiate on.** Either every option has it or none does. Either way it isn't a choosing criterion, and carrying it as one makes the decision look harder than it is.

Say both plainly. The mismatch between how the spec is framed and how the market is organised is usually the single most useful thing this workspace produces.

## Then the segments

For each: the **boundary** (what makes something belong, not a description), price band, members, what it optimises for, its typical compromise, and how it fits the spec — including which requirements it *structurally* can't meet. "Nothing in this segment can do X, by construction" is worth more than a per-option note repeated five times.

Two to five segments. If you have more, you're describing products; fewer, and you haven't found the boundary yet.

## Market shape

Write the shape paragraph honestly:

- How thin is it, once rebadges are collapsed?
- Which "different" products are the same hardware?
- Who is actually in the market — established brands, indie, one dominant vendor, a long unbranded tail?
- Direction of travel, with the evidence: new entrants, discontinuations, price movement.
- The price/capability relationship — linear, a cliff at some threshold, or a dead zone in the middle where nothing sensible is sold.

## Name the real choice

Finish by identifying which segment boundary the buyer is actually choosing across, and why the spec straddles it. Most specs do straddle one — they want the price of one segment and a capability that only exists in another. Naming that trade-off is the point of segmenting.

## Feed back into the sweep

Segmenting almost always reveals a corner of the market the sweep missed — a segment with one member usually means the sweep stopped early, not that the segment is genuinely tiny. When it does, say so and re-run `/procurement-tools:mkt-survey <segment>` before moving on. Survey → segment → matrix is a loop.

Next: `/procurement-tools:mkt-matrix`.
