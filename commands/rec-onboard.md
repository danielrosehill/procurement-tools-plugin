---
description: First-run setup for the recommendation workspace — picks format, captures initial preferences, builds the folder structure, and suggests MCPs.
---

# /onboard

Set up this recommendation workspace for the user.

## Steps

### 1. Confirm purpose and format(s)

Ask the user (use AskUserQuestion). Format selection is **multi-select** — the workspace can be specialised for one format or cover several:

- **Formats:** any combination of: Movies, Netflix Series (and other streaming series), Podcasts, Books, YouTube Videos, Online Courses. Allow "Other (custom)" for things outside this list (music, games, papers, newsletters, etc.).
- **Project name:** how they want to refer to this workspace (e.g. "Alex's Podcast Discovery", "Family Movie Night", "CPD Library")
- **Recommendation cadence:** on-demand only / weekly digest / monthly digest
- **Existing data to import:** none / OPML / CSV / JSON / web export — if yes, which command they'll use after onboarding

### 1b. Capture availability context

Ask the user (AskUserQuestion). These are critical — recommendations are useless if the user can't access them. Tailor the questions to the formats chosen in step 1:

- **Geographical area** (always ask) — country/region; affects every format
- **Streaming services** — only if Movies or Netflix Series chosen; multi-select Netflix, Prime, Disney+, Apple TV+, HBO/Max, Hulu, regional services, library streaming (Kanopy/Hoopla)
- **Reading formats** — only if Books chosen; multi-select physical, Kindle, Audible, library ebook (Libby/OverDrive), web/PDF
- **Podcast platform** — only if Podcasts chosen; e.g. Pocket Casts, Apple Podcasts, Spotify, Overcast
- **Course platforms** — only if Online Courses chosen; multi-select Coursera, edX, Udemy, O'Reilly, LinkedIn Learning, free YouTube, university OCW
- **YouTube context** — only if YouTube Videos chosen; Premium status, subscription-driven vs discovery-driven

Write the answers into `memory/preferences.md` under the "Availability context" section.

### 2. Build dynamic folder structure

For each format chosen, create the relevant subfolders. Examples:

- **Movies:** `recommendations/movies/`, `ingest/watch-history/`
- **Netflix Series / streaming series:** `recommendations/series/`, `ingest/watch-history/`
- **Podcasts:** `recommendations/podcasts/shows/`, `recommendations/podcasts/episodes/`, `ingest/opml/`
- **Books:** `recommendations/books/`, `ingest/reading-list/`, `ingest/goodreads/`
- **YouTube Videos:** `recommendations/youtube/channels/`, `recommendations/youtube/videos/`, `ingest/youtube/`
- **Online Courses:** `recommendations/courses/`, `ingest/learning-history/`
- **Custom format:** `recommendations/<format-slug>/`, `ingest/<format-slug>/`

Use the Bash tool to `mkdir -p` and add `.gitkeep` files so the structure is committable. If the workspace covers multiple formats, create the union of all the relevant subfolders.

### 3. Replace placeholders in CLAUDE.md

Open `CLAUDE.md` and replace:

- `{{PROJECT_NAME}}` → the user's project name
- `{{DESCRIPTION}}` → a one-line description of this specific workspace's purpose
- `{{FORMAT}}` → the chosen format(s)

### 4. Seed the preference profile

Ask the user (AskUserQuestion) how they want to populate `memory/preferences.md`:

- **Self-describe** — the user pastes or dictates a free-form description of their tastes, and you structure it into the scaffold sections of `preferences.md`. Best when the user already knows what they like and just wants to dump it.
- **Agent interview** — spawn the `preference-curator` subagent (via the Agent tool) to interview the user. The curator asks open-ended questions about strong likes, dislikes, recent enjoys, constraints, and writes the structured profile back to `memory/preferences.md`. Best when the user wants to be drawn out, or isn't sure how to articulate their taste cold.
- **Skip for now** — leave the scaffold as-is. Use this if the user is about to ingest existing data (OPML, CSV, etc.) and wants the curator to derive the profile from that instead.

Honour the choice. If self-describe, capture the description and write it into the relevant sections of `memory/preferences.md` (don't just dump raw text — slot it under "Strong likes", "Strong dislikes", etc.). If agent interview, hand off cleanly with a prompt that gives the curator the user's chosen format and cadence as context.

### 5. Suggest MCPs

Read `mcp.md` and surface the most relevant MCP servers for the chosen format. For each, tell the user:

- What it adds (e.g. "TMDB gives you canonical film IDs and watch-provider data")
- Where to install it (their MCP Jungle, a plugin, or directly)
- Whether it's required or just recommended

### 6. Capture context

Write `context/onboarding.md` with a record of the choices made — format, cadence, MCPs suggested, ingest plans. The recommender agent reads this for additional context.

### 7. Confirm and next steps

Tell the user:

- The workspace is ready
- Folder structure created
- What command to run next: `/opml-ingest`, `/watch-history-ingest`, `/reading-list-ingest`, or jump straight to asking for recommendations
- Reminder that `/log-feedback` is what makes the recommender improve over time

## Notes

- This command should be safe to re-run — if folders already exist, leave them; if `preferences.md` has content, ask before overwriting.
- Don't proceed to recommendations until `memory/preferences.md` has at least minimal content (likes, dislikes, or ingested history).
