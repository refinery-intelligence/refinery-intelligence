try:
    from .base_adapter import BaseAdapter
    from .shared_normalizer import calculate_risk_band, calculate_risk_score, get_base_record_template
except (ImportError, ValueError):
    from base_adapter import BaseAdapter
    from shared_normalizer import calculate_risk_band, calculate_risk_score, get_base_record_template

class CompoundAdapter(BaseAdapter):
    def fetch_raw_data(self):
        # Mock raw data from a hypothetical Compound API or RPC call
        return [
            {
                "account": "0x456",
                "asset": "WBTC",
                "collateral": "cWBTC",
                "debt": "USDT",
                "health": "1.25",
                "collateralFactor": "0.7",
                "incentive": "0.08",
                "sizeUsd": "120000.0",
                "liqPrice": "35000.0",
                "refPrice": "42000.0"
            }
        ]

    def normalize(self, raw):
        hf = float(raw["health"])
        record = get_base_record_template()
        record.update({
            "position_id": f"compound-{raw['account']}",
            "protocol": "Compound-V3",
            "chain": "ethereum",
            "asset": raw["asset"],
            "collateral_asset": raw["collateral"],
            "debt_asset": raw["debt"],
            "health_factor": hf,
            "liquidation_threshold": float(raw["collateralFactor"]),
            "liquidation_bonus": float(raw["incentive"]),
            "position_size_usd": float(raw["sizeUsd"]),
            "liquidation_price": float(raw["liqPrice"]),
            "reference_price": float(raw["refPrice"]),
            "risk_band": calculate_risk_band(hf),
            "risk_score": calculate_risk_score(hf),
            "source": "compound_api_mock"
        })
        return record
