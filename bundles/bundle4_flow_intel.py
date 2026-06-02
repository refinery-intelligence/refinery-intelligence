import requests
import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path("/home/dalien/Refinery-01")
PUBLIC_PREVIEW_PATH = BASE_DIR / "public/defi-flow-intel-v1.json"
HISTORY_PATH = BASE_DIR / "data/defi-flow-intel-history.jsonl"
VAULT_OUTPUT_PATH = BASE_DIR / "vault/datasets/defi-flow-intel-v1/latest.json"
PRIVATE_INTEL_PATH = BASE_DIR / "vault/datasets/defi-flow-intel-v1/latest_intel.json"

SOURCES = {
    "stablecoins": "https://stablecoins.llama.fi/stablecoins?includePrices=true",
    "chains": "https://api.llama.fi/chains",
    "protocols": "https://api.llama.fi/protocols",
    "dex_volumes": "https://api.llama.fi/overview/dexs",
    "fees": "https://api.llama.fi/overview/fees",
    "yields": "https://yields.llama.fi/pools"
}


def safe_fetch(name, url):
    try:
        r = requests.get(url, timeout=25)
        r.raise_for_status()
        return {"ok": True, "name": name, "data": r.json()}
    except Exception as e:
        return {"ok": False, "name": name, "error": str(e), "data": None}


def top_stablecoins(data):
    chains = data.get("chains", [])
    rows = []

    for chain in chains:
        total = chain.get("totalCirculatingUSD", {}).get("peggedUSD", 0)
        if total and total > 0:
            rows.append({
                "chain": chain.get("name"),
                "stablecoin_supply_usd": round(total, 2)
            })

    return sorted(rows, key=lambda x: x["stablecoin_supply_usd"], reverse=True)[:10]


def top_chains(data):
    rows = []

    for chain in data:
        tvl = chain.get("tvl", 0)
        if tvl and tvl > 0:
            rows.append({
                "chain": chain.get("name"),
                "tvl_usd": round(tvl, 2)
            })

    return sorted(rows, key=lambda x: x["tvl_usd"], reverse=True)[:10]


def top_protocols(data):
    rows = []

    for p in data:
        tvl = p.get("tvl", 0)
        if tvl and tvl > 0:
            rows.append({
                "protocol": p.get("name"),
                "chain": p.get("chain"),
                "tvl_usd": round(tvl, 2)
            })

    return sorted(rows, key=lambda x: x["tvl_usd"], reverse=True)[:10]


def top_dex_volumes(data):
    protocols = data.get("protocols", [])
    rows = []

    for p in protocols:
        volume = p.get("total24h") or p.get("dailyVolume") or 0
        if volume and volume > 0:
            rows.append({
                "protocol": p.get("name"),
                "category": p.get("category"),
                "volume_24h_usd": round(volume, 2)
            })

    return sorted(rows, key=lambda x: x["volume_24h_usd"], reverse=True)[:10]


def top_fees(data):
    protocols = data.get("protocols", [])
    rows = []

    for p in protocols:
        fees = p.get("total24h") or p.get("dailyFees") or 0
        if fees and fees > 0:
            rows.append({
                "protocol": p.get("name"),
                "category": p.get("category"),
                "fees_24h_usd": round(fees, 2)
            })

    return sorted(rows, key=lambda x: x["fees_24h_usd"], reverse=True)[:10]


def top_yields(data):
    pools = data.get("data", [])
    rows = []

    for p in pools:
        apy = p.get("apy", 0)
        tvl = p.get("tvlUsd", 0)

        if apy and tvl and tvl > 1000000:
            rows.append({
                "project": p.get("project"),
                "chain": p.get("chain"),
                "symbol": p.get("symbol"),
                "apy": round(apy, 2),
                "tvl_usd": round(tvl, 2)
            })

    return sorted(rows, key=lambda x: x["tvl_usd"], reverse=True)[:10]


def concentration_score(rows, key):
    if not rows:
        return 0

    total = sum(r.get(key, 0) for r in rows)
    if total <= 0:
        return 0

    top_3 = sum(r.get(key, 0) for r in rows[:3])
    return round(top_3 / total, 4)


