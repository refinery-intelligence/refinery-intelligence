import json

# This mimics a global registry of restricted or sanctioned addresses/regions
COMPLIANCE_REGISTRY = {
    "restricted_addresses": [
        "rP8Z9p9...some_bad_actor_address", 
    ],
    "restricted_regions": ["REGION_X", "REGION_Y"],
    "min_node_version": "2.1.0"
}

def validate_compliance(destination):
    """Checks if the transaction is compliant before broadcasting."""
    print(f"--- Compliance Check: {destination} ---")
    
    # 1. Address Check
    if destination in COMPLIANCE_REGISTRY["restricted_addresses"]:
        return False, "Destination address is on the Sanctioned List."
    
    # 2. Syntax Check (The issue we just fixed)
    if not destination.startswith('r') or len(destination) < 25:
        return False, "Invalid address format detected by Compliance Engine."

    print("✅ Transaction pre-cleared for broadcast.")
    return True, "Success"

if __name__ == "__main__":
    # Test it
    test_addr = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"
    is_ok, msg = validate_compliance(test_addr)
    print(f"Result: {is_ok} | Message: {msg}")
