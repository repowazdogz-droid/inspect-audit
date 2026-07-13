import importlib.util
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CORPUS = os.path.join(ROOT, "fixtures", "corpus")


def _build_corpus():
    spec = importlib.util.spec_from_file_location(
        "build_fixtures", os.path.join(ROOT, "fixtures", "build_fixtures.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()


@pytest.fixture(scope="session", autouse=True)
def corpus():
    expected = {
        "clean.eval", "silent_dropped_errors.eval", "scorer_parse_failure.eval",
        "missing_judge_metadata.eval", "self_judging.eval",
        "duplicate_sample_ids.eval", "regime_unpinned.eval",
        "config_variant_b.eval", "truncated_log.eval",
    }
    have = set(os.listdir(CORPUS)) if os.path.isdir(CORPUS) else set()
    if not expected.issubset(have):
        _build_corpus()
    return CORPUS


def fx(name: str) -> str:
    return os.path.join(CORPUS, name)


def status_of(report, check_id: str):
    """Return the Status.label for a check_id, or None if absent."""
    for c in report.checks:
        if c.check_id == check_id:
            return c.status.label
    return None
