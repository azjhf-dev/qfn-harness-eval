"""Offline validation of the task set. No model, no endpoint, deterministic.

For every patcher task: the shipped (buggy) sources must score below 1.0 and the
reference solution in docs/reference_solutions must score 1.0. For multi-file tasks,
fixing only one file must earn strictly partial credit (the bug really spans files).
For every reviewer task: a precise canned review must score 1.0, and (scoring v2) a
noisy review that also flags the decoys and over-reports must score strictly less.
For the clean-code control (no seeded issues), "No issues found." must score 1.0 and
an invented-findings review must score below it.

Section 3 (v4) drives run_one with a stub client: a multi-file patcher reply with no
`# file:` headers must trigger one format-repair re-prompt and then score 1.0 with
repair_used=true; with format_repair_retries=0 the same reply must score below 1.0
with repair_used=false and detail.format_ok=false.

Run from the repo root:  python3 docs/selftest_tasks.py
Exit code 0 means every check passed."""
import json, os, shutil, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from evalkit.runner import load_tasks, score_review, apply_and_test, editable_files, run_one

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
# --- Section 3: format repair (v4), stub client, no server ---------------------------------
class StubClient:
    def __init__(self, replies):
        self.replies = list(replies); self.seen = []
    def chat(self, msgs):
        self.seen.append(msgs[-1]["content"])
        return self.replies.pop(0), {"seconds": 0.01, "completion_tokens": 10}

TASKS = {t["id"]: t for t in load_tasks(os.path.join(ROOT, "tasks"))}
t5 = TASKS["py-bugfix-5"]
ref5 = {f: open(os.path.join(SOL, "py-bugfix-5", f)).read() for f in editable_files(t5)}
multi_ok = "\n\n".join("```python\n# file: " + f + "\n" + ref5[f] + "\n```" for f in editable_files(t5))
multi_bad = "```python\n" + ref5[editable_files(t5)[0]] + "\n```"   # one block, no `# file:` header
base_cfg = {"harness": {"system_prompt_file": os.path.join(ROOT, "docs", "harness_system_prompt.txt")},
            "run": {"harness_max_turns": 4},
            "compile_check_cmd": "python -m py_compile {file}"}

stub = StubClient([multi_bad, multi_ok])
cfg = json.loads(json.dumps(base_cfg)); cfg["run"]["format_repair_retries"] = 1
r = run_one(stub, cfg, t5, "patcher", "harness")
check("v4 repair triggers", r["repair_used"] and r["repair_attempts"] == 1,
      f"(repair_used={r['repair_used']}, attempts={r['repair_attempts']})")
check("v4 repair re-prompts", any("Format problem" in s for s in stub.seen),
      "(a later user message carries the format correction)")
check("v4 repair scores", r["score"] == 1.0 and r["detail"]["format_ok"],
      f"(score {r['score']:.2f}, format_ok={r['detail']['format_ok']})")

stub = StubClient([multi_bad])
cfg = json.loads(json.dumps(base_cfg)); cfg["run"]["format_repair_retries"] = 0
r = run_one(stub, cfg, t5, "patcher", "harness")
check("v4 repair off", not r["repair_used"] and r["score"] < 1.0 and not r["detail"]["format_ok"],
      f"(repair_used={r['repair_used']}, score {r['score']:.2f}, format_ok={r['detail']['format_ok']})")

stub = StubClient([multi_bad])
cfg = json.loads(json.dumps(base_cfg)); cfg["run"]["format_repair_retries"] = 1
r = run_one(stub, cfg, t5, "patcher", "bare")
check("v4 bare never repairs", not r["repair_used"] and not r["detail"]["format_ok"],
      f"(repair_used={r['repair_used']}, format_ok={r['detail']['format_ok']})")

sys.exit(0 if ok else 1)
