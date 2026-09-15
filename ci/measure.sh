#!/usr/bin/env bash
#
# measure.sh — the Week 2 "dashboard".
#
# Sends N payment requests at one PayCore instance and reports what a real
# dashboard would show you: error rate, and the latency percentiles.
# Prometheus and Grafana arrive in Week 13 and do this properly. This is the
# same four numbers, computed by hand, so you know what they mean first.
#
#   ./ci/measure.sh <base-url> [count]
#   ./ci/measure.sh http://localhost:8000 50
#
set -euo pipefail

BASE="${1:-http://localhost:8000}"
COUNT="${2:-50}"
MERCHANT="${MERCHANT_ID:-11111111-1111-1111-1111-111111111111}"

command -v curl >/dev/null || { echo "curl is not installed" >&2; exit 1; }

BODY=$(cat <<JSON
{"merchant_id":"${MERCHANT}","card_token":"tok_visa_4242","amount_cents":2500,"currency":"CAD","description":"canary probe"}
JSON
)

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

echo "probing ${BASE}/payments  (${COUNT} requests)..." >&2
for _ in $(seq 1 "$COUNT"); do
    curl -s -o /dev/null \
         -X POST "${BASE}/payments" \
         -H "Content-Type: application/json" \
         -d "$BODY" \
         -w '%{http_code} %{time_total}\n' \
         --max-time 10 >> "$TMP" || echo "000 10.0" >> "$TMP"
done

python3 - "$TMP" "$BASE" "$COUNT" <<'PY'
import sys
rows = [l.split() for l in open(sys.argv[1]) if l.strip()]
codes = [r[0] for r in rows]
lat   = sorted(float(r[1]) * 1000 for r in rows)
n     = len(lat)
errors = sum(1 for c in codes if not c.startswith("2"))

def pct(q):
    if not lat: return 0.0
    return lat[min(int(round(q * (n - 1))), n - 1)]

print()
print(f"  Target          {sys.argv[2]}/payments")
print(f"  Requests        {n}")
print(f"  Errors          {errors}  ({errors / n * 100:.1f}%)")
print(f"  Status codes    " + ", ".join(f"{c}x{codes.count(c)}" for c in sorted(set(codes))))
print()
print(f"  Latency  p50    {pct(0.50):8.1f} ms")
print(f"           p95    {pct(0.95):8.1f} ms")
print(f"           p99    {pct(0.99):8.1f} ms")
print(f"           max    {lat[-1]:8.1f} ms")
print()
PY
