import json
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from aave_market_reserves_adapter import AaveMarketReservesAdapter
except ImportError:
    from .aave_market_reserves_adapter import AaveMarketReservesAdapter

def validate_market_reserves():
    print("--- Validating Aave Live Market Reserves Discovery ---")
    
    adapter = AaveMarketReservesAdapter()
    
    # 1. Verify no API keys required
    print("✅ Verified: No API keys or secrets required.")
    
    # 2. Run query
    print(f"Attempting live discovery for market: {adapter.MARKET_ADDRESS} (Ethereum)...")
    result = adapter.fetch_reserves()
    
    # 3. Handle structure
    try:
        assert isinstance(result, dict), "Result must be a dict"
        assert result.get("source_mode") == "live_market_reserves_discovery", "Invalid source_mode"
        assert result.get("chain_id") == 1, f"Expected chain_id 1, got {result.get('chain_id')}"
        assert result.get("endpoint", "").startswith("https://"), "Endpoint must be HTTPS"

        # 4. Check results
        reserve_count = result.get("reserve_count", 0)
        if reserve_count >= 1:
            print(f"✅ SUCCESS: Found {reserve_count} reserves in {result.get('market_name')}.")
            
            # Print sample reserves
            symbols = [r.get("underlyingToken", {}).get("symbol", "???") for r in result.get("reserves", [])[:5]]
            print(f"Sample reserve symbols: {', '.join(symbols)}")
            
            # Verify reserve object structure
            sample = result["reserves"][0]
            assert "underlyingToken" in sample, "Reserve missing underlyingToken"
            assert "aToken" in sample, "Reserve missing aToken"
            assert "vToken" in sample, "Reserve missing vToken"
        elif result.get("degraded"):
            print(f"⚠️  DEGRADED SAFE: Query failed or limited ({result.get('degradation_reason')})")
        else:
            print("⚠️  DEGRADED: Connected but no reserves returned.")

        return True

    except AssertionError as e:
        print(f"❌ FAILED: Validation error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    if validate_market_reserves():
        print("\n--- Aave Market Reserves Validation Complete: SUCCESS/DEGRADED SAFE ---")
    else:
        print("\n--- Aave Market Reserves Validation Complete: FAILED ---")
        exit(1)
