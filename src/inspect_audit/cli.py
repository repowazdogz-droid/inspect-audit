"""Command-line entry point.

    inspect-audit run.eval [more.eval ...] [--json] [--verbose] [--header-only]

Exit codes (unless --exit-zero):
    0  overall PASS or NOT_CHECKED-only
    1  overall WARN
    2  overall FAIL
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .audit import audit_paths
from .model import Status
from .report import to_json, to_text

_EXIT = {Status.NOT_CHECKED: 0, Status.PASS: 0, Status.WARN: 1, Status.FAIL: 2}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="inspect-audit",
        description="Audit Inspect (.eval) logs for silent validity failures. Read-only.",
    )
    p.add_argument("logs", nargs="+", help="one or more .eval (or .json) Inspect logs")
    p.add_argument("--json", action="store_true", help="emit a JSON report")
    p.add_argument("--verbose", "-v", action="store_true", help="also list PASS and NOT_CHECKED checks")
    p.add_argument("--header-only", action="store_true", help="read headers only (skips sample-level checks, which report NOT_CHECKED)")
    p.add_argument("--exit-zero", action="store_true", help="always exit 0 regardless of verdict")
    p.add_argument("--version", action="version", version=f"inspect-audit {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = audit_paths(args.logs, header_only=args.header_only)
    out = to_json(report) if args.json else to_text(report, verbose=args.verbose)
    print(out)
    if args.exit_zero:
        return 0
    return _EXIT[report.overall]


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
