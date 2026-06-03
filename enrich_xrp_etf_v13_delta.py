import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("/home/dalien/Refinery-01/vault/datasets/xrp-etf-temporal-intel-v1")
LATEST = BASE / "latest.json"
LATEST_INTEL = BASE / "latest_intel.json"
HISTORY = BASE / "history.jsonl"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_current():
    if not LATEST_INTEL.exists():
        raise SystemExit(f"missing source: {LATEST_INTEL}")
    return json.loads(LATEST_INTEL.read_text())


def load_previous_enriched(current):
    if not HISTORY.exists():
        return None

    current_timestamp = current.get("timestamp")
    current_enriched_at = current.get("enriched_at")

    rows = []
    with HISTORY.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue

    for row in reversed(rows):
        # Ignore current record if v1.2 enricher already appended it.
        if current_timestamp and row.get("timestamp") == current_timestamp:
            continue
        if current_enriched_at and row.get("enriched_at") == current_enriched_at:
            continue

        # Only compare against structured enriched records.
        if row.get("version") in {"1.2.0", "1.3.0"} or "etf_flow_layer" in row:
            return row

    return None


def pct_delta(current, previous):
    if current is None or previous in (None, 0):
        return None
    try:
        return round(((current - previous) / previous) * 100, 4)
    except Exception:
        return None


def numeric_delta(current, previous):
    if current is None or previous is None:
        return None
    try:
        return current - previous
    except Exception:
        return None


def classify_flow_direction(aum_delta, holdings_delta):
    if aum_delta is None and holdings_delta is None:
        return "baseline"

    positive = any(x is not None and x > 0 for x in [aum_delta, holdings_delta])
    negative = any(x is not None and x < 0 for x in [aum_delta, holdings_delta])

    if positive and not negative:
        return "inflow"
    if negative and not positive:
        return "outflow"
    if positive and negative:
        return "mixed"
    return "flat"


def classify_flow_strength(aum_delta_pct, holdings_delta_pct):
    values = [abs(x) for x in [aum_delta_pct, holdings_delta_pct] if isinstance(x, (int, float))]

    if not values:
        return "baseline"

    strongest = max(values)

    if strongest >= 5:
        return "high"
    if strongest >= 1:
        return "moderate"
    if strongest > 0:
        return "low"
    return "flat"


def source_status_changes(current, previous):
    if not previous:
        return []

    cur = current.get("source_status", {})
    prev = previous.get("source_status", {})
    changes = []

    for key, cur_status in cur.items():
        prev_status = prev.get(key, {})
        cur_ok = cur_status.get("ok")
        prev_ok = prev_status.get("ok")

        if cur_ok != prev_ok:
            changes.append({
                "layer": key,
                "previous_ok": prev_ok,
                "current_ok": cur_ok,
                "change_type": "source_status_changed"
            })

    return changes


def market_flow_correlation_hint(current, flow_direction):
    market = current.get("xrp_market_layer", {})
    market_state = market.get("market_state") or current.get("market_state")

    if flow_direction == "inflow" and market_state == "risk_off":
        return "possible_contrarian_accumulation_watch"
    if flow_direction == "outflow" and market_state == "risk_off":
        return "risk_off_outflow_confirmation_watch"
    if flow_direction == "inflow" and market_state == "risk_on":
        return "risk_on_flow_confirmation_watch"
    if flow_direction == "flat":
        return "no_material_flow_change_detected"
    if flow_direction == "baseline":
        return "baseline_established_no_prior_enriched_record"
    return "watch_for_market_flow_confirmation"


def priority_from_layers(flow_strength, readiness_delta, source_changes):
    if source_changes:
        return "high"
    if isinstance(readiness_delta, (int, float)) and abs(readiness_delta) >= 10:
        return "high"
    if flow_strength in {"high", "moderate"}:
        return "medium"
    return "low"


