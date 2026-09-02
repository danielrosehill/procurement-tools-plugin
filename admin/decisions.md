# Design decisions

Newest first. Each entry records what was decided, why, and what would reverse it.

## 2026-09-02 — Workspace identity lives in a manifest file, not a directory naming convention

Every workspace gets `procurement.json` at its root with a stable
`PW-YYYYMMDD-XXXXXX` id.

A naming convention (`<Thing>-Purchase-MMDD`) was the previous answer and it
does not survive contact with reality: directories get renamed, folders get
promoted to repos, and a name carries no status, no spec revision and no report
trail. Parsing meaning back out of a directory name is guesswork that looks
like data.

The id is random-suffixed rather than sequential because sequential ids need a
central allocator, and there isn't one — workspaces get created on whatever
machine is to hand, sometimes offline. Date prefix keeps them sortable; six hex
characters make collision irrelevant at this volume.

**Would reverse it:** an actual database becoming the source of truth, at which
point the manifest becomes a cache of a row rather than the record itself.

## 2026-09-02 — Private is the default visibility for every workspace variant

Previously public by default, with `market-landscape` inverted to private.

The inversion had the reasoning right and the scope wrong: a landscape spec
describes what the user is planning, and so does a general-purchasing spec, a
tech-procurement rig plan and a vendor-recommendations preference profile. All
four state what someone intends to buy, what they will pay, and often where
they live. Public is the exception, not the rule.

## 2026-09-02 — Admin material ships in the repo rather than being gitignored

`admin/` is committed. Reasoning is in `admin/README.md`; the short version is
that a plugin's loadable surface is by convention directory only, so `admin/`
costs a user nothing, and a gitignored roadmap is invisible to the agent who
opens this repo cold six months from now.

The constraint that makes it safe: **no frontmatter in `admin/`**. The skill
substrate walks plugin repos and ingests skill-shaped content, so a `name:` or
`description:` block outside `skills/` is how a planning note gets indexed as a
skill by accident.

## 2026-09-02 — No GitHub template repo for the workspace scaffold

Considered, and rejected for now.

`gh repo create --template` gives GitHub-native provenance and one fewer local
step. Against that: it cannot serve **folder mode** at all, which is half the
requirement — `workspace-folder` copies a scaffold into an existing repo, and
there is no template mechanism for that. It also introduces a second release
cadence and a permanent drift risk between the template repo and the bundled
`template/` tree, and it makes provisioning need the network.

The bundled scaffold serves both modes, works offline, and is one `cp -r`.

**Would reverse it:** wanting the scaffold usable by people who do not have the
plugin installed. If that happens, the right shape is a **generated mirror** —
the bundled `template/` stays the source of truth and a script publishes it —
rather than a hand-maintained second copy.

## 2026-09-02 — The conformance matrix does not rank, and the ranker is a separate skill

Predates this file; recorded here because it keeps coming up and the separation
looks like duplication until the reason is stated.

`evaluation-matrix` answers "who qualifies" per requirement and deliberately
emits no score. `market-evaluator` is where ranking is allowed to happen. The
split exists because a weighted total buries exactly the trade-off the matrix
was built to expose, and because an `unknown` on a `must` requirement is
missing information rather than a low score — burying it in a ranking presents
ignorance as judgement.
