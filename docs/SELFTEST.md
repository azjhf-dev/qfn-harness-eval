# Self-test

Two offline checks, no model, no endpoint, deterministic.

## 1. Task validation
```
python3 docs/selftest_tasks.py
```
For every patcher task: the shipped buggy source must score below 1.0 and the
reference solution in `docs/reference_solutions/` must score 1.0 against the
task's test command(s). Multi-file tasks (py-bugfix-5) get an extra check:
fixing only one file must earn strictly partial credit, which proves the bug
really spans files and the graded scoring works.

For every reviewer task: a precise canned review listing exactly the seeded
issues must score 1.00. Scoring v2 adds the mirror check: a noisy review that
also flags the decoys (`must_not_flag`) and reports more findings than
`max_findings` must score strictly less. For the clean-code control
(py-review-4, no seeded issues) "No issues found." must score 1.00 and an
invented-findings review must score below it.

Exit code 0 means every check passed.

Result on 2026-11-24 (v3): all 11 tasks OK. Noisy reviews score 0.29-0.42 on
the seeded tasks and 0.00 on the clean control, vs 1.00 for precise reviews.

## 2. End-to-end plumbing
```
python3 docs/mock_server.py &          # fake endpoint on 127.0.0.1:8099
python3 -m evalkit.runner --config config.mock.json
```
The mock returns the reference solution for patcher prompts (one fenced block
per file for multi-file tasks) and a precise canned review for reviewer prompts
("No issues found." for the clean control), so a healthy pipeline scores 1.00
everywhere.

Result on 2026-11-24 (v3): 33 runs (11 tasks x 3 modes), all 1.00, then
`python3 -m evalkit.report` summarised all six role x mode cells.
Re-run on 2026-11-24 (v4): same 33 runs, all 1.00.

## 3. Format repair (v4)
Covered in `docs/selftest_tasks.py` (section 3) with a stub client, no server:
a multi-file patcher reply with no `# file:` headers must trigger exactly one
format-repair re-prompt (the correction message is checked), then score 1.00
with `repair_used=true`. With `format_repair_retries=0` the same reply scores
below 1.0 with `repair_used=false` and `detail.format_ok=false`. Bare mode
never repairs.

Result on 2026-11-24 (v4): all five repair checks OK (27 checks total).

Both checks exercise the plumbing only - prompting, multi-file extraction,
compile check, scoring, reporting. Neither says anything about any model.
