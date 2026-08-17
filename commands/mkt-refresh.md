---
description: Re-sweep a previously surveyed market and report what changed since the last survey
argument-hint: [since YYYY-MM-DD, optional — defaults to the most recent report]
---

# Refresh the Survey

Re-run the sweep against an existing field and report the delta. This is why a landscape workspace is durable where a purchase workspace is disposable: the map ages, and knowing *how* it aged is worth more than a fresh survey with no baseline.

## Establish the baseline

Take the date from `$ARGUMENTS`, or the most recent report in `outputs/`. Read that report, `landscape/field.md` and `landscape/gaps.md` as they stand. Note the baseline sweep date and entry counts before changing anything.

Re-read `spec.md` too, and ask whether the requirement still holds. Requirements drift — a spec written a year ago may have constraints that no longer apply, or a new hard no. Update via `/procurement-tools:update-spec` before sweeping if so, and record that the spec changed, because it will explain part of the delta.

## Sweep

Run the `/procurement-tools:mkt-survey` procedure again against the same scope. Additionally, for every existing entry:

- **Still available?** Discontinued entries move to the dead table with the approximate date and successor.
- **Still meets the spec?** Firmware, licensing and business-model changes move options between live and excluded without any hardware changing. A feature moved behind a subscription is a status change.
- **Price band moved?** Update the band; a whole segment shifting is a market-shape finding.
- **`announced` entries** — did they ship, slip or die? A vapourware entry that has now been "coming soon" across two surveys should be re-labelled honestly.

Re-verify dates on anything load-bearing. An entry carrying a two-year-old verification date is not evidence any more.

## Report the delta

Write a new dated set in `outputs/`, opening with **"Changes since [baseline date]"**:

- **New entrants** — and whether they're genuinely new or were missed by the earlier sweep. Say which; a miss is a note on the earlier survey's coverage, not a market movement.
- **Departures** — discontinued, withdrawn from the market, vendor gone.
- **Status changes** — live ↔ excluded, and what caused each.
- **Price movement** — by segment, not by product.
- **Segment changes** — a boundary that has moved or dissolved, a segment that has emptied.
- **Gap changes** — the important one. Has a previously unmet requirement become met? Has a met one become unmet? A gap that closed is usually the reason the refresh was worth running.
- **Direction** — has the market grown, consolidated or thinned since the baseline? Two dated surveys support a claim about direction that a single one can't.

Then update `landscape/*` in place so the working documents reflect the current state, leaving the previous report untouched in `outputs/`.

## When nothing changed

Say so plainly and briefly. "Nine months on, the field is unchanged; the gap identified in the [date] survey is still open" is a complete and useful result — it says the market is static, which is itself a decision input. Don't inflate a no-change refresh into a full report.

Update `spec.md`'s **Last full sweep** date either way.
