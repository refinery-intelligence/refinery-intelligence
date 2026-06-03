# Schema for Agent-Ready Liquidation Bundle

BUNDLE_METADATA_FIELDS = [
    "bundle_id",
    "bundle_type",
    "version",
    "generated_at",
    "record_count",
    "source_mode",
    "intended_consumer"
]

RECORD_FIELDS = [
    "position_id",
    "protocol",
    "chain",
    "asset",
    "collateral_asset",
    "debt_asset",
    "health_factor",
    "liquidation_threshold",
    "liquidation_bonus",
    "position_size_usd",
    "liquidation_price",
    "reference_price",
    "risk_band",
    "risk_score",
    "timestamp",
    "source",
    "confidence_score",
    "anomaly_flags",
    "temporal_change_1h",
    "temporal_change_24h"
]

RISK_BANDS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
MAX_STALENESS_SECONDS = 3600
