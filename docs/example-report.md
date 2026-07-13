# Example audit report

Real `inspect-audit` output on the committed example logs. Reproduce with the commands shown.

## A failing log — a scorer that looks scored but graded nothing

`examples/broken.eval` has a silently dropped errored sample and a model-graded scorer whose grader returned no parseable grade (so every grade is NaN over an empty denominator).

```
$ inspect-audit examples/broken.eval
inspect-audit 0.1.0
target: examples/broken.eval
VERDICT: FAIL  (3 FAIL, 1 WARN, 15 PASS, 4 NOT_CHECKED)

[WARN] DEN003 Scorer denominator shrink (unscored samples)
    evidence : results.scores[0].unscored_samples
    detail   : scorer=match scored=1 unscored=1 total=2
    why      : scorer 'match' scored 1 of 2 sample(s); 1 were excluded from its metric denominator. The metric reads as clean while ignoring a subset.
    fix      : Determine why samples went unscored (errors, abstentions, grader failures) and either fix scoring or report the true denominator.
    aggregate_may_be_invalid: True

[FAIL] DEN003 Scorer denominator shrink (unscored samples)
    evidence : results.scores[1].unscored_samples
    detail   : scorer=model_graded_qa scored=0 unscored=2 total=2
    why      : scorer 'model_graded_qa' scored 0 of 2 sample(s); 2 were excluded from its metric denominator. The metric reads as clean while ignoring a subset — in fact NO sample was scored.
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

[FAIL] SCO004 Model-graded parse failure resolved to a default
    evidence : samples[0].scores['model_graded_qa'].explanation
    detail   : id=1 scorer=model_graded_qa value=nan explanation='Grade not found in model output: (no grade line)'
    why      : the grader for 'model_graded_qa' on sample id=1 returned no parseable grade; the scorer fell back to a default/NaN value. The metric treats a grading failure as a data point.
    fix      : Fix the grader prompt/parse pattern or the judge model output; do not count grade-not-found as a score.
    aggregate_may_be_invalid: True

[FAIL] SCO004 Model-graded parse failure resolved to a default
    evidence : samples[1].scores['model_graded_qa'].explanation
    detail   : id=2 scorer=model_graded_qa value=nan explanation='Grade not found in model output: (no grade line)'
    why      : the grader for 'model_graded_qa' on sample id=2 returned no parseable grade; the scorer fell back to a default/NaN value. The metric treats a grading failure as a data point.
    fix      : Fix the grader prompt/parse pattern or the judge model output; do not count grade-not-found as a score.
    aggregate_may_be_invalid: True

[WARN] DEN002 Completed vs total samples
    evidence : results.completed_samples
    detail   : completed=1 total=2
    why      : 1 of 2 samples did not complete. Metrics computed over completed samples describe a subset of the intended evaluation.
    fix      : Investigate incomplete samples (errors/limits); decide whether to retry, exclude explicitly, or report the reduced denominator.
    aggregate_may_be_invalid: True


checks: 3 FAIL, 1 WARN, 15 PASS, 4 NOT_CHECKED
aggregate_may_be_invalid: True
VERDICT: FAIL
note: PASS means only that the implemented checks found no issue; it is not a guarantee that the evaluation is valid. NOT_CHECKED != PASS.
```

## A clean log (verbose — note NOT_CHECKED is distinct from PASS)

```
$ inspect-audit examples/clean.eval --verbose
inspect-audit 0.1.0
target: examples/clean.eval
VERDICT: PASS  (0 FAIL, 0 WARN, 16 PASS, 7 NOT_CHECKED)

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
