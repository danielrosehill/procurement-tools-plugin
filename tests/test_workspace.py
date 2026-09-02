#!/usr/bin/env python3
"""Self-checks for the procurement workspace manifest.

Deterministic and offline. What is worth testing here is the discipline the
manifest exists to enforce — an id that no longer matches its opening date, a
folder that cannot say which repo it lives in, a workspace marked purchased
with nothing recorded as bought — because each of those makes an index quietly
wrong rather than loudly broken, and a wrong index is worse than none.

    python3 tests/test_workspace.py
"""

from __future__ import annotations

import copy
import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from workspace import (  # noqa: E402
    MANIFEST,
    Problems,
    detect_spec,
    manifest_path,
    new_id,
    render_index_md,
    scan,
    validate,
)

FAILURES: list[str] = []


def check(label: str, got, want) -> None:
    if got != want:
        FAILURES.append(f"{label}: got {got!r}, wanted {want!r}")


def check_has(label: str, haystack: str, needle: str) -> None:
    if needle not in haystack:
        FAILURES.append(f"{label}: {needle!r} missing from output")


def problems(m: dict) -> list[str]:
    p = Problems()
    validate(m, p)
    return p.items


def clean(m: dict) -> bool:
    return not problems(m)


def has_problem(m: dict, fragment: str) -> bool:
    return any(fragment in i for i in problems(m))


BASE = {
    "schema_version": "1.0",
    "id": "PW-20260902-A1B2C3",
    "name": "laser-measure-0902",
    "title": "Laser measure for site surveys",
    "variant": "general-purchasing",
    "mode": "repo",
    "visibility": "private",
    "status": "open",
    "opened": "2026-09-02",
    "updated": "2026-09-02",
    "closed": None,
    "spec": {"path": "spec.yaml", "revision": 3},
    "reports": [],
    "tags": ["tooling"],
}


def m(**over) -> dict:
    out = copy.deepcopy(BASE)
    out.update(over)
    return out


# --------------------------------------------------------------------------
# identity
# --------------------------------------------------------------------------

def test_valid_manifest_is_clean() -> None:
    check("valid manifest", problems(m()), [])


def test_bad_id_shape_is_an_error() -> None:
    check("lowercase hex", has_problem(m(id="PW-20260902-a1b2c3"), "expected PW-"), True)
    check("short suffix", has_problem(m(id="PW-20260902-A1B2"), "expected PW-"), True)
    check("no prefix", has_problem(m(id="20260902-A1B2C3"), "expected PW-"), True)


def test_id_date_prefix_must_match_opened() -> None:
    bad = m(opened="2026-08-01")
    check("mismatch caught", has_problem(bad, "does not match"), True)
    check("id named authoritative", has_problem(bad, "id is authoritative"), True)


def test_new_id_shape_and_date_prefix() -> None:
    wid = new_id("2026-09-02")
    check("prefix", wid[:12], "PW-20260902-")
    check("length", len(wid), 18)
    check("validates", clean(m(id=wid, opened="2026-09-02")), True)
    check("ids differ", new_id("2026-09-02") != new_id("2026-09-02"), True)


def test_name_must_be_kebab_case() -> None:
    check("underscore", has_problem(m(name="laser_measure"), "kebab-case"), True)
    check("capital", has_problem(m(name="LaserMeasure"), "kebab-case"), True)


def test_tags_must_be_kebab_case() -> None:
    check("bad tag", has_problem(m(tags=["Power Tools"]), "tags[0]"), True)


# --------------------------------------------------------------------------
# mode: a folder must know its parent, a repo must not claim one
# --------------------------------------------------------------------------

def test_folder_mode_needs_a_parent_path() -> None:
    check("no parent block", has_problem(m(mode="folder"), "parent.path"), True)
    check("empty path", has_problem(
        m(mode="folder", parent={"repo": "procurement", "path": ""}), "parent.path"), True)


def test_folder_mode_with_parent_is_clean() -> None:
    ok = m(mode="folder", parent={"repo": "procurement", "path": "decisions/desk-lamp"})
    check("folder ok", problems(ok), [])


def test_repo_mode_must_not_carry_a_parent() -> None:
    check("repo with parent", has_problem(
        m(parent={"repo": "x", "path": "y"}), "not 'folder'"), True)


# --------------------------------------------------------------------------
# lifecycle
# --------------------------------------------------------------------------

def test_purchased_without_an_outcome_is_an_error() -> None:
    check("no outcome", has_problem(
        m(status="purchased", closed="2026-09-10"), "no 'outcome'"), True)


def test_purchased_with_an_outcome_is_clean() -> None:
    ok = m(status="purchased", closed="2026-09-10",
           outcome={"product": "Bosch GLM 165-27 C", "price": 449,
                    "currency": "ILS", "date": "2026-09-10"})
    check("purchased ok", problems(ok), [])


def test_closed_status_needs_a_closed_date() -> None:
    check("abandoned open-ended", has_problem(
        m(status="abandoned"), "'closed' is not set"), True)


def test_closed_date_on_an_open_workspace_is_an_error() -> None:
    check("open but closed", has_problem(
        m(closed="2026-09-10"), "clear one"), True)


def test_decided_stays_open_ended() -> None:
    check("decided ok", problems(m(status="decided")), [])


