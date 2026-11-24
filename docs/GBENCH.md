# gBench lane

What Google DeepMind's gBench adds to this repo, and how to run it against the same endpoints.

Source thread: r/LocalLLaMA, 2026-11-24, u/jacek2023 posting googlegemma's announcement
(https://www.reddit.com/r/LocalLLaMA/comments/1y3wyk6/github_googledeepmindgbench_evaluation_serving/).
Upstream: https://github.com/google-deepmind/gbench (Apache-2.0, created 2026-10-30;
checked at commit d3e4283, PyPI gbench 0.5.0.post1). Claims register: docs/CLAIMS.md,
section "gBench thread".

## What it is

An open-source benchmark and evaluation harness for open LLMs/VLMs, two halves:

- **Capability**, three tiers:
  1. `--evals`: 86 academic/domain suites in `--evals all` across 6 pillars, reasoning mode
     on request (`--eval-thinking`), custom JSONL datasets.
  2. `--golden-only`: the 16-case Golden Set smoke test - deterministic checks
     (`code_canonical`, `function_call_single`, `structured_json`, ...) with two-sided
     presence assertions and `python_exec` unit-test matching.
  3. `--quality-only`: the GemmaClaw agentic QA suite in Docker (multi-turn tool calling,
     session memory, plugin routing).
- **Serving performance**: workload campaigns, repeatability stats (mean/median/stdev,
  P50/P95/P99, coefficient of variation gated by `--max-cv-percent`), and an open-loop
  Poisson stress sweep (`--stress-test`) that brackets the failing rate and then certifies
  the limit with ~1400-request probes against P99 TTFT/ITL SLOs.

It talks to any OpenAI-compatible `/v1` server through `--remote-endpoint` (README says
validated on vLLM and Ollama) or starts a local vLLM server itself. Not vendored here:
`pip install "gbench[evals]" transformers`, Python 3.11+, heavy dependencies.

## What it adds to this repo

This repo tests harness behaviour (bare vs harness vs harness_compile) on private coding
tasks. gBench is complementary, not a replacement:

- **Golden Set chat-template sensitivity pairs.** Four `chat_template` cases each have a
  twin that asks the same thing in one plain user turn; read together they separate a
  broken chat template from a weak model (fail/pass = template; fail/fail = model). This
  is the missing check for two open questions here: the v3 live run's patcher format
  failure (v4 repairs the prompt side; the Golden Set checks the serving side), and the
  thread comment that half the "x beats y" posts are really chat template and sampler
  settings (No-Library8065). Run it once per endpoint before trusting any task score.
- **Deterministic two-sided scoring.** Cases require expected tokens AND the absence of
  forbidden ones (including the served model's own chat-template tokens, read from its
  tokenizer at run time). Same philosophy as this repo's deterministic patcher/reviewer
  scoring - no LLM judge on the smoke tier.
- **Comparability bookkeeping.** Every result carries `subject_id` (the model's observable
  identity) and `scaffold_id` (everything pinned about how it was asked), plus a
  `leaderboard_comparable` flag with reasons. This repo's results have no equivalent;
  gBench numbers ingested here keep those ids.
- **Serving numbers.** The stress sweep and repeatability stats give TTFT/ITL/throughput
  under load, which this repo does not measure at all (its report derives only tok/s).

## Run

```
python3 -m evalkit.gbench_lane plan                 # commands built from config.json
python3 -m evalkit.gbench_lane plan --endpoint omlx-mac --evals gpqa,mmlu --no-thinking
```

Then run the printed commands (gbench must be installed on a machine that can reach the
endpoint), and normalize the run into this repo's results:

```
python3 -m evalkit.gbench_lane ingest results/gbench/basalt-5090/<timestamp> --endpoint basalt-5090
```

Ingest appends one JSON object per gBench run to `results/gbench.jsonl`: golden pass/fail
counts, per-suite accuracy with `scoring_mode`, subject/scaffold ids, the gBench commit,
failures, and warnings. It flags the cases that change how a number may be quoted:
`scoring_mode = judge_fallback` (see below), `leaderboard_comparable = false`, errored
Golden Set cases and failed configurations.

## Limits and traps

- **Judge fallback.** Suites whose canonical metric is an LLM judge (a Gemini cascade)
  fall back to substring matching when the judge is unreachable. At the checked commit
  (d3e4283) this is recorded, not silent: the run's `scoring_mode` becomes
  `judge_fallback`, `judge_failures`/`judge_outages` are on the result, and a warning is
  logged - but the run does not fail, and the number is a lower bound, not the metric.
  A thread commenter (readreaddrawdraw) called this out as easy to miss; check
  `scoring_mode` before quoting any judged suite. Pure offline runs are unaffected only
  if the judge was configured to begin with.
- **Benchmaxxing.** Half the thread (Izento, Hrethric vs Kolkoris) debates whether a
  popular public benchmark just becomes a target for model-makers. The working position
  this repo takes: gBench for standardized, comparable numbers; this repo's private task
  ladder for "job interview" numbers on your own work. Neither replaces the other.
- **Dataset licenses.** gBench docs/THIRD_PARTY_DATASETS.md: each suite's dataset license
  (some gated, some non-commercial) governs your use of it and of scores computed on it.
  Read it before publishing any numbers.
- **Tool-call parsers.** Golden Set tool cases depend on the serving stack's tool-call
  and reasoning parsers (README quick start passes `--tool-call-parser`/`--reasoning-parser`
  for local vLLM). For a remote Basalt serve endpoint the parser is the server's; a tool
  case failure there is a serving-stack finding, not necessarily a model finding.
- **Not run here yet.** No gBench command has been run against any endpoint in this
  repo's results. Everything above is from the upstream repo and docs, verified at the
  commit named at the top.
