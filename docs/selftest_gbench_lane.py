"""Offline self-test for evalkit.gbench_lane. No model, no network, no gbench install.

Builds a fixture config and a fixture gBench run directory in a temp dir, then checks:
- plan builds the expected commands from config.json endpoints
- ingest normalizes summary.json + metadata.json into one JSONL row
- judge-fallback scoring and a failed configuration surface as warnings
- a directory without summary.json exits cleanly with an error
"""
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_lane(argv, cwd):
    return subprocess.run(
        [sys.executable, "-m", "evalkit.gbench_lane"] + argv,
        cwd=cwd, capture_output=True, text=True)


def main():
    checks = []
    with tempfile.TemporaryDirectory() as tmp:
        # fixture config
        cfg = {"endpoints": {"test-endpoint": {
                   "base_url": "http://gpu-box:8080/v1",
                   "model": "TestModel-Q4", "api_key_env": "", "note": "fixture"}},
               "results_dir": os.path.join(tmp, "results")}
        with open(os.path.join(tmp, "config.json"), "w") as f:
            json.dump(cfg, f)

        # plan
        r = run_lane(["plan", "--config", os.path.join(tmp, "config.json")], cwd=REPO)
        out = r.stdout
        checks.append(("plan exit 0", r.returncode == 0))
        checks.append(("plan golden cmd", "gbench --golden-only --remote-endpoint "
                       "http://gpu-box:8080/v1 --tokenizer TestModel-Q4" in out))
        checks.append(("plan served id", "--served-model-id TestModel-Q4" in out))
        checks.append(("plan evals cmd", "--evals gpqa mmlu --eval-thinking" in out))
        checks.append(("plan stress cmd", "gbench --stress-test" in out))
        checks.append(("plan results dir", os.path.join(tmp, "results", "gbench",
                       "test-endpoint") in out))
        r2 = run_lane(["plan", "--config", os.path.join(tmp, "config.json"),
                       "--no-thinking", "--evals", "gpqa"], cwd=REPO)
        checks.append(("plan custom evals, no thinking",
                       "--evals gpqa" in r2.stdout and "--eval-thinking" not in r2.stdout
                       and "mmlu" not in r2.stdout))
        r3 = run_lane(["plan", "--config", os.path.join(tmp, "config.json"),
                       "--endpoint", "nope"], cwd=REPO)
        checks.append(("plan bad endpoint fails", r3.returncode != 0))

        # fixture gBench run dir
        run_dir = os.path.join(tmp, "gbench-run")
        os.makedirs(run_dir)
        with open(os.path.join(run_dir, "metadata.json"), "w") as f:
            json.dump({"gbench": "deadbeef", "served_model_id": "TestModel-Q4"}, f)
        summary = {
            "timestamp": "11-24-120000",
            "total_configurations": 3, "successful_configurations": 2,
            "failed_configurations": 1,
            "models": [
                {"benchmark_type": "golden", "model": "TestModel-Q4",
                 "status": "failed", "total_tasks": 16, "applicable_tasks": 15,
                 "passed_cases": 13, "failed_cases": 2, "error_cases": 0,
                 "accuracy_percent": 86.67, "subject_id": "subj1",
                 "scaffold_id": "scaf1"},
                {"benchmark_type": "eval", "eval_name": "gpqa",
                 "model_short": "TestModel-Q4", "status": "success",
                 "accuracy": 0.42, "total_questions": 100, "correct_answers": 42,
                 "scoring_mode": "judge_fallback", "judge_outages": 3,
                 "leaderboard_comparable": False,
                 "subject_id": "subj1", "scaffold_id": "scaf1"},
            ],
            "failures": [{"benchmark_type": "eval", "eval_name": "mmlu",
                          "error": "endpoint unreachable"}],
        }
        with open(os.path.join(run_dir, "summary.json"), "w") as f:
            json.dump(summary, f)

        out_jsonl = os.path.join(tmp, "results", "gbench.jsonl")
        r = run_lane(["ingest", run_dir, "--config", os.path.join(tmp, "config.json"),
                      "--endpoint", "test-endpoint"], cwd=REPO)
        checks.append(("ingest exit 0", r.returncode == 0))
        checks.append(("ingest wrote jsonl", os.path.exists(out_jsonl)))
        if os.path.exists(out_jsonl):
            row = json.loads(open(out_jsonl).read().strip())
            checks.append(("row lane", row["lane"] == "gbench"))
            checks.append(("row endpoint", row["endpoint"] == "test-endpoint"))
            checks.append(("row commit", row["gbench_commit"] == "deadbeef"))
            checks.append(("row ids", row["subject_id"] == "subj1"
                           and row["scaffold_id"] == "scaf1"))
            checks.append(("row golden", row["golden"][0]["passed_cases"] == 13
                           and row["golden"][0]["status"] == "failed"))
            checks.append(("row eval", row["evals"][0]["eval_name"] == "gpqa"
                           and row["evals"][0]["accuracy"] == 0.42))
            w = " | ".join(row["warnings"])
            checks.append(("warn judge_fallback", "judge" in w and "gpqa" in w))
            checks.append(("warn golden fail", "golden: status=failed" in w))
            checks.append(("warn failure", "mmlu" in w))
            checks.append(("warn leaderboard", "not leaderboard-comparable" in w))
        # second ingest appends
        run_lane(["ingest", run_dir, "--config", os.path.join(tmp, "config.json")], cwd=REPO)
        if os.path.exists(out_jsonl):
            checks.append(("append, not overwrite",
                           len(open(out_jsonl).read().strip().splitlines()) == 2))

        # missing summary.json
        r = run_lane(["ingest", tmp, "--config", os.path.join(tmp, "config.json")], cwd=REPO)
        checks.append(("no summary.json -> clean error",
                       r.returncode != 0 and "summary.json" in (r.stderr + r.stdout)))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print("%s %s" % ("PASS" if ok else "FAIL", name))
    if failed:
        print("\n%d check(s) failed" % len(failed))
        sys.exit(1)
    print("\nAll %d gbench-lane self-test checks passed." % len(checks))


if __name__ == "__main__":
    main()
