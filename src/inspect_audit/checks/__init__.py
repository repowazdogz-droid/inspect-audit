"""Check registry.

SINGLE_LOG_CHECKS run against one Target. CROSS_LOG_CHECKS run against the list
of Targets (and self-report NOT_CHECKED when fewer than two are supplied).
Order here is the deterministic reporting order.
"""

from . import crossrun, denominator, judge, regime, run_integrity, scorer

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

# Every check implemented as a function (RUN000 is implemented in audit.py as the
# load-failure path, not as a check function, and is registered separately).
ALL_CHECK_FUNCS = [*SINGLE_LOG_CHECKS, *CROSS_LOG_CHECKS]

IMPLEMENTED_IDS = {fn.check_id for fn in ALL_CHECK_FUNCS} | {"RUN000"}

__all__ = ["SINGLE_LOG_CHECKS", "CROSS_LOG_CHECKS", "ALL_CHECK_FUNCS", "IMPLEMENTED_IDS"]
