# T-9 Result — Agentic Adrián send_proactive_reengagement tool wrapper

**Ticket:** T-9
**Story:** vitalia-slice-1-fidelizacion
**Brand:** vitalia
**State:** tests-passing
**Builder:** Claude Opus 4.7 (1M context) — R23 production_code=true HARD GATE
**Date:** 2026-05-20

## Summary

Implemented Adrián `send_proactive_reengagement` LangChain `@tool` wrapper around the existing brand-local `ProactiveOutboundService` (T-5 shipped), plus EP-3 registration in `vitalia/backend/src/modules/vitalia/extensions.py`. Tool is a thin adapter that delegates the full 8-step proactive flow (opt_out → marketing_opt_in → throttle → ComplianceService channel guard → audit_log sync write → persist ReEngagementEvent → emit `ReEngagementTriggered` via outbox → return `ProactiveReminderResponse`) to the SSoT service layer. Tool surface enforces HIPAA-lite PHI containment (no `patient_name` / `patient_phone` echoed in return string), graceful-degradation envelope, and tenant + clinic dual filter cardinal at the Pydantic v2 input schema.

11 tool unit tests added (TDD RED → GREEN), all passing. Lint clean (ruff check + ruff format). 265/265 arch fitness gates GREEN. 50/50 (11 new + 39 existing) extensions tests pass — EP-3 surface count grows by 1 with no regression.

## Skills Consulted

| Skill | Reason | Decision |
|---|---|---|
| `copilot-expert` | Anti-duplication §0 cardinal + best-effort observability invariants | Tool delegates to ProactiveOutboundService (service owns audit_log sync + outbox emit). No mirror of engine `BaseAgentCallbackHandler` / `turn_envelope` / cost_recorder. structlog warning only at tool-level resolver failure + service exception. |
| `sales-agent-expert` | §0 anti-duplication + §3 NO se toca + LangChain `@tool` patterns | Followed `screening_questions` / `payment_link` precedent (resolver DI hook + Pydantic v2 args_schema + frozen + extra=forbid + dual filter cardinal). NO touch to engine `agent_state_checkpoints`, `OutputManager.process_response`, `Closer Studio`, `SmartBufferService`. Voice tenant respected — tool surface returns Spanish-neutro structural summary (no voseo in summary; tenant voice fidelity preserved at engine compiler v2 slot 5). |
| `tessl__langgraph` | Whether new StateGraph needed | NO — tool is a pure LangChain `@tool` wrapping an existing service. Engine `core/luana-core-sales-agent/` supervisor consumes the tool via Extension SDK EP-3 dispatch; no graph extension overlay required (per 03-arch-agentic § 3). |
| `tessl__graceful-degradation` | External call envelope (WhatsApp Business API via ProactiveOutboundService) | Try/except around `_get_service()` + `ReEngagementPattern(pattern)` enum coercion + `service.send_proactive_reminder(...)`. Every failure path returns a sanitized Spanish-neutro fallback (no PII leak); the agent turn never crashes. The WhatsApp adapter timeout + retry budget lives inside the service layer (per T-5 design). |
| `claude-api` | Cache slot 5 BRAND_VOICE invariance | Tool returns deterministic structural summary for LLM chain-of-thought — does NOT participate in prompt cache prefix composition. Slot 5 invariance preserved at engine compiler v2 (no change). |
| `.claude/rules/sales-agent-brand-voice.md` | Voice fidelity + slot architecture | Tool surface returns Spanish-neutro structural summary; does not compose system prompts or inject tenant_name mid-block. Voice slot 5 SSoT remains `personality_profiles.system_instruction`. |
| `.claude/rules/copilot-observability.md` | Best-effort observability writes | `structlog.warning` at tool-level resolver failure + service exception + invalid pattern; never breaks turn. Service layer owns all observability writes (audit_log sync, ReEngagementTriggered via outbox). |
| `.claude/rules/anti-duplication.md` | Pre-write cross-codebase grep | Grep verified: NO existing `send_proactive_reengagement` in `core/luana-core-*/` or any other brand. NEW brand-local wrapper around shared ProactiveOutboundService is correct EXTEND pattern (not NEW infrastructure). No shared abstraction violated. |
| `.claude/rules/tenant-isolation.md` | `tenant_id` mandatory cardinal | Pydantic v2 input schema requires `tenant_id` (root) + `clinic_id` (HIPAA-lite dual filter); test `test_input_schema_requires_tenant_and_clinic` enforces. |
| `vitalia/.claude/rules/hipaa-lite.md` | PHI containment + MARKETING opt-in enforcement | PHI fields (`patient_name`, `patient_phone`) accepted in input (passed to service for template variable substitution + Meta API dispatch) but NEVER echoed back in the tool return string; 5 tests assert PHI absence on success/blocked/throttled/exception paths. MARKETING template opt-in enforcement lives at service layer (verified via mock); tool faithfully surfaces `blocked_reason='marketing_opt_in_required'`. |
| `.claude/rules/tdd-mandatory.md` | RED → GREEN → REFACTOR | 11 tests written first, all failed with `ModuleNotFoundError`; tool then implemented; all 11 GREEN. |
| `.claude/rules/auditor-self-fix-policy.md` | Auditor cap awareness | N/A at build phase; awareness only. |

