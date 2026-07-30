<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 -->
# Backend Code Review: T-8 WhatsApp HSM templates fideliz + EP-8 registration

**Date:** 2026-05-20
**Brand:** vitalia
**Ticket:** T-8
**Files Reviewed:** 9 (5 JSON templates + registry.py + __init__.py extension + extensions.py extension + tests extension)
**Verdict:** **PASS**

## Category Summary

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | DDD Compliance | PASS | Templates JSON config + registry frozen dataclass viven en `connections/whatsapp/` infra. NO domain/application/api layers requeridas (es config) |
| 2 | Tenant Isolation | PASS | Templates son catalog (cross-tenant). Enforcement opt-in/opt-out vive en service (T-5) |
| 3 | Soft Deletes | N/A | Templates immutable JSON config |
| 4 | Code Quality | PASS | ruff 0 errors, format clean |
| 5 | SQLAlchemy 2.0 | N/A | Sin SQLA |
| 6 | Async Consistency | N/A | Registry sync (loaded at module import) |
| 7 | Pydantic v2 / PII | PASS | **Templates bodies usan SOLO `{{N}}` placeholders** — no PHI fields aparecen literally. Arch test `test_whatsapp_template_no_phi_in_body_text` enforce |
| 8 | Migration Quality | N/A | Sin migrations |
| 9 | Security | PASS | MARKETING templates con `requires_marketing_opt_in=True` (enforcement en service T-5 + tool T-9). UTILITY = False (citas confirmadas, NPS post-tratamiento) |
| 10 | Tests / TDD | PASS | 11 new tests Part D RED→GREEN, 39/39 extensions tests PASS |
| 11 | Cross-cutting | PASS | Spanish neutro: tuteo en los 5 template bodies (no voseo detectado). `{{1}} = patient_name`, `{{2}} = clinic_name` |
| 12 | Mirror detection | PASS | `WhatsAppTemplateDef` frozen dataclass + registry brand-local. NO existe en core ni cross-brand (grep verified per T-8-result.md anti-duplication audit). Pattern análogo a `conversation_initiation/registry.py` (mismo brand) — consistencia, no duplicación |

## Allowlist Movement

- EP-8 surface registry grows by 5 (`vitalia.fidelizacion_recordatorio_proxima_sesion`, etc.) — additions tracked en `test_extensions.py` Part D.

## Template inventory (per T-8-result.md)

| Slug | Category | Params | requires_marketing_opt_in |
|---|---|---|---|
| `recordatorio_proxima_sesion` | UTILITY | 3 | False |
| `recordatorio_control_doctor` | UTILITY | 2 | False |
| `invitacion_mantenimiento` | MARKETING | 2 | True |
| `re_engagement_ausencia` | MARKETING | 2 | True |
| `nps_post_tratamiento` | UTILITY | 2 | False |

## Verdict Math

- 12 PASS / 0 WARN / 0 FAIL → **PASS**
- Note: ver T-5 review F1 — el `requires_marketing_opt_in` boolean del registry NO se está consultando en `proactive_outbound_service.py` step 2. Bug pertenece a T-5 (consumer no del producer T-8).

## Skills Consulted Trace

✓ backend-expert ✓ backend-ddd ✓ anti-duplication (cross-codebase grep) ✓ spanish-text (tuteo verified) ✓ hipaa-lite (no PHI in templates) ✓ tdd-mandatory (RED→GREEN) ✓ parallel-safety (M8 extend-not-replace) — per T-8-result.md
