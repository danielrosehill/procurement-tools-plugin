#!/usr/bin/env python3
"""Self-checks for the spec / conformance / BOM / RFQ artefact chain.

Deterministic and offline: fixtures are built in memory. What is worth testing
here is the discipline the script exists to enforce — reused ids, missing
cells, a `must` settled on a retail listing, a `partial` with no condition —
because those are the failures that otherwise reach a shortlist looking fine.

    python3 tests/test_spec_tools.py
"""

from __future__ import annotations

import copy
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from spec_tools import (  # noqa: E402
    Problems,
    bom_to_rfq,
    clears_all_must,
    render_criteria,
    render_matrix,
    validate_bom,
    parse_spec_ref,
    render_variant_diff,
    spec_ident,
    validate_conformance,
    validate_family,
    validate_spec,
)

FAILURES: list[str] = []


def check(label: str, got, want) -> None:
    if got != want:
        FAILURES.append(f"{label}: got {got!r}, wanted {want!r}")


def check_has(label: str, haystack: str, needle: str) -> None:
    if needle not in haystack:
        FAILURES.append(f"{label}: {needle!r} missing from output")


def check_lacks(label: str, haystack: str, needle: str) -> None:
    if needle in haystack:
        FAILURES.append(f"{label}: {needle!r} should not be in output")


def errors_of(fn, *args) -> list[str]:
    p = Problems()
    fn(*args, p)
    return p.errors


def warnings_of(fn, *args) -> list[str]:
    p = Problems()
    fn(*args, p)
    return p.warnings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def a_spec() -> dict:
    return {
        "spec_version": 1,
        "id": "widget-2026-01",
        "title": "A widget",
        "revision": 2,
        "revised": "2026-01-15",
        "scope": "A widget that widgets.",
        "out_of_scope": ["Colour."],
        "requirements": [
            {
                "id": "REQ-001", "title": "Has a radio", "kind": "must",
                "statement": "Carries a Bluetooth radio.",
                "verify": "datasheet", "evidence": "Datasheet naming the radio.",
                "rationale": "Otherwise it cannot report readings.", "added_in": 1,
            },
            {
                "id": "REQ-002", "title": "Range", "kind": "must",
                "statement": "Rated to at least 50 m.",
                "parameter": "max_range", "operator": "gte", "value": 50, "unit": "m",
                "verify": "datasheet", "evidence": "Datasheet range figure.",
                "rationale": "Longest run is 30 m.", "added_in": 1,
            },
            {
                "id": "REQ-003", "title": "Subscription-locked", "kind": "must-not",
                "statement": "Readings are not gated behind a subscription.",
                "verify": "manual", "evidence": "Manual or app listing.",
                "rationale": "A tool that expires is not a tool.", "added_in": 1,
            },
            {
                "id": "REQ-004", "title": "Green", "kind": "nice",
                "statement": "Green beam.", "verify": "datasheet",
                "evidence": "Datasheet.", "added_in": 1,
            },
            {
                "id": "REQ-005", "title": "Retired one", "kind": "must",
                "statement": "An old requirement.", "verify": "datasheet",
                "evidence": "Datasheet.", "added_in": 1,
                "retired": True, "retired_in": 2, "retired_reason": "Superseded by REQ-002.",
            },
        ],
        "history": [
            {"revision": 1, "date": "2026-01-01", "change": "Initial."},
            {"revision": 2, "date": "2026-01-15", "change": "Retired REQ-005."},
        ],
    }


def a_conformance(**over) -> dict:
    rec = {
        "conformance_version": 1,
        "spec": {"id": "widget-2026-01", "revision": 2},
        "candidate": {"id": "acme-w1", "name": "Acme W1", "part_number": "W1"},
        "evaluated": "2026-01-20",
        "cells": [
            {"req": "REQ-001", "verdict": "pass", "value": "BLE",
             "source": {"type": "datasheet", "doc_revision": "r3", "retrieved": "2026-01-20"}},
            {"req": "REQ-002", "verdict": "pass", "value": 60,
             "source": {"type": "datasheet", "doc_revision": "r3", "retrieved": "2026-01-20"}},
            {"req": "REQ-003", "verdict": "pass",
             "source": {"type": "manual", "doc_revision": "r3", "retrieved": "2026-01-20"}},
            {"req": "REQ-004", "verdict": "unknown",
             "resolves_to": "Not published; ask the vendor."},
        ],
    }
    rec.update(over)
    return rec


