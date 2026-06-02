# Refinery v1.2

Machine-readable temporal intelligence infrastructure for autonomous agents.

---

## Overview

Refinery is a live temporal intelligence refinery focused on transforming fragmented network telemetry, DeFi signals, and blockchain state into compressed machine-readable decision bundles.

The platform is designed primarily for autonomous agents, algorithmic systems, and machine-native consumers.

Refinery operates as a continuous intelligence pipeline:

```text
poll → normalize → timestamp → persist → derive → package
```

The objective is not raw data resale.

Refinery produces temporal intelligence:
state transitions, anomalies, persistence signals, escalation conditions, and decision-relevant summaries derived from rolling historical context.

---

# Core Architecture

Refinery bundles operate through layered temporal pipelines.

## Pipeline Structure

```text
live network telemetry
        ↓
temporal capture
        ↓
historical persistence
        ↓
rolling intelligence generation
        ↓
machine-readable bundle delivery
```

---

# Current Capabilities

- Temporal historical persistence
- Rolling intelligence generation
- Machine-readable JSON delivery
- Append-only telemetry archives
- Live network monitoring
- Derived temporal signal generation
- Agent-native bundle packaging
- XRPL-compatible machine commerce architecture
- Autonomous signal refresh pipelines

---

# Live Bundles

## defi-liquidation-intel-v1

Agent-ready DeFi liquidation intelligence.

### Signal Layers

- oracle_divergence
- liquidation_pressure_proxy
- composite_liquidation_risk
- escalation_event

### Intelligence Model

Focused on detecting:
- liquidation pressure escalation
- cross-protocol instability
- temporal risk persistence
- oracle stress conditions

### Update Frequency

```text
5 minutes
```

---

## solana-temporal-intel-v1

Live Solana temporal intelligence bundle.

### Current Signal Layers

- slot_progression
- rpc_latency
- temporal_network_health

### Current Capabilities

- Live Solana RPC telemetry
- Slot progression tracking
- RPC latency monitoring
- Rolling historical persistence
- Temporal intelligence generation
- Anomaly-ready telemetry architecture

### Pipeline Components

```text
solana_rpc_monitor.py
        ↓
history.jsonl
        ↓
solana_temporal_generator.py
        ↓
latest_intel.json
```

### Output Structure

```text
bundle.json
latest.json
history.jsonl
latest_intel.json
```

### Update Frequency

```text
60 seconds
```

---

# Machine-Readable Endpoints

Refinery exposes machine-discoverable metadata and bundle interfaces.

## Public Discovery

```text
/public/refinery.json
/public/agent_manifest.json
/public/llms.txt
/meta
/packages
/health
```

---

# Design Philosophy

Refinery is designed machine-first.

Primary optimization targets:

- agent discoverability
- machine readability
- low-latency ingestion
- temporal state awareness
- autonomous consumption
- compressed decision advantage

Human readability is secondary to machine operability.

---

# Current Status

Refinery is now operating as a live temporal intelligence platform with active persistent telemetry pipelines.

Current operational state includes:

- live Solana telemetry ingestion
- rolling intelligence generation
- historical persistence layers
- machine-readable intelligence outputs
- autonomous bundle refresh architecture

---

# Roadmap Direction

Planned expansions include:

- congestion scoring
- validator instability heuristics
- whale flow detection
- DEX liquidity fragmentation analysis
- oracle divergence systems
- anomaly classification
- temporal escalation detection
- predictive network stress modeling
- multi-chain temporal intelligence bundles
- autonomous bundle pricing systems

---

# Version

Current platform version:

```text
Refinery v1.2
```
