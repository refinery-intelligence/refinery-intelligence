def build_escalation_events(signals):

    escalation_events = []

    composite_signals = [
        s for s in signals
        if s.get("signal_type") == "composite_liquidation_risk"
    ]

    grouped = {}

    for signal in composite_signals:

        asset = signal.get("asset", "UNKNOWN")

        if asset not in grouped:
            grouped[asset] = []

        grouped[asset].append(signal)

    for asset, asset_signals in grouped.items():

        if len(asset_signals) < 2:
            continue

        avg_score = (
            sum(s.get("composite_score", 0) for s in asset_signals)
            / len(asset_signals)
        )

        urgency = "low"

        if avg_score >= 0.45:
            urgency = "medium"

        if avg_score >= 0.7:
            urgency = "high"

        escalation_events.append({
            "signal_type": "escalation_event",
            "asset": asset,
            "event_category": "cross_protocol_liquidation_risk",
            "supporting_signal_count": len(asset_signals),
            "average_composite_score": round(avg_score, 4),
            "temporal_urgency": urgency,
            "confidence": 0.91,
            "agent_action_hint": "prioritize active monitoring and liquidation-path analysis",
            "value_reason": "Multiple composite liquidation-risk signals detected simultaneously across protocols."
        })

    return escalation_events
