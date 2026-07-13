# Example audit report

Real `inspect-audit` output on fixture logs (regenerate with `python fixtures/build_fixtures.py`).

## A failing log: a model-graded scorer that graded nothing

The grader returned no parseable grade, so every sample got a `NaN` score, yet a metric row exists over an empty denominator.

```
inspect-audit 0.1.0
target: fixtures/corpus/scorer_parse_failure.eval

[FAIL] DEN003 Scorer denominator shrink (unscored samples)
    evidence : results.scores[1].unscored_samples
    detail   : scorer=model_graded_qa scored=0 unscored=3 total=3
    why      : scorer 'model_graded_qa' scored 0 of 3 sample(s); 3 were excluded from its metric denominator. The metric reads as clean while ignoring a subset — in fact NO sample was scored.
    fix      : Determine why samples went unscored (errors, abstentions, grader failures) and either fix scoring or report the true denominator.
    aggregate_may_be_invalid: True

[FAIL] SCO002 Invalid score values
    evidence : samples[0].scores['model_graded_qa'].value
    detail   : id=1 scorer=model_graded_qa value=nan reason=non-finite (NaN/inf)
    why      : score 'model_graded_qa' on sample id=1 has a non-finite (NaN/inf) value (nan). Aggregating it can silently corrupt or skew the metric.
    fix      : Locate the scoring failure; a NaN/None value usually means the scorer errored or could not parse a result.
    aggregate_may_be_invalid: True

[FAIL] SCO002 Invalid score values
    evidence : samples[1].scores['model_graded_qa'].value
    detail   : id=2 scorer=model_graded_qa value=nan reason=non-finite (NaN/inf)
    why      : score 'model_graded_qa' on sample id=2 has a non-finite (NaN/inf) value (nan). Aggregating it can silently corrupt or skew the metric.
    fix      : Locate the scoring failure; a NaN/None value usually means the scorer errored or could not parse a result.
    aggregate_may_be_invalid: True

[FAIL] SCO002 Invalid score values
    evidence : samples[2].scores['model_graded_qa'].value
    detail   : id=3 scorer=model_graded_qa value=nan reason=non-finite (NaN/inf)
    why      : score 'model_graded_qa' on sample id=3 has a non-finite (NaN/inf) value (nan). Aggregating it can silently corrupt or skew the metric.
    fix      : Locate the scoring failure; a NaN/None value usually means the scorer errored or could not parse a result.
    aggregate_may_be_invalid: True

[FAIL] SCO004 Model-graded parse failure resolved to a default
    evidence : samples[0].scores['model_graded_qa'].explanation
    detail   : id=1 scorer=model_graded_qa value=nan explanation='Grade not found in model output: Default output'
    why      : the grader for 'model_graded_qa' on sample id=1 returned no parseable grade; the scorer fell back to a default/NaN value. The metric treats a grading failure as a data point.
    fix      : Fix the grader prompt/parse pattern or the judge model output; do not count grade-not-found as a score.
    aggregate_may_be_invalid: True

[FAIL] SCO004 Model-graded parse failure resolved to a default
    evidence : samples[1].scores['model_graded_qa'].explanation
    detail   : id=2 scorer=model_graded_qa value=nan explanation='Grade not found in model output: Default output'
    why      : the grader for 'model_graded_qa' on sample id=2 returned no parseable grade; the scorer fell back to a default/NaN value. The metric treats a grading failure as a data point.
    fix      : Fix the grader prompt/parse pattern or the judge model output; do not count grade-not-found as a score.
    aggregate_may_be_invalid: True

[FAIL] SCO004 Model-graded parse failure resolved to a default
    evidence : samples[2].scores['model_graded_qa'].explanation
    detail   : id=3 scorer=model_graded_qa value=nan explanation='Grade not found in model output: Default output'
    why      : the grader for 'model_graded_qa' on sample id=3 returned no parseable grade; the scorer fell back to a default/NaN value. The metric treats a grading failure as a data point.
    fix      : Fix the grader prompt/parse pattern or the judge model output; do not count grade-not-found as a score.
    aggregate_may_be_invalid: True


checks: 3 FAIL, 0 WARN, 16 PASS, 4 NOT_CHECKED
aggregate_may_be_invalid: True
VERDICT: FAIL
note: PASS means only that the implemented checks found no issue; it is not a guarantee that the evaluation is valid. NOT_CHECKED != PASS.
```

