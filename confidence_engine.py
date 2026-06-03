def calculate_confidence(
    oracle_divergence,
    liquidation_pressure,
    escalation_level,
    persistence_minutes
):
    """
    Refinery Confidence Engine v1

    Returns:
    - confidence score (0.0 → 1.0)
    - signal strength classification
    """

    oracle_weight = min(oracle_divergence / 10, 1.0)
    liquidation_weight = min(liquidation_pressure / 100, 1.0)
    escalation_weight = min(escalation_level / 5, 1.0)
    persistence_weight = min(persistence_minutes / 60, 1.0)

    confidence = (
        oracle_weight * 0.30 +
        liquidation_weight * 0.35 +
        escalation_weight * 0.20 +
        persistence_weight * 0.15
    )

    confidence = round(confidence, 3)

    if confidence >= 0.80:
        strength = "critical"
    elif confidence >= 0.60:
        strength = "high"
    elif confidence >= 0.40:
        strength = "moderate"
    else:
        strength = "low"

    return {
        "confidence": confidence,
        "signal_strength": strength
    }


if __name__ == "__main__":

    sample = calculate_confidence(
        oracle_divergence=7.5,
        liquidation_pressure=82,
        escalation_level=4,
        persistence_minutes=45
    )

    print(sample)
