"""Cross-run checks fire only with >=2 logs and catch comparability drift."""

from inspect_audit.audit import audit_paths
from conftest import fx, status_of


def test_crossrun_not_checked_single_log():
    report = audit_paths([fx("clean.eval")])
    for cid in ("XRN001", "XRN002", "XRN003"):
        assert status_of(report, cid) == "NOT_CHECKED"


def test_crossrun_config_divergence():
    report = audit_paths([fx("clean.eval"), fx("config_variant_b.eval")])
    # clean has temperature=0, seed=42; variant_b has temperature=0.7, no seed
    assert status_of(report, "XRN002") == "WARN"  # settings differ
    assert status_of(report, "XRN003") == "WARN"  # seed set in one, unset in other


def test_crossrun_consistent_configs_pass():
    report = audit_paths([fx("clean.eval"), fx("clean.eval")])
    assert status_of(report, "XRN002") == "PASS"
    assert status_of(report, "XRN003") == "PASS"
