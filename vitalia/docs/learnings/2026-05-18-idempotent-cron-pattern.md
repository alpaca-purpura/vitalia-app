---
brand: vitalia
date: 2026-05-18
slug: idempotent-cron-pattern
promotable: yes
proposal_link: docs/promotion-protocol/proposals/2026-05-20-core-platform-extensions-slice-1.md
migrated_engine_path: core/luana-core-platform/src/luana_core_platform/workers/cron_envelope.py
migrated_at: 2026-05-20
migrated_engine_decorator: cron_envelope  # renamed (verify-first reveló @idempotent ya en core, solo lift envelope wrapper)
applies_to_other_brands_potentially: [vitalia, nicolify, comunify, lupulo, fitflow, fixia, retailly, guestly, inmoflow, saasora]
target_core_package: core/luana-core-platform/workers/
origin_story: vitalia-slice-1-infra-cross-cutting
origin_ticket: T-infra-8 (ARQ cron scaffold)
related_capabilities:
  - vitalia/docs/product/capabilities/workers/idempotent-cron-arq-scaffold.yaml
arch_test: vitalia/backend/tests/workers/test_idempotent_cron_decorator.py (8 tests)
---

# `idempotent_cron` decorator — patrón cross-brand para ARQ cron jobs

**Qué aprendimos:** El decorator `@idempotent_cron(span_name, idem_ttl_seconds=600)` introducido por T-infra-8 wrapea funciones ARQ cron con 4 cross-cutting concerns standard: (1) idempotency key check via `RedisIdempotencyStore` (engine `luana_core_idempotency`), (2) OTel `cron_span` context manager (graceful degradation T-infra-5), (3) `structlog` audit on completion, (4) Sentry capture before re-raise. Soft-fail philosophy: si Redis no disponible, idempotency skip silencioso pero cron sigue ejecutando. Engine `luana_core_idempotency` ya provee `IdempotencyKey` + `RedisIdempotencyStore` — el decorator es el "glue layer" brand-side que arma el wrapper específico para workers ARQ.

**Origen:** `vitalia/backend/src/modules/vitalia/_shared/workers/base.py` (T-infra-8, mergeado 2026-05-18 via squash `50143d5`). Consumers iniciales: `lucas_weekly_recommendations.py` (cron semanal copilot Lucas). Ratchet baseline 55 parametrized job scaffolds en arch fitness.

**Why:** Cada brand que necesite cron jobs (todas las 10 brands del portfolio probablemente) inevitablemente toca los 4 mismos concerns: idempotency, observability, audit, error capture. Sin un decorator unificado, cada brand re-implementa el wrapper a mano → drift entre brands + violación de [[anti-duplication]] § lift shared rule. El patrón actual vitalia es brand-local (`src/modules/vitalia/_shared/workers/base.py`) pero es 90% brand-agnostic — solo el `namespace=f"vitalia.cron.{fn.__name__}"` y el path import de `cron_span` son brand-specific.

**How to apply:** Para promover a engine:

1. Lift `idempotent_cron` decorator a `core/luana-core-platform/src/luana_core_platform/workers/idempotent_cron.py` (o crear `core/luana-core-workers` si se justifica módulo dedicado)
2. Parameterizar el namespace prefix: `idempotent_cron(brand: str, span_name: str)` o derivarlo del `__module__` del callable (preferido — auto-detección)
3. Engine consume `luana_core_idempotency` + `luana_core_observability` (ambos ya core) — sin nuevas deps
4. Soft-fail behavior identical cross-brand (idempotency optional, cron always runs)
5. Brand opt-in via import: `from luana_core_platform.workers import idempotent_cron`
6. Brands que necesitan customización per-brand (ej: vitalia HIPAA-lite specific sentry tags) heredan vía monkey-patch o subclass del decorator factory
7. Arch test genérico `core/luana-core-platform/tests/workers/test_idempotent_cron_contract.py` valida soft-fail Redis + sentry capture + structlog audit

**Cross-brand candidacy:** Las 10 brands del portfolio tienen casos cron típicos:

- **Vitalia**: `followup_24h`, `prepaid_booking_release_locks`, `phi_retention_sweep` (HIPAA 10y)
- **Nicolify**: `proposal_followup_72h`, `hours_billing_summary_weekly`
- **Comunify**: `cohort_release_module_weekly`, `creator_analytics_daily`
- **Lupulo**: `reservation_release_no_show_30min`, `daily_revenue_kds_sync`
- **Fitflow**: `membership_renewal_charge_monthly`, `class_capacity_reset_midnight`
- **Fixia**: `tech_dispatch_reassign_30min`, `local_seo_review_request_daily`
- **Retailly**: `cart_abandonment_24h`, `cross_sell_recommendation_daily`
- **Guestly**: `ota_inventory_sync_hourly`, `guest_pre_arrival_email_24h`
- **InmoFlow**: `lead_routing_zone_2min`, `portal_sync_daily`
- **SaaSora**: `subscription_dunning_3d`, `churn_alert_weekly`

100% de los crons listados aplicarían el mismo decorator contract. ROI promoción: alto.

**Threshold lift:** Por convención anti-duplication.md § lift shared rule, threshold 2 brands consumer → lift. Vitalia hoy. Nicolify probable Q3 con `proposal_followup_72h` (campaigns module). → ratchet rationale para `/pm-luana` proposal.

**Proposal trigger:** `/pm-luana` puede levantar proposal `docs/promotion-protocol/proposals/2026-MM-DD-lift-idempotent-cron-decorator.md` cuando segunda brand (nicolify o comunify) intente recrear el patrón. Caveats:

- Engine package debe heredar comportamiento soft-fail vitalia (no breaking change al lift)
- `sentry_sdk` import opcional graceful degradation preservado
- TTL default `600s` per cron window — documentar que brand puede override

**Anti-patterns a evitar al promover:**
- ❌ Forzar Redis dependency hard (rompe soft-fail philosophy original)
- ❌ Lift sin auto-detección de namespace (forzar brands a hardcodear `brand=` arg desperdicia DRY)
- ❌ Lift sin documentar contract `cron_span` integration (brands deben aún registrar sus span_names en su propia config OTel)
- ❌ Lift como módulo Python aparte sin docs en `docs/core-modules/` (cross-brand discoverability sufre)
