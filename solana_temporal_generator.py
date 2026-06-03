import json
from pathlib import Path
from datetime import datetime, timezone

DATASET_DIR = Path("vault/datasets/solana-temporal-intel-v1")

HISTORY_FILE = DATASET_DIR / "history.jsonl"
LATEST_INTEL_FILE = DATASET_DIR / "latest_intel.json"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_history(limit=20):
    if not HISTORY_FILE.exists():
        return []

    lines = HISTORY_FILE.read_text().strip().splitlines()
    lines = lines[-limit:]

    records = []
    for line in lines:
        try:
            records.append(json.loads(line))
        except Exception:
            pass

    return records


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def classify_latency(avg_latency, max_latency):
    if max_latency >= 5:
        return "degraded"
    if avg_latency >= 2:
        return "elevated"
    return "normal"


def generate_intel(records):
    if len(records) < 2:
        return {
            "timestamp": now_iso(),
            "network": "solana",
            "status": "warming_up",
            "message": "Not enough Solana history yet to generate temporal intelligence."
        }

    first = records[0]
    latest = records[-1]

    first_time = parse_time(first["timestamp"])
    latest_time = parse_time(latest["timestamp"])

    elapsed_seconds = max((latest_time - first_time).total_seconds(), 1)

    slot_delta = latest["solana_current_slot"] - first["solana_current_slot"]
    slots_per_second = round(slot_delta / elapsed_seconds, 4)

    latencies = [r.get("rpc_latency_seconds", 0) for r in records]
    avg_latency = round(sum(latencies) / len(latencies), 4)
    max_latency = round(max(latencies), 4)
    latest_latency = round(latest.get("rpc_latency_seconds", 0), 4)

    latency_state = classify_latency(avg_latency, max_latency)

    anomaly_detected = False
    anomaly_type = None
    severity = "none"

    if max_latency >= 5:
        anomaly_detected = True
        anomaly_type = "rpc_latency_spike"
        severity = "moderate"

    if slots_per_second < 1.5:
        anomaly_detected = True
        anomaly_type = "slot_progression_slowdown"
        severity = "high"

    health_score = 1.0

    if avg_latency > 1:
        health_score -= 0.1
    if avg_latency > 2:
        health_score -= 0.2
    if max_latency >= 5:
        health_score -= 0.25
    if slots_per_second < 2:
        health_score -= 0.25

    health_score = round(max(0, min(1, health_score)), 3)

    if health_score >= 0.8:
        network_state = "healthy"
        agent_action_hint = "Solana network telemetry appears normal. Execution-sensitive agents may proceed with standard RPC caution."
    elif health_score >= 0.55:
        network_state = "watch"
        agent_action_hint = "Monitor Solana execution conditions. RPC latency or slot progression shows signs of instability."
    else:
        network_state = "stressed"
        agent_action_hint = "Use caution before execution-sensitive Solana actions. Consider alternate RPC routes or delayed execution."

    return {
        "timestamp": now_iso(),
        "network": "solana",
        "status": "active",
        "window_records": len(records),
        "window_seconds": round(elapsed_seconds, 2),
        "latest_slot": latest["solana_current_slot"],
        "slot_delta": slot_delta,
        "slots_per_second": slots_per_second,
        "latest_rpc_latency_seconds": latest_latency,
        "average_rpc_latency_seconds": avg_latency,
        "max_rpc_latency_seconds": max_latency,
        "latency_state": latency_state,
        "network_state": network_state,
        "health_score": health_score,
        "anomaly_detected": anomaly_detected,
        "anomaly_type": anomaly_type,
        "severity": severity,
        "agent_action_hint": agent_action_hint,
        "signal_layers": [
            "slot_progression",
            "slot_velocity",
            "rpc_latency",
            "rpc_latency_anomaly",
            "temporal_network_health"
        ]
    }


def main():
    records = load_history(limit=20)
    intel = generate_intel(records)

    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    with open(LATEST_INTEL_FILE, "w") as f:
        json.dump(intel, f, indent=2)

    print(json.dumps(intel, indent=2))


if __name__ == "__main__":
    main()
