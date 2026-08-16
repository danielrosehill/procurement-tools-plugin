---
name: marketplace-plugins
description: Find and install the dedicated plugin for a specific marketplace when a purchasing question turns out to be marketplace-specific — Amazon US, and others as they land. Use when the user names a marketplace, when a price or delivery answer needs that marketplace's own quirks to be correct, or when they ask which shopping plugins are available and how they fit together.
allowed-tools: Read, WebSearch, Bash(gh *), Bash(ls *), Bash(cat *)
---

# Marketplace-specific plugins

`purchasing` is the **generalist** ecommerce research plugin: intake, specs,
cross-vendor comparison, evaluation, recommendations, preference memory. It is
deliberately marketplace-agnostic.

Individual marketplaces get their own plugins, because the knowledge that makes
an answer *correct* on a given marketplace is specific, volatile and does not
generalise — which fetch route reaches it, which of its fields lie, how its
filter grammar works, what its delivery promise is actually conditional on.
Folding that into the generalist would make it wrong everywhere else.

This skill is the bridge: recognise when a question has become
marketplace-specific, and hand off.

## Registry

| Marketplace | Plugin | Repo |
| --- | --- | --- |
| Amazon.com (US) | `amazon-us` | [`danielrosehill/Claude-Amazon-US-Plugin`](https://github.com/danielrosehill/Claude-Amazon-US-Plugin) |

Regional consumer retail — local vendors, language, VAT, regional aggregators —
is handled by [`shopping`](https://github.com/danielrosehill/Claude-Shopping-Plugin),
which is a sibling rather than a marketplace plugin.

If the user needs a marketplace with no plugin here, say so plainly rather than
improvising marketplace-specific behaviour inside `purchasing`. Getting a fetch
route or a delivery caveat wrong produces a confident wrong answer, which is
worse than "not covered yet".

## When to hand off

Hand off when the answer depends on the marketplace itself rather than on the
product:

- The user names the marketplace, or gives a URL or product ID belonging to it.
- The question is price, stock, delivery date or seller identity **on that
  marketplace** — as opposed to "what should I buy", which stays here.
- A generic fetch already failed on that domain, or returned something that
  looks right but cannot be trusted.

Stay in `purchasing` for the buying workflow itself: turning a vague need into a
spec, comparing across vendors, weighing trade-offs, recording the decision. A
marketplace plugin answers *what does this marketplace say*; it does not decide
what to buy.

## Installing

Check whether it is already installed before suggesting an install — the skills
appear in the session's skill list if it is.

```
/plugin marketplace add danielrosehill/Claude-Code-Plugins
/plugin install amazon-us
```

Tell the user what installing gets them in a sentence, and let them run it.
Installing a plugin changes their configuration, so do not do it for them
without being asked.

After installing, the user may need to reload the session before the new skills
and commands are available.

## Reporting

When you hand off, say which plugin you are using and why, so the answer carries
its own provenance — "checked on Amazon via `amazon-us`, which reads the listing
rather than the search grid" is more useful than an unattributed price.

Where a marketplace plugin returns a caveat — a delivery date that is
non-Prime, a ZIP that could not be confirmed, a price that excludes an
untickable coupon — carry that caveat into the purchasing decision rather than
flattening it into a single number.