## A clean log (verbose, showing NOT_CHECKED vs PASS)

```
inspect-audit 0.1.0
target: fixtures/corpus/clean.eval

[PASS] DEN001 Scheduled vs recorded sample count
[PASS] DEN002 Completed vs total samples
[PASS] DEN003 Scorer denominator shrink (unscored samples)
[PASS] DEN004 Samples truncated by a limit
[PASS] DEN005 Abstentions (NOANSWER) accounting
[PASS] REG002 Generation determinism pinned
[PASS] REG003 Generation settings explicitly recorded
[PASS] RUN001 Run reached a successful terminal state
[PASS] RUN002 Results and sample records present
[PASS] RUN003 Unique (sample id, epoch)
[PASS] RUN004 Recorded sample count matches results
[PASS] RUN006 Run not marked invalidated
[PASS] SCO001 Missing sample scores
[PASS] SCO002 Invalid score values
[PASS] SCO003 Scorer produced no usable metric
[PASS] SCO004 Model-graded parse failure resolved to a default
[NOT_CHECKED] JUD001 Judge model recorded — no model-graded scorer detected
[NOT_CHECKED] JUD002 Self-judging risk (generator == judge) — no model-graded scorer detected
[NOT_CHECKED] JUD004 Judge rationale preserved — no model-graded scorer detected
[NOT_CHECKED] REG001 Reasoning regime pinned (heuristic) — model name does not match the reasoning-model heuristic; regime pinning not applicable
[NOT_CHECKED] XRN001 Consistent judge model across runs — requires >= 2 logs
[NOT_CHECKED] XRN002 Comparable generation settings across runs — requires >= 2 logs
[NOT_CHECKED] XRN003 Generation fields set symmetrically across runs — requires >= 2 logs
checks: 0 FAIL, 0 WARN, 16 PASS, 7 NOT_CHECKED
aggregate_may_be_invalid: False
VERDICT: PASS
note: PASS means only that the implemented checks found no issue; it is not a guarantee that the evaluation is valid. NOT_CHECKED != PASS.
```

## Cross-run comparability (two logs)

```
inspect-audit 0.1.0
target: 2 log(s)

[WARN] REG002 Generation determinism pinned
    evidence : eval.model_generate_config.seed
    detail   : seed=None temperature=0.7
    why      : no seed is set and temperature is not 0 (temperature=0.7); re-running will not reproduce these exact outputs, so the numbers are not replayable.
    fix      : Set a seed and/or temperature=0 where the provider supports it; record that determinism is best-effort for closed APIs.
    aggregate_may_be_invalid: False

[WARN] XRN002 Comparable generation settings across runs
    evidence : eval.model_generate_config.seed
    detail   : seed values=['42', 'None']
    why      : 'seed' differs across the runs (['42', 'None']); a metric difference may be an artefact of generation settings, not the model.
    fix      : Pin 'seed' to the same value across all compared runs.
    aggregate_may_be_invalid: False

[WARN] XRN002 Comparable generation settings across runs
    evidence : eval.model_generate_config.temperature
    detail   : temperature values=['0.0', '0.7']
    why      : 'temperature' differs across the runs (['0.0', '0.7']); a metric difference may be an artefact of generation settings, not the model.
    fix      : Pin 'temperature' to the same value across all compared runs.
    aggregate_may_be_invalid: False

[WARN] XRN003 Generation fields set symmetrically across runs
    evidence : eval.model_generate_config.seed
    detail   : seed set_in=['clean.eval'] unset_in=['config_variant_b.eval']
    why      : 'seed' is set in some runs (['clean.eval']) but left to the provider default in others (['config_variant_b.eval']); the unset runs may use a silently different regime.
    fix      : Set 'seed' explicitly in every compared run, or confirm the defaults match.
    aggregate_may_be_invalid: False


checks: 0 FAIL, 3 WARN, 32 PASS, 8 NOT_CHECKED
aggregate_may_be_invalid: False
VERDICT: WARN
note: PASS means only that the implemented checks found no issue; it is not a guarantee that the evaluation is valid. NOT_CHECKED != PASS.
```
