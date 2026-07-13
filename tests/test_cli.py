"""CLI: exit codes and output modes."""

import json

from conftest import fx
from inspect_audit.cli import main


def test_exit_pass(capsys):
    assert main([fx("clean.eval")]) == 0
    assert "VERDICT: PASS" in capsys.readouterr().out


def test_exit_warn():
    assert main([fx("silent_dropped_errors.eval")]) == 1


def test_exit_fail():
    assert main([fx("scorer_parse_failure.eval")]) == 2


def test_exit_zero_flag():
    assert main([fx("scorer_parse_failure.eval"), "--exit-zero"]) == 0


def test_json_is_valid(capsys):
    main([fx("scorer_parse_failure.eval"), "--json"])
    doc = json.loads(capsys.readouterr().out)
    assert doc["tool"] == "inspect-audit"
    assert doc["overall"] == "FAIL"
    assert doc["aggregate_may_be_invalid"] is True
    ids = {c["check_id"] for c in doc["checks"]}
    assert "SCO004" in ids


def test_missing_file_is_fail():
    # a non-existent log becomes a RUN000 FAIL, not a crash
    assert main([fx("does_not_exist.eval")]) == 2
