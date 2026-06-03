import json
import urllib.request
from datetime import datetime, timezone

class AaveMarketReservesAdapter:
    """
    Read-only market reserves discovery adapter for Aave V3.
    Uses discovered Market.reserves structure for deep asset parameter discovery.
    """
    
    ENDPOINT = "https://api.v3.aave.com/graphql"
    MARKET_ADDRESS = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
    CHAIN_ID = 1

    QUERY = """
    query MarketReserves($request: MarketRequest!) {
      market(request: $request) {
        name
        address
        chain {
          chainId
          name
        }
        reserves {
          underlyingToken {
            symbol
            name
            address
          }
          aToken {
            symbol
            address
          }
          vToken {
            symbol
            address
          }
        }
      }
    }
    """

    def __init__(self, timeout=10):
        self.timeout = timeout
        self.degraded = False
        self.degradation_reason = None

    def _verify_safety(self, query):
        """
        Enforces strict read-only behavior through safety checks.
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
                raise SecurityError(f"Forbidden keyword detected: {word}")

    def fetch_reserves(self):
        """
        Executes the reserves discovery query.
        """
        self._verify_safety(self.QUERY)
        
        variables = {
            "request": {
                "address": self.MARKET_ADDRESS,
                "chainId": self.CHAIN_ID
            }
        }
        
        payload_dict = {
            "query": self.QUERY,
            "variables": variables
        }
        
        payload = json.dumps(payload_dict).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Refinery-Market-Reserves-Worker"
        }

        req = urllib.request.Request(self.ENDPOINT, data=payload, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode("utf-8"))
                    if "errors" in result:
                        self.degraded = True
                        self.degradation_reason = f"GraphQL Errors: {result['errors'][0].get('message')}"
                        return self._normalize(None)
                    
                    market_data = result.get("data", {}).get("market")
                    return self._normalize(market_data)
                else:
                    self.degraded = True
                    self.degradation_reason = f"HTTP {response.status}"
                    return self._normalize(None)
        except Exception as e:
            self.degraded = True
            self.degradation_reason = str(e)
            return self._normalize(None)

    def _normalize(self, market_data):
        """
        Normalizes market reserve data into the standard discovery format.
        """
        if not market_data:
            reserves = []
            market_name = "Unknown"
        else:
            reserves = market_data.get("reserves", [])
            market_name = market_data.get("name", "Unknown")

        return {
            "source": "aave_v3_graphql",
            "source_mode": "live_market_reserves_discovery",
            "endpoint": self.ENDPOINT,
            "market_name": market_name,
            "market_address": self.MARKET_ADDRESS,
            "chain": "ethereum",
            "chain_id": self.CHAIN_ID,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "reserve_count": len(reserves),
            "reserves": reserves,
            "degraded": self.degraded,
            "degradation_reason": self.degradation_reason
        }

class SecurityError(Exception):
    pass

if __name__ == "__main__":
    adapter = AaveMarketReservesAdapter()
    print(json.dumps(adapter.fetch_reserves(), indent=4))
