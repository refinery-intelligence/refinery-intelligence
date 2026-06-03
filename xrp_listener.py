import json
import time
from pathlib import Path

from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountTx

from refinery_bridge import link_tx_to_data
from ledger_store import save_transaction

REFINERY_WALLET = "rpxqpBFyrBBvjHJmpjtnei149eecbXy28A"

REQUIRED_XRP = 0.15
AGENT_ID = "AGENT_XRP_01"
ASSET_FILE = "defi-liquidation-intel-v1/bundle.json"

BASE_DIR = Path.home() / "Refinery-01"
LEDGER_DIR = BASE_DIR / "vault" / "agent_ledger"
CONSUMED_HASHES_PATH = LEDGER_DIR / "consumed_hashes.json"
PACKAGES_PATH = BASE_DIR / "packages.json"
NETWORKS = {
    "testnet": JsonRpcClient("https://s.altnet.rippletest.net:51234/"),
    "mainnet": JsonRpcClient("https://s1.ripple.com:51234/"),
}


def load_consumed_hashes():
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)

    if not CONSUMED_HASHES_PATH.exists():
        return set()

    try:
        with open(CONSUMED_HASHES_PATH, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_consumed_hash(tx_hash):
    hashes = load_consumed_hashes()
    hashes.add(tx_hash)

    with open(CONSUMED_HASHES_PATH, "w") as f:
        json.dump(sorted(hashes), f, indent=2)


def check_for_payments():
    print(f"\nMonitoring XRPL networks for payments to {REFINERY_WALLET}...")

    consumed = load_consumed_hashes()

    for network_name, client in NETWORKS.items():
        print(f"\nChecking {network_name}...")

        response = client.request(
            AccountTx(
                account=REFINERY_WALLET,
                limit=10
            )
        )

        print(f"{network_name} response received")

        transactions = response.result.get("transactions", [])

        for item in transactions:
            meta = item.get("meta", {})
            tx_data = item.get("tx_json", {})

            tx_hash = tx_data.get("hash") or item.get("hash")
            print("DEBUG TX:", tx_hash)
            print("DEBUG TYPE:", tx_data.get("TransactionType"))
            print("DEBUG DEST:", tx_data.get("Destination"))
            print("DEBUG TAG:", tx_data.get("DestinationTag"))
            print("DEBUG RESULT:", meta.get("TransactionResult"))
            print("DEBUG AMOUNT:", meta.get("delivered_amount", tx_data.get("Amount")))

            if not tx_hash:
                continue

            if tx_hash in consumed:
                continue

            if meta.get("TransactionResult") != "tesSUCCESS":
                continue

            if tx_data.get("TransactionType") != "Payment":
                continue

            if tx_data.get("Destination") != REFINERY_WALLET:
                continue

            try:
                amount_drops = int(
                    meta.get("delivered_amount", tx_data.get("Amount", 0))
                )
                amount_xrp = amount_drops / 1_000_000      
                
                required_price = REQUIRED_XRP
                asset_file = ASSET_FILE

                if amount_xrp < required_price:
                    print(
                        f"Insufficient XRP: {amount_xrp} XRP received, {required_price} required"
                    )
                    continue

                print("📦 PACKAGE PURCHASED: fuel_intel_v1")
                print(f"📁 ASSET FILE: {asset_file}") 
                link_tx_to_data(tx_hash, AGENT_ID, asset_file)
                save_consumed_hash(tx_hash)
                consumed.add(tx_hash)
            except Exception as e:
                print("DELIVERY ERROR:", e)
                continue
                
if __name__ == "__main__":
    while True:
        check_for_payments()
        time.sleep(10)