def test_superseded_must_name_its_successor() -> None:
    check("no successor", has_problem(
        m(status="superseded", closed="2026-09-10"), "names no id"), True)
    ok = m(status="superseded", closed="2026-09-10",
           superseded_by="PW-20261001-FFEE00")
    check("with successor", problems(ok), [])


def test_outcome_currency_must_be_iso_4217() -> None:
    bad = m(status="purchased", closed="2026-09-10",
            outcome={"product": "x", "currency": "shekel", "date": "2026-09-10"})
    check("bad currency", has_problem(bad, "ISO 4217"), True)


# --------------------------------------------------------------------------
# report trail
# --------------------------------------------------------------------------

def test_report_needs_a_markdown_path() -> None:
    bad = m(reports=[{"date": "2026-09-02", "kind": "recommendation"}])
    check("no path", has_problem(bad, "missing 'path'"), True)


def test_report_kind_is_constrained() -> None:
    bad = m(reports=[{"date": "2026-09-02", "kind": "writeup", "path": "r.md"}])
    check("bad kind", has_problem(bad, "kind is 'writeup'"), True)


def test_duplicate_report_record_is_an_error() -> None:
    rec = {"date": "2026-09-02", "kind": "recommendation", "path": "r.md"}
    check("duplicate", has_problem(
        m(reports=[rec, copy.deepcopy(rec)]), "duplicate report record"), True)


def test_same_path_on_a_later_date_is_allowed() -> None:
    ok = m(reports=[
        {"date": "2026-09-02", "kind": "recommendation", "path": "a.md"},
        {"date": "2026-09-20", "kind": "recommendation", "path": "b.md"},
    ])
    check("two dated reports", problems(ok), [])


# --------------------------------------------------------------------------
# filesystem helpers
# --------------------------------------------------------------------------

def test_manifest_path_accepts_a_directory_or_the_file() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / MANIFEST).write_text("{}")
        check("from dir", manifest_path(root).name, MANIFEST)
        check("from file", manifest_path(root / MANIFEST).name, MANIFEST)


def test_detect_spec_prefers_yaml_and_finds_variants() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / "spec.md").write_text("# prose")
        (root / "spec.yaml").write_text("revision: 4\n")
        (root / "spec-budget.yaml").write_text("revision: 1\n")
        (root / "spec-premium.yaml").write_text("revision: 1\n")
        got = detect_spec(root)
        check("prefers yaml", got["path"], "spec.yaml")
        check("reads revision", got.get("revision"), 4)
        check("finds variants", got.get("variants"),
              ["spec-budget.yaml", "spec-premium.yaml"])


def test_detect_spec_falls_back_to_prose() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / "spec.md").write_text("# prose")
        got = detect_spec(root)
        check("prose path", got["path"], "spec.md")
        check("no revision", "revision" in got, False)


def test_detect_spec_returns_none_when_absent() -> None:
    with tempfile.TemporaryDirectory() as td:
        check("no spec", detect_spec(pathlib.Path(td)), None)


# --------------------------------------------------------------------------
# the scan an index would read
# --------------------------------------------------------------------------

def _write(root: pathlib.Path, rel: str, data: dict) -> None:
    p = root / rel / MANIFEST
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data), encoding="utf-8")


def test_scan_finds_nested_workspaces_and_sorts_by_open_date() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        _write(root, "later", m(id="PW-20261001-000002", name="later",
                                opened="2026-10-01", updated="2026-10-01"))
        _write(root, "parent/decisions/earlier",
               m(id="PW-20260902-000001", name="earlier",
                 mode="folder",
                 parent={"repo": "p", "path": "decisions/earlier"}))
        rows = scan(root)
        check("found both", len(rows), 2)
        check("sorted by opened", [r[1]["name"] for r in rows], ["earlier", "later"])


def test_scan_skips_noise_directories() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        _write(root, "real", m(name="real"))
        _write(root, "node_modules/pkg", m(id="PW-20260902-BADBAD", name="vendored"))
        _write(root, ".git/modules/x", m(id="PW-20260902-BADBA1", name="gitinternal"))
        rows = scan(root)
        check("only the real one", [r[1]["name"] for r in rows], ["real"])


def test_scan_reports_unreadable_manifests_rather_than_crashing() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        _write(root, "good", m(name="good"))
        bad = root / "broken" / MANIFEST
        bad.parent.mkdir(parents=True)
        bad.write_text("{not json", encoding="utf-8")
        rows = scan(root)
        check("both surfaced", len(rows), 2)
        check("one flagged", sum(1 for _, d in rows if d.get("_unreadable")), 1)


def test_index_markdown_carries_ids_and_relative_paths() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        _write(root, "parent/decisions/desk-lamp",
               m(id="PW-20260902-A1B2C3", name="desk-lamp", mode="folder",
                 parent={"repo": "p", "path": "decisions/desk-lamp"}))
        out = render_index_md(scan(root), root)
        check_has("id present", out, "PW-20260902-A1B2C3")
        check_has("folder path", out, "parent/decisions/desk-lamp")
        check_has("mode column", out, "folder")
        check_has("count line", out, "1 workspace(s).")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print(f"{len(tests)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
