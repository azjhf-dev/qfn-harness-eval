"""Offline validation of the task set. No model, no endpoint, deterministic.

For every patcher task: the shipped (buggy) source must FAIL its test command and the
reference solution in docs/reference_solutions must PASS it.
For every reviewer task: the mock server's canned review must score 1.0, which proves
the seeded-issue keywords are reachable.

Run from the repo root:  python3 docs/selftest_tasks.py
Exit code 0 means every check passed."""
import json, os, shutil, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from evalkit.runner import load_tasks, sh, score_review

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOL = os.path.join(ROOT, "docs", "reference_solutions")

ok = True
for t in load_tasks(os.path.join(ROOT, "tasks")):
    if "patcher" in t["roles"]:
        with tempfile.TemporaryDirectory() as w:
            shutil.copytree(t["dir"], w, dirs_exist_ok=True)
            rc_bad, _ = sh(t["test_cmd"], w)
            sol_path = os.path.join(SOL, t["id"], t["source_file"])
            with open(sol_path) as f:
                open(os.path.join(w, t["source_file"]), "w").write(f.read())
            rc_good, out = sh(t["test_cmd"], w)
        good = rc_bad != 0 and rc_good == 0
        ok = ok and good
        print(f"{t['id']}: buggy rc={rc_bad} (want !=0), reference rc={rc_good} (want 0) {'OK' if good else 'FAIL'}")
        if rc_good != 0:
            print(out[-400:])
    else:
        canned = "\n".join(f"{n+1}. {i['id']}: {i['keywords'][0]}"
                           for n, i in enumerate(t.get("seeded_issues", [])))
        s, d = score_review(canned, t)
        good = s == 1.0
        ok = ok and good
        print(f"{t['id']}: canned review scores {s:.2f} (want 1.00), found {d['found']} {'OK' if good else 'FAIL'}")
sys.exit(0 if ok else 1)
