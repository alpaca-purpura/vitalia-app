# Currency Handling

> **Slim pointer (W1-Phase2 eviction 2026-06-09 · tier: project).** Cuerpo operativo + ex-always-on body (flow provider→DTO→FE) en `backend-expert` skill → `references/currency-handling.md`.

Trigger: monetary fields en DTOs/KPIs/FE display.

No-skip 1-liner: currency viene del data source (`official_metrics.currency`) — DTO monetary SIEMPRE con `currency: str | None` · FE fallback `response.currency ?? parentData.currency ?? 'USD'` — NUNCA `formatMoney(value, 'USD')` sin verify.