def a_bom() -> dict:
    return {
        "bom_version": 1,
        "id": "widget-kit",
        "title": "Widget kit",
        "revision": 1,
        "purpose": "Widgeting on site.",
        "currency": "USD",
        "destination": "storrs",
        "required_by": "2026-03-01",
        "lines": [
            {"id": "LINE-001", "description": "A widget with a radio, 50 m minimum.",
             "quantity": 1, "unit": "ea", "spec_ref": "widget-2026-01#REQ-001,REQ-002",
             "substitution": "equivalent-only", "target_price": 100},
            {"id": "LINE-002", "description": "Acme W1, exactly.", "quantity": 2,
             "substitution": "none",
             "identified": {"manufacturer": "Acme", "part_number": "W1", "region": "US"}},
            {"id": "LINE-003", "description": "A spare, only if LINE-001 lands short.",
             "quantity": 1, "criticality": "contingent", "substitution": "allowed"},
        ],
        "groups": [{"name": "core", "lines": ["LINE-001", "LINE-002"]}],
    }


# ---------------------------------------------------------------------------
# spec
# ---------------------------------------------------------------------------

def test_valid_spec_is_clean() -> None:
    check("valid spec errors", errors_of(validate_spec, a_spec()), [])


def test_reused_requirement_id_is_an_error() -> None:
    spec = a_spec()
    spec["requirements"][1]["id"] = "REQ-001"
    errs = errors_of(validate_spec, spec)
    check("duplicate id caught", any("defined twice" in e for e in errs), True)


def test_bad_id_shape_is_an_error() -> None:
    spec = a_spec()
    spec["requirements"][0]["id"] = "R1"
    check("bad id caught", any("REQ-nnn" in e for e in errors_of(validate_spec, spec)), True)


def test_unknown_verify_class_is_an_error() -> None:
    spec = a_spec()
    spec["requirements"][0]["verify"] = "vibes"
    check("bad verify caught", any("verify" in e for e in errors_of(validate_spec, spec)), True)


def test_range_operator_needs_two_values() -> None:
    spec = a_spec()
    spec["requirements"][1].update({"operator": "range", "value": 50})
    check("range arity caught",
          any("two-element" in e for e in errors_of(validate_spec, spec)), True)


def test_history_must_reach_current_revision() -> None:
    spec = a_spec()
    spec["revision"] = 3
    check("history drift caught",
          any("does not match revision" in e for e in errors_of(validate_spec, spec)), True)


def test_disqualifying_requirement_without_rationale_warns() -> None:
    spec = a_spec()
    del spec["requirements"][0]["rationale"]
    check("missing rationale warns",
          any("rationale" in w for w in warnings_of(validate_spec, spec)), True)


# ---------------------------------------------------------------------------
# criteria
# ---------------------------------------------------------------------------

def test_criteria_separates_kinds_and_excludes_retired() -> None:
    out = render_criteria(a_spec())
    check_has("criteria musts", out, "## Must have")
    check_has("criteria must-nots", out, "## Must not have")
    check_has("criteria nices", out, "## Nice to have")
    check_has("criteria retired section", out, "## Retired requirements")
    # A retired requirement must not appear as something to research.
    check("retired not in must block",
          out.index("REQ-005") > out.index("## Retired requirements"), True)


def test_criteria_states_that_unknown_beats_a_guess() -> None:
    out = render_criteria(a_spec())
    check_has("criteria unknown rule", out, "`unknown` is a complete answer")


