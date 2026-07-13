"""Hard-constraint contract tests: read-only, deterministic, PASS!=NOT_CHECKED."""

import hashlib
import os

from conftest import CORPUS, fx, status_of
from inspect_audit.audit import audit_paths
from inspect_audit.report import to_json, to_text


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def test_read_only_never_mutates_logs():
    files = [f for f in os.listdir(CORPUS) if f.endswith(".eval")]
    before = {f: _sha(fx(f)) for f in files}
    for f in files:
        audit_paths([fx(f)])
    after = {f: _sha(fx(f)) for f in files}
    assert before == after, "a source log was modified during audit"


def test_deterministic_json_output():
    a = to_json(audit_paths([fx("scorer_parse_failure.eval")]))
    b = to_json(audit_paths([fx("scorer_parse_failure.eval")]))
    assert a == b


def test_deterministic_text_output():
    a = to_text(audit_paths([fx("scorer_parse_failure.eval")]), verbose=True)
    b = to_text(audit_paths([fx("scorer_parse_failure.eval")]), verbose=True)
    assert a == b


def test_not_checked_is_distinct_from_pass():
    # header-only turns the sample-level checks into NOT_CHECKED, never PASS
    report = audit_paths([fx("clean.eval")], header_only=True)
    assert status_of(report, "SCO002") == "NOT_CHECKED"
    assert status_of(report, "RUN003") == "NOT_CHECKED"
    # and a run-level check that needs no samples still runs
    assert status_of(report, "RUN001") == "PASS"


def test_pass_disclaimer_present_in_text():
    text = to_text(audit_paths([fx("clean.eval")]))
    assert "PASS means only that the implemented checks found no issue" in text


def test_aggregate_flag_semantics():
    # a pure comparability WARN must not claim the aggregate is invalid
    report = audit_paths([fx("regime_unpinned.eval")])
    assert report.overall.label == "WARN"
    assert report.aggregate_may_be_invalid is False
    # a denominator/scoring FAIL must
    report2 = audit_paths([fx("scorer_parse_failure.eval")])
    assert report2.aggregate_may_be_invalid is True
