# Copilot Observability

> **Slim pointer (W1-Phase2 eviction 2026-06-09 · tier: project).** Cuerpo operativo + ex-always-on body (split engine/brand + tablas mirror) en `copilot-expert` skill → `references/copilot-observability.md`.

Trigger: `core/luana-core-copilot/src/**/observability/**` · `core/luana-core-observability/src/**` · `{brand}/.../copilot/observability/**` · queries costo/billing/cycle.

No-skip 1-liner: toda escritura observability `try/except + structlog warning` (no rompe turn) · PII via `sanitize_payload(...)` shared de `luana_core_observability` (NUNCA reimplementar — `anti-duplication.md`).
