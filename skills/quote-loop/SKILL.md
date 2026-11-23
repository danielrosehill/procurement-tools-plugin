---
name: quote-loop
description: Get quotes from sellers until there is a good option: research, shortlist, contact, check replies, follow up, compare, repeat
allowed-tools: Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Bash(cat *), Bash(ls *), Bash(date *), Bash(TZ=*), Bash(git *)
---

# Quote loop

The orchestrator for buying from real sellers who have to be asked: stock,
condition, delivery and the real price are only known once a seller confirms
them in writing. It repeats until there is a **good option**: one that meets
the purchase constraints, has price and stock confirmed in writing, and that the
user approves.

## Inputs

- The purchase spec (item, use case, budget, fit questions, delivery city).
  If there isn't one, run `define-spec` / `spec-as-code` first.
- The purchase workspace (repo or folder). The contact log lives there:
  default `docs/sellers-contacted.md`, created from
  `${CLAUDE_PLUGIN_ROOT}/template/quote-loop/contact-log.md`.
- Locale: the user's, else the overlay's `default_locale`, else `default`.
  Profiles: `${CLAUDE_PLUGIN_ROOT}/locales/<locale>.json`.

## User overlay

`${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/procurement-tools/config.json`,
section `quote_loop` (schema in the README). Without it the loop still runs:
drafts instead of sends, the user forwards replies, defaults for constraints.
Say once which parts are degraded.

Record the purchase's constraints (reputable only, new only, excluded sellers)
in the workspace's `CLAUDE.md` or the log header, so every later session and
scheduled check applies the same ones.

## The loop

1. **Research:** `vendor-identification`. Frames the need as local search
   vocabulary, excludes everyone already in the contact log, and fans out over
   the locale's channels (site-restricted web search, aggregators, directories,
   brand-to-importer lookup, maps for showrooms and workshops) into a ranked
   candidate table. Add `price-scan` results or marketplace plugins (see
   `marketplace-handoff`) when the exact model is known.
2. **Shortlist and dedupe:** `seller-shortlist`. Reputable sellers only,
   condition filter, exclusions, one row per operator, nobody already
   contacted.
3. **Contact:** `contact-sellers`. Channel order per locale, varied wording,
   logged at send time with the message or thread ID.
4. **Check replies:** `check-replies` across every configured channel.
5. **Follow up:** inside `check-replies`: answer questions from the spec, ask
   what's needed to confirm price, stock, condition, fit and delivery. Chase
   once at most.
6. **Compare:** `quote-compare` once two or more offers are confirmed, or when
   one confirmed offer might already be good enough.
7. **Decide:** if there's a good option, put it to the user. If not (too few
   replies, all fail a constraint, prices out of budget), go back to step 1 for
   more sellers (`vendor-identification` with wider vocabulary), widening the
   search terms rather than re-contacting.

## Updating the user

Update the user **only when there is an answer**: a seller replied with
substance, or the best option changed. Silent checks stay silent. An update is
one short table of what's new, the current best option, and what's still open.

## Scheduling (optional)

Offer once to run `check-replies` on a recurring timer within the locale's
business hours (e.g. Israel: every 2 hours, Sun-Thu 09-17 and Friday 09-13), via
whatever scheduler the user has (`/loop`, `/schedule`, cron). Don't set one up
without a yes.

## Stop

Stop when the user picks an option. **Ordering, payment and giving a full name
and address are always the user's call**, never the loop's. After the pick,
send the other sellers who quoted a short thank-you only if the user wants that,
and mark their rows closed.

## Data storage

Reads the user overlay (read-only) and the plugin's locale profiles. Writes the
contact log and, optionally, the constraints note in the user's purchase
workspace. Nothing in plugin data.

## Notes

- Sends messages from the user's accounts through `contact-sellers` and
  `check-replies`; their approval rules apply.
- Absorbs `israel-shopping:ask-store`: the Israeli message template, channel
  order and grading now live in `locales/israel.json` and these skills.
