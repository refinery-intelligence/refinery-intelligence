import json
import os
import shutil

# PATHS
MANIFEST_PATH = os.path.expanduser("~/Refinery-01/vault/agent_ledger/manifest.json")
PAYLOAD_DIR = os.path.expanduser("~/Refinery-01/inventory")
OUTBOX_DIR = os.path.expanduser("~/Refinery-01/vault/outbox/agent_xrp_01")

def run_agent_picker():
    print("--- Agent Picker: Scanning Manifest ---")
    
    if not os.path.exists(MANIFEST_PATH):
        print("No manifest found.")
        return

    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    updated = False
    for entry in manifest:
        # Only pick up assets that are SETTLED but not yet PROCESSED
        if entry["status"] == "SETTLED":
            asset_name = entry["asset_id"]
            src = os.path.join(PAYLOAD_DIR, asset_name)
            dest = os.path.join(OUTBOX_DIR, asset_name)

            if os.path.exists(src):
                print(f"Transferring {asset_name} to Agent Outbox...")
                shutil.move(src, dest)
                entry["status"] = "PROCESSED"
                updated = True
            else:
                print(f"Warning: Asset {asset_name} listed in manifest but file missing.")

    if updated:
        with open(MANIFEST_PATH, "w") as f:
            json.dump(manifest, f, indent=4)
        print("✅ Manifest updated to PROCESSED.")
    else:
        print("No new settled assets to pick up.")

if __name__ == "__main__":
    run_agent_picker()

