import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

BASE_URL = "https://api.llama.fi"

def fetch_protocols(limit=10):
    """
    Fetches protocols from DeFiLlama and filters for Lending category.
    """
    url = f"{BASE_URL}/protocols"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                # Filter for Lending protocols
                lending_protocols = [p for p in data if p.get("category") == "Lending"]
                return lending_protocols[:limit]
            else:
                print(f"DeFiLlama API error: HTTP {response.status}")
                return []
    except Exception as e:
        print(f"Network error fetching DeFiLlama data: {e}")
        return []

def normalize_protocol_context(raw_protocol):
    """
    Transforms raw DeFiLlama data into a normalized market context record.
    """
    return {
        "protocol": raw_protocol.get("name", "Unknown"),
        "chain": raw_protocol.get("chain", "Unknown"),
        "category": raw_protocol.get("category", "Unknown"),
        "tvl": raw_protocol.get("tvl", 0.0),
        "change_1h": raw_protocol.get("change_1h", 0.0),
        "change_1d": raw_protocol.get("change_1d", 0.0),
        "change_7d": raw_protocol.get("change_7d", 0.0),
        "source": "defillama_free_api",
        "source_mode": "live_public_context",
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }

def get_mock_protocol_context():
    """
    Returns fallback demo data for market context.
    """
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "protocol": "Aave-Mock-Context",
            "chain": "Multi-Chain",
            "category": "Lending",
            "tvl": 12500000000.0,
            "change_1h": 0.05,
            "change_1d": -1.2,
            "change_7d": 5.4,
            "source": "defillama_free_api",
            "source_mode": "mock_public_context",
            "fetched_at": now
        },
        {
            "protocol": "Compound-Mock-Context",
            "chain": "Ethereum",
            "category": "Lending",
            "tvl": 4500000000.0,
            "change_1h": -0.02,
            "change_1d": 0.5,
            "change_7d": -2.1,
            "source": "defillama_free_api",
            "source_mode": "mock_public_context",
            "fetched_at": now
        }
    ]

if __name__ == "__main__":
    # Test execution
    print("Fetching live data...")
    raw = fetch_protocols(limit=2)
    if raw:
        normalized = [normalize_protocol_context(p) for p in raw]
        print(json.dumps(normalized, indent=4))
    else:
        print("Falling back to mock...")
        print(json.dumps(get_mock_protocol_context(), indent=4))
