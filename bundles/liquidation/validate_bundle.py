import os
import json
import sys
from datetime import datetime, timezone

# Add current directory to path for standalone execution
sys.path.append(os.path.dirname(__file__))

try:
    from builder import LiquidationBundleBuilder
    from schema import BUNDLE_METADATA_FIELDS, RECORD_FIELDS, RISK_BANDS, MAX_STALENESS_SECONDS
except ImportError:
    from .builder import LiquidationBundleBuilder
    from .schema import BUNDLE_METADATA_FIELDS, RECORD_FIELDS, RISK_BANDS, MAX_STALENESS_SECONDS

def validate_record_entry(i, record, generated_at):
    """
    Strict validation for a single liquidation record entry.
    Returns (is_valid, error_message)
    """
    # Field existence check
    missing_fields = [f for f in RECORD_FIELDS if f not in record]
    if missing_fields:
        return False, f"Record {i} is missing fields: {missing_fields}"

    try:
        # Risk Score (Integer 0-100)
        if not isinstance(record["risk_score"], int) or not (0 <= record["risk_score"] <= 100):
            return False, f"Record {i} risk_score invalid: {record['risk_score']}"

        # Risk Band (Enum)
        if record["risk_band"] not in RISK_BANDS:
            return False, f"Record {i} risk_band invalid: {record['risk_band']}"

        # Anomaly Flags (List)
        if not isinstance(record["anomaly_flags"], list):
            return False, f"Record {i} anomaly_flags must be a list"

        # Confidence Score (Numeric 0-1)
        if not isinstance(record["confidence_score"], (int, float)) or not (0 <= record["confidence_score"] <= 1):
            return False, f"Record {i} confidence_score invalid: {record['confidence_score']}"

        # Health Factor (Numeric Positive)
        if not isinstance(record["health_factor"], (int, float)) or record["health_factor"] <= 0:
            return False, f"Record {i} health_factor must be positive: {record['health_factor']}"

        # Position Size (Numeric Non-negative)
        if not isinstance(record["position_size_usd"], (int, float)) or record["position_size_usd"] < 0:
            return False, f"Record {i} position_size_usd invalid: {record['position_size_usd']}"

        # Prices (Numeric Positive)
        if not isinstance(record["liquidation_price"], (int, float)) or record["liquidation_price"] <= 0:
            return False, f"Record {i} liquidation_price must be positive"
        if not isinstance(record["reference_price"], (int, float)) or record["reference_price"] <= 0:
            return False, f"Record {i} reference_price must be positive"

        # Health Factor / Risk Correlation
        if record["health_factor"] < 1.0 and record["risk_band"] not in ["CRITICAL", "HIGH"]:
            return False, f"Record {i} health_factor < 1.0 but risk_band is {record['risk_band']}"

        # Temporal Validation
        record_ts = datetime.fromisoformat(record["timestamp"]).replace(tzinfo=timezone.utc)
        if record_ts > generated_at:
            return False, f"Record {i} timestamp is in the future relative to generated_at"
        
        staleness = (generated_at - record_ts).total_seconds()
        if staleness > MAX_STALENESS_SECONDS:
            return False, f"Record {i} is too stale ({staleness}s)"

    except Exception as e:
        return False, f"Error validating record {i}: {str(e)}"
    
    return True, "OK"

def validate_bundle_structure(bundle):
    """
    Validates the top-level structure and all records in a bundle.
    Returns (is_valid, errors_list)
    """
    errors = []
    
    # 1. Validate Top-Level Metadata
    missing_meta = [f for f in BUNDLE_METADATA_FIELDS if f not in bundle]
    if missing_meta:
        errors.append(f"Missing metadata fields: {missing_meta}")
        return False, errors
    
    try:
        generated_at = datetime.fromisoformat(bundle["generated_at"]).replace(tzinfo=timezone.utc)
    except Exception as e:
        errors.append(f"Invalid generated_at format: {str(e)}")
        return False, errors

    # 2. Validate Market Context if present
    if "market_context" in bundle:
        if not isinstance(bundle["market_context"], list):
            errors.append("'market_context' must be a list")

    # 3. Validate Records
    if "records" not in bundle or not isinstance(bundle["records"], list):
        errors.append("'records' array is missing or invalid.")
        return False, errors

    for i, record in enumerate(bundle["records"]):
        is_valid, msg = validate_record_entry(i, record, generated_at)
        if not is_valid:
            errors.append(msg)
    
    return len(errors) == 0, errors

def validate():
    print("--- Validating Enhanced Liquidation Bundle Module (Strict Mode) ---")
    builder = LiquidationBundleBuilder()
    bundle_id = "STRICT-ENRICHED-VAL-001"
    path = builder.build(bundle_id)
    
    if not os.path.exists(path):
        print(f"❌ Error: Bundle file not found at {path}")
        return

    print(f"✅ Success: Bundle file exists at {path}")
    
    with open(path, 'r') as f:
        bundle = json.load(f)
        
    is_valid, errors = validate_bundle_structure(bundle)
    
    if is_valid:
        print("✅ Success: Top-level metadata fields verified.")
        if "market_context" in bundle:
            print(f"✅ Success: 'market_context' validated (Count: {len(bundle['market_context'])})")
        print(f"✅ Success: 'records' array found with {len(bundle['records'])} entries.")
        print("✅ Success: All records passed strict validation.")
        print("\n--- Validation Complete: PASSED ---")
    else:
        for err in errors:
            print(f"❌ {err}")
        print("\n--- Validation Complete: FAILED ---")

if __name__ == "__main__":
    validate()
