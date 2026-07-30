# Master Data: Currency + Timezone

> **Slim pointer (W1-Phase2 eviction 2026-06-09 · tier: project).** Cuerpo operativo + ex-always-on body en `backend-expert` skill → `references/master-data.md` (+ `references/currency-handling.md`).

Trigger: tocás fechas/moneda/locale en BE o FE.

No-skip 1-liner: BE store UTC siempre (`utc_now()` + `DateTime(timezone=True)`) · `TenantLocale` VO / `useTenantLocale()` — NUNCA `datetime.utcnow()`, hardcoded timezone ni `= "USD"` default.
