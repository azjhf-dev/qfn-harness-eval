"""Run tasks in three modes mirroring the thread's description:
bare             one request, one response (blue rows)
harness          tuned system prompt + feedback loop (green rows; stand-in for Pi)
harness_compile  harness plus a compile check before accepting the answer (dark green rows)
Roles: reviewer (find issues, scored by recall + precision of seeded issues) and
       patcher (fix a described bug, scored by the task's test command(s)).

Scoring versions (per task, "scoring_version" in task.json; absent = 1):
  reviewer v1  recall only: found seeded issues / all seeded issues. Backward compatible
               with the original task set, but a keyword dump scores 1.00.
  reviewer v2  recall plus precision: penalties for flagging listed decoys
               ("must_not_flag": things the code demonstrably is/does not have) and for
               reporting more findings than "max_findings". Deterministic keyword
               matching, same as v1. Weights: "w_decoy" (default 0.5), "w_over"
               (default 0.25). A task with no seeded issues is a clean-code control:
               any finding or decoy hit is a pure false positive.
  patcher      "test_cmd" (one command, binary) or "test_cmds" (a list; the score is the
               fraction that pass, so partial credit is possible, e.g. bug tests pass but
               the pre-existing regression tests broke).

Multi-file patcher tasks set "source_files" (files the model may change) and optionally
"context_files" (read-only, shown for context). The model returns each changed file in
its own fenced block whose first line is `# file: <name>`; files not returned are kept
as shipped. Single-file tasks keep the original "source_file" behaviour.

Format repair (v4): when a patcher reply to a multi-file task has no `# file:` headers,
or headers naming none of the editable files, nothing can be applied - a format failure,
not a model failure. In the harness modes the runner can re-prompt once (or
"format_repair_retries" times) with a format correction before scoring. Logged per run as
"repair_used" / "repair_attempts" (and detail.repair_issues), so runs without repair stay
directly comparable with earlier results. Bare mode never repairs (one request, one
response). A bare-mode format failure now scores 0.0 with detail.format_ok=false instead
of aborting the run with a KeyError."""
import argparse, json, os, re, subprocess, sys, tempfile, time, shutil
from .client import Client

FENCE = re.compile(r"```(?:\w+)?\n(.*?)```", re.S)
FILE_HDR = re.compile(r"^#\s*file:\s*(\S+)\s*$", re.M)
# A "finding" in a review is a numbered or bulleted list line. Deterministic.
FINDING = re.compile(r"^\s*(?:\d+\s*[\.\):]|[-*\u2022])\s*\S", re.M)


def extract_code(text):
    m = FENCE.findall(text)
    return (m[-1] if m else text).strip() + "\n"


def extract_codes(text):
    """Multi-file extraction: fenced blocks whose body starts with `# file: name`.
    Returns {name: code} or None when no block carries a file header (single-file tasks)."""
    files = {}
    for b in FENCE.findall(text):
        m = FILE_HDR.search(b)
        if m:
            files[m.group(1)] = (b[:m.start()] + b[m.end():]).strip() + "\n"
    return files or None


REPAIR_ASK = ("Format problem: {issue}. Resend the fix as one fenced code block per changed file, "
              "each block's first line exactly `# file: <name>`, where <name> is one of: {names}. "
              "Code blocks only, no prose.")


def format_issue(text, task):
    """Patcher reply format check; None when the reply is usable. A multi-file reply with no
    `# file:` header, or headers naming none of the editable files, applies nothing - repairable
    by a re-prompt, not a scoreable attempt."""
    if len(editable_files(task)) < 2:
        return None
    codes = extract_codes(text)
    if codes is None:
        return "no fenced block starts with `# file: <name>`"
    if not any(n in set(editable_files(task)) for n in codes):
        return "no `# file:` header names an editable file (" + ", ".join(editable_files(task)) + ")"
    return None


def load_tasks(d):
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name, "task.json")
        if os.path.exists(p):
            t = json.load(open(p)); t["dir"] = os.path.join(d, name); t["id"] = name
            yield t


# Task commands are written as `python ...` / `python3 ...`. Many current distros ship only
# `python3` (Debian 12+, Ubuntu 24.04+, this container), so an unqualified `python` makes every
# test exit 127 and every score 0.0 — a silent total failure that looks like bad model output.
# Point the first `python`/`python3` token at the interpreter running this script.
_PY = sys.executable or "python3"

