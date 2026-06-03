try:
    from .base_adapter import BaseAdapter
    from .shared_normalizer import calculate_risk_band, calculate_risk_score, get_base_record_template
except (ImportError, ValueError):
    from base_adapter import BaseAdapter
    from shared_normalizer import calculate_risk_band, calculate_risk_score, get_base_record_template

class AaveAdapter(BaseAdapter):
    def fetch_raw_data(self):
        # Mock raw data from a hypothetical Aave subgraph or API
        return [
            {
                "id": "aave-pos-1",
                "user": "0x123",
                "reserve": "ETH",
                "collateral": "WSTETH",
                "debt": "USDC",
                "healthFactor": "1.02",
                "liquidationThreshold": "0.85",
                "currentLiquidationBonus": "0.05",
                "totalValueUsd": "50000.0",
                "liquidationPrice": "2150.0",
                "marketPrice": "2200.0"
            }
        ]

    def normalize(self, raw):
        hf = float(raw["healthFactor"])
        record = get_base_record_template()
        record.update({
            "position_id": raw["id"],
            "protocol": "Aave-V3",
            "chain": "ethereum",
            "asset": raw["reserve"],
            "collateral_asset": raw["collateral"],
            "debt_asset": raw["debt"],
            "health_factor": hf,
            "liquidation_threshold": float(raw["liquidationThreshold"]),
            "liquidation_bonus": float(raw["currentLiquidationBonus"]),
            "position_size_usd": float(raw["totalValueUsd"]),
            "liquidation_price": float(raw["liquidationPrice"]),
            "reference_price": float(raw["marketPrice"]),
            "risk_band": calculate_risk_band(hf),
            "risk_score": calculate_risk_score(hf),
            "source": "aave_subgraph_mock"
        })
        return record
