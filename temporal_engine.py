def analyze_temporal_state(
    current_score,
    previous_score,
    active_minutes
):
    """
    Refinery Temporal Engine v1

    Detects:
    - persistence
    - acceleration
    - trend state
    """

    delta = current_score - previous_score

    if delta > 0.15:
        acceleration = "rapidly_worsening"
    elif delta > 0.05:
        acceleration = "worsening"
    elif delta < -0.15:
        acceleration = "rapidly_improving"
    elif delta < -0.05:
        acceleration = "improving"
    else:
        acceleration = "stable"

    if active_minutes >= 120:
        persistence = "very_high"
    elif active_minutes >= 60:
        persistence = "high"
    elif active_minutes >= 30:
        persistence = "moderate"
    else:
        persistence = "low"

    return {
        "risk_delta": round(delta, 3),
        "acceleration_state": acceleration,
        "persistence_strength": persistence,
        "signal_active_minutes": active_minutes
    }


if __name__ == "__main__":

    result = analyze_temporal_state(
        current_score=0.62,
        previous_score=0.41,
        active_minutes=75
    )

    print(result)
