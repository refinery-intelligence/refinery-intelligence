import sys
import os
from datetime import datetime, timezone

# Path setup to import from parent and local
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from aave_adapter import AaveAdapter
    from compound_adapter import CompoundAdapter
    from shared_normalizer import calculate_risk_band, calculate_risk_score, deduplicate_records
    from validate_bundle import validate_record_entry
    from schema import RECORD_FIELDS
except ImportError:
    from .aave_adapter import AaveAdapter
    from .compound_adapter import CompoundAdapter
    from .shared_normalizer import calculate_risk_band, calculate_risk_score, deduplicate_records
    from ..validate_bundle import validate_record_entry
    from ..schema import RECORD_FIELDS

def test_edge_cases():
    print("--- Running Adapter Edge Case Tests ---")
    
    # 1 & 2. Basic return checks
    aave = AaveAdapter()
    comp = CompoundAdapter()
    
    aave_records = aave.get_records()
    comp_records = comp.get_records()
    generated_at = datetime.now(timezone.utc)
    
    assert len(aave_records) > 0, "Aave adapter should return records"
    assert len(comp_records) > 0, "Compound adapter should return records"
    print("✅ Basic return checks passed.")

    # 3, 4, 5, 6. Schema and Value Validation
    for protocol, records in [("Aave", aave_records), ("Compound", comp_records)]:
        for i, record in enumerate(records):
            # Fields existence
            missing = [f for f in RECORD_FIELDS if f not in record]
            assert not missing, f"{protocol} record {i} missing fields: {missing}"
            
            # Strict validation
            is_valid, msg = validate_record_entry(i, record, generated_at)
            assert is_valid, f"{protocol} record {i} failed strict validation: {msg}"
            
            # Score and Band ranges
            assert 0 <= record["risk_score"] <= 100, f"Risk score out of range: {record['risk_score']}"
            assert record["risk_band"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"], f"Invalid risk band: {record['risk_band']}"

    print("✅ Schema and value range validation passed.")

    # 7. Duplicate Detection
    mock_duplicates = [
        {"position_id": "dup-1", "data": "a"},
        {"position_id": "dup-1", "data": "b"},
        {"position_id": "unique-1", "data": "c"}
    ]
    unique = deduplicate_records(mock_duplicates)
    assert len(unique) == 2, f"Deduplication failed: expected 2, got {len(unique)}"
    assert unique[0]["data"] == "a", "Should keep the first occurrence"
    print("✅ Duplicate detection logic passed.")

    # 8 & 9. Normalizer Logic
    assert calculate_risk_band(0.9) == "CRITICAL", "Health factor < 1.0 must be CRITICAL"
    assert calculate_risk_band(1.6) == "LOW", "Health factor >= 1.5 must be LOW"
    assert calculate_risk_score(1.0) == 100, "Health factor 1.0 must be risk score 100"
    assert calculate_risk_score(2.0) == 0, "Health factor 2.0 must be risk score 0"
    print("✅ Shared normalizer logic passed.")

    # 10 & 11. Malformed Data Safety
    class MalformedAave(AaveAdapter):
        def fetch_raw_data(self):
            return [{"id": "bad-data"}] # Missing healthFactor etc

    bad_aave = MalformedAave()
    # Should not raise exception, but return empty list (or list without the bad record)
    results = bad_aave.get_records()
    assert isinstance(results, list), "Should return a list even on error"
    assert len(results) == 0, "Malformed record should have been skipped"
    print("✅ Malformed data safety passed.")

    print("\n--- Edge Case Tests Complete: SUCCESS ---")

if __name__ == "__main__":
    try:
        test_edge_cases()
    except AssertionError as e:
        print(f"❌ Assertion Failed: {e}")
        exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        exit(1)