def _py_cmd(cmd):
    return re.sub(r"^\s*python(3(\.\d+)?)?\b", lambda m: _PY, cmd or "")


def sh(cmd, cwd, timeout=120):
    r = subprocess.run(_py_cmd(cmd), shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr)[-2000:]


def editable_files(task):
    return task.get("source_files") or [task["source_file"]]


def prompt_for(task, role):
    def show(name):
        src = open(os.path.join(task["dir"], name)).read()
        return f"File {name}:\n```\n{src}\n```"
    if role == "reviewer":
        ask = ("Review this code. List every design flaw, bug or risk as a numbered list, one line each. "
               "Do not rewrite the code. Only list problems you are confident are real defects in this code; "
               "do not list generic risks, style nits, or things the code already handles. "
               "If you find no real defects, reply exactly: No issues found.")
        return f"{ask}\n\n" + show(task["source_file"])
    multi = len(editable_files(task)) > 1
    if multi:
        ask = ("Fix this bug. It may span more than one file. Return every file you change in its own fenced "
               "code block, each starting with a line `# file: <name>`. Files you do not return are kept as-is.\n\nBug: "
               + task["bug"])
    else:
        ask = "Fix this bug and return the full corrected file in one fenced code block.\n\nBug: " + task["bug"]
    parts = [show(f) for f in editable_files(task)]
    parts += [show(f) for f in task.get("context_files", [])]
    return f"{ask}\n\n" + "\n".join(parts)


def score_review(text, task):
    seeded = task.get("seeded_issues", [])
    lower = text.lower()
    found = [i for i in seeded if any(k.lower() in lower for k in i["keywords"])]
    version = task.get("scoring_version", 1)
    if version == 1:
        n = len(seeded) or 1
        return len(found) / n, {"found": [i["id"] for i in found], "scoring_version": 1}
    # v2: recall + precision (decoys that must not be flagged, cap on findings)
    decoys = task.get("must_not_flag", [])
    decoy_hits = [d["id"] for d in decoys if any(k.lower() in lower for k in d["keywords"])]
    findings = len(FINDING.findall(text))
    max_findings = task.get("max_findings", max(2 * len(seeded), 1))
    w_decoy = task.get("w_decoy", 0.5)
    w_over = task.get("w_over", 0.25)
    recall = len(found) / len(seeded) if seeded else 1.0
    decoy_pen = w_decoy * (len(decoy_hits) / len(decoys)) if decoys else 0.0
    over = max(0, findings - max_findings)
    over_pen = w_over * min(1.0, over / max(max_findings, 1))
    score = max(0.0, recall - decoy_pen - over_pen)
    return score, {"found": [i["id"] for i in found], "scoring_version": 2, "recall": recall,
                   "decoy_hits": decoy_hits, "findings": findings, "max_findings": max_findings}


def apply_and_test(codes, task, work):
    """codes: {filename: text} of files to overwrite. Returns (score, detail)."""
    shutil.copytree(task["dir"], work, dirs_exist_ok=True)
    allowed = set(editable_files(task))
    for name, code in codes.items():
        if name in allowed:
            open(os.path.join(work, name), "w").write(code)
    cmds = task.get("test_cmds") or [task["test_cmd"]]
    per, passed = [], 0
    for cmd in cmds:
        rc, out = sh(cmd, work)
        # Exit 127 / "not found" means the test never ran, so 0.0 would be a lie: record it as an error.
        broken = rc == 127 or "not found" in out
        per.append({"cmd": cmd, "rc": rc, "output": out,
                    "error": "test command could not run (interpreter missing?) — score not comparable" if broken else None})
        if not broken and rc == 0:
            passed += 1
    score = passed / len(cmds)
    detail = {"tests": per, "passed": passed, "of": len(cmds)}
    if any(p["error"] for p in per):
        detail["error"] = "one or more test commands could not run (interpreter missing?) — score not comparable"
    return score, detail


def score_patch(code, task, cfg, work):
    return apply_and_test({task["source_file"]: code}, task, work)