## Files Created

- `vitalia/backend/src/modules/vitalia/sales_agent/tools/send_proactive_reengagement.py` (NEW — 263 LOC including docstrings)
  - `SendProactiveReEngagementInput` Pydantic v2 schema (`frozen=True`, `extra="forbid"`) — 12 required fields (tenant_id, clinic_id, patient_id, patient_phone, patient_name, pattern Literal, template_id, marketing_opt_in, opt_out, re_engagement_event_id, trigger_source, triggered_by_user_id).
  - `set_proactive_outbound_service_resolver(resolver)` DI hook (signature: `() -> ProactiveOutboundService`).
  - `@tool("send_proactive_reengagement", args_schema=...)` async coroutine — delegates to `service.send_proactive_reminder(...)` with idempotency key `proactive::{tenant_id}::{re_engagement_event_id}`.
  - Spanish-neutro structural summary mapper for the 4 ProactiveReminderResponse statuses (sent / throttled / blocked / unknown defensive).
  - `_BLOCKED_REASON_HINTS` dict for the 3 known service-layer blocked_reason values (marketing_opt_in_required, patient_opted_out, compliance_blocked).
  - `__all__` exports the 3 public symbols.

- `vitalia/backend/tests/modules/vitalia/sales_agent/tools/test_send_proactive_reengagement.py` (NEW — 11 tests, 360 LOC)
  - Happy: `test_delegates_to_service_and_emits_event` (SC-01 + PII containment + service kwargs verification).
  - Negative: `test_refuses_marketing_no_optin` (SC-02 + PII containment).
  - Adversarial: `test_refuses_opted_out_patient`, `test_throttle_exceeded_reports_throttled`, `test_unexpected_exception_graceful` (SC-04 + PII containment on exception path).
  - Resolver: `test_resolver_not_configured_graceful` (DI bootstrap contract).
  - Input schema: `test_input_schema_requires_tenant_and_clinic`, `test_input_schema_pattern_enum`, `test_input_schema_extra_forbid`.
  - Surface: `test_tool_surface_metadata`, `test_module_public_exports`.

## Files Modified

- `vitalia/backend/src/modules/vitalia/extensions.py` (EXTEND per M8 — added 2 blocks, no replacement of existing surface):
  1. Import block after the Adrián 3 MVP tools import: `from src.modules.vitalia.sales_agent.tools.send_proactive_reengagement import send_proactive_reengagement` (with comment citing T-9 + T-5 dependency).
  2. `registry.sales_agent_tool_register(ToolDef(...))` block after the existing `reschedule_appointment` registration, before the EP-4 workflow section. CC-4 namespace prefix preserved (`vitalia.send_proactive_reengagement`). `tool_groups=("sales_agent", "vertical_medical", "fidelizacion", "re_engagement")`. JSON Schema mirrors the Pydantic v2 input schema 12 required fields.

