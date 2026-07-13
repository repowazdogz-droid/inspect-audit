"""The public Python API must be importable and stable."""

import os

import inspect_audit
from inspect_audit import AuditReport, Status, audit_paths, to_dict, to_json

EXAMPLES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")


def test_public_symbols_exported():
    for name in ["audit_paths", "AuditReport", "Status", "to_dict", "to_json", "CATALOG"]:
        assert name in inspect_audit.__all__
        assert hasattr(inspect_audit, name)


def test_programmatic_use_matches_readme_example():
    report = audit_paths([os.path.join(EXAMPLES, "broken.eval")])
    assert isinstance(report, AuditReport)
    assert report.overall is Status.FAIL
    assert report.aggregate_may_be_invalid is True
    doc = to_dict(report)
    assert doc["overall"] == "FAIL"
    assert isinstance(to_json(report), str)


def test_clean_example_passes():
    report = audit_paths([os.path.join(EXAMPLES, "clean.eval")])
    assert report.overall is Status.PASS
