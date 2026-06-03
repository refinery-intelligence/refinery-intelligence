# Refinery Build Roadmap

## Definitive Steps From Concept to Finished Product

- **Define the final product vision**
  - Refinery is a machine-first DeFi intelligence platform.
  - Raw feeds are only inputs.
  - The sellable products are processed intelligence bundles stored in vaults.

- **Lock the first product**
  - Start with the **Liquidation Protection Bundle**.
  - Do not build all 12 bundles at once.
  - Use the first bundle to prove the full system.

- **Define the simple agent flow**
  - Agent finds site.
  - Agent reads machine-readable bundle metadata.
  - Agent chooses bundle.
  - Agent pays.
  - Payment is verified.
  - Vault access is granted.
  - Bundle is delivered through API, webhook, or dashboard.

- **Design the machine-first site structure**
  - Human-readable homepage.
  - Agent start page.
  - Bundle catalog.
  - Vault catalog.
  - Pricing page.
  - API documentation.
  - Machine-readable files such as `/refinery.json`, `/bundles.json`, `/pricing.json`, `/openapi.json`, and `/llms.txt`.

- **Create the public bundle page**
  - Build the Liquidation Protection Bundle page.
  - Include what it does, who it is for, sample JSON output, pricing, access method, trial option, and buy button.

- **Create the machine-readable bundle schema**
  - Define the exact JSON output for the bundle.
  - Include risk level, liquidation distance, oracle confidence, liquidity exit quality, recommended agent action, confidence score, time window, and invalidation condition.

- **Build the first data input layer**
  - Connect the required data for liquidation protection.
  - Include lending market data, asset price data, oracle data, liquidity data, volatility data, and historical movement.

- **Build the processing engine**
  - Normalize incoming data.
  - Preserve history.
  - Detect anomalies.
  - Calculate risk scores.
  - Calculate confidence scores.
  - Generate agent-readable recommendations.

- **Create the first vault**
  - Store the processed Liquidation Protection Bundle output.
  - Version each signal.
  - Track timestamps.
  - Track confidence changes.
  - Store access permissions.
  - Prepare the vault for API and webhook delivery.

- **Build the payment flow**
  - Allow wallet, card, or subscription payment.
  - Create purchase intent.
  - Verify payment.
  - Unlock vault access after successful verification.

- **Build the access system**
  - Issue API keys or wallet-based access.
  - Set rate limits.
  - Track usage.
  - Control trial access.
  - Protect private endpoints.

- **Build the delivery system**
  - API endpoint for latest bundle signal.
  - Webhook alerts for major risk changes.
  - Optional human dashboard view.
  - Sample endpoint for free or public testing.

- **Create the free trial system**
  - Offer 7-day trial access.
  - Limit calls.
  - Limit history.
  - Do not expose internal architecture or scoring logic.
  - Convert trial users to paid vault access.

- **Secure the platform**
  - Hide internal architecture.
  - Protect data sources.
  - Protect scoring logic.
  - Protect API keys.
  - Add rate limits.
  - Add abuse detection.
  - Add logging.
  - Add access revocation.

- **Test the first bundle manually**
  - Compare signals against real market movement.
  - Check false positives.
  - Check missed risks.
  - Tune thresholds.
  - Improve confidence scoring.

- **Launch the first public version**
  - Publish the machine-first site.
  - Publish the Liquidation Protection Bundle.
  - Publish docs.
  - Publish sample outputs.
  - Open free trials.
  - Accept paid users.

- **Collect usage and validation data**
  - Track which agents and humans query the bundle.
  - Track which signals were useful.
  - Track prediction accuracy.
  - Track upgrade conversions.
  - Track API errors and user drop-off.

- **Improve the first bundle**
  - Tune the scoring.
  - Improve response speed.
  - Improve documentation.
  - Improve trial-to-paid conversion.
  - Improve webhook usefulness.

- **Add the second bundle**
  - Build the **Oracle & Price Integrity Bundle**.
  - Connect it to its own vault.
  - Add it to the site and machine-readable catalog.

- **Add the third bundle**
  - Build the **Liquidity Pool Intelligence Bundle**.
  - Connect it to vault access.
  - Bundle it with liquidation and oracle intelligence.

- **Create the first bundle stack**
  - Combine Liquidation Protection, Oracle Integrity, and Liquidity Pool Intelligence.
  - Sell this as a higher-value agent protection stack.

- **Build the remaining 12 bundle areas one by one**
  - Lending & Borrowing Intelligence.
  - Stablecoin Risk.
  - Yield Quality.
  - Cross-chain Flow.
  - DEX Trading Intelligence.
  - Protocol Health.
  - Treasury & DAO Intelligence.
  - Agent Execution Intelligence.
  - Predictive DeFi Intelligence.

- **Build the DeFi Sentinel AI**
  - Allow it to monitor all active bundle vaults.
  - Summarize cross-bundle conditions.
  - Detect relationships between bundles.
  - Generate DeFi-wide predictions and alerts.

- **Build the Macro Sentinel AI**
  - Monitor global human and macro conditions.
  - Compress macro signals into machine-readable variables.
  - Track risk appetite, liquidity conditions, regulation, geopolitical stress, market stress, and institutional flow.

- **Build the Overwatch inference layer**
  - Combine DeFi Sentinel output with Macro Sentinel output.
  - Generate cross-domain predictions.
  - Produce strategic intelligence for agents.

- **Create the premium predictive feed**
  - Sell DeFi Sentinel predictions.
  - Sell Macro Sentinel signals.
  - Sell Overwatch cross-domain inference as the highest-tier product.

- **Expand pricing**
  - Human SaaS tiers.
  - Agent API tiers.
  - Usage credits.
  - Pay-per-bundle-call.
  - Premium Sentinel calls.
  - Enterprise and private vaults.

- **Accelerate discovery**
  - Publish machine-readable discovery files.
  - Publish OpenAPI docs.
  - Publish `/llms.txt`.
  - Publish sample bundle outputs.
  - Publish agent instructions.
  - Add the site to agent, MCP, and tool directories.
  - Create public proof content.

- **Scale the platform**
  - Add more protocols.
  - Add more chains.
  - Add more vaults.
  - Add more bundle variations.
  - Improve prediction validation.
  - Improve uptime, speed, and reliability.

- **Final product state**
  - Refinery becomes a machine-compliant DeFi intelligence marketplace.
  - Agents can discover, understand, buy, verify, and consume bundles.
  - Humans can use dashboards and manage subscriptions.
  - Vaults store processed intelligence.
  - Sentinel AI monitors all bundles.
  - Macro AI monitors global conditions.
  - Overwatch produces cross-domain predictive intelligence.
