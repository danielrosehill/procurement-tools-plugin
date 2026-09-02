---
name: workspace-folder
description: Add a purchase-decision folder inside an existing procurement workspace repository, rather than creating a standalone repo for it. Use when the user already has a general procurement or purchasing repo and wants a new subfolder for one decision, when a purchase is too small to deserve its own repo, when several related purchases should live and be diffed together, or when they say "make a folder for this" rather than "make a repo". The standalone-repo sibling is new-workspace.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(mkdir *), Bash(cp *), Bash(cat *), Bash(ls *), Bash(git status), Bash(git rev-parse *), Bash(git add *), Bash(git commit *), Bash(date *)
---

# Purchase folder inside an existing workspace

The sibling of `new-workspace`. Same scaffold, same commands afterwards; the
difference is where it lands and who owns the git history.

| | `new-workspace` | `workspace-folder` |
| --- | --- | --- |
| Creates | A standalone repo | A folder in a repo that already exists |
| `git init` | Yes | **Never** |
| GitHub remote | By default | Inherits the parent's |
| Good for | A significant purchase with its own history | One decision among many; small purchases; a family of related buys |

## Why `new-workspace` cannot do this

`new-workspace` runs `git init` unconditionally — `--local-only` skips only the
GitHub creation and push, not the init. Pointing it inside an existing repo
therefore produces a **nested git repository**: the parent sees an opaque
directory it cannot diff, and the work is tracked by neither history in any
useful way.

That is the whole reason this skill exists. Do not work around it by running
`new-workspace` and deleting `.git` afterwards — the scaffold's commit will
already have been made in the wrong place.

## Choosing between them

Ask for a repo when the purchase has its own life: a long research trail, a
distinct audience, something that will be referred to on its own months later, or
anything that should be public or private *differently* from its neighbours.

Ask for a folder when the decision is one of many of the same kind, when the
value is in comparing it against its neighbours, or when it is small enough that
a repo is ceremony.

**When it is genuinely unclear, prefer the folder.** Promoting a folder to a repo
later is a `git init` and a push. Demoting a repo into a folder means unpicking a
history. If the user has an existing procurement workspace and has not asked for
a repo, they almost certainly mean a folder.

## Procedure

### 1. Establish the parent

Confirm you are inside a git repository and find its root:

```bash
git rev-parse --show-toplevel
```

If this fails, there is no parent workspace. Say so and offer `new-workspace`
instead — do not create a bare directory and leave it untracked.

Read the parent's `CLAUDE.md` and `README.md` if they exist. They set the
conventions this folder should follow, including where decision folders live —
follow the existing layout rather than inventing one. If the parent already has
`decisions/`, `purchases/` or similar, use it.

### 2. Name the folder

Kebab-case, and **dated** where the parent holds a series: `laser-measure-0902`,
matching whatever pattern its neighbours already use. Look before naming; a
folder that sorts differently from its siblings is a small permanent annoyance.

### 3. Copy the scaffold

```bash
mkdir -p <parent-root>/<subdir>/<folder-name>
cp -r "${CLAUDE_SKILL_DIR}/../../template/<variant>/." <parent-root>/<subdir>/<folder-name>/
```

Variants are the same four as `new-workspace`: `general-purchasing` (default),
`market-landscape`, `tech-procurement`, `vendor-recommendations`.

Do **not** copy any `.claude/` tree — the plugin's primitives are global.

### 4. Demote the scaffold's CLAUDE.md

This is the step that differs most from `new-workspace`, and getting it wrong is
the main way this goes bad.

The scaffold ships a `CLAUDE.md` written for a repo root. Two `CLAUDE.md` files
in one repo, one at the root and one three levels down, produce contradictory
standing instructions and the nested one usually wins by accident.

So: **do not keep the scaffold's `CLAUDE.md` as-is.**

- If the parent root already has a `CLAUDE.md` covering procurement conventions,
  **delete** the scaffold's copy. The parent's applies.
- If it says something the parent's does not — a currency, a destination profile,
  a constraint specific to this decision — fold those lines into the folder's
  `README.md` under a "Conventions for this decision" heading, then delete the
  `CLAUDE.md`.
- Only if the parent has no `CLAUDE.md` at all, promote the scaffold's to the
  **parent root**, generalised to cover the whole workspace rather than this one
  decision. Say that you did.

### 5. Personalise the README and spec

In the folder's `README.md`: the decision name, one line on what is being bought,
the date opened, and a link back to the parent workspace root.

In `spec.md` (or `spec.yaml` if going straight to `spec-as-code`), fill in what
is being bought. Then stop — do not invent requirements. `/procurement-tools:intake`
or `/procurement-tools:define-spec` is how the spec gets populated.

### 6. Register it with the parent

A folder that the parent's index does not know about is invisible within a month.

If the parent has an index — a table in its root `README.md`, a `decisions.md`,
anything listing its folders — **add a row**: folder name, what is being bought,
date opened, status `open`. Match the existing format exactly.

If the parent has no index and now holds three or more decision folders, say so
and offer to start one. Do not create it unasked.

### 7. Commit to the parent

```bash
git add <path-to-folder>
git commit -m "Add <folder-name> purchase workspace"
```

One commit, in the parent's history, where it belongs. Do not push unless the
user asks — the parent may have its own release habits.

### 8. Print next steps

Name the folder path, and the commands that follow for the variant chosen — for
`general-purchasing`: `/procurement-tools:intake`, then `/procurement-tools:research`,
then `/procurement-tools:compare`. Note that these read files relative to the
working directory, so they must be run **from inside the new folder**, not the
parent root.

## Promoting a folder to a repo later

If the decision outgrows the folder:

1. `git mv` it out of the parent, or `git filter-repo` if its history is worth keeping.
2. `git init` in the new location, commit, `gh repo create --source=. --push`.
3. Leave a line in the parent's index pointing at the new repo, so the trail
   from the old location does not dead-end.