def test_criteria_carries_the_rejects_line() -> None:
    spec = a_spec()
    spec["requirements"][0]["rejects"] = "Retail bullet points."
    check_has("criteria rejects", render_criteria(spec), "**Does not count:** Retail bullet points.")


# ---------------------------------------------------------------------------
# conformance
# ---------------------------------------------------------------------------

def test_valid_conformance_is_clean() -> None:
    check("valid conformance errors",
          errors_of(validate_conformance, a_conformance(), a_spec()), [])


def test_missing_cell_is_an_error() -> None:
    rec = a_conformance()
    rec["cells"] = rec["cells"][:2]
    errs = errors_of(validate_conformance, rec, a_spec())
    check("missing cells caught", any("no cell for" in e for e in errs), True)
    check("names the missing ids", any("REQ-003" in e for e in errs), True)


def test_retired_requirement_needs_no_cell() -> None:
    check("retired not demanded",
          any("REQ-005" in e for e in errors_of(validate_conformance, a_conformance(), a_spec())),
          False)


def test_cell_for_unknown_requirement_is_an_error() -> None:
    rec = a_conformance()
    rec["cells"].append({"req": "REQ-099", "verdict": "pass",
                         "source": {"type": "datasheet"}})
    check("unknown req caught",
          any("not in the spec" in e for e in errors_of(validate_conformance, rec, a_spec())), True)


def test_partial_without_a_note_is_an_error() -> None:
    rec = a_conformance()
    rec["cells"][0] = {"req": "REQ-001", "verdict": "partial",
                       "source": {"type": "datasheet"}}
    check("bare partial caught",
          any("no note" in e for e in errors_of(validate_conformance, rec, a_spec())), True)


def test_pass_without_a_source_is_an_error() -> None:
    rec = a_conformance()
    del rec["cells"][0]["source"]
    check("sourceless pass caught",
          any("no source" in e for e in errors_of(validate_conformance, rec, a_spec())), True)


def test_must_settled_on_a_retail_listing_is_an_error() -> None:
    rec = a_conformance()
    rec["cells"][0]["source"] = {"type": "retail-listing", "url": "https://shop.example/w1"}
    errs = errors_of(validate_conformance, rec, a_spec())
    check("weak source on a must caught",
          any("retail-listing" in e and "unknown instead" in e for e in errs), True)


def test_weak_source_on_a_nice_to_have_is_allowed() -> None:
    rec = a_conformance()
    rec["cells"][3] = {"req": "REQ-004", "verdict": "pass",
                       "source": {"type": "retail-listing"}}
    check("weak source tolerated on nice",
          errors_of(validate_conformance, rec, a_spec()), [])


def test_stale_spec_revision_warns_rather_than_fails() -> None:
    rec = a_conformance()
    rec["spec"]["revision"] = 1
    p = Problems()
    validate_conformance(rec, a_spec(), p)
    check("stale revision warns", any("stale" in w for w in p.warnings), True)
    check("stale revision does not error", p.errors, [])


def test_wrong_spec_id_is_an_error() -> None:
    rec = a_conformance()
    rec["spec"]["id"] = "something-else"
    check("wrong spec caught",
          any("does not match" in e for e in errors_of(validate_conformance, rec, a_spec())), True)


def test_clears_all_must_reads_unknowns_as_open() -> None:
    spec = a_spec()
    check("all pass clears", clears_all_must(a_conformance(), spec), "yes")

    rec = a_conformance()
    rec["cells"][1]["verdict"] = "fail"
    check("a fail does not clear", clears_all_must(rec, spec), "no")

    rec = a_conformance()
    rec["cells"][1] = {"req": "REQ-002", "verdict": "unknown", "resolves_to": "Ask."}
    check("an unknown is open, not a pass", clears_all_must(rec, spec), "?")

    # A nice-to-have never affects the verdict.
    rec = a_conformance()
    rec["cells"][3] = {"req": "REQ-004", "verdict": "fail", "source": {"type": "datasheet"}}
    check("nice-to-have does not disqualify", clears_all_must(rec, spec), "yes")


