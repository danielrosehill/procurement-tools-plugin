---
name: price-scan
description: Scan a shortlist of products for current price, stock, shipping and landed cost across the user's configured marketplaces, from the user's own machine with the VPN exit set to the country each shop requires. Use when comparing live prices across shops, re-checking whether a shortlisted item has moved, working out what something will actually cost delivered to a specific address, or checking which delivery options make a deadline. Works inside any purchase-research repo.
allowed-tools: Bash(python3 *), Bash(./scripts/*), Bash(ls *), Bash(cat *), Bash(mkdir *), Read, Write, Edit, Glob, Grep
---

# Price Scan — Live Prices and Delivery Options for a Shortlist

Turns a shortlist of candidate products into a table of current prices, shipping
options and landed costs, delivered to a named address profile. Designed to run
**inside a purchase-research repo**, writing results into that repo so scans
accumulate next to the research they inform.

The plugin is public; the config it reads is not. Marketplaces, VPN setup and
delivery addresses live in the plugin data directory outside any repo — see
`/procurement-tools:shop-setup`.

## The one rule

**Never source a price from a cloud fetch.** `WebSearch`, `WebFetch`, Tavily and
gateway-side fetchers egress from somewhere that is not the user's machine, so
they return whatever country that host resolves to — a plausible number for the
wrong market, with nothing on the page to signal it. Prices, stock and shipping
quotes come from this machine, through the user's own VPN exit, or they are
marked unavailable. Cloud tools are fine for *finding* candidate products and
reading reviews; they are not fine for pricing them.

## Prerequisites

Config at `<plugin-data-dir>/marketplaces.yaml` and `addresses.yaml`, where
`<plugin-data-dir>` resolves as `$CLAUDE_USER_DATA/procurement-tools/` →
`$XDG_DATA_HOME/claude-plugins/procurement-tools/` →
`~/.local/share/claude-plugins/procurement-tools/` (the convention the plugin's other
commands use). If it's missing, run `/procurement-tools:shop-setup` first rather than
guessing values.

## Flow

### 1. Preflight the exit

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/price_scan.py" --check-egress
```

Reports the observed exit country, whether the VPN client is on PATH, and which
exits the in-scope shops need. This sends one request to a public IP-geolocation
endpoint — that endpoint sees the machine's exit IP and nothing else.

Do this before pricing anything. The failure mode it prevents is silent: a scan
run from the wrong exit returns real-looking numbers in the wrong currency for
the wrong market, and nothing downstream flags it.

### 2. Make sure there's a watchlist

The scanner reads `price-watchlist.yaml` from the repo root. If there isn't one,
create it from `${CLAUDE_PLUGIN_ROOT}/examples/price-watchlist.example.yaml` and
populate it from whatever the repo already knows — a shortlist in `research/`,
candidates in `spec.md`, a comparison table in `docs/`. Confirm the list with
the user before scanning; a watchlist assembled from stale research wastes the
run.

Use **direct product URLs**. Search-result pages are the most heavily
bot-protected part of these sites, and a search URL doesn't pin one product
between runs, which makes the price history meaningless.

### 3. Scan

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/price_scan.py" --address <profile-id>
```

Useful flags: `--marketplace <id>` to restrict to one shop, `--no-vpn` to leave
the connection alone entirely, `--dry-run` to see what it would do to the VPN
without doing it, `--watchlist` / `--out-dir` for non-default paths.

The scanner groups candidates by the exit country their shop requires and flips
the VPN once per country. With a kill-switch enabled each flip briefly drops
connectivity, so never work around this by scanning candidates one at a time
with separate invocations.

Tell the user when the VPN moved and where to. It is their network connection;
a scan that silently leaves them on a different continent is not acceptable even
when `auto_switch` permits the move.

### 4. Finish the blocked rows in a browser

Amazon and Newegg both sit behind bot protection. `blocked` rows are an expected
outcome of scripted fetching, not a defect to debug — the scan report lists them
under "Needs a browser".

For those, use `claude-in-chrome`: a real session, already logged in, already on
the same VPN exit. Read the price, shipping options and delivery estimate off
the page and write them into the scan's markdown report. Mark by-hand rows as
such so a later reader can tell which numbers a script parsed and which a human
read.

Do not click through to checkout, place orders, or trigger confirmation dialogs.
This skill prices things; buying them is the user's action.

### 5. Report

Summarise in the reply: cheapest landed, whether anything is out of stock, which
rows are unresolved, and any delivery option that misses the address profile's
deadline. Point at the generated files rather than pasting them wholesale.

## Output

Written to `data/price-scans/` in the current repo, created if absent:

| File | Contents |
|---|---|
| `<stamp>-scan.md` | Comparison table, unresolved rows, landed-cost workings, run log |
| `<stamp>-scan.json` | Same data structured, for later diffing |
| `price-history.csv` | Appended every run — this is what makes "has it dropped since last week?" answerable |

## Honesty constraints

These matter more than completeness of the table:

- **A missing price stays missing.** The scanner emits `null` with a status
  (`blocked`, `no_price`, `not_found`, `error`, `skipped_wrong_geo`). Never fill
  a gap with a remembered, estimated, or search-result price.
- **Landed cost states its assumptions.** Unknown shipping is counted as zero
  and *said to be*; an unconfirmed tax rate is labelled unconfirmed. Don't
  present a total whose caveats you've dropped.
- **Shipping cost off a product page is indicative.** Real cost usually appears
  at cart. Newegg in particular quotes at cart, not on the page.
- **A price is tied to an exit country and a moment.** Carry both into any claim
  built on it.

## Relationship to the rest of the plugin

`/procurement-tools:research` and `/procurement-tools:compare` decide *what to buy*; this skill
establishes *what it costs to get it here, now*. `/procurement-tools:market-check` does
the strategic version of the same question — local market versus international
RRP with import realism — and reads the same config. Run this when the shortlist
is settled and the question has become procurement rather than selection.
