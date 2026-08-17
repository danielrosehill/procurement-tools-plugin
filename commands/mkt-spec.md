---
description: Define the requirement envelope and survey scope for a market landscape survey — capability-framed, no candidates
argument-hint: [one-line description of the requirement, optional]
---

# Survey Spec

Populate `spec.md` at the repo root for a **market landscape survey**. The output is a requirement and a sweep boundary — not a purchase brief.

This is the `market-landscape` counterpart to `/procurement-tools:intake`. Do not run `/procurement-tools:intake` in this workspace; it asks decision questions (budget ceiling, urgency, deal-hunting posture) that bias a survey.

## Before asking anything

Read `spec.md`. If Status is already "Configured", ask whether to revise it or go straight to `/procurement-tools:mkt-survey`. For a targeted change use `/procurement-tools:update-spec <change>` instead.

Do **not** load standing buyer preferences here. Trusted brands, avoided brands and markup thresholds are decision inputs; applying them to a sweep silently deletes parts of the map. They belong in the purchase workspace this survey eventually feeds.

## What to capture

Conversational, batched. Use `AskUserQuestion` where a multiple choice helps.

### 1. The requirement, capability-framed

Ask what has to be possible that isn't possible now. If the user answers with a product ("a Rode Wireless Go"), push once: "what does that let you do?" — the survey needs the capability, or it will only ever find that product's direct competitors.

Capture the underlying problem in one line. Then ask what the market calls this, if anything. **"No established category" is a valid and important answer** — it usually predicts a thin, incoherent field, and it should shape the sweep toward adjacent categories.

### 2. Must-haves and hard nos

Same distinction as the purchase flow: must-haves are positive requirements, hard nos are disqualifying characteristics. Both remove an option from contention — but here, a removed option is still **logged with its reason**, because the shape of what doesn't qualify is part of the map.

Probe for hard nos explicitly; don't let the user skip the section.

### 3. Nice-to-haves — reframed

Explain the difference from the purchase flow: here these aren't tie-breakers, they're **cluster detectors**. If most options in one segment have a nice-to-have and none in another does, that's a segment boundary. Capture them, and say what they're for.

### 4. Survey scope — the part that makes this terminate

Fill the scope table. Ask about each dimension:

- **Geography** — which markets count as reachable. Include importable-from where relevant.
- **Price band** — as a *sweep bound*, not a budget. "Nothing over $400" excludes a tier from the map; it isn't a ceiling to negotiate against. If the user answers in budget language ("I'd like to spend about $200"), convert it: ask what price they'd stop bothering to look above.
- **Form factors** — in and out.
- **Condition** — does used / refurb count as available?
- **Maturity** — does announced-but-not-shipping count? Crowdfunding?
- **Vendor type** — do unbranded marketplace listings count as options?

Then set the **termination condition** explicitly: what will make the sweep done. Without one, either the survey never closes or it closes arbitrarily at the first good find. Good conditions look like "three independent sources stop surfacing new names" or "every vendor in each identified segment checked directly".

### 5. Adjacent categories

Ask directly: what else might solve this problem a different way? Offer two or three yourself, drawn from the requirement — a software answer to a hardware need, a service answer to a product need, a general-purpose tool instead of a dedicated one.

This is the single highest-value question in the intake. A survey that sweeps only the named category misses the answer whenever the answer sits one category over. Record each with the rationale and an unticked box.

### 6. Known starting points

What does the user already know exists? Logged separately so the report can show what the survey *added*.

### 7. What the survey is for

Intended use, whether it feeds a decision, and refresh cadence. A survey feeding a purchase in three months gets written differently from one that exists to answer "does this even exist yet".

## Save

1. Write into `spec.md`, replacing placeholders.
2. Set **Status**: Configured, **Last updated**: today, **Last full sweep**: never.
3. Seed `## Open questions` with anything raised in the interview that the sweep should resolve.
4. Summarise the requirement and the scope boundary in 4–6 lines.
5. Prompt: "Spec saved. Run `/procurement-tools:mkt-survey` to start the sweep. Drop any catalogues or screenshots you already have into `sources/` first — `/procurement-tools:extract` can pull options out of them."

## Style

- One repo = one spec. If the user describes two separable requirements, say so and suggest a second workspace.
- Never propose candidates during intake. Naming products here anchors the sweep to them.
- If the user's requirement is really a decision between two known products, tell them plainly: they want `--variant=general-purchasing`, not this.
