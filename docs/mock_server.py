import json, http.server
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers["Content-Length"]); req = json.loads(self.rfile.read(n))
        txt = req["messages"][-1]["content"]
        if "Fix this bug" in txt:
            out = "```python\ndef mean_of_positive(xs):\n    pos = [x for x in xs if x > 0]\n    return sum(pos) / len(pos) if pos else 0.0\n```"
        else:
            out = "1. unbounded cache grows forever\n2. not thread safe, race\n"
        b = json.dumps({"choices": [{"message": {"content": out}}], "usage": {"completion_tokens": 20, "prompt_tokens": 50}}).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass
http.server.HTTPServer(("127.0.0.1", 8099), H).serve_forever()