No other file in the parallel-session WIP touched (M8 leave-alone respected: T-6, T-7, T-10, T-inbox-*, CRM `lead_dto`/`router`/`service`, etc.).

## Tool Surface Contract

| Field | Type | HIPAA-lite | Notes |
|---|---|---|---|
| `tenant_id` | UUID | dual filter root | required |
| `clinic_id` | UUID | dual filter overlay | required |
| `patient_id` | UUID | identifier | required, surfaced in return |
| `patient_phone` | str (E.164) | PHI — never in return | required, passed to service |
| `patient_name` | str | PHI — never in return | required, passed to service for template var sub |
| `pattern` | Literal[5] | — | matches ReEngagementPattern enum values |
| `template_id` | str | — | one of 5 WhatsApp HSM slugs (T-8) |
| `marketing_opt_in` | bool | — | service enforces vs MARKETING templates |
| `opt_out` | bool | — | service short-circuits when True |
| `re_engagement_event_id` | UUID | — | idempotency key suffix |
| `trigger_source` | str | — | cron name or "manual" |
| `triggered_by_user_id` | UUID | — | audit_log attribution |

## Return Shape (Spanish-neutro LatAm)

| status | Return string template |
|---|---|
| `sent` | `Recordatorio proactivo enviado (patrón={pattern}, template={template_id}, event_id={event_id}, sent_at={iso}).` |
| `throttled` | `Recordatorio no enviado: ventana de throttle activa para el patrón '{pattern}' (event_id={event_id}). Esperá la próxima ventana antes de reintentar.` |
| `blocked` | `Recordatorio no enviado: bloqueado por '{blocked_reason}' — {human-readable hint} (event_id={event_id}, patrón={pattern}).` |
| unknown defensive | `Estado del recordatorio: '{status}' (event_id={event_id}, patrón={pattern}).` |
| service exception | `Hubo un problema técnico al enviar el recordatorio proactivo. Caso registrado para revisión por el equipo de operaciones.` |
| resolver not configured | `Hubo un problema interno con el dispatcher de mensajes proactivos. Caso registrado para revisión técnica.` |
| invalid pattern | `Patrón de re-engagement '{pattern}' no reconocido. Caso registrado para revisión.` |

## Anti-duplication audit (Step 0 GATE complete)

- `find /home/chalreme/Proyectos/luana-vitalia/core -name "send_proactive*"` → no matches (engine has no equivalent — re-engagement is vitalia-specific fidelization vertical).
- `find /home/chalreme/Proyectos/luana-vitalia -name "send_proactive_reengagement*"` → no matches (no cross-brand mirror).
- `ProactiveOutboundService` already exists at `vitalia/backend/src/modules/vitalia/fidelizacion/application/services/proactive_outbound_service.py` (T-5 shipped — commit edac078). Tool delegates via DI resolver; NEVER instantiates.
- `WHATSAPP_TEMPLATE_REGISTRY` already exists at `vitalia/backend/src/modules/vitalia/connections/whatsapp/registry.py` (T-8 shipped — commit c805cbe). Tool does not load templates directly; service consumes registry.
- `BaseAgentCallbackHandler` lives at `core/luana-core-observability/` (engine SSoT). Tool surface emits `structlog.warning` only — no mirror.

## HIPAA-lite Compliance

- **Dual filter cardinal:** input schema requires `tenant_id` + `clinic_id`; service applies on all repo queries (verified in T-5).
- **PHI containment:** `patient_name` + `patient_phone` accepted as input but NEVER echoed in return string. 5 tests assert this on happy, blocked, throttled, exception, and resolver-not-configured paths.
- **MARKETING opt-in:** enforced at service layer (verified via mock returning `blocked_reason='marketing_opt_in_required'`). Tool faithfully surfaces the blocked status with Spanish-neutro hint.
- **opt_out:** enforced at service layer (verified via mock returning `blocked_reason='patient_opted_out'`).
- **Compliance channel guard:** ComplianceService runs at service layer (T-5 step 4). Tool surfaces `blocked_reason='compliance_blocked'` with hint.
- **Audit log sync write:** service step 5 — tool does NOT touch `audit_log` directly.
- **ReEngagementTriggered event:** service step 7 emits via `adapter_bus.publish` (outbox pattern). Tool does NOT touch outbox.