# ---------------------------------------------------------------------------
# matrix
# ---------------------------------------------------------------------------

def test_matrix_never_emits_a_score() -> None:
    out = render_matrix(a_spec(), [(pathlib.Path("a.json"), a_conformance())])
    for banned in ("Score", "Total", "Weighted", "/10"):
        check_lacks("matrix scoring", out, banned)


def test_matrix_column_findings_need_a_field() -> None:
    one = render_matrix(a_spec(), [(pathlib.Path("a.json"), a_conformance())])
    check_lacks("no column findings from one candidate", one, "It is not separating anything")

    records = []
    for i in range(3):
        rec = copy.deepcopy(a_conformance())
        rec["candidate"] = {"id": f"cand-{i}", "name": f"Cand {i}"}
        records.append((pathlib.Path(f"{i}.json"), rec))
    three = render_matrix(a_spec(), records)
    check_has("column findings from three", three, "It is not separating anything")


def test_matrix_distinguishes_unresolved_from_empty() -> None:
    rec = a_conformance()
    rec["cells"][1] = {"req": "REQ-002", "verdict": "unknown", "resolves_to": "Ask."}
    out = render_matrix(a_spec(), [(pathlib.Path("a.json"), rec)])
    check_has("unresolved wording", out, "unfinished evaluation")

    rec = a_conformance()
    rec["cells"][1]["verdict"] = "fail"
    out = render_matrix(a_spec(), [(pathlib.Path("a.json"), rec)])
    check_has("confirmed-failure wording", out, "confirmed failure")


def test_matrix_labels_must_not_columns_as_compliance() -> None:
    out = render_matrix(a_spec(), [(pathlib.Path("a.json"), a_conformance())])
    check_has("must-not reading rule", out, "disqualifying characteristic is **absent**")


# ---------------------------------------------------------------------------
# bom
# ---------------------------------------------------------------------------

def test_valid_bom_is_clean() -> None:
    check("valid bom errors", errors_of(validate_bom, a_bom(), a_spec()), [])


def test_reused_line_id_is_an_error() -> None:
    bom = a_bom()
    bom["lines"][1]["id"] = "LINE-001"
    check("duplicate line caught",
          any("defined twice" in e for e in errors_of(validate_bom, bom, None)), True)


def test_spec_ref_to_a_missing_requirement_is_an_error() -> None:
    bom = a_bom()
    bom["lines"][0]["spec_ref"] = "widget-2026-01#REQ-001,REQ-042"
    check("dangling spec_ref caught",
          any("REQ-042" in e for e in errors_of(validate_bom, bom, a_spec())), True)


def test_spec_ref_to_a_retired_requirement_is_allowed() -> None:
    bom = a_bom()
    bom["lines"][0]["spec_ref"] = "widget-2026-01#REQ-005"
    check("retired ref tolerated", errors_of(validate_bom, bom, a_spec()), [])


def test_no_substitution_without_a_part_number_is_an_error() -> None:
    bom = a_bom()
    del bom["lines"][1]["identified"]
    check("closed substitution needs a part number",
          any("forbids substitution" in e for e in errors_of(validate_bom, bom, None)), True)


def test_group_referencing_an_unknown_line_is_an_error() -> None:
    bom = a_bom()
    bom["groups"][0]["lines"].append("LINE-099")
    check("dangling group ref caught",
          any("LINE-099" in e for e in errors_of(validate_bom, bom, None)), True)


def test_part_number_without_a_region_warns() -> None:
    bom = a_bom()
    del bom["lines"][1]["identified"]["region"]
    check("regionless part number warns",
          any("region" in w for w in warnings_of(validate_bom, bom, None)), True)


# ---------------------------------------------------------------------------
# rfq
# ---------------------------------------------------------------------------

# Mirrors dsrholdings-rfq's schema/rfq.schema.json, which is
# additionalProperties:false. If that schema gains a field, this list is what
# has to move first — an unknown key makes the renderer reject the document.
RFQ_TOP = {"rfq_number", "date", "response_by", "buyer_reference", "currency",
           "vendor", "items", "delivery", "terms", "questions", "notes"}
