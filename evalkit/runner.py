"""Run tasks in three modes mirroring the thread's description:
bare             one request, one response (blue rows)
harness          tuned system prompt + feedback loop (green rows; stand-in for Pi)
harness_compile  harness plus a compile check before accepting the answer (dark green rows)
Roles: reviewer (find issues, scored by recall of seeded issues) and
       patcher (fix a described bug, scored by the task's test command)."""
import argparse, json, os, re, subprocess, sys, tempfile, time, shutil
from .client import Client

FENCE = re.compile(r"```(?:\w+)?\n(.*?)```", re.S)

def extract_code(text):
    m = FENCE.findall(text)
    return (m[-1] if m else text).strip() + "\n"

def load_tasks(d):
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name, "task.json")
        if os.path.exists(p):
            t = json.load(open(p)); t["dir"] = os.path.join(d, name); t["id"] = name
            yield t

def sh(cmd, cwd, timeout=120):
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr)[-2000:]

def prompt_for(task, role):
    src = open(os.path.join(task["dir"], task["source_file"])).read()
    if role == "reviewer":
        ask = "Review this code. List every design flaw, bug or risk as a numbered list, one line each. Do not rewrite the code."
    else:
        ask = "Fix this bug and return the full corrected file in one fenced code block.\n\nBug: " + task["bug"]
    return f"{ask}\n\nFile {task['source_file']}:\n```\n{src}\n```"

def score_review(text, task):
    hits = [i for i in task.get("seeded_issues", []) if any(k.lower() in text.lower() for k in i["keywords"])]
    n = len(task.get("seeded_issues", [])) or 1
    return len(hits) / n, {"found": [i["id"] for i in hits]}

def score_patch(code, task, cfg, work):
    shutil.copytree(task["dir"], work, dirs_exist_ok=True)
    open(os.path.join(work, task["source_file"]), "w").write(code)
    rc, out = sh(task["test_cmd"], work)
    return (1.0 if rc == 0 else 0.0), {"test_output": out}

def run_one(client, cfg, task, role, mode):
    sys_prompt = open(cfg["harness"]["system_prompt_file"]).read() if mode != "bare" else None
    msgs = ([{"role": "system", "content": sys_prompt}] if sys_prompt else []) + [{"role": "user", "content": prompt_for(task, role)}]
    total = {"seconds": 0.0, "completion_tokens": 0, "turns": 0}
    turns = 1 if mode == "bare" else cfg["run"]["harness_max_turns"]
    text = ""
    for _ in range(turns):
        text, m = client.chat(msgs)
        total["seconds"] += m["seconds"]; total["completion_tokens"] += m["completion_tokens"] or 0; total["turns"] += 1
        if role == "reviewer" or mode != "harness_compile":
            break
        with tempfile.TemporaryDirectory() as w:
            f = os.path.join(w, task["source_file"]); open(f, "w").write(extract_code(text))
            rc, out = sh(cfg["compile_check_cmd"].format(file=f), w)
        if rc == 0:
            break
        msgs += [{"role": "assistant", "content": text}, {"role": "user", "content": "Compile check failed:\n" + out + "\nFix it and return the full file."}]
    with tempfile.TemporaryDirectory() as w:
        s, detail = score_review(text, task) if role == "reviewer" else score_patch(extract_code(text), task, cfg, w)
    return {"score": s, "detail": detail, **total}

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--endpoint", action="append", help="endpoint name(s) from config; default all")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, send nothing")
    a = ap.parse_args(argv)
    cfg = json.load(open(a.config))
    eps = a.endpoint or list(cfg["endpoints"])
    tasks = list(load_tasks(cfg["tasks_dir"]))
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
            row = {"endpoint": e, "model": cfg["endpoints"][e]["model"], "task": t["id"], "role": r, "mode": m, "repeat": i, **res}
            fh.write(json.dumps(row) + "\n"); fh.flush()
            print(e, t["id"], r, m, i, res.get("score", res.get("error")))
    print("wrote", out)
    return 0

if __name__ == "__main__":
    sys.exit(main())
