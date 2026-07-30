---
module: sales_agent
brand: vitalia
last_updated: 2026-05-20
---

# sales_agent — Adrián 3 tools MVP + medical guardrails + state overlay

Extensión brand de `core/luana-core-sales-agent`. Esta historia (`vitalia-copilot-tools-impl`, 2026-05-18) introduce la PRIMERA capa de capabilities sales_agent brand-specific vitalia.

## Surface

- **Adrián 3 tools MVP** (EP-3): screening_questions, send_payment_link, reschedule_appointment — LangChain @tool async wrapping application services Wave 2 BE
- **6-slot prompt architecture**: Slot 0 system constant + Slot 1 agent_id + Slot 2 medical_vertical + Slot 3 module_context + **Slot 4 MEDICAL_SAFETY_RAILS** (canonical j2 at `agentic/prompts/`, pointer at `sales_agent/prompts/`) + Slot 5 adrian_persona_base (brand-default; tenant overrides via personality_profile.system_instruction)
- **5 production personas YAML**: warm_close_default + warm_close_{dental, estetica, psicologia, fertilidad}
- **MedicalGuardrailsService** (HIPAA-lite vitalia overlay) orquesta 4 guardrails reales: prevent_diagnosis_disclosure_on_unencrypted_channel + redirect_results_to_portal + block_unauthorized_phi_access + validate_compliance_outbound. 4 guardrail callables compliance shims re-export agentic/guardrails/ canonical (single source enforced).
- **VitaliaSalesAgentStateOverlay** (TypedDict): patient_clinic_id (dual filter HIPAA-lite) + treatment_type + compliance_level
- **VitaliaSalesAgentCallbackHandler** + **ObservabilityContext** subclasses (anti-duplication §0 cardinal — inherit engine bases, NEVER mirror)

## Capabilities

<!-- auto-list:start -->
- `adrian-3-tools-mvp` (live · 2026-05-18)
- `medical-guardrails` (live · 2026-05-18)
- `state-overlay-langgraph` (live · 2026-05-18)
- `inbox-handler-mode-occ` (live · 2026-05-20)
- `adrian-reengagement-tool` (live · 2026-05-20)
<!-- auto-list:end -->

## Voice exception

Per `.claude/rules/sales-agent-brand-voice.md`: sales_agent OUTPUT respeta voz tenant (puede voseo es-AR). Slot 5 anchored per-tenant `personality_profile.system_instruction`. Medical guardrails hardcodeados aplican regardless de voz (4 invariants enforced via adversarial tests).

## HIPAA-lite vitalia overlay

Per `vitalia/.claude/rules/hipaa-lite.md`: dual filter tenant_id + clinic_id en queries PHI + audit log sync write antes response + sanitize_payload(compliance_level="hipaa_lite") en traces + channel guards WhatsApp tier free + SMS bloquean PHI outbound + RBAC strict (doctor/nurse/admin_clinic only para PHI fields canónicos).

## Dependencies

- `core/luana-core-sales-agent` (engine — state extended, NOT mirrored)
- `core/luana-core-observability.recording.base_callback_handler.BaseAgentCallbackHandler` (subclassed)
- `core/luana-core-compliance.ComplianceService` (validate_outbound_message wrapper)
- `core/luana-core-extension-sdk` (EP-3 ToolDef + EP-13 GuardrailDef registration)
