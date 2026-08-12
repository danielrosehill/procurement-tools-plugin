---
name: new-workspace
description: Provision a new purchasing workspace on disk. Use when the user wants to start a new purchase decision, market landscape survey, tech-rig planning exercise, or vendor-recommendation workspace. Accepts a workspace name and optional variant (general-purchasing | market-landscape | tech-procurement | vendor-recommendations). Scaffolds the workspace, personalises CLAUDE.md from the user's global memory, and (by default) creates a GitHub repo.
disable-model-invocation: true
allowed-tools: Bash(mkdir *), Bash(cp *), Bash(cat *), Bash(git init *), Bash(git add *), Bash(git commit *), Bash(gh repo create *), Bash(gh auth status), Bash(git push *), Read
---

# Provision Purchasing Workspace

Creates a new workspace for running a purchase decision, a market landscape survey, or a recommendation exercise. This plugin's commands (`/purchasing:intake`, `/purchasing:research`, `/purchasing:mkt-survey`, `/purchasing:rig-analyze`, `/purchasing:rec-more-like-this`, etc.) are globally available once installed — this skill only provisions the **data scaffold** (CLAUDE.md, spec.md, context/, memory/, etc.) that those commands read from and write to.

## Picking the variant

If the user hasn't named one, the split that matters most is **decision vs survey**:

- They know what they're buying and want to choose between options → `general-purchasing`.
- They have a requirement and want to know what exists that meets it → `market-landscape`.

If it's ambiguous, ask which — the two workspaces are shaped in opposite directions and converting later means redoing the work.

## Arguments

`$ARGUMENTS` is parsed as:

- **First positional**: workspace name (kebab-case, used as directory and GitHub repo name). Required.
- **Second positional** (optional): target parent path. Defaults to `~/repos/github/my-repos`.
- **`--variant=<general-purchasing|market-landscape|tech-procurement|vendor-recommendations>`** (optional): which scaffold to copy. Default: `general-purchasing`.
- **`--local-only`** (optional): skip GitHub repo creation and push. Default: create a public GitHub repo and push.
- **`--private`** (optional): create the GitHub repo as private. Default: public — **except `market-landscape`, which defaults to private** (its spec describes what the user is planning). Pass `--public` to override that.

### Examples

```
/purchasing:new-workspace new-laptop-2026
/purchasing:new-workspace wearable-mic-landscape --variant=market-landscape
/purchasing:new-workspace workstation-rig --variant=tech-procurement
/purchasing:new-workspace podcast-picks --variant=vendor-recommendations --private
/purchasing:new-workspace scratch-buy --local-only
```

## Procedure

### 1. Parse arguments

Extract workspace name, target parent path, variant, and flags from `$ARGUMENTS`. If workspace name is missing, ask the user for it before proceeding.

### 2. Resolve the scaffold path

The bundled scaffold lives at `${CLAUDE_SKILL_DIR}/../../template/<variant>/`. Confirm it exists. If the variant isn't `general-purchasing`, `market-landscape`, `tech-procurement`, or `vendor-recommendations`, tell the user which variants are available.

### 3. Read ambient facts

Read `~/.claude/CLAUDE.md` if it exists. Extract OS, locale, timezone, currency, and user identity facts. These will personalise the workspace's CLAUDE.md at step 6.

### 4. Create the workspace directory

```bash
mkdir -p <target-parent>/<workspace-name>
cp -r ${CLAUDE_SKILL_DIR}/../../template/<variant>/. <target-parent>/<workspace-name>/
```

Do **not** copy any `.claude/` tree. The plugin's primitives are global.

### 5. Personalise CLAUDE.md

Open the new workspace's `CLAUDE.md` and:

- Replace any placeholder identity / `{{PROJECT_NAME}}` tokens with workspace name and ambient facts.
- Add a short header noting the workspace name and variant.
- If ambient facts include OS / locale / currency, embed them so downstream commands can skip re-asking.

### 6. Prompt for workspace-specific facts

Ask the user only for facts this plugin can't infer:

- **general-purchasing**: what the user is buying (category + primary use case). Write into `spec.md` under "What I'm buying". Remind them they can run `/purchasing:intake` to complete the spec interactively.
- **market-landscape**: the requirement in one line, capability-framed (what has to be possible, not which product). Write into `spec.md` under "The requirement". Don't ask for candidates — naming products at provisioning time anchors the sweep to them. Remind them to run `/purchasing:mkt-spec` to set the requirement envelope and the survey scope.
- **tech-procurement**: the target machine label (e.g. `workstation`, `gaming-pc`). Remind them to run `/purchasing:rig-setup` then `/purchasing:rig-profile` to build hardware context.
- **vendor-recommendations**: the format(s) they want recommendations for (films, podcasts, books, etc.). Remind them to run `/purchasing:rec-onboard` to capture preferences.

### 7. Initialise git and (optionally) publish

```bash
cd <target-parent>/<workspace-name>
git init
git add .
git commit -m "Initial workspace from purchasing plugin"
```

Unless `--local-only` is set:

```bash
gh repo create <workspace-name> --<public|private> --source=. --push
```

Use `--public` by default, `--private` if the flag was passed. For `--variant=market-landscape` invert that default: private unless `--public` is passed explicitly.

### 8. Print next steps

Tell the user:

- Workspace path.
- Variant chosen.
- Which plugin commands apply:
  - **general-purchasing** → `/purchasing:intake`, `/purchasing:research`, `/purchasing:compare`, `/purchasing:recommend`, `/purchasing:market-check`, `/purchasing:load-preferences`, `/purchasing:save-preferences`.
  - **market-landscape** → `/purchasing:mkt-spec`, `/purchasing:mkt-survey`, `/purchasing:mkt-segment`, `/purchasing:mkt-matrix`, `/purchasing:mkt-gaps`, `/purchasing:mkt-report`, `/purchasing:mkt-refresh`. Note that `/purchasing:intake`, `/purchasing:research` and `/purchasing:recommend` are deliberately *not* part of this flow — they drive toward a pick.
  - **tech-procurement** → `/purchasing:rig-setup`, `/purchasing:rig-profile`, `/purchasing:rig-analyze`, `/purchasing:rig-compare`, `/purchasing:rig-recommend`, `/purchasing:rig-estimate`.
  - **vendor-recommendations** → `/purchasing:rec-onboard`, `/purchasing:rec-more-like-this`, `/purchasing:rec-log-feedback`, `/purchasing:rec-opml-ingest`, `/purchasing:rec-reading-list-ingest`, `/purchasing:rec-watch-history-ingest`, `/purchasing:rec-list`.
- Reminder that the workspace is **data** — it can be deleted or moved freely without losing the plugin's commands.

## Notes

- The scaffold path must be resolved via `${CLAUDE_SKILL_DIR}/../../template/` (not `${CLAUDE_PLUGIN_ROOT}` — that variable isn't exported in skill bash injection, only in hooks/MCP).
- Never copy `.claude/commands/`, `.claude/agents/`, or `.claude/skills/` into the new workspace. If the user wants workspace-local overrides, they can add them manually later.
- Don't hard-code any personal paths or identifiers here — everything comes from user memory or prompts.
