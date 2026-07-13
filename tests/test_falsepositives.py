"""Guards against known false positives found in the three-persona review."""

import warnings

from inspect_audit.audit import audit_paths
from conftest import status_of

warnings.filterwarnings("ignore")


def _limited_log(tmp_path):
    from inspect_ai import Task, eval as inspect_eval
    from inspect_ai.dataset import Sample
    from inspect_ai.model import GenerateConfig, ModelOutput, get_model
    from inspect_ai.scorer import match

    m = get_model(
        "mockllm/model",
        custom_outputs=[ModelOutput.from_content("mockllm/model", "4")] * 5,
        config=GenerateConfig(temperature=0.0, seed=1),
    )
    task = Task(dataset=[Sample(input=str(i), target="4") for i in range(5)], scorer=match())
    logs = inspect_eval(task, model=m, display="none", log_dir=str(tmp_path), limit=2)
    return logs[0].location


def test_limited_run_does_not_false_positive_den001(tmp_path):
    # dataset has 5 samples but the run was limited to 2; DEN001 must NOT warn
    path = _limited_log(tmp_path)
    report = audit_paths([path])
    assert status_of(report, "DEN001") == "NOT_CHECKED"
    # and the limited run is otherwise clean
    assert report.overall.label == "PASS"


def test_custom_string_score_not_flagged_sco002(tmp_path):
    # a categorical string score value is legitimate and must not be flagged
    import copy
    from inspect_ai.log import read_eval_log, write_eval_log
    from inspect_ai.scorer._metric import Score

    path = _limited_log(tmp_path)
    log = read_eval_log(path)
    for s in log.samples:
        s.scores = dict(s.scores or {})
        s.scores["category"] = Score(value="refused", explanation="model refused")
    out = str(tmp_path / "custom.eval")
    write_eval_log(log, out)
    report = audit_paths([out])
    assert status_of(report, "SCO002") == "PASS"
