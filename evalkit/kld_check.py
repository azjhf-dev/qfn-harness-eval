"""Compare numbers quoted in the thread with the published Basalt table (data/kld_published.csv vs data/kld_thread_claims.csv)."""
import csv
pub = {r["pack"]: r for r in csv.DictReader(open("data/kld_published.csv"))}
print("claim | claimed KLD / top1 | published KLD / top1 | verdict")
for c in csv.DictReader(open("data/kld_thread_claims.csv")):
    p = pub.get(c["maps_to_pack"])
    if not p:
        print(f"{c['label']} | {c['kld']} / {c['top1']} | no published row | UNVERIFIED"); continue
    same = abs(float(c["kld"]) - float(p["kld_mean"])) < 0.002 and abs(float(c["top1"]) - float(p["top1"])) < 0.2
    print(f"{c['label']} | {c['kld']} / {c['top1']} | {p['kld_mean']} / {p['top1']} | {'MATCH' if same else 'DIFFERS'}")
