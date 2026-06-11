# Refinery Intelligence Listing Pack

Name: Refinery Intelligence

Website: https://dalien.net

API Base: https://api.dalien.net

Agent Buy Guide: https://api.dalien.net/agent-buy.json

Agent Manifest: https://api.dalien.net/public/agent_manifest.json

OpenAPI: https://dalien.net/openapi.json

Package Registry: https://api.dalien.net/packages

Platform Metadata: https://api.dalien.net/meta

LLM Discovery: https://api.dalien.net/public/llms.txt

Payment Rail: Polygon USDC

Description:
Refinery is an agent-native temporal intelligence API for DeFi and blockchain monitoring. It exposes machine-readable discovery, package metadata, redacted public previews, and payment-gated paid payloads via Polygon USDC.

Agent Commerce:
Autonomous agents can discover available bundles, inspect payment metadata, create a Polygon USDC payment request, verify payment on-chain, and retrieve paid JSON payloads. Unpaid paid-bundle access returns HTTP 402 payment_required with a machine-readable next action.

Recommended First Bundle:
solana-temporal-intel-v1

Primary Agent Use Case:
Before submitting a time-sensitive Solana transaction, an agent can buy a fresh network-state snapshot to decide whether to act now, delay, retry, or reroute.
