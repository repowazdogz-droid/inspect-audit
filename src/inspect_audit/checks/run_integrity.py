"""Family 4: run integrity.

Is the log complete and internally consistent — a finished run, with unique
samples, and counts that agree?
"""

from __future__ import annotations

from ..catalog import idtitle, registered
from ..loader import Target
from ..model import CheckResult, Finding, Status


@registered("RUN001")
def check_status(t: Target) -> CheckResult:
    cid, title = idtitle("RUN001")
    status = getattr(t.log, "status", None)
    if status == "success":
        return CheckResult.from_findings(cid, title, [])
    sev = Status.FAIL if status == "error" else Status.WARN
    err = getattr(t.log, "error", None)
    detail = f"status={status}"
    if err is not None:
        detail += f" error={getattr(err, 'message', '')[:120]!r}"
    return CheckResult.from_findings(
        cid, title,
        [Finding(
            cid, sev, "status",
            why_it_matters=(
                f"the run status is '{status}', not 'success'. Any metric read from "
                "this log describes an incomplete or failed run."
            ),
            remediation="Re-run or resume the evaluation to completion before trusting its metrics.",
            aggregate_may_be_invalid=True,
            detail=detail,
        )],
    )


@registered("RUN002")
def check_results_completeness(t: Target) -> CheckResult:
    cid, title = idtitle("RUN002")
    log = t.log
    findings: list[Finding] = []
    results = getattr(log, "results", None)
    if getattr(log, "status", None) == "success" and results is None:
        findings.append(Finding(
            cid, Status.WARN, "results",
            why_it_matters="status is 'success' but no results block was recorded; there are no metrics to trust.",
            remediation="Confirm scoring ran; a success status with no results usually indicates a truncated write.",
            aggregate_may_be_invalid=True,
            detail="results=None",
        ))
    # sample records missing while the config asked to log them
    log_samples = getattr(log.eval.config, "log_samples", None)
    samples = getattr(log, "samples", None)
    total = getattr(results, "total_samples", 0) if results else 0
    if samples is None and log_samples is not False and total and total > 0:
        findings.append(Finding(
            cid, Status.WARN, "samples",
            why_it_matters=f"results record {total} sample(s) but no per-sample data is present though log_samples was not disabled; the log may be truncated.",
            remediation="Check for an interrupted write; per-sample records are needed to audit scoring.",
            aggregate_may_be_invalid=False,
            detail=f"total_samples={total} log_samples={log_samples}",
        ))
    return CheckResult.from_findings(cid, title, findings)


@registered("RUN003")
def check_duplicate_ids(t: Target) -> CheckResult:
    cid, title = idtitle("RUN003")
    if not t.samples_available:
        return CheckResult.not_checked(cid, title, "per-sample records not available")
    seen: dict[tuple, int] = {}
    findings: list[Finding] = []
    for idx, s in enumerate(t.log.samples):
        key = (s.id, s.epoch)
        if key in seen:
            findings.append(Finding(
                cid, Status.FAIL, f"samples[{idx}]",
                why_it_matters=(
                    f"sample id={s.id!r} epoch={s.epoch} appears more than once. "
                    "Duplicated samples double-count in the denominator and corrupt "
                    "aggregate metrics."
                ),
                remediation="Deduplicate the dataset/run; ensure sample ids are unique per epoch.",
                aggregate_may_be_invalid=True,
                detail=f"id={s.id!r} epoch={s.epoch} first_index={seen[key]} dup_index={idx}",
            ))
        else:
            seen[key] = idx
    return CheckResult.from_findings(cid, title, findings)


@registered("RUN004")
def check_sample_count_mismatch(t: Target) -> CheckResult:
    cid, title = idtitle("RUN004")
    if not t.samples_available:
        return CheckResult.not_checked(cid, title, "per-sample records not available")
    results = getattr(t.log, "results", None)
    if results is None:
        return CheckResult.not_checked(cid, title, "results not recorded")
    n = len(t.log.samples)
    if n == results.total_samples:
        return CheckResult.from_findings(cid, title, [])
    return CheckResult.from_findings(
        cid, title,
        [Finding(
            cid, Status.FAIL if n < results.total_samples else Status.WARN,
            "samples",
            why_it_matters=(
                f"{n} per-sample record(s) present but results.total_samples="
                f"{results.total_samples}. The metric denominator and the stored "
                "samples disagree."
            ),
            remediation="Investigate the missing/extra samples; the log is internally inconsistent.",
            aggregate_may_be_invalid=True,
            detail=f"len(samples)={n} total_samples={results.total_samples}",
        )],
    )


@registered("RUN006")
def check_invalidated(t: Target) -> CheckResult:
    cid, title = idtitle("RUN006")
    findings: list[Finding] = []
    if getattr(t.log, "invalidated", False):
        findings.append(Finding(
            cid, Status.WARN, "invalidated",
            why_it_matters="the log is explicitly flagged invalidated; its results were disowned by whoever ran it.",
            remediation="Do not report metrics from an invalidated run.",
            aggregate_may_be_invalid=True,
            detail="invalidated=True",
        ))
    if t.samples_available:
        for idx, s in enumerate(t.log.samples):
            if getattr(s, "invalidation", None) is not None:
                findings.append(Finding(
                    cid, Status.WARN, f"samples[{idx}].invalidation",
                    why_it_matters=f"sample id={s.id!r} carries an invalidation record; its score was overridden/disowned.",
                    remediation="Confirm the aggregate accounts for invalidated samples.",
                    aggregate_may_be_invalid=True,
                    detail=f"id={s.id!r}",
                ))
    return CheckResult.from_findings(cid, title, findings)


CHECKS = [
    check_status,
    check_results_completeness,
    check_duplicate_ids,
    check_sample_count_mismatch,
    check_invalidated,
]
