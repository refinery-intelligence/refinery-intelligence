import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RPC = "https://s1.ripple.com:51234/"

BASE = Path("vault/datasets/xrpl-settlement-intel-v1")
BUNDLE = BASE / "bundle.json"
LATEST = BASE / "latest.json"
LATEST_INTEL = BASE / "latest_intel.json"
HISTORY = BASE / "history.jsonl"

VERSION = "1.1.0"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def rpc_call(method, params=None, timeout=20):
    payload = {
        "method": method,
        "params": [params or {}]
    }

    req = urllib.request.Request(
        RPC,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )

    start = time.time()

    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode())

    latency = round(time.time() - start, 4)
    return data, latency


def classify_age(age):
    if age <= 2:
        return "fresh"
    if age <= 6:
        return "watch"
    return "stale"


def classify_load(load_factor):
    if load_factor <= 1.2:
        return "normal"
    if load_factor <= 2:
        return "elevated"
    return "congested"


def score_network(age, load_factor, object_hit_rate, successor_hit_rate, validated):
    score = 1.0

    if not validated:
        score -= 0.35

    if age > 2:
        score -= min(0.30, (age - 2) * 0.05)

    if load_factor > 1:
        score -= min(0.25, (load_factor - 1) * 0.10)

    if object_hit_rate is not None:
        score -= max(0, min(0.10, (0.90 - object_hit_rate)))

    if successor_hit_rate is not None:
        score -= max(0, min(0.10, (0.90 - successor_hit_rate)))

    return round(max(0, min(1, score)), 3)


def append_history(row):
    with HISTORY.open("a") as f:
        f.write(json.dumps(row) + "\n")


def load_previous():
    if not HISTORY.exists():
        return None

    try:
        with HISTORY.open() as f:
            lines = f.readlines()
        if not lines:
            return None
        return json.loads(lines[-1])
    except Exception:
        return None


