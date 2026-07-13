"""Documentation must not drift from the implemented check set."""

import os
import re

from inspect_audit.catalog import all_ids

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ID_RE = re.compile(r"\b(?:DEN|SCO|JUD|RUN|REG|XRN)\d{3}\b")


def _readme_ids():
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
        return set(ID_RE.findall(f.read()))


def test_readme_lists_every_check():
    missing = all_ids() - _readme_ids()
    assert not missing, f"README does not document: {sorted(missing)}"


def test_readme_mentions_no_unknown_check():
    unknown = _readme_ids() - all_ids()
    assert not unknown, f"README references non-existent checks: {sorted(unknown)}"
