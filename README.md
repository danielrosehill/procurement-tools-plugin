# procurement-tools

**Product research and procurement skills for Claude Code, with a particular focus on
technical specification conformance.**

The question this plugin is built around is not "where is it cheapest" but *does this
part actually meet the requirement*, and can you show your working. It takes a
purchase from a vague want — or a photograph — to a vendor-neutral spec, retrieves
manufacturer datasheets, resolves part numbers across regions, scores candidates
against the spec in a conformance matrix, and ends in a recommendation, a bill of
materials, or an RFQ package.

It is deliberately **marketplace-agnostic**. It never assumes a particular shop; the
marketplace-specific plugins listed below do that.

Part of the [danielrosehill Claude Code marketplace](https://github.com/danielrosehill/Claude-Code-Plugins).

```
/plugin marketplace add danielrosehill/Claude-Code-Plugins
/plugin install procurement-tools@danielrosehill
```

## Spec conformance is the through-line

Most buying advice optimises price against reviews. That works for commodities and
fails wherever a datasheet decides the outcome — where the wrong flange, voltage,
ingress rating or regional part suffix means the thing arrives and does not fit, does
not comply, or does not work.

So the spine of the plugin is a chain in which the **specification is the artefact** —
versioned, machine-checkable, and the thing every later step is judged against.
Requirement ids (`REQ-001`) and BOM line ids (`LINE-001`) thread through every
document, so a claim can always be traced back to where it came from.

| Skill | What it settles |
| --- | --- |
| `spec-as-code` | The requirement as a versioned, machine-checkable artefact rather than prose that drifts |
| `spec-sheet-retrieval` | The manufacturer's own datasheet, not a retailer's retyped summary of it |
| `part-number-equivalence` | Whether a part number sold in one region is the same thing as the one you specced |
| `evaluation-matrix` | Candidate-by-requirement conformance, with unknowns recorded as unknown rather than guessed |
| `technical-sourcing` | Sourcing where specifications decide the purchase and price is a constraint |
| `bom-build` | A multi-item list with quantities, alternates and rationale |
| `rfq-package` | That list turned into something a supplier can quote against |

Each is atomic and usable on its own — see [**Technical sourcing**](#technical-sourcing)
below for how they join, and [`docs/artefact-chain.md`](docs/artefact-chain.md) for the
file contract.

## Which plugin do I want?

This plugin is the **process** half of the buying stack: working out what the thing
is, what it has to do, which candidates qualify, and which one to buy. The plugins
below are the **place** half — how a given retailer's catalogue, language, currency,
tax treatment and stock data actually work.

| You are doing this | Use | Repo |
| --- | --- | --- |
| I don't know what this thing is called, or what to search for | **`procurement-tools`** → `define-spec` | this repo |
| Turning a want into a spec, then judging candidates against it | **`procurement-tools`** | this repo |
| Specifications decide the purchase, not price or reviews | **`procurement-tools`** → `technical-sourcing` | this repo |
| Chasing a manufacturer datasheet, or a part number across regions | **`procurement-tools`** → `spec-sheet-retrieval`, `part-number-equivalence` | this repo |
| A multi-item list going to suppliers for quotes | **`procurement-tools`** → `bom-build`, `rfq-package` | this repo |
| Surveying a whole product category before choosing | **`procurement-tools`** → `mkt-*` | this repo |
| Planning a hardware build or rig | **`procurement-tools`** → `rig-*` | this repo |
| Finding who stocks it locally, at what price, in stock when | **`shopping`** | [`Claude-Shopping-Plugin`](https://github.com/danielrosehill/Claude-Shopping-Plugin) |
| Israeli retailers, Hebrew terms, Zap, ILS, parallel imports | **`israel-shopping`** | [`Claude-Israel-Shopping-Plugin`](https://github.com/danielrosehill/Claude-Israel-Shopping-Plugin) |
| Amazon listings, Prime-aware delivery dates, seller identity | **`amazon`** | [`Claude-Amazon-Plugin`](https://github.com/danielrosehill/Claude-Amazon-Plugin) |
| AliExpress in Israel — Choice, VAT and customs thresholds | **`aliexpress-israel-skills`** | [`Aliexpress-Israel-Skills`](https://github.com/danielrosehill/Aliexpress-Israel-Skills) |
| Assembling a full hardware build specification | **`hardware-spec-assembly`** | [`Claude-Hardware-Spec-Assembly-Plugin`](https://github.com/danielrosehill/Claude-Hardware-Spec-Assembly-Plugin) |
| Certifying something against a published standard | **`spec-led-certification`** | [`spec-led-certification-plugin`](https://github.com/danielrosehill/spec-led-certification-plugin) |

The halves are designed to be installed together. Once a question narrows from "what
should I buy" to "how does *this shop* work", the `marketplace-handoff` skill routes it
out of here. The maintained roster of marketplace plugins lives in `shopping`'s
`marketplace-plugins` skill — kept in one place so it cannot go stale in two.

## Spec definition

The step before searching. You know roughly what you want but not what it is called,
so you cannot search for it yet — you may only have a photograph of one.

```
/procurement-tools:define-spec
```

Give it a description, a photo, a listing that is close but wrong, or a part number.
It produces two things:

- **`spec.md`** — a vendor-neutral capability specification. What the thing must do,
  its fit and interface constraints, and — importantly — what is *not* required, so
  that incidental details of the example you showed don't silently become filters.
- **`search-terms.md`** — the search vocabulary, grouped by register, with a bare
  `search-terms.txt` alongside it for pasting straight into a search box.

The vocabulary is grouped by register because register decides which half of the
market a search reaches. The same object has a consumer name, a trade name, and
often a spec code, and they return different catalogues at different prices. Each
term is annotated with what it skews toward, which marketplaces it works on, and
what noise to expect — including a **decoy terms** section for the strings that look
correct and return the wrong thing.

## What you get

### Primitives (always available once the plugin is installed)

**General-purchasing commands** (`/procurement-tools:*`):
- `define-spec` — turn a vague want (or a photograph) into a vendor-neutral spec **and** an annotated search vocabulary. See [Spec definition](#spec-definition).
- `intake` — build the per-purchase spec (`spec.md`)
- `research` — evaluate candidates against the spec
- `compare` — side-by-side comparison of 2–4 shortlisted products
- `evaluate` — quick one-off evaluation of a single product
- `recommend` — generate the final PDF recommendation report
- `recompare` — re-run the shortlist against the current spec
- `extract` — pull product data from screenshots, PDFs, and catalogs
- `market-check` — local vs international price realism with import costs
- `load-preferences` / `save-preferences` — standing preferences to/from Mem0
- `apply-profile` — bias this purchase toward a named buyer archetype (BIFL, budget, minimalist, etc.)
- `update-spec` — targeted edit to `spec.md`
- `shop-setup` — configure the marketplaces, VPN egress and delivery addresses the price scanner uses

**Market-landscape commands** (`/procurement-tools:mkt-*`):
- `mkt-spec` — requirement envelope + survey scope (capability-framed, no candidates)
- `mkt-survey` — sweep the market and enumerate the field, breadth first
- `mkt-segment` — derive the segments and the axes the market actually varies along
- `mkt-matrix` — conformance matrix over the whole field, unknowns kept as unknowns
- `mkt-gaps` — unmet and over-served requirements, compromise axes, thin patches
- `mkt-report` — the landscape report (markdown + PDF)
- `mkt-refresh` — re-sweep later and report what changed

**Tech-procurement commands** (`/procurement-tools:rig-*`):
- `rig-setup` — initial hardware-planning interview
- `rig-profile` — document a specific machine's hardware
- `rig-analyze` — identify bottlenecks and upgrade opportunities
- `rig-compare` — compare specific components
- `rig-recommend` — generate upgrade recommendations
- `rig-estimate` — produce a formal cost estimate document

**Vendor-recommendations commands** (`/procurement-tools:rec-*`):
- `rec-onboard` — first-run preference capture (format + availability)
- `rec-more-like-this` — similar-item recommendations from a seed
- `rec-log-feedback` — record like / dislike on past recommendations and update the profile
- `rec-list` — surface recommendation history and feedback status
- `rec-opml-ingest` / `rec-reading-list-ingest` / `rec-watch-history-ingest` — bulk-seed preferences from exports

**Agents**:
- `manufacturer-research`, `price-comparison`, `product-extraction`, `review-aggregation`, `spec-verification` — research sub-agents for the general-purchasing flow
- `preference-curator`, `recommender` — recommendation-profile and suggestion sub-agents

### Skills

All model-invocable, so a subagent can reach for them mid-task.

**Technical-sourcing toolkit** — atomic and composable; each is usable alone, and they chain through shared file formats. See [Technical sourcing](#technical-sourcing).

- **`technical-sourcing`** — the meta skill. Sequences the six below and says which steps this purchase can skip.
- **`spec-as-code`** — versioned `spec.yaml` with stable requirement ids.
- **`spec-sheet-retrieval`** — the manufacturer's own documentation, with the document and revision behind every value.
- **`part-number-equivalence`** — which part numbers name the same product across regions and brands, and which look identical and are not.
- **`evaluation-matrix`** — conformance checking against the spec: pass / fail / partial / unknown, never a score.
- **`bom-build`** — a shopping list written as requirements rather than products.
- **`rfq-package`** — a BOM projected onto a supplier request.

**Everything else:**

- **`price-scan`** — model-invocable. Scans a shortlist of product URLs for current price, stock, shipping and landed cost across your configured marketplaces, from your own machine with the VPN exit set to the country each shop requires. Runs inside any purchase-research repo and writes results there. See [Price scanning](#price-scanning).
- **`/procurement-tools:new-workspace <name> [--variant=general-purchasing|market-landscape|tech-procurement|vendor-recommendations] [--local-only] [--private]`** — scaffolds a new workspace from one of four templates, personalises `CLAUDE.md` from `~/.claude/CLAUDE.md`, and (by default) creates a public GitHub repo for it. `market-landscape` defaults to private.

## Technical sourcing

The half of purchasing where **conformity to a specification decides the buy** and
price is a constraint rather than the question. Most of the market fails the
requirements; the work is finding the ones that do not, and proving it.

```
/procurement-tools:define-spec ──▶ spec-as-code ──▶ evaluation-matrix ──▶ recommend
                                    spec.yaml        criteria.md           │
                                    REQ ids          conformance/*.json    │
                                        │            matrix.md             │
                                        ▼                ▲                 ▼
                                   bom-build ────────────┤            price-scan
                                   bom.yaml, LINE ids    │
                                        │                │
                                        ▼                │
                                   rfq-package           │
                                                         │
                spec-sheet-retrieval ────────────────────┤  evidence
                part-number-equivalence ─────────────────┘  which product is which
```

Every box is a separate skill. They are **atomic on purpose**: pulling one
datasheet, or settling whether a US and a European part number are the same
tool, is a complete task on its own and does not need the rest of the pipeline
dragged along. What makes them a toolkit rather than seven unrelated skills is
that they share file formats and join on ids that are never reused —
requirement ids (`REQ-001`) and BOM line ids (`LINE-001`) thread through every
artefact, so a claim can always be traced back to the document it came from.

Full file contract, join keys and validation gates:
**[`docs/artefact-chain.md`](docs/artefact-chain.md)**.

### Three rules the toolkit enforces

**Unknown beats plausible.** Every verdict is `pass`, `fail`, `partial` or
`unknown`, and `unknown` is a complete answer. A disqualifying requirement
cannot be settled on a retail listing, a review or an inference — the validator
*errors* on that rather than warning, because a plausible wrong `pass` is
indistinguishable from a verified one two steps later, and it propagates into a
shortlist and then into a purchase.

**Nothing is scored.** No weights, no totals, no winner column. A weighted total
needs weights the user has not given, and once a total exists it is the only
thing anyone reads — which buries the single `fail` that actually decides the
purchase. The matrix says what each candidate does and does not do;
`/procurement-tools:recommend` is where a recommendation gets written.

**Specs are versioned, requirements are retired rather than deleted.** Research
that never changes the spec has not learned anything, so the spec is expected to
move — but a conformance record written six weeks ago cites `REQ-004`, and if
`REQ-004` later means something else, that record silently becomes a false
statement about a product. Revisions are pinned in every record and stale ones
are reported as stale.

### The parts that fan out

`spec-sheet-retrieval` and `evaluation-matrix` write **one file per candidate**
rather than one shared table, which is what lets them run as concurrent
subagents without collisions. Launch them together in one message; the matrix is
assembled at read time by `spec_tools.py matrix`.

### Validation

```bash
python3 scripts/spec_tools.py validate-spec spec.yaml
python3 scripts/spec_tools.py criteria spec.yaml -o evaluation/criteria.md
python3 scripts/spec_tools.py validate-conformance evaluation/conformance/*.json --spec spec.yaml
python3 scripts/spec_tools.py matrix spec.yaml evaluation/conformance -o evaluation/matrix.md
python3 scripts/spec_tools.py validate-bom bom.yaml --spec spec.yaml
python3 scripts/spec_tools.py rfq bom.yaml --vendor "Name" --number RFQ-2026-001
```

The script validates and renders; it never judges whether a product meets a
requirement, because a script that guessed at that would launder a guess into a
table. Schemas in [`schema/`](schema), worked examples in [`examples/`](examples).

Tests: `python3 tests/test_spec_tools.py` (offline, synthetic fixtures).

### RFQs stop short of sending

`rfq-package` builds the document and nothing else. The JSON it emits conforms
exactly to the input schema of
[`dsrholdings-rfq`](https://github.com/danielrosehill/dsrholdings-rfq-plugin),
which renders the branded PDF and sends it — that plugin owns supplier
correspondence, and emailing a supplier gets confirmed each time rather than
inherited from a previous approval. For an informal request, the JSON plus a
pasteable plain-text rendering is the deliverable.

## Price scanning

Research tells you *what* to buy. This tells you *what it costs to get it here, now*.

```bash
python3 scripts/price_scan.py --check-egress    # where am I exiting from?
python3 scripts/price_scan.py --address storrs  # price the shortlist
```

The `price-scan` skill drives it, so in practice you just ask for a price scan while sitting in the purchase repo.

### Egress is the whole design

Marketplace prices, stock and shipping quotes are geo-dependent, and a fetch from the wrong country returns real-looking numbers for the wrong market with nothing on the page to signal it. So:

- **Everything egresses from your own machine**, carrying whatever exit your VPN is currently set to. Cloud fetchers (`WebSearch`, `WebFetch`, Tavily, gateway-side fetch) are explicitly barred from sourcing a price — they leave from somewhere else. They remain fine for *finding* candidates.
- Each marketplace declares `requires_geo`. The scanner groups candidates by required exit and **flips the VPN once per country**, not once per candidate — with a kill-switch on, every flip drops connectivity briefly.
- The VPN client is used to *set* the exit; an independent IP lookup is used to *confirm* it. Neither is trusted alone: a client can report "connected" before routes settle, and a location label like `Montreal - Expo 67` doesn't name a country.

### Swapping VPN client

`scripts/vpn_control.py` is the fork point, and it's config-driven rather than code-driven. Windscribe is the reference implementation because it's what the author runs; `mullvad`, `nordvpn` and `protonvpn` command sets are built in too. Anything else needs no code change — declare its command lines in `marketplaces.yaml`:

```yaml
vpn:
  provider: custom
  commands:
    status:  ["myvpn", "status"]
    connect: ["myvpn", "connect", "{location}"]
  locations: { US: "united-states", IL: "israel" }
```

Set `auto_switch: false` to have the scanner stop and print the command instead of changing your connection, or `provider: none` to manage the VPN entirely by hand.

### Public plugin, private config

The plugin is public. Your delivery addresses, account details and VPN setup are not, so they live **outside any repo**, in the plugin data directory (`$CLAUDE_USER_DATA/procurement-tools/` → `$XDG_DATA_HOME/claude-plugins/procurement-tools/` → `~/.local/share/claude-plugins/procurement-tools/`):

| File | Scope | Lives in |
|---|---|---|
| `marketplaces.yaml` | Which shops, which exits, tax rules | Plugin data dir (private) |
| `addresses.yaml` | Destinations, tax rates, deadlines, delivery quirks | Plugin data dir (private) |
| `price-watchlist.yaml` | The shortlist for one purchase | The purchase repo (committed) |
| `data/price-scans/` | Scan reports + `price-history.csv` | The purchase repo (committed) |

Documented examples for all three are in [`examples/`](examples/). Run `/procurement-tools:shop-setup` to generate the private pair by interview.

### What it refuses to do

Amazon and Newegg both sit behind bot protection, so `blocked` is a routine outcome of scripted fetching rather than a defect. The scanner never fills a gap with a guess: unresolved candidates come back with a status (`blocked`, `no_price`, `not_found`, `error`, `skipped_wrong_geo`) and a null price, listed under "Needs a browser" in the report for a `claude-in-chrome` pass in your real, logged-in session on the same exit. Landed costs state their assumptions — unknown shipping counted as zero *and said to be*, unconfirmed tax rates labelled unconfirmed.

Exit codes: `0` everything priced, `1` needs a browser pass (report still written), `2` config or watchlist missing, `3` PyYAML missing.

Tests: `python3 tests/test_price_scan.py` (offline, synthetic fixtures).

## Pattern

Primitives live in the plugin → globally available from any cwd.
Workspace scaffolds are provisioned as **data** → no `.claude/` tree inside provisioned workspaces.
Plugin updates never touch your workspace data.

See [PLAN.md in Claude-Workspace-Reshaping-190426](https://github.com/danielrosehill/Claude-Workspace-Reshaping-190426) for the full pattern spec this plugin follows.

## Variants

- `general-purchasing` (default) — one-purchase-per-repo workflow with spec, buyer profiles, research, and PDF report.
- `market-landscape` — spec-driven survey of a market: what exists that meets a requirement, how the market divides, where the gaps are. Deliberately produces no ranking. Defaults to private.
- `tech-procurement` — hardware rig planning: profile existing machines, analyse bottlenecks, recommend components, produce a formal cost estimate.
- `vendor-recommendations` — ongoing content/vendor recommendation workspace: learns preferences over time, generates similar-item suggestions, tracks feedback.

### Landscape vs purchase

The first two variants point in opposite directions, and picking the wrong one means redoing the work:

| | `market-landscape` | `general-purchasing` |
|---|---|---|
| Starts from | a spec / capability need | a thing you've decided to buy |
| Question | what's out there that meets this? | which of these should I get? |
| Output | a survey of the field + gaps | a ranked recommendation + PDF |
| Ranking | deliberately avoided | the whole point |
| Lifespan | durable, periodically refreshed | disposable, closed at purchase |

They chain: survey the market once, then spin up a purchase repo per actual buy. The landscape repo stays as the standing map and gets `mkt-refresh`ed when the market moves.

A landscape survey can legitimately conclude **"this doesn't exist yet"** — that's a complete answer, and the variant is built to report it as the headline rather than soften it into a nearest-fit suggestion. Buyer profiles are deliberately unavailable here: biasing a survey defeats its purpose. Apply one later, in the purchase repo.

## Install

Via the danielrosehill marketplace:

```
/plugin marketplace add danielrosehill/Claude-Code-Plugins
/plugin install procurement-tools@danielrosehill
```

## License

MIT.
