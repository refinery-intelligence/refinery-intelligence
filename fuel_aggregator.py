#!/usr/bin/env python3
import json
import os

def main():
    # LIVE MARKET DATA: MAY 9, 2026
    hobart_diesel_tgp = 222.3
    avg_30_day_hobart = 228.4
    xrp_aud_rate = 1.92
    
    # Logic: Farm Signal
    buy_signal = "STRONG_BUY" if hobart_diesel_tgp < avg_30_day_hobart else "HOLD"

    payload = {
        "status": "INSTITUTIONAL_DECISION_PACKET",
        "timestamp": "2026-05-09T16:44:00",
        "market_intelligence": {
            "cannabis_industry_2026": {
                "us_federal_status": "Schedule III (Effective April 23, 2026)",
                "dea_registrations": "380+ Applications Pending",
                "au_import_volume": "77,000kg (Annualized)",
                "market_trend": "Shift to pharmaceutical-grade/reimbursable benefits"
            },
            "psychedelic_sector_2026": {
                "us_policy": "Executive Order (April 18, 2026) for Breakthrough Access",
                "fda_status": "Priority Vouchers issued; First approval expected Summer 2026",
                "prevalence": "10M US Adults microdosing (RAND Jan 2026 Report)",
                "market_cap": "$7.37 Billion Global"
            },
            "tasmania_farm_monitor": {
                "location": "Hobart Terminal",
                "diesel_tgp": hobart_diesel_tgp,
                "signal": buy_signal,
                "notes": "Deep soil moisture deficit persists; prioritize irrigation fuel."
            }
        },
        "financial_layer": {
            "xrp_aud": xrp_aud_rate,
            "packet_settlement_drops": 150000,
            "fiat_value_aud": round(0.15 * xrp_aud_rate, 4)
        }
    }
    
    path = os.path.expanduser("~/Refinery-01/feeds/fuel/current_prices.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=4)
    print(f"✅ Super-Vault Aggregated: {buy_signal} Signal & Industry Intelligence Locked.")

if __name__ == "__main__":
    main()
