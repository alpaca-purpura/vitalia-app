# luana-core-observability

**Version:** 0.0.1-alpha  
**Lift origin:** `AISALESHT/backend/src/shared/agent_observability/`  
**Lift commit:** `bdefd80` (feat(luana-core-observability): lift observability package)

## Overview

Agent observability infrastructure shared across all agent modules (copilot,
sales_agent, and future agents). Handles LLM call recording, pricing snapshots,
cost calculation, persistence, and reporting.

## Key exports

- `luana_core_observability.recording` — `BaseObservabilityContext`, `BaseAgentCallbackHandler`, PII sanitization
- `luana_core_observability.cost` — `CostCalculator`, `FXResolver`, `PricingResolver`
- `luana_core_observability.persistence` — `BaseTraceEventRepo`, `BaseLLMCallRepo`, `TenantBillingConfigRepository`
- `luana_core_observability.pricing` — `PricingSnapshotRepository`, `ModelPricingSnapshotModel`
- `luana_core_observability.reporting` — cost reporting aggregates
- `luana_core_observability.workers` — background worker base classes
