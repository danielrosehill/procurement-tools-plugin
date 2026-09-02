# admin

Project tracking for this plugin's **authors**. Nothing here is user surface.

## Why this ships instead of being gitignored

A Claude Code plugin's loadable surface is by convention directory only —
`commands/`, `agents/`, `skills/`, plus `hooks/` and `.mcp.json`. Everything
else in the repo lands on disk at install and is never loaded into a user's
context. `docs/`, `schema/`, `scripts/`, `examples/`, `template/` and `tests/`
already ship on exactly that basis; `admin/` costs a user nothing either.

Gitignoring it instead would defeat the point. The next person to open this
repo is an agent with no memory of the session that wrote these notes and no
way to ask a follow-up question. A roadmap that was never committed is
invisible to that reader, absent from a fresh clone, and gone if the machine
is. Planning material is history, and git is where history goes.

## Rules

**No frontmatter.** Not `name:`, not `description:`, not a `---` block of any
kind. The skill substrate walks plugin repos and ingests skill-shaped content;
frontmatter outside `skills/` is how a planning note gets indexed as a skill by
accident. Plain markdown, plain `#` headings.

**Nothing private.** This repo is public. Anything that should not be
world-readable does not belong here in any form — a `private/` directory is
already covered by the global excludes file, and genuinely sensitive material
belongs outside this repo entirely.

**Absolute dates.** `2026-09-02`, never "recently" or "last week". These notes
are read cold, months later, by someone who cannot infer when "now" was.

## Files

| File | Holds |
| --- | --- |
| `roadmap.md` | What is planned, what is in progress, what was deferred and why |
| `decisions.md` | Design decisions with the reasoning that settled them |
| `debugging.md` | Known defects, reproductions, and wrong turns already ruled out |
