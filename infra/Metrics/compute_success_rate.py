import json, datetime

def parse_ts(s):
    return datetime.datetime.fromisoformat(s.replace("Z","+00:00"))

HOURS_BACK = 6
cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=HOURS_BACK)

data = json.load(open("jobs.json"))
items = data["Items"]

success = failed = pending = processing = other = 0

for it in items:
    status = it.get("status", {}).get("S", "UNKNOWN")

    # time filter (use createdAt if present)
    c = it.get("createdAt", {}).get("S")
    if c:
        if parse_ts(c) < cutoff:
            continue

    if status == "SUCCESS":
        success += 1
    elif status == "FAILED":
        failed += 1
    elif status == "PENDING":
        pending += 1
    elif status == "PROCESSING":
        processing += 1
    else:
        other += 1

terminal = success + failed
rate = (success / terminal * 100) if terminal else 0.0

print("cutoff_utc =", cutoff.isoformat())
print(f"SUCCESS={success} FAILED={failed} (terminal={terminal})")
print(f"PENDING={pending} PROCESSING={processing} OTHER={other}")
print(f"Success rate (terminal only) = {rate:.2f}%")
