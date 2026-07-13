"""Deterministic rendering of an AuditReport (text and JSON).

No wall-clock timestamps or non-deterministic ordering appear in the output, so
the same log always produces byte-identical reports.
"""

from __future__ import annotations

import json

from .model import AuditReport, Status

_ORDER = {"FAIL": 0, "WARN": 1, "PASS": 2, "NOT_CHECKED": 3}


def to_dict(report: AuditReport) -> dict:
    return {
        "tool": "inspect-audit",
        "tool_version": report.tool_version,
        "target": report.target,
        "overall": report.overall.label,
        "aggregate_may_be_invalid": report.aggregate_may_be_invalid,
        "counts": report.counts(),
        "checks": [
            {
                "check_id": c.check_id,
                "title": c.title,
                "status": c.status.label,
                "not_checked_reason": c.not_checked_reason,
                "findings": [
                    {
                        "check_id": f.check_id,
                        "severity": f.severity.label,
                        "evidence_path": f.evidence_path,
                        "why_it_matters": f.why_it_matters,
                        "remediation": f.remediation,
                        "aggregate_may_be_invalid": f.aggregate_may_be_invalid,
                        "detail": f.detail,
                    }
                    for f in c.findings
                ],
            }
            for c in report.checks
        ],
    }


def to_json(report: AuditReport) -> str:
    return json.dumps(to_dict(report), indent=2, ensure_ascii=False, sort_keys=False)


def to_text(report: AuditReport, verbose: bool = False) -> str:
    lines: list[str] = []
    lines.append(f"inspect-audit {report.tool_version}")
    lines.append(f"target: {report.target}")
    lines.append("")

    checks = sorted(report.checks, key=lambda c: (_ORDER[c.status.label], c.check_id))
    for c in checks:
        if c.status == Status.NOT_CHECKED:
            if verbose:
                lines.append(f"[NOT_CHECKED] {c.check_id} {c.title} — {c.not_checked_reason}")
            continue
        if not c.findings:
            if verbose:
                lines.append(f"[PASS] {c.check_id} {c.title}")
            continue
        for f in c.findings:
            lines.append(f"[{f.severity.label}] {f.check_id} {c.title}")
            lines.append(f"    evidence : {f.evidence_path}")
            if f.detail:
                lines.append(f"    detail   : {f.detail}")
            lines.append(f"    why      : {f.why_it_matters}")
            lines.append(f"    fix      : {f.remediation}")
            lines.append(f"    aggregate_may_be_invalid: {f.aggregate_may_be_invalid}")
            lines.append("")

    counts = report.counts()
    if not verbose:
        lines.append("")
    lines.append(
        "checks: "
        f"{counts['FAIL']} FAIL, {counts['WARN']} WARN, "
        f"{counts['PASS']} PASS, {counts['NOT_CHECKED']} NOT_CHECKED"
    )
    lines.append(f"aggregate_may_be_invalid: {report.aggregate_may_be_invalid}")
    lines.append(f"VERDICT: {report.overall.label}")
    lines.append(
        "note: PASS means only that the implemented checks found no issue; "
        "it is not a guarantee that the evaluation is valid. NOT_CHECKED != PASS."
    )
    return "\n".join(lines)
