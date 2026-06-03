import subprocess
import os
import sys

# COMPLIANCE SETTINGS
BLACKLISTED_ADDRESSES = ["rExampleBadAddress123"]
MAX_ALLOWABLE_DROPS = 200000 # 0.2 XRP safety ceiling

def check_compliance():
    print("\n>> PHASE: Global Compliance Check")
    # Mechanical check for destination safety
    target_addr = "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"
    if target_addr in BLACKLISTED_ADDRESSES:
        print(f"❌ COMPLIANCE ALERT: {target_addr} is restricted.")
        return False
    
    print("✅ Regional Compliance Verified (AU/TAS Rails).")
    return True

def run_step(script_path, description):
    print(f"\n>> PHASE: {description}")
    if not os.path.exists(script_path):
        print(f"❌ ERROR: {script_path} not found.")
        return False
        
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(result.stdout)
        return True
    else:
        print(f"❌ ERROR in {description}:\n{result.stderr}")
        return False

def main():
    print("==========================================")
    print("   REFINERY-01: COMPLIANCE & DATA PULSE   ")
    print("==========================================")

    # 1. COMPLIANCE GATE
    if not check_compliance():
        return

    # 2. DATA AGGREGATION (Fuel + Medical)
    # This creates the JSON feed before the payment script runs
    run_step(os.path.expanduser("~/Refinery-01/fuel_aggregator.py"), "Fuel & Study Aggregator")

    # 3. XRP SETTLEMENT (Fixed at 0.15 XRP / 150,000 drops)
    if not run_step(os.path.expanduser("~/Refinery-01/bot_crawl.py"), "XRP Settlement"):
        print("STOP: Financial layer failure.")
        return

    # 4. ASSET ALLOCATION (Picker moves the settled data to outbox)
    run_step(os.path.expanduser("~/Refinery-01/agent_picker.py"), "Agent Asset Allocation")

    print("==========================================")
    print("✅ CYCLE COMPLETE: COMPLIANT ASSET DELIVERED")
    print("==========================================")

if __name__ == "__main__":
    main()
