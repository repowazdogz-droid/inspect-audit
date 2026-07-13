# inspect-audit

A small, read-only auditor for [Inspect](https://github.com/UKGovernmentBEIS/inspect_ai)
`.eval` logs. It looks for **silent validity failures** — the kind that let an
evaluation result read as clean while being wrong: samples quietly dropped from a
metric's denominator, grader parse-failures scored as data, a model grading its
own output, duplicated samples, truncated logs, and runs whose generation
settings make them non-reproducible or not comparable.

It is static analysis. It does **not** run models, does **not** use an LLM judge,
and **never modifies the log it reads**.

```bash
pip install inspect-audit
inspect-audit run.eval
```

```
inspect-audit run.eval another.eval   # cross-run comparability checks
inspect-audit run.eval --json          # machine-readable
inspect-audit run.eval --verbose       # also list PASS / NOT_CHECKED
```

## What it checks

Five families, grounded in fields that actually exist in the Inspect log schema
(verified against `inspect_ai` 0.3.246). Each is motivated by a real, observed
failure mode — see [docs/technical-writeup.md](docs/technical-writeup.md).

| Family | Checks | Example failure caught |
|---|---|---|
| **Denominator integrity** | DEN001–DEN005 | a scorer reports a clean mean over samples it silently didn't score ([inspect_ai#4286](https://github.com/UKGovernmentBEIS/inspect_ai/issues/4286)) |
| **Scorer integrity** | SCO001–SCO004 | a grader returns no parseable grade and the sample gets a NaN/default score |
| **Judge integrity** | JUD001, JUD002, JUD004 | the generator model also grades its own answers |
| **Run integrity** | RUN000–RUN006 | duplicated sample ids, truncated log, non-success status |
| **Provider / regime** | REG001–REG003, XRN001–XRN003 | reasoning effort left to provider default, making two models incomparable ([inspect_ai#4295](https://github.com/UKGovernmentBEIS/inspect_ai/issues/4295)) |

## Output

Every finding carries: a **check id**, the **evidence path** into the `.eval`
log, **why it matters**, a **remediation**, and whether the finding means the
**aggregate result may be invalid**. The overall verdict is `PASS`, `WARN`, or
`FAIL`. Exit codes: `0` PASS, `1` WARN, `2` FAIL (use `--exit-zero` to suppress).

See [docs/example-report.md](docs/example-report.md) for a worked example.

## Assurance boundary (read this)

`inspect-audit` tells you where an evaluation log **is** wrong in the ways it
knows how to look. It cannot tell you an evaluation is **right**.

- **`PASS` means only that the implemented checks found no issue.** It is not a
  certificate of validity. There are many ways an evaluation can be wrong that
  this tool does not model (a biased dataset, a mis-specified task, a subtly
  wrong-but-parseable grade, contamination, an unfair prompt).
- **`NOT_CHECKED` is not `PASS`.** A check reports `NOT_CHECKED` when the data it
  needs is absent (samples not logged, header-only read, or a cross-run check
  given a single log). The report always shows these explicitly.
- **The checks are static and conservative.** They read only what the log
  records. Where a signal is heuristic (e.g. guessing a reasoning model from its
  name, REG001) it is labelled as such and only ever raises a `WARN`.
- **No universal claims.** The tool asserts nothing about evaluations in general,
  only about the specific log in front of it.

Full statement: [docs/assurance-boundary.md](docs/assurance-boundary.md).

## Development

```bash
pip install -e ".[dev]"
python fixtures/build_fixtures.py   # regenerate the fixture corpus
pytest                              # run the suite (incl. mutation tests)
```

## License

MIT.