def synthesize(signals):
    stable_score = concentration_score(
        signals.get("stablecoin_liquidity_concentration", []),
        "stablecoin_supply_usd"
    )

    tvl_score = concentration_score(
        signals.get("chain_tvl_concentration", []),
        "tvl_usd"
    )

    protocol_score = concentration_score(
        signals.get("protocol_tvl_concentration", []),
        "tvl_usd"
    )

    avg_concentration = round(
        (stable_score + tvl_score + protocol_score) / 3,
        4
    )

    if avg_concentration >= 0.75:
        condition = "highly_concentrated"
    elif avg_concentration >= 0.55:
        condition = "moderately_concentrated"
    else:
        condition = "distributed"

    available_layers = len([v for v in signals.values() if v])
    confidence = round(min(1.0, available_layers / 6), 2)

    return {
        "market_structure": condition,
        "liquidity_concentration_score": avg_concentration,
        "available_signal_layers": available_layers,
        "confidence_score": confidence,
        "agent_decision_summary": (
            "Bundle 4 aggregates stablecoin supply, TVL, protocol concentration, "
            "DEX activity, fees, and yield context to help autonomous agents assess "
            "where DeFi liquidity, activity, and opportunity are concentrated."
        )
    }


def build_bundle():
    fetched = {
        name: safe_fetch(name, url)
        for name, url in SOURCES.items()
    }

    signals = {
        "stablecoin_liquidity_concentration": [],
        "chain_tvl_concentration": [],
        "protocol_tvl_concentration": [],
        "dex_volume_concentration": [],
        "fee_generation_concentration": [],
        "yield_opportunity_context": []
    }

    if fetched["stablecoins"]["ok"]:
        signals["stablecoin_liquidity_concentration"] = top_stablecoins(fetched["stablecoins"]["data"])

    if fetched["chains"]["ok"]:
        signals["chain_tvl_concentration"] = top_chains(fetched["chains"]["data"])

    if fetched["protocols"]["ok"]:
        signals["protocol_tvl_concentration"] = top_protocols(fetched["protocols"]["data"])

    if fetched["dex_volumes"]["ok"]:
        signals["dex_volume_concentration"] = top_dex_volumes(fetched["dex_volumes"]["data"])

    if fetched["fees"]["ok"]:
        signals["fee_generation_concentration"] = top_fees(fetched["fees"]["data"])

    if fetched["yields"]["ok"]:
        signals["yield_opportunity_context"] = top_yields(fetched["yields"]["data"])

    source_status = {
        name: {
            "ok": result["ok"],
            "error": result.get("error")
        }
        for name, result in fetched.items()
    }

    synthesis = synthesize(signals)

    return {
        "package_id": "defi-flow-intel-v1",
        "bundle_number": 4,
        "bundle_name": "DeFi Flow Intelligence",
        "version": "1.0.0",
        "status": "live",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": list(SOURCES.keys()),
        "source_status": source_status,
        "architecture": [
            "fetch",
            "normalize",
            "store",
            "synthesize",
            "output"
        ],
        "signal_layer": signals,
        "intelligence_layer": synthesis,
        "agent_summary": {
            "purpose": "Aggregate DeFi liquidity, activity, fee, and yield flow intelligence into one agent-readable temporal bundle.",
            "interpretation": "Agents can use this bundle to assess where liquidity, activity, revenue, and opportunity are concentrating across DeFi ecosystems.",
            "target_user": "autonomous agents, trading bots, risk systems, routing systems, liquidity monitors"
        }
    }


def public_preview():
    return {
        "bundle_id": "defi-flow-intel-v1",
        "status": "preview_only",
        "access": "paid_full_payload_required",
        "public_payload": "redacted",
        "payment_required": True,
        "message": "This is a public discovery preview only. Full temporal intelligence is available only after payment verification.",
        "paid_access_flow": {
            "step_1": "Read package metadata from /packages or /packages.json",
            "step_2": "Submit required payment",
            "step_3": "Submit transaction hash for verification",
            "step_4": "Receive full bundle payload after verified payment"
        }
    }


def store(bundle):
    PUBLIC_PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    VAULT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PRIVATE_INTEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(PUBLIC_PREVIEW_PATH, "w") as f:
        json.dump(public_preview(), f, indent=2)

    with open(VAULT_OUTPUT_PATH, "w") as f:
        json.dump(bundle, f, indent=2)

    with open(PRIVATE_INTEL_PATH, "w") as f:
        json.dump(bundle, f, indent=2)

    with open(HISTORY_PATH, "a") as f:
        f.write(json.dumps(bundle) + "\n")

def main():
    bundle = build_bundle()
    store(bundle)
    print(json.dumps(bundle, indent=2))


if __name__ == "__main__":
    main()
