"""OpenAI-compatible chat client with a polite rate limiter (stdlib only)."""
import json, os, threading, time, urllib.request, urllib.error

class RateLimiter:
    def __init__(self, min_interval_s, max_concurrency):
        self.min_interval = min_interval_s
        self.sem = threading.Semaphore(max(1, int(max_concurrency)))
        self.lock = threading.Lock()
        self.last = 0.0
    def __enter__(self):
        self.sem.acquire()
        with self.lock:
            wait = self.last + self.min_interval - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self.last = time.monotonic()
        return self
    def __exit__(self, *a):
        self.sem.release()

class Client:
    def __init__(self, ep, run, rl):
        self.base = ep["base_url"].rstrip("/")
        self.model = ep["model"]
        self.key = os.environ.get(ep.get("api_key_env") or "", "")
        self.run = run
        self.rl = rl
        self.limiter = RateLimiter(rl["min_interval_s"], rl["max_concurrency"])

    def chat(self, messages):
        body = {"model": self.model, "messages": messages,
                "temperature": self.run["temperature"], "max_tokens": self.run["max_tokens"]}
        if self.run.get("reasoning_effort"):
            body["reasoning_effort"] = self.run["reasoning_effort"]
        data = json.dumps(body).encode()
        headers = {"Content-Type": "application/json"}
        if self.key:
            headers["Authorization"] = "Bearer " + self.key
        for attempt in range(self.rl["max_retries"] + 1):
            with self.limiter:
                t0 = time.monotonic()
                try:
                    req = urllib.request.Request(self.base + "/chat/completions", data, headers)
                    with urllib.request.urlopen(req, timeout=self.run["request_timeout_s"]) as r:
                        out = json.load(r)
                    dt = time.monotonic() - t0
                    msg = out["choices"][0]["message"]
                    usage = out.get("usage", {})
                    return msg.get("content") or "", {"seconds": dt, "completion_tokens": usage.get("completion_tokens"), "prompt_tokens": usage.get("prompt_tokens")}
                except urllib.error.HTTPError as e:
                    retry_after = e.headers.get("Retry-After") if self.rl.get("honor_retry_after") else None
                    if e.code not in (429, 500, 502, 503, 504) or attempt == self.rl["max_retries"]:
                        raise
                    delay = float(retry_after) if retry_after and retry_after.replace(".", "").isdigit() else None
                except (urllib.error.URLError, TimeoutError):
                    if attempt == self.rl["max_retries"]:
                        raise
                    delay = None
            if delay is None:
                delay = min(self.rl["backoff_max_s"], self.rl["backoff_base_s"] * (2 ** attempt))
            time.sleep(delay)
