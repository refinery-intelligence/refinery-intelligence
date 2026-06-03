def build_composite_signals(signals):

    composites = []

    oracle_signals = [
        s for s in signals
        if s.get("signal_type") == "oracle_divergence"
    ]

    liquidation_signals = [
        s for s in signals
        if s.get("signal_type") == "liquidation_pressure_proxy"
    ]

    for oracle in oracle_signals:

        oracle_divergence = oracle.get("divergence_pct", 0)

        for liquidation in liquidation_signals:

            risk_score = liquidation.get("risk_score", 0)

            composite_score = (
                (oracle_divergence * 0.35)
                + (risk_score * 100 * 0.65)
            ) / 100

            urgency = "low"

            if composite_score >= 0.45:
                urgency = "medium"

            if composite_score >= 0.7:
                urgency = "high"

            composites.append({
                "signal_type": "composite_liquidation_risk",
                "asset": oracle.get("asset"),
                "protocol": liquidation.get("protocol"),
                "chain": liquidation.get("chain"),
                "oracle_divergence_pct": oracle_divergence,
                "protocol_risk_score": risk_score,
                "composite_score": round(composite_score, 4),
                "temporal_urgency": urgency,
                "confidence": 0.84,
                "agent_action_hint": "prioritize liquidation monitoring during simultaneous oracle divergence and protocol stress",
                "value_reason": "Fuses multiple market stress dimensions into a composite liquidation-risk event."
            })

    return composites
