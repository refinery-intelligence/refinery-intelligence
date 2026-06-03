import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("/home/dalien/Refinery-01/vault/datasets/xrp-etf-temporal-intel-v1")
LATEST = BASE / "latest.json"
LATEST_INTEL = BASE / "latest_intel.json"
HISTORY = BASE / "history.jsonl"

WATCHLIST_ISSUERS = [
    "Bitwise",
    "Franklin Templeton",
    "21Shares",
    "Canary",
    "Grayscale",
    "WisdomTree",
    "ProShares",
    "Volatility Shares",
    "REX-Osprey"
]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def signal_value(signals, signal_type, field):
    for s in signals or []:
        if s.get("type") == signal_type:
            return s.get(field)
    return None


def main():
    if not LATEST_INTEL.exists():
        raise SystemExit(f"missing source: {LATEST_INTEL}")

    data = json.loads(LATEST_INTEL.read_text())

    signals = data.get("signals", [])
    timestamp = data.get("timestamp") or now_iso()

    aum_usd = signal_value(signals, "xrp_etf_aum_detected", "value_usd")
    holdings_xrp = signal_value(signals, "xrp_etf_holdings_detected", "value_xrp")
    watchlist_depth = signal_value(signals, "issuer_watchlist_depth", "value") or 9

    # Keep old top-level values for backward compatibility.
    data["version"] = "1.2.0"
    data["timestamp"] = timestamp
    data["enriched_at"] = now_iso()

    data["source_status"] = {
        "xrp_market_layer": {
            "ok": True,
            "source": "existing_xrp_etf_generator",
            "error": None
        },
        "xrpl_network_layer": {
            "ok": True,
            "source": "existing_xrp_etf_generator",
            "error": None
        },
        "etf_registry_layer": {
            "ok": True,
            "source": "internal_watchlist",
            "error": None
        },
        "etf_flow_layer": {
            "ok": aum_usd is not None or holdings_xrp is not None,
            "source": "xrp-insights",
            "error": None
        },
        "issuer_activity_layer": {
            "ok": True,
            "source": "internal_watchlist",
            "error": None
        },
        "dtcc_readiness_layer": {
            "ok": False,
            "source": "dtcc_scaffold",
            "error": "direct_dtcc_live_feed_not_enabled"
        },
        "sec_filing_layer": {
            "ok": False,
            "source": "sec_scaffold",
            "error": "direct_sec_live_feed_not_enabled"
        }
    }

    data["xrp_market_layer"] = {
        "market_state": data.get("market_state"),
        "risk_state": data.get("risk_state"),
        "risk_score": data.get("risk_score"),
        "source": "existing_xrp_etf_generator",
        "source_status": data["source_status"]["xrp_market_layer"],
        "interpretation": "XRP market state derived by the existing XRP ETF temporal generator."
    }

    data["xrpl_network_layer"] = {
        "source": "existing_xrp_etf_generator",
        "source_status": data["source_status"]["xrpl_network_layer"],
        "network_state": "live_observed",
        "interpretation": "XRPL ledger and RPC telemetry are included in the generator summary and tracked over time."
    }

    data["etf_registry_layer"] = {
        "source": "internal_watchlist",
        "source_status": data["source_status"]["etf_registry_layer"],
        "watchlist_count": watchlist_depth,
        "issuers": WATCHLIST_ISSUERS,
        "interpretation": "Tracks XRP ETF/ETP issuer/product candidates without asserting approval or launch."
    }

    data["etf_flow_layer"] = {
        "source": "xrp-insights",
        "source_status": data["source_status"]["etf_flow_layer"],
        "flow_state": data.get("flow_state"),
        "aggregate_aum_usd": aum_usd,
        "aggregate_xrp_holdings": holdings_xrp,
        "tracked_product_count": 7 if aum_usd is not None or holdings_xrp is not None else None,
        "interpretation": "AUM and holdings context detected for tracked XRP ETP/product layer."
    }

    data["issuer_activity_layer"] = {
        "source": "internal_watchlist",
        "source_status": data["source_status"]["issuer_activity_layer"],
        "issuer_count": len(WATCHLIST_ISSUERS),
        "active_watchlist_items": watchlist_depth,
        "issuer_watchlist": WATCHLIST_ISSUERS,
        "interpretation": "Issuer activity layer measures watchlist breadth only; it does not assert regulatory approval."
    }

    data["dtcc_readiness_layer"] = {
        "source": "dtcc_scaffold",
        "source_status": data["source_status"]["dtcc_readiness_layer"],
        "dtcc_readiness_state": "unknown",
        "dtcc_listing_claim": False,
        "interpretation": "DTCC readiness remains unknown until directly verified from an authoritative source."
    }

    data["sec_filing_layer"] = {
        "source": "sec_scaffold",
        "source_status": data["source_status"]["sec_filing_layer"],
        "filing_state": "unknown",
        "sec_approval_claim": False,
        "interpretation": "SEC filing/approval status is not claimed without direct authoritative verification."
    }

    data["claim_guardrail_layer"] = {
        "approval_claim": False,
        "guardrail_state": "clear",
        "claim_policy": "No approval, listing, launch, or DTCC-readiness claim is emitted without verified SEC, exchange, issuer, or DTCC evidence.",
        "blocked_claims": [
            "xrp_etf_approved",
            "spot_xrp_etf_approved",
            "dtcc_listing_confirmed",
            "issuer_launch_confirmed"
        ]
    }

    readiness_score = data.get("etf_readiness_score", 0)
    if readiness_score >= 75:
        readiness_state = "high"
    elif readiness_score >= 40:
        readiness_state = "watch"
    else:
        readiness_state = "early"

    data["composite_readiness_layer"] = {
        "score": readiness_score,
        "state": readiness_state,
        "components": [
            {
                "component": "issuer_watchlist_depth",
                "present": watchlist_depth is not None,
                "value": watchlist_depth
            },
            {
                "component": "aum_holdings_layer",
                "present": aum_usd is not None or holdings_xrp is not None,
                "aum_usd": aum_usd,
                "xrp_holdings": holdings_xrp
            },
            {
                "component": "sec_filing_layer",
                "present": False,
                "reason": "direct_sec_live_feed_not_enabled"
            },
            {
                "component": "dtcc_readiness_layer",
                "present": False,
                "reason": "direct_dtcc_live_feed_not_enabled"
            }
        ],
        "interpretation": "Readiness score measures observable ETF/ETP infrastructure and market context, not regulatory approval."
    }

    if readiness_state == "watch":
        agent_action_hint = "monitor_aum_holdings_delta_issuer_activity_and_authoritative_sec_dtcc_sources"
    else:
        agent_action_hint = "continue_monitoring_for_authoritative_readiness_changes"

    data["agent_action_hint"] = agent_action_hint

    data["agent_decision_summary"] = {
        "readiness_state": readiness_state,
        "risk_state": data.get("risk_state"),
        "primary_observation": "Live XRP ETF/ETP AUM and holdings context is active while SEC and DTCC authoritative layers remain unknown.",
        "recommended_agent_behavior": agent_action_hint,
        "do_not_infer": [
            "SEC approval",
            "DTCC listing",
            "issuer launch",
            "spot ETF approval"
        ]
    }

    LATEST.write_text(json.dumps(data, indent=2) + "\n")
    LATEST_INTEL.write_text(json.dumps(data, indent=2) + "\n")

    # Append enriched version to history so paid bundle history captures v1.2.0.
    with HISTORY.open("a") as f:
        f.write(json.dumps(data, separators=(",", ":")) + "\n")

    print("enriched XRP ETF private payload")
    print("version:", data.get("version"))
    print("latest:", LATEST)
    print("latest_intel:", LATEST_INTEL)
    print("history:", HISTORY)


if __name__ == "__main__":
    main()
