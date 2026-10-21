# Load Preferences — Pull Standing Shopping Preferences from Memory

Load the user's standing shopping preferences (country, currency, trusted/avoided brands, markup threshold, risk tolerance, preferred vendors, etc.) into the current session so they can be applied during `/intake`, `/research`, and `/recommend`.

## Migration from legacy path (one-time)

Before resolving the data directory, check for legacy data at these paths:
- `~/.claude/shopping-preferences.md`

If a legacy file exists AND the corresponding file at the new path does NOT exist, move it to the new location and delete the legacy file. Tell the user: "Migrated shopping-preferences.md from ~/.claude/ to <new>."

## Path resolution

Resolve the plugin's data directory as `$CLAUDE_USER_DATA/procurement-tools/` if `CLAUDE_USER_DATA` is set; otherwise `$XDG_DATA_HOME/claude-plugins/procurement-tools/` if `XDG_DATA_HOME` is set; otherwise `~/.local/share/claude-plugins/procurement-tools/`. Create the directory if it doesn't exist. See the canonical convention in the `meta-tools:plugin-data-storage` skill. The local preferences file lives at `<plugin-data-dir>/shopping-preferences.md`.

## What "standing preferences" means

Things that apply to **every** purchase the user makes — not to this specific one:

- **Geographic context**: country, currency, VAT rate, VAT status (consumer / business-reclaimable / exempt)
- **Brand attitudes**: permanently trusted manufacturers, permanently avoided manufacturers
- **Vendor attitudes**: preferred marketplaces/retailers, avoided ones, international shipping tolerance
- **Thresholds**: default markup ceiling (% over international RRP), review score floor, risk tolerance
- **Delivery**: email for PDF report

These are stored in **memory** (the `memory` server on the MCP gateway, recommended), not in any per-purchase repo. One update, all future purchases benefit.

## Preferred storage: gateway `memory` server

The recommended persistence layer is the `memory` upstream on the MCP gateway (tools `mcp__gateway__memory__*`). The tools are deferred — load them with `ToolSearch` (`select:mcp__gateway__memory__recall,mcp__gateway__memory__list_memories`) before the first call. If they resolve:

1. Query memories tagged `shopping_preferences`
2. Parse into the fields listed above
3. Write the snapshot into the **"Standing preferences snapshot"** section of `spec.md`
4. Report to the user what was loaded: "Loaded preferences from memory — country: X, markup threshold: Y%, etc."

### Tool calls

- `mcp__gateway__memory__recall` — `query: "shopping preferences"`, `namespaces: ["personal"]` (or whichever namespace `/save-preferences` used)
- `mcp__gateway__memory__list_memories` — `namespace: "personal"`, then keep the records tagged `shopping_preferences`

## Fallback 1: local file

If the gateway `memory` tools don't resolve, check `<plugin-data-dir>/shopping-preferences.md`. If present, read it and populate the snapshot section of `spec.md` from it.

Tell the user: "Gateway memory server not available. Loaded preferences from `<plugin-data-dir>/shopping-preferences.md` instead (this machine only)."

## Fallback 2: prompt the user

If neither source is available:

1. Tell the user: "No standing preferences found. You can either (a) run `/save-preferences` to set them up now (recommended — one-time setup, benefits every future purchase), or (b) skip and I'll ask you per-purchase questions each time."
2. If the user chooses (a): delegate to `/save-preferences`.
3. If the user chooses (b): proceed — `/intake` will prompt for the standing-preference fields in-line.

## After loading

1. Write the loaded values into `spec.md` → **Standing preferences snapshot** section
2. Report a 3–5 line summary: "Loaded preferences — Country: X, Currency: Y, Markup threshold: Z%. Full snapshot in spec.md. Run `/intake` next."

## What NOT to do

- **Do not write per-purchase information here.** Must-haves, hard nos for this purchase, budget for this purchase, timeline — those belong in `spec.md` via `/intake`.
- **Do not write to memory from this command.** `/load-preferences` is read-only. Writes go through `/save-preferences`.
