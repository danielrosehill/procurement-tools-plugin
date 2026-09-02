#!/usr/bin/env python3
"""Create, validate and index procurement workspace manifests.

Every workspace — a standalone repo from `new-workspace`, or a folder inside a
parent repo from `workspace-folder` — carries `procurement.json` at its root.
This script writes it, checks it, and scans a tree for all of them.

    ./workspace.py init . --name laser-measure-0902 --variant general-purchasing
    ./workspace.py validate procurement.json
    ./workspace.py set . --status decided --tag tooling
    ./workspace.py add-report . --kind recommendation --path reports/recommendation-2026-09-02.md
    ./workspace.py purchase . --product "Bosch GLM 165-27 C" --price 449 --currency ILS
    ./workspace.py index ~/repos/github/logistics-procurement --format md

The id (PW-YYYYMMDD-XXXXXX) is written once at init and never rewritten. It is
the join key: renaming the directory, promoting a folder to a repo or moving the
workspace between machines all leave it intact, which is what makes `index`
trustworthy and what a later database would key on.

This script never decides anything about a purchase. It maintains an identity
record and reports what it finds.

Exit codes: 0 clean; 1 validation problems found (all reported, not just the
first); 2 a file is missing or an argument is wrong.

Schema: ../schema/workspace.schema.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import secrets
import sys
from typing import Any

MANIFEST = "procurement.json"
SCHEMA_VERSION = "1.0"
SCHEMA_URL = ("https://github.com/danielrosehill/procurement-tools-plugin"
              "/schema/workspace.schema.json")

WS_ID = re.compile(r"^PW-\d{8}-[0-9A-F]{6}$")
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CURRENCY = re.compile(r"^[A-Z]{3}$")

VARIANTS = ["general-purchasing", "market-landscape",
            "tech-procurement", "vendor-recommendations"]
MODES = ["repo", "folder"]
VISIBILITY = ["private", "public"]
STATUSES = ["open", "decided", "purchased", "abandoned", "superseded"]
REPORT_KINDS = ["recommendation", "landscape", "conformance", "estimate", "rfq"]
CLOSED_STATUSES = {"purchased", "abandoned", "superseded"}


class Problems:
    """Collects every problem so one run reports all of them."""

    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, where: str, msg: str) -> None:
        self.items.append(f"{where}: {msg}")

    def report(self) -> int:
        if not self.items:
            return 0
        print(f"{len(self.items)} problem(s):", file=sys.stderr)
        for i in self.items:
            print(f"  - {i}", file=sys.stderr)
        return 1


def today() -> str:
    return dt.date.today().isoformat()


def new_id(opened: str | None = None) -> str:
    """PW-YYYYMMDD-XXXXXX. Date sorts; hex makes collision irrelevant.

    Random rather than sequential because there is no central allocator —
    workspaces get created on whatever machine is to hand, sometimes offline.
    """
    day = (opened or today()).replace("-", "")
    return f"PW-{day}-{secrets.token_hex(3).upper()}"


def manifest_path(target: str | pathlib.Path) -> pathlib.Path:
    """Accept either a workspace directory or the manifest file itself."""
    p = pathlib.Path(target).expanduser()
    return p if p.is_file() or p.name == MANIFEST else p / MANIFEST


def load(path: pathlib.Path) -> Any:
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        print(f"no manifest at {path}", file=sys.stderr)
        raise SystemExit(2)
    except json.JSONDecodeError as e:
        print(f"{path} is not valid JSON: {e}", file=sys.stderr)
        raise SystemExit(2)


def save(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def spec_revision(root: pathlib.Path, spec_rel: str) -> int | None:
    """Read `revision` out of a spec file, best-effort.

    Returns None rather than raising when PyYAML is absent or the spec is prose
    — a missing revision is a fact about the workspace, not an error here.
    """
    p = root / spec_rel
    if not p.is_file():
        return None
    if p.suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError:
            return None
        try:
            with p.open(encoding="utf-8") as fh:
                doc = yaml.safe_load(fh)
        except Exception:
            return None
        if isinstance(doc, dict) and isinstance(doc.get("revision"), int):
            return doc["revision"]
    return None


def detect_spec(root: pathlib.Path) -> dict | None:
    """Find the governing spec, preferring the machine-readable one."""
    for name in ("spec.yaml", "spec.yml", "spec.md"):
        if (root / name).is_file():
            block: dict[str, Any] = {"path": name}
            rev = spec_revision(root, name)
            if rev is not None:
                block["revision"] = rev
            variants = sorted(p.name for p in root.glob("spec-*.y*ml"))
            if variants:
                block["variants"] = variants
            return block
    return None


# --------------------------------------------------------------------------
# validation
# --------------------------------------------------------------------------

def _enum(m: dict, key: str, allowed: list[str], p: Problems, where: str,
          required: bool = False) -> None:
    v = m.get(key)
    if v is None:
        if required:
            p.add(where, f"missing required field '{key}'")
        return
    if v not in allowed:
        p.add(where, f"{key} is {v!r}, expected one of {', '.join(allowed)}")


def _date(m: dict, key: str, p: Problems, where: str,
          required: bool = False) -> None:
    v = m.get(key)
    if v is None:
        if required:
            p.add(where, f"missing required field '{key}'")
        return
    if not isinstance(v, str) or not ISO_DATE.match(v):
        p.add(where, f"{key} is {v!r}, expected ISO date YYYY-MM-DD")


def validate(m: Any, p: Problems, where: str = MANIFEST) -> None:
    if not isinstance(m, dict):
        p.add(where, "manifest must be a JSON object")
        return

    sv = m.get("schema_version")
    if not isinstance(sv, str) or not re.match(r"^\d+\.\d+$", sv):
        p.add(where, f"schema_version is {sv!r}, expected e.g. '1.0'")

    wid = m.get("id")
    if not isinstance(wid, str) or not WS_ID.match(wid):
        p.add(where, f"id is {wid!r}, expected PW-YYYYMMDD-XXXXXX "
                     "(6 uppercase hex)")

    name = m.get("name")
    if not isinstance(name, str) or not SLUG.match(name):
        p.add(where, f"name is {name!r}, expected kebab-case")

    _enum(m, "variant", VARIANTS, p, where, required=True)
    _enum(m, "mode", MODES, p, where, required=True)
    _enum(m, "status", STATUSES, p, where, required=True)
    _enum(m, "visibility", VISIBILITY, p, where)
    _date(m, "opened", p, where, required=True)
    _date(m, "updated", p, where)

    status = m.get("status")
    closed = m.get("closed")
    if status in CLOSED_STATUSES:
        if not closed:
            p.add(where, f"status is '{status}' but 'closed' is not set")
        else:
            _date(m, "closed", p, where)
    elif closed:
        p.add(where, f"'closed' is set but status is '{status}' — clear one")

    # id date prefix and opened date should agree; a mismatch means one of the
    # two was hand-edited, and the id is the one that must not move.
    if isinstance(wid, str) and WS_ID.match(wid) and isinstance(m.get("opened"), str):
        if wid[3:11] != m["opened"].replace("-", ""):
            p.add(where, f"id date prefix {wid[3:11]} does not match "
                         f"opened {m['opened']} — id is authoritative, "
                         "fix 'opened'")

    if m.get("mode") == "folder":
        par = m.get("parent")
        if not isinstance(par, dict) or not par.get("path"):
            p.add(where, "mode is 'folder' but 'parent.path' is not set — "
                         "an index cannot group siblings without it")
    elif m.get("parent"):
        p.add(where, "'parent' is set but mode is not 'folder'")

    for key in ("supersedes", "superseded_by"):
        v = m.get(key)
        if v is not None and (not isinstance(v, str) or not WS_ID.match(v)):
            p.add(where, f"{key} is {v!r}, expected a PW- id or null")

    if m.get("status") == "superseded" and not m.get("superseded_by"):
        p.add(where, "status is 'superseded' but 'superseded_by' names no id")

    for i, tag in enumerate(m.get("tags") or []):
        if not isinstance(tag, str) or not SLUG.match(tag):
            p.add(where, f"tags[{i}] is {tag!r}, expected kebab-case")

    seen: set[tuple] = set()
    for i, r in enumerate(m.get("reports") or []):
        rw = f"{where} reports[{i}]"
        if not isinstance(r, dict):
            p.add(rw, "must be an object")
            continue
        _date(r, "date", p, rw, required=True)
        _enum(r, "kind", REPORT_KINDS, p, rw, required=True)
        if not r.get("path"):
            p.add(rw, "missing 'path' — the markdown twin always exists")
        key = (r.get("date"), r.get("kind"), r.get("path"))
        if key in seen:
            p.add(rw, f"duplicate report record for {key[2]!r}")
        seen.add(key)

    out = m.get("outcome")
    if out is not None:
        if not isinstance(out, dict):
            p.add(where, "outcome must be an object or null")
        else:
            _date(out, "date", p, f"{where} outcome")
            cur = out.get("currency")
            if cur is not None and (not isinstance(cur, str) or not CURRENCY.match(cur)):
                p.add(f"{where} outcome", f"currency is {cur!r}, expected ISO 4217")
    if m.get("status") == "purchased" and not out:
        p.add(where, "status is 'purchased' but no 'outcome' is recorded")


# --------------------------------------------------------------------------
# subcommands
# --------------------------------------------------------------------------

def cmd_init(a: argparse.Namespace) -> int:
    root = pathlib.Path(a.directory).expanduser()
    if not root.is_dir():
        print(f"{root} is not a directory", file=sys.stderr)
        return 2
    path = root / MANIFEST

    if path.exists() and not a.force:
        existing = load(path)
        print(f"{path} already exists (id {existing.get('id')}). "
              "Use --force to rewrite, or 'set' to change fields.",
              file=sys.stderr)
        return 2

    opened = a.opened or today()
    if not ISO_DATE.match(opened):
        print(f"--opened must be YYYY-MM-DD, got {opened!r}", file=sys.stderr)
        return 2

    name = a.name or root.resolve().name
    m: dict[str, Any] = {
        "$schema": SCHEMA_URL,
        "schema_version": SCHEMA_VERSION,
        "id": a.id or new_id(opened),
        "name": name,
        "variant": a.variant,
        "mode": a.mode,
        "visibility": a.visibility,
        "status": "open",
        "opened": opened,
        "updated": today(),
        "closed": None,
    }
    if a.title:
        m["title"] = a.title
    if a.mode == "folder":
        m["parent"] = {"repo": a.parent_repo or "", "path": a.parent_path or ""}
    spec = detect_spec(root)
    if spec:
        m["spec"] = spec
    m["reports"] = []
    m["tags"] = list(a.tag or [])
    gen: dict[str, str] = {"plugin": "procurement-tools"}
    if a.plugin_version:
        gen["version"] = a.plugin_version
    gen["scaffold"] = a.scaffold or "bundled"
    m["generator"] = gen

    p = Problems()
    validate(m, p, str(path))
    if p.items:
        p.report()
        return 1

    save(path, m)
    print(f"{m['id']}  {path}")
    return 0


def cmd_validate(a: argparse.Namespace) -> int:
    p = Problems()
    n = 0
    for target in a.paths:
        path = manifest_path(target)
        validate(load(path), p, str(path))
        n += 1
    rc = p.report()
    if rc == 0:
        print(f"{n} manifest(s) checked, no problems found")
    return rc


def cmd_set(a: argparse.Namespace) -> int:
    path = manifest_path(a.directory)
    m = load(path)
    changed: list[str] = []

    if a.status:
        if a.status == "purchased" and not m.get("outcome"):
            print("use 'purchase' to close a workspace — it sets status, closed "
                  "date and outcome together, which 'set' cannot do one flag at "
                  "a time", file=sys.stderr)
            return 2
        m["status"] = a.status
        changed.append(f"status={a.status}")
        if a.status in CLOSED_STATUSES:
            m["closed"] = a.closed or today()
        else:
            m["closed"] = None
    if a.title:
        m["title"] = a.title
        changed.append("title")
    if a.visibility:
        m["visibility"] = a.visibility
        changed.append(f"visibility={a.visibility}")
    if a.superseded_by:
        m["superseded_by"] = a.superseded_by
        changed.append("superseded_by")
    if a.tag:
        tags = sorted(set(m.get("tags") or []) | set(a.tag))
        m["tags"] = tags
        changed.append("tags")
    if a.refresh_spec:
        spec = detect_spec(path.parent)
        if spec:
            m["spec"] = spec
            changed.append("spec")

    if not changed:
        print("nothing to change", file=sys.stderr)
        return 2

    m["updated"] = today()
    p = Problems()
    validate(m, p, str(path))
    if p.items:
        p.report()
        return 1
    save(path, m)
    print(f"{m['id']}  updated: {', '.join(changed)}")
    return 0


def cmd_add_report(a: argparse.Namespace) -> int:
    path = manifest_path(a.directory)
    m = load(path)
    rec: dict[str, Any] = {
        "date": a.date or today(),
        "kind": a.kind,
        "path": a.path,
    }
    if a.pdf:
        rec["pdf"] = a.pdf
    if a.spec_revision is not None:
        rec["spec_revision"] = a.spec_revision
    elif isinstance(m.get("spec"), dict) and "revision" in m["spec"]:
        rec["spec_revision"] = m["spec"]["revision"]
    if a.candidates is not None:
        rec["candidates"] = a.candidates
    if a.headline:
        rec["headline"] = a.headline

    m.setdefault("reports", []).append(rec)
    m["updated"] = today()

    p = Problems()
    validate(m, p, str(path))
    if p.items:
        p.report()
        return 1
    save(path, m)
    print(f"{m['id']}  report recorded: {rec['kind']} {rec['date']} {rec['path']}")
    return 0


def cmd_purchase(a: argparse.Namespace) -> int:
    """Close a workspace with what was actually bought.

    Status, closed date and outcome move together — a 'purchased' workspace
    with no outcome is a state the schema rejects, so it must not be reachable
    one flag at a time.
    """
    path = manifest_path(a.directory)
    m = load(path)

    outcome: dict[str, Any] = {"date": a.date or today()}
    for key, val in (("product", a.product), ("manufacturer", a.manufacturer),
                     ("part_number", a.part_number), ("vendor", a.vendor),
                     ("currency", a.currency)):
        if val:
            outcome[key] = val
    if a.price is not None:
        outcome["price"] = a.price
    outcome["matched_report"] = a.matched_report or None

    m["outcome"] = outcome
    m["status"] = "purchased"
    m["closed"] = outcome["date"]
    m["updated"] = today()

    p = Problems()
    validate(m, p, str(path))
    if p.items:
        p.report()
        return 1
    save(path, m)
    note = "" if a.matched_report else "  (no report matched — purchase departed from the recommendation)"
    print(f"{m['id']}  purchased: {outcome.get('product', '?')}{note}")
    return 0


def scan(root: pathlib.Path, follow: bool = False) -> list[tuple[pathlib.Path, dict]]:
    """Walk a tree for manifests, skipping noise directories.

    Deliberately a filesystem scan rather than a service: the manifests are the
    source of truth, so an index can never be stale relative to them.
    """
    skip = {".git", "node_modules", "__pycache__", ".venv", "venv",
            ".pytest_cache", ".mypy_cache"}
    found: list[tuple[pathlib.Path, dict]] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow):
        dirnames[:] = [d for d in dirnames if d not in skip]
        if MANIFEST in filenames:
            p = pathlib.Path(dirpath) / MANIFEST
            try:
                with p.open(encoding="utf-8") as fh:
                    found.append((p, json.load(fh)))
            except (json.JSONDecodeError, OSError):
                found.append((p, {"_unreadable": True}))
    found.sort(key=lambda t: (t[1].get("opened", ""), t[1].get("id", "")))
    return found


def render_index_md(rows: list[tuple[pathlib.Path, dict]], root: pathlib.Path) -> str:
    out = ["# Procurement workspace index", "",
           f"Generated {today()} by `workspace.py index` over `{root}`.",
           f"{len(rows)} workspace(s).", ""]
    bad = [p for p, m in rows if m.get("_unreadable")]
    ok = [(p, m) for p, m in rows if not m.get("_unreadable")]

    by_status: dict[str, int] = {}
    for _, m in ok:
        by_status[m.get("status", "?")] = by_status.get(m.get("status", "?"), 0) + 1
    if by_status:
        out.append("| Status | Count |")
        out.append("| --- | --- |")
        for s in STATUSES:
            if s in by_status:
                out.append(f"| {s} | {by_status[s]} |")
        out.append("")

    out.append("| Id | Opened | Status | Variant | Mode | Name | Reports | Title |")
    out.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for p, m in ok:
        out.append(
            f"| `{m.get('id','?')}` | {m.get('opened','?')} | {m.get('status','?')} "
            f"| {m.get('variant','?')} | {m.get('mode','?')} | {m.get('name','?')} "
            f"| {len(m.get('reports') or [])} | {m.get('title','') or ''} |")
    out.append("")
    out.append("Paths are relative to the scan root:")
    out.append("")
    for p, m in ok:
        try:
            rel = p.parent.relative_to(root)
        except ValueError:
            rel = p.parent
        out.append(f"- `{m.get('id','?')}` — `{rel}`")
    if bad:
        out.append("")
        out.append("## Unreadable")
        out.append("")
        for p in bad:
            out.append(f"- `{p}`")
    return "\n".join(out) + "\n"


def cmd_index(a: argparse.Namespace) -> int:
    root = pathlib.Path(a.root).expanduser().resolve()
    if not root.is_dir():
        print(f"{root} is not a directory", file=sys.stderr)
        return 2
    rows = scan(root, follow=a.follow_symlinks)

    if a.status:
        rows = [(p, m) for p, m in rows if m.get("status") in a.status]
    if a.variant:
        rows = [(p, m) for p, m in rows if m.get("variant") in a.variant]
    if a.tag:
        want = set(a.tag)
        rows = [(p, m) for p, m in rows if want & set(m.get("tags") or [])]

    if a.format == "md":
        text = render_index_md(rows, root)
    else:
        payload = {
            "generated": today(),
            "root": str(root),
            "count": len(rows),
            "workspaces": [
                {**m, "_path": str(p.parent), "_manifest": str(p)}
                for p, m in rows
            ],
        }
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

    if a.out:
        pathlib.Path(a.out).expanduser().write_text(text, encoding="utf-8")
        print(f"{len(rows)} workspace(s) -> {a.out}")
    else:
        sys.stdout.write(text)

    if a.validate:
        p = Problems()
        for path, m in rows:
            if not m.get("_unreadable"):
                validate(m, p, str(path))
        return p.report()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="write procurement.json into a workspace")
    s.add_argument("directory")
    s.add_argument("--name")
    s.add_argument("--title")
    s.add_argument("--variant", choices=VARIANTS, default="general-purchasing")
    s.add_argument("--mode", choices=MODES, default="repo")
    s.add_argument("--visibility", choices=VISIBILITY, default="private",
                   help="default private: a workspace states what you plan to buy")
    s.add_argument("--parent-repo")
    s.add_argument("--parent-path")
    s.add_argument("--opened")
    s.add_argument("--id", help="reuse an existing id; normally omit")
    s.add_argument("--tag", action="append")
    s.add_argument("--plugin-version")
    s.add_argument("--scaffold")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("validate", help="check one or more manifests")
    s.add_argument("paths", nargs="+")
    s.set_defaults(fn=cmd_validate)

    s = sub.add_parser("set", help="update manifest fields")
    s.add_argument("directory")
    s.add_argument("--status", choices=STATUSES)
    s.add_argument("--closed")
    s.add_argument("--title")
    s.add_argument("--visibility", choices=VISIBILITY)
    s.add_argument("--superseded-by")
    s.add_argument("--tag", action="append")
    s.add_argument("--refresh-spec", action="store_true",
                   help="re-read the spec path and revision from disk")
    s.set_defaults(fn=cmd_set)

    s = sub.add_parser("add-report", help="append a dated report record")
    s.add_argument("directory")
    s.add_argument("--kind", choices=REPORT_KINDS, required=True)
    s.add_argument("--path", required=True, help="relative path to the markdown twin")
    s.add_argument("--pdf")
    s.add_argument("--date")
    s.add_argument("--spec-revision", type=int)
    s.add_argument("--candidates", type=int)
    s.add_argument("--headline")
    s.set_defaults(fn=cmd_add_report)

    s = sub.add_parser("purchase", help="close a workspace with what was bought")
    s.add_argument("directory")
    s.add_argument("--product", required=True)
    s.add_argument("--manufacturer")
    s.add_argument("--part-number")
    s.add_argument("--vendor")
    s.add_argument("--price", type=float)
    s.add_argument("--currency")
    s.add_argument("--date")
    s.add_argument("--matched-report",
                   help="path of the report whose pick was followed; omit if it was not")
    s.set_defaults(fn=cmd_purchase)

    s = sub.add_parser("index", help="scan a tree for workspaces")
    s.add_argument("root")
    s.add_argument("-o", "--out")
    s.add_argument("--format", choices=["json", "md"], default="json")
    s.add_argument("--status", action="append", choices=STATUSES)
    s.add_argument("--variant", action="append", choices=VARIANTS)
    s.add_argument("--tag", action="append")
    s.add_argument("--validate", action="store_true",
                   help="also validate every manifest found")
    s.add_argument("--follow-symlinks", action="store_true")
    s.set_defaults(fn=cmd_index)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
