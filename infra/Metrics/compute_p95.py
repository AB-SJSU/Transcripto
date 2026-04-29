import json, math, datetime

def parse_ts(s):
    return datetime.datetime.fromisoformat(s.replace("Z","+00:00"))

# change this window as needed
HOURS_BACK = 6
cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=HOURS_BACK)

data = json.load(open("jobs.json"))
items = data["Items"]

lat = []
skipped = {"no_ts": 0, "not_terminal": 0, "too_old": 0}

for it in items:
    # DynamoDB JSON format
    status = it.get("status", {}).get("S")
    if status not in ("SUCCESS", "FAILED"):
        skipped["not_terminal"] += 1
        continue

    if "createdAt" not in it or "updatedAt" not in it:
        skipped["no_ts"] += 1
        continue

    c = parse_ts(it["createdAt"]["S"])
    u = parse_ts(it["updatedAt"]["S"])

    if c < cutoff:
        skipped["too_old"] += 1
        continue

    lat.append((u - c).total_seconds())

lat.sort()

print("cutoff_utc =", cutoff.isoformat())
print("included =", len(lat), "skipped =", skipped)

if not lat:
    print("No latencies found in window")
else:
    p50 = lat[len(lat)//2]
    idx95 = math.ceil(0.95*len(lat)) - 1
    p95 = lat[idx95]
    print("p50 =", p50, "sec")
    print("p95 =", p95, "sec")
    print("max =", lat[-1], "sec")