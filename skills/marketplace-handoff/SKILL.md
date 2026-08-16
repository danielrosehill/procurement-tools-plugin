---
name: marketplace-handoff
description: Decide when a purchasing question has stopped being about the product and become a question about a specific marketplace, and hand it to that marketplace's dedicated plugin instead of answering it here. Use mid-workflow when a comparison, price check or delivery question narrows to one named marketplace. The roster of which marketplaces have plugins is maintained in the shopping plugin's marketplace-plugins skill, not here.
allowed-tools: Read, WebSearch, Bash(ls *)
---

# Marketplace handoff

`purchasing` is the **generalist** ecommerce research plugin: intake, specs,
cross-vendor comparison, evaluation, recommendations, preference memory. It is
deliberately marketplace-agnostic, and it should stay that way.

This skill is the boundary rule. It does not carry a list.

## The rule

Hand off when the answer depends on the **marketplace** rather than on the
**product**:

| Stays here | Hands off |
| --- | --- |
| What should I buy for this purpose | What does this cost on Amazon |
| Which of these three is better value | Is this ASIN in stock, and when does it arrive |
| What spec do I actually need | Which seller is behind this listing |
| Is it worth the upgrade | Does the price include a coupon I have to tick |

The test: could the answer change if the same product were sold somewhere else?
If yes, it is a marketplace question.

## Why not just answer it here

The knowledge that makes a marketplace answer *correct* is specific and
volatile — which fetch route reaches it, which of its fields lie, how its filter
grammar composes, what its delivery promise is conditional on, which facts only
render to a signed-in session. Encoding any of that here would make it stale
within months and wrong for every other marketplace.

**If no plugin covers the marketplace, say so** rather than improvising. A
guessed fetch route or an unqualified delivery date produces a confident wrong
answer, which is worse than "not covered yet".

## Where the roster lives

The maintained list of marketplace plugins — which exist, what each covers, how
to install them — is the `marketplace-plugins` skill in the
[`shopping`](https://github.com/danielrosehill/Claude-Shopping-Plugin) plugin.

It is deliberately in one place. Do not restate it here; a second copy goes
stale and then contradicts the first.

If `shopping` is not installed, the roster at time of writing was `amazon-us`
(Amazon.com US) and `aliexpress-israel-skills` (AliExpress Israel) — but check
the live list rather than trusting that sentence.

## Carrying the answer back

When a marketplace plugin answers, bring its **caveats** back into the
purchasing decision rather than flattening them into a number. A delivery date
that is non-Prime, a ZIP that could not be confirmed, a price that excludes an
untickable coupon — each of those changes a comparison, and each disappears if
you record only the figure.

Say which plugin produced the figure, so the recommendation carries its
provenance.
