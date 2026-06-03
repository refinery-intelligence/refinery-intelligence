
## Payment Ledger Cleanup — 2026-06-03

The USDC payment ledgers were cleaned after the paid-delivery repair.

Actions completed:

- Test/manual confirmations were removed from the active `confirmed.jsonl`.
- Duplicate real confirmation records were deduplicated by `tx_hash`.
- Test/manual access grants were removed from the active `access_grants.jsonl`.
- Duplicate access grants were removed.
- Stale/test pending payment requests were archived.
- All removed records were preserved under `vault/quarantine/`.

Final active payment-ledger state:

- `confirmed.jsonl`: 3 real on-chain Polygon USDC confirmations.
- `access_grants.jsonl`: 3 matching active grants.
- `pending.jsonl`: 0 active pending requests.
- Active payment ledger scan: clean.

The active payment ledgers now exclude test hashes, manual confirmation strings, stale pending requests, and duplicate transaction records. This improves payment analytics, entitlement integrity, and future external-sale detection.

## Payment Ledger Cleanup — 2026-06-03

The USDC payment ledgers were cleaned after the paid-delivery repair.

Actions completed:

- Test/manual confirmations were removed from the active `confirmed.jsonl`.
- Duplicate real confirmation records were deduplicated by `tx_hash`.
- Test/manual access grants were removed from the active `access_grants.jsonl`.
- Duplicate access grants were removed.
- Stale/test pending payment requests were archived.
- All removed records were preserved under `vault/quarantine/`.

Final active payment-ledger state:

- `confirmed.jsonl`: 3 real on-chain Polygon USDC confirmations.
- `access_grants.jsonl`: 3 matching active grants.
- `pending.jsonl`: 0 active pending requests.
- Active payment ledger scan: clean.

The active payment ledgers now exclude test hashes, manual confirmation strings, stale pending requests, and duplicate transaction records. This improves payment analytics, entitlement integrity, and future external-sale detection.
