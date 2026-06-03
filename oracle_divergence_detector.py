import json
import urllib.request


BINANCE_URL = "https://api.binance.com/api/v3/ticker/price"
COINBASE_URL = "https://api.coinbase.com/v2/prices/{pair}/spot"

ASSETS = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD"
}


def fetch_binance_prices():
    try:
        with urllib.request.urlopen(BINANCE_URL, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        return {
            item["symbol"].replace("USDT", ""): float(item["price"])
            for item in data
            if item["symbol"] in ["BTCUSDT", "ETHUSDT"]
        }

    except Exception as e:
        print("BINANCE FETCH ERROR:", e)
        return {}


def fetch_coinbase_price(pair):
    try:
        url = COINBASE_URL.format(pair=pair)

        with urllib.request.urlopen(url, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        return float(data["data"]["amount"])

    except Exception as e:
        print("COINBASE FETCH ERROR:", e)
        return None


def generate_oracle_divergence():

    binance_prices = fetch_binance_prices()

    signals = []

    for asset, coinbase_pair in ASSETS.items():

        binance_price = binance_prices.get(asset)
        coinbase_price = fetch_coinbase_price(coinbase_pair)

        if not binance_price or not coinbase_price:
            continue

        divergence_pct = abs(
            (binance_price - coinbase_price)
            / binance_price
        ) * 100

        urgency = "low"

        if divergence_pct >= 0.5:
            urgency = "medium"

        if divergence_pct >= 1:
            urgency = "high"

        signals.append({
            "signal_id": f"{asset.lower()}_binance_coinbase_oracle_divergence",
            "signal_type": "oracle_divergence",
            "asset": asset,
            "primary_oracle": "Binance_Market",
            "secondary_oracle": "Coinbase_Spot",
            "primary_price": round(binance_price, 2),
            "secondary_price": round(coinbase_price, 2),
            "divergence_pct": round(divergence_pct, 4),
            "confidence": 0.82,
            "temporal_urgency": urgency,
            "agent_action_hint": "monitor liquidation sensitivity during cross-exchange oracle deviation",
            "value_reason": "Live cross-source oracle divergence may reveal temporary liquidation inefficiencies."
        })

    return signals
