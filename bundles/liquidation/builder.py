import json
import os
from datetime import datetime, timezone

# Local imports for the module structure
try:
    from .schema import BUNDLE_METADATA_FIELDS, RECORD_FIELDS
    from .mock_data import MOCK_RECORDS
    from .sources.defillama import fetch_protocols, normalize_protocol_context, get_mock_protocol_context
except (ImportError, ValueError):
    import schema
    import mock_data
    from sources.defillama import fetch_protocols, normalize_protocol_context, get_mock_protocol_context
    BUNDLE_METADATA_FIELDS = schema.BUNDLE_METADATA_FIELDS
    RECORD_FIELDS = schema.RECORD_FIELDS
    MOCK_RECORDS = mock_data.MOCK_RECORDS

class LiquidationBundleBuilder:
    """
    Builds a refined, agent-ready liquidation bundle using mock data
    and integrated public market context.
    """
    def __init__(self, output_dir="../../inventory"):
        # Resolve path relative to this file
        self.output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), output_dir))
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def get_market_context(self):
        """
        Retrieves market context from DeFiLlama with fallback.
        """
        raw_protocols = fetch_protocols(limit=5)
        if raw_protocols:
            return [normalize_protocol_context(p) for p in raw_protocols]
        return get_mock_protocol_context()

    def build(self, bundle_id, include_market_context=True):
        # Assemble records from mock data
        records = MOCK_RECORDS
        
        # Build the top-level bundle structure
        payload = {
            "bundle_id": bundle_id,
            "bundle_type": "DEFI_LIQUIDATION_INTEL",
            "version": "1.4.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "record_count": len(records),
            "source_mode": "mixed",
            "intended_consumer": "autonomous_agent",
            "records": records
        }
        
        if include_market_context:
            payload["market_context"] = self.get_market_context()
        
        filename = f"liquidation_bundle_{bundle_id}.json"
        file_path = os.path.join(self.output_dir, filename)
        
        with open(file_path, "w") as f:
            json.dump(payload, f, indent=4)
            
        return file_path

if __name__ == "__main__":
    builder = LiquidationBundleBuilder()
    print(f"Enriched bundle created at: {builder.build('ENRICHED-CONTEXT-001')}")
