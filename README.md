# qfn-harness-eval

Evaluation repo built from the r/LocalLLM thread "Qwen 3.8 Flash Next vs Hy4-flash vs Inkling-2-Mini vs Opus and Sonet" (https://www.reddit.com/r/LocalLLM/s/kqivphT83t).

## What this is, and what it is not
The post's benchmark is private (Salesforce-based, no repo). So there is no code to fork. This repo is a **clean-room stand-in** with the same structure, so you can test the thread's claims on your own hardware:

- Two roles: **reviewer** (find issues) and **patcher** (fix a described bug).
- Three modes: **bare** (one request), **harness** (tuned system prompt, feedback loop; stand-in for the Pi harness), **harness_compile** (adds a compile check before accepting).
- An **OpenAI-compatible** client, so it targets Basalt serve (RTX 5090 + 5060 Ti), oMLX (Macs), llama.cpp, vLLM, Proxmox hosts.
- A **claims register** (docs/CLAIMS.md) marking each claim from the post and comments as verified, contradicted or unverified, with links.
- A **KLD check** comparing numbers quoted in comments with Basalt's published table.

The two sample tasks are toys to prove the pipeline. Real conclusions need your own task set in `tasks/`.

## Run
```
cp config.example.json config.json   # edit endpoints, repeats, rate limits
python3 -m evalkit.runner --dry-run  # shows the plan, sends nothing
python3 -m evalkit.runner --endpoint basalt-5090
python3 -m evalkit.report            # summary, flags n<3 as indicative
python3 -m evalkit.kld_check         # thread KLD claims vs published table
```
Python 3.8+, standard library only. Task format: `tasks/<id>/task.json` (see the two samples).

## Settings (all in config.json)
Endpoints and models, modes, roles, repeats, temperature, max tokens, reasoning effort, timeout, harness prompt file, compile command, task and result dirs. **Rate limits:** `min_interval_s`, `max_concurrency`, retries with exponential backoff, `Retry-After` honoured. Defaults are one request at a time, one second apart.

## Status
Verified: the runner, report and KLD check run offline against a mock server (see docs/SELFTEST.md). Not run: anything on a real GPU or Mac.

## Attribution and licences
- Idea, results and claims: the r/LocalLLM post by its OP and comments by Realistic_Gap_5871, Mil0Mammon, JurandM2, bippityBoppityboux, tomByrer, paramarioh. Quoted only as short facts with links. Their content belongs to them.
- Basalt (https://github.com/jesdga95/basalt, MIT; fork of Strata, MIT). KLD table copied as data from the model card https://huggingface.co/jesdga/Qwen3.8-Flash-Next-Basalt . Model packs: Qwen Community License 1.0 (derived from Qwen3.8-Flash-Next; Unsloth and NVIDIA quants). Not redistributed here.
- Pi (https://github.com/earendil-works/pi, MIT), oMLX (https://github.com/jundot/omlx), ds4 (https://github.com/antirez/ds4, MIT), MTPLX (https://mtplx.com/benchmarks/): referenced, not vendored.
- This repo's code: MIT. Fork-only: no issues, PRs or comments were made on any upstream or on Reddit.
