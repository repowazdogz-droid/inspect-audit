"""Family 3: judge / grader integrity.

When an evaluation is graded by a model, can a reader see which model graded,
with what configuration, and can they audit the grade? And is the generator
grading its own output? Judge metadata is recorded in scorer params (not in
model_roles for model_graded scorers, verified against Inspect 0.3.246).
"""

from __future__ import annotations

from typing import Any, Optional

from ..loader import Target
from ..model import CheckResult, Finding, Status
from ._util import (
    judge_model_from_score,
    judge_model_from_scorer_spec,
    models_materially_identical,
    score_name_looks_model_graded,
    scorer_specs,
    spec_looks_model_graded,
)


def _spec_by_name(t: Target) -> dict[str, Any]:
    return {getattr(s, "name", ""): s for s in scorer_specs(t.log)}


def _model_graded_scores(t: Target):
    """Yield (index, score, judge_model_or_None) for model-graded scorers."""
    results = getattr(t.log, "results", None)
    if not results or not results.scores:
        return
    specs = _spec_by_name(t)
    for i, sc in enumerate(results.scores):
        spec = specs.get(sc.name)
        jm = judge_model_from_score(sc) or (judge_model_from_scorer_spec(spec) if spec else None)
        graded = (
            jm is not None
            or (spec is not None and spec_looks_model_graded(spec))
            or score_name_looks_model_graded(sc)
        )
        if graded:
            yield i, sc, jm


def check_judge_model_recorded(t: Target) -> CheckResult:
    cid, title = "JUD001", "Judge model recorded"
    results = getattr(t.log, "results", None)
    if not results or not results.scores:
        return CheckResult.not_checked(cid, title, "no scores recorded")
    mg = list(_model_graded_scores(t))
    if not mg:
        return CheckResult.not_checked(cid, title, "no model-graded scorer detected")
    findings: list[Finding] = []
    for i, sc, jm in mg:
        if jm is None:
            findings.append(Finding(
                cid, Status.WARN, f"results.scores[{i}].params.model",
                why_it_matters=f"scorer '{sc.name}' appears model-graded but records no judge model; the result cannot be attributed to a grader.",
                remediation="Record the grader model explicitly in the scorer configuration.",
                aggregate_may_be_invalid=False,
                detail=f"scorer={sc.name}",
            ))
    return CheckResult.from_findings(cid, title, findings)


def check_self_judging(t: Target) -> CheckResult:
    cid, title = "JUD002", "Self-judging risk (generator == judge)"
    gen = getattr(t.log.eval, "model", None)
    mg = list(_model_graded_scores(t))
    if not mg:
        return CheckResult.not_checked(cid, title, "no model-graded scorer detected")
    findings: list[Finding] = []
    for i, sc, jm in mg:
        if models_materially_identical(gen, jm):
            findings.append(Finding(
                cid, Status.WARN, f"results.scores[{i}].params.model",
                why_it_matters=(
                    f"the generator model '{gen}' also graded its own output for "
                    f"scorer '{sc.name}'. Self-grading can inflate scores; the number "
                    "may be biased even though it is computed correctly."
                ),
                remediation="Grade with an independent model, or state explicitly that self-grading is intended and interpret accordingly.",
                aggregate_may_be_invalid=False,
                detail=f"generator={gen} judge={jm} scorer={sc.name}",
            ))
    return CheckResult.from_findings(cid, title, findings)


def check_judge_rationale_preserved(t: Target) -> CheckResult:
    cid, title = "JUD004", "Judge rationale preserved"
    if not t.samples_available:
        return CheckResult.not_checked(cid, title, "per-sample records not available")
    mg_names = {sc.name for _, sc, _ in _model_graded_scores(t)}
    if not mg_names:
        return CheckResult.not_checked(cid, title, "no model-graded scorer detected")
    findings: list[Finding] = []
    for idx, s in enumerate(t.log.samples):
        for name, sco in (getattr(s, "scores", None) or {}).items():
            if name not in mg_names:
                continue
            if not (sco.explanation or (sco.metadata or {})):
                findings.append(Finding(
                    cid, Status.WARN, f"samples[{idx}].scores['{name}'].explanation",
                    why_it_matters=f"model-graded score '{name}' on sample id={s.id!r} preserves no rationale; the grade cannot be audited.",
                    remediation="Preserve the grader's response/explanation so grades are inspectable.",
                    aggregate_may_be_invalid=False,
                    detail=f"id={s.id!r} scorer={name}",
                ))
    return CheckResult.from_findings(cid, title, findings)


CHECKS = [
    check_judge_model_recorded,
    check_self_judging,
    check_judge_rationale_preserved,
]
