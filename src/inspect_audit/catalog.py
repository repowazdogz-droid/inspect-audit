"""The single source of truth for every check: id, title, family, description,
maximum severity, and documentation reference.

Check functions read their id and title from here; the README catalog and the
registry tests are validated against it. Nothing else may define a check id.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import Status


@dataclass(frozen=True)
class CheckSpec:
    id: str
    title: str
    family: str
    description: str
    max_severity: Status  # the worst severity this check can emit
    doc_ref: str  # anchor into docs/technical-writeup.md


_DOC = "docs/technical-writeup.md"

_SPECS: list[CheckSpec] = [
    # Family 1 — denominator integrity
    CheckSpec("DEN001", "Scheduled vs recorded sample count", "denominator",
              "Reconciles dataset size x epochs against results.total_samples (skipped when the run was explicitly subset).",
              Status.WARN, f"{_DOC}#family-1--denominator-integrity-den001den005"),
    CheckSpec("DEN002", "Completed vs total samples", "denominator",
              "Flags samples that did not complete, so metrics describe a subset.",
              Status.WARN, f"{_DOC}#family-1--denominator-integrity-den001den005"),
    CheckSpec("DEN003", "Scorer denominator shrink (unscored samples)", "denominator",
              "Flags scorers whose metric denominator excludes unscored samples (inspect_ai#4286).",
              Status.FAIL, f"{_DOC}#family-1--denominator-integrity-den001den005"),
    CheckSpec("DEN004", "Samples truncated by a limit", "denominator",
              "Flags samples truncated by a token/time/message limit, whose outputs are not genuine.",
              Status.WARN, f"{_DOC}#family-1--denominator-integrity-den001den005"),
    CheckSpec("DEN005", "Abstentions (NOANSWER) accounting", "denominator",
              "Counts NOANSWER abstentions whose denominator treatment is metric-dependent.",
              Status.WARN, f"{_DOC}#family-1--denominator-integrity-den001den005"),
    # Family 2 — scorer integrity
    CheckSpec("SCO001", "Missing sample scores", "scorer",
              "Flags completed (non-errored) samples missing an expected score.",
              Status.WARN, f"{_DOC}#family-2--scorer-integrity-sco001sco004"),
    CheckSpec("SCO002", "Invalid score values", "scorer",
              "Flags NaN/inf/None score values (unambiguous corruption only).",
              Status.FAIL, f"{_DOC}#family-2--scorer-integrity-sco001sco004"),
    CheckSpec("SCO003", "Scorer produced no usable metric", "scorer",
              "Flags a scorer that recorded no metrics.",
              Status.WARN, f"{_DOC}#family-2--scorer-integrity-sco001sco004"),
    CheckSpec("SCO004", "Model-graded parse failure resolved to a default", "scorer",
              "Detects a grader parse failure scored as a data point (Inspect's 'Grade not found' contract).",
              Status.FAIL, f"{_DOC}#family-2--scorer-integrity-sco001sco004"),
    # Family 3 — judge integrity
    CheckSpec("JUD001", "Judge model recorded", "judge",
              "Flags a model-graded scorer with no judge model recorded.",
              Status.WARN, f"{_DOC}#family-3--judge-integrity-jud001-jud002-jud004"),
    CheckSpec("JUD002", "Self-judging risk (generator == judge)", "judge",
              "Flags a generator model grading its own output (bias risk, not miscomputation).",
              Status.WARN, f"{_DOC}#family-3--judge-integrity-jud001-jud002-jud004"),
    CheckSpec("JUD004", "Judge rationale preserved", "judge",
              "Flags model-graded scores that preserve no rationale to audit.",
              Status.WARN, f"{_DOC}#family-3--judge-integrity-jud001-jud002-jud004"),
    # Family 4 — run integrity
    CheckSpec("RUN000", "Log is readable", "run",
              "A log that will not parse (truncation/corruption) is a failure.",
              Status.FAIL, f"{_DOC}#family-4--run-integrity-run000run006"),
    CheckSpec("RUN001", "Run reached a successful terminal state", "run",
              "Flags status not 'success' (started/cancelled/error).",
              Status.FAIL, f"{_DOC}#family-4--run-integrity-run000run006"),
    CheckSpec("RUN002", "Results and sample records present", "run",
              "Flags missing results/sample records that should be present.",
              Status.WARN, f"{_DOC}#family-4--run-integrity-run000run006"),
    CheckSpec("RUN003", "Unique (sample id, epoch)", "run",
              "Flags duplicate (sample id, epoch) that double-count the denominator.",
              Status.FAIL, f"{_DOC}#family-4--run-integrity-run000run006"),
    CheckSpec("RUN004", "Recorded sample count matches results", "run",
              "Flags a recorded sample count that disagrees with results.total_samples.",
              Status.FAIL, f"{_DOC}#family-4--run-integrity-run000run006"),
    CheckSpec("RUN006", "Run not marked invalidated", "run",
              "Flags a run (or sample) explicitly flagged invalidated.",
              Status.WARN, f"{_DOC}#family-4--run-integrity-run000run006"),
    # Family 5 — provider / regime
    CheckSpec("REG001", "Reasoning regime pinned (heuristic)", "regime",
              "Heuristic WARN for an unpinned reasoning regime on a reasoning-looking model (inspect_ai#4295).",
              Status.WARN, f"{_DOC}#family-5--provider--regime-reg001reg003-xrn001xrn003"),
    CheckSpec("REG002", "Generation determinism pinned", "regime",
              "Flags no seed with temperature != 0 (outputs not replayable).",
              Status.WARN, f"{_DOC}#family-5--provider--regime-reg001reg003-xrn001xrn003"),
    CheckSpec("REG003", "Generation settings explicitly recorded", "regime",
              "Flags a run with no generation settings recorded (pure provider defaults).",
              Status.WARN, f"{_DOC}#family-5--provider--regime-reg001reg003-xrn001xrn003"),
    CheckSpec("XRN001", "Consistent judge model across runs", "crossrun",
              "Flags different judge models across compared runs (requires >= 2 logs).",
              Status.WARN, f"{_DOC}#family-5--provider--regime-reg001reg003-xrn001xrn003"),
    CheckSpec("XRN002", "Comparable generation settings across runs", "crossrun",
              "Flags divergent generation settings across compared runs (requires >= 2 logs).",
              Status.WARN, f"{_DOC}#family-5--provider--regime-reg001reg003-xrn001xrn003"),
    CheckSpec("XRN003", "Generation fields set symmetrically across runs", "crossrun",
              "Flags a generation field set in some runs but defaulted in others (requires >= 2 logs).",
              Status.WARN, f"{_DOC}#family-5--provider--regime-reg001reg003-xrn001xrn003"),
]

CATALOG: dict[str, CheckSpec] = {s.id: s for s in _SPECS}

FAMILY_TITLES = {
    "denominator": "Denominator integrity",
    "scorer": "Scorer integrity",
    "judge": "Judge integrity",
    "run": "Run integrity",
    "regime": "Provider / regime",
    "crossrun": "Cross-run comparability",
}


def spec(check_id: str) -> CheckSpec:
    return CATALOG[check_id]


def idtitle(check_id: str) -> tuple[str, str]:
    """Return (id, title) for a check from the single source of truth."""
    s = CATALOG[check_id]
    return s.id, s.title


def registered(check_id: str):
    """Decorator: tag a check function with its catalog id and validate it."""
    if check_id not in CATALOG:
        raise KeyError(f"check id {check_id!r} is not in the catalog")

    def deco(fn):
        fn.check_id = check_id
        return fn

    return deco


def all_ids() -> set[str]:
    return set(CATALOG)


def render_markdown() -> str:
    """Render the catalog as a Markdown table, grouped by family."""
    lines = ["| ID | Title | Max | What it catches |", "|----|-------|-----|-----------------|"]
    for fam in FAMILY_TITLES:
        for s in _SPECS:
            if s.family == fam:
                lines.append(f"| `{s.id}` | {s.title} | {s.max_severity.label} | {s.description} |")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    print(render_markdown())
