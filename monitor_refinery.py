import os
import time
import json
from datetime import datetime

def get_status():
    manifest_path = os.path.expanduser("~/Refinery-01/vault/agent_ledger/manifest.json")
    outbox_dir = os.path.expanduser("~/Refinery-01/vault/outbox/agent_xrp_01/")
    
    os.system('clear')
    print("===============================================================")
    print(f"       REFINERY-01 MONITOR | {datetime.now().strftime('%H:%M:%S')} | STATUS: ONLINE")
    print("===============================================================")
    
    # 1. Check Outbox Inventory
    assets = os.listdir(outbox_dir)
    print(f"Pending Assets in Outbox: {len(assets)}")
    
    # 2. Show Last 5 Manifest Entries
    print("\n--- RECENT SETTLEMENTS (XRPL) ---")
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            data = json.load(f)
            for entry in data[-5:]: # Show last 5
                status_icon = "✅" if entry.get('status') == 'PROCESSED' else "⏳"
                print(f"{status_icon} {entry['timestamp'][11:19]} | {entry['tx_hash'][:20]}... | {entry['amount_drops']} drops")
    else:
        print("Waiting for first manifest entry...")

    print("\n--- SYSTEM COMMANDS ---")
    print("Viewing Log: tail -f ~/Refinery-01/vault/ingest/logs/heartbeat.log")
    print("Press Ctrl+C to exit monitor.")

while True:
    get_status()
    time.sleep(10) # Refresh every 10 seconds
