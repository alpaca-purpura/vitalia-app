---
story_id: vitalia-fase2-valeria-agenda
brand: vitalia
outcome: vitalia-mvp-ui-foundation
phase: fase-2
type: ui-story
module: scheduling
capability_target: scheduling/valeria-agenda
agent_owner: valeria
arch_version: 1
schema_version: v4.1
last_modified: 2026-05-27
generated_by: /architect (Opus 4.7 single-shot full-stack)
hipaa_lite_overlay: true
service_deps_status:
  vitalia-payment-adapter-mvp: refined          # blocker /dev-team — needs developed
  vitalia-fiscal-emission-pe: refining          # blocker /dev-team — needs developed
mockups_ratified: 10/10                          # 2026-05-26 batch_1 iter_1
---

# F2-S1 vitalia-fase2-valeria-agenda — 03-arch CONSOLIDADO

> Single-file architecture (BE + FE + cross-cutting). Architect run on **2026-05-27** via Opus 4.7 single-shot full-stack. **No agentic surface** — Valeria.agenda es sub-tab UI operativa (no LLM runtime).
>
> Story type: `ui-story` mixed (BE brand-extension nuevo + FE feature root + service-deps externos).

---

## § 0 — Context Summary

### 0.1 Surface → builder → auditor mapping (★ /dev-team spawn dispatcher)

| Surface | Paths primarios | Builder | Auditor | Owner pool |
|---|---|---|---|---|
| **BE — scheduling brand-extension** (NEW módulo) | `vitalia/backend/src/modules/vitalia/scheduling/{domain,infrastructure,application,api,persistence}/` | `builder-backend` (Sonnet) | `auditor-backend` (Opus) | `[qwen-opencode, claude-sonnet, claude-opus]` |
| **BE — payments brand-extension** (NEW módulo, consume payment-adapter-mvp) | `vitalia/backend/src/modules/vitalia/payments/{api,application}/` (separate from existing `vitalia/payment/` adapters) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) | idem |
| **BE — fiscal brand-extension** (NEW módulo, consume fiscal-emission-pe) | `vitalia/backend/src/modules/vitalia/fiscal/{api,application}/` | `builder-backend` (Sonnet) | `auditor-backend` (Opus) | idem |
| **FE — feature root + components** | `vitalia/frontend/src/features/valeria/{components/agenda,api,hooks,store,types}/` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) | idem |
| **FE — route page** | `vitalia/frontend/src/app/[tenantId]/(shell-organism)/valeria/agenda/page.tsx` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) | idem |
| **FE — Shadcn primitives install** | `vitalia/frontend/src/components/ui/{sheet,accordion,calendar,popover,select,form,sonner}.tsx` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) | idem |
| **Tests E2E Playwright** | `vitalia/frontend/e2e/shell-organism/*.spec.ts` + `e2e/__screenshots__/agenda/*.png` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) | idem |
| **BE tests** | `vitalia/backend/tests/modules/vitalia/scheduling/*.py` + `tests/architecture/*.py` | `builder-backend` (Sonnet) | `auditor-backend` (Opus) | idem |

**NO agentic surface.** Cero tickets `surface=AGENTIC`. Si emerge necesidad agentic (Valeria conversacional sobre slot, Camila trigger NPS) → escalate separadamente.

### 0.2 Skills consultadas (architect orchestrator)

| Skill | Decisión tomada | Anchor en CONTRACT |
|---|---|---|
| `backend-expert` | DDD Inside-Out + dual filter `tenant_id+clinic_id` via `PhiRepositoryBase` shared brand-local + raw-SQL idempotent migrations | § 2, § 3, § 5, § 9 |
| `frontend-expert` | FSD-Lite `features/valeria/components/agenda/` + Server-First page con `getInitialAgendaState` SSR + React Query + RHF/Zod + Shadcn `Sheet/Accordion` | § 6, § 7 |
| `playwright-expert` | Mandatory POMs + Clerk auth fixture + MSW network mocks + 14 visual goldens + axe a11y | § 11 § Test Construction Plan |
| `metrics-expert` | Telemetry → `growth_studio_event` table (NEW, brand-local, NO mezcla con `copilot_trace_event` engine) + bucketed amounts (no PHI) | § 10 |
| HIPAA-lite overlay rule | Dual filter mandatory en `Appointment` + `vitalia_audit_log` sync write antes response en cada PHI endpoint + sanitize_payload(`hipaa_lite`) + PHI masking visual | Cross-cutting § 8 |
| `.claude/rules/anti-duplication.md` | NEW brand-extension `scheduling/` — engine `core/luana-core-scheduling/Appointment` consumido READ-ONLY via repository, NO mirror | § Existing Systems Audit |
| `tessl__fastapi` | `redirect_slashes=False` ya satisfecho en `main.py` brand. response_model en cada endpoint nuevo | § 4 |
| `tessl__pytest-api-testing` | AsyncSession fixtures + dual-tenant test pattern + AsyncAuditWriter mock | § 11 |
| `tessl__react-patterns` | Server component page + `'use client'` para `ValeriaAgendaView` root client | § 6 |
| `tessl__shadcn-ui` | `npx shadcn@latest add sheet accordion calendar popover select form sonner` batch | § 6.1 |
| `tessl__zod` | Discriminated union schema por currency en `chargeSchema` | § 7.4 |
| `tessl__nextjs-app-router-modularization` | Route group `(shell-organism)/valeria/agenda/page.tsx` toma precedencia sobre dinámico `[agent]/[subtab]` | § 6.0 |
| `tessl__graceful-degradation` | Saga payment+fiscal con compensation: charge OK + fiscal fail → `<Alert variant=warning>` + retry-emit standalone | § 8.5 |

### 0.3 CONTEXT-BRIEF source

Direct reads (no `CONTEXT-BRIEF.md` produced by context-builder Haiku — story complejidad amerita architect direct grep). Self-ran greps Path B per `.claude/rules/anti-duplication.md`. Audit detail en § Existing Systems Audit.

### 0.4 capability YAML files affected (post-merge mandatory)

- **NEW:** `vitalia/docs/product/capabilities/scheduling/valeria-agenda.yaml` (capability `scheduling/valeria-agenda` promoción post-done)
- **MODIFY:** `vitalia/docs/product/modules/scheduling.md` (sección "Capabilities operativas" agregar entrada + auto-list regen via `scripts/reconcile_capabilities.py --brand vitalia`)
- **MODIFY (auto):** `vitalia/docs/product/BACKLOG.md` (gitignored — regen via `scripts/generate_backlog.py --brand vitalia`)

### 0.5 Architecture fitness gates (que deben mantenerse GREEN)

| Test | Path | Modificación |
|---|---|---|
| `test_phi_dual_filter.py` | `vitalia/backend/tests/architecture/` | EXTEND (nuevo `AppointmentDetailRepository` debe heredar `PhiRepositoryBase`) |
| `test_audit_log_sync_write.py` | `vitalia/backend/tests/architecture/` | EXTEND (cada nuevo endpoint PHI debe escribir audit_log row pre-response) |
| `test_response_model_required.py` | `vitalia/backend/tests/architecture/` | sin cambio (nuevos endpoints mandatory cumplen) |
| `test_no_observability_mirror.py` | `vitalia/backend/tests/architecture/` | sin cambio (no tocamos observability) |
| `test_extension_sdk_registration.py` | `vitalia/backend/tests/architecture/` | EXTEND (scheduling brand-extension registra EPs si aplica) |
| `test_scheduling_module_ddd.py` | `vitalia/backend/tests/architecture/` (★ NEW) | NEW arch test — enforces DDD boundaries en módulo scheduling brand-extension |
| `test_no_phi_in_url_params.py` | `vitalia/backend/tests/architecture/` (★ NEW) | NEW — whitelist query params + grep PHI fields |
| `test_no_legacy_eventbus_mock_when_outbox_on.py` | (engine + brand) | sin cambio (no flippea defaults) |

Allowlists shrink-only: nuevo módulo scheduling se agrega de cero (no expande allowlist legacy).

---

## § 1 — Existing Systems Audit (NO NEW LAYER rule)

### 1.1 Source of evidence

- [x] Self-run greps (Path B — fallback, sin `CONTEXT-BRIEF.md`)
- [ ] CONTEXT-BRIEF § 7 + § 8 (no producido para esta story)

### 1.2 Greps ejecutados

```bash
WS=/home/chalreme/Proyectos/luana-vitalia

# 1. Engine scheduling — qué existe shipped (read-only)
find ${WS}/core/luana-core-scheduling/src -name "*.py"
# → Appointment domain entity + AppointmentModel SQLA + AppointmentRepository + agenda.py API thin + AppointmentStatus enum (SCHEDULED|CANCELLED|COMPLETED|NO_SHOW)

# 2. Vitalia brand backend — qué módulos ya existen vs NEW
ls ${WS}/vitalia/backend/src/modules/vitalia/
# → admin agentic api application audit clinics compliance connections copilot crm fidelizacion iam inbox infrastructure marketing payment persistence sales_agent _shared
# → NO scheduling/ · NO payments/ (singular `payment/` con adapters scaffold) · NO fiscal/

# 3. PhiRepositoryBase shared
cat ${WS}/vitalia/backend/src/modules/vitalia/_shared/repositories/phi_repository.py
# → Abstract base + dual filter + validate_dual_filter + MissingClinicFilterError ya existe — REUSE

# 4. Audit writer
cat ${WS}/vitalia/backend/src/modules/vitalia/audit/audit_writer.py
# → write_audit_log_sync + AsyncAuditWriter ya existen — REUSE

# 5. Compliance service
ls ${WS}/vitalia/backend/src/modules/vitalia/compliance/
# → ComplianceService + phi_fields.py + whatsapp_free_phi_guard.py + medical_results_guard.py — REUSE

# 6. Cross-brand mirror check (HARD ban)
for B in nicolify comunify lupulo; do
  grep -rln "AppointmentDrawer\|AgendaSlot\|scheduling" ${WS}/$B/backend/src/ 2>/dev/null | head -3
done
# → nicolify/comunify/lupulo NO tienen módulo scheduling — zero mirror risk
```

### 1.3 Sistemas existentes encontrados

| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| Engine `Appointment` domain + model | `core/luana-core-scheduling/src/luana_core_scheduling/{domain/appointment.py, infrastructure/models/appointment_model.py, infrastructure/repositories/appointment_repository.py}` | shipped, single-tenant agnostic | **EXTEND via consumer** (no mirror): brand-local `Vitalia AppointmentDetailService` consume `AppointmentRepository` engine vía import |
| Engine `AppointmentStatus` enum (SCHEDULED/CANCELLED/COMPLETED/NO_SHOW) | `core/luana-core-scheduling/src/luana_core_scheduling/domain/enums.py` | shipped | REUSE 100%. Brand añade overlay enum `AppointmentOrigin(walk_in/telefono/proactivo_adrian)` brand-local (no leak a engine) |
| `Patient` model + PHI masking | `vitalia/backend/src/modules/vitalia/crm/domain/patient.py` | shipped | REUSE — consume vía API `/api/crm/patients` y dependency injection servicios cruzados (mediante port-style import) |
| `Clinic` model + tenant_clinic junction | `vitalia/backend/src/modules/vitalia/clinics/` | shipped | REUSE — `clinic_id` mandatory en queries scheduling |
| `PhiRepositoryBase` dual-filter | `vitalia/backend/src/modules/vitalia/_shared/repositories/phi_repository.py` | shipped | REUSE — `AppointmentDetailRepository` y `AgendaGridRepository` brand-local heredan |
| `write_audit_log_sync` + `AsyncAuditWriter` | `vitalia/backend/src/modules/vitalia/audit/audit_writer.py` | shipped | REUSE — cada endpoint PHI escribe via AsyncAuditWriter |
| `ComplianceService.validate_outbound_message` | `vitalia/backend/src/modules/vitalia/compliance/application/compliance_service_adapter.py` | shipped | REUSE — endpoint `/api/v1/scheduling/appointments/{id}/notify` invoca guard pre-send |
| `sanitize_payload(compliance_level='hipaa_lite')` | `core/luana-core-observability/src/luana_core_observability/recording/sanitization.py` | shipped | REUSE — telemetry events + audit log payload + sentry capture |
| Payment adapters scaffold (Stripe Connect + MercadoPago) | `vitalia/backend/src/modules/vitalia/payment/{stripe_connect_adapter,mercadopago_adapter}.py` | scaffold (story `vitalia-payment-adapter-mvp` refined NOT developed) | **CONSUME via service-blocker pattern** — `vitalia/backend/src/modules/vitalia/payments/api/charge_router.py` NEW abstrae el adapter del tenant (gateway selector); si service-blocker NO developed → MSW mocks Opción A (§ 8.6) |
| Fiscal emission Nubefact PE | `vitalia/backend/src/modules/vitalia/fiscal/` | **NO existe** (story `vitalia-fiscal-emission-pe` refining) | **NEW módulo brand-extension** con stub interface — implementación real lift cuando service-blocker developed |
| `vitalia_audit_log` table | DDL gestionado por audit module | shipped | REUSE — agregar `resource_type='appointment_*'` + `action='charge'/'status_change'/'send_notification'/'read_appointment_detail'` (sin nueva tabla) |
| `growth_studio_event` table (telemetry) | NO existe vitalia | greenfield | **NEW brand-local migration** — separa de `copilot_trace_event` engine (no mezcla agentic LLM cost con UX telemetry); architect ratifica decisión spec § 10 |
| Cross-brand mirror (nicolify/comunify/lupulo) | n/a | zero match | OK |