def run_one(client, cfg, task, role, mode):
    sys_prompt = open(cfg["harness"]["system_prompt_file"]).read() if mode != "bare" else None
    msgs = ([{"role": "system", "content": sys_prompt}] if sys_prompt else []) + [{"role": "user", "content": prompt_for(task, role)}]
    total = {"seconds": 0.0, "completion_tokens": 0, "turns": 0}
    turns = 1 if mode == "bare" else cfg["run"]["harness_max_turns"]
    # Default on (1) so an older config.json without the key repairs; 0 restores v3 behaviour.
    repairs_left = cfg["run"].get("format_repair_retries", 1) if (role == "patcher" and mode != "bare") else 0
    repair = {"used": False, "attempts": 0, "issues": []}
    text = ""
    for _ in range(turns):
        text, m = client.chat(msgs)
        total["seconds"] += m["seconds"]; total["completion_tokens"] += m["completion_tokens"] or 0; total["turns"] += 1
        if role == "reviewer":
            break
        issue = format_issue(text, task)
        if issue and repairs_left > 0:
            repairs_left -= 1
            repair["used"] = True; repair["attempts"] += 1; repair["issues"].append(issue)
            msgs += [{"role": "assistant", "content": text},
                     {"role": "user", "content": REPAIR_ASK.format(issue=issue, names=", ".join(editable_files(task)))}]
            continue
        if mode != "harness_compile":
            break
        codes = extract_codes(text) or {editable_files(task)[0]: extract_code(text)}
        with tempfile.TemporaryDirectory() as w:
            bad = ""
            for name, code in codes.items():
                if name not in set(editable_files(task)):
                    continue
                f = os.path.join(w, name); open(f, "w").write(code)
                rc, out = sh(cfg["compile_check_cmd"].format(file=f), w)
                if rc != 0:
                    bad = f"{name}: {out}"
                    break
        if not bad:
            break
        msgs += [{"role": "assistant", "content": text}, {"role": "user", "content": "Compile check failed:\n" + bad + "\nFix it and return the full file."}]
    with tempfile.TemporaryDirectory() as w:
        if role == "reviewer":
            s, detail = score_review(text, task)
        else:
            codes = extract_codes(text) or {editable_files(task)[0]: extract_code(text)}
            s, detail = apply_and_test(codes, task, w)
            detail["format_ok"] = format_issue(text, task) is None
    out = {"score": s, "detail": detail, **total}
    if role == "patcher":
        out["repair_used"] = repair["used"]
        out["repair_attempts"] = repair["attempts"]
        if repair["issues"]:
            out["detail"]["repair_issues"] = repair["issues"]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--endpoint", action="append", help="endpoint name(s) from config; default all")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, send nothing")
    a = ap.parse_args(argv)
    cfg = json.load(open(a.config))
    eps = a.endpoint or list(cfg["endpoints"])
    tasks = list(load_tasks(cfg["tasks_dir"]))
    sel = cfg["run"].get("tasks")          # optional list of task ids; empty/absent = all
    if sel:
        tasks = [t for t in tasks if t["id"] in sel]
    plan = [(e, t, r, m, i) for e in eps for t in tasks for r in cfg["run"]["roles"] for m in cfg["run"]["modes"] for i in range(cfg["run"]["repeats"])
            if (r in t["roles"])]
    print(f"{len(plan)} runs planned across {len(eps)} endpoint(s), {len(tasks)} task(s)")
    if a.dry_run:
        return 0
    os.makedirs(cfg["results_dir"], exist_ok=True)
    out = os.path.join(cfg["results_dir"], time.strftime("%Y%m%d-%H%M%S") + ".jsonl")
    clients = {e: Client(cfg["endpoints"][e], cfg["run"], cfg["rate_limit"]) for e in eps}
    with open(out, "w") as fh:
        for e, t, r, m, i in plan:
            try:
                res = run_one(clients[e], cfg, t, r, m)
            except Exception as ex:
                res = {"error": str(ex)[:300]}
            row = {"endpoint": e, "model": cfg["endpoints"][e]["model"], "task": t["id"], "difficulty": t.get("difficulty"), "role": r, "mode": m, "repeat": i, **res}
            fh.write(json.dumps(row) + "\n"); fh.flush()
            print(e, t["id"], r, m, i, res.get("score", res.get("error")))
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
