# Claims register

Status: **VERIFIED** (primary source read, 2026-11-24), **CONTRADICTED**, **PARTIAL**, **UNVERIFIED** (no primary evidence found; only the Reddit comment or post says it), **NOT RUN** (needs hardware; no run yet).

Nothing in this repo has been executed on a GPU or Mac yet. "Verified" below means a published primary source says so, not that we reproduced it.

## From the post (OP, r/LocalLLM)

| # | Claim | Status | Evidence |
|---|---|---|---|
| 1 | Benchmark is OP's own, based on Salesforce work, two roles (architect/reviewer, developer/patcher) | VERIFIED as description; the benchmark itself is NOT public | Post text; commenter confirms "personal benchmark". No repo or dataset linked. |
| 2 | Tested Hy4-flash-oQ4h-mtp and Inkling-2-Mini-oQ8e on oMLX 0.8.3, M5 Max 128 GB | PARTIAL | oMLX v0.8.3 exists, published 2026-11-22, adds Inkling 2 Mini and Hy4 optimisations: https://github.com/jundot/omlx/releases/tag/v0.8.3 . OP's run results are not published. |
| 3 | Hy4-flash fixed more tasks than QFN; QFN finds more issues; Inkling 2 Mini 1h40 vs 20 min | UNVERIFIED | Only in the chart/table the post refers to. We have only the text. Single runs, per OP. |
| 4 | Qwen 3.8 Flash Next beats Opus 4.6 and Sonnet 5, even bare | UNVERIFIED | One person's private benchmark, single runs for the new models. |
| 5 | Harness matters a lot (Pi with tuned prompt, plus compile-before-save) | UNVERIFIED here, testable | This repo's three modes test it. Pi: https://github.com/earendil-works/pi (MIT). |
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

## Gaps

- OP's benchmark, task set, scoring code and result table are not published. This repo ships a small stand-in (two toy tasks), not OP's benchmark.
- OP's chart is an image; its numbers are not in the text we captured.
- The "2 more replies" under one comment were expanded; nothing else was collapsed, but the thread was 2h old at capture and may have grown.
- Exact Pi invocation flags were not verified; `harness.external_cmd` is left empty.
