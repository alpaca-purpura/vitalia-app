---
story_id: vitalia-fase2-adrian-canal-inbound
brand: vitalia
doc: 03-arch-agentic
owner_builder: builder-agentic (flagship)
owner_auditor: auditor-agentic (flagship)
consumes: 03-arch.md · 02-design-agentic.md (v3)
lift_gated: true   # tools nuevos (book/match/share) BLOQUEADOS hasta lift /pm-vitalia ESC-1/2/3
---

# 03-arch-agentic — superficie agentic (Adrián)

> **Frontera dura:** lo de abajo se divide en **buildable hoy** (cero engine) y **lift-gated** (requiere
> `/pm-vitalia` ESC-1/2/3, ver 03-arch.md § Engine-boundary escalations). El `builder-agentic` arranca lo
> buildable; los tools nuevos esperan el lift. **§3 protected del engine NO se toca** (sales-agent-expert).

## 1 · Buildable hoy (cero engine)

### 1.1 EXTEND `state_overlay` (`domain/state_overlay.py`)
`VitaliaSalesAgentStateExtension` (TypedDict total=False) + keys: `recommended_doctor_id`,
`recommended_service_offer_id`, `candidate_slots`, `doctor_profile_shared_at`. NO se extiende `MeetingEntry`
del engine (frozen/slots → GAP-4); el `doctor_id`/`service_id` del meeting va en el overlay o en
`metadata_info` JSONB. `tenant_id`+`clinic_id` mandatorios.

### 1.2 Operator instruction wiring (`application/services/operator_instruction_service.py`)
REUSE `override_context_wire.set_override_context` → `metadata_info[operator_instructions]` (o reusar la key
existente `override_context`). Persistente (steerea todos los turnos hasta editar/limpiar — D1). SLOT volátil
(post cache-boundary), nunca cacheable. Audit row + activity NON-PHI (RN-15). El supervisor del engine ya honra
`[INSTRUCCION DEL OPERADOR]` con prioridad máxima (`supervisor_routing.j2`) — no se toca.

### 1.3 Persona / playbook tuning (`prompts/` + `personas/warm_close_*.yaml`)
Tune descubrimiento médico (reweight señales). **Guardrails éticos NO se tocan** (ya cubren no-diagnóstico/
no-overpromise/PHI/emergencia — `slot_4_medical_safety_rails.j2` + `forbidden_phrases`/`emergency_protocol`).
Voz = `personality_profiles` per-tenant (slot 5, cacheable 1h — **declarar `ttl:1h` explícito**, SOTA 2026-06-21).

### 1.4 Eval goldens (`goldens/`)
- honor-mode: decide→envía · consulta→borrador · pausa→silencio
- screening-gate: `DERIVAR_EMERGENCIA` → NO bookea, deriva + escala
- objection-trust: "¿quién me atiende?" → bio + (share_doctor_profile post-lift), sin overpromise
- ethical: NUNCA urgencia falsa / dark pattern
- book-* (post-lift): book-happy (slot por razonamiento, NO parser), book-no-isla (agenda Mateo + slot marcado),
  book-consulta, book-race (409→re-propone), hold-expira
- `trial_policy: {trials_per_scenario: 3, per_trial_pass_threshold: 0.66, pass_k_threshold: 0.5}`
- rubrics: `voice-fidelity`, `vertical-medical-fidelity`, `no-hallucination`, `no-overpromise`,
  `tool-trajectory`, `ethical-persuasion(no-dark-patterns)`.

## 2 · Lift-gated (requiere /pm-vitalia ESC-1/2/3 — NO generar ticket de builder hasta merge del lift)

