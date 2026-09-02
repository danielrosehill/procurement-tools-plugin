---
description: Write the landscape report — the state of the market against the spec, as markdown and PDF
argument-hint: [--md-only, optional]
---

# Landscape Report

Consolidate the workspace into a dated report in `outputs/`. Markdown always; Typst + PDF unless `--md-only`.

## Prerequisites

`landscape/field.md` sweep status should be Complete. If it isn't, ask whether to report on a partial sweep — and if so, **state the incompleteness in the report's opening**, with which ground is uncovered. A partial survey presented as complete is the one genuinely misleading output this workspace can produce.

## Audience

Someone who has never seen this market and needs to understand it cold: what exists, how it's organised, what they'd have to give up. Not someone looking for a product name.

## Structure

```
1. The question          — the requirement, in the user's terms, one paragraph
2. The short answer      — 3–6 sentences. Does this exist? How thin or crowded?
                           What's the unavoidable trade-off? Answer the question
                           asked, before any detail.
3. The field             — how many options, by segment, collapsed for rebadges.
                           The full table can be an appendix; the body carries
                           the count and the shape.
4. How the market divides— segments, what each optimises for, what it gives up.
                           Include the spec-vs-market axis mismatch — the axes
                           the market varies on that the spec never mentioned.
5. Against the spec      — the conformance matrix. Unknowns visible as unknowns.
6. Gaps                  — unmet requirements first, with structural reasons.
                           Over-served requirements. Where the market is thin.
7. The trade-off         — the one choice that can't be avoided, named plainly.
8. Conditional narrowings— if you weight X, it's these. Conditions stated.
9. What survives         — the unranked shortlist, with the open question on each.
10. Method and limits    — ground covered, sources by type, what couldn't be
                           verified, dates. What would change the conclusions.
11. Appendix             — full field table, sources index.
```

## Rules

**No recommendation section.** No #1, no runner-up, no "best value". If the field points somewhere, it points conditionally and section 8 carries it. A landscape report that ends in a pick has answered a question the user didn't ask, and it makes the map look like advice.

**Lead with the answer.** If nothing meets the spec, section 2 says so in its first sentence. If the market is four products wearing twelve names, section 2 says that.

**Dates on everything.** Every claim in the report is as-of. Put the survey date in the header and the verification date on anything that could move — availability, price band, shipping status.

**Unknowns survive to the report.** Carry the matrix `?`s into section 5 and section 10. A report that quietly resolves its unknowns has fabricated them.

**Prices stay indicative and labelled.** Bands for segmentation, marked as such. Any hard price figure names its source and date, and if it's a shop price, it came from the `price-scan` skill on the user's own egress.

**Say what you didn't cover.** Section 10 is not boilerplate. Unswept adjacent categories, regions out of scope, source types that didn't exist for this market — all of it goes in. The next reader's first question is "how much do I trust this", and section 10 is the answer.

## Output

Write `outputs/landscape-YYYY-MM-DD.md`. Unless `--md-only`, render the PDF through
the `procurement-report` skill (kind `landscape`) so this report shares styling with
every other report the plugin produces:

```bash
cp "${CLAUDE_PLUGIN_ROOT}/assets/report/base.typ" outputs/base.typ
```

```typst
#import "base.typ": *
#show: report.with(
  title: "[Category]",
  kind: "Market landscape",
  date: "YYYY-MM-DD",
  meta: (("Spec", "spec.md"), ("Options", "[n]"), ("Swept", "YYYY-MM-DD")),
)
```

Compile to `outputs/landscape-YYYY-MM-DD.pdf`, keeping the `.typ` source alongside.
Wide conformance matrices want landscape orientation or a smaller size on that page —
check the compiled PDF rather than assuming it fits.

Use `verdict()` and `conformance-table()` for the matrix and `unknown-box[...]` for
the `?`s, so an unverified cell cannot be mistaken for a finding.

Never overwrite a previous report. Dated files accumulate; `/procurement-tools:mkt-refresh` diffs against them.

## Finally

Print the path, the short answer from section 2, and the offer to hand off:

> "If you want to move to buying: `/procurement-tools:new-workspace <thing>-purchase-MMDD --variant=general-purchasing --private`, carrying the shortlist and requirements across. This repo stays as the standing map."