RFQ_ITEM = {"sku", "description", "manufacturer", "quantity", "unit",
            "target_price", "notes"}
RFQ_VENDOR = {"name", "contact", "address", "email", "phone", "reference"}
RFQ_DELIVERY = {"address", "required_by", "incoterms", "method", "notes"}


def test_rfq_output_stays_inside_the_renderer_schema() -> None:
    rfq = bom_to_rfq(a_bom(), "Acme Ltd", "RFQ-2026-001")
    check("rfq top-level keys", set(rfq) - RFQ_TOP, set())
    check("rfq vendor keys", set(rfq["vendor"]) - RFQ_VENDOR, set())
    check("rfq delivery keys", set(rfq.get("delivery", {})) - RFQ_DELIVERY, set())
    for item in rfq["items"]:
        check("rfq item keys", set(item) - RFQ_ITEM, set())


def test_rfq_drops_contingent_lines() -> None:
    rfq = bom_to_rfq(a_bom(), "Acme Ltd", "RFQ-2026-001")
    check("contingent line dropped", len(rfq["items"]), 2)


def test_rfq_withholds_target_prices_unless_asked() -> None:
    plain = bom_to_rfq(a_bom(), "Acme Ltd", "RFQ-2026-001")
    check("no anchor by default", any("target_price" in i for i in plain["items"]), False)
    anchored = bom_to_rfq(a_bom(), "Acme Ltd", "RFQ-2026-001", targets=True)
    check("anchor on request", any("target_price" in i for i in anchored["items"]), True)


def test_rfq_states_the_substitution_rule_per_line() -> None:
    rfq = bom_to_rfq(a_bom(), "Acme Ltd", "RFQ-2026-001")
    check_has("closed substitution stated", rfq["items"][1]["notes"], "No substitution")
    check_has("equivalent-only stated", rfq["items"][0]["notes"], "meets every point")


def test_rfq_group_filter_selects_lines() -> None:
    bom = a_bom()
    bom["groups"] = [{"name": "core", "lines": ["LINE-001"]}]
    rfq = bom_to_rfq(bom, "Acme Ltd", "RFQ-2026-001", group="core")
    check("group filter", len(rfq["items"]), 1)
    check_has("group in buyer reference", rfq["buyer_reference"], "core")


def test_rfq_carries_the_purpose_so_suppliers_can_substitute_sanely() -> None:
    rfq = bom_to_rfq(a_bom(), "Acme Ltd", "RFQ-2026-001")
    check_has("purpose carried", rfq["notes"], "Widgeting on site")


def test_rfq_keeps_an_unidentified_line_quotable() -> None:
    rfq = bom_to_rfq(a_bom(), "Acme Ltd", "RFQ-2026-001")
    check("described line has no sku", "sku" in rfq["items"][0], False)
    check("described line still has a description",
          bool(rfq["items"][0]["description"]), True)


# ---------------------------------------------------------------------------
# Variants — parallel either/or branches, each versioned on its own axis
# ---------------------------------------------------------------------------

def a_budget_spec() -> dict:
    spec = copy.deepcopy(a_spec())
    spec["variant"] = "budget"
    spec["variant_label"] = "Budget"
    spec["variant_rationale"] = "Cheapest that still clears the safety floor."
    spec["revision"] = 3
    spec["history"] = (spec.get("history") or []) + [
        {"revision": 3, "date": "2026-02-01", "change": "Branched as the budget variant.",
         "reason": "Two real bars for one purchase."},
    ]
    return spec


def a_premium_spec() -> dict:
    spec = copy.deepcopy(a_spec())
    spec["variant"] = "premium"
    spec["variant_label"] = "Premium"
    spec["variant_rationale"] = "No compromise on range; accept the cost."
    spec["variant_of"] = "budget"
    spec["revision"] = 1
    # A new sibling starts a fresh history: the original's revisions describe a
    # spec that no longer exists under that name.
    spec["history"] = [
        {"revision": 1, "date": "2026-02-01", "change": "Branched from budget.",
         "reason": "Range bar worth paying for if the market has it."},
    ]
    for req in spec["requirements"]:
        if req["id"] == "REQ-002":
            req["value"] = 150
            req["variant_note"] = "Held high; this variant exists to buy the range."
    return spec


