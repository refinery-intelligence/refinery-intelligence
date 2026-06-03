from datetime import datetime, timezone

def calculate_risk_band(health_factor):
    """
    Standard logic for mapping health factor to risk band.
    """
    if health_factor < 1.0:
        return "CRITICAL"
    elif health_factor < 1.1:
        return "HIGH"
    elif health_factor < 1.5:
        return "MEDIUM"
    else:
        return "LOW"

def calculate_risk_score(health_factor):
    """
    Standard logic for mapping health factor to a 0-100 risk score.
    """
    if health_factor <= 1.0:
        return 100
    if health_factor >= 2.0:
        return 0
    # Linear scale between 1.0 and 2.0
    return int((2.0 - health_factor) * 100)

def get_base_record_template():
    """
    Returns a template with common fields initialized.
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "confidence_score": 1.0,
        "anomaly_flags": [],
        "temporal_change_1h": 0.0,
        "temporal_change_24h": 0.0
    }

def deduplicate_records(records):
    """
    Removes records with duplicate position_id.
    """
    seen = set()
    unique = []
    for r in records:
        pid = r.get("position_id")
        if pid and pid not in seen:
            seen.add(pid)
            unique.append(r)
    return unique
