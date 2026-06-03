import json
import os

def validate_public_manifest():
    manifest_path = "public/.well-known/refinery-bundles.json"
    print(f"--- Validating Public Manifest: {manifest_path} ---")
    
    if not os.path.exists(manifest_path):
        print(f"❌ Error: {manifest_path} not found.")
        return False

    try:
        with open(manifest_path, "r") as f:
            manifest_raw = f.read()
            manifest = json.loads(manifest_raw)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON format: {str(e)}")
        return False

    # 1. Top-level safety checks
    if manifest.get("production_ready") is not False:
        print("❌ Error: Top-level production_ready must be false.")
        return False
    
    if manifest.get("payment_connected") is not False:
        print("❌ Error: Top-level payment_connected must be false.")
        return False

    # 2. Bundle entry checks
    bundles = manifest.get("bundles", [])
    target_id = "defi-liquidation-intel-v1"
    liquidation_bundle = next((b for b in bundles if b.get("bundle_id") == target_id), None)

    if not liquidation_bundle:
        print(f"❌ Error: Bundle '{target_id}' missing from manifest.")
        return False

    if liquidation_bundle.get("production_ready") is not False:
        print(f"❌ Error: Bundle production_ready must be false.")
        return False

    if liquidation_bundle.get("payment_connected") is not False:
        print(f"❌ Error: Bundle payment_connected must be false.")
        return False

    # 3. Forbidden Key Check (recursive)
    forbidden_keys = [
        "private_key", "seed", "secret", "wallet_seed", 
        "api_key", "password", "destination_tag", "xrpl_wallet"
    ]
    
    def check_for_forbidden_keys(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if any(fk in key.lower() for fk in forbidden_keys):
                    return False, key
                res, found_key = check_for_forbidden_keys(value)
                if not res:
                    return False, found_key
        elif isinstance(obj, list):
            for item in obj:
                res, found_key = check_for_forbidden_keys(item)
                if not res:
                    return False, found_key
        return True, None

    is_clean, leaked_key = check_for_forbidden_keys(manifest)
    if not is_clean:
        print(f"❌ Error: Forbidden key detected: '{leaked_key}'")
        return False

    print(f"✅ PASSED: Public manifest is safe, valid, and correctly describes the '{target_id}' bundle.")
    return True

if __name__ == "__main__":
    if validate_public_manifest():
        print("\n--- Public Manifest Validation Complete: SUCCESS ---")
    else:
        print("\n--- Public Manifest Validation Complete: FAILED ---")
        exit(1)
