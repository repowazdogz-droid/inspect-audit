"""Regression tests for the error-handling fixes in the polish sprint."""


from conftest import fx
from inspect_audit.audit import audit_paths
from inspect_audit.report import to_dict


def _write_junk(tmp_path):
    p = tmp_path / "junk.txt"
    p.write_text("not an eval log")
    return str(p)


def test_load_error_message_not_doubled(tmp_path):
    report = audit_paths([_write_junk(tmp_path)])
    finding = report.checks[0].findings[0]
    # the phrase must appear once, not "could not read log ... could not read log"
    assert finding.why_it_matters.count("not a readable Inspect log") == 1
    assert "could not read log" not in finding.why_it_matters


def test_internal_error_not_leaked_in_headline(tmp_path):
    report = audit_paths([_write_junk(tmp_path)])
    finding = report.checks[0].findings[0]
    assert "No recorder for location" not in finding.why_it_matters
    # ...but the raw cause is preserved in detail for debugging
    assert finding.detail  # non-empty


def test_single_failed_file_target_is_the_path(tmp_path):
    junk = _write_junk(tmp_path)
    report = audit_paths([junk])
    assert report.target == junk
    assert "log(s)" not in report.target


def test_multilog_json_ids_not_mutated():
    doc = to_dict(audit_paths([fx("clean.eval"), fx("config_variant_b.eval")]))
    for c in doc["checks"]:
        assert "@" not in c["check_id"], "check id was mutated in multi-log mode"
        for f in c["findings"]:
            assert f["check_id"] == c["check_id"]
    # source is used to disambiguate instead
    sources = {c["source"] for c in doc["checks"] if c["source"]}
    assert "clean.eval" in sources


def test_missing_file_is_single_clean_finding(tmp_path):
    report = audit_paths([str(tmp_path / "nope.eval")])
    assert report.overall.label == "FAIL"
    assert report.checks[0].check_id == "RUN000"
