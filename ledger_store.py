import json
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data")
TX_FILE = DATA_DIR / "tx_index.json"

DATA_DIR.mkdir(exist_ok=True)

def load_transactions():
    if not TX_FILE.exists():
        return []

    with open(TX_FILE, "r") as f:
        return json.load(f)

def save_transaction(tx_hash, account, destination, amount, raw_tx=None):
    transactions = load_transactions()

    if any(tx.get("tx_hash") == tx_hash for tx in transactions):
        print(f"⚠️ TX already stored: {tx_hash[:12]}...")
        return False

    record = {
        "tx_hash": tx_hash,
        "account": account,
        "destination": destination,
        "amount": amount,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "raw_tx": raw_tx or {}
    }

    transactions.append(record)

    with open(TX_FILE, "w") as f:
        json.dump(transactions, f, indent=2)

    print(f"✅ Stored TX: {tx_hash[:12]}...")
    return True

