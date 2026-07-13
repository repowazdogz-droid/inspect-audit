"""Audit orchestration: load logs read-only, run every check, collect results."""

from __future__ import annotations

import os

from . import __version__
from .catalog import idtitle
from .checks import CROSS_LOG_CHECKS, SINGLE_LOG_CHECKS
from .loader import LogLoadError, Target, load_target
from .model import AuditReport, CheckResult, Finding, Status


def _load_failure_check(path: str, err: LogLoadError) -> CheckResult:
    """A log that will not load is itself a FAIL (corrupt/truncated)."""
    cid, title = idtitle("RUN000")
    cause = err.__cause__
    cause_detail = f"{type(cause).__name__}: {cause}" if cause is not None else str(err)
    r = CheckResult.from_findings(
        cid, title,
        [Finding(
            cid, Status.FAIL, path,
            why_it_matters=f"{err} — a corrupt or truncated log yields no trustworthy metrics.",
            remediation="Recover from a backup or re-run; a log that fails to parse cannot be audited.",
            aggregate_may_be_invalid=True,
            detail=cause_detail,
        )],
    )
    r.source = os.path.basename(path)
    return r


def audit_paths(paths: list[str], header_only: bool = False) -> AuditReport:
    single = len(paths) == 1
    target_desc = paths[0] if single else f"{len(paths)} logs"

    targets: list[Target] = []
    checks: list[CheckResult] = []
    for p in paths:
        try:
            targets.append(load_target(p, header_only=header_only))
        except LogLoadError as e:
            checks.append(_load_failure_check(p, e))

    if single:
        # flat report: single-log checks + cross-run checks (which self-report
        # NOT_CHECKED for one log). If the one log failed to load, only RUN000.
        for t in targets:
            checks.extend(fn(t) for fn in SINGLE_LOG_CHECKS)
        checks.extend(fn(targets) for fn in CROSS_LOG_CHECKS)
    else:
        # per-target single-log checks tagged by source, then cross-run checks
        for t in targets:
            for fn in SINGLE_LOG_CHECKS:
                r = fn(t)
                r.source = t.name
                checks.append(r)
        checks.extend(fn(targets) for fn in CROSS_LOG_CHECKS)

    return AuditReport(target=target_desc, tool_version=__version__, checks=checks)
