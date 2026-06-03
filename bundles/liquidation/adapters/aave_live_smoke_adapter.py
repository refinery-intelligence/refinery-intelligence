import json
import urllib.request
from datetime import datetime, timezone

class AaveLiveSmokeAdapter:
    """
    Read-only smoke-test adapter for Aave V3.
    Strictly limited to public, non-sensitive chain discovery.
    """
    
    ENDPOINT = "https://api.v3.aave.com/graphql"
    QUERY = """
    query Chains {
      chains {
        name
        chainId
      }
    }
    """

    def __init__(self, timeout=10):
        self.timeout = timeout
        self._verify_safety()

    def _verify_safety(self):
        """
        Enforces strict safety boundaries on endpoint and query.
        """
        # Endpoint check
        if not self.ENDPOINT.startswith("https://"):
            raise SecurityError("Endpoint must use HTTPS")

        # Query content check
        forbidden = [
            "mutation", "transaction", "approve", "supply", 
            "borrow", "withdraw", "repay"
        ]
        query_lower = self.QUERY.lower()
        for word in forbidden:
            if word in query_lower:
                raise SecurityError(f"Forbidden keyword detected in query: {word}")

    def fetch_live_smoke_data(self):
        """
        Executes the read-only GraphQL query using urllib.
        """
        data = {"query": self.QUERY}
        payload = json.dumps(data).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Refinery-Gemini-Worker-A-SmokeTest"
        }

        req = urllib.request.Request(self.ENDPOINT, data=payload, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode("utf-8"))
                    return self._normalize(result)
                else:
                    return {"error": f"HTTP {response.status}", "status": "DEGRADED"}
        except Exception as e:
            return {"error": str(e), "status": "NETWORK_FAILURE"}

    def _normalize(self, raw_data):
        """
        Normalizes raw GraphQL response into a smoke-test record.
        """
        chains_data = raw_data.get("data", {}).get("chains", [])
        
        return {
            "source": "aave_v3_graphql",
            "source_mode": "live_read_only_smoke_test",
            "endpoint": self.ENDPOINT,
            "query_type": "chains",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "chain_count": len(chains_data),
            "chains": chains_data,
            "status": "SUCCESS"
        }

class SecurityError(Exception):
    pass

if __name__ == "__main__":
    adapter = AaveLiveSmokeAdapter()
    print(json.dumps(adapter.fetch_live_smoke_data(), indent=4))
