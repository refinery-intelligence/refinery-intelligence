import sys
import os
from datetime import datetime, timezone

# Add parent directory to path to import validate_bundle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from aave_adapter import AaveAdapter
    from compound_adapter import CompoundAdapter
    from validate_bundle import validate_record_entry
except ImportError:
    from .aave_adapter import AaveAdapter
    from .compound_adapter import CompoundAdapter
    from ..validate_bundle import validate_record_entry

def validate_adapters():
    print("--- Validating Protocol Adapters ---")
    adapters = [AaveAdapter(), CompoundAdapter()]
    
    all_passed = True
    for adapter in adapters:
        protocol_name = adapter.__class__.__name__
        print(f"Testing {protocol_name}...")
        
        try:
            records = adapter.get_records()
            generated_at = datetime.now(timezone.utc) # Capture after records are created
            if not records:
                print(f"❌ Error: No records returned from {protocol_name}")
                all_passed = False
                continue
                
            for i, record in enumerate(records):
                is_valid, msg = validate_record_entry(i, record, generated_at)
                if is_valid:
                    print(f"✅ Record {i} valid for {protocol_name}")
                else:
                    print(f"❌ Record {i} invalid for {protocol_name}: {msg}")
                    all_passed = False
        except Exception as e:
            print(f"❌ Exception in {protocol_name}: {str(e)}")
            all_passed = False

    if all_passed:
        print("\n--- Adapter Validation Complete: SUCCESS ---")
    else:
        print("\n--- Adapter Validation Complete: FAILED ---")
        exit(1)

if __name__ == "__main__":
    validate_adapters()
