import json
import os

def validate_catalogue():
    catalogue_path = "bundles/catalogue.json"
    print(f"--- Validating Bundle Catalogue: {catalogue_path} ---")
    
    if not os.path.exists(catalogue_path):
        print(f"❌ Error: {catalogue_path} not found.")
        return False

    try:
        with open(catalogue_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON format: {str(e)}")
        return False

    if "bundles" not in data or not isinstance(data["bundles"], list):
        print("❌ Error: 'bundles' array missing or invalid.")
        return False

    # Target bundle to verify
    target_id = "defi-liquidation-intel-v1"
    liquidation_bundle = next((b for b in data["bundles"] if b.get("bundle_id") == target_id), None)

    if not liquidation_bundle:
        print(f"❌ Error: Bundle '{target_id}' missing from catalogue.")
        return False

    # Safety checks
    if liquidation_bundle.get("payment_connected") is not False:
        print(f"❌ Error: '{target_id}' must have payment_connected=false.")
        return False
    
    if liquidation_bundle.get("production_ready") is not False:
        print(f"❌ Error: '{target_id}' must have production_ready=false.")
        return False

    # Field presence checks
    required_commands = ["validation_command", "negative_test_command"]
    for cmd in required_commands:
        if not isinstance(liquidation_bundle.get(cmd), str):
            print(f"❌ Error: '{cmd}' must be a string.")
            return False

    print(f"✅ PASSED: Catalogue is valid and '{target_id}' is correctly registered (Non-Production).")
    return True

if __name__ == "__main__":
    if validate_catalogue():
        print("\n--- Catalogue Validation Complete: SUCCESS ---")
    else:
        print("\n--- Catalogue Validation Complete: FAILED ---")
        exit(1)
