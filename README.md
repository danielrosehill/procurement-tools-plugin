# procurement-tools

Claude Code plugin for running purchasing decisions end-to-end — from intake and spec, through research and comparison, to a recommendation and (optionally) a PDF report. Covers four purchasing surfaces: general consumer/business purchasing, spec-driven market landscape surveys, technical rig procurement, and vendor/content recommendations.

Part of the [danielrosehill Claude Code marketplace](https://github.com/danielrosehill/Claude-Code-Plugins).

## Which plugin do I want?

This plugin is the **general, marketplace-agnostic** half of the buying stack. It is
about the *process*: working out what the thing is, what it has to do, which
candidates qualify, and which one to buy. It never assumes a particular shop.

The **`shopping`** plugin and its regional and per-marketplace siblings are the other
half. They are about *specific places*: how a given retailer's catalogue, language,
currency, tax treatment and stock data actually work.

| You are doing this | Use |
| --- | --- |
| I don't know what this thing is called, or what to search for | **`procurement-tools`** → `define-spec` |
| Turning a want into a spec, then judging candidates against it | **`procurement-tools`** |
| Surveying a whole product category before choosing | **`procurement-tools`** → `mkt-*` |
| Planning a hardware build or rig | **`procurement-tools`** → `rig-*` |
| Finding who stocks it locally, at what price, in stock when | **`shopping`** |
| Israeli retailers, Hebrew terms, Zap, ILS, parallel imports | **`israel-shopping`** |
| One named marketplace's search syntax and quirks | that marketplace's own plugin (`amazon-us`, `aliexpress-israel-skills`, `grainger`, …) |

The two halves are designed to be installed together. Once a question narrows from
"what should I buy" to "how does *this shop* work", the `marketplace-handoff` skill
routes it out of here.

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

- **`price-scan`** — model-invocable. Scans a shortlist of product URLs for current price, stock, shipping and landed cost across your configured marketplaces, from your own machine with the VPN exit set to the country each shop requires. Runs inside any purchase-research repo and writes results there. See [Price scanning](#price-scanning).
- **`/procurement-tools:new-workspace <name> [--variant=general-purchasing|market-landscape|tech-procurement|vendor-recommendations] [--local-only] [--private]`** — scaffolds a new workspace from one of four templates, personalises `CLAUDE.md` from `~/.claude/CLAUDE.md`, and (by default) creates a public GitHub repo for it. `market-landscape` defaults to private.

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