### 2.1 `VitaliaSchedulerProvider` (`infrastructure/scheduler/vitalia_scheduler_provider.py`)
Impl del `SchedulerProvider` Protocol del engine (`runtime_checkable`):
```python
provider_id = "vitalia"
def get_available_slots(*, tenant_id, event_slug, days_ahead=14) -> list[SchedulerSlot]:
    # lee availability_slots libres (has_confirmed_appointment=False) filtrados por doctores
    # del servicio matcheado (offer_service_specialist_links). tenant+clinic scoped.
def create_booking_link(*, tenant_id, lead_id, event_slug, expires_in_hours=72) -> BookingLinkOutput:
    # crea turno en lane VIVO: scheduling/create_appointment_service(origin="proactivo_adrian")
    #   → marca availability_slot.has_confirmed_appointment=True + hold-status
def verify_booking_status(*, tenant_id, lead_id, tracking_id) -> BookingStatus:
    # resuelve hold→confirmed→expired desde el lane vivo (alimenta verify_pending_bookings worker)
```
Registro: `register_scheduler_provider(VitaliaSchedulerProvider)` en `extensions.py`. **⚠️ El routing
requiere ESC-1** (el resolver `scheduler_provider_for_tenant` debe elegirlo per-tenant).
**Sync vs async (decisión architect):** el Protocol del engine es **sync** (`def`, `db: Session`); los services
vitalia son async (`AsyncSession`). El provider corre en el contexto sync del engine tool → usa una sesión sync
o un bridge sync-wrapper sobre el service async (el engine ya provee `db: Session` al provider). **NO convertir
el Protocol a async (eso es engine).**

### 2.2 Tools nuevos (EP-3 — requieren ESC-2 merge + ESC-3 stage-scope)
- `match_service_and_specialist(service_intent)` → `{primary: doctor(bio_public+url), callbacks}` vía
  `offer_service_specialist_links` + disponibilidad. Stage: discovery/presentation.
- `share_doctor_profile(doctor_id)` → URL pública `/d/{clinica-slug}/{doctor-slug}` (trivial). Stage: presentation.
- `book_appointment(slot, doctor, offer, patient, origin=proactivo_adrian)` → tool fina → `VitaliaSchedulerProvider`.
  Stage: closing. Modo: decide=ejecuta · consulta=borrador. **Base portable:** el cuerpo de
  `agentic/tools/appointment_reschedule_with_doctor.py::propose_and_book` (tiene schema + lógica) — DEPRECAR
  esa ruta duplicada (dedup, §8 03-arch). Idempotencia por `(patient,doctor,slot)`.

### 2.3 Prompt slots (REUSE `compose.py`)
Slots 1-5 cacheable (declarar `ttl:1h`), 6-9 volátiles. `candidate_slots` en SLOT 8 (volátil) para el mapeo
por razonamiento. Forbidden en prefix cacheable: timestamps, conversation_id, chat_id, turn_counter, texto de
instrucción, candidate_slots, tenant_name interpolado mid-block.

## 3 · Observability (mandatory)
- `SalesAgentCallbackHandler` (subclasea `BaseAgentCallbackHandler` engine) → `sanitize_payload(compliance_level="hipaa_lite")`
  en CADA write a `sales_agent_trace_event` / `sales_agent_llm_call`. Best-effort (try/except + structlog + rollback).
- Trace: turn_start/turn_end + node/tool + honor-mode `{mode, paused, instruction_applied}`. PHI NUNCA en payload.
- Cost: tokens + cache_creation/cache_read + cost_usd (LiteLLM Chinese-first). Target ≥60% cache_read. BudgetGuard SA pool.

## 4 · Anti-patterns (sales-agent-expert §3 — PARAR si se cruzan)
- ❌ Editar `core/luana-core-sales-agent/src/` (orchestrator/graph/registry/providers/state). → `/pm-vitalia`.
- ❌ Migrar a deepagents / subagents deepagents. ❌ `from __future__ import annotations` en `graph.py`.
- ❌ Bypass `sanitize_payload`. ❌ Mirror `turn_envelope`/`callback_handler`. ❌ Tocar `PromptVersionModel`.
- ❌ Selección de slot con regex/parser/if-chain (bar no-`if`s). ❌ `BookingService`/`vitalia_bookings` (deprecado).
- ❌ Dos rutas de reschedule vivas. ❌ Voz neutro forzada en output del agente (respeta tenant).
