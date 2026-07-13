"""Shared helpers for checks. Pure functions over the Inspect log model."""

from __future__ import annotations

import math
from typing import Any, Optional

# Inspect's model-graded scorers write this exact explanation prefix when the
# grader response contains no parseable grade (see inspect_ai.scorer._model).
GRADE_NOT_FOUND_PREFIX = "Grade not found in model output"

# Conservative list of substrings identifying models that run a reasoning /
# thinking regime whose effort is provider-defaulted when unset. Used only by a
# clearly-labelled heuristic WARN (REG001); never drives a FAIL.
REASONING_MODEL_HINTS = (
    "o1", "o3", "o4", "gpt-5", "deepseek-r1", "deepseek-reasoner",
    "-thinking", "qwq", "reason",
)


def is_nan(v: Any) -> bool:
    return isinstance(v, float) and math.isnan(v)


def is_bad_number(v: Any) -> bool:
    return isinstance(v, float) and (math.isnan(v) or math.isinf(v))


def scorer_specs(log: Any) -> list[Any]:
    return list(getattr(log.eval, "scorers", None) or [])


def judge_model_from_score(score: Any) -> Optional[str]:
    """Judge/grader model recorded in an EvalScore's params, if any."""
    params = getattr(score, "params", None) or {}
    m = params.get("model")
    return m if isinstance(m, str) and m else None


def judge_model_from_scorer_spec(spec: Any) -> Optional[str]:
    opts = getattr(spec, "options", None) or {}
    m = opts.get("model")
    return m if isinstance(m, str) and m else None


def score_looks_model_graded(score: Any) -> bool:
    """A score is treated as model-graded iff a judge model is recorded for it.

    This is a deliberately conservative signal: we only make judge-related claims
    about scorers that demonstrably invoked a judge model.
    """
    return judge_model_from_score(score) is not None


def spec_looks_model_graded(spec: Any) -> bool:
    if judge_model_from_scorer_spec(spec) is not None:
        return True
    name = (getattr(spec, "name", "") or "").lower()
    return "model_graded" in name or "grader" in name


def score_name_looks_model_graded(score: Any) -> bool:
    text = f"{getattr(score, 'name', '')} {getattr(score, 'scorer', '')}".lower()
    return "model_graded" in text or "grader" in text


def models_materially_identical(a: Optional[str], b: Optional[str]) -> bool:
    """Same provider/model string => same weights answering and grading."""
    if not a or not b:
        return False
    return a.strip() == b.strip()


def looks_like_reasoning_model(model: str) -> bool:
    m = (model or "").lower()
    return any(h in m for h in REASONING_MODEL_HINTS)


def gen_config_dict(log: Any) -> dict[str, Any]:
    cfg = getattr(log.eval, "model_generate_config", None)
    if cfg is None:
        return {}
    if hasattr(cfg, "model_dump"):
        return {k: v for k, v in cfg.model_dump().items() if v is not None}
    return {}
