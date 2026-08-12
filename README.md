# purchasing

Claude Code plugin for running purchasing decisions end-to-end — from intake and spec, through research and comparison, to a recommendation and (optionally) a PDF report. Covers four purchasing surfaces: general consumer/business purchasing, spec-driven market landscape surveys, technical rig procurement, and vendor/content recommendations.

Part of the [danielrosehill Claude Code marketplace](https://github.com/danielrosehill/Claude-Code-Plugins).

## What you get

### Primitives (always available once the plugin is installed)

**General-purchasing commands** (`/purchasing:*`):
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

**Market-landscape commands** (`/purchasing:mkt-*`):
- `mkt-spec` — requirement envelope + survey scope (capability-framed, no candidates)
- `mkt-survey` — sweep the market and enumerate the field, breadth first
- `mkt-segment` — derive the segments and the axes the market actually varies along
- `mkt-matrix` — conformance matrix over the whole field, unknowns kept as unknowns
- `mkt-gaps` — unmet and over-served requirements, compromise axes, thin patches
- `mkt-report` — the landscape report (markdown + PDF)
- `mkt-refresh` — re-sweep later and report what changed

**Tech-procurement commands** (`/purchasing:rig-*`):
- `rig-setup` — initial hardware-planning interview
- `rig-profile` — document a specific machine's hardware
- `rig-analyze` — identify bottlenecks and upgrade opportunities
- `rig-compare` — compare specific components
- `rig-recommend` — generate upgrade recommendations
- `rig-estimate` — produce a formal cost estimate document

**Vendor-recommendations commands** (`/purchasing:rec-*`):
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
- **`/purchasing:new-workspace <name> [--variant=general-purchasing|market-landscape|tech-procurement|vendor-recommendations] [--local-only] [--private]`** — scaffolds a new workspace from one of four templates, personalises `CLAUDE.md` from `~/.claude/CLAUDE.md`, and (by default) creates a public GitHub repo for it. `market-landscape` defaults to private.

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

The plugin is public. Your delivery addresses, account details and VPN setup are not, so they live **outside any repo**, in the plugin data directory (`$CLAUDE_USER_DATA/purchasing/` → `$XDG_DATA_HOME/claude-plugins/purchasing/` → `~/.local/share/claude-plugins/purchasing/`):

| File | Scope | Lives in |
|---|---|---|
| `marketplaces.yaml` | Which shops, which exits, tax rules | Plugin data dir (private) |
| `addresses.yaml` | Destinations, tax rates, deadlines, delivery quirks | Plugin data dir (private) |
| `price-watchlist.yaml` | The shortlist for one purchase | The purchase repo (committed) |
| `data/price-scans/` | Scan reports + `price-history.csv` | The purchase repo (committed) |

Documented examples for all three are in [`examples/`](examples/). Run `/purchasing:shop-setup` to generate the private pair by interview.

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
/plugin install purchasing
```

## License

MIT.
