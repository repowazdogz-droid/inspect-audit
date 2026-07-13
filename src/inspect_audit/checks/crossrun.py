"""Cross-run consistency checks (require >= 2 logs).

When several logs are audited together (``inspect-audit a.eval b.eval``) these
flag differences that make the runs not directly comparable. With a single log
they report NOT_CHECKED.
"""

from __future__ import annotations

from ..catalog import idtitle, registered
from ..loader import Target
from ..model import CheckResult, Finding, Status
from ._util import gen_config_dict, judge_model_from_score

COMPARABILITY_KEYS = (
    "temperature", "seed", "top_p", "top_k", "max_tokens",
    "reasoning_effort", "effort", "reasoning_tokens",
)


def _judge_models(t: Target) -> dict[str, str]:
    out: dict[str, str] = {}
    results = getattr(t.log, "results", None)
    for sc in (getattr(results, "scores", None) or []):
        jm = judge_model_from_score(sc)
        if jm:
            out[sc.name] = jm
    return out


@registered("XRN001")
def check_judge_divergence(targets: list[Target]) -> CheckResult:
    cid, title = idtitle("XRN001")
    if len(targets) < 2:
        return CheckResult.not_checked(cid, title, "requires >= 2 logs")
    by_scorer: dict[str, set[str]] = {}
    for t in targets:
        for name, jm in _judge_models(t).items():
            by_scorer.setdefault(name, set()).add(jm)
    findings: list[Finding] = []
    for name, models in sorted(by_scorer.items()):
        if len(models) > 1:
            findings.append(Finding(
                cid, Status.WARN, f"results.scores[name={name}].params.model",
                why_it_matters=f"scorer '{name}' was graded by different judge models across the runs ({sorted(models)}); scores graded by different judges are not directly comparable.",
                remediation="Use the same judge model/version across all runs being compared.",
                aggregate_may_be_invalid=False,
                detail=f"scorer={name} judges={sorted(models)}",
            ))
    return CheckResult.from_findings(cid, title, findings)


@registered("XRN002")
def check_config_divergence(targets: list[Target]) -> CheckResult:
    cid, title = idtitle("XRN002")
    if len(targets) < 2:
        return CheckResult.not_checked(cid, title, "requires >= 2 logs")
    cfgs = [gen_config_dict(t.log) for t in targets]
    findings: list[Finding] = []
    for key in COMPARABILITY_KEYS:
        vals = {c.get(key) for c in cfgs}
        if len(vals) > 1:
            findings.append(Finding(
                cid, Status.WARN, f"eval.model_generate_config.{key}",
                why_it_matters=f"'{key}' differs across the runs ({sorted(map(repr, vals))}); a metric difference may be an artefact of generation settings, not the model.",
                remediation=f"Pin '{key}' to the same value across all compared runs.",
                aggregate_may_be_invalid=False,
                detail=f"{key} values={sorted(map(repr, vals))}",
            ))
    return CheckResult.from_findings(cid, title, findings)


@registered("XRN003")
def check_presence_asymmetry(targets: list[Target]) -> CheckResult:
    cid, title = idtitle("XRN003")
    if len(targets) < 2:
        return CheckResult.not_checked(cid, title, "requires >= 2 logs")
    cfgs = [gen_config_dict(t.log) for t in targets]
    findings: list[Finding] = []
    for key in COMPARABILITY_KEYS:
        present = [key in c for c in cfgs]
        if any(present) and not all(present):
            set_in = [targets[i].name for i, p in enumerate(present) if p]
            unset_in = [targets[i].name for i, p in enumerate(present) if not p]
            findings.append(Finding(
                cid, Status.WARN, f"eval.model_generate_config.{key}",
                why_it_matters=f"'{key}' is set in some runs ({set_in}) but left to the provider default in others ({unset_in}); the unset runs may use a silently different regime.",
                remediation=f"Set '{key}' explicitly in every compared run, or confirm the defaults match.",
                aggregate_may_be_invalid=False,
                detail=f"{key} set_in={set_in} unset_in={unset_in}",
            ))
    return CheckResult.from_findings(cid, title, findings)


CHECKS = [
    check_judge_divergence,
    check_config_divergence,
    check_presence_asymmetry,
]
