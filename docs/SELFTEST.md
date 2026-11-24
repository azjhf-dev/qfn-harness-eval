# Self-test

Two offline checks, no model, no endpoint, deterministic.

## 1. Task validation
```
python3 docs/selftest_tasks.py
```
For every patcher task: the shipped buggy source must FAIL its test command and the
reference solution in `docs/reference_solutions/` must PASS it. For every reviewer
task: the mock server's canned review must score 1.00 (proves the seeded-issue
keywords are reachable). Exit code 0 means every check passed.

Result on 2026-11-24: all 7 tasks OK.

## 2. End-to-end plumbing
```
python3 docs/mock_server.py &          # fake endpoint on 127.0.0.1:8099
python3 -m evalkit.runner --config config.mock.json
```
The mock returns the reference solution for patcher prompts and a full-issue review
for reviewer prompts, so a healthy pipeline scores 1.00 everywhere.

Result on 2026-11-24: 21 runs (7 tasks x 3 modes), all 1.00, then
`python3 -m evalkit.report` summarised all six role x mode cells.

Both checks exercise the plumbing only - prompting, extraction, compile check,
scoring, reporting. Neither says anything about any model.
