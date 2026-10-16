# inspect-audit

`inspect-audit` reads an Inspect AI .eval log without modifying it and reports FAIL when a grader's parse failure was scored as data.

[![CI](https://github.com/repowazdogz-droid/inspect-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/repowazdogz-droid/inspect-audit/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/repowazdogz-droid/inspect-audit)](https://github.com/repowazdogz-droid/inspect-audit/releases/latest)

## Try it

Two example logs ship in `examples/`. With [pipx](https://pipx.pypa.io):

```console
git clone https://github.com/repowazdogz-droid/inspect-audit
cd inspect-audit
pipx install .
inspect-audit examples/broken.eval
inspect-audit examples/clean.eval
```

In `broken.eval` the model-graded scorer graded none of its two samples: both
grader outputs failed to parse and were recorded as NaN scores. The first command
reports `VERDICT: FAIL` (SCO002, SCO004 and DEN003 fire) and exits `2`. The
second reports `VERDICT: PASS` and exits `0`.

## What this does not show

`inspect-audit` reports where an evaluation log is wrong in the ways it knows how
to look. It cannot tell you an evaluation is right. Full statement:
[docs/assurance-boundary.md](docs/assurance-boundary.md).

- **`PASS` means only that the implemented checks found no issue.** It is not a
  certificate of validity. Many ways an evaluation can be wrong are not modelled
  here: a biased or contaminated dataset, a mis-specified task, an unfair prompt,
  a grade that is wrong but parseable.
- **`NOT_CHECKED` is not `PASS`.** A check reports `NOT_CHECKED` when the data it
  needs is absent (samples not logged, header-only read, or a cross-run check
  given a single log). The report always shows these explicitly.
- **It sees only what the log records.** It is static analysis over the `.eval`
  file. It runs no model and uses no LLM judge, so it does not judge whether an
  answer or a grade was correct.
- **Some signals are heuristic or rest on a string contract.** REG001 guesses a
  reasoning model from its name and is only ever `WARN`. SCO004 keys off the
  explanation prefix Inspect writes on a grader parse failure (`"Grade not found
  in model output"`); a future Inspect release could change it.
- **Not every check has a mutation test.** The mutation matrix in
  `tests/test_mutation.py` (a fixture carrying the defect, and the clean log)
  covers 10 of the 24 checks.

## What it does

A read-only auditor for [Inspect](https://github.com/UKGovernmentBEIS/inspect_ai)
`.eval` logs. It looks for silent validity failures, the kind that let an
evaluation result read as clean while being wrong: samples quietly dropped from a
metric's denominator, grader parse failures scored as data, a model grading its
own output, duplicated samples, truncated logs, and runs whose generation
settings make them non-reproducible or not comparable. It is static analysis and
never modifies the log it reads.

## Install

Not yet published to PyPI. Install from GitHub:

```bash
pip install git+https://github.com/repowazdogz-droid/inspect-audit
```

## Use

```bash
inspect-audit run.eval another.eval   # cross-run comparability checks
inspect-audit run.eval --json          # machine-readable
inspect-audit run.eval --verbose       # also list PASS / NOT_CHECKED
```

Exit codes: `0` PASS, `1` WARN, `2` FAIL (`--exit-zero` to suppress).

## Programmatic use

```python
from inspect_audit import audit_paths, to_json

report = audit_paths(["run.eval"])          # never modifies the log
print(report.overall.label)                 # "PASS" | "WARN" | "FAIL"
if report.aggregate_may_be_invalid:
    print(to_json(report))                  # full machine-readable report
```

`audit_paths`, `AuditReport`, `Status`, `to_dict`, `to_json`, and the check
`CATALOG` are the stable public surface.

## Check catalog

Every implemented check (the catalog below is the single source of truth; a test
fails if this list and the code diverge). Motivation for each is in
[docs/technical-writeup.md](docs/technical-writeup.md).

<!-- CATALOG -->
| ID | Title | Max | What it catches |
|----|-------|-----|-----------------|
| `DEN001` | Scheduled vs recorded sample count | WARN | Reconciles dataset size x epochs against results.total_samples (skipped when the run was explicitly subset). |
| `DEN002` | Completed vs total samples | WARN | Flags samples that did not complete, so metrics describe a subset. |
| `DEN003` | Scorer denominator shrink (unscored samples) | FAIL | Flags scorers whose metric denominator excludes unscored samples (inspect_ai#4286). |
| `DEN004` | Samples truncated by a limit | WARN | Flags samples truncated by a token/time/message limit, whose outputs are not genuine. |
| `DEN005` | Abstentions (NOANSWER) accounting | WARN | Counts NOANSWER abstentions whose denominator treatment is metric-dependent. |
| `SCO001` | Missing sample scores | WARN | Flags completed (non-errored) samples missing an expected score. |
| `SCO002` | Invalid score values | FAIL | Flags NaN/inf/None score values (unambiguous corruption only). |
| `SCO003` | Scorer produced no usable metric | WARN | Flags a scorer that recorded no metrics. |
| `SCO004` | Model-graded parse failure resolved to a default | FAIL | Detects a grader parse failure scored as a data point (Inspect's 'Grade not found' contract). |
| `JUD001` | Judge model recorded | WARN | Flags a model-graded scorer with no judge model recorded. |
| `JUD002` | Self-judging risk (generator == judge) | WARN | Flags a generator model grading its own output (bias risk, not miscomputation). |
| `JUD004` | Judge rationale preserved | WARN | Flags model-graded scores that preserve no rationale to audit. |
| `RUN000` | Log is readable | FAIL | A log that will not parse (truncation/corruption) is a failure. |
| `RUN001` | Run reached a successful terminal state | FAIL | Flags status not 'success' (started/cancelled/error). |
| `RUN002` | Results and sample records present | WARN | Flags missing results/sample records that should be present. |
| `RUN003` | Unique (sample id, epoch) | FAIL | Flags duplicate (sample id, epoch) that double-count the denominator. |
| `RUN004` | Recorded sample count matches results | FAIL | Flags a recorded sample count that disagrees with results.total_samples. |
| `RUN006` | Run not marked invalidated | WARN | Flags a run (or sample) explicitly flagged invalidated. |
| `REG001` | Reasoning regime pinned (heuristic) | WARN | Heuristic WARN for an unpinned reasoning regime on a reasoning-looking model (inspect_ai#4295). |
| `REG002` | Generation determinism pinned | WARN | Flags no seed with temperature != 0 (outputs not replayable). |
| `REG003` | Generation settings explicitly recorded | WARN | Flags a run with no generation settings recorded (pure provider defaults). |
| `XRN001` | Consistent judge model across runs | WARN | Flags different judge models across compared runs (requires >= 2 logs). |
| `XRN002` | Comparable generation settings across runs | WARN | Flags divergent generation settings across compared runs (requires >= 2 logs). |
| `XRN003` | Generation fields set symmetrically across runs | WARN | Flags a generation field set in some runs but defaulted in others (requires >= 2 logs). |
<!-- /CATALOG -->

Two checks were considered and deliberately cut; they are documented in the
[technical write-up](docs/technical-writeup.md#checks-considered-and-cut).

## Output

Every finding carries: a **check id**, the **evidence path** into the `.eval`
log, **why it matters**, a **remediation**, and whether the finding means the
**aggregate result may be invalid**. The overall verdict (`PASS`/`WARN`/`FAIL`)
prints at the top and the bottom. See
[docs/example-report.md](docs/example-report.md) for a worked example.

## Development

```bash
pip install -e ".[dev]"
python examples/build_examples.py   # regenerate example logs
python fixtures/build_fixtures.py   # regenerate the test fixture corpus
pytest                              # tests
ruff check .                        # lint
mypy src                            # type-check
```

The suite has 58 tests (`pytest --collect-only -q` collects 58).

Maintainer: [@repowazdogz-droid](https://github.com/repowazdogz-droid). See
[CONTRIBUTING.md](CONTRIBUTING.md). Licensed MIT.
