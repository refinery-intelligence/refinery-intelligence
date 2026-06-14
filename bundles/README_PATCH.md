# Refinery public bundle-page patch

This package adds six generated static documentation pages without changing the live API,
payment flow, bundle generators, nginx, Cloudflare, systemd, or paid payloads.

## Apply

Copy the package contents into the root of the authoritative repository, preserving paths.

Then run:

```bash
python3 scripts/generate_bundle_pages.py --check
python3 scripts/generate_bundle_pages.py
git diff --check
git status --short
```

Review the diff before committing or deploying.

## Generated routes

- `/bundles/solana-temporal-intel-v1`
- `/bundles/defi-liquidation-intel-v1`
- `/bundles/defi-flow-intel-v1`
- `/bundles/flare-temporal-intel-v1`
- `/bundles/xrp-etf-temporal-intel-v1`
- `/bundles/xrpl-settlement-intel-v1`

## Important boundary

The public preview JSON remains intentionally minimal and redacted. The generated pages explain
bundle value and purchase mechanics without exposing paid signal values, detector thresholds,
weights, formulas, or full payload structure.

The canonical purchase request is:

```http
POST https://api.dalien.net/payments/usdc/request
Content-Type: application/json
```

This package does not deploy anything. Static route serving must be confirmed against the actual
dalien.net document root before production publication.