## Cost + Latency

- **LLM calls:** 0 (no model call — template is Meta-approved HSM; deterministic variable substitution at WhatsApp Business API).
- **Tool overhead:** <10ms (Pydantic v2 input parse + resolver call + 1 `await` + return string format).
- **Service overhead (T-5):** p95 ≤3s (ComplianceService check + audit_log sync write + DB persist + outbox publish + WhatsApp Business API serial). The tool inherits this budget transparently.

## Quality Gates

| Gate | Result |
|---|---|
| ruff check (`src/modules/vitalia/sales_agent/tools/` + `tests/modules/vitalia/sales_agent/` + `src/modules/vitalia/extensions.py`) | PASS — 0 errors |
| ruff format --check (3 files) | PASS — already formatted |
| pytest `tests/modules/vitalia/sales_agent/tools/test_send_proactive_reengagement.py` | PASS — 11/11 |
| pytest `tests/test_extensions.py` | PASS — 39/39 (no regression on T-8 part D) |
| pytest `tests/architecture/` | PASS — 265/265 |
| pytest `tests/modules/vitalia/sales_agent/` + `tests/test_extensions.py` (combined) | PASS — 62/62 |
| TDD RED → GREEN confirmed | YES — initial run failed `ModuleNotFoundError`, all GREEN after implementation |
| Anti-duplication grep (core + all brands) | PASS — no mirror |
| Step 0.5 default-flip detection | N/A — no config flags touched |

## Pre-existing failures (NOT caused by T-9)

- `tests/modules/vitalia/fidelizacion/infrastructure/test_nps_response_repository.py::test_list_for_patient` — `fixture 'db_session' not found`. Verified pre-existing via `git stash + run`. Belongs to T-4 / T-5 infra surface and parallel session work; not in T-9 scope.

## Validators Status (per 04-validators.yaml)

| Validator ID | Command | Status |
|---|---|---|
| `be_arch_fitness` | `pytest tests/architecture/ -x -q --override-ini='addopts='` | PASS (265/265) |
| `be_lint_agentic` | `ruff check src/modules/vitalia/sales_agent/tools/ ... --no-cache` | PASS |
| `be_unit_tests_fidelizacion` | `pytest tests/modules/vitalia/fidelizacion/ -x -q --ignore=tests/modules/vitalia/fidelizacion/workers` | PRE-EXISTING fail unrelated to T-9 (fixture missing in T-4/T-5 surface; parallel session work); T-9 native tests in `tests/modules/vitalia/sales_agent/tools/` PASS 11/11 |
| `agentic_observability_invariants` | `pytest tests/agentic_evals/test_observability_invariants.py -x -v -k 'reengagement or lucas'` | DEFERRED to T-15 (eval goldens ticket); tool surface enforces invariant (no PHI in return) verified via 5 PII-containment unit tests |

## Next steps (post T-9)

- T-10 (Lucas tool — production_code=true Opus 4.7): blocked by T-4 + T-5 (both shipped). Can proceed in parallel.
- T-15 (eval goldens for Adrián reengagement + Lucas — Sonnet OK): blocked by T-9 + T-10. Includes 4 Adrián scenarios + 3 Lucas scenarios + voice fidelity grader smoke + observability invariants extension.
- Composition root wiring: `vitalia/backend/src/main.py` lifespan startup must call `set_proactive_outbound_service_resolver(lambda: ProactiveOutboundService(...))` for the tool to be live. This wiring is part of the orchestrator initialization sequence (existing tools `screening_questions`, `send_payment_link`, `reschedule_appointment` follow the same pattern).
