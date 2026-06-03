import json
import datetime
from pathlib import Path

BASE_DIR = Path.home() / "Refinery-01"
VAULT_DIR = BASE_DIR / "vault" / "datasets"
LEDGER_DIR = BASE_DIR / "vault" / "agent_ledger"
MANIFEST_PATH = LEDGER_DIR / "manifest.json"

ALLOWED_FILES = {
    "fuel_intel_v1.json": "fuel_intel_v1.json",
    "defi-liquidation-intel-v1/bundle.json": "defi-liquidation-intel-v1/bundle.json"
}

def safe_file_name(file_name):
    if file_name not in ALLOWED_FILES:
        raise ValueError("File not allowed for release")
    return ALLOWED_FILES[file_name]


def load_manifest():
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)

    if not MANIFEST_PATH.exists() or MANIFEST_PATH.stat().st_size == 0:
        return []

    try:
        with open(MANIFEST_PATH, "r") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            return [data]

        return []

    except Exception:
        return []


def save_manifest(data):
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)

    with open(MANIFEST_PATH, "w") as f:
        json.dump(data, f, indent=4)


def tx_already_linked(tx_hash):
    manifest = load_manifest()

    for entry in manifest:
        if isinstance(entry, dict) and entry.get("tx_hash") == tx_hash:
            return True

        if isinstance(entry, str) and entry == tx_hash:
            return True

    return False


def link_tx_to_data(tx_hash, agent_id, file_name):
    if tx_already_linked(tx_hash):
        print(f"⚠️ TX already linked: {tx_hash[:10]}...")
        return False

    safe_name = safe_file_name(file_name)

    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    payload_path = VAULT_DIR / safe_name

    if not payload_path.exists():
        with open(payload_path, "w") as f:
            f.write(f"TELEMETRY_DATA_ENCRYPTED_FOR_{agent_id}")

    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "tx_hash": tx_hash,
        "agent_id": agent_id,
        "asset_linked": safe_name,
        "status": "PAID_RELEASED"
    }

    manifest = load_manifest()
    manifest.append(entry)
    save_manifest(manifest)

    print(f"✅ Asset {safe_name} linked to TX {tx_hash[:10]}... for Agent {agent_id}")
    return True


if __name__ == "__main__":
    link_tx_to_data(
        "TEST_HASH_123",
        "AGENT_XRP_01",
        "node_report_v1.dat"
    )
