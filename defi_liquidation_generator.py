import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from oracle_divergence_detector import generate_oracle_divergence
from composite_signal_engine import build_composite_signals
from escalation_engine import build_escalation_events
from confidence_engine import calculate_confidence
from temporal_engine import analyze_temporal_state

OUT = Path("vault/datasets/defi-liquidation-intel-v1/bundle.json")
HISTORY = Path("vault/datasets/defi-liquidation-intel-v1/history.json")

HISTORY_ARCHIVE = Path("vault/datasets/defi-liquidation-intel-v1/history_archive.jsonl")

PROTOCOLS_URL = "https://api.llama.fi/protocols"

TARGETS = {
    "aave": ["Ethereum", "Arbitrum", "Base"],
    "compound-finance": ["Ethereum"],
    "morpho-blue": ["Ethereum", "Base"],
    "makerdao": ["Ethereum"],
    "spark": ["Ethereum"],
    "curve-dex": ["Ethereum", "Arbitrum"],
    "liquity": ["Ethereum"]
}


def fetch_json(url):
    try:
        with urllib.request.urlopen(url, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print("FETCH ERROR:", e)
        print("Using empty protocol list fallback.")
        return []

def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def load_history():
    if not HISTORY.exists():
        return {}

    try:
        return json.loads(HISTORY.read_text())
    except Exception:
        return {}


def save_history(history):
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    HISTORY.write_text(json.dumps(history, indent=2))

def append_history_archive(bundle):

    HISTORY_ARCHIVE.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": bundle.get("updated_at"),
        "bundle_id": bundle.get("bundle_id"),
        "version": bundle.get("version"),
        "signal_count": len(bundle.get("signals", [])),
        "signals": bundle.get("signals", [])
    }

    with open(HISTORY_ARCHIVE, "a") as f:
        f.write(json.dumps(record) + "\n")


def temporal_delta(signal, history):
    old = history.get(signal["signal_id"])

    if not old:
        return {
            "previous_risk_score": None,
            "risk_delta": None,
            "trend": "new_signal",
            "anomaly": False
        }

    previous = old.get("risk_score", 0)
    current = signal["risk_score"]

    delta = round(current - previous, 3)

    if delta >= 0.15:
        trend = "risk_accelerating"
        anomaly = True
    elif delta <= -0.15:
        trend = "risk_cooling"
        anomaly = False
    elif delta > 0:
        trend = "risk_rising"
        anomaly = False
    elif delta < 0:
        trend = "risk_falling"
        anomaly = False
    else:
        trend = "stable"
        anomaly = False

    return {
        "previous_risk_score": previous,
        "risk_delta": delta,
        "trend": trend,
        "anomaly": anomaly
    }


def risk_score(tvl, change_1d, change_7d):
    tvl_factor = 0.25 if tvl and tvl > 1_000_000_000 else 0.15

    drop_1d = abs(min(change_1d or 0, 0)) / 6
    drop_7d = abs(min(change_7d or 0, 0)) / 15

    return round(clamp(tvl_factor + drop_1d + drop_7d), 3)


def urgency(score):
    if score >= 0.75:
        return "high"

    if score >= 0.45:
        return "medium"

    return "low"


def main():
    protocols = fetch_json(PROTOCOLS_URL)

    signals = []
    signals.extend(generate_oracle_divergence())
    history = load_history()
    new_history = {}

    for p in protocols:
        slug = p.get("slug")

        if slug not in TARGETS:
            continue

        tvl = p.get("tvl") or 0
        change_1d = p.get("change_1d") or 0
        change_7d = p.get("change_7d") or 0

        score = risk_score(tvl, change_1d, change_7d)

        for chain in TARGETS[slug]:

            signal = {
                "signal_id": f"{slug}_{chain.lower()}_liquidation_pressure",
                "protocol": p.get("name", slug),
                "chain": chain,
                "asset": "multi_collateral",
                "signal_type": "liquidation_pressure_proxy",
                "tvl_usd": round(tvl, 2),
                "change_1d_pct": change_1d,
                "change_7d_pct": change_7d,
                "risk_score": score,
                "confidence": 0.61,
                "temporal_urgency": urgency(score),
                "agent_action_hint": "prioritize deeper protocol-specific health-factor and oracle checks when urgency is medium_or_high",
                "value_reason": "Compresses protocol TVL drawdown and market stress into a liquidation-pressure proxy signal."
            }

            signal["temporal"] = temporal_delta(signal, history)

            signals.append(signal)

            new_history[signal["signal_id"]] = {
                "risk_score": signal["risk_score"],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
           
    composite_signals = build_composite_signals(signals)

    signals.extend(composite_signals)
    escalation_events = build_escalation_events(signals)

    signals.extend(escalation_events)
    confidence_data = calculate_confidence(
         oracle_divergence=7.5,
         liquidation_pressure=82,
         escalation_level=4,
         persistence_minutes=45
    )

    temporal_state = analyze_temporal_state(
        current_score=0.62,
        previous_score=0.41,
        active_minutes=75

    )

    bundle = {
        "bundle_id": "defi-liquidation-intel-v1",
        "version": "1.1.0",
        "confidence": confidence_data["confidence"],
        "signal_strength": confidence_data["signal_strength"],
        "temporal_state": temporal_state,
        "category": "defi_temporal_intelligence",
        "price_xrp": 0.15,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "description": "Agent-ready liquidation intelligence bundle focused on compressed decision advantage for DeFi systems.",
        "agent_value_target": ">=30_percent_decision_advantage",
        "source_mode": "defillama_temporal_liquidation_proxy",
        "supported_chains": [
            "Ethereum",
            "Arbitrum",
            "Base"
        ],
        "signals": signals,
        "delivery": {
            "format": "json",
            "machine_readable": True,
            "human_ui_required": False
        }
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)

    OUT.write_text(json.dumps(bundle, indent=2))

    save_history(new_history)
    append_history_archive(bundle)
    print(f"Wrote {OUT} with {len(signals)} signals")


if __name__ == "__main__":
    main()
