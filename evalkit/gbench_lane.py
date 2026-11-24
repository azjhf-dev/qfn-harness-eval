"""gBench lane: plan gBench runs against this repo's endpoints and ingest gBench results.

gBench (https://github.com/google-deepmind/gbench, Apache-2.0) is NOT vendored here.
Install it yourself (Python 3.11+): pip install "gbench[evals]" transformers
See docs/GBENCH.md for what it adds and its limits.

Subcommands:
  plan    Print ready-to-run gbench commands built from config.json endpoints.
  ingest  Normalize one gBench run directory (summary.json + metadata.json) into
          results/gbench.jsonl, flagging judge-fallback scoring and pillar failures.

Stdlib only, Python 3.8+.
"""
import argparse
import datetime
import json
import os
import sys

STARTER_EVALS = ["gpqa", "mmlu"]


def _load_config(path):
    if not os.path.exists(path):
        sys.exit("config not found: %s (cp config.example.json config.json)" % path)
    with open(path) as f:
        return json.load(f)


def _endpoint(cfg, name):
    eps = cfg.get("endpoints") or {}
    if not eps:
        sys.exit("config has no endpoints")
    if name:
        if name not in eps:
            sys.exit("unknown endpoint %r; configured: %s" % (name, ", ".join(sorted(eps))))
        return name, eps[name]
    name = sorted(eps)[0]
    return name, eps[name]


def cmd_plan(args):
    cfg = _load_config(args.config)
    name, ep = _endpoint(cfg, args.endpoint)
    base = ep["base_url"].rstrip("/")
    model = ep["model"]
    results_dir = os.path.join(cfg.get("results_dir", "results"), "gbench", name)
    evals = args.evals.split(",") if args.evals else STARTER_EVALS

    common = ["--remote-endpoint", base, "--tokenizer", model,
              "--served-model-id", model, "--results-dir", results_dir]
    golden = ["gbench", "--golden-only"] + common
    eval_cmd = (["gbench", "--evals-only"] + common +
                ["--evals"] + evals +
                (["--eval-thinking", "--max-output-tokens", "65536"] if args.thinking else []))
    stress = ["gbench", "--stress-test"] + common

    print("# gBench plan for endpoint %r (%s, model %s)" % (name, base, model))
    print("# Install first (Python 3.11+): pip install \"gbench[evals]\" transformers")
    print("# gBench is not vendored in this repo. Read docs/GBENCH.md before quoting scores:")
    print("# dataset licenses (gbench docs/THIRD_PARTY_DATASETS.md) govern published scores.")
    print()
    print("# 1. Golden Set smoke test (16 deterministic cases; the 4 chat_template cases")
    print("#    separate a broken chat template from a weak model):")
    print(" ".join(golden))
    print()
    print("# 2. Academic evals (starter set %s; widen with --evals):" % ",".join(evals))
    print(" ".join(eval_cmd))
    print()
    print("# 3. Serving stress sweep (open-loop Poisson; needs a quiet box):")
    print(" ".join(stress))
    print()
    print("# Then: python3 -m evalkit.gbench_lane ingest %s/<timestamp> --endpoint %s"
          % (results_dir, name))
    print("# Tip: add --dry-run to any gbench command to validate the plan without sending.")


def _read_json(path):
    with open(path) as f:
        return json.load(f)


def _first(records, key):
    for r in records:
        v = r.get(key)
        if v:
            return v
    return None