### 1.4 Decisión por sistema (EXTEND > REPLACE > NEW)

- **Sistema `Appointment` engine** → **EXTEND via consumer** (read-only). Brand-local `AgendaGridRepository` envuelve `AppointmentRepository` engine + agrega dual filter `clinic_id` mediante composite WHERE en query SQL crudo (engine repo no soporta `clinic_id` nativamente; agregar engine modify requeriría `/pm-luana` promotion proposal — out-of-scope F2-S1). **Justificación:** filter `clinic_id` se aplica brand-local en repo crudo via `select(AppointmentModel).where(...)` reutilizando model engine + agregando filtros vitalia (HIPAA-lite). NO mirror, NO core modify.
- **`AppointmentStatus` enum** → **REUSE 100%**. NEW `AppointmentOrigin` (walk_in/telefono/proactivo_adrian) brand-local vive en `vitalia/scheduling/domain/appointment_origin.py` (StrEnum) — vitalia-specific, no candidate para engine lift.
- **`Patient` model** → **REUSE via existing `crm` module port-style**. Drawer FE consume API REST `/api/v1/crm/patients/{id}` (PHI masked en response). NO import cross-module BE directo (DDD arch test).
- **Payment adapters scaffold** → **CONSUME via NEW `payments/` brand-extension API thin**. `POST /api/v1/payments/charge` mediante `vitalia.payments.application.ChargeOrchestrator` selecciona adapter del tenant (`tenant.config.payment_gateway`) — wraps Stripe/MP/efectivo. Si `vitalia-payment-adapter-mvp` NO developed al pickup → MSW mock + interface stub `PaymentChargePort` (§ 8.6).
- **Fiscal emission** → **NEW `fiscal/` brand-extension** con `FiscalEmitPort` interface. Implementación real arriva con `vitalia-fiscal-emission-pe` story; F2-S1 entrega stub + endpoint thin con MSW mock pattern.
- **`vitalia_audit_log`** → **REUSE 100%** — agregar nuevas `action` values dentro del enum string (no schema change). Migration sólo si necesitamos column nueva — en F2-S1 NO (current schema cubre).
- **`growth_studio_event`** → **NEW brand-local table** + idempotent migration. Justificación: agentic events viven en `copilot_trace_event` engine (cost+LLM concerns); UX/funnel events son orthogonal (sin LLM call, sin agentic state). Lift candidate cross-brand cuando ≥2 brands quieran funnel — `/pm-luana` futuro.
- **Cross-brand mirror** → **N/A** (zero match). Pattern `AppointmentDrawer + Sheet + Accordion` puede ser lift candidate cuando ≥2 brands necesiten drawer right-side con secciones colapsables (escalate `/pm-luana` futuro core/luana-core-ui/) — NO blocker F2-S1.

**Engine boundary respect:** zero edits a `core/luana-core-*/src/`. Si scope requiere → escalate `/pm-luana` promotion proposal explícita (out-of-scope F2-S1).


---

## § 2 — Domain Entities (BE)

### 2.1 Brand-local domain entities NEW

`vitalia/backend/src/modules/vitalia/scheduling/domain/`

```python
# appointment_origin.py
from enum import StrEnum

class AppointmentOrigin(StrEnum):
    """Vitalia-specific origin enum for agenda slot UI badge.

    Brand-local. Engine Appointment is origin-agnostic.
    """
    WALK_IN = "walk_in"               # paciente walk-in (sin agendamiento previo)
    TELEFONO = "telefono"             # reserva telefónica (staff manual)
    PROACTIVO_ADRIAN = "proactivo_adrian"  # auto-creada por flujo embudo Adrián
    PORTAL = "portal"                 # paciente auto-agendó portal público
```

```python
# agenda_filter.py
from enum import StrEnum

class AgendaPresetFilter(StrEnum):
    """Whitelist preset filters Agenda. Cualquier query-param fuera de este enum es rechazado."""
    HOY = "hoy"
    POR_CONFIRMAR_MANANA = "por_confirmar_manana"
    REAGENDAR_PENDIENTES = "reagendar_pendientes"
    NO_SHOWS_DIA = "no_shows_dia"
    SALDOS_PENDIENTES = "saldos_pendientes"
```

```python
# agenda_view.py
from enum import StrEnum

class AgendaView(StrEnum):
    DIA = "dia"
    SEMANA = "semana"   # default
    MES = "mes"
```

```python
# payment_method.py
from enum import StrEnum

class PaymentMethod(StrEnum):
    EFECTIVO = "efectivo"
    TARJETA = "tarjeta"
    TRANSFERENCIA = "transferencia"
    MERCADO_PAGO = "mercado_pago"
    OTRO = "otro"
```

```python
# fiscal_doc_type.py
from enum import StrEnum

class FiscalDocType(StrEnum):
    # PE
    BOLETA = "boleta"
    FACTURA = "factura"
    # AR
    FACTURA_B = "factura_b"
    FACTURA_A = "factura_a"
    RECIBO = "recibo"
    # MX
    CFDI = "cfdi"
    # generic
    TICKET = "ticket"
```

### 2.2 Slot DTO (no SQLA table — projection)

Slot es DTO de presentación derivado de `Appointment` engine + balance computado (`AppointmentPayment` brand-local) + PHI mask aplicada. NO se persiste como tabla independiente.

```python
# vitalia/backend/src/modules/vitalia/scheduling/domain/agenda_slot.py
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

class SlotPaymentStatus(StrEnum):
    PAGADO = "pagado"           # 🟢 balance == 0 + has payments
    DEPOSITO = "deposito"       # 🟡 balance > 0 + has payments
    SIN_PAGO = "sin_pago"       # 🔴 balance > 0 + no payments
    NO_SHOW = "no_show"         # ⚫ status==NO_SHOW

@dataclass(frozen=True)
class AgendaSlot:
    """Domain projection — calendar cell shape for FE."""
    appointment_id: UUID
    tenant_id: UUID
    clinic_id: UUID
    patient_id: UUID
    patient_name_masked: str          # "P. Hernández" — never PII
    start_time: datetime              # tz-aware UTC
    end_time: datetime
    doctor_id: UUID
    doctor_label: str                 # display name (NO PHI)
    service_label: str                # "Limpieza dental"
    appointment_status: str           # AppointmentStatus value
    payment_status: SlotPaymentStatus
    origin: str                       # AppointmentOrigin value
    balance_due: int | None           # cents
    balance_paid: int | None          # cents
    currency: str                     # ISO 4217 (PEN/ARS/USD/MXN/...)
    currency_override: str | None     # set when appointment.currency != tenant default
```

### 2.3 AppointmentPayment (NEW brand-local persisted)

```python
# vitalia/backend/src/modules/vitalia/scheduling/domain/appointment_payment.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

@dataclass
class AppointmentPayment:
    id: UUID                          # PK
    tenant_id: UUID                   # mandatory
    clinic_id: UUID                   # mandatory (HIPAA dual filter)
    appointment_id: UUID              # FK → engine appointments.id
    amount: int                       # cents (Money store as int)
    currency: str                     # ISO 4217
    method: str                       # PaymentMethod value
    external_payment_id: str | None   # Stripe/MP transaction ref
    fiscal_doc_id: UUID | None        # FK → fiscal_documents.id (nullable until emit)
    notes: str | None
    balance_version: int = 1          # optimistic lock (SC-5 race condition)
    deleted_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by_user_id: UUID | None = None
```

### 2.4 FiscalDocument (NEW brand-local, stub-friendly)

```python
# vitalia/backend/src/modules/vitalia/fiscal/domain/fiscal_document.py
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass
class FiscalDocument:
    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    appointment_payment_id: UUID      # FK → appointment_payments.id
    doc_type: str                     # FiscalDocType value
    doc_number: str | None            # provider-issued serial
    doc_url: str | None               # PDF/XML link
    provider: str                     # "nubefact" | "afip" | "sat" | "stub"
    status: str                       # "pending"|"emitted"|"failed"
    error_message: str | None
    deleted_at: datetime | None
    created_at: datetime
```

---

## § 3 — SQLAlchemy 2.0 Models

### 3.1 `appointment_payments` (brand-local NEW)

`vitalia/backend/src/modules/vitalia/scheduling/persistence/models/appointment_payment_model.py`

```python
from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column


class VitaliaAppointmentPaymentModel(Base):
    """SA 2.0 model — vitalia brand-local appointment_payments table."""

    __tablename__ = "vitalia_appointment_payments"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    appointment_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)   # cents
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    external_payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    fiscal_doc_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("vitalia_fiscal_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    balance_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by_user_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

Composite indexes via migration:
- `idx_vit_payment_tenant_clinic_apt` `(tenant_id, clinic_id, appointment_id)` — dual filter + drawer fetch
- `idx_vit_payment_external` `(external_payment_id) WHERE external_payment_id IS NOT NULL` — idempotency lookup

### 3.2 `vitalia_fiscal_documents` (brand-local NEW)

```python
class VitaliaFiscalDocumentModel(Base):
    __tablename__ = "vitalia_fiscal_documents"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    appointment_payment_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), nullable=False, index=True,
    )
    doc_type: Mapped[str] = mapped_column(String(32), nullable=False)
    doc_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    doc_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

### 3.3 `growth_studio_event` (brand-local telemetry NEW)

```python
class GrowthStudioEventModel(Base):
    __tablename__ = "vitalia_growth_studio_event"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True, index=True)
    user_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    event_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    props_sanitized: Mapped[dict] = mapped_column("props", JSONB, nullable=False, default=dict)  # noqa
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
```

(JSONB import from `sqlalchemy.dialects.postgresql`.)

### 3.4 Engine `appointments` table — NO modify

Engine `appointments` (`core/luana-core-scheduling`) shipped sin `clinic_id` column. Per § 1.4: brand-local repository agrega `clinic_id` filter via JOIN con tabla brand-local relationship (NO modify engine schema). Implementación: tabla brand `vitalia_appointment_clinic_map` (NEW lightweight join).

```python
class VitaliaAppointmentClinicMapModel(Base):
    """Brand-local clinic_id binding for engine appointments.

    Engine `appointments` table doesn't carry clinic_id (single-tenant in engine).
    Brand-local map enables HIPAA dual-filter without engine modify.
    """
    __tablename__ = "vitalia_appointment_clinic_map"

    appointment_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    patient_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    doctor_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    service_label: Mapped[str] = mapped_column(String(128), nullable=False)
    origin: Mapped[str] = mapped_column(String(32), nullable=False)
    currency_override: Mapped[str | None] = mapped_column(String(3), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

`AgendaGridRepository` JOIN `appointments` ⨝ `vitalia_appointment_clinic_map` por `appointment_id`, filtra `tenant_id + clinic_id` brand-local.

---

## § 4 — Pydantic v2 DTOs

### 4.1 Agenda grid DTOs

`vitalia/backend/src/modules/vitalia/scheduling/api/dtos/agenda_dtos.py`

```python
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgendaSlotDTO(BaseModel):
    """Slot projection PHI-masked — sent to FE."""
    model_config = ConfigDict(from_attributes=True)

    appointment_id: UUID
    patient_id: UUID                  # opaque ref (FE uses for drawer fetch only)
    patient_name_masked: str          # "P. Hernández"
    start_time: datetime              # tz-aware
    end_time: datetime
    doctor_id: UUID
    doctor_label: str
    service_label: str
    appointment_status: str           # SCHEDULED|CANCELLED|COMPLETED|NO_SHOW
    payment_status: str               # pagado|deposito|sin_pago|no_show
    origin: str                       # walk_in|telefono|proactivo_adrian|portal
    balance_due_cents: int | None     # nullable: appointment without payment record
    balance_paid_cents: int | None
    currency: str                     # ISO 4217


class AgendaGridResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    view: str                         # dia|semana|mes
    date_from: datetime
    date_to: datetime
    slots: list[AgendaSlotDTO]
    server_time: datetime             # for FreshnessIndicator
    clinic_id: UUID
    tenant_id: UUID


class AgendaAggregatesResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    class DayAggregate(BaseModel):
        model_config = ConfigDict(from_attributes=True)
        date: str                     # YYYY-MM-DD
        total_slots: int
        status_breakdown: dict[str, int]  # {"pagado": N, "deposito": N, ...}

    month: str                        # YYYY-MM
    days: list[DayAggregate]


class AppointmentDetailDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    appointment_id: UUID
    patient_id: UUID
    patient_name_masked: str          # "P. Hernández"
    patient_dni_masked: str | None    # "12.***.***"
    patient_phone_masked: str | None  # "+51 9** *** 423"
    patient_email_masked: str | None  # "p***@gmail.com"
    start_time: datetime
    end_time: datetime
    doctor_id: UUID
    doctor_label: str
    service_label: str
    appointment_status: str
    payment_status: str
    origin: str
    balance_due_cents: int | None
    balance_paid_cents: int | None
    currency: str
    currency_override: str | None
    payments: list["AppointmentPaymentDTO"]
    notes_internal: str | None        # staff-facing (NO clinical PHI)
    last_activity_at: datetime | None
    last_activity_by_label: str | None  # staff label (NO PHI)


class AppointmentPaymentDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    payment_id: UUID
    amount_cents: int
    currency: str
    method: str
    fiscal_doc_url: str | None
    fiscal_doc_type: str | None
    created_at: datetime
    created_by_label: str | None
```

### 4.2 Charge DTOs

`vitalia/backend/src/modules/vitalia/payments/api/dtos/charge_dtos.py`

```python
from typing import Literal

class ChargeRequestDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    appointment_id: UUID
    amount_cents: int = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    method: Literal["efectivo", "tarjeta", "transferencia", "mercado_pago", "otro"]
    emit_invoice: bool = True
    fiscal_doc_type: str | None = None    # required if emit_invoice=true
    notes: str | None = Field(None, max_length=500)
    idempotency_key: str = Field(..., min_length=10, max_length=128)  # client-generated


class ChargeResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    payment_id: UUID
    amount_cents: int
    currency: str
    method: str
    external_payment_id: str | None
    fiscal_doc_id: UUID | None
    fiscal_doc_url: str | None
    fiscal_emission_status: Literal["emitted", "pending", "failed", "skipped"]
    fiscal_error_message: str | None


class ChargeConflict409DTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    error_code: Literal["BALANCE_ALREADY_CHARGED"]
    message: str
    latest_balance_due_cents: int | None
    latest_payment_status: str
```

### 4.3 Fiscal emit DTOs

```python
class FiscalEmitRequestDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    appointment_payment_id: UUID
    doc_type: str
    idempotency_key: str = Field(..., min_length=10, max_length=128)


class FiscalEmitResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    fiscal_doc_id: UUID
    doc_type: str
    doc_number: str | None
    doc_url: str | None
    status: Literal["emitted", "pending", "failed"]
    error_message: str | None
```

### 4.4 Create + Patch appointment DTOs

```python
class CreateAppointmentRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    origin: Literal["walk_in", "telefono", "desde_paciente_existente"]
    patient_id: UUID | None           # required if origin=desde_paciente_existente
    patient_new_data: "PatientNewDataDTO | None"  # required if walk_in or telefono
    doctor_id: UUID
    service_label: str = Field(..., min_length=1, max_length=128)
    start_time: datetime
    end_time: datetime
    notes_internal: str | None = Field(None, max_length=500)
    currency_override: str | None = None


class PatientNewDataDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=2, max_length=128)
    dni: str | None = Field(None, max_length=32)
    phone: str = Field(..., min_length=6, max_length=24)
    email: str | None = None


class PatchAppointmentRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    new_status: Literal["CANCELLED", "COMPLETED", "NO_SHOW"]
    reason: str | None = Field(None, max_length=500)


class SendNotificationRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    template_id: str = Field(..., min_length=1, max_length=64)
    channel: Literal["whatsapp"]
```

### 4.5 Suspicious request log (PHI-bypass detection)

```python
class SuspiciousRequestLogDTO(BaseModel):
    """Audit trail entry para queries con PHI en URL. Internal use."""
    model_config = ConfigDict(from_attributes=True)
    request_path: str
    bypass_params: list[str]          # keys del query rechazados
    client_ip: str | None
    user_agent: str | None
```

---

## § 5 — API Routes

All routes under `/api/v1/...`. `Bearer` (Clerk session) + `X-Tenant-ID` header (middleware-derived) + `X-Clinic-ID` header (HIPAA-lite mandatory, derived from RBAC token claims). `FastAPI(redirect_slashes=False)` already enforced en `vitalia/backend/src/main.py`.

### 5.1 Routes table

| Method | Path | Auth | Request DTO | response_model | RBAC roles | Description |
|---|---|---|---|---|---|---|
| GET | `/api/v1/scheduling/agenda/grid` | Bearer + Tenant + Clinic | (query: view, date, preset_filter) | `AgendaGridResponseDTO` | valeria_assistant, doctor, nurse, admin_clinic | Slots for view+date with dual filter + whitelist params |
| GET | `/api/v1/scheduling/agenda/aggregates` | idem | (query: month YYYY-MM) | `AgendaAggregatesResponseDTO` | idem | Month counts (NO bulk slots) |
| GET | `/api/v1/scheduling/appointments/{appointment_id}` | idem | — | `AppointmentDetailDTO` | idem | Drawer detail (PHI masked + dual filter + audit log row) |
| POST | `/api/v1/scheduling/appointments` | idem | `CreateAppointmentRequestDTO` | `AppointmentDetailDTO` | idem | Crear cita (walk-in/teléfono/desde-existente) |
| PATCH | `/api/v1/scheduling/appointments/{id}/status` | idem | `PatchAppointmentRequestDTO` | `AppointmentDetailDTO` | idem | Cancel/complete/no-show + audit log + Dialog confirm flow upstream FE |
| POST | `/api/v1/scheduling/appointments/{id}/notify` | idem | `SendNotificationRequestDTO` | `{status: "sent"}` | idem | Template-only WhatsApp + ComplianceService guard |
| POST | `/api/v1/payments/charge` | idem | `ChargeRequestDTO` | `ChargeResponseDTO` (200) / `ChargeConflict409DTO` (409) | idem | Saga charge + emit (consume payment-adapter-mvp) |
| POST | `/api/v1/fiscal/emit` | idem | `FiscalEmitRequestDTO` | `FiscalEmitResponseDTO` | idem | Emit comprobante (consume fiscal-emission-pe) |

### 5.2 Query-param whitelist + suspicious request log

`agenda/grid` accepted query params (HARD whitelist enforced by arch test `test_no_phi_in_url_params.py`):

```python
ALLOWED_GRID_PARAMS = frozenset(["view", "date", "preset_filter"])
```

Cualquier param fuera → router descarta + emite `audit_log` row con `action="suspicious_request"`, `payload_redacted={"path": req.path, "bypass_params": <keys>}`, sin contenido del valor PHI.

### 5.3 RBAC decorator

```python
# vitalia/backend/src/modules/vitalia/_shared/auth/rbac.py (extend)
ALLOWED_PHI_ROLES = frozenset(["valeria_assistant", "doctor", "nurse", "admin_clinic"])

def require_phi_access(roles: frozenset[str] = ALLOWED_PHI_ROLES):
    """FastAPI dependency that 403s if user.role NOT IN roles."""
    async def _dep(user=Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, detail={"error_code": "PHI_RBAC_DENIED"})
        return user
    return _dep
```

Every PHI route decorated `Depends(require_phi_access())`.

### 5.4 Idempotency strategy

- POST `/payments/charge` + POST `/fiscal/emit`: `idempotency_key` field in body (client-generated UUID). Repo lookup `WHERE tenant_id+clinic_id+external_payment_id == idempotency_key` antes de procesar → si match retornar resultado previo.
- PATCH `/appointments/{id}/status`: idempotent por design (state machine — same `to_status` no-op).
- POST `/appointments`: server-generated `appointment_id` UUID. Cliente repite → mismo response si already existed (dedup natural).


---

## § 6 — Frontend Architecture

### 6.0 Route resolution (Next.js 16 App Router)

Folder structure post F2-S1:

```
vitalia/frontend/src/app/[tenantId]/(shell-organism)/
├── [agent]/                          # dynamic — unchanged F1-S10
│   ├── [subtab]/page.tsx             # dispatcher SubTabContent (defaults to placeholder)
│   ├── page.tsx                      # agent overview
│   └── layout.tsx
├── valeria/                          # ★ NEW static segment — more specific takes precedence
│   └── agenda/
│       └── page.tsx                  # ★ NEW server component (this story)
└── layout.tsx                        # global shell-organism layout
```

**Routing rule:** Next.js App Router resolves the more specific static segment first. `/{tenant}/valeria/agenda` hits the new dedicated `valeria/agenda/page.tsx`, NOT `[agent]/[subtab]/page.tsx`. Other Valeria subtabs (pacientes, mensajes, reportes) keep using the dispatcher dynamic route → `AgendaPlaceholder` is **archived/deleted** post-merge (replaced by real feature).

### 6.1 Shadcn primitives — batch install

Run in `vitalia/frontend/`:

```bash
npx shadcn@latest add sheet accordion calendar popover select form sonner
```

Primitives target paths: `vitalia/frontend/src/components/ui/{sheet,accordion,calendar,popover,select,form,sonner}.tsx`.
Tailwind tokens enforced — NO hex literals. All primitives consume CSS vars `--background`, `--foreground`, `--primary`, `--destructive`, etc. from `vitalia/frontend/src/app/globals.css`.

### 6.2 FSD-Lite layout (feature root + sub-components)

```
vitalia/frontend/src/features/valeria/
├── index.ts                          # public API — re-exports placeholders + components
├── components/
│   ├── placeholders/
│   │   ├── AgendaPlaceholder.tsx     # ★ DEPRECATED — keep until F2-S1 merge then delete
│   │   ├── PacientesPlaceholder.tsx  # unchanged
│   │   └── ...
│   └── agenda/
│       ├── ValeriaAgendaView.tsx          # client root
│       ├── AgendaHeader.tsx               # view-toggle + date-picker + FreshnessIndicator
│       ├── AgendaCalendar.tsx             # dispatcher day/week/month
│       ├── DayCalendar.tsx                # variant (react-window virtualization)
│       ├── WeekCalendar.tsx               # variant default
│       ├── MonthCalendar.tsx              # variant (aggregates dots)
│       ├── AgendaSlot.tsx                 # molecule cell (PHI-masked + border-status + origin-badge)
│       ├── AgendaPresetFilters.tsx        # 5 chips single-select
│       ├── CrearCitaButton.tsx            # DropdownMenu 3 opciones
│       ├── CrearCitaForm.tsx              # form unificado walk-in/telefono/existing
│       ├── PatientAutocomplete.tsx        # Combobox + debounced search
│       ├── AppointmentDrawer.tsx          # Sheet wrapper 5 acordeones
│       ├── AppointmentDrawerSkeleton.tsx  # loading state
│       ├── CobrarSaldoSubform.tsx         # ★ corazón valor F2-S1
│       ├── FreshnessIndicator.tsx         # "Actualizado hace Xs" + refresh manual
│       ├── MobileBottomSheet.tsx          # <md responsive wrapper
│       ├── SkeletonCalendar.tsx           # idle pre-fetch placeholder
│       └── __tests__/                     # Vitest unit tests co-located
├── api/
│   ├── agenda.ts                          # useAgendaGrid + useAggregates + useAppointmentDetail
│   ├── agenda-server.ts                   # getInitialAgendaState (SSR fetch)
│   ├── payments.ts                        # useChargeMutation
│   ├── fiscal.ts                          # useFiscalEmitMutation
│   ├── notify.ts                          # useSendNotificationMutation
│   └── __tests__/
├── hooks/
│   ├── useAgendaFilters.ts                # URL params persist
│   ├── useDrawerWidth.ts                  # localStorage 440-640px
│   └── useFreshness.ts                    # computed from dataUpdatedAt
├── store/
│   ├── drawer-store.ts                    # zustand: selectedSlotId+isOpen+drawerWidth
│   └── filters-store.ts                   # zustand: chip activo + URL sync
└── types/
    ├── agenda.types.ts                    # AgendaSlot, AppointmentDetail, Payment
    └── agenda-schema.ts                   # Zod schemas (chargeSchema discriminated union)
```

### 6.3 Page server component (entry)

`vitalia/frontend/src/app/[tenantId]/(shell-organism)/valeria/agenda/page.tsx`

```tsx
// Server Component — no "use client"
import { ValeriaAgendaView } from "@/features/valeria";
import { getInitialAgendaState } from "@/features/valeria/api/agenda-server";

interface PageProps {
  params: Promise<{ tenantId: string }>;
  searchParams: Promise<{ view?: string; date?: string; preset_filter?: string }>;
}

export default async function ValeriaAgendaPage({ params, searchParams }: PageProps) {
  const { tenantId } = await params;
  const sp = await searchParams;
  const view = sp.view ?? "semana";
  const date = sp.date ?? new Date().toISOString().slice(0, 10);
  const presetFilter = sp.preset_filter ?? null;

  // SSR initial state (single fetch, cookie auth, X-Tenant-ID header propagated)
  const initialData = await getInitialAgendaState({ tenantId, view, date, presetFilter });

  return (
    <ValeriaAgendaView
      initialData={initialData}
      initialView={view}
      initialDate={date}
      initialPresetFilter={presetFilter}
    />
  );
}
```

`getInitialAgendaState` uses `fetch()` server-side with cookies forwarded. NO PHI in URL (params + searchParams whitelist enforced upstream).

### 6.4 ValeriaAgendaView root client

`features/valeria/components/agenda/ValeriaAgendaView.tsx`

```tsx
"use client";

interface ValeriaAgendaViewProps {
  initialData: AgendaGridResponseDTO;
  initialView: "dia" | "semana" | "mes";
  initialDate: string;
  initialPresetFilter: string | null;
}

export function ValeriaAgendaView(props: ValeriaAgendaViewProps) {
  // 1. Hydrate React Query cache with initialData
  // 2. useAgendaGrid({ view, date, presetFilter }) with placeholderData=initialData + refetchInterval=30_000
  // 3. useDrawerStore() for drawer state
  // 4. useAgendaFilters() for URL params + chip state sync
  // 5. Compose: AgendaHeader + AgendaPresetFilters + AgendaCalendar + CrearCitaButton + AppointmentDrawer
  return (
    <main aria-label="Agenda">
      <AgendaHeader />
      <AgendaPresetFilters />
      <AgendaCalendar />
      {/* Mobile FAB fixed bottom-right, hidden md+ */}
      <CrearCitaButton variant="fab" className="md:hidden" />
      <AppointmentDrawer />
      <Toaster /> {/* Sonner */}
    </main>
  );
}
```

### 6.5 AgendaSlot (molécula)

Visual contract (per mockup `slot-states-matrix.html`):

```tsx
"use client";
import { cn } from "@/lib/utils";

