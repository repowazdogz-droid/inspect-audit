"""Read-only loading of Inspect ``.eval`` (and ``.json``) logs.

This module never writes to, moves, or mutates a source log. It uses
``inspect_ai.log.read_eval_log``, which opens logs read-only.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

from inspect_ai.log import read_eval_log


class LogLoadError(Exception):
    pass


@dataclass
class Target:
    """One loaded log plus the checks' view onto it."""

    path: str
    log: Any  # inspect_ai.log.EvalLog
    samples_available: bool  # True if per-sample records were logged and read

    @property
    def name(self) -> str:
        return os.path.basename(self.path)


def load_target(path: str, header_only: bool = False) -> Target:
    """Load a single log. Raises LogLoadError with a clean message on failure.

    A load failure is itself audit-relevant (a truncated/corrupt log), so callers
    convert it into a FAIL finding rather than a crash.
    """
    if not os.path.exists(path):
        raise LogLoadError(f"file not found: {path}")
    try:
        log = read_eval_log(path, header_only=header_only)
    except Exception as e:  # noqa: BLE001 - surface any decode/zip error as load failure
        raise LogLoadError(f"could not read log ({type(e).__name__}): {e}") from e

    samples = getattr(log, "samples", None)
    samples_available = bool(samples) and not header_only
    return Target(path=path, log=log, samples_available=samples_available)
