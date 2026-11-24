# Claims register

Status: **VERIFIED** (primary source read, 2026-11-24), **CONTRADICTED**, **PARTIAL**, **UNVERIFIED** (no primary evidence found; only the Reddit comment or post says it), **NOT RUN** (needs hardware; no run yet).

"Verified" below means a published primary source says so, not that we reproduced it.

## Live runs

| date | endpoint | tasks | result | reading |
|---|---|---|---|---|
| 2026-11-24 | Basalt serve, RTX 5090 + 5060 Ti, 262K ctx, IQ3_S (reported by @azjam798276) | the two original difficulty-1 toys | 12/12 runs scored 1.00 (3 modes x 2 roles x 2 repeats) | pipeline works against real hardware; tasks too easy, so no bare/harness separation and nothing about model quality |
| 2026-11-24 | same endpoint (reported by @azjam798276) | full v2 ladder (7 tasks) | 21/21 runs scored 1.00 (7 tasks x 3 modes), incl. the difficulty-3 security review | v2 ladder still saturated: no bare/harness separation, nothing about model quality. Also confirmed the reviewer score was recall-only - a keyword-dump review scored 1.00 with no penalty. v3 (same day) adds precision scoring and difficulty 4-5 tasks; no discriminating run yet |

The first run also caught a portability bug: task commands said `python`, but the box ships only `python3`, so every test exited 127 and scored 0.0 until fixed (commit 934f585, cherry-picked). A first run scoring 0/0 on this repo was the bug, not the model.

## From the post (OP, r/LocalLLM)

| # | Claim | Status | Evidence |
|---|---|---|---|
| 1 | Benchmark is OP's own, based on Salesforce work, two roles (architect/reviewer, developer/patcher) | VERIFIED as description; the benchmark itself is NOT public | Post text; commenter confirms "personal benchmark". No repo or dataset linked. |
| 2 | Tested Hy4-flash-oQ4h-mtp and Inkling-2-Mini-oQ8e on oMLX 0.8.3, M5 Max 128 GB | PARTIAL | oMLX v0.8.3 exists, published 2026-11-22, adds Inkling 2 Mini and Hy4 optimisations: https://github.com/jundot/omlx/releases/tag/v0.8.3 . OP's run results are not published. |
| 3 | Hy4-flash fixed more tasks than QFN; QFN finds more issues; Inkling 2 Mini 1h40 vs 20 min | UNVERIFIED | Only in the chart/table the post refers to. We have only the text. Single runs, per OP. |
| 4 | Qwen 3.8 Flash Next beats Opus 4.6 and Sonnet 5, even bare | UNVERIFIED | One person's private benchmark, single runs for the new models. Our 2026-11-24 run tested QFN only and saturated the toy tasks; no Opus/Sonnet endpoint has been run. |
| 5 | Harness matters a lot (Pi with tuned prompt, plus compile-before-save) | UNVERIFIED here, testable | This repo's three modes test it. The 2026-11-24 live runs could not discriminate: bare, harness and harness_compile all scored 1.00, first on the difficulty-1 toys (12/12) and then on the full v2 ladder (21/21). The v3 set added 2026-11-24 (precision-scored reviewer, multi-file/regression/performance patcher tasks at difficulty 4-5) exists to answer this; no discriminating run yet. Pi: https://github.com/earendil-works/pi (MIT). |
| 6 | DS4 (antirez) most stable with oMLX; MTPLX and MLX Server a bit worse | UNVERIFIED | ds4 exists: https://github.com/antirez/ds4 (MIT). Stability claim has no source. MTPLX publishes speed, not stability: https://mtplx.com/benchmarks/ |
| 7 | UD-Q4_K_XL / UD-Q5_K_XL are best speed/quality | PARTIAL | Basalt's table shows Q5_K_XL KLD 0.0255 vs Q4_K_XL 0.0496. Speed side not in that table. |

## From comments

