<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 -->
# Backend Code Review: T-9 Adrián send_proactive_reengagement tool (CROSS-SCOPE)

**Date:** 2026-05-20
**Brand:** vitalia
**Ticket:** T-9
**Files Reviewed:** 3 (NEW tool + extensions.py extension + 11 unit tests)
**Verdict:** **PASS (limited backend-side audit — primary verdict by auditor-agentic)**

## Cross-scope flag

| File | Module | Action |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/sales_agent/tools/send_proactive_reengagement.py` | sales_agent (brand extension) | **[CROSS-SCOPE — auditor-agentic primary]** |
| `vitalia/backend/tests/modules/vitalia/sales_agent/tools/test_send_proactive_reengagement.py` | sales_agent | **[CROSS-SCOPE — auditor-agentic primary]** |
| `vitalia/backend/src/modules/vitalia/extensions.py` (EP-3 registration) | brand extension surface | OK — scope intersect with backend-auditor |

**Per backend-expert audit STRICT SCOPE:** files bajo `{brand}/backend/src/modules/{brand}/sales_agent/` SON sales-agent extension territory. R23 Opus 4.7 production_code=true HARD requires agentic-auditor primary verdict for cross-cutting concerns (LangGraph state, prompt cache, observability invariants, voice fidelity, eval golden goldens).

**Auditor-agentic ámbito (no aquí):**
- LangChain `@tool` surface dispatch via Extension SDK EP-3
- Voice fidelity tenant (slot 5 BRAND_VOICE cache prefix)
- Observability invariants (cost_bucket=user_visible vs evals_only)
- Graceful-degradation envelope per tessl rule
- Agentic golden test mapping (T-15)

**Backend-auditor ámbito (HERE):**

## Category Summary (BE-side subset)

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | DDD Compliance | PASS | Tool delega a `ProactiveOutboundService` (T-5 service SSoT). No duplicación lógica negocio en tool surface |
| 2 | Tenant Isolation | PASS | Pydantic input schema `tenant_id` + `clinic_id` required + dual filter test enforced |
| 7 | Pydantic v2 / PII | PASS | `frozen=True, extra="forbid"` input schema. PHI (patient_name + patient_phone) accepted en input pero NEVER echoed en return string (5 PII containment tests) |
| 9 | Security | PASS | MARKETING opt-in enforcement surface via service (`blocked_reason="marketing_opt_in_required"` propagado) — pero ver T-5 F1: el service no consulta el flag del registry → tool surface también afectado downstream |
| 10 | Tests / TDD | PASS | 11 unit tests RED→GREEN. Happy + negative + adversarial cubiertos |
| 12 | Mirror detection | PASS | grep cross-codebase `send_proactive_reengagement` → solo this file. Re-engagement es vitalia-specific vertical (no engine equivalent). EXTEND pattern correcto (no NEW infrastructure) |

## Findings

### info — Downstream impact from T-5 F1

**Issue:** Tool delega correctamente a service, pero hereda el bug F1 de T-5 (proactive_outbound bloquea TODAS templates si `marketing_opt_in=False`, sin distinguir UTILITY vs MARKETING). Tool no agrega lógica propia → no es bug del tool sino del consumer.

**Fix:** Resolución en T-5 fix automáticamente arregla esto.

## Verdict Math

- BE-side subset: 6 PASS / 0 WARN / 0 FAIL → **PASS** (limited)
- **Primary verdict pending:** `auditor-agentic` debe emitir veredicto LangGraph/observability/voice fidelity/eval coverage.
- Esperar handoff a auditor-agentic. Si el sub-auditor agentic flagea cross-cutting concerns → re-audit cascade.

## Skills Consulted Trace

✓ backend-expert (Pydantic v2 + tests pattern) ✓ tessl__fastapi (input schema patterns) ✓ tessl__pytest-api-testing (11 unit tests) — per T-9-result.md
✓ Plus: sales-agent-expert, copilot-expert, tessl__langgraph, tessl__graceful-degradation (all per T-9 build trace — fall under auditor-agentic ámbito)
