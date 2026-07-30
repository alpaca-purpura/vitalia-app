<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 -->
# Backend Code Review: T-15 Agentic eval goldens (CROSS-SCOPE)

**Date:** 2026-05-20
**Brand:** vitalia
**Ticket:** T-15
**Files Reviewed:** 11 (4 Adrián goldens + 3 Lucas goldens + 4 personas + 3 test files + 1 test extension)
**Verdict:** **PASS (limited backend-side audit — primary verdict by auditor-agentic)**

## Cross-scope flag

| File | Module | Action |
|---|---|---|
| `vitalia/backend/tests/agentic_evals/sales_agent/goldens/reengagement/*.yaml` (4) | agentic eval goldens | **[CROSS-SCOPE — auditor-agentic primary]** |
| `vitalia/backend/tests/agentic_evals/lucas/re_engagement_recommendation/*.yaml` (3) | agentic eval goldens (Lucas internal recommendation) | **[CROSS-SCOPE — auditor-agentic primary]** |
| `vitalia/backend/tests/agentic_evals/sales_agent/personas/*.yaml` (4 NEW) | eval personas | **[CROSS-SCOPE — auditor-agentic primary]** |
| `vitalia/backend/tests/agentic_evals/sales_agent/test_voice_fidelity_reengagement.py` | voice fidelity grader smoke | **[CROSS-SCOPE — auditor-agentic primary]** |
| `vitalia/backend/tests/agentic_evals/lucas/test_prompt_cache_hit_rate.py` | prompt cache validation | **[CROSS-SCOPE — auditor-agentic primary]** |
| `vitalia/backend/tests/agentic_evals/test_observability_invariants.py` (extended) | observability invariants | **[CROSS-SCOPE — auditor-agentic primary]** |

**Per backend-expert audit STRICT SCOPE:** archivos bajo `{brand}/backend/tests/agentic_evals/sales_agent/` y `agentic_evals/lucas/` SON agentic eval territory. R23 production_code=false (Sonnet OK) — pero la AUDITORIA pertenece a auditor-agentic.

**Auditor-agentic ámbito:**
- Goldens schema completeness (per `core/luana-core-sales-agent/tests/architecture/test_goldens_schema_completeness.py`)
- Cost-bucket invariants (H7 cement — `evals_only` enforced)
- Voice fidelity grader threshold ≥0.85
- Prompt cache hit rate ≥0.60 + prefix byte-stability
- PII scanner over goldens (no real PHI leaked)
- Trajectory invariants (tool sequence + observability payload shape)
- Persona archetype-dialect mapping (V2 sub-slot rotation)

## Backend-auditor ámbito (HERE — limited)

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | DDD Compliance | N/A | Tests-only ticket |
| 2 | Tenant Isolation | PASS | Goldens declare `expected_tenant_isolation` con tenant_id + clinic_id |
| 4 | Code Quality | PASS | ruff clean per T-15-result.md |
| 7 | Pydantic v2 / PII | PASS | **No real PHI en goldens** (verified `grep -E "[0-9]{8}|@gmail" goldens/**` → no matches). Placeholders `[PATIENT_ID]` / `[PATIENT_PHONE]` |
| 9 | Security | PASS | PII scanner gate enforce + dual filter declarado en goldens. Cost-bucket `evals_only` per spec H7 |
| 10 | Tests / TDD | PASS | 47/47 tests PASS (15 voice fidelity + 11 cache hit + 11 observability + 4 pass-k extensions). PASS verified runtime |
| 12 | Mirror detection | PASS | Goldens reference engine simulator via `from core/luana-core-sales-agent`. NO mirror del simulator infra |

## Anti-duplication check (per skill prompt)

Per `.claude/rules/anti-duplication.md` § Cross-codebase grep:
- Eval simulator SSoT: `core/luana-core-sales-agent/tests/agentic_evals/simulator/` (engine)
- Voice fidelity grader: `core/luana-core-sales-agent/tests/agentic_evals/grader/` (engine)
- Brand goldens correctly live at `{brand}/backend/tests/agentic_evals/{tool}/goldens/` — consume engine simulator, NO mirror

**No mirror detected.** ✓

## Cost bucket invariant (H7 cement)

Per reference doc § F (auditor-downstream-targets):
- T-15 surface modifications: brand goldens + 3 NEW test files
- Downstream `core/luana-core-sales-agent/tests/architecture/test_grader_writes_eval_only_bucket.py` PASS
- Goldens declare `eval_metadata.cost_bucket: evals_only` — verified

## Verdict Math

- BE-side subset: 8 PASS / 0 WARN / 0 FAIL → **PASS** (limited)
- **Primary verdict pending:** `auditor-agentic` debe verificar voice fidelity, cache validation, observability invariants, persona archetype loader contract.

## Skills Consulted Trace

✓ backend-expert (test patterns) ✓ tessl__pytest-api-testing (eval goldens fixture pattern) — per T-15-result.md
✓ Plus: sales-agent-expert, copilot-expert (per T-15 build trace — fall under auditor-agentic ámbito)