| # | Who | Claim | Status | Evidence |
|---|---|---|---|---|
| 8 | Realistic_Gap_5871 | On a 5090 with 96 GB+ DDR5, NVFP4 runs QFN at 140-220 tok/s, 200+ for coding | UNVERIFIED | Basalt's own post reports different numbers on a 5090 + 5060 Ti: https://www.reddit.com/r/LocalLLaMA/comments/1x223ai/basalt_flashnext_at_665_toks_structured_354_prose/ . Not the same rig; run `basalt-bench` to settle. |
| 9 | Realistic_Gap_5871 | KLD/top-1: oQ5e 0.0625/92.40, Basalt nvfp4 0.0680/91.46, Unsloth IQ3 0.1650/85.40 | DIFFERS from primary | Basalt's published table: NVFP4-DQ6_K 0.0624/91.65, NVFP4-DQ8 0.0561/92.25, UD-IQ3_XXS 0.1188/88.67. See `python -m evalkit.kld_check`. Commenter did not say which pack or dataset, so a different method is possible. oQ5e has no published row. |
| 10 | Realistic_Gap_5871 | UD-Q4_K_XL KLD 0.047, top-1 92.3% | CLOSE, not exact | Published 0.0496 / 92.63% https://huggingface.co/jesdga/Qwen3.8-Flash-Next-Basalt |
| 11 | Realistic_Gap_5871 | Own AWQ g32 quant at KLD 0.0207, top-1 97.06% | UNVERIFIED | No artifact or log shared. |
| 12 | Realistic_Gap_5871 | QFN beats Opus 4.6 at coding, maybe equals 4.8, worse at architecting | UNVERIFIED | Opinion from personal use. |
| 13 | Mil0Mammon | A good IQ3 probably beats NVFP4 on fidelity | CONTRADICTED by the table | IQ3_XXS KLD 0.1188 vs NVFP4-DQ6_K 0.0624 (Basalt table). |
| 14 | Mil0Mammon | KLD/top-1 matter less than task performance; concerns about NVFP4 on tasks | Reasonable; UNVERIFIED | This repo exists to measure task performance. |
| 15 | bippityBoppityboux | Inkling thinking at 0.1 effort may help; default overthinks | UNVERIFIED, testable | Set `run.reasoning_effort` in config. oMLX 0.8.3 notes mention Inkling 2 reasoning_effort handling. |
| 16 | tomByrer | Asked how much VRAM; likely unified memory | OP unanswered in the capture | M5 Max 128 GB is unified. |
| 17 | paramarioh | Wants Flash with Basalt | Request only | Basalt: https://github.com/jesdga95/basalt (MIT), packs https://huggingface.co/jesdga/Qwen3.8-Flash-Next-Basalt |

## gBench thread (r/LocalLLaMA, 2026-11-24)

Thread: u/jacek2023 posting googlegemma's gBench announcement
(https://www.reddit.com/r/LocalLLaMA/comments/1y3wyk6/github_googledeepmindgbench_evaluation_serving/,
score 65, 9 comments at capture; 8 captured - one stayed collapsed). What it adds here: docs/GBENCH.md.

| # | Who | Claim | Status | Evidence |
|---|---|---|---|---|
| G1 | OP (googlegemma announcement) | gBench is open source: capability (86 academic suites, 16-case Golden Set, GemmaClaw agentic suite) plus serving performance and stress, against any OpenAI-compatible /v1 endpoint via --remote-endpoint, validated on vLLM and Ollama | VERIFIED as published; NOT RUN here | Repo exists, Apache-2.0, created 2026-10-30: https://github.com/google-deepmind/gbench ; PyPI gbench 0.5.0.post1. README matches the post. "Validated on vLLM and Ollama" is the README's own wording; no run here yet. Checked at commit d3e4283. |
| G2 | OP | Golden Set: two-sided presence matching, python_exec unit tests, and 4 chat-template cases with plain-turn twins that separate a broken chat template from a weak model | VERIFIED in source, with one limit | docs/golden-set.md and gbench/runners/golden.py at d3e4283. Its own docs state the twin isolation is a structural argument, never measured against a deliberately corrupted template on real weights. |
| G3 | OP | Stress sweep certifies a rate limit to +-9% with >=1099-request probes against P99 TTFT/ITL SLOs | VERIFIED as published; NOT RUN | README --stress-test description and docs/performance.md. |
| G4 | readreaddrawdraw | There is a judge fallback that "would mess up the judging quietly" during judge-model outages | PARTIAL | The fallback exists (record_judge_fallback, per-sample scoring_mode judge_fallback, eval_suites/base.py). At d3e4283 it is recorded, not silent: any fallback sample flips the run's top-level scoring_mode to "judge_fallback", judge_failures/judge_outages land on the result, and a warning is logged - but the run does not fail and the number is a lower bound, not the canonical metric. Easy to miss if you only read accuracy. evalkit.gbench_lane ingest flags it. Commenter's blog write-up referenced, not captured. |
| G5 | Izento, Hrethric vs Kolkoris | A shared public benchmark unifies numbers vs becomes a benchmaxxing target, so private task benchmarks stay necessary | Opinion, both sides | Thread comments (scores 14/7 vs 3). Working position here: gBench for standardized numbers, this repo's private ladder for task numbers. |
| G6 | No-Library8065 | Half the "x beats y" posts are really different chat templates and sampler settings | Opinion, testable | The Golden Set chat-template pairs are exactly the check; run them per endpoint before quoting task scores. |

## Gaps

- OP's benchmark, task set, scoring code and result table are not published. This repo ships a stand-in (eleven tasks, graded difficulty, precision-scored reviewer), not OP's benchmark.
- OP's chart is an image; its numbers are not in the text we captured.
- The "2 more replies" under one comment were expanded; nothing else was collapsed, but the thread was 2h old at capture and may have grown.
- Exact Pi invocation flags were not verified; `harness.external_cmd` is left empty.