const STATUS_BORDER_CLASS: Record<SlotPaymentStatus, string> = {
  pagado:   "border-l-[3px] border-l-[var(--color-success)]",
  deposito: "border-l-[3px] border-l-[var(--color-warning)]",
  sin_pago: "border-l-[3px] border-l-[var(--color-destructive)]",
  no_show:  "border-l-[3px] border-l-[var(--muted-foreground)]",
};

const ORIGIN_BADGE_ICON: Record<AppointmentOrigin, string> = {
  walk_in: "👤",
  telefono: "📞",
  proactivo_adrian: "🤖",
  portal: "🌐",
};

export function AgendaSlot({ slot, onClick }: { slot: AgendaSlotDTO; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-md bg-card hover:bg-accent transition-colors p-2 text-left",
        "focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none",
        STATUS_BORDER_CLASS[slot.payment_status],
      )}
      role="button"
      aria-haspopup="dialog"
      aria-label={`Slot ${formatTime(slot.start_time)} ${dayOfWeekEs(slot.start_time)} · ${slot.patient_name_masked} · ${slot.service_label} · estado ${slot.payment_status}`}
    >
      <div className="flex items-start justify-between">
        <PHIMaskedText className="font-medium text-sm">{slot.patient_name_masked}</PHIMaskedText>
        <span aria-hidden className="text-xs">{ORIGIN_BADGE_ICON[slot.origin]}</span>
      </div>
      <div className="text-xs text-muted-foreground mt-1">
        {slot.service_label} · {formatTime(slot.start_time)}
      </div>
    </button>
  );
}
```

### 6.6 AppointmentDrawer (Sheet + Accordion)

- `<Sheet open={isOpen} onOpenChange={setOpen} side="right">` desktop
- Mobile (<md): `<MobileBottomSheet>` wraps with `side="bottom"`, 95vh
- Drawer width: `useDrawerWidth()` reads `localStorage.vitalia.agenda.drawerWidth` (default 440px). Drag handle on left edge — Pointer events update width 440-640px, debounced 100ms write to localStorage
- 5 acordeones via Shadcn `<Accordion type="multiple" defaultValue={["turno", "pago"]}>`:
  1. `turno` (expanded default)
  2. `pago` (expanded default — contains `CobrarSaldoSubform`)
  3. `historico` (collapsed)
  4. `notas` (collapsed)
  5. `acciones-avanzadas` (collapsed)
- Header: `<PHIMaskedText>` for name + DNI + "Ver ficha completa" disabled button + `<Tooltip>` "Pacientes — próximamente disponible en Fase 2"
- Action gates: Cancelar + No-show open `<Dialog>` confirm via existing `<Dialog>` primitive (shipped F1)
- ARIA: `role="dialog"` + `aria-modal="true"` + `aria-labelledby="drawer-title"` + focus trap (Sheet handles internally)

### 6.7 CobrarSaldoSubform (★ corazón valor)

Zod schema discriminated union by currency:

```ts
// agenda-schema.ts
const baseChargeSchema = z.object({
  appointmentId: z.string().uuid(),
  amountCents: z.number().int().positive(),
  method: z.enum(["efectivo", "tarjeta", "transferencia", "mercado_pago", "otro"]),
  emitInvoice: z.boolean().default(true),
  fiscalDocType: z.string().optional(),
  notes: z.string().max(500).optional(),
  idempotencyKey: z.string().uuid(),
});

export const chargeSchema = z.discriminatedUnion("currency", [
  baseChargeSchema.extend({ currency: z.literal("PEN"),
    fiscalDocType: z.enum(["boleta", "factura"]).optional() }),
  baseChargeSchema.extend({ currency: z.literal("ARS"),
    fiscalDocType: z.enum(["factura_b", "factura_a", "recibo"]).optional() }),
  baseChargeSchema.extend({ currency: z.literal("MXN"),
    fiscalDocType: z.enum(["cfdi", "ticket"]).optional() }),
  baseChargeSchema.extend({ currency: z.literal("USD"),
    fiscalDocType: z.enum(["ticket", "factura"]).optional() }),
  baseChargeSchema.extend({ currency: z.literal("COP"),
    fiscalDocType: z.enum(["ticket"]).optional() }),
  baseChargeSchema.extend({ currency: z.literal("CLP"),
    fiscalDocType: z.enum(["boleta", "factura"]).optional() }),
]).refine((d) => !d.emitInvoice || !!d.fiscalDocType, {
  message: "fiscalDocType requerido cuando emitInvoice=true",
  path: ["fiscalDocType"],
});

export type ChargeFormValues = z.infer<typeof chargeSchema>;
```

Submit handler invokes `useChargeMutation`. On success:
- Toast success via `sonner` "Cobro {currency} {amount} registrado · {doc_type} emitida" + Link `Ver comprobante` opens fiscal_doc_url new tab
- Invalidate `['agenda', 'grid', ...]` + `['agenda', 'appointment', appointmentId]`
- Slot border-status updates 🟡 → 🟢 via re-render
- Form resets + collapses

On error (per `useChargeMutation` handler):
- HTTP 409 → `<Alert>` conflict + auto-invalidate + auto-collapse
- HTTP 5xx payment fail → `<Alert variant="destructive">` "No pudimos procesar el cobro." + botón `Reintentar` (re-submits with SAME idempotencyKey — backend dedups)
- HTTP 200 payment OK + fiscal emit fail → `<Alert variant="warning">` "Cobro registrado, comprobante pendiente — reintentar emisión" + botón `Reintentar emisión` (calls `useFiscalEmitMutation` standalone)

### 6.8 AgendaPresetFilters (chips)

5 chips single-select. Click toggles URL param `?preset_filter=<value>`. State persistence via URL only (no localStorage). Hover/active/focus per mockup `preset-filters.html`.

ARIA: `<button role="switch" aria-checked={isActive}>` per chip.

### 6.9 CrearCitaButton

Desktop: `<DropdownMenu>` with 3 opciones → opens `<Dialog>` containing `CrearCitaForm` variant per opción.
Mobile: FAB `fixed bottom-4 right-4` + DropdownMenu UP direction.

`CrearCitaForm` 3 variants:
- `walk_in` → form `<PatientNewDataDTO>` fields
- `telefono` → idem
- `desde_paciente_existente` → `<PatientAutocomplete>` (Combobox + debounced `/api/v1/crm/patients?q=` PHI-masked)

### 6.10 React Query keys + mutations

```ts
// keys schema
export const agendaKeys = {
  all: ["agenda"] as const,
  grid: (tenantId, clinicId, view, date, presetFilter) =>
    ["agenda", "grid", { tenantId, clinicId, view, date, presetFilter }] as const,
  aggregates: (tenantId, clinicId, month) =>
    ["agenda", "aggregates", { tenantId, clinicId, month }] as const,
  appointment: (tenantId, clinicId, appointmentId) =>
    ["agenda", "appointment", { tenantId, clinicId, appointmentId }] as const,
};

export const crmKeys = {
  patients: (tenantId, clinicId, q) =>
    ["crm", "patients", { tenantId, clinicId, q }] as const,
};
```

Mutations invalidations:

| Mutation | Invalidates |
|---|---|
| `useChargeMutation` | `agendaKeys.grid(...)` + `agendaKeys.appointment(...)` |
| `useFiscalEmitMutation` | `agendaKeys.appointment(...)` |
| `useCreateAppointmentMutation` | `agendaKeys.grid(...)` + `agendaKeys.aggregates(...)` |
| `useUpdateAppointmentStatusMutation` | grid + appointment |
| `useSendNotificationMutation` | appointment (history list) |

Polling: `refetchInterval: 30_000` on `useAgendaGrid` only. Detail fetch is on-demand (drawer open).

### 6.11 Realtime — polling + stale detection (SC-6)

Polling 30s on grid. If detail open + grid refetch detects `appointment_id` updated_at remoto > local → set `useDrawerStore.staleDetected = true` → AppointmentDrawer renders `<Banner variant="warning">` "Este turno fue actualizado por otro usuario. ¿Recargar datos?" + botón triggers `queryClient.invalidateQueries(agendaKeys.appointment(...))`.

### 6.12 react-window virtualization (SC-9)

Used only in `DayCalendar` with `> 50 slots`. Render via `FixedSizeList` (~80px row height), overscan=2. WeekCalendar grid 7×13 (91 cells max) → no virtualization needed. MonthCalendar consumes `/aggregates` (no bulk slots, no virtualization).

### 6.13 Mobile responsive (SC-1 responsive + SC-9 mobile)

Breakpoints per Tailwind config:
- `<md` (<768px): vista Día only + `<MobileBottomSheet>` 95vh + chip carousel `<ScrollArea orientation="horizontal">` + FAB

- `md..lg` (768-1024px): Día + Semana views (Mes disabled tooltip) + Drawer side="right" 380px fixed
- `lg..xl` (1024-1440px): All views + Drawer resizable 440-640px
- `xl+` (>1440px): same + Drawer default 480px

### 6.14 useTenantLocale + formatTenantMoney

`vitalia/frontend/src/lib/tenant-locale.ts` (EXTEND or NEW if absent):

```ts
export function useTenantLocale(): { currency: string; timezone: string; locale: string } {
  const { tenant } = useTenantStore();
  return { currency: tenant.currency, timezone: tenant.timezone, locale: tenant.locale };
}

export function formatTenantMoney(
  amountCents: number,
  currency: string | null,
  locale: string | null,
): string {
  const safeCurrency = currency ?? "USD";
  const safeLocale = locale ?? "es-PE";
  const amount = amountCents / 100;
  return new Intl.NumberFormat(safeLocale, {
    style: "currency",
    currency: safeCurrency,
  }).format(amount);
}
```

Currency per-transaction override: `CobrarSaldoSubform` reads `appointment.currency_override` if set → preseed `<Select currency>` to override + show both as options (`tenant.currency` default + override). Backend stores both `currency` (effective at charge time) explicit in `appointment_payments`.

---

## § 7 — Repository Interfaces + Application Services

### 7.1 Repositories (BE)

`vitalia/backend/src/modules/vitalia/scheduling/infrastructure/repositories/`

```python
# agenda_grid_repository.py
from abc import abstractmethod
from datetime import datetime
from uuid import UUID

from src.modules.vitalia._shared.repositories.phi_repository import PhiRepositoryBase
from src.modules.vitalia.scheduling.domain.agenda_slot import AgendaSlot


class AgendaGridRepository(PhiRepositoryBase):
    """Repo for agenda grid queries — dual filter mandatory."""

    @abstractmethod
    async def get_by_id(
        self, entity_id: UUID, *, tenant_id: UUID, clinic_id: UUID,
    ) -> AgendaSlot | None: ...

    @abstractmethod
    async def list_by_filter(
        self, *, tenant_id: UUID, clinic_id: UUID, **filters,
    ) -> list[AgendaSlot]: ...

    @abstractmethod
    async def list_grid(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        date_from: datetime,
        date_to: datetime,
        preset_filter: str | None = None,
    ) -> list[AgendaSlot]: ...
```

Implementation `agenda_grid_repository_impl.py` uses SQLA 2.0:

```python
from sqlalchemy import select
from sqlalchemy.orm import aliased

# JOIN engine appointments ⨝ brand map ⨝ payments (LEFT) to compute balance + status
async def list_grid(self, *, tenant_id, clinic_id, date_from, date_to, preset_filter=None):
    self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)
    stmt = (
        select(
            AppointmentModel,                               # engine
            VitaliaAppointmentClinicMapModel,               # brand map
            VitaliaAppointmentPaymentModel,                 # payments (LEFT JOIN)
        )
        .join(
            VitaliaAppointmentClinicMapModel,
            VitaliaAppointmentClinicMapModel.appointment_id == AppointmentModel.id,
        )
        .outerjoin(
            VitaliaAppointmentPaymentModel,
            (VitaliaAppointmentPaymentModel.appointment_id == AppointmentModel.id) &
            (VitaliaAppointmentPaymentModel.deleted_at.is_(None)),
        )
        .where(
            VitaliaAppointmentClinicMapModel.tenant_id == tenant_id,
            VitaliaAppointmentClinicMapModel.clinic_id == clinic_id,
            VitaliaAppointmentClinicMapModel.deleted_at.is_(None),
            AppointmentModel.start_time >= date_from,
            AppointmentModel.start_time < date_to,
        )
        .order_by(AppointmentModel.start_time)
    )
    # preset_filter applies additional WHERE clauses per AgendaPresetFilter enum
    if preset_filter == "saldos_pendientes":
        stmt = stmt.where(VitaliaAppointmentPaymentModel.id.is_(None))  # no payment row
    # ... other presets
    result = await self.session.execute(stmt)
    rows = result.all()
    return [self._project_slot(r) for r in rows]