def cmd_ingest(args):
    run_dir = args.run_dir
    summary_path = os.path.join(run_dir, "summary.json")
    if not os.path.exists(summary_path):
        sys.exit("no summary.json in %s - is this a finished gBench run directory?" % run_dir)
    summary = _read_json(summary_path)
    meta_path = os.path.join(run_dir, "metadata.json")
    meta = _read_json(meta_path) if os.path.exists(meta_path) else {}

    models = summary.get("models") or []
    failures = summary.get("failures") or []

    golden, evals, other = [], [], []
    warnings = []
    for r in models:
        btype = r.get("benchmark_type")
        if btype == "golden" or "passed_cases" in r:
            g = {"status": r.get("status"),
                 "passed_cases": r.get("passed_cases"),
                 "applicable_tasks": r.get("applicable_tasks"),
                 "failed_cases": r.get("failed_cases"),
                 "error_cases": r.get("error_cases"),
                 "accuracy_percent": r.get("accuracy_percent")}
            golden.append(g)
            if r.get("error_cases"):
                warnings.append("golden: %d case(s) errored - harness error, no verdict"
                                % r["error_cases"])
            elif r.get("status") and r.get("status") != "passed":
                warnings.append("golden: status=%s (%s/%s applicable cases passed)"
                                % (r["status"], r.get("passed_cases"),
                                   r.get("applicable_tasks")))
        elif btype == "eval" or r.get("eval_name"):
            e = {"eval_name": r.get("eval_name"),
                 "status": r.get("status"),
                 "accuracy": r.get("accuracy"),
                 "total_questions": r.get("total_questions"),
                 "correct_answers": r.get("correct_answers"),
                 "scoring_mode": r.get("scoring_mode"),
                 "judge_outages": r.get("judge_outages"),
                 "leaderboard_comparable": r.get("leaderboard_comparable")}
            evals.append(e)
            if r.get("scoring_mode") == "judge_fallback":
                warnings.append(
                    "%s: scored by the no-judge substring fallback - a lower bound, "
                    "not the canonical metric (judge outage?)" % r.get("eval_name"))
            if r.get("leaderboard_comparable") is False:
                warnings.append("%s: not leaderboard-comparable (see its "
                                "leaderboard_comparable_reason in the eval_*.json)"
                                % r.get("eval_name"))
        else:
            other.append({"benchmark_type": btype, "status": r.get("status"),
                          "name": r.get("name") or r.get("model_short")})
    for r in failures:
        warnings.append("failed configuration: %s %s - %s"
                        % (r.get("benchmark_type", "?"),
                           r.get("eval_name") or r.get("model_short") or "",
                           str(r.get("error"))[:200]))

    row = {
        "lane": "gbench",
        "ingested_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "endpoint": args.endpoint or "",
        "model": args.model or _first(models, "model") or "",
        "source_dir": os.path.abspath(run_dir),
        "gbench_timestamp": summary.get("timestamp"),
        "gbench_commit": meta.get("gbench"),
        "served_model_id": meta.get("served_model_id") or _first(models, "served_model_id"),
        "subject_id": _first(models, "subject_id"),
        "scaffold_id": _first(models, "scaffold_id"),
        "golden": golden,
        "evals": evals,
        "other": other,
        "failures": [{"benchmark_type": r.get("benchmark_type"),
                      "name": r.get("eval_name") or r.get("model_short"),
                      "error": str(r.get("error"))[:500]} for r in failures],
        "warnings": warnings,
    }

    out_path = args.out or os.path.join(
        _load_config(args.config).get("results_dir", "results")
        if os.path.exists(args.config) else "results", "gbench.jsonl")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "a") as f:
        f.write(json.dumps(row) + "\n")

    print("ingested %s -> %s" % (run_dir, out_path))
    for g in golden:
        print("  golden: %s (%s/%s applicable passed)" % (
            g["status"], g["passed_cases"], g["applicable_tasks"]))
    for e in evals:
        print("  eval %s: accuracy=%s scoring=%s" % (
            e["eval_name"], e["accuracy"], e["scoring_mode"]))
    for w in warnings:
        print("  WARNING: %s" % w)


def main(argv=None):
    p = argparse.ArgumentParser(prog="evalkit.gbench_lane", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("plan", help="print gbench commands for a config.json endpoint")
    pp.add_argument("--config", default="config.json")
    pp.add_argument("--endpoint", default="", help="endpoint name (default: first)")
    pp.add_argument("--evals", default="", help="comma-separated suite names")
    pp.add_argument("--no-thinking", dest="thinking", action="store_false",
                    help="omit --eval-thinking from the evals command")
    pp.set_defaults(func=cmd_plan)

    pi = sub.add_parser("ingest", help="normalize a gBench run dir into results/gbench.jsonl")
    pi.add_argument("run_dir")
    pi.add_argument("--config", default="config.json")
    pi.add_argument("--endpoint", default="")
    pi.add_argument("--model", default="")
    pi.add_argument("--out", default="", help="output JSONL path (default: <results_dir>/gbench.jsonl)")
    pi.set_defaults(func=cmd_ingest)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
