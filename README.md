# qfn-harness-eval

Evaluation repo built from the r/LocalLLM thread "Qwen 3.8 Flash Next vs Hy4-flash vs Inkling-2-Mini vs Opus and Sonet" (https://www.reddit.com/r/LocalLLM/s/kqivphT83t).

## What this is, and what it is not
The post's benchmark is private (Salesforce-based, no repo). So there is no code to fork. This repo is a **clean-room stand-in** with the same structure, so you can test the thread's claims on your own hardware:

- Two roles: **reviewer** (find issues) and **patcher** (fix a described bug).
- Three modes: **bare** (one request), **harness** (tuned system prompt, feedback loop; stand-in for the Pi harness), **harness_compile** (adds a compile check before accepting).
- An **OpenAI-compatible** client, so it targets Basalt serve (RTX 5090 + 5060 Ti), oMLX (Macs), llama.cpp, vLLM, Proxmox hosts.
- A **claims register** (docs/CLAIMS.md) marking each claim from the post and comments as verified, contradicted or unverified, with links.
- A **KLD check** comparing numbers quoted in comments with Basalt's published table.

## Task set
Eleven tasks in a graded ladder. Difficulty 1 tasks are the original toys; any capable model saturates them (see Status). The v2 ladder (difficulty 2-4) also saturated live on 2026-11-24, so v3 adds genuinely hard tasks (multi-file, regression-sensitive, performance) and precision scoring for the reviewer.

| task | role | difficulty | what it tests |
|---|---|---|---|
| py-bugfix-1 | patcher | 1 | one-line bug, toy |
| py-bugfix-2 | patcher | 2 | three bugs (sorting, boundary, mutation) in interval merging |
| py-bugfix-3 | patcher | 3 | three interacting bugs in an LRU cache (recency, eviction direction, size accounting) |
| py-bugfix-4 | patcher | 4 | largest-remainder apportionment; exact cent conservation, ties, zero weights |
| py-bugfix-5 | patcher | 5 | multi-file money-rounding bug across pricing.py + orders.py (round once, ties away from zero, shipping boundary); graded per test file |
| py-bugfix-6 | patcher | 4 | regression-sensitive: fix cascading month-end clamping without breaking 8 existing recurrence tests (separate test files, graded) |
| py-bugfix-7 | patcher | 4 | performance: quadratic pair counter must become average-linear; element reads are metered, correctness and no-mutation enforced |
| py-review-1 | reviewer | 1 | three obvious defects, toy |
| py-review-2 | reviewer | 2 | four classic defects (mutable default, swallowed errors, closure late binding, unjoined threads) |
| py-review-3 | reviewer | 3 | five security defects (SQL injection, pickle RCE, path traversal, shell injection, hardcoded secret) |
| py-review-4 | reviewer | 4 | clean-code control: there is deliberately nothing to find; every reported finding is a false positive |

### Scoring
**Patcher** scoring is deterministic: run the task's test command(s). A single `test_cmd` scores 1.0/0.0; a `test_cmds` list scores the fraction that pass, so partial credit is possible (fix the bug but break the pre-existing regression tests and py-bugfix-6 pays 0.5). Multi-file tasks (`source_files`) accept one fenced block per changed file, each starting with `# file: <name>`; files not returned are kept as shipped.

**Format repair (v4).** A multi-file patcher reply with no `# file:` headers (or headers naming none of the editable files) applies nothing - a format failure, not a model failure. In the harness modes the runner re-prompts with a format correction, `run.format_repair_retries` times (default 1; 0 = v3 behaviour; bare mode never repairs). Every run logs `repair_used` and `repair_attempts` as their own fields (plus `detail.repair_issues` and `detail.format_ok`), so runs where no repair happened stay directly comparable with v3 results, and the harness's help is separable from the repair loop's help. A bare-mode format failure now scores 0.0 with `format_ok=false` instead of aborting the run with a KeyError.

**Reviewer** scoring is versioned per task (`scoring_version` in task.json):

- **v1** (default for unversioned tasks): recall only - found seeded issues / all seeded issues, matched by keyword families. A review that dumps many keywords scores 1.00 with no penalty.
- **v2** (all shipped reviewer tasks): recall **plus precision**, still deterministic keyword matching. Two penalties: flagging a listed decoy (`must_not_flag` - topics the code demonstrably does not involve), and reporting more findings than `max_findings`. Weights `w_decoy` (default 0.5) and `w_over` (default 0.25). A task with no seeded issues (py-review-4) is a pure false-positive control. The reviewer prompt now also instructs the model to list only confident real defects and to reply "No issues found." when there are none.

Keyword matching is a blunt instrument: a correct review phrased around a decoy keyword can be penalised, and a seeded issue phrased without any keyword can be missed. v2 makes recall-only dumping costly, which is what the ladder needed; it is not a semantic judge.

Reference solutions live in `docs/reference_solutions/` and are validated by `python3 docs/selftest_tasks.py`; they are for the mock endpoint and maintainers, not shipped to the model. Add your own tasks as `tasks/<id>/task.json`; restrict a run with `run.tasks` in config.json.

## Run
```
cp config.example.json config.json   # edit endpoints, repeats, rate limits
python3 -m evalkit.runner --dry-run  # shows the plan, sends nothing
python3 -m evalkit.runner --endpoint basalt-5090
python3 -m evalkit.report            # summary, flags n<3 as indicative
python3 -m evalkit.kld_check         # thread KLD claims vs published table
```
Python 3.8+, standard library only. Task format: `tasks/<id>/task.json` (see any of the eleven shipped tasks).

To run only the new v3 tasks, set in config.json:
```
"run": { ..., "tasks": ["py-bugfix-5", "py-bugfix-6", "py-bugfix-7", "py-review-4"] }
```

## gBench lane (v5)
Google DeepMind's gBench (announced on r/LocalLLaMA 2026-11-24; https://github.com/google-deepmind/gbench, Apache-2.0) complements this repo: a 16-case Golden Set smoke test with chat-template sensitivity twin pairs, 86 academic eval suites, and serving stress/repeatability measurement, all against any OpenAI-compatible endpoint. It is not vendored (pip install gbench; Python 3.11+, heavy deps). This repo adds a thin lane:

```
python3 -m evalkit.gbench_lane plan                      # gbench commands from config.json endpoints
python3 -m evalkit.gbench_lane ingest <gbench-run-dir>   # normalize a run into results/gbench.jsonl
python3 docs/selftest_gbench_lane.py                     # offline self-test (22 checks)
```

Ingest flags judge-fallback scoring, non-leaderboard-comparable results and failed configurations. Why it matters here: the Golden Set's chat-template pairs check the serving side of the v3 live run's patcher format failure, and the "x beats y is templates and samplers" concern, before any task score is quoted. Details and traps: docs/GBENCH.md. Not run against any endpoint yet.

## Settings (all in config.json)
Endpoints and models, modes, roles, repeats, temperature, max tokens, reasoning effort, timeout, harness prompt file, compile command, task and result dirs, `format_repair_retries` (v4). **Rate limits:** `min_interval_s`, `max_concurrency`, retries with exponential backoff, `Retry-After` honoured. Defaults are one request at a time, one second apart.

## Status
- **Offline self-test (2026-11-24, v3):** all 11 tasks validated - every buggy source scores below 1.0, every reference solution scores 1.0, the multi-file task pays partial credit for a one-file fix, precise canned reviews score 1.00 and noisy/decoy-flagging reviews score strictly less; 33-run end-to-end pass through the runner against the mock endpoint. Plumbing only; no model involved. See docs/SELFTEST.md.
- **Live run (2026-11-24, reported by @azjam798276):** 12 runs (3 modes x 2 roles x 2 repeats) against a live Basalt serve endpoint (RTX 5090 + 5060 Ti, 262K context, IQ3_S), on the two original difficulty-1 tasks: **12/12 scored 1.00**. Proved the pipeline works end-to-end against real hardware; tasks too easy to discriminate.
- **Live run (2026-11-24, v2 ladder, reported by @azjam798276):** **21/21 runs scored 1.00** (7 tasks x 3 modes) across bare/harness/harness_compile, including the difficulty-3 security review. The v2 ladder still cannot separate modes. The run also confirmed reviewer scoring was recall-only: a review dumping many keywords scored 1.00 with no penalty. Both gaps are what v3 (this commit) targets.
- **Live run (2026-11-24, v3 tasks, reported by @azjam798276):** first live pass over the hard tasks showed the harness at +0.08 on py-review-4 and 0.00 on py-bugfix-5 (n=1) - the patcher reply came back as one fenced block instead of two `# file:` blocks, so nothing was applied: a format failure the runner could not repair. That gap is what v4 (format-repair retry) targets.
- **Not yet run:** the v4 runner (format repair on) against any model; any Mac/oMLX endpoint; the v5 gBench lane (no gbench command has been run against any endpoint). Claims 4 and 5 in docs/CLAIMS.md remain UNVERIFIED until a run shows separation. When comparing with v3 runs, use rows with `repair_used=false`.

## Fixes
- `python`/`python3` in task commands is rewritten to the running interpreter, and an unrunnable test command is recorded as an error instead of a fake 0.0 (rc 127 would silently zero every score). Contributed by @azjam798276 from his fork (commit 934f585, cherry-picked).

## Attribution and licences
- Idea, results and claims: the r/LocalLLM post by its OP and comments by Realistic_Gap_5871, Mil0Mammon, JurandM2, bippityBoppityboux, tomByrer, paramarioh. Quoted only as short facts with links. Their content belongs to them.
- Basalt (https://github.com/jesdga95/basalt, MIT; fork of Strata, MIT). KLD table copied as data from the model card https://huggingface.co/jesdga/Qwen3.8-Flash-Next-Basalt . Model packs: Qwen Community License 1.0 (derived from Qwen3.8-Flash-Next; Unsloth and NVIDIA quants). Not redistributed here.
- Pi (https://github.com/earendil-works/pi, MIT), oMLX (https://github.com/jundot/omlx), ds4 (https://github.com/antirez/ds4, MIT), MTPLX (https://mtplx.com/benchmarks/): referenced, not vendored.
- gBench (https://github.com/google-deepmind/gbench, Apache-2.0): referenced, not vendored. gBench-thread commenters quoted as short facts: Izento, Hrethric, Kolkoris, readreaddrawdraw, YogurtExternal7923, No-Library8065, Milk_Bots. Their content belongs to them.
- This repo's code: MIT. Fork-only: no issues, PRs or comments were made on any upstream or on Reddit.
