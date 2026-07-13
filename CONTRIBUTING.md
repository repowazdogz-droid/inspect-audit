# Contributing

Thanks for taking a look. inspect-audit is deliberately small and conservative.

## Principles

- **Read-only.** A check may never modify, move, or rewrite a source log.
- **Ground every check in the real schema.** Bind to fields that exist in
  `inspect_ai`; don't guess. If a signal is heuristic, label it and cap it at
  `WARN`.
- **No universal claims.** `PASS` means the implemented checks found nothing, not
  that an evaluation is valid. Keep `NOT_CHECKED` distinct from `PASS`.
- **Every check must be falsifiable.** A new check needs a fixture that carries
  its defect and a mutation test proving it fires on that fixture and stays quiet
  on a clean log.

## Adding a check

1. Add its entry to `src/inspect_audit/catalog.py` (the single source of truth).
2. Implement it in the relevant `src/inspect_audit/checks/*.py`, decorated with
   `@registered("XXX")`, sourcing its id/title from the catalog.
3. Add a defect fixture to `fixtures/build_fixtures.py` and a row to the mutation
   test matrix in `tests/test_mutation.py`.
4. Add its id to the README catalog table (a test enforces docs == code).

## Dev loop

```bash
pip install -e ".[dev]"
python fixtures/build_fixtures.py
pytest
ruff check .
mypy src
```

All of the above run in CI on Python 3.11–3.13. Please keep lint and types green
without disabling error classes.
