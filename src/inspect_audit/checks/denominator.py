"""Family 1: denominator integrity.

Does the number the metric was computed over match the number of samples that
were actually scheduled, run, and scored? Motivated by inspect_ai#4286 (scoring
metrics silently drop inconclusive/errored samples from the denominator).
"""

from __future__ import annotations

from typing import Any

from ..loader import Target
from ..model import CheckResult, Finding, Status
from ._util import scorer_specs

NOANSWER = "N"


def check_dataset_vs_results(t: Target) -> CheckResult:
    cid, title = "DEN001", "Scheduled vs recorded sample count"
    log = t.log
    results = getattr(log, "results", None)
    ds = getattr(log.eval, "dataset", None)
    scheduled = getattr(ds, "samples", None) if ds else None
    cfg = log.eval.config
    epochs = getattr(cfg, "epochs", None) or 1
    if results is None or scheduled is None:
        return CheckResult.not_checked(
            cid, title, "dataset sample count or results not recorded in log"
        )
    # A run may be deliberately subset (--limit / --sample-id). Then the dataset
    # size is not the scheduled size and reconciling would false-positive.
    if getattr(cfg, "limit", None) is not None or getattr(cfg, "sample_id", None) is not None:
        return CheckResult.not_checked(
            cid, title,
            "run was explicitly subset (limit/sample_id set); scheduled count is not reconcilable from the log",
        )
    expected = scheduled * epochs
    total = results.total_samples
    if expected == total:
        return CheckResult.from_findings(cid, title, [])
    return CheckResult.from_findings(
        cid, title,
        [Finding(
            cid, Status.WARN, "results.total_samples",
            why_it_matters=(
                f"dataset declares {scheduled} sample(s) x {epochs} epoch(s) = "
                f"{expected} scheduled, but results record {total}. Samples were "
                "added or lost relative to the dataset."
            ),
            remediation="Reconcile the dataset with the run; confirm no samples were filtered or failed to schedule.",
            aggregate_may_be_invalid=total < expected,
            detail=f"expected={expected} recorded={total}",
        )],
    )


def check_completed_vs_total(t: Target) -> CheckResult:
    cid, title = "DEN002", "Completed vs total samples"
    results = getattr(t.log, "results", None)
    if results is None:
        return CheckResult.not_checked(cid, title, "results not recorded in log")
    missing = results.total_samples - results.completed_samples
    if missing <= 0:
        return CheckResult.from_findings(cid, title, [])
    return CheckResult.from_findings(
        cid, title,
        [Finding(
            cid, Status.WARN, "results.completed_samples",
            why_it_matters=(
                f"{missing} of {results.total_samples} samples did not complete. "
                "Metrics computed over completed samples describe a subset of the "
                "intended evaluation."
            ),
            remediation="Investigate incomplete samples (errors/limits); decide whether to retry, exclude explicitly, or report the reduced denominator.",
            aggregate_may_be_invalid=True,
            detail=f"completed={results.completed_samples} total={results.total_samples}",
        )],
    )


def check_scorer_denominator(t: Target) -> CheckResult:
    cid, title = "DEN003", "Scorer denominator shrink (unscored samples)"
    results = getattr(t.log, "results", None)
    if results is None or not results.scores:
        return CheckResult.not_checked(cid, title, "no scores recorded in log")
    total = results.total_samples
    findings: list[Finding] = []
    for i, sc in enumerate(results.scores):
        unscored = getattr(sc, "unscored_samples", None)
        scored = getattr(sc, "scored_samples", None)
        if not unscored:
            continue
        graded_nothing = scored == 0
        findings.append(Finding(
            cid,
            Status.FAIL if graded_nothing else Status.WARN,
            f"results.scores[{i}].unscored_samples",
            why_it_matters=(
                f"scorer '{sc.name}' scored {scored} of {total} sample(s); "
                f"{unscored} were excluded from its metric denominator. The metric "
                "reads as clean while ignoring a subset"
                + (" — in fact NO sample was scored." if graded_nothing else ".")
            ),
            remediation="Determine why samples went unscored (errors, abstentions, grader failures) and either fix scoring or report the true denominator.",
            aggregate_may_be_invalid=True,
            detail=f"scorer={sc.name} scored={scored} unscored={unscored} total={total}",
        ))
    return CheckResult.from_findings(cid, title, findings)


def check_sample_limits(t: Target) -> CheckResult:
    cid, title = "DEN004", "Samples truncated by a limit"
    if not t.samples_available:
        return CheckResult.not_checked(cid, title, "per-sample records not available (log_samples off or header-only)")
    findings: list[Finding] = []
    for idx, s in enumerate(t.log.samples):
        lim = getattr(s, "limit", None)
        if lim is None:
            continue
        findings.append(Finding(
            cid, Status.WARN, f"samples[{idx}].limit",
            why_it_matters=(
                f"sample id={s.id!r} epoch={s.epoch} hit a '{lim.type}' limit; its "
                "output is truncated, so any score derived from it may not reflect "
                "the model's real behaviour."
            ),
            remediation="Raise the relevant limit or exclude truncated samples explicitly; do not treat a truncated response as a genuine one.",
            aggregate_may_be_invalid=True,
            detail=f"id={s.id!r} epoch={s.epoch} limit_type={lim.type} limit={lim.limit}",
        ))
    return CheckResult.from_findings(cid, title, findings)


def check_abstentions(t: Target) -> CheckResult:
    cid, title = "DEN005", "Abstentions (NOANSWER) accounting"
    if not t.samples_available:
        return CheckResult.not_checked(cid, title, "per-sample records not available (log_samples off or header-only)")
    count = 0
    example = ""
    for idx, s in enumerate(t.log.samples):
        for name, sco in (getattr(s, "scores", None) or {}).items():
            if sco.value == NOANSWER:
                count += 1
                if not example:
                    example = f"samples[{idx}].scores['{name}']"
    if count == 0:
        return CheckResult.from_findings(cid, title, [])
    return CheckResult.from_findings(
        cid, title,
        [Finding(
            cid, Status.WARN, example,
            why_it_matters=(
                f"{count} sample score(s) are NOANSWER (abstentions). Whether these "
                "count toward the denominator is metric-dependent; if silently "
                "dropped or counted as incorrect the headline number is skewed."
            ),
            remediation="Confirm the metric handles abstentions as you intend; report abstention rate alongside the score.",
            aggregate_may_be_invalid=False,
            detail=f"abstention_scores={count}",
        )],
    )


CHECKS = [
    check_dataset_vs_results,
    check_completed_vs_total,
    check_scorer_denominator,
    check_sample_limits,
    check_abstentions,
]
