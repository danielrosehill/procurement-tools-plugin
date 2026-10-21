# Intake — Build the Spec for This Purchase

You are running the intake for this purchase. The goal is to populate `spec.md` at the repo root with the per-purchase brief.

**Two-tier model:**

- **Standing preferences** (country, currency, trusted/avoided brands, markup threshold, risk tolerance, etc.) live in **memory** (the gateway `memory` server). Load them first with `/load-preferences` — don't re-ask.
- **Per-purchase spec** (`spec.md`) holds only what's specific to *this* decision: what you're buying, must-haves, hard nos, budget, timeline, priorities, context.

**One repo = one purchase.**

## Step 0: Load standing preferences

Before asking anything, run `/load-preferences`:

- If preferences load from memory or the local fallback file — great, the snapshot is now in `spec.md` → don't re-ask those fields
- If no preferences are found — tell the user: "No standing preferences yet. You have three options: **(a)** run `/save-preferences` first (one-time setup, applies to all future purchases) — recommended if you shop frequently; **(b)** apply a **buyer profile** from `buyer-profiles/` (BIFL, budget, minimalist, etc.) as a shortcut pattern for just this purchase — good if you don't want to set up standing preferences yet; **(c)** skip and I'll ask you the standing questions inline now — but you'll be re-asked in every future workspace. Which do you prefer?"
  - If (b): after finishing the per-purchase intake, prompt the user to run `/apply-profile` (or do it inline).

## Step 1: Read existing state

1. Read `spec.md` — is Status "Configured" or still template?
2. Check `for-ai/` — any files already dropped in?

If `spec.md` is configured, ask whether to update or go straight to `/research`.

## Step 2: Capture per-purchase fields

Walk through these conversationally. Batch related questions. Skip anything the user clearly doesn't care about. **Do not re-ask anything already loaded from standing preferences.**

### 1. What they're buying

- Short description (one sentence)
- Category label
- Primary use case

### 2. Must-haves

*Positive hard requirements. Disqualifies if missed.*

Ask: "What are your non-negotiable requirements for this purchase? Features or specs the product absolutely must have?"

### 3. Hard nos / Dealbreakers — **distinct from must-haves**

*Disqualifying characteristics. Disqualifies if present.*

Ask explicitly and separately: "Any dealbreakers specific to this purchase — things that rule a product out even if everything else matches? For example: form factors you can't use, anti-features like soldered RAM or glossy screens, business models you reject (subscription-locked features, always-on cloud)."

Note: The user's **standing avoided brands** from memory already apply automatically. Ask here only for *new* / *this-purchase-specific* dealbreakers.

Prompt for each if the user doesn't volunteer:

- Form factors or designs that are a non-starter for this use case
- Anti-features (no soldered RAM, no glossy screen, no cloud dependency)
- New brand/vendor exclusions that aren't in standing prefs

**Do not let the user skip this section.** If they say "nothing comes to mind", probe gently: "Any past frustration with this product category?"

### 4. Nice-to-haves

Soft preferences for tie-breaking. "Anything you'd prefer but wouldn't hold out for?"

### 5. Budget (this purchase)

- Target (ideal spend)
- Ceiling (absolute max)
- Flexibility (hard / flexible / very flexible)

### 6. Timeline

- Urgency (ASAP / within a week / flexible)
- Deal-hunting (wait for sales?)

### 7. Priorities (this purchase)

Ranked factors for tie-breaking — this decision specifically. Common factors: durability, feature match, value vs RRP, manufacturer reputation, aesthetics, local support.

### 8. Per-purchase overrides to standing preferences

Ask: "Anything about your usual shopping preferences that should be overridden for *this* purchase? For example: willing to accept higher markup for a niche item, willing to skip international shipping because you need it fast."

Capture into the "Per-purchase overrides" table in `spec.md`.

### 9. Context / history

- Replacing something? What and why?
- Past products in this category — loved / hated?
- Compatibility constraints (existing ecosystem, accessories, space)

## Step 3: Save

1. Write answers into `spec.md`, replacing placeholder text
2. Set `**Status**: Configured`
3. Set `**Last updated**: [today YYYY-MM-DD]`
4. Leave the **Standing preferences snapshot** section alone — it was already populated by `/load-preferences`
5. Summarise in 4–6 lines
6. Prompt: "Spec saved. Drop sources into `for-ai/` if you have candidates in mind, or run `/research` to have me evaluate candidates. If you'd like to bias this purchase toward a named pattern (BIFL, budget, minimalist, etc.), run `/apply-profile` before `/research`."

## Interview style

- Conversational, not interrogative
- Batch related questions
- Use `AskUserQuestion` for multiple-choice where it helps
- Accept partial answers + sensible defaults
- **Never re-ask standing preferences** that are already loaded from memory
- **Explicitly probe for hard nos** — push a little if the user tries to skip

## Example opening

```
Welcome. Let me set up the spec for this purchase.

[Runs /load-preferences — reports: "Loaded standing prefs from memory — [summary of loaded fields]."]

Good — I'll apply those. A few questions specific to this purchase:

What are you looking to buy? Short description is fine — e.g. "ergonomic office chair", "14-inch laptop for dev".
```
