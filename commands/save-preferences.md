# Save Preferences — Persist Standing Shopping Preferences to Memory

Run a one-time setup (or update) for the user's standing shopping preferences, and save them to memory (Mem0 MCP) so every future purchase workspace can `/load-preferences` them.

## When to run

- First time the user uses any purchasing template — before `/intake`
- When standing preferences change (moved countries, new trusted brand discovered, raised markup threshold after lessons learned)

## What to capture

Walk through these conversationally. Batch related questions. Offer sensible defaults.

### Geographic context

- Country
- Currency
- VAT / sales tax rate
- VAT status (standard consumer / business-reclaimable / exempt)

### Brand attitudes

- Manufacturers you trust across the board
- Manufacturers you avoid across the board (and briefly, why — so the agent can explain disqualifications in future reports)

### Vendor attitudes

- Preferred marketplaces / retailers (across categories)
- Avoided marketplaces / vendors
- International shipping tolerance (yes / only if significant savings / no)

### Thresholds

- Default markup ceiling (% over international RRP you'd accept — typical: 25–50%)
- Review score floor (default 3.5/5)
- Risk tolerance with lesser-known brands (low / medium / high)

### Delivery

- Email for PDF report delivery (optional but recommended)

## Preferred storage: Mem0 MCP

If Mem0 MCP is configured:

1. Structure the answers as a small set of related memories, each tagged `shopping_preferences` (or stored under a dedicated namespace)
2. Use the installed Mem0 server's write tool — commonly `mcp__mem0__add_memory` — to persist
3. One memory per field, OR a single consolidated memory, depending on what the Mem0 server accepts cleanly
4. Report: "Saved N memories to Mem0 under tag `shopping_preferences`."

### Example memory content

Each memory should be self-describing so it can be retrieved individually:

```
Shopping preference (country): [Country]
Shopping preference (currency): [Currency]
Shopping preference (markup threshold): [N]% over international RRP — default; override per-purchase if justified
Shopping preference (trusted brands): [Brand A], [Brand B], [Brand C]
Shopping preference (avoided brands): [Brand X] — [brief reason]; [Brand Y] — [brief reason]
Shopping preference (international shipping): [user's stance]
```

## Fallback: local file

If Mem0 MCP is not available:

1. Write to `<plugin-data-dir>/shopping-preferences.md` (where `<plugin-data-dir>` is `$CLAUDE_USER_DATA/procurement-tools/` if set, else `$XDG_DATA_HOME/claude-plugins/procurement-tools/`, else `~/.local/share/claude-plugins/procurement-tools/` — see the `meta-tools:plugin-data-storage` canonical skill) as a structured markdown file
2. Tell the user: "Saved locally. Install Mem0 MCP (`/plugin install ...`) for cross-device / cross-machine persistence."

## Confirmation

After saving:

1. Echo back what was saved in a compact list
2. Tell the user: "Standing preferences saved. Run `/load-preferences` in any new purchase workspace to pull these in automatically."
3. If this was called as part of `/intake` bootstrap, return control and continue with `/intake`.

## Style

- Don't interrogate — batch and offer defaults
- Assume the user has opinions; prompt for them explicitly rather than leaving blank
- For avoided brands: always ask *why*, briefly. The agent needs the reason so future reports can explain disqualifications.
