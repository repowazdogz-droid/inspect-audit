"""Generate the fixture corpus.

Builds one genuinely clean Inspect log with mock models, then derives one
precise-defect variant per fixture by mutating a freshly-read copy and writing
it to fixtures/corpus/. Fixtures are real .eval files produced by inspect_ai's
own writer, so they exercise the real schema.

Run:  python fixtures/build_fixtures.py
"""

from __future__ import annotations

import copy
import math
import os
import shutil
import warnings

warnings.filterwarnings("ignore")

from inspect_ai import Task, eval as inspect_eval
from inspect_ai.dataset import Sample
from inspect_ai.model import GenerateConfig, ModelOutput, get_model
from inspect_ai.scorer import match
from inspect_ai.scorer._metric import Score
from inspect_ai.log import read_eval_log, write_eval_log
from inspect_ai.log._log import EvalScore
from inspect_ai._util.error import EvalError

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "corpus")


def _clean_model():
    # deterministic mock: each sample's completion equals its target
    outputs = [
        ModelOutput.from_content("mockllm/model", "4"),
        ModelOutput.from_content("mockllm/model", "Paris"),
        ModelOutput.from_content("mockllm/model", "7"),
    ]
    return get_model(
        "mockllm/model",
        custom_outputs=outputs,
        config=GenerateConfig(temperature=0.0, seed=42),
    )


def build_clean(path: str) -> str:
    task = Task(
        dataset=[
            Sample(input="2+2?", target="4"),
            Sample(input="capital of France?", target="Paris"),
            Sample(input="3+4?", target="7"),
        ],
        scorer=match(),
    )
    tmp = os.path.join(HERE, "_tmp_clean")
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    logs = inspect_eval(task, model=_clean_model(), display="none", log_dir=tmp)
    src = logs[0].location
    shutil.copyfile(src, path)
    shutil.rmtree(tmp)
    return path


def _write(log, path):
    write_eval_log(log, path)


def mutate_dropped_errors(clean_path, out):
    log = read_eval_log(clean_path)
    s0 = log.samples[0]
    s0.error = EvalError(message="RuntimeError: boom", traceback="Traceback...\nRuntimeError: boom", traceback_ansi="boom")
    s0.scores = {}  # errored sample went unscored
    log.results.completed_samples -= 1
    sc = log.results.scores[0]
    sc.scored_samples = (sc.scored_samples or log.results.total_samples) - 1
    sc.unscored_samples = (sc.unscored_samples or 0) + 1
    _write(log, out)


def mutate_parse_failure(clean_path, out):
    log = read_eval_log(clean_path)
    total = log.results.total_samples
    # add an independent-judge model-graded score whose grader returned no grade
    mg = copy.deepcopy(log.results.scores[0])
    mg.name = "model_graded_qa"
    mg.scorer = "model_graded_qa"
    mg.params = {"model": "mockllm/grader"}  # independent judge -> isolates from JUD002
    mg.scored_samples = 0
    mg.unscored_samples = total
    log.results.scores.append(mg)
    for s in log.samples:
        s.scores = dict(s.scores or {})
        s.scores["model_graded_qa"] = Score(
            value=math.nan,
            explanation="Grade not found in model output: Default output",
        )
    _write(log, out)


def mutate_missing_judge_meta(clean_path, out):
    log = read_eval_log(clean_path)
    mg = copy.deepcopy(log.results.scores[0])
    mg.name = "model_graded_qa"   # name marks it model-graded...
    mg.scorer = "model_graded_qa"
    mg.params = {}                # ...but no judge model recorded
    log.results.scores.append(mg)
    # a real model-graded log also carries a scorer spec (options without model)
    if log.eval.scorers:
        spec = copy.deepcopy(log.eval.scorers[0])
        spec.name = "model_graded_qa"
        spec.options = {}
        log.eval.scorers.append(spec)
    for s in log.samples:
        s.scores = dict(s.scores or {})
        s.scores["model_graded_qa"] = Score(value="C", explanation="looks correct")
    _write(log, out)


def mutate_self_judging(clean_path, out):
    log = read_eval_log(clean_path)
    mg = copy.deepcopy(log.results.scores[0])
    mg.name = "model_graded_qa"
    mg.scorer = "model_graded_qa"
    mg.params = {"model": log.eval.model}  # judge == generator
    log.results.scores.append(mg)
    if log.eval.scorers:
        spec = copy.deepcopy(log.eval.scorers[0])
        spec.name = "model_graded_qa"
        spec.options = {"model": log.eval.model}
        log.eval.scorers.append(spec)
    for s in log.samples:
        s.scores = dict(s.scores or {})
        s.scores["model_graded_qa"] = Score(value="C", explanation="looks correct")
    _write(log, out)


def mutate_duplicate_ids(clean_path, out):
    log = read_eval_log(clean_path)
    dup = copy.deepcopy(log.samples[0])  # same id + epoch
    log.samples.append(dup)
    # keep counts internally consistent so ONLY RUN003 fires
    log.results.total_samples += 1
    log.results.completed_samples += 1
    sc = log.results.scores[0]
    sc.scored_samples = (sc.scored_samples or 0) + 1
    _write(log, out)


def mutate_regime_unpinned(clean_path, out):
    log = read_eval_log(clean_path)
    log.eval.model = "openai/o3-mini"
    log.eval.model_generate_config = GenerateConfig()  # empty -> provider defaults
    _write(log, out)


def mutate_config_variant_b(clean_path, out):
    # comparison partner for cross-run: different temperature, no seed
    log = read_eval_log(clean_path)
    log.eval.model_generate_config = GenerateConfig(temperature=0.7)
    _write(log, out)


def make_truncated(clean_path, out):
    with open(clean_path, "rb") as f:
        data = f.read()
    with open(out, "wb") as f:
        f.write(data[: len(data) // 2])  # chop -> invalid zip


def main():
    if os.path.isdir(CORPUS):
        shutil.rmtree(CORPUS)
    os.makedirs(CORPUS)
    clean = os.path.join(CORPUS, "clean.eval")
    build_clean(clean)
    mutate_dropped_errors(clean, os.path.join(CORPUS, "silent_dropped_errors.eval"))
    mutate_parse_failure(clean, os.path.join(CORPUS, "scorer_parse_failure.eval"))
    mutate_missing_judge_meta(clean, os.path.join(CORPUS, "missing_judge_metadata.eval"))
    mutate_self_judging(clean, os.path.join(CORPUS, "self_judging.eval"))
    mutate_duplicate_ids(clean, os.path.join(CORPUS, "duplicate_sample_ids.eval"))
    mutate_regime_unpinned(clean, os.path.join(CORPUS, "regime_unpinned.eval"))
    mutate_config_variant_b(clean, os.path.join(CORPUS, "config_variant_b.eval"))
    make_truncated(clean, os.path.join(CORPUS, "truncated_log.eval"))
    print("fixtures written to", CORPUS)
    for f in sorted(os.listdir(CORPUS)):
        print("  ", f, os.path.getsize(os.path.join(CORPUS, f)), "bytes")


if __name__ == "__main__":
    main()