def a_family() -> list:
    return [("spec-budget.yaml", a_budget_spec()), ("spec-premium.yaml", a_premium_spec())]


def test_unvaried_spec_stays_valid_and_prints_without_a_variant() -> None:
    """The common case must be untouched by variants existing."""
    check("no variant fields needed", errors_of(validate_spec, a_spec()), [])
    check("ident omits the @ part", spec_ident(a_spec()), "widget-2026-01 r2")


def test_variant_identity_is_id_variant_revision() -> None:
    check("variant ident", spec_ident(a_budget_spec()), "widget-2026-01@budget r3")


def test_revisions_are_independent_per_variant() -> None:
    """Budget at r3 and premium at r1 are both current — neither is stale."""
    check("family accepts differing revisions", errors_of(validate_family, a_family()), [])


def test_variant_field_without_a_variant_is_an_error() -> None:
    spec = a_spec()
    spec["variant_rationale"] = "orphaned"
    errs = errors_of(validate_spec, spec)
    check("orphan variant field rejected", len(errs), 1)
    check_has("names the field", errs[0], "variant_rationale")


def test_variant_must_be_a_slug_and_not_its_own_parent() -> None:
    spec = a_budget_spec()
    spec["variant"] = "Budget Option"
    check("non-slug variant rejected", len(errors_of(validate_spec, spec)), 1)
    spec = a_budget_spec()
    spec["variant_of"] = "budget"
    errs = errors_of(validate_spec, spec)
    check("self-parent rejected", len(errs), 1)
    check_has("explains siblings", errs[0], "siblings")


def test_variant_without_a_rationale_warns() -> None:
    spec = a_budget_spec()
    del spec["variant_rationale"]
    check_has("rationale warned", " ".join(warnings_of(validate_spec, spec)), "trade-off")


def test_family_rejects_specs_of_different_purchases() -> None:
    family = a_family()
    family[1][1]["id"] = "something-else"
    errs = errors_of(validate_family, family)
    check("differing ids rejected", len(errs), 1)
    check_has("explains why", errs[0], "not variants of one purchase")


def test_family_rejects_a_bare_spec_beside_variants() -> None:
    """A spec.yaml surviving next to spec-budget.yaml is ambiguous, not merely untidy."""
    family = [("spec.yaml", a_spec()), ("spec-budget.yaml", a_budget_spec())]
    errs = errors_of(validate_family, family)
    check("bare spec rejected", len(errs), 1)
    check_has("explains ambiguity", errs[0], "which one is in force")


def test_family_rejects_a_duplicate_variant_slug() -> None:
    family = a_family()
    family[1][1]["variant"] = "budget"
    check("duplicate variant rejected", len(errors_of(validate_family, family)), 1)


def test_req_id_naming_a_different_subject_across_variants_is_an_error() -> None:
    """The property everything else rests on: REQ-002 means one subject everywhere."""
    family = a_family()
    for req in family[1][1]["requirements"]:
        if req["id"] == "REQ-002":
            req["parameter"] = "battery_life"
    errs = errors_of(validate_family, family)
    check("subject drift rejected", len(errs), 1)
    check_has("names the id", errs[0], "REQ-002")
    check_has("says to reallocate", errs[0], "Allocate a new id")


def test_a_requirement_in_only_one_variant_is_fine() -> None:
    family = a_family()
    family[1][1]["requirements"].append({
        "id": "REQ-009", "title": "Rugged", "kind": "must",
        "statement": "IP67 rated.", "parameter": "ip_rating", "operator": "eq",
        "value": "IP67", "verify": "datasheet", "evidence": "Datasheet ingress rating.",
        "rationale": "Outdoor use.",
    })
    check("one-sided requirement allowed", errors_of(validate_family, family), [])
    diff = render_variant_diff(family)
    check_has("listed as variant-only", diff, "Present in some variants only")
    check_has("shows not required", diff, "not required")


