"""Check registry.

SINGLE_LOG_CHECKS run against one Target. CROSS_LOG_CHECKS run against the list
of Targets (and self-report NOT_CHECKED when fewer than two are supplied).
Order here is the deterministic reporting order.
"""

from . import denominator, judge, regime, run_integrity, scorer
from . import crossrun

SINGLE_LOG_CHECKS = [
    *denominator.CHECKS,
    *scorer.CHECKS,
    *judge.CHECKS,
    *run_integrity.CHECKS,
    *regime.CHECKS,
]

CROSS_LOG_CHECKS = [
    *crossrun.CHECKS,
]

__all__ = ["SINGLE_LOG_CHECKS", "CROSS_LOG_CHECKS"]
