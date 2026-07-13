# The failure modes inspect-audit checks, and why

Each check exists because an evaluation log can look clean while being wrong in a
specific way. This document records the motivation for each, grounded in the real
Inspect log schema (verified against `inspect_ai` 0.3.246) and in observed
behaviour — including a failure the tool's own fixtures reproduced spontaneously.

## The motivating observation

While building the fixture corpus, a two-sample eval scored with
`model_graded_qa` backed by a mock grader produced this, with no special effort:

- `results.scores[1].scored_samples = 0`, `unscored_samples = 2`
- each sample's grade `value = NaN`, `explanation = "Grade not found in model output: ..."`
- a metric row nonetheless present, and the grader model equal to the generator model.

That single accident contains four independent silent failures: an empty
denominator, NaN score values, a grader parse-failure resolved to a default, and
self-grading. Every family below traces to a defect of that kind.

## Family 1 — Denominator integrity (DEN001–DEN005)

Motivated by [inspect_ai#4286](https://github.com/UKGovernmentBEIS/inspect_ai/issues/4286):
scoring metrics can silently drop inconclusive or errored samples from the
denominator, so a mean reads as clean while ignoring a subset.

- **DEN001** reconciles `dataset.samples x epochs` against `results.total_samples`.
  It reports `NOT_CHECKED` when the run was explicitly subset (`limit`/`sample_id`),
  because then the dataset size is not the scheduled size — reconciling would
  false-positive (this was caught in review against a real `--limit` run).
- **DEN002** flags `completed_samples < total_samples`.
- **DEN003** is the core #4286 check: any scorer with `unscored_samples > 0` has a
  shrunk denominator; `scored_samples == 0` (scored nothing) is a FAIL.
- **DEN004** flags samples truncated by a `limit` (their outputs are not genuine).
- **DEN005** counts `NOANSWER` abstentions, whose denominator treatment is
  metric-dependent and easy to get silently wrong.

## Family 2 — Scorer integrity (SCO001–SCO004)

- **SCO001** flags completed (non-errored) samples missing an expected score.
- **SCO002** flags `NaN`/`inf`/`None` score values — unambiguous corruption. It
  deliberately does **not** flag arbitrary strings, numbers, lists or dicts:
  those are legitimate for custom scorers, and flagging them would false-positive
  on valid categorical scorers (cut in review).
- **SCO003** flags a scorer that recorded no metrics.
- **SCO004** detects a model-graded parse failure via Inspect's own explanation
  contract (`"Grade not found in model output"`). A grade-not-found scored as a
  data point is a FAIL.

## Family 3 — Judge integrity (JUD001, JUD002, JUD004)

Judge metadata for model-graded scorers lives in the scorer's `params`
(`params.model`), not in `model_roles` — verified directly against 0.3.246.

- **JUD001** flags a model-graded scorer with no judge model recorded.
- **JUD002** flags self-grading (generator model == judge model). It is a WARN,
  not a FAIL, and does not claim the aggregate is *invalid* — self-grading biases
  a number without miscomputing it, and is sometimes intentional.
- **JUD004** flags model-graded scores that preserve no rationale to audit.

## Family 4 — Run integrity (RUN000–RUN006)

- **RUN000** a log that will not parse (truncation/corruption) is a FAIL.
- **RUN001** status not `success` (started/cancelled/error).
- **RUN002** results/sample records missing when they should be present.
- **RUN003** duplicate `(sample id, epoch)` — double-counts the denominator.
- **RUN004** recorded sample count disagrees with `results.total_samples`.
- **RUN006** the run (or a sample) is explicitly flagged invalidated.

## Family 5 — Provider / regime (REG001–REG003, XRN001–XRN003)

Motivated by [inspect_ai#4295](https://github.com/UKGovernmentBEIS/inspect_ai/issues/4295):
an unset `reasoning_effort` yields a provider-default regime, so two models are
compared on unequal footing. The maintainers explicitly declined to fix this by
default ("the user needs to consider this explicitly"), which is why an external
companion is the right home for it.

- **REG001** (heuristic, WARN-only) an unpinned reasoning regime on a model whose
  name looks like a reasoning model.
- **REG002** no seed and temperature not 0 — outputs are not replayable.
- **REG003** no generation settings recorded at all — pure provider defaults.
- **XRN001–XRN003** (require >= 2 logs) judge model, generation settings, and
  field-presence divergence across runs being compared.

## Checks considered and cut

Kept out of v0.1 on the "survive a hostile review" bar:

- **JUD003 "judge rubric captured"** — Inspect stores only overridden scorer
  args, so the default grading template is legitimately absent from the log. This
  check would fire on essentially every default-template model-graded eval:
  technically true, but too noisy to be trusted, and not a defect.
- **RUN005 "model-usage consistency"** — comparing the models seen in usage
  against the declared model plus roles produced false positives around grader
  and fallback models. Not robust enough to ship.

## Version contract

The checks bind to fields present in `inspect_ai` 0.3.246. The most brittle
coupling is SCO004's dependence on the exact "Grade not found in model output"
explanation string; if a future Inspect release changes that text, SCO004 needs
updating. Everything else reads structured fields.
