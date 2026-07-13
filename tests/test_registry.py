"""The catalog is the single source of truth; these tests keep it honest."""

import os

from conftest import CORPUS, fx
from inspect_audit.audit import audit_paths
from inspect_audit.catalog import CATALOG, all_ids
from inspect_audit.checks import (
    ALL_CHECK_FUNCS,
    CROSS_LOG_CHECKS,
    IMPLEMENTED_IDS,
    SINGLE_LOG_CHECKS,
)
from inspect_audit.loader import load_target

EXAMPLES = os.path.join(os.path.dirname(CORPUS), "..", "examples")


def test_ids_unique():
    ids = [s.id for s in CATALOG.values()]
    assert len(ids) == len(set(ids))


def test_every_implemented_check_is_registered():
    assert IMPLEMENTED_IDS <= all_ids(), IMPLEMENTED_IDS - all_ids()


def test_every_registered_check_is_implemented():
    assert all_ids() <= IMPLEMENTED_IDS, all_ids() - IMPLEMENTED_IDS


def test_registered_equals_implemented():
    assert all_ids() == IMPLEMENTED_IDS


def test_check_functions_emit_their_registered_id():
    # each single-log check, run on a clean target, must return its own id
    t = load_target(fx("clean.eval"))
    for fn in SINGLE_LOG_CHECKS:
        r = fn(t)
        assert r.check_id == fn.check_id, f"{fn.__name__} emitted {r.check_id}, tagged {fn.check_id}"
    for fn in CROSS_LOG_CHECKS:
        r = fn([t])
        assert r.check_id == fn.check_id


def test_findings_never_exceed_declared_max_severity():
    logs = [fx(f) for f in os.listdir(CORPUS) if f.endswith(".eval")]
    logs += [os.path.join(EXAMPLES, "clean.eval"), os.path.join(EXAMPLES, "broken.eval")]
    for path in logs:
        report = audit_paths([path])
        for c in report.checks:
            for f in c.findings:
                cap = CATALOG[f.check_id].max_severity
                assert f.severity <= cap, (
                    f"{f.check_id} emitted {f.severity.label} > declared max {cap.label}"
                )


def test_catalog_titles_match_emitted_titles():
    t = load_target(fx("clean.eval"))
    for fn in ALL_CHECK_FUNCS:
        r = fn([t]) if fn in CROSS_LOG_CHECKS else fn(t)
        assert r.title == CATALOG[fn.check_id].title
