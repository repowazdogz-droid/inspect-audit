"""Family 2: scorer integrity.

Did scoring actually run and produce meaningful values, or did it fail in a way
that a headline metric conceals? Motivated by grader parse-failures that resolve
to a default/NaN score (observed directly in Inspect's model_graded scorers).
"""

from __future__ import annotations

from typing import Any

from ..loader import Target
from ..model import CheckResult, Finding, Status
from ._util import GRADE_NOT_FOUND_PREFIX, is_bad_number


def _iter_scores(t: Target):
    for idx, s in enumerate(t.log.samples):
        for name, sco in (getattr(s, "scores", None) or {}).items():
            yield idx, s, name, sco


def check_missing_scores(t: Target) -> CheckResult:
    cid, title = "SCO001", "Missing sample scores"
    if not t.samples_available:
        return CheckResult.not_checked(cid, title, "per-sample records not available")
    results = getattr(t.log, "results", None)
    expected = {sc.name for sc in results.scores} if (results and results.scores) else set()
    if not expected:
        return CheckResult.not_checked(cid, title, "no scorer names recorded to check against")
    findings: list[Finding] = []
    for idx, s in enumerate(t.log.samples):
        got = set((getattr(s, "scores", None) or {}).keys())
        missing = expected - got
        # A sample that errored is legitimately unscored; report it under DEN,
        # here we flag samples that completed yet lack an expected score.
        if missing and getattr(s, "error", None) is None:
            findings.append(Finding(
                cid, Status.WARN, f"samples[{idx}].scores",
                why_it_matters=(
                    f"sample id={s.id!r} completed without error but is missing "
                    f"score(s): {sorted(missing)}. It contributes to the run yet not "
                    "to those metrics."
                ),
                remediation="Ensure every completed sample is scored by every declared scorer, or account for the gap.",
                aggregate_may_be_invalid=True,
                detail=f"id={s.id!r} missing={sorted(missing)}",
            ))
    return CheckResult.from_findings(cid, title, findings)


def check_invalid_values(t: Target) -> CheckResult:
    cid, title = "SCO002", "Invalid score values"
    if not t.samples_available:
        return CheckResult.not_checked(cid, title, "per-sample records not available")
    # Only unambiguous corruption is flagged. Arbitrary strings, numbers, lists
    # and dicts are all legitimate score values for custom scorers, so they are
    # never flagged here — that would false-positive on valid categorical scorers.
    findings: list[Finding] = []
    for idx, s, name, sco in _iter_scores(t):
        v = sco.value
        if is_bad_number(v):
            reason = "non-finite (NaN/inf)"
        elif v is None:
            reason = "null"
        else:
            continue
        findings.append(Finding(
            cid, Status.FAIL, f"samples[{idx}].scores['{name}'].value",
            why_it_matters=(
                f"score '{name}' on sample id={s.id!r} has a {reason} value "
                f"({v!r}). Aggregating it can silently corrupt or skew the metric."
            ),
            remediation="Locate the scoring failure; a NaN/None value usually means the scorer errored or could not parse a result.",
            aggregate_may_be_invalid=True,
            detail=f"id={s.id!r} scorer={name} value={v!r} reason={reason}",
        ))
    return CheckResult.from_findings(cid, title, findings)


def check_empty_scorer_metrics(t: Target) -> CheckResult:
    cid, title = "SCO003", "Scorer produced no usable metric"
    results = getattr(t.log, "results", None)
    if results is None or not results.scores:
        return CheckResult.not_checked(cid, title, "no scores recorded")
    findings: list[Finding] = []
    for i, sc in enumerate(results.scores):
        if not getattr(sc, "metrics", None):
            findings.append(Finding(
                cid, Status.WARN, f"results.scores[{i}].metrics",
                why_it_matters=f"scorer '{sc.name}' recorded no metrics; there is nothing to trust or a downstream default fills in.",
                remediation="Confirm the scorer defines metrics and that scoring completed.",
                aggregate_may_be_invalid=True,
                detail=f"scorer={sc.name}",
            ))
    return CheckResult.from_findings(cid, title, findings)


def check_grade_parse_failure(t: Target) -> CheckResult:
    cid, title = "SCO004", "Model-graded parse failure resolved to a default"
    if not t.samples_available:
        return CheckResult.not_checked(cid, title, "per-sample records not available")
    findings: list[Finding] = []
    for idx, s, name, sco in _iter_scores(t):
        expl = (sco.explanation or "")
        if expl.startswith(GRADE_NOT_FOUND_PREFIX):
            findings.append(Finding(
                cid, Status.FAIL, f"samples[{idx}].scores['{name}'].explanation",
                why_it_matters=(
                    f"the grader for '{name}' on sample id={s.id!r} returned no "
                    "parseable grade; the scorer fell back to a default/NaN value. "
                    "The metric treats a grading failure as a data point."
                ),
                remediation="Fix the grader prompt/parse pattern or the judge model output; do not count grade-not-found as a score.",
                aggregate_may_be_invalid=True,
                detail=f"id={s.id!r} scorer={name} value={sco.value!r} explanation={expl[:80]!r}",
            ))
    return CheckResult.from_findings(cid, title, findings)


CHECKS = [
    check_missing_scores,
    check_invalid_values,
    check_empty_scorer_metrics,
    check_grade_parse_failure,
]
