---
description: Create or update the private marketplace, VPN and delivery-address config the price scanner reads
argument-hint: [nothing — this command interviews you]
---

# Shop Setup — Configure Marketplaces, Egress and Delivery Addresses

Writes the two config files the `price-scan` skill and `/purchasing:market-check`
depend on. Run once, then edit when a shop, address or VPN changes.

## Where the config goes — and where it must not

Resolve `<plugin-data-dir>` as `$CLAUDE_USER_DATA/purchasing/` if set; otherwise
`$XDG_DATA_HOME/claude-plugins/purchasing/`; otherwise
`~/.local/share/claude-plugins/purchasing/`. Create it if absent. This is the
same convention `/load-preferences` uses, so all the plugin's user data sits
together.

Write `marketplaces.yaml` and `addresses.yaml` there. **Never write real values
into the plugin repo or a purchase repo.** The plugin is public and purchase
repos are frequently made public; these files carry a postal address, delivery
contact numbers and account details. The repo gets the examples in
`${CLAUDE_PLUGIN_ROOT}/examples/config/`, nothing else.

If either file already exists, read it first and amend rather than overwrite.

## Interview

Ask only what you can't already determine. Check the environment before asking:
which VPN clients are on PATH, what the existing config holds, whether the user's
global memory or `shopping-preferences.md` already names a country and currency.

### Marketplaces

Two or three is the normal answer — this is a scoped shopping tool, not a
comparison engine. For each:

- **id and name** (`id` is what watchlists reference)
- **Base URL**
- **Currency**
- **`requires_geo`** — the ISO country the VPN must exit from for prices to be
  the ones the user would actually pay. This is the field that makes the whole
  thing work; don't leave it blank because the site "seems to work anyway".
- **Account state** — a paid subscription that changes shipping cost (Prime and
  similar) belongs here, because it changes the maths, not just the experience.
- **Tax rule** — `destination_sales_tax`, `vat_added`, `vat_inclusive`, `none`
- **Shipping options per address profile** — method, cost, and the note that
  explains when it's the right choice

### Egress / VPN

- **Which client.** `windscribe`, `mullvad`, `nordvpn` and `protonvpn` have
  built-in command sets. Anything else: set `provider: custom` and declare
  `commands.status` and `commands.connect` (with `{location}`) directly. Check
  what's actually installed rather than asking blind.
- **`locations` map.** ISO code → the string that client's `connect` wants.
  Clients differ ("US" / "us" / "United_States"), so verify against the client's
  own location list rather than assuming.
- **`auto_switch`.** May the scanner change the connection itself? Ask
  explicitly — this reaches outside the plugin and alters the user's network.
  Off means it stops and prints the command instead.
- **`settle_seconds`.** How long after connecting before routes work. Raise it
  if the first fetch of a batch tends to fail.

### Address profiles

One per place things get delivered to. For each:

- **id and label**, country, currency
- **Address lines**
- **Tax** — `sales_tax_pct` or `vat_pct`. Set `confirmed: true` only if the rate
  has actually been checked for that address; until then every total the scanner
  produces is labelled "rate unconfirmed", which is the correct behaviour.
- **Deadline** — the date after which delivery is worthless, and *why* that date
  (a trip ending, a job starting). Record how firm it is.
- **Constraints** — what disqualifies an otherwise-cheap option. Weight limits,
  luggage, no-signature-available, a delivery window.
- **Local delivery truth** — where the driver actually goes if that isn't the
  street address, access barriers, who to call. Most of this is only learned by
  getting it wrong once; capture it here so it isn't relearned.
- **`reference`** — path or URL to a fuller delivery-instructions document, if
  one exists. Point at it rather than duplicating it.

## After writing

1. Show the user the file paths and a short summary of what went in — shops,
   exits, address ids. Don't echo full addresses back into the transcript.
2. Verify the config parses and the VPN provider resolves:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/price_scan.py" --check-egress
   ```

   This reports the current exit country and whether the client is reachable. It
   sends one request to a public IP-geolocation endpoint and nothing else.

3. If the observed exit doesn't match what the in-scope shops need, say so
   plainly and leave it to the user — setup is not the time to start moving
   their network connection around.

## What this command does not do

- **No preferences.** Brand attitudes, markup thresholds and risk tolerance are
  `/save-preferences`, and live in `shopping-preferences.md`. This file is about
  shops, exits and destinations only.
- **No shortlists.** Candidate products belong in a `price-watchlist.yaml` in
  the purchase repo, not in global config.
- **No credentials.** Marketplace logins live in the browser profile and the
  user's password manager. Never accept a password into these files, and if the
  user offers one, decline and note that `claude-in-chrome` uses their existing
  session.
