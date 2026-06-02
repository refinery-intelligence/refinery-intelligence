import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("/home/dalien/Refinery-01/vault/datasets/defi-liquidation-intel-v1")

BUNDLE = BASE / "bundle.json"
LATEST = BASE / "latest.json"
LATEST_INTEL = BASE / "latest_intel.json"
HISTORY_JSONL = BASE / "history.jsonl"

def main():
    if not BUNDLE.exists():
        raise SystemExit(f"missing source bundle: {BUNDLE}")

    data = json.loads(BUNDLE.read_text())

    # Ensure there is a machine-readable freshness field.
    if "timestamp" not in data and "updated_at" in data:
        data["timestamp"] = data["updated_at"]

    if "synced_at" not in data:
        data["synced_at"] = datetime.now(timezone.utc).isoformat()

    LATEST.write_text(json.dumps(data, indent=2) + "\n")
    LATEST_INTEL.write_text(json.dumps(data, indent=2) + "\n")

    with HISTORY_JSONL.open("a") as f:
        f.write(json.dumps(data, separators=(",", ":")) + "\n")

    print("synced liquidation private outputs")
    print("source:", BUNDLE)
    print("latest:", LATEST)
    print("latest_intel:", LATEST_INTEL)
    print("history_jsonl:", HISTORY_JSONL)

if __name__ == "__main__":
    main()
