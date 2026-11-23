"""Summarise results/*.jsonl: mean score, spread and n per (endpoint, role, mode). Single runs are flagged."""
import glob, json, sys, statistics as st, collections
rows = [json.loads(l) for f in sorted(glob.glob(sys.argv[1] if len(sys.argv) > 1 else "results/*.jsonl")) for l in open(f)]
g = collections.defaultdict(list)
for r in rows:
    if "score" in r: g[(r["endpoint"], r["model"], r["role"], r["mode"])].append(r)
print("endpoint | model | role | mode | n | mean | stdev | tok/s | note")
for k, v in sorted(g.items()):
    s = [x["score"] for x in v]; secs = sum(x["seconds"] for x in v); tok = sum(x["completion_tokens"] for x in v)
    print(" | ".join([*k, str(len(s)), f"{st.mean(s):.2f}", f"{st.pstdev(s):.2f}" if len(s) > 1 else "-", f"{tok/secs:.1f}" if secs else "-", "single run, indicative only" if len(s) < 3 else ""]))
