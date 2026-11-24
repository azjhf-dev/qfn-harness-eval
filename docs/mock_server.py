"""Fake OpenAI-compatible endpoint on 127.0.0.1:8099 for plumbing checks only.

For a patcher prompt it returns the reference solution for that task (one fenced
block per file, with `# file:` headers for multi-file tasks); for a reviewer prompt
it returns a canned review listing every seeded issue, or "No issues found." for the
clean-code control. Every task therefore scores 1.0 through the full runner, which
exercises the whole pipeline (prompting, extraction, compile check, scoring,
reporting) without a model. It says nothing about any model.
Run from the repo root:  python3 docs/mock_server.py"""
import json, http.server, os, re

TASKS = os.environ.get("QHE_TASKS_DIR", "tasks")
SOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reference_solutions")

def task_by_file(name):
    for d in sorted(os.listdir(TASKS)):
        p = os.path.join(TASKS, d, "task.json")
        if os.path.exists(p):
            t = json.load(open(p))
            if name in (t.get("source_files") or [t.get("source_file")]):
                return d, t
    return None, None

class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers["Content-Length"]); req = json.loads(self.rfile.read(n))
        txt = req["messages"][-1]["content"]
        m = re.search(r"File (\S+):", txt)
        tid, task = task_by_file(m.group(1)) if m else (None, None)
        if task and "Fix this bug" in txt:
            files = task.get("source_files") or [task["source_file"]]
            blocks = []
            for f in files:
                code = open(os.path.join(SOL, tid, f)).read()
                hdr = f"# file: {f}\n" if len(files) > 1 else ""
                blocks.append("```python\n" + hdr + code + "\n```")
            out = "\n\n".join(blocks)
        elif task:
            seeded = task.get("seeded_issues", [])
            out = ("\n".join(f"{n+1}. {i['id']}: {i['keywords'][0]}" for n, i in enumerate(seeded))
                   or "No issues found.")
        else:
            out = "no answer"
        b = json.dumps({"choices": [{"message": {"content": out}}],
                        "usage": {"completion_tokens": 20, "prompt_tokens": 50}}).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass

http.server.HTTPServer(("127.0.0.1", 8099), H).serve_forever()
