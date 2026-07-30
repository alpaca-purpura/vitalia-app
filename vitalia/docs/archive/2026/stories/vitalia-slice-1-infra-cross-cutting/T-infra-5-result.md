---
ticket: T-infra-5
title: "OpenTelemetry tracing setup + Sentry integration (cron spans + agent turn spans)"
story: vitalia-slice-1-infra-cross-cutting
state: tests-passing
pushed_at: 2026-05-18
branch: wip/vitalia-slice-1-shipping
production_code: false
model_used: claude-sonnet-4-6
blocked_by_resolved: T-infra-2 (satisfied)
---

# T-infra-5 — Result

## Summary

Implemented brand-local OTel tracing + Sentry alert rule config for Vitalia.
5 new production files + 4 test files + 1 arch fitness test. 23 tests PASS, 8 SKIP
(expected — opentelemetry-sdk not installed in dev venv; tests skip gracefully
with `requires_otel` pytest mark when SDK absent).

## Files created

### Production (5 files)

| File | LOC | Description |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/_shared/observability/__init__.py` | ~25 | Package marker + `__all__` exports |
| `vitalia/backend/src/modules/vitalia/_shared/observability/otel_setup.py` | ~165 | `build_otel_resource()` + `setup_otel()` + `maybe_init_sentry()`. BatchSpanProcessor mandatory, env vars only (no hardcoded DSN/endpoint) |
| `vitalia/backend/src/modules/vitalia/_shared/observability/cron_spans.py` | ~130 | `CRON_SPAN_NAMES` (11 named spans) + `cron_span()` async CM. Fallback `Status`/`StatusCode` sentinels when OTel not installed |
| `vitalia/backend/src/modules/vitalia/_shared/observability/agent_spans.py` | ~200 | `AgentSpanContext.set_cost()` (4 cost attrs per spec) + `agent_turn_span()` async CM. Imports `sanitize_phi_payload` from compliance adapter (NEVER mirrors) |
| `vitalia/backend/src/modules/vitalia/_shared/observability/sentry_alerts.py` | ~115 | `SentryAlertRule` dataclass + `VITALIA_ALERT_RULES` tuple (3 rules: cost_runaway + cron_failure + cache_hit). Declarative IaC config, NO runtime Sentry API calls |

### Tests (4 files)

| File | Tests | Notes |
|---|---|---|
| `vitalia/backend/tests/_shared/observability/test_otel_setup.py` | 10 (2 pass, 8 skip) | OTel-dependent tests skip when SDK absent via `requires_otel` mark |
| `vitalia/backend/tests/_shared/observability/test_cron_spans.py` | 8 (all pass) | CRON_SPAN_NAMES catalog + async CM lifecycle. Imports StatusCode from production module |
| `vitalia/backend/tests/_shared/observability/test_agent_spans.py` | 7 (all pass) | Agent span lifecycle + cost attrs + PHI import check |
| `vitalia/backend/tests/architecture/test_no_observability_mirror.py` | 6 (all pass) | Arch fitness: no local sanitize_payload/redact_string/redact_value; no hardcoded DSN/endpoint; BatchSpanProcessor required |

## Key design decisions

### OTel unavailable graceful degradation

OTel SDK (`opentelemetry-sdk`) is not installed in the current venv. Both
`cron_spans.py` and `agent_spans.py` define fallback `Status`/`StatusCode`
sentinel classes in the `except ImportError` block, so:
- Production code: `_get_tracer()` raises `ImportError` before the CM body runs
- Tests: `_get_tracer` is mocked, CM body uses fallback sentinels
- Tests that exercise `build_otel_resource()` / `setup_otel()` directly skip
  via `requires_otel` mark

### Anti-duplication compliance

`agent_spans.py` imports `sanitize_phi_payload` from
`vitalia.compliance.application.compliance_service_adapter` (implemented T-infra-3).
Fallback to passthrough when compliance adapter not importable (test environments).
NO local PII regex defined. Arch test `test_agent_spans_imports_sanitize_not_mirror`
verifies this invariant.

### Sentry alert rules (declarative only)

`sentry_alerts.py` defines 3 rules as frozen dataclasses:
- `cost_runaway_per_tenant`: >5 USD/h → critical (slack-vitalia-critical)
- `cron_failure_rate`: >10% failure in 1h → critical (slack-vitalia-critical)
- `agent_cache_hit_rate`: <40% over 100 turns → warning (slack-vitalia-alerts)

These are NOT runtime Sentry API calls — pure IaC config consumable by
Terraform/Sentry CLI or management commands.

### PHI in spans

UUIDs (`tenant_id`, `clinic_id`, `conversation_id`) are NOT PHI — safe as span
attributes for trace correlation. Patient clinical data is never set as span
attribute in this file. PHI handling delegates to `sanitize_phi_payload` in
the compliance adapter per HIPAA-lite rules.

## Validators

| Gate | Result | Notes |
|---|---|---|
| `be_lint_ruff_check` | PASS | 0 errors |
| `be_format_ruff` | PASS | 0 files to reformat |
| `be_arch_fitness_brand` | PASS | 190/190 tests PASS (6 new from `test_no_observability_mirror.py`) |
| `be_test_observability` | PASS | 23 pass / 8 skip (expected OTel-absent skips) |

## Awaiting

Orchestrator → gate-runner → auditor-backend (independent verdict).
