# Module — Scheduling (vitalia brand-extension)

> Brand: vitalia
> Owner: Valeria (asistente operativa)
> Status: live (post F2-S1 merge 2026-05-27)
> Pattern: ADR-vitalia-004 shell-feature-architecture (source story)
> Path: `vitalia/backend/src/modules/vitalia/scheduling/`

## Goal narrativa

Módulo scheduling de Vitalia maneja la agenda operativa de la clínica: calendario operativo día/semana/mes, drawer detalle por slot con datos paciente PHI-masked, subform inline para cobrar saldo (con emisión de comprobante fiscal sin salir del flujo), y filtros preset para los workflows recurrentes (turnos del día, pendientes confirmar, no-shows, saldos pendientes).

Consumido por Valeria sub-tab agenda dentro del shell-organism agéntico. Habilita el loop end-to-end con Adrián (reservas pre-pagadas → slot auto-creado) y Camila (post-visita → NPS trigger).

## Boundaries

- **Domain ownership:** scheduling brand-local extiende `core/luana-core-scheduling` (engine read-only). Mappings brand-specific (clinic_id, payment_status mirror, growth_studio events) viven aquí.
- **HIPAA-lite overlay:** dual filter `tenant_id + clinic_id`, audit log sync, PHI masking, sanitize_payload, RBAC roles médicos, ComplianceService channel guard.
- **No cross-brand mirror:** zero hits en nicolify/comunify/lupulo (verified anti-duplication scan).
- **Engine consumed via import:** `from luana_core_scheduling import Appointment, AppointmentRepository` (read-only, dual filter wrapper aplicado en infrastructure).

## Sub-modules dependents

- `vitalia/backend/src/modules/vitalia/payments/` — charge orchestrator saga + port impls + stubs (Option A pending vitalia-payment-adapter-mvp)
- `vitalia/backend/src/modules/vitalia/fiscal/` — fiscal document emit + stubs (Option A pending vitalia-fiscal-emission-pe)
- `vitalia/backend/src/modules/vitalia/_shared/phi_masking.py` — mask utils
- `vitalia/backend/src/modules/vitalia/_shared/telemetry/` — growth_studio_emitter + amount_bucket
- `vitalia/backend/src/modules/vitalia/audit/` — AsyncAuditWriter (consumed)
- `vitalia/backend/src/modules/vitalia/compliance/` — ComplianceService (consumed)

## Auto-list capabilities (AUTO-GENERATED por scripts/reconcile_capabilities.py — NO editar a mano)

<!-- AUTO-LIST START -->
| Capability | Status | Story introducer | Date | Path |
|---|---|---|---|---|
| valeria.agenda | live | vitalia-fase2-valeria-agenda | 2026-05-27 | `vitalia/docs/product/capabilities/scheduling/valeria-agenda.yaml` |
<!-- AUTO-LIST END -->

## Tables (Postgres)

| Table | Purpose | HIPAA dual filter |
|---|---|---|
| `vitalia_appointment_payments` | Payment records per appointment + optimistic lock + idempotency | tenant_id + clinic_id |
| `vitalia_fiscal_documents` | Comprobantes fiscales emitidos (PE boleta / AR factura / MX factura) | tenant_id + clinic_id |
| `vitalia_appointment_clinic_map` | Mapping engine appointments → brand-local clinic_id | tenant_id + clinic_id (PK composite) |
| `vitalia_growth_studio_event` | Telemetría brand-local (NO copilot_trace_event engine) | tenant_id + clinic_id |

## Future iterations

- F2-S2 vitalia-fase2-valeria-pacientes — drawer link "Ver ficha completa" habilitado (actualmente disabled tooltip)
- F2-S4 vitalia-fase2-adrian-embudo — stage "reservado" auto-crea slot agenda via API
- F2-S21 vitalia-fase2-config-conexiones — WebSocket subscribe tenant:{id}:scheduling (real-time replace polling 30s)
- Cleanup post-merge: W3 AgendaPlaceholder dead code en SubTabContent.tsx PLACEHOLDER_MAP

## Referencias

- Story source: `vitalia/docs/archive/2026/stories/vitalia-fase2-valeria-agenda/`
- ADR pattern: `vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md`
- HIPAA-lite overlay: `vitalia/.claude/rules/hipaa-lite.md`
- Shell mockup protocol: `vitalia/.claude/rules/shell-mockup-per-component.md`
