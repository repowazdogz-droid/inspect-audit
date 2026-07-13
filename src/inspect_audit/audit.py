"""Audit orchestration: load logs read-only, run every check, collect results."""

from __future__ import annotations

from typing import Optional

from . import __version__
from .checks import CROSS_LOG_CHECKS, SINGLE_LOG_CHECKS
from .loader import LogLoadError, Target, load_target
from .model import AuditReport, CheckResult, Finding, Status


def _load_failure_check(path: str, err: str) -> CheckResult:
    """A log that will not load is itself a FAIL (corrupt/truncated)."""
    return CheckResult.from_findings(
        "RUN000", "Log is readable",
        [Finding(
            "RUN000", Status.FAIL, path,
            why_it_matters=f"the log could not be read: {err}. A corrupt or truncated log yields no trustworthy metrics.",
            remediation="Recover from a backup or re-run; a log that fails to parse cannot be audited.",
            aggregate_may_be_invalid=True,
            detail=err,
        )],
    )


def audit_paths(paths: list[str], header_only: bool = False) -> AuditReport:
    targets: list[Target] = []
    load_fail_checks: list[CheckResult] = []
    for p in paths:
        try:
            targets.append(load_target(p, header_only=header_only))
        except LogLoadError as e:
            load_fail_checks.append(_load_failure_check(p, str(e)))

    checks: list[CheckResult] = []

    if len(paths) == 1 and targets:
        # single-log report: flat list of single-log checks + cross-run NOT_CHECKED
        t = targets[0]
        checks.extend(fn(t) for fn in SINGLE_LOG_CHECKS)
        checks.extend(fn(targets) for fn in CROSS_LOG_CHECKS)
        target_desc = t.path
    else:
        # multi-log: run single-log checks per target (id-prefixed by file), then cross
        for t in targets:
            for fn in SINGLE_LOG_CHECKS:
                r = fn(t)
                r.check_id = f"{r.check_id}@{t.name}"
                checks.append(r)
        checks.extend(fn(targets) for fn in CROSS_LOG_CHECKS)
        target_desc = f"{len(paths)} log(s)"

    checks = load_fail_checks + checks
    return AuditReport(target=target_desc, tool_version=__version__, checks=checks)
