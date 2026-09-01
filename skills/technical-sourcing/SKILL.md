---
name: technical-sourcing
description: Run a technical purchasing investigation end to end — spec as code, manufacturer documentation, part-number equivalence across regions, conformance evaluation, bill of materials, RFQ. Use when a purchase turns on specifications rather than on price or reviews, when requirements are specific enough that most of the market fails them, when sourcing across regions, or when the user asks for in-depth or serious purchasing research. Sequences the atomic sourcing skills and says which steps this particular purchase can skip.
allowed-tools: Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Agent, Skill, Bash(python3 *), Bash(ls *), Bash(cat *), Bash(mkdir *)
---

# Technical sourcing

The orchestrator for spec-driven purchasing. It owns the sequence and the
handoffs; the work happens in the atomic skills, each of which is usable on its
own and invocable by a subagent.

## What kind of purchase this is for

Technical purchasing is where **conformity to a specification decides the
purchase** and price is a constraint rather than the question. Marketplace
purchasing is where the object is a known commodity and the question is who has
it, at what price, delivered when.

Use this when:

- Most of the market fails the requirements, and the work is finding the ones
  that do not.
- The distinction that matters is not visible in a listing — a protocol, a
  tolerance, a rating, a certification.
- The same product is sold under different numbers in different markets.
- The purchase is several interdependent items.
- The user says "in depth", "properly", "serious", or has been burned by a
  near-sibling before.

Do not use it for a commodity purchase with a clear winner. The overhead is real
and it buys nothing there — `/procurement-tools:evaluate` or the `shopping`
plugin is the right size of tool.

## The pipeline

Each step is a skill. Steps are skippable; say which you skipped and why.

```
define-spec ──▶ spec-as-code ──▶ evaluation-matrix ──▶ (recommend)
  (what is       spec.yaml         criteria.md            │
   it called)    REQ ids           conformance/*.json     │
                    │              matrix.md              │
                    │                  ▲                  │
                    │                  │                  │
                    ▼                  │                  ▼
              bom-build ───────────────┤            price-scan
              bom.yaml, LINE ids       │            (what it costs
                    │                  │             here, now)
                    ▼                  │
              rfq-package              │
              rfq/*.json               │
                                       │
   spec-sheet-retrieval ───────────────┤  evidence
   data/datasheets/*.json              │
                                       │
   part-number-equivalence ────────────┘  which product is which
   data/equivalence/*.json
```

### 1. Identify — `/procurement-tools:define-spec`

Skip if the user already knows what the thing is called in trade terms. Run it
if they have a photograph, a vague description, or a listing that is close but
wrong. It produces `spec.md` and the search vocabulary.

### 2. Specify — `spec-as-code`

Convert the settled requirements into `spec.yaml` with stable requirement ids.
Skip only for a single-requirement purchase. Everything downstream references
these ids, so a purchase that skips this cannot use the rest of the pipeline.

### 3. Gather candidates

Ordinary search, `/procurement-tools:research`, or a `mkt-survey` if the field
is unmapped. Nothing structured yet — a name, a manufacturer, a part number, a
region. Keep regional siblings as separate candidates until step 4 says
otherwise.

### 4. Disambiguate — `part-number-equivalence`

Run it as soon as two candidates look like the same product, or the moment a
part number has to cross a border. Running it late is how a fully-evaluated
frontrunner turns out to be the variant without the feature, or the variant not
sold in the destination market.

### 5. Document — `spec-sheet-retrieval`

For every candidate that survives a first pass, and every requirement whose
`verify` class is `datasheet`, `manual` or `standard`. This is the step that
converts "the listing says 50 m" into something that can carry a `pass`.

**Parallelise it.** One subagent per candidate, launched together in one
message. Each writes its own `data/datasheets/<mfr>-<pn>.json`, so there is
nothing to coordinate.

### 6. Evaluate — `evaluation-matrix`

Generate `criteria.md`, fan out a subagent per candidate, validate, render.
Again one file per candidate, again launched in one message.

Then read the matrix as a picture of the field before reading it as a list of
candidates: a requirement nothing clears, a requirement everything clears, a
requirement nobody publishes. Those findings usually change the spec, and a spec
change here is a success, not a restart.

### 7. Decide, or report that there is nothing to decide

If exactly one candidate clears everything, say so. If several do, the remaining
differences are price, availability and the `nice` requirements — hand to
`price-scan` for what they cost delivered, and `/procurement-tools:recommend`
for the write-up.

If **nothing** clears, that is the deliverable. Report it as the headline, with
the requirement that did the eliminating and what relaxing it would open up.
Do not fill the gap with the nearest miss presented as a recommendation.

### 8. Procure — `bom-build` → `rfq-package`

For multi-item purchases, or when the route to market is a supplier rather than
a shop. Lines can go out described-but-unidentified; a supplier telling you what
they carry is often faster than another week of evaluation.

## Running it well

**Parallelise the fan-out steps and nothing else.** Steps 5 and 6 are separable —
each candidate can be briefed completely up front and returns a conclusion.
Launch them together in one message. Steps 2, 4 and 6 depend on their
predecessor's output and must not be split; guessing the input to skip a wait
substitutes a confident guess for the fact you were waiting on.

**Validate at each artefact boundary.** `validate-spec` before rendering
criteria, `validate-conformance` before rendering the matrix, `validate-bom`
before generating an RFQ. Each one catches a class of error that is invisible
downstream — a dangling requirement reference reads as a completed check.

**Let the spec move, and record it when it does.** Research that never changes
the spec has not learned anything. Bump the revision, write the reason, say
which conformance records went stale.

**Unknown beats plausible, everywhere in this pipeline.** The failure mode that
matters is not a slow answer; it is a `pass` that came from a retail bullet
point, which is indistinguishable from a verified one two steps later.

## What this is not

Not a ranking engine. Nothing here scores or weights. The matrix says what each
candidate does and does not do; the choice is the user's, and
`/procurement-tools:recommend` is where a recommendation gets written.

Not a price tool. Prices come from `price-scan`, which egresses from the user's
own machine through the right country's VPN exit, because a price fetched from
the wrong country is a real number for the wrong market.

Not marketplace-specific. Once the question narrows to how one shop works, the
`marketplace-handoff` skill routes it to that marketplace's own plugin.