```

`appointment_detail_repository.py` — `get_by_id` retrieves single appointment + map + payments via similar JOIN with `with_for_update()` only for `charge_orchestrator.lock_for_charge(...)` not for read.

`appointment_payment_repository.py` — insert + update (balance_version increment via optimistic lock) + read by `external_payment_id` (idempotency).

`appointment_aggregates_repository.py` — pure SQL aggregate (`GROUP BY date(start_time), payment_status`) for MonthCalendar.

`fiscal_document_repository.py` — `vitalia/backend/src/modules/vitalia/fiscal/infrastructure/repositories/`. Heredada `PhiRepositoryBase` aunque fiscal_document NO contiene PHI clínica (sólo monto+doc type) — dual filter es defense-in-depth + uniformidad.

### 7.2 Application services

`vitalia/backend/src/modules/vitalia/scheduling/application/`

#### `agenda_grid_service.py`

```python
class AgendaGridService:
    def __init__(self, repo: AgendaGridRepository, audit: AsyncAuditWriter): ...

    async def list_grid(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        view: AgendaView,
        date: date,
        preset_filter: AgendaPresetFilter | None,
        suspicious_params: list[str] | None = None,
    ) -> AgendaGridResponseDTO:
        # date_from/date_to from view+date (UTC math with tenant timezone via TenantLocale)
        # repo.list_grid()
        # If suspicious_params present → emit audit_log row action='suspicious_request' (NO PHI content)
        # If preset_filter applied → emit audit_log row action='read_agenda' with redacted preset value
        # Return DTO
```

#### `appointment_detail_service.py`

```python
class AppointmentDetailService:
    async def get_detail(
        self, *, tenant_id, clinic_id, user_id, appointment_id,
    ) -> AppointmentDetailDTO:
        # Repo dual filter
        # Audit log row action='read_appointment_detail' sync BEFORE response
        # If cross-clinic (record found in another clinic_id) → return 404, audit_log action='cross_clinic_attempt' (without leak existence)
        # Project PHI-masked DTO (apply mask via PHIMasker shared util)
```

#### `appointment_status_service.py`

```python
class AppointmentStatusService:
    async def patch_status(
        self, *, tenant_id, clinic_id, user_id, appointment_id, new_status, reason,
    ) -> AppointmentDetailDTO:
        # Validate state machine (CANCELLED/COMPLETED/NO_SHOW only)
        # Optimistic lock + UPDATE
        # Audit log action='status_change' with from_status, to_status, reason (sanitized)
        # Return updated detail
```

#### `charge_orchestrator.py` (★ saga payment + fiscal + audit)

```python
class ChargeOrchestrator:
    """Saga: charge → audit log → fiscal emit (optional) → audit log → response.

    Compensation:
      - Charge OK + fiscal emit FAIL → DO NOT rollback charge (paying twice = bad). Return
        fiscal_emission_status='failed' + audit_log action='fiscal_emit_failed_post_charge'.
        FE shows warning + offers retry-emit standalone.
      - Charge FAIL → no fiscal emit (transaction aborts). Audit log action='charge_failed'.

    Optimistic lock pattern (SC-5):
      - Repo `appointment_payment_repo.lock_for_charge(appointment_id, expected_version)`
        returns balance + version. UPDATE WHERE balance_version=expected_version.
      - On 0 rows updated → raise BalanceAlreadyChargedError → 409 to FE.

    Idempotency:
      - Lookup existing payment by (tenant_id, clinic_id, idempotency_key) → if found,
        return previous response (no double charge).
    """

    def __init__(
        self,
        payment_port: PaymentChargePort,            # implemented by payments module → wraps Stripe/MP scaffold
        fiscal_port: FiscalEmitPort,                # implemented by fiscal module → stub or real
        payment_repo: AppointmentPaymentRepository,
        audit: AsyncAuditWriter,
        compliance: ComplianceService,
    ): ...

    async def execute(
        self, *, tenant_id, clinic_id, user_id, request: ChargeRequestDTO,
    ) -> ChargeResponseDTO:
        # 1. Idempotency check
        existing = await self.payment_repo.find_by_idempotency_key(
            tenant_id=tenant_id, clinic_id=clinic_id, key=request.idempotency_key,
        )
        if existing:
            return self._project_response(existing, ...)

        # 2. Optimistic lock + balance check
        try:
            await self.payment_repo.lock_for_charge(
                appointment_id=request.appointment_id, tenant_id=tenant_id, clinic_id=clinic_id,
            )
        except BalanceAlreadyChargedError:
            raise HTTPException(409, detail={"error_code": "BALANCE_ALREADY_CHARGED", ...})

        # 3. Call payment port (wraps Stripe/MP adapter)
        try:
            external = await self.payment_port.charge(...)
        except PaymentAdapterUnavailableError:
            await self.audit.write(action="charge_failed", ...)
            raise HTTPException(503, detail={"error_code": "PAYMENT_ADAPTER_503", ...})

        # 4. Persist payment row
        payment = await self.payment_repo.create(...)
        await self.audit.write(action="charge", payload={"amount": request.amount_cents, ...})

        # 5. Optional fiscal emit
        fiscal_status = "skipped"
        fiscal_doc_url = None
        fiscal_error = None
        if request.emit_invoice:
            try:
                fiscal = await self.fiscal_port.emit(
                    payment_id=payment.id, doc_type=request.fiscal_doc_type,
                    idempotency_key=f"fiscal-{request.idempotency_key}",
                )
                fiscal_status = "emitted"
                fiscal_doc_url = fiscal.doc_url
                await self.audit.write(action="invoice_emitted", ...)
            except FiscalEmitError as e:
                fiscal_status = "failed"
                fiscal_error = str(e)
                await self.audit.write(action="fiscal_emit_failed_post_charge", ...)

        return self._project_response(payment, fiscal_status, fiscal_doc_url, fiscal_error)
```

#### `notify_service.py`

```python
class NotifyService:
    async def send_notification(
        self, *, tenant_id, clinic_id, user_id, appointment_id, template_id, channel,
    ) -> dict:
        # 1. Load template_id → resolve template_content from seed catalog
        # 2. ComplianceService.validate_outbound_message(template_content, channel) — raises BlockedChannelError if PHI
        # 3. Dispatch to channel adapter (WhatsApp template-only via core/luana-core-channels)
        # 4. Audit log action='send_notification' with template_id, channel (no body)
```

#### Port interfaces (service-blocker decoupling)

`vitalia/backend/src/modules/vitalia/scheduling/application/ports/payment_charge_port.py`

```python
from abc import ABC, abstractmethod

class PaymentChargePort(ABC):
    @abstractmethod
    async def charge(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        appointment_id: UUID,
        amount_cents: int,
        currency: str,
        method: str,
        idempotency_key: str,
    ) -> "ExternalPaymentResult": ...


class PaymentAdapterUnavailableError(Exception): ...
```

Implementation `vitalia/backend/src/modules/vitalia/payments/application/payment_charge_port_impl.py` selects adapter from `tenant.config.payment_gateway` ∈ {stripe, mercadopago, efectivo_manual} → wraps existing `stripe_connect_adapter.py` / `mercadopago_adapter.py` (scaffold). Si scaffold methods missing → raise `PaymentAdapterUnavailableError` → 503.

`vitalia/backend/src/modules/vitalia/fiscal/application/ports/fiscal_emit_port.py` — similar pattern.

### 7.3 Transaction boundaries

- `charge_orchestrator.execute` runs inside a single AsyncSession transaction. `audit_log` row uses **same session** (per `AsyncAuditWriter`) — atomic commit.
- Payment + fiscal emit are **NOT same-DB-transaction** (fiscal is external API call). Saga compensation: charge persisted before fiscal emit attempted. If fiscal fails → charge stays, audit logs failure, FE shows retry.
- All DB writes use `async with session.begin():` block pattern.

### 7.4 Idempotency tables

No new dedup tables. Use `vitalia_appointment_payments.external_payment_id` (indexed) as natural idempotency key (`idempotency_key` field stored verbatim there). FK + UNIQUE index `(tenant_id, clinic_id, external_payment_id) WHERE external_payment_id IS NOT NULL`.

---

## § 8 — Cross-cutting Concerns (HIPAA-lite mandatory)

### 8.1 Tenant + clinic isolation (dual filter HIPAA)

- **Every query** filters `tenant_id AND clinic_id`. `AgendaGridRepository`, `AppointmentDetailRepository`, `AppointmentPaymentRepository`, `FiscalDocumentRepository` heredan `PhiRepositoryBase` + invoke `validate_dual_filter(...)` at top of every method.
- Cross-clinic query returns **404** (no 403 — evita leak existencia). Audit log row `action="cross_clinic_attempt"`.
- Arch test `test_phi_dual_filter.py` extended con nuevos repos brand.

### 8.2 PHI sanitization (server-side traces + logs + telemetry)

- All audit_log payloads → `sanitize_payload(payload, compliance_level="hipaa_lite")` (already enforced in `AsyncAuditWriter`).
- Sentry capture → wrap `before_send` hook to sanitize. Telemetry events idem.
- structlog WARN events: NO interpolate `patient.name` / `dni` / `email` / clinical fields. Use `patient_id` UUID hash only.
- `console.log` dev mode prohibido para PHI (FE lint rule via `no-console` + arch test grep).

### 8.3 PHI masking visual (FE projection)

- `<PHIMaskedText>` shared component (`vitalia/frontend/src/components/shared/phi/PHIMaskedText.tsx` — already shipped).
- Backend projects DTOs already masked:
  - Name: `"P. Hernández"` (first-initial + last word). Function `mask_name(full_name) -> str` lives in `vitalia/backend/src/modules/vitalia/_shared/phi_masking.py` (NEW shared util — extract from existing patterns).
  - DNI: `"12.***.***"`.
  - Phone: `"+51 9** *** 423"`.
  - Email: `"p***@gmail.com"`.

### 8.4 Audit log (sync write antes response)

Every PHI-adjacent action persists row antes de return:

| Endpoint | action value |
|---|---|
| GET `/agenda/grid` (with preset_filter or suspicious_params) | `"read_agenda"` / `"suspicious_request"` |
| GET `/appointments/{id}` | `"read_appointment_detail"` |
| POST `/appointments` | `"create_appointment"` |
| PATCH `/appointments/{id}/status` (CANCELLED/COMPLETED/NO_SHOW) | `"status_change"` |
| POST `/appointments/{id}/notify` | `"send_notification"` |
| POST `/payments/charge` (success) | `"charge"` |
| POST `/payments/charge` (fail) | `"charge_failed"` |
| POST `/fiscal/emit` (success) | `"invoice_emitted"` |
| POST `/fiscal/emit` (fail) | `"fiscal_emit_failed"` |
| Cross-clinic 404 detected | `"cross_clinic_attempt"` |

Arch test `test_audit_log_sync_write.py` extended con grep verificación per nuevo endpoint.

### 8.5 Currency per-transaction override (Q14 cement)

- Backend `vitalia_appointment_clinic_map.currency_override: str | None` columna persiste override desde turista (USD en clínica AR, etc.)
- DTOs `ChargeRequestDTO.currency` requerido explícito — no infiere de tenant. Repo persiste verbatim en `vitalia_appointment_payments.currency`.
- FE: `formatTenantMoney(amount, currency, locale)` consume currency del DTO (NO `useTenantLocale().currency` fallback hardcoded).
- Fiscal emit aplica tax rules per currency country via `fiscal_port.emit(...)` — implementación lives en fiscal module.

### 8.6 Service-blocker pattern (★ payment-adapter-mvp + fiscal-emission-pe NOT developed)

`vitalia-payment-adapter-mvp` state=`refined`, `vitalia-fiscal-emission-pe` state=`refining`. /dev-team REFUSE pickup hasta ambas en `developed`. Si Chris ratifica arranque early:

**Option A (recommended) — MSW mocks + interface stubs:**
- Backend: `PaymentChargePort` interface ya definida. Stub impl en `payments/application/stubs/stub_payment_charge_port.py` retorna `ExternalPaymentResult(external_payment_id=f"stub-{uuid4()}", succeeded=True)` para tests + dev local.
- Backend: `FiscalEmitPort` interface ya definida. Stub impl retorna `FiscalDocument(doc_number=f"STUB-{seq}", doc_url=None, status="emitted")`.
- Frontend: MSW handlers en `vitalia/frontend/src/test-utils/msw/handlers/agenda-handlers.ts` mock `POST /api/v1/payments/charge` + `POST /api/v1/fiscal/emit` con success/503/conflict variants.
- Real adapter wiring lifted cuando service-blockers `developed` (no rework FE).

**Option B (escalate) — BLOCKED until both `developed`:**
- /dev-team emite `state: blocked`, escalates `/pm-vitalia` para sequence service-blockers first.

**Default decision en `06-tickets.yaml`:** Option A (stub + MSW), unblocking F2-S1 BE+FE work parallel. Service blockers can land late without breaking F2-S1 contract. Auditor verifies stub paths are `/* deprecated post-merge */` commented + tracked.

### 8.7 Spanish neutro LatAm

All UI strings + microcopy validated via `.claude/rules/spanish-text.md` glosario. Pre-commit hook verifies (existing). Excepción sales_agent voice no aplica (story es UI chrome puro).

### 8.8 Native-first dev gates

- BE: `cd vitalia/backend && ${WS}/.venv/bin/{ruff,pytest,mypy}` (root venv)
- FE: `cd vitalia/frontend && npx {tsc,eslint,vitest,playwright}` (no docker exec)


---

## § 9 — Migration Notes (idempotent raw SQL)

`vitalia/backend/src/modules/vitalia/scheduling/persistence/migrations/`

Naming: `XXXX_agenda_drawer_phase2_<descriptor>.py` per Alembic per-brand convention. Reuse brand's Alembic config (single migrations folder per-brand under `vitalia/backend/alembic/versions/`).

### 9.1 Migration `XXXX_vitalia_agenda_phase2.py`

```python
"""F2-S1 Vitalia agenda: appointment_payments + fiscal_documents + clinic_map + growth_studio_event.

Idempotent — uses IF NOT EXISTS / IF EXISTS. Safe to re-run.

Revision ID: f2_s1_vitalia_agenda
Revises: <last vitalia revision>
Create Date: 2026-MM-DDT00:00:00.000000

downstream-regression-na: brand-local scheduling tables; no engine modify.
"""
from __future__ import annotations
from alembic import op

