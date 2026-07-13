"""inspect-audit: a static, read-only validity auditor for Inspect .eval logs.

Public API:

    from inspect_audit import audit_paths, to_dict, to_json
    report = audit_paths(["run.eval"])
    if report.overall.label == "FAIL":
        print(to_json(report))

`audit_paths` never modifies the logs it reads.
"""

__version__ = "0.1.0"

from .audit import audit_paths
from .catalog import CATALOG, CheckSpec
from .model import AuditReport, CheckResult, Finding, Status
from .report import to_dict, to_json, to_text

__all__ = [
    "__version__",
    "audit_paths",
    "AuditReport",
    "CheckResult",
    "Finding",
    "Status",
    "CheckSpec",
    "CATALOG",
    "to_dict",
    "to_json",
    "to_text",
]