def main():
    BASE.mkdir(parents=True, exist_ok=True)

    previous = load_previous()

    server_info, rpc_latency = rpc_call("server_info")
    result = server_info.get("result", {})
    info = result.get("info", {})

    ledger = info.get("validated_ledger", {})
    cache = info.get("cache", {})

    ledger_seq = ledger.get("seq")
    ledger_age = ledger.get("age")
    base_fee_xrp = ledger.get("base_fee_xrp")
    load_factor = info.get("load_factor", 1)
    validation_quorum = info.get("validation_quorum")
    complete_ledgers = info.get("complete_ledgers")
    network_id = info.get("network_id")
    validated = bool(result.get("validated"))

    object_hit_rate = cache.get("object_hit_rate")
    successor_hit_rate = cache.get("successor_hit_rate")

    ledger_delta = None
    seconds_since_previous = None
    ledgers_per_second = None

    if previous:
        prev_seq = previous.get("validated_ledger_seq")
        prev_ts = previous.get("timestamp_epoch")

        if prev_seq is not None and ledger_seq is not None:
            ledger_delta = ledger_seq - prev_seq

        if prev_ts is not None:
            seconds_since_previous = round(time.time() - prev_ts, 3)

        if ledger_delta is not None and seconds_since_previous and seconds_since_previous > 0:
            ledgers_per_second = round(ledger_delta / seconds_since_previous, 4)

    ledger_freshness = classify_age(ledger_age if ledger_age is not None else 999)
    load_state = classify_load(load_factor)
    network_health_score = score_network(
        ledger_age if ledger_age is not None else 999,
        load_factor,
        object_hit_rate,
        successor_hit_rate,
        validated
    )

    if network_health_score >= 0.85:
        network_state = "healthy"
    elif network_health_score >= 0.65:
        network_state = "watch"
    else:
        network_state = "degraded"

    if load_state == "congested" or ledger_freshness == "stale":
        congestion_state = "elevated"
    elif load_state == "elevated" or ledger_freshness == "watch":
        congestion_state = "watch"
    else:
        congestion_state = "normal"

    raw = {
        "timestamp": now_iso(),
        "timestamp_epoch": time.time(),
        "rpc_endpoint": RPC,
        "rpc_latency_seconds": rpc_latency,
        "validated": validated,
        "validated_ledger_seq": ledger_seq,
        "validated_ledger_age_seconds": ledger_age,
        "ledger_delta": ledger_delta,
        "seconds_since_previous": seconds_since_previous,
        "ledgers_per_second": ledgers_per_second,
        "base_fee_xrp": base_fee_xrp,
        "load_factor": load_factor,
        "validation_quorum": validation_quorum,
        "complete_ledgers": complete_ledgers,
        "network_id": network_id,
        "cache_object_hit_rate": object_hit_rate,
        "cache_successor_hit_rate": successor_hit_rate,
        "ledger_freshness": ledger_freshness,
        "load_state": load_state,
        "network_state": network_state,
        "network_health_score": network_health_score,
        "congestion_state": congestion_state
    }

    signals = [
        {
            "signal_type": "xrpl_validated_ledger_progression",
            "validated_ledger_seq": ledger_seq,
            "ledger_delta": ledger_delta,
            "ledgers_per_second": ledgers_per_second,
            "confidence": 0.88 if ledger_delta is not None else 0.72,
            "temporal_urgency": "low" if network_state == "healthy" else "moderate",
            "agent_action_hint": "use XRPL for settlement when ledger progression is fresh and stable",
            "value_reason": "Validated ledger progression indicates settlement continuity and network liveness."
        },
        {
            "signal_type": "xrpl_settlement_latency",
            "validated_ledger_age_seconds": ledger_age,
            "rpc_latency_seconds": rpc_latency,
            "ledger_freshness": ledger_freshness,
            "confidence": 0.86,
            "temporal_urgency": "low" if ledger_freshness == "fresh" else "moderate",
            "agent_action_hint": "prefer XRPL settlement while validated ledger age remains fresh",
            "value_reason": "Ledger age and RPC latency provide direct settlement freshness context for autonomous payment flows."
        },
        {
            "signal_type": "xrpl_payment_rail_health",
            "network_health_score": network_health_score,
            "network_state": network_state,
            "load_factor": load_factor,
            "load_state": load_state,
            "validation_quorum": validation_quorum,
            "confidence": 0.84,
            "temporal_urgency": "low" if network_state == "healthy" else "high",
            "agent_action_hint": "confirm rail health before routing high-value autonomous settlement operations",
            "value_reason": "Network health determines whether XRPL is suitable as a real-time machine payment rail."
        },
        {
            "signal_type": "xrpl_congestion_state",
            "congestion_state": congestion_state,
            "load_factor": load_factor,
            "ledger_freshness": ledger_freshness,
            "confidence": 0.81,
            "temporal_urgency": "low" if congestion_state == "normal" else "high",
            "agent_action_hint": "delay non-urgent settlement when congestion_state is elevated",
            "value_reason": "Congestion state helps agents avoid degraded execution windows."
        }
    ]

    latest_intel = {
        "bundle_id": "xrpl-settlement-intel-v1",
        "version": VERSION,
        "category": "xrpl_settlement_intelligence",
        "updated_at": raw["timestamp"],
        "supported_network": "XRPL",
        "source_type": "live_xrpl_validated_telemetry",
        "description": "Agent-native XRPL settlement intelligence derived from live validated ledger telemetry.",
        "confidence": network_health_score,
        "signal_strength": "high" if network_health_score >= 0.85 else "moderate" if network_health_score >= 0.65 else "low",
        "network_state": network_state,
        "congestion_state": congestion_state,
        "signals": signals,
        "delivery": {
            "format": "json",
            "machine_readable": True,
            "human_ui_required": False
        }
    }

    BUNDLE.write_text(json.dumps(latest_intel, indent=2))
    LATEST.write_text(json.dumps(raw, indent=2))
    LATEST_INTEL.write_text(json.dumps(latest_intel, indent=2))
    append_history(raw)

    print(f"Wrote {BUNDLE}")
    print(f"Wrote {LATEST}")
    print(f"Wrote {LATEST_INTEL}")
    print(f"Appended {HISTORY}")


if __name__ == "__main__":
    main()
