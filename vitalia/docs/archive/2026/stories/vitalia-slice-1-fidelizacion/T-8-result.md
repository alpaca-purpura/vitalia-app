# T-8 Result — WhatsApp HSM Templates Fidelización + EP-8 Registration

> Brand: vitalia
> Story: vitalia-slice-1-fidelizacion
> Ticket: T-8
> Builder: claude-sonnet-4-6
> Completed: 2026-05-20
> State: tests-passing

## Summary

Implemented 5 Meta-approved WhatsApp HSM template JSON configs + brand-local registry + EP-8 registration for vitalia patient fidelización workflows.

## Files Created / Modified

| File | Action | Notes |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/connections/whatsapp/templates/fidelizacion/recordatorio_proxima_sesion.json` | CREATED | UTILITY — 4 params, 2 quick-reply buttons |
| `vitalia/backend/src/modules/vitalia/connections/whatsapp/templates/fidelizacion/recordatorio_control_doctor.json` | CREATED | UTILITY — 2 params, 1 quick-reply button |
| `vitalia/backend/src/modules/vitalia/connections/whatsapp/templates/fidelizacion/invitacion_mantenimiento.json` | CREATED | MARKETING — 2 params, 1 quick-reply button |
| `vitalia/backend/src/modules/vitalia/connections/whatsapp/templates/fidelizacion/re_engagement_ausencia.json` | CREATED | MARKETING — 2 params, 1 quick-reply button |
| `vitalia/backend/src/modules/vitalia/connections/whatsapp/templates/fidelizacion/nps_post_tratamiento.json` | CREATED | UTILITY — 2 params, 1 quick-reply button |
| `vitalia/backend/src/modules/vitalia/connections/whatsapp/registry.py` | CREATED | WhatsAppTemplateDef frozen dataclass + WHATSAPP_TEMPLATE_REGISTRY dict + helpers |
| `vitalia/backend/src/modules/vitalia/connections/whatsapp/__init__.py` | EXTENDED | Added registry exports alongside existing adapter exports (M8: extend-not-replace) |
| `vitalia/backend/src/modules/vitalia/extensions.py` | EXTENDED | Import WHATSAPP_TEMPLATE_REGISTRY + EP-8 loop for 5 fidelización adapters |
| `vitalia/backend/tests/test_extensions.py` | EXTENDED | Part D — 11 new tests (RED first, then GREEN) |

## Template Summary

| Slug | Category | Params | Requires Opt-in |
|---|---|---|---|
| `recordatorio_proxima_sesion` | UTILITY | patient_name, appointment_datetime, clinic_name | No |
| `recordatorio_control_doctor` | UTILITY | patient_name, clinic_name | No |
| `invitacion_mantenimiento` | MARKETING | patient_name, clinic_name | Yes |
| `re_engagement_ausencia` | MARKETING | patient_name, clinic_name | Yes |
| `nps_post_tratamiento` | UTILITY | patient_name, clinic_name | No |

## Design Decisions

**D1 — EP-8 `channel_adapter_register` (not non-existent `register_whatsapp_template`)**
The ticket's suggested pseudocode referenced `registry.register_whatsapp_template(...)` which does not exist in the Extension SDK. Confirmed via `core/luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py` — EP-8 is `channel_adapter_register(adapter: ChannelAdapterDef)`. Used one `ChannelAdapterDef` per template slug with `channel_slug = vitalia.fidelizacion_{template_slug}` (CC-4 namespace compliant).

**D2 — Brand-local registry pattern (WhatsAppTemplateDef frozen dataclass)**
Followed pattern from `conversation_initiation/registry.py` (frozen dataclass + dict + lookup helpers). The `WHATSAPP_TEMPLATE_REGISTRY` is loaded at module import time from JSON files, providing fast runtime lookup for `ProactiveOutboundService` (T-5/T-9).

**D3 — HIPAA-lite: no PHI in template bodies**
All 5 template bodies use only `{{N}}` placeholders for `patient_name`, `clinic_name`, `appointment_datetime`. No diagnosis, medication, medical_notes, or other PHI fields appear literally. `test_whatsapp_template_no_phi_in_body_text` enforces this.

**D4 — MARKETING templates: `requires_marketing_opt_in=True`**
`invitacion_mantenimiento` and `re_engagement_ausencia` are MARKETING category — `requires_marketing_opt_in=True` is set in the registry. Enforcement at `ProactiveOutboundService` layer (T-5/T-9 implementation — service checks `if template.requires_marketing_opt_in and not patient.marketing_opt_in: raise HTTPException(403)`).

**D5 — `__init__.py` extended via M8 (extend-not-replace)**
The `whatsapp/__init__.py` was created by the parallel T-inbox-be-4 session for the WhatsApp retract adapter. Extended with `from src.modules.vitalia.connections.whatsapp.registry import ...` appended alongside the existing adapter exports. No adapter functionality was modified.

**D6 — Import style: `src.modules.vitalia...` (not `vitalia.backend.src...`)**
The parallel session's adapter used the `vitalia.backend.src...` import path which fails in the test environment (tests run with `src.modules...` root). Switched to `src.modules.vitalia.connections.whatsapp.registry` for consistency with all other established registries (payment, fiscal, conversation_initiation, etc.).

## Quality Gates

| Gate | Result |
|---|---|
| `ruff check` (lint) | PASS — 0 errors |
| `ruff format --check` (format) | PASS — 5 files already formatted |
| `pytest tests/test_extensions.py` | PASS — 39/39 tests (11 new Part D + 28 existing) |
| `pytest tests/architecture/` | PASS — 265/265 tests |
| TDD RED→GREEN | Confirmed: all 11 Part D tests failed before implementation, passed after |

## Skills Consulted (must_load enforcement v4.1)

| Skill | Invoked | Decision |
|---|---|---|
| `backend-expert` (runtime-quality-checklist.md) | YES — context loaded via rules | No SQLAlchemy/FastAPI here (pure config module). Frozen dataclass pattern confirmed correct for brand-local registry. |
| `.claude/rules/backend-ddd.md` | YES — loaded | No new layers: `connections/whatsapp/` is infrastructure-level brand config. No domain/application/api layer needed for template registry. |
| `.claude/rules/anti-duplication.md` | YES — loaded | Confirmed no existing `WhatsAppTemplateDef` in core or other brands. Brand-specific template config stays in `vitalia/connections/whatsapp/` (not core). |
| `.claude/rules/spanish-text.md` | YES — loaded | All 5 template bodies verified: tuteo used throughout. No voseo forms detected. `{{1}}` placeholder for patient name uses `Hola {{1}},` (neutro). |
| `vitalia/.claude/rules/hipaa-lite.md` | YES — loaded | PHI check: template bodies use `{{N}}` placeholders only. No PHI field names appear literally. MARKETING templates have `requires_marketing_opt_in=True`. Test `test_whatsapp_template_no_phi_in_body_text` enforces this. |
| `.claude/rules/tdd-mandatory.md` | YES — loaded | RED tests written first (Part D in test_extensions.py). Confirmed all 11 failed with `ImportError`/`AssertionError` before any implementation. All 11 GREEN after. |
| `.claude/rules/parallel-safety.md` | YES — loaded | Parallel sessions T-2, T-3, T-inbox-be-2, T-inbox-be-4 on disjoint paths. M8 applied: extended `__init__.py` (not replaced). Staged only exact files modified in T-8. |

## Validator Status

| Validator ID | Command | Status |
|---|---|---|
| `be_arch_fitness` | `pytest vitalia/backend/tests/architecture/ -v` | PASS (265/265) |
| `be_test_extensions` | `pytest vitalia/backend/tests/test_extensions.py -v` | PASS (39/39 — 11 new Part D) |