revision = "f2_s1_vitalia_agenda"
down_revision = "<previous>"

def upgrade() -> None:
    # vitalia_fiscal_documents
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_fiscal_documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            clinic_id UUID NOT NULL,
            appointment_payment_id UUID NOT NULL,
            doc_type VARCHAR(32) NOT NULL,
            doc_number VARCHAR(64),
            doc_url VARCHAR(512),
            provider VARCHAR(32) NOT NULL,
            status VARCHAR(16) NOT NULL DEFAULT 'pending',
            error_message VARCHAR(500),
            deleted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_vit_fiscal_tenant_clinic ON vitalia_fiscal_documents (tenant_id, clinic_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_vit_fiscal_payment ON vitalia_fiscal_documents (appointment_payment_id);")

    # vitalia_appointment_payments (with FK to fiscal_documents)
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_appointment_payments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            clinic_id UUID NOT NULL,
            appointment_id UUID NOT NULL,
            amount INTEGER NOT NULL,
            currency VARCHAR(3) NOT NULL,
            method VARCHAR(32) NOT NULL,
            external_payment_id VARCHAR(128),
            fiscal_doc_id UUID REFERENCES vitalia_fiscal_documents(id) ON DELETE SET NULL,
            notes VARCHAR(500),
            balance_version INTEGER NOT NULL DEFAULT 1,
            created_by_user_id UUID,
            deleted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ,
            CONSTRAINT fk_vit_payment_appointment FOREIGN KEY (appointment_id)
                REFERENCES appointments(id) ON DELETE RESTRICT
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_vit_payment_tenant_clinic_apt ON vitalia_appointment_payments (tenant_id, clinic_id, appointment_id);")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_vit_payment_external ON vitalia_appointment_payments (tenant_id, clinic_id, external_payment_id) WHERE external_payment_id IS NOT NULL;")

    # vitalia_appointment_clinic_map
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_appointment_clinic_map (
            appointment_id UUID PRIMARY KEY REFERENCES appointments(id) ON DELETE CASCADE,
            tenant_id UUID NOT NULL,
            clinic_id UUID NOT NULL,
            patient_id UUID NOT NULL,
            doctor_id UUID NOT NULL,
            service_label VARCHAR(128) NOT NULL,
            origin VARCHAR(32) NOT NULL,
            currency_override VARCHAR(3),
            deleted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_vit_apt_map_tenant_clinic ON vitalia_appointment_clinic_map (tenant_id, clinic_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_vit_apt_map_patient ON vitalia_appointment_clinic_map (patient_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_vit_apt_map_doctor ON vitalia_appointment_clinic_map (doctor_id);")

    # vitalia_growth_studio_event (telemetry, brand-local — separate from copilot_trace_event)
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_growth_studio_event (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            clinic_id UUID,
            user_id UUID,
            event_name VARCHAR(64) NOT NULL,
            props JSONB NOT NULL DEFAULT '{}'::jsonb,
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_vit_gse_tenant_clinic_event ON vitalia_growth_studio_event (tenant_id, clinic_id, event_name);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_vit_gse_occurred ON vitalia_growth_studio_event (occurred_at);")

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS vitalia_growth_studio_event;")
    op.execute("DROP TABLE IF EXISTS vitalia_appointment_clinic_map;")
    op.execute("DROP TABLE IF EXISTS vitalia_appointment_payments;")
    op.execute("DROP TABLE IF EXISTS vitalia_fiscal_documents;")
```

### 9.2 Prod-clone test command

```bash
# Verify migration idempotency against a clone of vitalia prod schema
WS=$(git rev-parse --show-toplevel)
docker exec luana-vitalia-postgres-dev psql -U postgres -d vitalia_migration_test -c "BEGIN;" \
  && docker exec luana-vitalia-backend-dev alembic upgrade head \
  && docker exec luana-vitalia-backend-dev alembic upgrade head    # second run = no-op (idempotency)
```

Pre-prod gate: run migration twice; second run MUST produce zero DDL changes.

---

## § 9.5 — Tests Audit (default flip — N/A for F2-S1)

| Field | Value |
|---|---|
| `[x] No aplica` | F2-S1 NO flippea defaults side-effect. No tocan `USE_OUTBOX_PATTERN_*` / `LITELLM_PROXY_ENABLED` / `USE_DEEPAGENTS_*` ni equivalente. |

(Reference: `.claude/rules/anti-default-flip-audit.md` — story arquitectura no modifica feature flag inventory.)

---

## § 10 — Telemetría arquitectura

### 10.1 Sink: NEW `vitalia_growth_studio_event` brand-local table

Justificación architect-ratified (per Open Question + best-practice consultada):
- `copilot_trace_event` (engine `core/luana-core-observability/`) registra LLM cost + turn envelopes + agentic spans — concerns ortogonal a UX funnel events.
- Mezclar → ruido en costo dashboards + retention policies confusas.
- Telemetry events son async fire-forget OK (distinto de audit_log mandatorio sync) → no impacta turn latency.

### 10.2 Endpoint emit + sanitize

```python
# vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py
async def emit_growth_event(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    clinic_id: UUID | None,
    user_id: UUID | None,
    event_name: str,
    props: dict,
) -> None:
    """Emit growth_studio event. Fire-forget OK (try/except + structlog warn)."""
    try:
        safe = sanitize_payload(props, compliance_level="hipaa_lite")
        await session.execute(
            text("""INSERT INTO vitalia_growth_studio_event ... """),
            {"tenant_id": tenant_id, ..., "props": json.dumps(safe), "occurred_at": utc_now()},
        )
    except Exception as e:
        logger.warning("growth_event_emit_failed", event=event_name, error=str(e))
```

POST `/api/v1/telemetry/events` thin endpoint para FE emit. Body `{event_name, props}`. Server reasserts `tenant_id` + `clinic_id` from JWT (NO trust FE-supplied IDs).

### 10.3 7 eventos críticos (HIPAA-lite payload constraints)

| Event | Trigger | Props sanitized |
|---|---|---|
| `agenda_viewed` | Page mount + grid load success | `{view, date, slot_count, preset_filter, has_filter}` |
| `slot_drawer_opened` | Click slot → drawer | `{appointment_id_hash, slot_status, origin}` |
| `charge_initiated` | Subform submit | `{payment_method, amount_bucket: "0-50"/"50-100"/"100-500"/"500+", currency, fiscal_doc_emit_intent}` |
| `charge_succeeded` | POST /charge 200 | `{payment_method, amount_bucket, currency, fiscal_doc_emitted, duration_ms}` |
| `charge_failed` | POST /charge !200 | `{error_code, retry_count, stage: "payment"|"fiscal"}` |
| `invoice_emitted` | POST /fiscal/emit 200 | `{doc_type, country}` (NO doc_url, NO amount exact) |
| `reminder_sent` | POST /notify 200 | `{template_id, channel}` |

NO en props: `patient_name`, `patient_dni`, `patient_phone`, `diagnosis`, `treatment`, `exact_amount`, `doctor_name`, `appointment_id` raw. `appointment_id_hash` is SHA256 truncated 16 chars.

### 10.4 amount_bucket function

```python
def bucket_amount(amount_cents: int) -> str:
    amount = amount_cents / 100
    if amount < 50: return "0-50"
    if amount < 100: return "50-100"
    if amount < 500: return "100-500"
    return "500+"
```

Frontend mirror in `vitalia/frontend/src/lib/telemetry.ts`.

---

## § 11 — Test Surfaces (TDD-mandatory + ★ v4.1 Test Construction Plan)

### 11.1 BE test layers (RED-first per layer)

| Layer | File | Coverage |
|---|---|---|
| Domain | `tests/modules/vitalia/scheduling/test_agenda_slot_domain.py` | AgendaSlot + AppointmentPayment + enums |
| Infra | `tests/modules/vitalia/scheduling/test_agenda_grid_repository.py` | Dual filter + JOINs + preset_filter |
| Infra | `tests/modules/vitalia/scheduling/test_appointment_payment_repository.py` | Optimistic lock + idempotency lookup |
| Application | `tests/modules/vitalia/scheduling/test_agenda_grid_service.py` | List grid + suspicious params logging |
| Application | `tests/modules/vitalia/scheduling/test_appointment_detail_service.py` | PHI masking + cross-clinic 404 + audit log |
| Application | `tests/modules/vitalia/scheduling/test_charge_orchestrator.py` | Saga happy + payment 503 + fiscal 503 + 409 + idempotency |
| Application | `tests/modules/vitalia/scheduling/test_notify_service.py` | ComplianceService guard + template-only |
| API | `tests/modules/vitalia/scheduling/test_drawer_charge_flow.py` | End-to-end charge happy + 503 + 409 (SC-1, SC-2, SC-5) |
| API | `tests/modules/vitalia/scheduling/test_phi_url_protection.py` | Whitelist params + suspicious request audit (SC-4) |
| API | `tests/modules/vitalia/scheduling/test_dual_filter_clinic_isolation.py` | Cross-clinic 404 (SC-4) |
| API | `tests/modules/vitalia/scheduling/test_audit_log_drawer.py` | Audit log row per action (AC-10) |
| API | `tests/modules/vitalia/scheduling/test_notify_compliance_guard.py` | Template-only + PHI block + audit (AC-30) |
| API | `tests/modules/vitalia/scheduling/test_create_appointment_router.py` | Create flow 3 origins |
| API | `tests/modules/vitalia/scheduling/test_patch_status_router.py` | Status transitions |
| Architecture | `tests/architecture/test_scheduling_module_ddd.py` (NEW) | DDD layers + extension SDK registration |
| Architecture | `tests/architecture/test_no_phi_in_url_params.py` (NEW) | Grep PHI fields in query param keys |
| Architecture | `tests/architecture/test_audit_log_row_per_phi_endpoint.py` (NEW) | Grep `audit.write(...)` invocation per PHI endpoint |

### 11.2 FE Vitest unit tests

| File | Coverage |
|---|---|
| `features/valeria/components/agenda/__tests__/ValeriaAgendaView.test.tsx` | Composition + initialData hydration + view toggle |
| `features/valeria/components/agenda/__tests__/AgendaCalendar.test.tsx` | 3 variants dispatch + virtualization gate |
| `features/valeria/components/agenda/__tests__/AgendaSlot.test.tsx` | Border-status + origin-badge + click + ARIA |
| `features/valeria/components/agenda/__tests__/AppointmentDrawer.test.tsx` | Sheet open/close + acordeones + resize + stale banner |
| `features/valeria/components/agenda/__tests__/CobrarSaldoSubform.test.tsx` | Form validate + multi-currency + 409 handling + retry button + fiscal warning |
| `features/valeria/components/agenda/__tests__/AgendaPresetFilters.test.tsx` | 5 chips single-select + URL param sync |
| `features/valeria/components/agenda/__tests__/CrearCitaButton.test.tsx` | Dropdown + 3 form variants |
| `features/valeria/api/__tests__/agenda.test.ts` | React Query hooks + invalidations |
| `features/valeria/hooks/__tests__/useAgendaFilters.test.ts` | URL param round-trip |
| `features/valeria/store/__tests__/drawer-store.test.ts` | Zustand state shape |

### 11.3 Playwright E2E specs (★ Test Construction Plan v4.1)

`base_path:` `vitalia/frontend/e2e/regression/vitalia-fase2-valeria-agenda/`

**creation_order (numerado steps con fixtures → POMs → spec.ts):**

| Step | File | Content | Depends_on |
|---|---|---|---|
| 1 | `fixtures/valeria-agenda.fixture.ts` | Clerk authedAsValeria + tenant PE setup + DB seed appointments(N=20, clinic_id) + MSW handlers payment/fiscal | [] |
| 2 | `fixtures/mock-payment-adapter.ts` | MSW handlers `POST /api/v1/payments/charge` variants: 200 / 503 / 409 + idempotency lookup | [1] |
| 3 | `fixtures/mock-fiscal-emission.ts` | MSW handlers `POST /api/v1/fiscal/emit` variants: 200 / 503 | [1] |
| 4 | `fixtures/network-failure.ts` | route.abort() helper for grid timeout (SC-7) | [1] |
| 5 | `poms/agenda-view-page.pom.ts` | AgendaViewPage POM: viewToggle, datePicker, chipPreset, createCitaButton, freshnessIndicator | [1] |
| 6 | `poms/appointment-drawer-page.pom.ts` | AppointmentDrawerPage POM: open(slotId), close, accordion(name), resize(px), staleBanner | [1] |
| 7 | `poms/cobrar-saldo-subform-page.pom.ts` | CobrarSaldoSubformPage POM: fields fill, currencySelect, submit, errorAlert, retryButton | [1] |
| 8 | `poms/crear-cita-button-page.pom.ts` | CrearCitaButtonPage POM: dropdownOpen, selectOption, patientAutocomplete | [1] |
| 9 | `valeria-agenda-cobro.spec.ts` | SC-1 happy + SC-2 negative (payment 503) | [5,6,7] |
| 10 | `valeria-agenda-tenant-switch.spec.ts` | SC-3 tenant switch invalidate + reset | [5,6] |
| 11 | `valeria-agenda-concurrent-users.spec.ts` | SC-6 2 contexts polling + stale banner | [5,6] |
| 12 | `valeria-agenda-network.spec.ts` | SC-7 timeout + retry empty state | [5] |
| 13 | `valeria-agenda-empty.spec.ts` | SC-8 empty day + CTA | [5,8] |
| 14 | `valeria-agenda-large-dataset.spec.ts` | SC-9 240 slots virtualization perf | [5] |
| 15 | `valeria-agenda-keyboard.spec.ts` | SC-10 keyboard nav + axe | [5,6,7] |
| 16 | `valeria-agenda-i18n.spec.ts` | SC-11 multi-currency override | [5,6,7] |
| 17 | `valeria-agenda-mobile.spec.ts` | <md responsive + bottom-sheet + FAB | [5,6,7] |
| 18 | `valeria-agenda-conflict-409.spec.ts` | SC-5 concurrent charge → 409 FE handling (mocked) | [5,6,7] |
| 19 | `../a11y/valeria-agenda-a11y.spec.ts` | axe wcag2aa calendar + drawer + subform | [9] |
| 20 | `../visual/valeria-agenda-visual.spec.ts` | Visual goldens: 3 views × 2 themes + drawer + subform states + mobile = ~14 snapshots | [9,10] |

**scenario_to_test mapping:**

| Gherkin SC | Spec file | test() function | Validator |
|---|---|---|---|
| SC-1 happy cobro | `valeria-agenda-cobro.spec.ts` | `test("happy path PEN boleta emit end-to-end", ...)` | scenario_happy_path |
| SC-2 negative 503 | `valeria-agenda-cobro.spec.ts` | `test("payment adapter 503 shows retry", ...)` | scenario_negative |
| SC-3 edge tenant switch | `valeria-agenda-tenant-switch.spec.ts` | `test("tenant switch invalidates drawer + cache", ...)` | scenario_edge |
| SC-4 adversarial PHI URL | n/a (BE only) — `test_phi_url_protection.py` | n/a | scenario_adversarial |
| SC-5 race 409 | `valeria-agenda-conflict-409.spec.ts` + BE `test_charge_orchestrator.py::test_concurrent_charge_optimistic_lock` | `test("409 conflict shows graceful banner + auto-collapse", ...)` | scenario_race_condition |
| SC-6 concurrent_users | `valeria-agenda-concurrent-users.spec.ts` | `test("staff B cancel reflects in staff A polling 30s", ...)` | scenario_concurrent_users |
| SC-7 network_failure | `valeria-agenda-network.spec.ts` | `test("3 retries then EmptyState error + manual retry", ...)` | scenario_network_failure |
| SC-8 empty_state | `valeria-agenda-empty.spec.ts` | `test("empty day renders empty state with CTA", ...)` | scenario_empty_state |
| SC-9 large_dataset | `valeria-agenda-large-dataset.spec.ts` | `test("day with 240 slots virtualizes under 100ms", ...)` | scenario_large_dataset |
| SC-10 accessibility | `valeria-agenda-keyboard.spec.ts` + `valeria-agenda-a11y.spec.ts` | `test("keyboard nav slot→drawer→Esc", ...)` + axe | scenario_accessibility |
| SC-11 i18n | `valeria-agenda-i18n.spec.ts` | `test("currency override USD on AR tenant", ...)` | scenario_i18n |

### 11.4 POMs spec

- `AgendaViewPage`: getViewToggle(), clickView(name), getDatePicker(), getChipPreset(filter), getSlot(by), waitForLoaded()
- `AppointmentDrawerPage`: open(appointmentId), close(), getAccordion(name), getCobrarSaldoButton(), resize(width), getStaleBanner()
- `CobrarSaldoSubformPage`: fillAmount(cents), selectMethod(m), selectFiscalDocType(t), selectCurrency(c), submit(), getErrorAlert(), getRetryButton(), getSuccessToast()
- `CrearCitaButtonPage`: openDropdown(), selectOption(o), fillPatientNewData(d), searchPatient(q), submit()

### 11.5 Fixtures spec

- `authedAsValeria`: returns `BrowserContext` with Clerk storage state injected for `valeria_assistant` role
- `dbSeedAppointments(n, clinic_id)`: REST seed via test-utility endpoint or direct DB write fixture
- `mockPaymentAdapter503()`: MSW handler returning 503
- `mockFiscalEmission503()`: MSW handler returning 503
- `networkFailure(endpoint)`: Playwright `page.route(endpoint, route => route.abort('timedout'))`
- `tenantBSwitcher`: helper to invoke TenantSwitcher and assert hard redirect


---

## § 12 — Architecture Decisions (ratified spec + arch additions)

Source decisions (cementadas en `01-spec.md` checkpoint `cemented_decisions_iter_1` batches 1-4 + new architect decisions below). Builders MUST honor each in commits via `## Decisions honored` block.

### From spec (D-decisions cemented 2026-05-26)

| ID | Decision | Spec anchor |
|---|---|---|
| D1 | 1 grid TOC + 8 standalone mockups (parity F1-S10) | Q1 batch_1 |
| D2 | Cobrar saldo full inline (end-to-end payment + fiscal) | Q2 batch_1 |
| D3 | Calendar default Semana + URL params persist + `lastView` localStorage | Q3 batch_1 |
| D4 | Slot matrix 4×3 + 4 estados interactivos = 16 cells total | Q4 batch_1 |
| D5 | Drawer width resizable 440-640px + localStorage persist | Q5 batch_2 |
| D6 | Drawer sections acordeones colapsables (Turno+Pago expanded default) | Q6 batch_2 |
| D7 | "Ver ficha completa" botón disabled + Tooltip "Próximamente" | Q7 batch_2 |
| D8 | Action gates Cancelar + No-show → Dialog Shadcn confirm | Q8 batch_2 |
| D9 | 5 chips preset filters single-select (Hoy/Por confirmar/Re-agendar/No-shows/Saldos pendientes) | Q9 batch_3 |
| D10 | Crear cita DropdownMenu 3 opciones (walk-in/teléfono/desde-existente) | Q10 batch_3 |
| D11 | Mobile vista Día only + bottom-sheet 95vh + chip carousel + FAB Crear cita | Q11 batch_3 |
| D12 | Realtime polling 30s + manual refresh + FreshnessIndicator "Actualizado hace Xs" | Q12 batch_3 |
| D13 | Large dataset virtualización react-window (Day only) + aggregates endpoint mes | Q13 batch_4 |
| D14 | i18n per-transaction currency_override (multi-currency clinic AR turistas) | Q14 batch_4 |
| D15 | WhatsApp notify template-only + ComplianceService.validate_outbound_message + audit log | Q15 batch_4 |
| D16 | 7 telemetry events críticos (agenda_viewed/slot_drawer_opened/charge_*/invoice_emitted/reminder_sent) | Q16 batch_4 |

### Architect decisions NEW

| ID | Decision | Rationale |
|---|---|---|
| A1 | NEW módulo `vitalia/backend/src/modules/vitalia/scheduling/` (brand-extension, NO mirror) | Engine `core/luana-core-scheduling/Appointment` consumido READ-ONLY; clinic_id refuerzo brand-local via `vitalia_appointment_clinic_map` lightweight join (NO engine schema modify) — § 1.4 |
| A2 | NEW módulos `vitalia/backend/src/modules/vitalia/{payments,fiscal}/` separados (NO mezclar) | Payment scaffold ya vive en `payment/` (singular); NEW `payments/` (plural) es API thin + orchestrator que wraps scaffold. Fiscal greenfield — interface stub pending service-blocker `developed` |
| A3 | `PaymentChargePort` + `FiscalEmitPort` ABCs en `application/ports/` (Dependency Inversion) | Permite stub implementation cuando service-blockers NOT developed (Option A MSW + stub) sin rework FE/BE consumers — § 8.6 |
| A4 | Sink telemetry NEW `vitalia_growth_studio_event` table (separado de `copilot_trace_event`) | UX/funnel events orthogonal a LLM cost; mezclar ensucia retention + dashboards | § 10.1 |
| A5 | Slot DTO PHI-masked **server-side** projection (no FE masking trust) | Defense-in-depth: backend nunca emite PHI raw; FE no riesgo mask bypass (DevTools network inspect) | § 8.3 |
| A6 | Charge saga **NOT same-DB-transaction with fiscal emit** (compensation pattern) | Fiscal emit es external API call (Nubefact/AFIP/SAT); rollback charge si fiscal fail = paying twice = MAL. Charge persisted + audit log + retry-emit standalone si fiscal fail | § 7.2 ChargeOrchestrator |
| A7 | Optimistic lock via `balance_version` column (NO SELECT FOR UPDATE) | `with_for_update()` row-level lock bloquea reads paralelos (Staff A leyendo grid mientras Staff B cobra). Optimistic con version check = 409 graceful | § 7 SC-5 |
| A8 | Idempotency key client-generated UUID en POST `/charge` + POST `/fiscal/emit` | Permite retry sin doubt-charge (FE retry button reusa key) | § 5.4 |
| A9 | Audit log via `AsyncAuditWriter` mismo AsyncSession que business operation (transactional atomicity) | Existing pattern shipped; nuevo charge orchestrator reusa | § 7.3 |
| A10 | NEW arch test `test_no_phi_in_url_params.py` enforces whitelist + grep `patient_dni/patient_name/diagnosis` keys | Adversarial SC-4 defense — ratchet shrink-only | § 5.2 |
| A11 | NEW arch test `test_audit_log_row_per_phi_endpoint.py` enforces audit.write invocation grep per PHI route | Defense-in-depth complementario al `test_audit_log_sync_write.py` shipped | § 8.4 |
| A12 | `vitalia_appointment_clinic_map` brand-local FK to engine `appointments.id` (NO engine modify) | Engine `Appointment` shipped sin `clinic_id` (single-tenant assumption); brand-local extension carries clinic_id + tenant_id + patient_id + doctor_id + service_label + origin + currency_override sin tocar engine | § 3.4 |
| A13 | Service-blocker pattern Option A (stub + MSW) por default | Unblocks F2-S1 BE+FE work parallel; auditor verifies stub `/* deprecated post-merge */` comment + tracked replace cuando service-blockers developed | § 8.6 |
| A14 | Module scheduling registers via Extension SDK in `vitalia/backend/src/modules/vitalia/extensions.py::register_all` cuando aplicable (opt-in EPs) | Vitalia brand mounting pattern shipped (Story 11 cement); F2-S1 NO bootstrap new EP — solo registra rutas vía FastAPI router include | § 0.1 |

---

## § 13 — capability YAML + modules/scheduling.md Updates

### 13.1 NEW capability file (post-merge)

`vitalia/docs/product/capabilities/scheduling/valeria-agenda.yaml`

```yaml
capability_id: scheduling/valeria-agenda
title: "Agenda operativa Valeria con cobro inline + comprobante fiscal"
agent_owner: valeria
module: scheduling
status: shipped
shipped_at: 2026-MM-DD                    # post-merge
story: vitalia-fase2-valeria-agenda
deliverable_paths:
  backend:
    - vitalia/backend/src/modules/vitalia/scheduling/
    - vitalia/backend/src/modules/vitalia/payments/
    - vitalia/backend/src/modules/vitalia/fiscal/
  frontend:
    - vitalia/frontend/src/features/valeria/components/agenda/
    - vitalia/frontend/src/app/[tenantId]/(shell-organism)/valeria/agenda/page.tsx
gherkin_scenarios: [SC-1, SC-2, SC-3, SC-4, SC-5, SC-6, SC-7, SC-8, SC-9, SC-10, SC-11]
hipaa_lite: true
api_endpoints:
  - GET /api/v1/scheduling/agenda/grid
  - GET /api/v1/scheduling/agenda/aggregates
  - GET /api/v1/scheduling/appointments/{id}
  - POST /api/v1/scheduling/appointments
  - PATCH /api/v1/scheduling/appointments/{id}/status
  - POST /api/v1/scheduling/appointments/{id}/notify
  - POST /api/v1/payments/charge
  - POST /api/v1/fiscal/emit
service_dependencies:
  - vitalia-payment-adapter-mvp
  - vitalia-fiscal-emission-pe
```

### 13.2 MODIFY `vitalia/docs/product/modules/scheduling.md`

Append/modify section "Capabilities operativas" + auto-list regen:
```bash
WS=$(git rev-parse --show-toplevel)
${WS}/.venv/bin/python ${WS}/scripts/reconcile_capabilities.py --brand vitalia
```

(R3 rule: auto-list block dentro de modules MD es tracked-with-hybrid intro; manually-written intro + auto-block.)

---

## § 14 — Research Notes (DATE-AWARE — accessed 2026-05-27)

| Topic | Source | accessed | Key takeaway |
|---|---|---|---|
| React Server Components Server-First Next.js 16 App Router | https://nextjs.org/docs (canonical) | 2026-05-27 | Page server component + delegate to client root with `'use client'`. `getInitialAgendaState` SSR populates React Query `initialData` for instant load with refetchInterval polling. Opus 4.7 cutoff Jan 2026; researched via live canonical docs URL. |
| React Query v5 SSR + initialData hydration | https://tanstack.com/query/latest/docs/framework/react/guides/ssr (canonical) | 2026-05-27 | `placeholderData` vs `initialData`: initialData treats as fresh up to staleTime. F2-S1 uses initialData + staleTime=30s matching refetchInterval. |
| Shadcn `Sheet` + `Accordion` + drag-resize pattern | https://ui.shadcn.com/docs/components/sheet | 2026-05-27 | Shadcn Sheet supports side="right"|"bottom" with custom width. Drag-resize NOT native — custom Pointer-events implementation + debounced localStorage persist (440-640px). |
| Pydantic v2 `Annotated` Literal + ConfigDict(extra="forbid") | https://docs.pydantic.dev/latest/concepts/fields/ | 2026-05-27 | `Literal["...", "..."]` enforces enum-like at API edge; `extra="forbid"` rejects unknown fields (SC-4 PHI URL params protection complement). |
| SQLAlchemy 2.0 optimistic concurrency control (balance_version) | https://docs.sqlalchemy.org/en/20/orm/versioning.html | 2026-05-27 | `version_id_col` + `version_id_generator` patterns. F2-S1 manual approach: UPDATE `WHERE balance_version=:expected` + rowcount=0 → raise `BalanceAlreadyChargedError` → 409. |
| LangGraph multi-agent patterns (state-of-the-art) | https://docs.langchain.com/oss/python/langgraph/workflows-agents | 2026-05-27 | N/A — F2-S1 NO agentic surface. Cited for completeness; revisit when Valeria conversational surface arrives. |
| Anthropic prompt caching strategy | https://platform.claude.com/docs/en/build-with-claude/prompt-caching | 2026-05-27 | N/A para F2-S1 (no LLM call runtime). Mantener cita disponible para futuras stories agentic. |
| MSW v2 Playwright integration | https://mswjs.io/docs/integrations/browser (canonical) | 2026-05-27 | `setupWorker` + `start({onUnhandledRequest: 'warn'})` in test fixture. Network interception layer mocks payment + fiscal endpoints without rewriting FE consumers. |
| react-window FixedSizeList performance ~60fps | https://github.com/bvaughn/react-window (canonical) | 2026-05-27 | overscan=2-5 + itemSize fixed → DOM nodes ~viewport-bound, 60fps Lighthouse perf. Day with 240 slots → ~15 visible slots rendered (vs 240 raw). |
| HIPAA-lite dual filter pattern (PhiRepositoryBase) | Internal SSoT `vitalia/backend/src/modules/vitalia/_shared/repositories/phi_repository.py` | 2026-05-27 | Brand-local ABC enforces dual filter. F2-S1 new repos inherit + validate_dual_filter(...) at top of each query method. |
| Anthropic graceful-degradation patterns for external dependencies | (tessl tile `graceful-degradation` consulted via skill) | 2026-05-27 | Saga compensation: charge OK + fiscal fail → don't rollback charge, log + retry-emit standalone. Idempotency key reused on retry. |

**Knowledge cutoff disclosure:** Opus 4.7 cutoff = Jan 2026. For Shadcn UI patterns (post-Jan-2026 minor updates), Next.js 16 + React Query v5 (current as of access date), and MSW v2 integration patterns researched live via canonical URLs on 2026-05-27.

---

## § 15 — File Structure Summary

### 15.1 Backend NEW + MODIFIED

```
vitalia/backend/src/modules/vitalia/
├── scheduling/                                        # NEW module brand-extension
│   ├── __init__.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── agenda_filter.py                          # AgendaPresetFilter StrEnum
│   │   ├── appointment_origin.py                     # AppointmentOrigin StrEnum
│   │   ├── agenda_view.py                            # AgendaView StrEnum
│   │   ├── agenda_slot.py                            # @dataclass projection
│   │   ├── appointment_payment.py                    # @dataclass
│   │   └── slot_payment_status.py                    # SlotPaymentStatus StrEnum
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   └── repositories/
│   │       ├── agenda_grid_repository.py             # ABC
│   │       ├── agenda_grid_repository_impl.py        # SQLA 2.0 impl
│   │       ├── appointment_detail_repository.py
│   │       ├── appointment_payment_repository.py     # optimistic lock + idempotency
│   │       └── appointment_aggregates_repository.py
│   ├── application/
│   │   ├── __init__.py
│   │   ├── services/
│   │   │   ├── agenda_grid_service.py
│   │   │   ├── appointment_detail_service.py
│   │   │   ├── appointment_status_service.py
│   │   │   ├── create_appointment_service.py
│   │   │   ├── charge_orchestrator.py                # ★ saga
│   │   │   └── notify_service.py
│   │   └── ports/
│   │       ├── payment_charge_port.py                # ABC
│   │       └── fiscal_emit_port.py                   # ABC
│   ├── api/
│   │   ├── __init__.py
│   │   ├── agenda_router.py                          # GET grid + aggregates + detail + POST create + PATCH status + POST notify
│   │   └── dtos/
│   │       ├── agenda_dtos.py
│   │       └── notify_dtos.py
│   └── persistence/
│       ├── __init__.py
│       ├── models/
│       │   ├── appointment_payment_model.py
│       │   ├── appointment_clinic_map_model.py
│       │   └── fiscal_document_model.py              # SA reference shared from fiscal/ module
│       └── migrations/                                # migrations live under vitalia/backend/alembic/versions/
├── payments/                                          # NEW module
│   ├── __init__.py
│   ├── application/
│   │   ├── payment_charge_port_impl.py               # selects adapter per tenant.payment_gateway
│   │   └── stubs/
│   │       └── stub_payment_charge_port.py           # service-blocker stub
│   └── api/
│       ├── charge_router.py                          # POST /api/v1/payments/charge
│       └── dtos/
│           └── charge_dtos.py
├── fiscal/                                            # NEW module
│   ├── __init__.py
│   ├── domain/
│   │   └── fiscal_document.py
│   ├── infrastructure/
│   │   └── repositories/
│   │       └── fiscal_document_repository.py
│   ├── application/
│   │   ├── fiscal_emit_port_impl.py                  # selects provider per tenant.country (PE→nubefact, AR→afip stub, MX→sat stub)
│   │   └── stubs/
│   │       └── stub_fiscal_emit_port.py              # service-blocker stub
│   └── api/
│       ├── emit_router.py                            # POST /api/v1/fiscal/emit
│       └── dtos/
│           └── emit_dtos.py
├── _shared/
│   ├── telemetry/                                     # NEW
│   │   ├── __init__.py
│   │   ├── growth_studio_emitter.py
│   │   └── amount_bucket.py
│   ├── phi_masking.py                                # NEW shared util
│   └── auth/
│       └── rbac.py                                   # MODIFY add require_phi_access
└── extensions.py                                      # MODIFY add scheduling EP if applicable

vitalia/backend/alembic/versions/
└── XXXX_f2_s1_vitalia_agenda.py                      # NEW migration

vitalia/backend/tests/
├── modules/vitalia/scheduling/                        # NEW
│   ├── test_agenda_slot_domain.py
│   ├── test_agenda_grid_repository.py
│   ├── test_appointment_payment_repository.py
│   ├── test_agenda_grid_service.py
│   ├── test_appointment_detail_service.py
│   ├── test_charge_orchestrator.py
│   ├── test_notify_service.py
│   ├── test_drawer_charge_flow.py
│   ├── test_phi_url_protection.py
│   ├── test_dual_filter_clinic_isolation.py
│   ├── test_audit_log_drawer.py
│   ├── test_notify_compliance_guard.py
│   ├── test_create_appointment_router.py
│   └── test_patch_status_router.py
└── architecture/
    ├── test_scheduling_module_ddd.py                  # NEW
    ├── test_no_phi_in_url_params.py                   # NEW
    └── test_audit_log_row_per_phi_endpoint.py         # NEW
```

### 15.2 Frontend NEW + MODIFIED

```
vitalia/frontend/src/
├── app/[tenantId]/(shell-organism)/
│   └── valeria/                                       # NEW segment
│       └── agenda/
│           └── page.tsx                               # NEW Server Component
├── features/valeria/
│   ├── components/agenda/                             # NEW (17 components)
│   │   ├── ValeriaAgendaView.tsx
│   │   ├── AgendaHeader.tsx
│   │   ├── AgendaCalendar.tsx
│   │   ├── DayCalendar.tsx
│   │   ├── WeekCalendar.tsx
│   │   ├── MonthCalendar.tsx
│   │   ├── AgendaSlot.tsx                            # NEW (replaces F1-S10 placeholder)
│   │   ├── AppointmentDrawer.tsx
│   │   ├── AppointmentDrawerSkeleton.tsx
│   │   ├── CobrarSaldoSubform.tsx                    # ★
│   │   ├── AgendaPresetFilters.tsx
│   │   ├── CrearCitaButton.tsx
│   │   ├── CrearCitaForm.tsx
│   │   ├── PatientAutocomplete.tsx
│   │   ├── FreshnessIndicator.tsx
│   │   ├── MobileBottomSheet.tsx
│   │   ├── SkeletonCalendar.tsx
│   │   └── __tests__/                                 # vitest co-located
│   ├── components/placeholders/
│   │   └── AgendaPlaceholder.tsx                     # DELETE post-merge
│   ├── api/                                           # NEW
│   │   ├── agenda.ts
│   │   ├── agenda-server.ts
│   │   ├── payments.ts
│   │   ├── fiscal.ts
│   │   └── notify.ts
│   ├── hooks/                                         # NEW
│   │   ├── useAgendaFilters.ts
│   │   ├── useDrawerWidth.ts
│   │   └── useFreshness.ts
│   ├── store/                                         # NEW
│   │   ├── drawer-store.ts
│   │   └── filters-store.ts
│   ├── types/                                         # NEW
│   │   ├── agenda.types.ts
│   │   └── agenda-schema.ts
│   └── index.ts                                       # MODIFY public API exports
├── components/ui/                                     # NEW Shadcn primitives
│   ├── sheet.tsx
│   ├── accordion.tsx
│   ├── calendar.tsx
│   ├── popover.tsx
│   ├── select.tsx
│   ├── form.tsx
│   └── sonner.tsx
├── lib/
│   ├── tenant-locale.ts                              # MODIFY/EXTEND if absent
│   └── telemetry.ts                                  # NEW (amount_bucket mirror + emit helper)
└── test-utils/
    └── msw/handlers/
        └── agenda-handlers.ts                        # NEW (payment + fiscal mocks)

vitalia/frontend/e2e/
├── regression/vitalia-fase2-valeria-agenda/           # NEW (per test_construction_plan)
│   ├── fixtures/
│   │   ├── valeria-agenda.fixture.ts
│   │   ├── mock-payment-adapter.ts
│   │   ├── mock-fiscal-emission.ts
│   │   └── network-failure.ts
│   ├── poms/
│   │   ├── agenda-view-page.pom.ts
│   │   ├── appointment-drawer-page.pom.ts
│   │   ├── cobrar-saldo-subform-page.pom.ts
│   │   └── crear-cita-button-page.pom.ts
│   └── *.spec.ts                                      # 11 spec files per § 11.3
├── a11y/
│   └── valeria-agenda-a11y.spec.ts                   # NEW
└── __screenshots__/agenda/                            # ~14 visual goldens
    ├── week-light.png · week-dark.png
    ├── day-light.png · day-dark.png
    ├── month-light.png · month-dark.png
    ├── drawer-open-light.png · drawer-open-dark.png
    ├── drawer-cobrar-saldo-expanded-light.png
    ├── drawer-cobrar-saldo-success-light.png
    ├── drawer-cobrar-saldo-error-light.png
    ├── drawer-cobrar-saldo-conflict409-light.png
    ├── slot-matrix-light.png · slot-matrix-dark.png
    └── mobile-day-bottom-sheet-light.png
```

---

## § 16 — Open Questions for PM

(Resolved during architect orchestration — listed for transparency)

1. ✅ **Telemetry sink table?** → NEW `vitalia_growth_studio_event` brand-local (A4). Architect ratified independently from `copilot_trace_event` per spec § 10 hint.
2. ✅ **`clinic_id` on engine `Appointment`?** → NO modify engine. Brand-local `vitalia_appointment_clinic_map` joins (A12).
3. ✅ **Service-blocker policy?** → Option A (stub + MSW) default (A13). /dev-team `06-tickets.yaml` notes_for_downstream documenta.
4. ✅ **Fiscal emit per-country provider mapping?** → tenant.country resolves provider (PE→nubefact, AR→afip stub, MX→sat stub). F2-S1 stub all 3; real impl land cuando `vitalia-fiscal-emission-pe` developed (PE primero).
5. ✅ **Concurrent charge 409 detection mechanism?** → Optimistic lock via `balance_version` column (A7); not row-level `SELECT FOR UPDATE` (blocks reads paralelos).
6. ✅ **Stub deprecation tracking?** → Stubs commented `# DEPRECATED: replace when vitalia-{service-blocker} state=done`. Auditor verifies via grep arch test that no production code path uses stubs at story merge time.

(No outstanding open questions blocking /dev-team pickup. Service-deps blockers documented in `06-tickets.yaml` per-ticket.)

