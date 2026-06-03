import json
import urllib.request
from datetime import datetime, timezone

class AaveMarketDiscoveryAdapter:
    """
    Read-only market and reserve discovery adapter for Aave V3.
    Strictly limited to public, non-sensitive market parameters.
    """
    
    ENDPOINT = "https://api.v3.aave.com/graphql"
    
    # Query 1: Chain Discovery
    CHAINS_QUERY = """
    query Chains {
      chains {
        name
        chainId
      }
    }
    """
    
    # Query 2: Reserve Discovery (Attempting to get public market metadata)
    RESERVES_QUERY = """
    query Reserves {
      reserves {
        symbol
        name
        isActive
        baseLTVasCollateral
        liquidationThreshold
        liquidationBonus
      }
    }
    """

    def __init__(self, timeout=10):
        self.timeout = timeout
        self.degraded = False
        self.degradation_reason = None

    def _verify_safety(self, query):
        """
        Enforces strict safety boundaries on endpoint and query content.
        """
        if not self.ENDPOINT.startswith("https://"):
            raise SecurityError("Endpoint must use HTTPS")

        forbidden = [
            "mutation", "transaction", "approve", "supply", 
            "borrow", "withdraw", "repay"
        ]
        query_lower = query.lower()
        for word in forbidden:
            if word in query_lower:
                raise SecurityError(f"Forbidden keyword detected in query: {word}")

    def _post_query(self, query):
        """
        Helper to execute a GraphQL POST request.
        """
        self._verify_safety(query)
        
        data = {"query": query}
        payload = json.dumps(data).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Refinery-Market-Discovery-Worker"
        }

        req = urllib.request.Request(self.ENDPOINT, data=payload, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    return json.loads(response.read().decode("utf-8")), None
                else:
                    return None, f"HTTP {response.status}"
        except Exception as e:
            return None, str(e)

    def fetch_discovery_data(self):
        """
        Orchestrates discovery of chains and reserves.
        Degrades gracefully if reserves query fails.
        """
        discovery_result = {
            "chains": [],
            "reserves": []
        }
        
        # 1. Fetch Chains
        chains_raw, err = self._post_query(self.CHAINS_QUERY)
        if chains_raw:
            discovery_result["chains"] = chains_raw.get("data", {}).get("chains", [])
        else:
            self.degraded = True
            self.degradation_reason = f"Chains fetch failed: {err}"
            return self._normalize(discovery_result)

        # 2. Fetch Reserves (Market Discovery)
        # Note: Some GraphQL endpoints require a chainId or have different schema for reserves.
        reserves_raw, err = self._post_query(self.RESERVES_QUERY)
        if reserves_raw and "errors" not in reserves_raw:
            discovery_result["reserves"] = reserves_raw.get("data", {}).get("reserves", [])
        else:
            self.degraded = True
            self.degradation_reason = f"Reserves query limited or failed: {err or 'Schema Mismatch'}"
            
        return self._normalize(discovery_result)

    def _normalize(self, raw):
        """
        Normalizes discovery data into the final discovery record.
        """
        return {
            "source": "aave_v3_graphql",
            "source_mode": "live_read_only_market_discovery",
            "endpoint": self.ENDPOINT,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "chain_count": len(raw["chains"]),
            "market_count": 0, # Placeholder if markets distinct from reserves
            "reserve_count": len(raw["reserves"]),
            "chains": raw["chains"],
            "markets_or_reserves": raw["reserves"],
            "degraded": self.degraded,
            "degradation_reason": self.degradation_reason
        }

class SecurityError(Exception):
    pass

if __name__ == "__main__":
    adapter = AaveMarketDiscoveryAdapter()
    print(json.dumps(adapter.fetch_discovery_data(), indent=4))
