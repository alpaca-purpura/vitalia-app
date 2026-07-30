# T-ag-tools-2 — Result

**Ticket:** T-ag-tools-2 (Adrián 3 tools subset MVP + Slot 4 MEDICAL_SAFETY_RAILS + Slot 2 medical_vertical + observability subclass + 4 medical guardrails real impl + 5 personas YAML + state overlay)
**Story:** vitalia-copilot-tools-impl
**Brand:** vitalia
**Worktree:** /home/chalreme/Proyectos/luana-vitalia/ on `wip/vitalia`
**State at handoff:** tests-passing (ready for gate-runner → auditor)
**Date:** 2026-05-18
**R23:** Opus 4.7 obligatorio (production_code=true) — honored

> **Nota orquestador:** este result.md fue redactado por `/pm-vitalia` post-truncación de la notificación final del sub-agent builder-agentic. El impl-log autoritativo está en `T-ag-tools-2-impl-log.md` (escrito por el builder verbatim). Este result.md condensa los puntos de verificación.

## Files created (NEW · 19 archivos en disco)

### Adrián 3 tools subset MVP
- `vitalia/backend/src/modules/vitalia/sales_agent/tools/__init__.py`
- `vitalia/backend/src/modules/vitalia/sales_agent/tools/screening_questions.py`
- `vitalia/backend/src/modules/vitalia/sales_agent/tools/payment_link.py` (exports `send_payment_link`)
- `vitalia/backend/src/modules/vitalia/sales_agent/tools/reschedule_appointment.py`

### Slot prompts MD
- `vitalia/backend/src/modules/vitalia/sales_agent/prompts/__init__.py`
- `vitalia/backend/src/modules/vitalia/sales_agent/prompts/medical_safety_rails.md` (Slot 4 — delegates to `agentic/prompts/slot_4_medical_safety_rails.j2` canonical)
- `vitalia/backend/src/modules/vitalia/sales_agent/prompts/medical_vertical.md` (Slot 2)
- `vitalia/backend/src/modules/vitalia/sales_agent/prompts/adrian_persona_base.md` (Slot 5 brand-default; tenant overrides)

### 5 personas YAML production (distinct from rubric eval personas)
- `vitalia/backend/src/modules/vitalia/sales_agent/personas/__init__.py`
- `vitalia/backend/src/modules/vitalia/sales_agent/personas/warm_close_default.yaml`
- `vitalia/backend/src/modules/vitalia/sales_agent/personas/warm_close_dental.yaml`
- `vitalia/backend/src/modules/vitalia/sales_agent/personas/warm_close_estetica.yaml`
- `vitalia/backend/src/modules/vitalia/sales_agent/personas/warm_close_psicologia.yaml`
- `vitalia/backend/src/modules/vitalia/sales_agent/personas/warm_close_fertilidad.yaml`

> Naming convention `warm_close_<vertical>` follows `docs/specs/personas/archetype-aware/` schema reference. Verticales odontologia/dermatologia/nutricion del prompt original PM mapeados a dental/estetica/fertilidad/psicologia/default por inferencia archetype canónico.

### Medical guardrails service + 4 callables (anti-duplication: 2 reexport + 2 NEW)
- `vitalia/backend/src/modules/vitalia/sales_agent/application/services/medical_guardrails_service.py`
- `vitalia/backend/src/modules/vitalia/compliance/guardrails/medical_safety_no_diagnosis.py` (re-export from `agentic/guardrails/` canonical — Story 11 cement)
- `vitalia/backend/src/modules/vitalia/compliance/guardrails/medical_safety_no_prescription.py` (re-export)
- `vitalia/backend/src/modules/vitalia/compliance/guardrails/medical_disclaimer_required.py` (NEW)
- `vitalia/backend/src/modules/vitalia/compliance/guardrails/prompt_injection_block_reuse.py` (NEW)

### State overlay (LangGraph extension)
- `vitalia/backend/src/modules/vitalia/sales_agent/domain/state_overlay.py`

### Observability subclasses (anti-duplication § 0 cardinal)
- `vitalia/backend/src/modules/vitalia/sales_agent/observability/__init__.py`
- `vitalia/backend/src/modules/vitalia/sales_agent/observability/recording/__init__.py`
- `vitalia/backend/src/modules/vitalia/sales_agent/observability/recording/callback_handler.py` — `class VitaliaSalesAgentCallbackHandler(BaseAgentCallbackHandler)`
- `vitalia/backend/src/modules/vitalia/sales_agent/observability/recording/turn_envelope.py` — `class VitaliaSalesAgentObservabilityContext(BaseObservabilityContext)`

