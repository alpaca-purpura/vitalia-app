# T-infra-5 review — APPROVED

> Auditor: Claude Opus 4.7 (orchestrator-direct)
> Date: 2026-05-18
> Surface: BE observability (OTel + Sentry)
> Commit SHA: 616bfe1

## Scope
5 NEW production files: `_shared/observability/{__init__.py, otel_setup.py, cron_spans.py, agent_spans.py, sentry_alerts.py}` + 3 test files + 1 arch fitness test. OTel SDK absent en dev venv → fallback `Status`/`StatusCode` sentinels + `requires_otel` pytest mark.

`agent_spans.py` importa `sanitize_phi_payload` de T-infra-3 compliance adapter (anti-duplication compliant). `sentry_alerts.py` declarative IaC config (NO runtime Sentry API calls). BatchSpanProcessor mandatory (NO SimpleSpanProcessor). DSN/endpoint from env vars only.

## Categorías scoring (10 BE categories)
1. **DDD layering** — ✅ `_shared/observability/` es infrastructure-layer puro, NO contaminates domain
2. **Tenant isolation** — N/A (observability es transversal, no queries) ✅
3. **HIPAA-lite dual filter** — N/A ✅
4. **HIPAA-lite audit log** — N/A (audit log infra es T-infra-3) ✅
5. **HIPAA-lite PII sanitization** — ✅ agent_spans.py importa sanitize_phi_payload de T-infra-3 (no local regex re-impl). Traces NUNCA loguean PHI plain
6. **HIPAA-lite RBAC** — N/A ✅
7. **Migrations idempotentes** — N/A ✅
8. **Extension SDK contracts** — N/A ✅
9. **Anti-duplication / cross-brand mirror** — ✅ NO mirror de `core/luana-core-observability/`. cron_spans/agent_spans/otel_setup brand-specific wrappers que SE ENGANCHAN al engine vía hsl pattern: import or graceful sentinel. Cross-brand grep `BatchSpanProcessor` en nicolify/comunify/lupulo = ZERO matches (vitalia-specific Slice 1 first-mover)
10. **Engine boundary** — ✅ ZERO edits a core/luana-core-*/src/. NEW arch test `test_no_observability_mirror.py` enforces

## Findings count
- FAIL: 0
- WARN: 0
- INFO: 8 tests SKIP via `requires_otel` mark (dev venv sin opentelemetry-sdk). Producción DEBE instalar SDK — esto es insurance no business-as-usual. /pm-vitalia debe verificar deploy K8s incluye opentelemetry-sdk en requirements

## Validators acceptance.validator_ids
- be_lint_ruff_check: PASS
- be_format_ruff: PASS
- be_arch_fitness_brand: PASS 190/190 (6 NEW del test_no_observability_mirror.py)
- be_test_observability: PASS 23 / 8 SKIP (expected)

## Downstream regression
- Surface: vitalia/backend/src/modules/vitalia/_shared/observability/ → consumido por:
  - T-infra-8 workers (idempotent_cron decorator uses cron_span context manager)
  - Future agents (sales_agent + copilot via agent_spans.py — todavía no consumido)
- Engine consumer: luana_core_observability (one-way import, NOT mirror)
- Cross-brand mirror: ZERO

## Self-fix log
N/A.

## Verdict
**APPROVED**. T-infra-5 establece observability infrastructure brand-specific con graceful degradation (SDK absent → NO-OP sentinels). PII redaction via engine import (anti-duplication compliant). Declarative IaC Sentry (no runtime API calls).
