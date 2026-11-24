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
Seven tasks in a graded ladder. Difficulty 1 tasks are the original toys; any capable model saturates them (see Status). Difficulty 2-4 is where bare vs harness should start to separate.

| task | role | difficulty | what it tests |
|---|---|---|---|
| py-bugfix-1 | patcher | 1 | one-line bug, toy |
| py-bugfix-2 | patcher | 2 | three bugs (sorting, boundary, mutation) in interval merging |
| py-bugfix-3 | patcher | 3 | three interacting bugs in an LRU cache (recency, eviction direction, size accounting) |
| py-bugfix-4 | patcher | 4 | largest-remainder apportionment; exact cent conservation, ties, zero weights |
| py-review-1 | reviewer | 1 | three obvious defects, toy |
| py-review-2 | reviewer | 2 | four classic defects (mutable default, swallowed errors, closure late binding, unjoined threads) |
| py-review-3 | reviewer | 3 | five security defects (SQL injection, pickle RCE, path traversal, shell injection, hardcoded secret) |

Patcher scoring is deterministic: the task's test command passes or fails. Reviewer scoring is recall over the planted defects (`seeded_issues` in each task.json, matched by keyword families). Reference solutions live in `docs/reference_solutions/` and are validated by `python3 docs/selftest_tasks.py`; they are for the mock endpoint and maintainers, not shipped to the model. Add your own tasks as `tasks/<id>/task.json`; restrict a run with `run.tasks` in config.json.

## Run
```
cp config.example.json config.json   # edit endpoints, repeats, rate limits
python3 -m evalkit.runner --dry-run  # shows the plan, sends nothing
python3 -m evalkit.runner --endpoint basalt-5090
python3 -m evalkit.report            # summary, flags n<3 as indicative
python3 -m evalkit.kld_check         # thread KLD claims vs published table
```
Python 3.8+, standard library only. Task format: `tasks/<id>/task.json` (see any of the seven shipped tasks).

## Settings (all in config.json)
Endpoints and models, modes, roles, repeats, temperature, max tokens, reasoning effort, timeout, harness prompt file, compile command, task and result dirs. **Rate limits:** `min_interval_s`, `max_concurrency`, retries with exponential backoff, `Retry-After` honoured. Defaults are one request at a time, one second apart.

## Status
- **Offline self-test (2026-11-24):** all 7 tasks validated - each buggy source fails its test, each reference solution passes, canned mock answers score 1.00; 21-run end-to-end pass through the runner against the mock endpoint. Plumbing only; no model involved. See docs/SELFTEST.md.
- **Live run (2026-11-24, reported by @azjam798276):** 12 runs (3 modes x 2 roles x 2 repeats) against a live Basalt serve endpoint (RTX 5090 + 5060 Ti, 262K context, IQ3_S), on the two original difficulty-1 tasks: **12/12 scored 1.00**. This proves the pipeline works end-to-end against real hardware. It says **nothing** about model quality or about bare vs harness: the tasks were too easy to discriminate. Claims 4 and 5 in docs/CLAIMS.md remain UNVERIFIED until a run on the difficulty 2-4 tasks shows separation.
- **Not yet run:** the difficulty 2-4 task set against any model; any Mac/oMLX endpoint.

## Fixes
- `python`/`python3` in task commands is rewritten to the running interpreter, and an unrunnable test command is recorded as an error instead of a fake 0.0 (rc 127 would silently zero every score). Contributed by @azjam798276 from his fork (commit 934f585, cherry-picked).

## Attribution and licences
- Idea, results and claims: the r/LocalLLM post by its OP and comments by Realistic_Gap_5871, Mil0Mammon, JurandM2, bippityBoppityboux, tomByrer, paramarioh. Quoted only as short facts with links. Their content belongs to them.
- Basalt (https://github.com/jesdga95/basalt, MIT; fork of Strata, MIT). KLD table copied as data from the model card https://huggingface.co/jesdga/Qwen3.8-Flash-Next-Basalt . Model packs: Qwen Community License 1.0 (derived from Qwen3.8-Flash-Next; Unsloth and NVIDIA quants). Not redistributed here.
- Pi (https://github.com/earendil-works/pi, MIT), oMLX (https://github.com/jundot/omlx), ds4 (https://github.com/antirez/ds4, MIT), MTPLX (https://mtplx.com/benchmarks/): referenced, not vendored.
- This repo's code: MIT. Fork-only: no issues, PRs or comments were made on any upstream or on Reddit.