def main():
    current = load_current()
    previous = load_previous_enriched(current)

    cur_flow = current.get("etf_flow_layer", {})
    prev_flow = previous.get("etf_flow_layer", {}) if previous else {}

    cur_aum = cur_flow.get("aggregate_aum_usd")
    prev_aum = prev_flow.get("aggregate_aum_usd")

    cur_holdings = cur_flow.get("aggregate_xrp_holdings")
    prev_holdings = prev_flow.get("aggregate_xrp_holdings")

    aum_delta = numeric_delta(cur_aum, prev_aum)
    holdings_delta = numeric_delta(cur_holdings, prev_holdings)

    aum_delta_pct = pct_delta(cur_aum, prev_aum)
    holdings_delta_pct = pct_delta(cur_holdings, prev_holdings)

    flow_direction = classify_flow_direction(aum_delta, holdings_delta)
    flow_strength = classify_flow_strength(aum_delta_pct, holdings_delta_pct)

    cur_readiness = current.get("etf_readiness_score")
    prev_readiness = previous.get("etf_readiness_score") if previous else None
    readiness_delta = numeric_delta(cur_readiness, prev_readiness)

    source_changes = source_status_changes(current, previous)

    current["version"] = "1.3.0"
    current["delta_enriched_at"] = now_iso()

    current["etf_flow_delta_layer"] = {
        "comparison_state": "delta_available" if previous else "baseline",
        "previous_timestamp": previous.get("timestamp") if previous else None,
        "current_timestamp": current.get("timestamp"),
        "aum_usd_current": cur_aum,
        "aum_usd_previous": prev_aum,
        "aum_usd_delta": aum_delta,
        "aum_usd_delta_pct": aum_delta_pct,
        "xrp_holdings_current": cur_holdings,
        "xrp_holdings_previous": prev_holdings,
        "xrp_holdings_delta": holdings_delta,
        "xrp_holdings_delta_pct": holdings_delta_pct,
        "flow_direction": flow_direction,
        "flow_strength": flow_strength,
        "interpretation": "Temporal delta layer compares current XRP ETF/ETP AUM and holdings context against the prior enriched paid payload."
    }

    current["readiness_delta_layer"] = {
        "score_current": cur_readiness,
        "score_previous": prev_readiness,
        "score_delta": readiness_delta,
        "state_current": current.get("composite_readiness_layer", {}).get("state"),
        "state_previous": previous.get("composite_readiness_layer", {}).get("state") if previous else None,
        "interpretation": "Tracks whether observable ETF readiness context is strengthening, weakening, or unchanged."
    }

    current["source_change_layer"] = {
        "change_count": len(source_changes),
        "changes": source_changes,
        "interpretation": "Flags source availability changes that may affect confidence or agent action."
    }

    current["market_flow_correlation_layer"] = {
        "market_state": current.get("market_state"),
        "flow_direction": flow_direction,
        "flow_strength": flow_strength,
        "correlation_hint": market_flow_correlation_hint(current, flow_direction),
        "interpretation": "Lightweight heuristic only. Does not assert causation between XRP price movement and ETF/ETP flow."
    }

    current["agent_action_priority"] = priority_from_layers(flow_strength, readiness_delta, source_changes)

    base_hint = current.get("agent_action_hint") or "continue_monitoring"
    current["agent_action_hint"] = (
        f"{base_hint}; "
        f"priority={current['agent_action_priority']}; "
        f"flow_direction={flow_direction}; "
        f"flow_strength={flow_strength}"
    )

    decision = current.get("agent_decision_summary", {})
    decision["delta_observation"] = {
        "flow_direction": flow_direction,
        "flow_strength": flow_strength,
        "aum_usd_delta": aum_delta,
        "xrp_holdings_delta": holdings_delta,
        "readiness_score_delta": readiness_delta,
        "source_change_count": len(source_changes)
    }
    decision["recommended_agent_priority"] = current["agent_action_priority"]
    current["agent_decision_summary"] = decision

    LATEST.write_text(json.dumps(current, indent=2) + "\n")
    LATEST_INTEL.write_text(json.dumps(current, indent=2) + "\n")

    with HISTORY.open("a") as f:
        f.write(json.dumps(current, separators=(",", ":")) + "\n")

    print("enriched XRP ETF v1.3 delta payload")
    print("version:", current.get("version"))
    print("flow_direction:", flow_direction)
    print("flow_strength:", flow_strength)
    print("agent_action_priority:", current["agent_action_priority"])


if __name__ == "__main__":
    main()
