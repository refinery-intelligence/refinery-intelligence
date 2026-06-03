from datetime import datetime, timezone

# Enriched mock records for DeFi liquidation intelligence
# Using UTC for consistent validation
now = datetime.now(timezone.utc).isoformat()

MOCK_RECORDS = [
    {
        "position_id": "eth-whale-001",
        "protocol": "Aave-V3",
        "chain": "ethereum",
        "asset": "ETH",
        "collateral_asset": "WSTETH",
        "debt_asset": "USDC",
        "health_factor": 1.05,
        "liquidation_threshold": 0.85,
        "liquidation_bonus": 0.05,
        "position_size_usd": 125000.00,
        "liquidation_price": 2100.50,
        "reference_price": 2205.10,
        "risk_band": "HIGH",
        "risk_score": 88,
        "timestamp": now,
        "source": "subgraph_mock",
        "confidence_score": 0.95,
        "anomaly_flags": [],
        "temporal_change_1h": -0.02,
        "temporal_change_24h": -0.15
    },
    {
        "position_id": "poly-yield-042",
        "protocol": "Compound-V3",
        "chain": "polygon",
        "asset": "MATIC",
        "collateral_asset": "WMATIC",
        "debt_asset": "USDT",
        "health_factor": 1.12,
        "liquidation_threshold": 0.80,
        "liquidation_bonus": 0.07,
        "position_size_usd": 45000.00,
        "liquidation_price": 0.65,
        "reference_price": 0.73,
        "risk_band": "MEDIUM",
        "risk_score": 52,
        "timestamp": now,
        "source": "rpc_mock",
        "confidence_score": 0.88,
        "anomaly_flags": ["low_liquidity_pool"],
        "temporal_change_1h": 0.01,
        "temporal_change_24h": -0.05
    },
    {
        "position_id": "spark-dai-999",
        "protocol": "Spark",
        "chain": "ethereum",
        "asset": "DAI",
        "collateral_asset": "RETH",
        "debt_asset": "DAI",
        "health_factor": 0.99,
        "liquidation_threshold": 0.90,
        "liquidation_bonus": 0.03,
        "position_size_usd": 1050000.00,
        "liquidation_price": 0.995,
        "reference_price": 1.001,
        "risk_band": "CRITICAL",
        "risk_score": 98,
        "timestamp": now,
        "source": "oracle_mock",
        "confidence_score": 0.99,
        "anomaly_flags": ["whale_position"],
        "temporal_change_1h": -0.05,
        "temporal_change_24h": -0.25
    }
]
