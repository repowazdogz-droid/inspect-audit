"""Family 5: provider / generation-regime warnings (single log).

Surfaces generation settings that make a result non-reproducible or not
comparable across models/providers. Motivated by inspect_ai#4295 (an unset
reasoning_effort silently yields different reasoning regimes across providers).
"""

from __future__ import annotations

from ..loader import Target
from ..model import CheckResult, Finding, Status
from ._util import gen_config_dict, looks_like_reasoning_model


def check_reasoning_regime(t: Target) -> CheckResult:
    cid, title = "REG001", "Reasoning regime pinned (heuristic)"
    cfg = gen_config_dict(t.log)
    model = getattr(t.log.eval, "model", "") or ""
    if ("reasoning_effort" in cfg) or ("effort" in cfg) or ("reasoning_tokens" in cfg):
        return CheckResult.from_findings(cid, title, [])  # explicitly pinned
    if not looks_like_reasoning_model(model):
        return CheckResult.not_checked(
            cid, title,
            "model name does not match the reasoning-model heuristic; regime pinning not applicable",
        )
    return CheckResult.from_findings(
        cid, title,
        [Finding(
            cid, Status.WARN, "eval.model_generate_config.reasoning_effort",
            why_it_matters=(
                f"model '{model}' looks like a reasoning model but no reasoning "
                "effort/tokens were pinned. The provider default regime is used, so "
                "this run is not comparable to another provider's default (heuristic "
                "based on model name)."
            ),
            remediation="Set reasoning_effort/effort explicitly for every model in a comparison.",
            aggregate_may_be_invalid=False,
            detail=f"model={model}",
        )],
    )


def check_nondeterministic(t: Target) -> CheckResult:
    cid, title = "REG002", "Generation determinism pinned"
    cfg = gen_config_dict(t.log)
    if not cfg:
        return CheckResult.not_checked(cid, title, "no generation settings recorded (see REG003)")
    seed = cfg.get("seed")
    temp = cfg.get("temperature")
    if seed is not None:
        return CheckResult.from_findings(cid, title, [])
    if temp == 0:
        return CheckResult.from_findings(cid, title, [])
    return CheckResult.from_findings(
        cid, title,
        [Finding(
            cid, Status.WARN, "eval.model_generate_config.seed",
            why_it_matters=(
                "no seed is set and temperature is not 0"
                f" (temperature={temp!r}); re-running will not reproduce these exact "
                "outputs, so the numbers are not replayable."
            ),
            remediation="Set a seed and/or temperature=0 where the provider supports it; record that determinism is best-effort for closed APIs.",
            aggregate_may_be_invalid=False,
            detail=f"seed=None temperature={temp!r}",
        )],
    )


def check_config_empty(t: Target) -> CheckResult:
    cid, title = "REG003", "Generation settings explicitly recorded"
    cfg = gen_config_dict(t.log)
    if cfg:
        return CheckResult.from_findings(cid, title, [])
    return CheckResult.from_findings(
        cid, title,
        [Finding(
            cid, Status.WARN, "eval.model_generate_config",
            why_it_matters=(
                "no generation settings were recorded; the run used provider "
                "defaults for temperature, seed, reasoning, etc. Two models compared "
                "this way are not on equal footing."
            ),
            remediation="Set generation parameters explicitly so runs are reproducible and comparable.",
            aggregate_may_be_invalid=False,
            detail="model_generate_config is empty",
        )],
    )


CHECKS = [
    check_reasoning_regime,
    check_nondeterministic,
    check_config_empty,
]
