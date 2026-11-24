"""Offline validation of the task set. No model, no endpoint, deterministic.

For every patcher task: the shipped (buggy) sources must score below 1.0 and the
reference solution in docs/reference_solutions must score 1.0. For multi-file tasks,
fixing only one file must earn strictly partial credit (the bug really spans files).
For every reviewer task: a precise canned review must score 1.0, and (scoring v2) a
noisy review that also flags the decoys and over-reports must score strictly less.
For the clean-code control (no seeded issues), "No issues found." must score 1.0 and
an invented-findings review must score below it.

Run from the repo root:  python3 docs/selftest_tasks.py
Exit code 0 means every check passed."""
import json, os, shutil, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from evalkit.runner import load_tasks, score_review, apply_and_test, editable_files

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOL = os.path.join(ROOT, "docs", "reference_solutions")

ok = True

def check(label, cond, extra=""):
    global ok
    ok = ok and cond
    print(f"{label}: {'OK' if cond else 'FAIL'} {extra}")

for t in load_tasks(os.path.join(ROOT, "tasks")):
    if "patcher" in t["roles"]:
        files = editable_files(t)
        ref = {f: open(os.path.join(SOL, t["id"], f)).read() for f in files}
        with tempfile.TemporaryDirectory() as w:
            s_bad, _ = apply_and_test({}, t, w)
        with tempfile.TemporaryDirectory() as w:
            s_good, d_good = apply_and_test(ref, t, w)
        check(f"{t['id']} buggy", s_bad < 1.0, f"(score {s_bad:.2f}, want <1.00)")
        check(f"{t['id']} reference", s_good == 1.0, f"(score {s_good:.2f}, want 1.00)")
        if s_good != 1.0:
            for p in d_good["tests"]:
                if p["rc"] != 0:
                    print(p["output"][-400:])
        if len(files) > 1:
            with tempfile.TemporaryDirectory() as w:
                s_part, _ = apply_and_test({files[0]: ref[files[0]]}, t, w)
            check(f"{t['id']} partial", 0.0 < s_part < 1.0,
                  f"(fixing only {files[0]} scores {s_part:.2f}, want between 0 and 1)")
    else:
        seeded = t.get("seeded_issues", [])
        canned = ("\n".join(f"{n+1}. {i['id']}: {i['keywords'][0]}" for n, i in enumerate(seeded))
                  or "No issues found.")
        s_precise, _ = score_review(canned, t)
        check(f"{t['id']} precise", s_precise == 1.0, f"(precise review scores {s_precise:.2f}, want 1.00)")
        if t.get("scoring_version", 1) >= 2:
            decoys = t.get("must_not_flag", [])
            lines = [canned] if seeded else []
            n0 = len(seeded)
            for j, d in enumerate(decoys):
                lines.append(f"{n0+j+1}. Also worried about {d['keywords'][0]} here")
            for j in range(5):
                lines.append(f"{n0+len(decoys)+j+1}. Generic style nit number {j}")
            s_noisy, d_noisy = score_review("\n".join(lines), t)
            check(f"{t['id']} noisy", s_noisy < s_precise,
                  f"(noisy review scores {s_noisy:.2f} < precise {s_precise:.2f}; "
                  f"decoys hit {d_noisy.get('decoy_hits')}, findings {d_noisy.get('findings')})")
sys.exit(0 if ok else 1)
