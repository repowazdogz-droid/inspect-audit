"""Mutation tests: every check must fire on the fixture carrying its defect,
and must NOT fire on the clean log. This is the core guarantee — a check that
cannot fail on the relevant defect is not a check.
"""

import pytest

from conftest import fx, status_of
from inspect_audit.audit import audit_paths

# (fixture, check_id, expected status when the defect is present)
MATRIX = [
    ("silent_dropped_errors.eval", "DEN003", "WARN"),
    ("silent_dropped_errors.eval", "DEN002", "WARN"),
    ("scorer_parse_failure.eval", "SCO004", "FAIL"),
    ("scorer_parse_failure.eval", "SCO002", "FAIL"),
    ("scorer_parse_failure.eval", "DEN003", "FAIL"),
    ("missing_judge_metadata.eval", "JUD001", "WARN"),
    ("self_judging.eval", "JUD002", "WARN"),
    ("duplicate_sample_ids.eval", "RUN003", "FAIL"),
    ("regime_unpinned.eval", "REG001", "WARN"),
    ("regime_unpinned.eval", "REG003", "WARN"),
    ("truncated_log.eval", "RUN000", "FAIL"),
]


@pytest.mark.parametrize("fixture,check_id,expected", MATRIX)
def test_check_fires_on_defect(fixture, check_id, expected):
    report = audit_paths([fx(fixture)])
    assert status_of(report, check_id) == expected, (
        f"{check_id} should be {expected} on {fixture}"
    )


@pytest.mark.parametrize("fixture,check_id,expected", MATRIX)
def test_check_quiet_on_clean(fixture, check_id, expected):
    report = audit_paths([fx("clean.eval")])
    status = status_of(report, check_id)
    # On the clean log the check must not raise a WARN/FAIL. It may be PASS,
    # NOT_CHECKED, or absent (RUN000 only exists on load failure).
    assert status in (None, "PASS", "NOT_CHECKED"), (
        f"{check_id} unexpectedly {status} on clean.eval"
    )


def test_clean_overall_pass():
    report = audit_paths([fx("clean.eval")])
    assert report.overall.label == "PASS"
    assert report.aggregate_may_be_invalid is False


def test_defect_verdicts():
    assert audit_paths([fx("scorer_parse_failure.eval")]).overall.label == "FAIL"
    assert audit_paths([fx("silent_dropped_errors.eval")]).overall.label == "WARN"
    assert audit_paths([fx("truncated_log.eval")]).overall.label == "FAIL"
