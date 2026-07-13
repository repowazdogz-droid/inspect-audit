"""Core data model for audit findings.

Design invariants (see docs/assurance-boundary.md):

* Every check reports one of PASS / WARN / FAIL / NOT_CHECKED.
* NOT_CHECKED is distinct from PASS. A check is NOT_CHECKED when the data it
  needs is absent from the log (e.g. samples were not logged, or fewer than two
  logs were supplied for a cross-run check). NOT_CHECKED never contributes to a
  passing verdict.
* PASS means only that this specific implemented check found no issue. It is not
  a statement that the evaluation is valid.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class Status(IntEnum):
    """Ordered so that ``max`` yields the worst status seen.

    NOT_CHECKED is intentionally lowest and never worsens a verdict, but it is
    reported explicitly so a reader can tell it apart from PASS.
    """

    NOT_CHECKED = 0
    PASS = 1
    WARN = 2
    FAIL = 3

    @property
    def label(self) -> str:
        return {
            Status.NOT_CHECKED: "NOT_CHECKED",
            Status.PASS: "PASS",
            Status.WARN: "WARN",
            Status.FAIL: "FAIL",
        }[self]


@dataclass(frozen=True)
class Finding:
    """A single concrete defect located in a log."""

    check_id: str
    severity: Status
    evidence_path: str  # dotted path into the .eval log, e.g. results.scores[1].unscored_samples
    why_it_matters: str
    remediation: str
    aggregate_may_be_invalid: bool
    detail: str = ""  # optional quoted evidence

    def sort_key(self) -> tuple:
        return (self.check_id, self.evidence_path, self.detail)


@dataclass
class CheckResult:
    """Outcome of one check over one audit target."""

    check_id: str
    title: str
    status: Status
    findings: list[Finding] = field(default_factory=list)
    not_checked_reason: str | None = None
    source: str | None = None  # which log this result is about (multi-log mode)

    @classmethod
    def not_checked(cls, check_id: str, title: str, reason: str) -> CheckResult:
        return cls(check_id, title, Status.NOT_CHECKED, [], reason)

    @classmethod
    def from_findings(
        cls, check_id: str, title: str, findings: list[Finding]
    ) -> CheckResult:
        if not findings:
            return cls(check_id, title, Status.PASS, [])
        status = max(f.severity for f in findings)
        return cls(check_id, title, status, sorted(findings, key=Finding.sort_key))


@dataclass
class AuditReport:
    target: str  # description of what was audited (file path, or "N logs")
    tool_version: str
    checks: list[CheckResult]

    @property
    def overall(self) -> Status:
        run = [c.status for c in self.checks if c.status != Status.NOT_CHECKED]
        if not run:
            return Status.NOT_CHECKED
        return max(run)

    @property
    def aggregate_may_be_invalid(self) -> bool:
        return any(
            f.aggregate_may_be_invalid for c in self.checks for f in c.findings
        )

    def counts(self) -> dict[str, int]:
        c = {"PASS": 0, "WARN": 0, "FAIL": 0, "NOT_CHECKED": 0}
        for chk in self.checks:
            c[chk.status.label] += 1
        return c
