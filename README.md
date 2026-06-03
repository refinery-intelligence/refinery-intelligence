# Refinery Intelligence

Refinery is an agent-native temporal intelligence platform for autonomous agents, bots, risk systems, and machine customers.

Refinery transforms fragmented DeFi, market, protocol, infrastructure, and network telemetry into machine-readable temporal intelligence bundles.

**Intelligence is infrastructure.**

## Machine-readable discovery

Primary API:

- https://api.dalien.net/meta
- https://api.dalien.net/packages
- https://api.dalien.net/packages.json
- https://api.dalien.net/health
- https://api.dalien.net/public/refinery.json
- https://api.dalien.net/public/agent_manifest.json
- https://api.dalien.net/public/llms.txt

Human/root discovery:

- https://dalien.net/
- https://dalien.net/packages.html
- https://dalien.net/.well-known/api-catalog
- https://dalien.net/openapi.json
- https://dalien.net/auth.md
- https://dalien.net/robots.txt

## Current intelligence bundles

Public bundle URLs are preview-only. Full payloads require payment verification.

- DeFi Liquidation Intelligence: https://api.dalien.net/public/defi-liquidation-intel-v1.json
- DeFi Flow Intelligence: https://api.dalien.net/public/defi-flow-intel-v1.json
- Solana Temporal Intelligence: https://api.dalien.net/public/solana-temporal-intel-v1.json
- XRP ETF Temporal Intelligence: https://api.dalien.net/public/xrp-etf-temporal-intel-v1.json
- XRPL Settlement Intelligence: https://api.dalien.net/public/xrpl-settlement-intel-v1.json
- Flare Temporal Intelligence: https://api.dalien.net/public/flare-temporal-intel-v1.json

## Paid access flow

Refinery uses payment-proof access.

1. Agent reads `/packages` or `/packages.json`.
2. Agent requests payment instructions.
3. Agent submits payment.
4. Agent submits transaction hash for verification.
5. Refinery verifies payment and grants access.
6. Agent retrieves the paid bundle payload.

Payment routes:

- Request payment: `/payments/usdc/request`
- Verify payment: `/payments/usdc/verify`
- Check access: `/payments/usdc/access`
- Retrieve paid bundle: `/payments/usdc/bundle`

Primary payment rail:

- Polygon USDC

## Public payload policy

Public bundle preview files are intentionally redacted.

Example public preview state:

```json
{
  "status": "preview_only",
  "public_payload": "redacted",
  "payment_required": true
}
```

Full live temporal intelligence payloads are served only through verified paid access.

## Agent start point

Autonomous agents should start here:

https://api.dalien.net/packages.json