def test_variant_diff_separates_shared_from_differing() -> None:
    diff = render_variant_diff(a_family())
    check_has("differing section", diff, "Same requirement, different bar")
    check_has("shows both bars", diff, "≥ 50 m")
    check_has("shows the other bar", diff, "≥ 150 m")
    check_has("carries the note", diff, "this variant exists to buy the range")
    check_has("states the trade-off", diff, "No compromise on range")


def test_variant_diff_ignores_prose_differences() -> None:
    """Reworded statements are expected across variants; flagging them buries real deltas."""
    family = a_family()
    for req in family[1][1]["requirements"]:
        req["statement"] = req["statement"] + " (premium wording)"
        req["rationale"] = "Different prose entirely."
    diff = render_variant_diff(family)
    check_has("prose alone is not a divergence", diff, "1 differ")


def test_identical_variants_are_called_out() -> None:
    family = [("spec-a.yaml", a_budget_spec()), ("spec-b.yaml", a_budget_spec())]
    family[1][1]["variant"] = "premium"
    check_has("convergence suggested", render_variant_diff(family), "identical")


def test_conformance_judged_against_another_variant_is_an_error_not_a_warning() -> None:
    """A budget verdict says nothing about the premium bar, so it is not merely stale."""
    rec = a_conformance()
    rec["spec"]["variant"] = "budget"
    errs = errors_of(validate_conformance, rec, a_premium_spec())
    check("cross-variant record rejected", len(errs), 1)
    check_has("explains the danger", errs[0], "belongs in a different matrix")


def test_conformance_matching_its_variant_is_accepted() -> None:
    rec = a_conformance()
    rec["spec"]["variant"] = "budget"
    rec["spec"]["revision"] = 3
    check("matching variant accepted", errors_of(validate_conformance, rec, a_budget_spec()), [])


def test_matrix_names_the_variant_it_judges() -> None:
    rec = a_conformance()
    rec["spec"]["variant"] = "budget"
    rec["spec"]["revision"] = 3
    out = render_matrix(a_budget_spec(), [(pathlib.Path("c.json"), rec)])
    check_has("heading names variant", out, "Budget variant")
    check_has("warns against generalising", out, "not thereby cleared under a sibling variant")
    check_has("cites the right file", out, "spec-budget.yaml")


def test_parse_spec_ref_handles_every_shape() -> None:
    check("bare id", parse_spec_ref("widget-2026-01"), ("widget-2026-01", None, []))
    check("with variant", parse_spec_ref("widget-2026-01@budget"),
          ("widget-2026-01", "budget", []))
    check("with reqs", parse_spec_ref("widget-2026-01#REQ-001,REQ-004"),
          ("widget-2026-01", None, ["REQ-001", "REQ-004"]))
    check("with both", parse_spec_ref("widget-2026-01@budget#REQ-001"),
          ("widget-2026-01", "budget", ["REQ-001"]))


def test_bom_line_without_a_variant_warns_when_the_spec_has_one() -> None:
    bom = a_bom()
    bom["lines"][0]["spec_ref"] = "widget-2026-01#REQ-001"
    warns = " ".join(warnings_of(validate_bom, bom, a_budget_spec()))
    check_has("undefined variant warned", warns, "which variant")


def test_variant_does_not_trip_the_id_numbering_heuristic() -> None:
    """A variant omitting a sibling's id is normal, not a sign of hand-editing."""
    spec = a_budget_spec()
    spec["requirements"] = [r for r in spec["requirements"] if r["id"] != "REQ-002"]
    warns = " ".join(warnings_of(validate_spec, spec))
    check_lacks("no numbering warning on a variant", warns, "highest id is")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for test in tests:
        test()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)} check(s) failed across {len(tests)} tests):")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print(f"ok — {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
