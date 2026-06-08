# Flare v1.2 Source Audit

Goal:
Upgrade flare-temporal-intel-v1 from v1.1 to v1.2 by auditing Flare-native data sources before code changes.

Scope:
- FTSO oracle feed source discovery
- FAssets / FXRP source discovery
- No code patch yet
- No registry or package metadata changes yet
- Observable-only claims

Current Flare v1.1 live layers:
- Flare RPC latency
- block progression
- block velocity
- FLR market state
- FLR price momentum
- Flare DeFi TVL context
- rolling latency baseline
- source_status
- intelligence_quality

Reserved layers:
- FTSO
- FAssets / FXRP

FTSO audit questions:
1. Which FTSOv2 feeds can be read from Flare mainnet?
2. What is the best public read method?
3. Can feed value, decimals, timestamp, and staleness be measured?
4. Can FLR/USD, XRP/USD, BTC/USD, and ETH/USD be tracked?
5. Can FTSO values be compared against CoinGecko references?
6. What failure states should be detected?

FAssets audit questions:
1. Which official FAssets contracts or APIs expose FXRP state?
2. Can minting state be read?
3. Can redemption state be read?
4. Can active agents or agent capacity be read?
5. Can collateral ratio, minting fee, redemption fee, or liquidation threshold be read?
6. Can mint/redeem events be monitored without private infrastructure?
7. Should FAssets remain inside the Flare bundle or become fassets-temporal-intel-v1?

Guardrails:
- Do not claim FTSO live unless data is actually fetched.
- Do not claim FAssets live unless data is actually fetched.
- Do not claim adoption, approval, institutional activity, or official readiness.
- Use live, partial_live, unavailable, or placeholder source states.
- Prefer official Flare docs, official contracts, and public RPC reads.
