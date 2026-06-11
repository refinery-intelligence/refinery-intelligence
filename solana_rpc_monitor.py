import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RPC = "https://api.mainnet-beta.solana.com"

DATASET_DIR = Path(
    "vault/datasets/solana-temporal-intel-v1"
)

LATEST_FILE = DATASET_DIR / "latest.json"
HISTORY_FILE = DATASET_DIR / "history.jsonl"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def rpc_call(method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method
    }

    if params is not None:
        payload["params"] = params

    req = urllib.request.Request(
        RPC,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )

    start = time.time()

    with urllib.request.urlopen(req, timeout=20) as response:
        body = response.read().decode()

    latency = round(time.time() - start, 4)

    data = json.loads(body)

    return data["result"], latency


def write_record(record):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    with open(LATEST_FILE, "w") as f:
        json.dump(record, f, indent=2)

    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")


def collect_once():
    slot, latency = rpc_call("getSlot")

    record = {
        "timestamp": now_iso(),
        "solana_current_slot": slot,
        "rpc_latency_seconds": latency
    }

    write_record(record)

    print(json.dumps(record, indent=2))
    return record


def main():
    if "--once" in sys.argv:
        collect_once()
        return

    while True:
        try:
            collect_once()

        except Exception as e:
            print("ERROR:", e)

        time.sleep(60)


if __name__ == "__main__":
    main()
