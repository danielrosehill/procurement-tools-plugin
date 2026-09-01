#!/usr/bin/env python3
"""Validate and render the spec / conformance / BOM / RFQ artefact chain.

The technical-sourcing skills all read and write the same four files, and this
script is what stops them drifting apart. It is deliberately dumb: it checks
structure and cross-references, and it renders. It never decides whether a
product meets a requirement — that is the model's job, and a script that
guessed at it would launder a guess into a table.

    ./spec_tools.py validate-spec spec.yaml
    ./spec_tools.py criteria spec.yaml -o evaluation/criteria.md
    ./spec_tools.py validate-conformance evaluation/conformance/*.json --spec spec.yaml
    ./spec_tools.py matrix spec.yaml evaluation/conformance -o evaluation/matrix.md
    ./spec_tools.py validate-bom bom.yaml [--spec spec.yaml]
    ./spec_tools.py rfq bom.yaml --vendor "Acme Ltd" --number RFQ-2026-001

Exit codes: 0 clean; 1 validation problems found (all of them reported, not
just the first); 2 a file is missing or an argument is wrong; 3 PyYAML missing.

Schemas live in ../schema/. Requirement ids (REQ-nnn) and BOM line ids
(LINE-nnn) are the join keys across every artefact and are never reused, so
most of what this script checks is that a reference still resolves.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
from typing import Any

try:
    import yaml
except ImportError:
    print("spec_tools.py needs PyYAML (pip install pyyaml, or: uv pip install pyyaml)", file=sys.stderr)
    raise SystemExit(3)

REQ_ID = re.compile(r"^REQ-\d{3,}$")
LINE_ID = re.compile(r"^LINE-\d{3,}$")
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RFQ_NUMBER = re.compile(r"^RFQ-\d{4}-\d{3}$")

KINDS = {"must", "must-not", "nice"}
VERDICTS = {"pass", "fail", "partial", "unknown"}
VERIFY = {
    "datasheet", "manual", "standard", "vendor-confirmation",
    "hands-on", "third-party-test", "review-consensus", "inspection",
}
SUBSTITUTION = {"allowed", "equivalent-only", "none"}

# Source classes that cannot settle a `must` on their own. Kept here rather
# than in the schema because it is a judgement rule, not a structural one.
WEAK_SOURCES = {"retail-listing", "review", "inference"}


class Problems:
    """Collects every problem rather than dying on the first one."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def report(self, label: str) -> int:
        for w in self.warnings:
            print(f"warn  {label}: {w}")
        for e in self.errors:
            print(f"ERROR {label}: {e}")
        if not self.errors and not self.warnings:
            print(f"ok    {label}")
        elif not self.errors:
            print(f"ok    {label} ({len(self.warnings)} warning(s))")
        return 1 if self.errors else 0


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def _iso_dates(node: Any) -> Any:
    """YAML parses an unquoted 2026-09-20 into a date object, which then fails
    to serialise into the RFQ JSON. Normalise on the way in so the rest of the
    script only ever sees ISO strings."""
    if isinstance(node, dict):
        return {k: _iso_dates(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_iso_dates(v) for v in node]
    if isinstance(node, dt.datetime):
        return node.date().isoformat()
    if isinstance(node, dt.date):
        return node.isoformat()
    return node


def load(path: pathlib.Path) -> Any:
    if not path.exists():
        print(f"not found: {path}", file=sys.stderr)
        raise SystemExit(2)
    text = path.read_text(encoding="utf-8")
    try:
        if path.suffix in (".yaml", ".yml"):
            return _iso_dates(yaml.safe_load(text))
        return json.loads(text)
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        print(f"unparseable: {path}: {exc}", file=sys.stderr)
        raise SystemExit(2)


def requirements(spec: dict, include_retired: bool = False) -> list[dict]:
    reqs = spec.get("requirements") or []
    if include_retired:
        return reqs
    return [r for r in reqs if not r.get("retired")]


def req_title(req: dict) -> str:
    title = req.get("title")
    if title:
        return title
    stmt = (req.get("statement") or "").strip().replace("\n", " ")
    return stmt[:60] + ("…" if len(stmt) > 60 else "")


# ---------------------------------------------------------------------------
# validate-spec
# ---------------------------------------------------------------------------

def validate_spec(spec: Any, p: Problems) -> None:
    if not isinstance(spec, dict):
        p.error("top level is not a mapping")
        return

    if spec.get("spec_version") != 1:
        p.error(f"spec_version must be 1, got {spec.get('spec_version')!r}")
    for field in ("id", "title", "revision", "requirements"):
        if field not in spec:
            p.error(f"missing required field: {field}")
    if isinstance(spec.get("id"), str) and not SLUG.match(spec["id"]):
        p.error(f"id {spec['id']!r} is not a lowercase slug")
    if isinstance(spec.get("revision"), bool) or not isinstance(spec.get("revision"), int):
        p.error("revision must be an integer")
    if spec.get("revised") and not ISO_DATE.match(str(spec["revised"])):
        p.error(f"revised {spec['revised']!r} is not YYYY-MM-DD")
    if not spec.get("scope"):
        p.warn("no scope — subagents get the requirement list with no idea what it is for")
    if not spec.get("out_of_scope"):
        p.warn("no out_of_scope — nothing stops an incidental attribute becoming a filter downstream")

    reqs = spec.get("requirements")
    if not isinstance(reqs, list) or not reqs:
        p.error("requirements must be a non-empty list")
        return

    seen: dict[str, int] = {}
    highest = 0
    for i, req in enumerate(reqs):
        where = f"requirements[{i}]"
        if not isinstance(req, dict):
            p.error(f"{where} is not a mapping")
            continue
        rid = req.get("id")
        if not isinstance(rid, str) or not REQ_ID.match(rid):
            p.error(f"{where} id {rid!r} must match REQ-nnn")
            continue
        where = rid
        if rid in seen:
            p.error(f"{rid} is defined twice (requirements[{seen[rid]}] and [{i}]) — ids are never reused")
        seen[rid] = i
        highest = max(highest, int(rid.split("-")[1]))

        if req.get("kind") not in KINDS:
            p.error(f"{where} kind {req.get('kind')!r} not one of {sorted(KINDS)}")
        if not req.get("statement"):
            p.error(f"{where} has no statement")
        if req.get("verify") not in VERIFY:
            p.error(f"{where} verify {req.get('verify')!r} not one of {sorted(VERIFY)}")
        if not req.get("evidence"):
            p.warn(f"{where} has no evidence line — a research subagent will not know what settles it")
        if req.get("kind") in ("must", "must-not") and not req.get("rationale"):
            p.warn(f"{where} is disqualifying but has no rationale — nothing to read when deciding to relax it")

        op = req.get("operator")
        if op and not req.get("parameter"):
            p.warn(f"{where} has operator {op!r} but no parameter")
        if op in ("eq", "ne", "gte", "lte", "matches") and req.get("value") is None:
            p.error(f"{where} operator {op!r} needs a value")
        if op == "in" and not isinstance(req.get("value"), list):
            p.error(f"{where} operator 'in' needs a list value")
        if op == "range":
            val = req.get("value")
            if not isinstance(val, list) or len(val) != 2:
                p.error(f"{where} operator 'range' needs a two-element [min, max] value")
        if op in ("gte", "lte", "range") and not req.get("unit"):
            p.warn(f"{where} is a numeric comparison with no unit")

        if req.get("retired") and not req.get("retired_in"):
            p.warn(f"{where} is retired but does not say in which revision")

    # Numbering discipline: gaps are fine (retirements), but an id above the
    # count of requirements with nothing retired usually means a hand edit.
    if highest > len(reqs) and not any(r.get("retired") for r in reqs if isinstance(r, dict)):
        p.warn(f"highest id is REQ-{highest:03d} but there are {len(reqs)} requirements and none are retired")

    history = spec.get("history") or []
    if isinstance(spec.get("revision"), int) and spec["revision"] > 1 and not history:
        p.warn("revision > 1 with no history — the record of what changed is the point of versioning this")
    revs = [h.get("revision") for h in history if isinstance(h, dict)]
    if revs and isinstance(spec.get("revision"), int) and max(revs) != spec["revision"]:
        p.error(f"history top revision {max(revs)} does not match revision {spec['revision']}")


# ---------------------------------------------------------------------------
# criteria — the briefing document handed to research subagents
# ---------------------------------------------------------------------------

def render_criteria(spec: dict) -> str:
    reqs = requirements(spec)
    musts = [r for r in reqs if r.get("kind") == "must"]
    must_nots = [r for r in reqs if r.get("kind") == "must-not"]
    nices = [r for r in reqs if r.get("kind") == "nice"]

    out: list[str] = []
    w = out.append
    w(f"# Evaluation criteria — {spec.get('title', spec.get('id'))}")
    w("")
    w(f"*Generated from `spec.yaml` revision {spec.get('revision')} "
      f"({spec.get('revised', 'undated')}) by `spec_tools.py criteria`. Do not edit by hand — "
      f"edit the spec and regenerate.*")
    w("")
    w("This is the backing document for anyone — human or subagent — judging a candidate. "
      "It is not a ranking scheme. Each requirement is checked independently and answered "
      "`pass`, `fail`, `partial` or `unknown`. Nothing is scored, weighted or totalled.")
    w("")
    if spec.get("scope"):
        w("## What is being specified")
        w("")
        w(str(spec["scope"]).strip())
        w("")
    if spec.get("out_of_scope"):
        w("## Explicitly not required")
        w("")
        w("A candidate is **not** penalised for lacking any of these, and a candidate is not "
          "preferred for having them.")
        w("")
        for item in spec["out_of_scope"]:
            w(f"- {item}")
        w("")

    w("## How to answer a requirement")
    w("")
    w("| Verdict | Use when |")
    w("|---|---|")
    w("| `pass` | The evidence class named in the requirement says so, and you have the source. |")
    w("| `fail` | Same standard of evidence, negative. |")
    w("| `partial` | Met under a condition. The condition goes in the note; a `partial` with no stated condition is an `unknown`. |")
    w("| `unknown` | You could not establish it to that standard. Record what would settle it. |")
    w("")
    w("`unknown` is a complete answer and always beats a plausible guess. A wrong `pass` "
      "propagates into a shortlist and then into a purchase; an `unknown` only costs another "
      "search. Where sources disagree, record `unknown` and keep both sources rather than "
      "picking one.")
    w("")

    def block(title: str, items: list[dict], preamble: str = "") -> None:
        if not items:
            return
        w(f"## {title}")
        w("")
        if preamble:
            w(preamble)
            w("")
        for r in items:
            w(f"### {r['id']} — {req_title(r)}")
            w("")
            w(str(r.get("statement", "")).strip())
            w("")
            if r.get("parameter"):
                bits = [f"`{r['parameter']}`"]
                if r.get("operator"):
                    bits.append(f"`{r['operator']}`")
                if r.get("value") is not None:
                    bits.append(f"`{json.dumps(r['value'])}`")
                if r.get("unit"):
                    bits.append(str(r["unit"]))
                w(f"- **Test:** {' '.join(bits)}")
            w(f"- **Settled by:** {r.get('verify', '—')}")
            if r.get("evidence"):
                w(f"- **What counts:** {str(r['evidence']).strip()}")
            if r.get("rejects"):
                w(f"- **Does not count:** {str(r['rejects']).strip()}")
            if r.get("rationale"):
                w(f"- **Why:** {str(r['rationale']).strip()}")
            w("")

    block("Must have", musts,
          "Failing any one of these disqualifies the candidate. Check them first — a `fail` "
          "here ends the evaluation and the remaining requirements need not be researched.")
    block("Must not have", must_nots,
          "Read these as characteristics, not as compliance. `pass` means the disqualifying "
          "characteristic is **absent**.")
    block("Nice to have", nices,
          "Tie-breakers only. These never disqualify and are never totalled into a score. "
          "They are recorded so that a choice between candidates that both clear every must "
          "has something to rest on.")

    retired = [r for r in requirements(spec, include_retired=True) if r.get("retired")]
    if retired:
        w("## Retired requirements")
        w("")
        w("Kept so that conformance records written against earlier revisions stay readable. "
          "Do not research these.")
        w("")
        for r in retired:
            w(f"- `{r['id']}` — {req_title(r)} "
              f"(retired in revision {r.get('retired_in', '?')}"
              f"{': ' + str(r['retired_reason']) if r.get('retired_reason') else ''})")
        w("")

    w("## Recording the answer")
    w("")
    w("One JSON file per candidate under `evaluation/conformance/`, conforming to "
      "`schema/conformance.schema.json`. One file per candidate rather than one shared "
      "table, so that several subagents can evaluate different candidates at once without "
      "writing to the same file. Then:")
    w("")
    w("```bash")
    w("spec_tools.py validate-conformance evaluation/conformance/*.json --spec spec.yaml")
    w("spec_tools.py matrix spec.yaml evaluation/conformance -o evaluation/matrix.md")
    w("```")
    w("")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# validate-conformance
# ---------------------------------------------------------------------------

def validate_conformance(rec: Any, spec: dict | None, p: Problems) -> None:
    if not isinstance(rec, dict):
        p.error("top level is not a mapping")
        return
    if rec.get("conformance_version") != 1:
        p.error(f"conformance_version must be 1, got {rec.get('conformance_version')!r}")

    cand = rec.get("candidate")
    if not isinstance(cand, dict) or not cand.get("id") or not cand.get("name"):
        p.error("candidate needs at least id and name")
    elif not SLUG.match(str(cand["id"])):
        p.error(f"candidate id {cand['id']!r} is not a lowercase slug")

    if rec.get("evaluated") and not ISO_DATE.match(str(rec["evaluated"])):
        p.error(f"evaluated {rec['evaluated']!r} is not YYYY-MM-DD")

    ref = rec.get("spec") or {}
    if spec is not None:
        if ref.get("id") != spec.get("id"):
            p.error(f"spec.id {ref.get('id')!r} does not match the spec being validated ({spec.get('id')!r})")
        elif ref.get("revision") != spec.get("revision"):
            p.warn(f"evaluated against spec revision {ref.get('revision')}, current is "
                   f"{spec.get('revision')} — stale, re-check the cells the revision touched")

    cells = rec.get("cells")
    if not isinstance(cells, list):
        p.error("cells must be a list")
        return

    known = {r["id"] for r in requirements(spec, include_retired=True)} if spec else set()
    live = {r["id"] for r in requirements(spec)} if spec else set()
    covered: set[str] = set()

    for i, cell in enumerate(cells):
        if not isinstance(cell, dict):
            p.error(f"cells[{i}] is not a mapping")
            continue
        rid = cell.get("req")
        if not isinstance(rid, str) or not REQ_ID.match(rid):
            p.error(f"cells[{i}] req {rid!r} must match REQ-nnn")
            continue
        if rid in covered:
            p.error(f"{rid} has two cells")
        covered.add(rid)
        if known and rid not in known:
            p.error(f"{rid} is not in the spec")

        verdict = cell.get("verdict")
        if verdict not in VERDICTS:
            p.error(f"{rid} verdict {verdict!r} not one of {sorted(VERDICTS)}")
            continue

        if verdict == "partial" and not cell.get("note"):
            p.error(f"{rid} is 'partial' with no note — the condition is the whole content of a partial")
        if verdict == "unknown" and not cell.get("resolves_to"):
            p.warn(f"{rid} is 'unknown' with no resolves_to — say what would settle it")
        if verdict in ("pass", "fail") and not cell.get("source"):
            p.error(f"{rid} is '{verdict}' with no source")

        src = cell.get("source")
        if isinstance(src, dict) and spec and rid in live:
            req = next((r for r in requirements(spec) if r["id"] == rid), None)
            if req and req.get("kind") in ("must", "must-not") and verdict in ("pass", "fail"):
                if src.get("type") in WEAK_SOURCES:
                    p.error(f"{rid} is disqualifying and is settled on a {src['type']} — "
                            f"the spec asks for {req.get('verify')}. Mark it unknown instead.")
                if src.get("type") in ("datasheet", "manual") and not src.get("doc_revision"):
                    p.warn(f"{rid} cites a document with no doc_revision — manufacturers "
                           f"replace documents at the same URL")

    if live:
        missing = sorted(live - covered)
        if missing:
            p.error(f"no cell for: {', '.join(missing)}")

    # clears_all_must is derivable, so it is checked rather than trusted.
    if spec and "clears_all_must" in rec:
        p.warn("clears_all_must is not part of the schema and is derived by `matrix` — remove it")


def clears_all_must(rec: dict, spec: dict) -> str:
    verdicts = {c.get("req"): c.get("verdict") for c in rec.get("cells", []) if isinstance(c, dict)}
    disqualifying = [r["id"] for r in requirements(spec) if r.get("kind") in ("must", "must-not")]
    if any(verdicts.get(rid) == "fail" for rid in disqualifying):
        return "no"
    if any(verdicts.get(rid) in (None, "unknown", "partial") for rid in disqualifying):
        return "?"
    return "yes"


# ---------------------------------------------------------------------------
# matrix
# ---------------------------------------------------------------------------

CELL_GLYPH = {"pass": "yes", "fail": "no", "partial": "part", "unknown": "?"}


def render_matrix(spec: dict, records: list[tuple[pathlib.Path, dict]]) -> str:
    reqs = requirements(spec)
    musts = [r for r in reqs if r.get("kind") == "must"]
    must_nots = [r for r in reqs if r.get("kind") == "must-not"]
    nices = [r for r in reqs if r.get("kind") == "nice"]
    records = sorted(records, key=lambda t: t[1].get("candidate", {}).get("name", ""))

    out: list[str] = []
    w = out.append
    w(f"# Conformance matrix — {spec.get('title', spec.get('id'))}")
    w("")
    w(f"*Generated by `spec_tools.py matrix` from `spec.yaml` revision {spec.get('revision')} "
      f"and {len(records)} conformance record(s) on {dt.date.today().isoformat()}. "
      f"Do not edit by hand.*")
    w("")
    w("`yes` / `no` / `part` / `?` — never a score. `?` means not established to the standard "
      "the requirement asks for, and is left as `?`.")
    w("")

    def table(title: str, group: list[dict], note: str = "") -> None:
        if not group:
            return
        w(f"## {title}")
        w("")
        if note:
            w(note)
            w("")
        w("| Candidate | " + " | ".join(r["id"] for r in group) + " |")
        w("|---|" + "---|" * len(group))
        for _, rec in records:
            cand = rec.get("candidate", {})
            verdicts = {c.get("req"): c.get("verdict") for c in rec.get("cells", []) if isinstance(c, dict)}
            row = [CELL_GLYPH.get(verdicts.get(r["id"]), "—") for r in group]
            w(f"| {cand.get('name', cand.get('id', '?'))} | " + " | ".join(row) + " |")
        w("")
        w("| Id | Requirement |")
        w("|---|---|")
        for r in group:
            w(f"| {r['id']} | {req_title(r)} |")
        w("")

    table("Must have", musts)
    table("Must not have", must_nots,
          "`yes` here means the disqualifying characteristic is **absent** — the column is "
          "read as compliance, matching the must-have tables above.")
    table("Nice to have", nices, "Tie-breakers. Not totalled.")

    w("## Clears every disqualifying requirement")
    w("")
    w("| Candidate | Part number | Clears? |")
    w("|---|---|---|")
    for _, rec in records:
        cand = rec.get("candidate", {})
        w(f"| {cand.get('name', cand.get('id', '?'))} | {cand.get('part_number', '—')} | "
          f"{clears_all_must(rec, spec)} |")
    w("")
    w("`?` means an open requirement, not a near miss — it is a candidate that has not been "
      "excluded yet.")
    w("")

    # Column-level readings: these are what the matrix exists to expose. A
    # column with one or two entries in it says nothing about a field, so they
    # are only emitted once there is a field to read.
    findings: list[str] = []
    disqualifying = musts + must_nots
    if len(records) >= 3:
        for r in disqualifying:
            col = [
                next((c.get("verdict") for c in rec.get("cells", []) if c.get("req") == r["id"]), None)
                for _, rec in records
            ]
            if all(v == "unknown" for v in col):
                findings.append(f"- **{r['id']} is unknown across the whole field.** No candidate "
                                f"publishes it, so it cannot be compared before buying. Either drop "
                                f"it, or resolve it by asking vendors directly.")
            elif all(v == "fail" for v in col):
                findings.append(f"- **Nothing clears {r['id']}.** Either the requirement is wrong or "
                                f"the market does not serve it. This is a finding, not a dead end.")
            elif all(v == "pass" for v in col):
                findings.append(f"- **Everything clears {r['id']}.** It is not separating anything; "
                                f"it is a property of the category rather than a requirement.")

    verdicts = [clears_all_must(rec, spec) for _, rec in records]
    if records and "yes" not in verdicts:
        if all(v == "no" for v in verdicts):
            findings.append("- **No candidate clears every disqualifying requirement**, and none is "
                            "merely unresolved — every one has a confirmed failure. Say so as the "
                            "headline rather than presenting the nearest miss as a recommendation.")
        else:
            open_reqs = sorted({
                c["req"] for _, rec in records for c in rec.get("cells", [])
                if c.get("req") in {r["id"] for r in disqualifying}
                and c.get("verdict") in ("unknown", "partial")
            })
            findings.append("- **No candidate has been confirmed to clear every disqualifying "
                            "requirement yet.** This is an unfinished evaluation, not an empty "
                            "field: the open cells are "
                            + ", ".join(open_reqs) + ". Resolve those before concluding anything.")

    if findings:
        w("## What the matrix says about the field")
        w("")
        out.extend(findings)
        w("")

    w("## Sources")
    w("")
    for path, rec in records:
        cand = rec.get("candidate", {})
        w(f"- `{cand.get('id', '?')}` — {cand.get('name', '?')}, evaluated "
          f"{rec.get('evaluated', 'undated')} against revision "
          f"{rec.get('spec', {}).get('revision', '?')} (`{path.name}`)")
    w("")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# validate-bom
# ---------------------------------------------------------------------------

def validate_bom(bom: Any, spec: dict | None, p: Problems) -> None:
    if not isinstance(bom, dict):
        p.error("top level is not a mapping")
        return
    if bom.get("bom_version") != 1:
        p.error(f"bom_version must be 1, got {bom.get('bom_version')!r}")
    for field in ("id", "title", "revision", "lines"):
        if field not in bom:
            p.error(f"missing required field: {field}")
    if isinstance(bom.get("id"), str) and not SLUG.match(bom["id"]):
        p.error(f"id {bom['id']!r} is not a lowercase slug")
    if not bom.get("purpose"):
        p.warn("no purpose — suppliers quote worse without one, and cannot propose a sane substitute")

    lines = bom.get("lines")
    if not isinstance(lines, list) or not lines:
        p.error("lines must be a non-empty list")
        return

    seen: set[str] = set()
    known_reqs = {r["id"] for r in requirements(spec, include_retired=True)} if spec else set()

    for i, line in enumerate(lines):
        if not isinstance(line, dict):
            p.error(f"lines[{i}] is not a mapping")
            continue
        lid = line.get("id")
        if not isinstance(lid, str) or not LINE_ID.match(lid):
            p.error(f"lines[{i}] id {lid!r} must match LINE-nnn")
            continue
        if lid in seen:
            p.error(f"{lid} is defined twice — line ids are never reused")
        seen.add(lid)

        if not line.get("description"):
            p.error(f"{lid} has no description")
        if line.get("quantity") in (None, ""):
            p.error(f"{lid} has no quantity")
        sub = line.get("substitution", "equivalent-only")
        if sub not in SUBSTITUTION:
            p.error(f"{lid} substitution {sub!r} not one of {sorted(SUBSTITUTION)}")

        ref = line.get("spec_ref")
        if sub == "equivalent-only" and not ref:
            p.warn(f"{lid} is 'equivalent-only' with no spec_ref — nothing defines what equivalent means")
        if ref and known_reqs:
            spec_id, _, req_list = str(ref).partition("#")
            if spec.get("id") and spec_id and spec_id != spec["id"]:
                p.warn(f"{lid} spec_ref points at {spec_id!r}, not the spec given ({spec['id']!r}) — not checked")
            elif req_list:
                for rid in [x.strip() for x in req_list.split(",") if x.strip()]:
                    if not REQ_ID.match(rid):
                        p.error(f"{lid} spec_ref names {rid!r}, which is not a REQ-nnn id")
                    elif rid not in known_reqs:
                        p.error(f"{lid} spec_ref names {rid}, which is not in the spec")

        ident = line.get("identified")
        if isinstance(ident, dict):
            if ident.get("part_number") and not ident.get("manufacturer"):
                p.warn(f"{lid} has a part number with no manufacturer — part numbers are not unique across makers")
            if ident.get("part_number") and not ident.get("region"):
                p.warn(f"{lid} has a part number with no region — the same product carries different "
                       f"numbers per market and a supplier will quote whichever it stocks")
        if sub == "none" and not (isinstance(ident, dict) and ident.get("part_number")):
            p.error(f"{lid} forbids substitution but names no part number")

    groups = bom.get("groups") or []
    for g in groups:
        if not isinstance(g, dict):
            p.error("groups entries must be mappings")
            continue
        for lid in g.get("lines", []):
            if lid not in seen:
                p.error(f"group {g.get('name')!r} references unknown line {lid}")


# ---------------------------------------------------------------------------
# rfq — emit the JSON that dsrholdings-rfq renders
# ---------------------------------------------------------------------------

def bom_to_rfq(bom: dict, vendor: str, number: str, *, group: str | None = None,
               targets: bool = False, questions: list[str] | None = None) -> dict:
    """Project a BOM onto the dsrholdings-rfq input schema.

    That schema is `additionalProperties: false`, so nothing procurement-tools
    specific may be smuggled into the document — line provenance stays in the
    BOM and in the sidecar written by the rfq-package skill.
    """
    lines = bom.get("lines", [])
    if group:
        wanted = next((g for g in bom.get("groups", []) if g.get("name") == group), None)
        if wanted is None:
            print(f"no group named {group!r} in {bom.get('id')}", file=sys.stderr)
            raise SystemExit(2)
        ids = set(wanted.get("lines", []))
        lines = [ln for ln in lines if ln.get("id") in ids]

    items = []
    for line in lines:
        if line.get("criticality") == "contingent":
            continue
        ident = line.get("identified") or {}
        desc = str(line.get("description", "")).strip()
        notes: list[str] = []
        sub = line.get("substitution", "equivalent-only")
        if sub == "none":
            notes.append("No substitution: this exact part number.")
        elif sub == "allowed":
            notes.append("Equivalent or better welcome — tell us what you propose and why.")
        else:
            notes.append("Substitution accepted only if it meets every point of the description.")
        if line.get("criticality") == "optional":
            notes.append("Optional line — price separately.")
        if line.get("notes"):
            notes.append(str(line["notes"]).strip())

        item: dict[str, Any] = {
            "description": desc,
            "quantity": line.get("quantity"),
            "notes": " ".join(notes),
        }
        if ident.get("part_number"):
            item["sku"] = ident["part_number"]
        if ident.get("manufacturer"):
            item["manufacturer"] = ident["manufacturer"]
        if line.get("unit"):
            item["unit"] = line["unit"]
        if targets and line.get("target_price") is not None:
            item["target_price"] = line["target_price"]
        items.append(item)

    if not items:
        print("nothing to quote: every line was contingent or filtered out", file=sys.stderr)
        raise SystemExit(2)

    rfq: dict[str, Any] = {
        "rfq_number": number,
        "date": dt.date.today().isoformat(),
        "vendor": {"name": vendor},
        "items": items,
    }
    if bom.get("currency"):
        rfq["currency"] = bom["currency"]
    if bom.get("id"):
        rfq["buyer_reference"] = bom["id"] + (f" / {group}" if group else "")
    delivery: dict[str, Any] = {}
    if bom.get("destination"):
        delivery["notes"] = f"Destination profile: {bom['destination']} — full address on request."
    if bom.get("required_by"):
        delivery["required_by"] = bom["required_by"]
    if delivery:
        rfq["delivery"] = delivery
    if bom.get("purpose"):
        rfq["notes"] = (
            f"What this is for: {str(bom['purpose']).strip()} "
            "Where a line is described rather than named, quote whatever you carry that meets "
            "the description and tell us what it is."
        )
    default_questions = [
        "Current stock and lead time per line.",
        "Whether any line is better served by something else you carry, and why.",
        "Price breaks at higher quantities, if any.",
        "Whether prices include VAT and delivery, and if not, what those add.",
    ]
    rfq["questions"] = questions if questions is not None else default_questions
    return rfq


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _write(text: str, out: str | None) -> None:
    if out:
        path = pathlib.Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path}")
    else:
        sys.stdout.write(text)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("validate-spec", help="check spec.yaml structure and id discipline")
    s.add_argument("spec")

    s = sub.add_parser("criteria", help="render the evaluation-criteria brief from a spec")
    s.add_argument("spec")
    s.add_argument("-o", "--out")

    s = sub.add_parser("validate-conformance", help="check conformance records against a spec")
    s.add_argument("records", nargs="+")
    s.add_argument("--spec")

    s = sub.add_parser("matrix", help="render the conformance matrix")
    s.add_argument("spec")
    s.add_argument("conformance_dir")
    s.add_argument("-o", "--out")

    s = sub.add_parser("validate-bom", help="check bom.yaml, and its spec references if given a spec")
    s.add_argument("bom")
    s.add_argument("--spec")

    s = sub.add_parser("rfq", help="project a BOM onto the dsrholdings-rfq input schema")
    s.add_argument("bom")
    s.add_argument("--vendor", required=True)
    s.add_argument("--number", required=True, help="RFQ-YYYY-NNN")
    s.add_argument("--group", help="quote only one BOM group")
    s.add_argument("--targets", action="store_true",
                   help="carry target_price through — this anchors the supplier, so it is opt-in")
    s.add_argument("-o", "--out")

    args = ap.parse_args()

    if args.cmd == "validate-spec":
        p = Problems()
        validate_spec(load(pathlib.Path(args.spec)), p)
        return p.report(args.spec)

    if args.cmd == "criteria":
        spec = load(pathlib.Path(args.spec))
        p = Problems()
        validate_spec(spec, p)
        if p.errors:
            p.report(args.spec)
            print("refusing to render criteria from an invalid spec", file=sys.stderr)
            return 1
        _write(render_criteria(spec), args.out)
        return 0

    if args.cmd == "validate-conformance":
        spec = load(pathlib.Path(args.spec)) if args.spec else None
        worst = 0
        for rec_path in args.records:
            path = pathlib.Path(rec_path)
            p = Problems()
            validate_conformance(load(path), spec, p)
            worst = max(worst, p.report(path.name))
        return worst

    if args.cmd == "matrix":
        spec = load(pathlib.Path(args.spec))
        d = pathlib.Path(args.conformance_dir)
        if not d.is_dir():
            print(f"not a directory: {d}", file=sys.stderr)
            return 2
        records = [(f, load(f)) for f in sorted(d.glob("*.json"))]
        if not records:
            print(f"no conformance records in {d}", file=sys.stderr)
            return 2
        _write(render_matrix(spec, records), args.out)
        return 0

    if args.cmd == "validate-bom":
        spec = load(pathlib.Path(args.spec)) if args.spec else None
        p = Problems()
        validate_bom(load(pathlib.Path(args.bom)), spec, p)
        return p.report(args.bom)

    if args.cmd == "rfq":
        if not RFQ_NUMBER.match(args.number):
            print(f"--number {args.number!r} must look like RFQ-2026-001", file=sys.stderr)
            return 2
        bom = load(pathlib.Path(args.bom))
        p = Problems()
        validate_bom(bom, None, p)
        if p.errors:
            p.report(args.bom)
            print("refusing to build an RFQ from an invalid BOM", file=sys.stderr)
            return 1
        rfq = bom_to_rfq(bom, args.vendor, args.number, group=args.group, targets=args.targets)
        _write(json.dumps(rfq, indent=2, ensure_ascii=False) + "\n", args.out)
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
