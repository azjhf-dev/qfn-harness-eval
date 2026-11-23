# Thread capture

Source: https://www.reddit.com/r/LocalLLM/s/kqivphT83t (resolves to /r/LocalLLM/comments/1y3u13g/). Captured 2026-11-24 ~07:06 SGT from the rendered page. OP's account name was not shown in the capture. Ads, "people also ask" and navigation removed.

## Post
Title: "Qwen 3.8 Flash Next vs Hy4-flash vs Inkling-2-Mini vs Opus and Sonet". OP shares results of a custom benchmark extended with Hy4-flash-oQ4h-mtp (high thinking) and Inkling-2-Mini-oQ8e (max thinking) on oMLX 0.8.3, M5 Max 128 GB. Two roles: Architect (reviewer) and Developer (patcher). Three row types: bare (blue), Pi harness with tuned Salesforce prompts (green), Pi plus compile-before-save (dark green). Findings and caveats (single runs, usually 3) are listed in docs/CLAIMS.md items 1-7.

## Comments kept (signal)
- Realistic_Gap_5871: NVFP4 on 5090 speed claim; KLD table; correction of an earlier mix-up (their AWQ g32 vs Basalt nvfp4); opinion vs Opus.
- Mil0Mammon: challenges nvfp4 fidelity; task performance over KLD; V100 W4A16 mention.
- JurandM2: asks what the benchmark is; wants to compare his own setup.
- bippityBoppityboux: try lower thinking effort on Inkling.
- tomByrer: VRAM allocation question.
- paramarioh: wants Flash with Basalt.

## Dropped (noise): FeydRowan "thanks", Raredisarray "thanks", michaelthatsit remark about a data-viz subreddit.
