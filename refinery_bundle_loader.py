"""Canonical paid-payload loader shared by payment delivery adapters."""

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DATASETS_DIR = BASE_DIR / "vault" / "datasets"

PREFERRED_PAYLOADS = {
    "solana-temporal-intel-v1": "latest_intel.json",
}


def load_bundle_payload(bundle_id: str) -> dict[str, Any]:
    """Load the canonical paid payload for an allowlisted bundle."""
    bundle_dir = DATASETS_DIR / bundle_id
    preferred_name = PREFERRED_PAYLOADS.get(bundle_id)

    if preferred_name and (bundle_dir / preferred_name).is_file():
        bundle_file = bundle_dir / preferred_name
    elif (bundle_dir / "latest.json").is_file():
        bundle_file = bundle_dir / "latest.json"
    elif (bundle_dir / "latest_intel.json").is_file():
        bundle_file = bundle_dir / "latest_intel.json"
    else:
        return {
            "access": False,
            "error": "bundle_not_found",
            "bundle_id": bundle_id,
        }

    try:
        with bundle_file.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "access": False,
            "error": "bundle_payload_unreadable",
            "bundle_id": bundle_id,
            "detail": type(exc).__name__,
        }

    return {
        "access": True,
        "bundle_id": bundle_id,
        "payload": payload,
    }