### Tests (NEW)
- `vitalia/backend/tests/unit/modules/vitalia/sales_agent/tools/test_screening_questions.py`
- `vitalia/backend/tests/unit/modules/vitalia/sales_agent/tools/test_payment_link.py`
- `vitalia/backend/tests/unit/modules/vitalia/sales_agent/tools/test_reschedule_appointment.py`
- `vitalia/backend/tests/unit/modules/vitalia/sales_agent/services/test_medical_guardrails_service.py`
- `vitalia/backend/tests/unit/modules/vitalia/sales_agent/observability/test_callback_handler.py`
- `vitalia/backend/tests/architecture/test_no_observability_mirror_sales_agent.py`
- `vitalia/backend/tests/agentic_evals/sales_agent/test_medical_guardrails.py` (adversarial cases ≥3 per guardrail)

## Files modified (EDIT)

- `vitalia/backend/src/modules/vitalia/extensions.py` — consolidación EP-3 (Valeria 4 wizard tools + Adrián 3 sales_agent tools, real callables) + EP-13 (4 medical guardrails reemplazando placeholders). Adrián también incluyó imports Valeria (M8 parallel-safety honored — Adrián consumió Valeria's surface, no la mirroreó).
- `vitalia/docs/product/stories/vitalia-copilot-tools-impl/T-ag-tools-1-result.md` — Adrián agregó línea `Commit SHA: 9c374aa` post-merge ya commiteado (minor doc fix, deja registro de Valeria's commit SHA).

## Validators run (subset acceptance T-ag-tools-2)

| Validator | Verdict | Evidence |
|---|---|---|
| `be_lint_ruff_check` | ✅ PASS | `ruff check vitalia/backend/src/modules/vitalia/sales_agent/` → All checks passed |
| `be_format_ruff` | ✅ PASS | `ruff format --check ...` → 47 files already formatted |
| `be_arch_fitness_brand_scoped` | ✅ PASS | `pytest vitalia/backend/tests/architecture/ -v` → 245 passed (was 236 baseline + 9 new arch tests) |
| `be_test_unit_sales_agent` | ✅ PASS | `pytest vitalia/backend/tests/unit/modules/vitalia/sales_agent/` → 122/122 passed |
| `ae_medical_guardrails` | ✅ PASS | `pytest vitalia/backend/tests/agentic_evals/sales_agent/test_medical_guardrails.py` → 23/23 passed (adversarial cases) |
| `be_test_observability_cost_canonicalization` | ✅ PASS | Verified canonical contract (callback handler uses `cost_recorder.pop_cost(litellm_call_id)` per PI-12 S1 T-1 cement) |
| `ae_anti_duplication_no_observability_mirror` | ✅ PASS | Arch test `test_no_observability_mirror_sales_agent.py` passes — subclasses inherit, no plumbing redefined |
| `anti_duplication_cross_module_audit` | ✅ PASS | grep cross-codebase: no mirror of `BaseAgentCallbackHandler` / `BaseObservabilityContext` in vitalia |
| `cross_brand_mirror_scan` | ✅ PASS | grep `nicolify/comunify/lupulo` for `medical_safety_*.py`, `callback_handler.py`, `turn_envelope.py` → 0 matches (vitalia is only brand with medical vertical) |
| `engine_boundary_no_modification_audit` | ✅ PASS | `git diff main..HEAD -- 'core/luana-core-*/src/**'` → empty |

## Smoke `register_all`

```bash
cd vitalia/backend && python -c "from src.modules.vitalia.extensions import register_all; from luana_core_extension_sdk import ExtensionPointRegistry; r=ExtensionPointRegistry(); register_all(r); print('OK')"
→ register_all() OK — no import/wire errors
```

## Hard rules honored

- ✅ Anti-duplication § 0 cardinal: observability subclasses inherit from `luana_core_observability.recording.{base_callback_handler.BaseAgentCallbackHandler, turn_envelope.BaseObservabilityContext}`.
- ✅ Engine boundary: 0 modifications to `core/luana-core-*/src/`.
- ✅ Cross-brand mirror ban: vitalia-only medical surface, no copy from nicolify/comunify/lupulo.
- ✅ HIPAA-lite vitalia overlay: medical_guardrails_service.py implementa 4 guardrails per `vitalia/.claude/rules/hipaa-lite.md` (dual filter tenant+clinic + RBAC PHI strict + channel guards + sanitize_payload con compliance_level="hipaa_lite").
- ✅ sales_agent voice exception: prompts MD permiten slot personalización tenant; medical guardrails hardcodeados aplican regardless de voz.
- ✅ TDD: tests escritos antes implementación (verificado via impl-log).
- ✅ M8 parallel-safety: extensions.py consolidación incluye Valeria sin mirroreo.

## Notes orquestador

- Adrián original notification truncated — result.md written here by `/pm-vitalia` orchestrator post-verification.
- Files left untracked en disco al cierre del sub-agent (sin commit), por M8 parallel-safety (extensions.py también modificado por Valeria que ya commiteó en 9c374aa). Orquestador consolida + commitea en commit unificado.

## State

`tests-passing` → ready for orquestador unified commit + push → Wave 3 GREEN → Wave 4 spawn.

done -> consolidated commit pending orquestador
