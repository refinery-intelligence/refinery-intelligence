import json
from datetime import datetime, timezone, timedelta
from validate_bundle import validate_record_entry

def get_base_valid_record():
    return {
        "position_id": "test-pos-001",
        "protocol": "Aave-V3",
        "chain": "ethereum",
        "asset": "ETH",
        "collateral_asset": "WSTETH",
        "debt_asset": "USDC",
        "health_factor": 1.5,
        "liquidation_threshold": 0.85,
        "liquidation_bonus": 0.05,
        "position_size_usd": 1000.0,
        "liquidation_price": 2000.0,
        "reference_price": 3000.0,
        "risk_band": "LOW",
        "risk_score": 10,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "test",
        "confidence_score": 1.0,
        "anomaly_flags": [],
        "temporal_change_1h": 0.0,
        "temporal_change_24h": 0.0
    }

def run_negative_tests():
    print("--- Running Negative Validation Tests ---")
    generated_at = datetime.now(timezone.utc)
    
    test_cases = [
        ("Missing field", lambda r: r.pop("position_id")),
        ("risk_score below 0", lambda r: r.update({"risk_score": -1})),
        ("risk_score above 100", lambda r: r.update({"risk_score": 101})),
        ("invalid risk_band", lambda r: r.update({"risk_band": "EXTREME"})),
        ("anomaly_flags not a list", lambda r: r.update({"anomaly_flags": "none"})),
        ("confidence_score below 0", lambda r: r.update({"confidence_score": -0.1})),
        ("confidence_score above 1", lambda r: r.update({"confidence_score": 1.1})),
        ("health_factor <= 0", lambda r: r.update({"health_factor": 0})),
        ("negative position_size_usd", lambda r: r.update({"position_size_usd": -100})),
        ("liquidation_price <= 0", lambda r: r.update({"liquidation_price": 0})),
        ("reference_price <= 0", lambda r: r.update({"reference_price": -5})),
        ("health_factor < 1.0 with LOW risk", lambda r: r.update({"health_factor": 0.9, "risk_band": "LOW"})),
        ("timestamp after generated_at", lambda r: r.update({"timestamp": (generated_at + timedelta(hours=1)).isoformat()})),
        ("timestamp too stale", lambda r: r.update({"timestamp": (generated_at - timedelta(hours=2)).isoformat()}))
    ]
    
    passed_all = True
    for description, mutation in test_cases:
        record = get_base_valid_record()
        mutation(record)
        is_valid, msg = validate_record_entry(0, record, generated_at)
        
        if is_valid:
            print(f"❌ FAILED: {description} was accepted but should have been rejected.")
            passed_all = False
        else:
            print(f"✅ PASSED: {description} rejected correctly. ({msg})")

    if passed_all:
        print("\n--- Negative Tests Complete: ALL REJECTED AS EXPECTED ---")
    else:
        print("\n--- Negative Tests Complete: SOME INVALID RECORDS WERE ACCEPTED ---")
        exit(1)

if __name__ == "__main__":
    run_negative_tests()
