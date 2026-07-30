<!-- voseo-allowed: glosario reference (forbidden voseo examples documented) -->
# 05-guidelines.md — F2-S1 vitalia-fase2-valeria-agenda

> Owner: `/architect` orchestrator. Patterns concretos que el `/dev-team` builder DEBE seguir/evitar — SIN AMBIGÜEDAD.
> Si dev-team sigue al pie + corre validators GREEN → ticket pasa auditoría.

---
story_id: vitalia-fase2-valeria-agenda
brand: vitalia
arch_version: 1
schema_version: v4.1
last_modified: 2026-05-27T00:00:00Z
hipaa_lite_overlay: true
---

## must_load_skills (★ v4.1 enforceable — builder MUST cargar todas + reportar "Skills consulted" en T-{n}-result.md)

> Builder spawn prompt cita esta lista verbatim. Si builder no carga + documenta → auditor CHANGES_REQUESTED automático.

### required (sin condición)

| ID | Tipo | Aplica a | Razón |
|---|---|---|---|
| `.claude/rules/tenant-isolation.md` | rule | TODOS tickets | Every query filter tenant_id |
| `vitalia/.claude/rules/hipaa-lite.md` | rule (brand overlay) | TODOS tickets BE | Dual filter tenant_id+clinic_id + audit log sync + PHI sanitize + RBAC roles médicos + ComplianceService guard + voice patterns |
| `.claude/rules/anti-duplication.md` | rule | TODOS tickets | Cross-brand mirror ban + shared abstractions inventory (`scheduling/payments/fiscal` NO mirror) |
| `.claude/rules/tdd-mandatory.md` | rule | TODOS tickets | RED→GREEN→REFACTOR — tests FIRST por capa |
| `.claude/rules/spanish-text.md` | rule | TODOS tickets FE | Voseo glosario neutro LatAm |
| `.claude/rules/auditor-self-fix-policy.md` | rule | TODOS | Conocer qué findings auditor self-fix vs spawn dev-team |
| `.claude/rules/git-safety.md` | rule | TODOS | Triple-branch + forbidden ops + Conventional Commits |
| `.claude/rules/parallel-safety.md` | rule | TODOS | M11 push >30min + sub-agents NO crean worktree |

### required by surface

| ID | Tipo | When |
|---|---|---|
| `backend-expert` | skill | surface=BE — DDD patterns + arch fitness + currency + master-data |
| `.claude/rules/backend-ddd.md` | rule | surface=BE — Inside-Out + SQLA 2.0 + tenant_id every query + soft delete |
| `.claude/rules/backend-migrations.md` | rule | surface=BE migrations — idempotent raw SQL `IF NOT EXISTS` |
| `.claude/rules/master-data.md` | rule | surface=BE — UTC store + `DateTime(timezone=True)` |
| `.claude/rules/currency-handling.md` | rule | surface=BE/FE — DTOs monetary include currency field, FE no hardcode |
| `vitalia/backend/src/modules/vitalia/_shared/repositories/phi_repository.py` | code SSoT | surface=BE PHI repo — heredar PhiRepositoryBase + validate_dual_filter |
| `vitalia/backend/src/modules/vitalia/audit/audit_writer.py` | code SSoT | surface=BE PHI endpoint — usar AsyncAuditWriter |
| `core/luana-core-observability/src/luana_core_observability/recording/sanitization.py` | code SSoT (engine read-only) | surface=BE — sanitize_payload(compliance_level='hipaa_lite') |
| `frontend-expert` | skill | surface=FE — FSD-Lite + Shadcn reuse + form-runtime + tokens |
| `.claude/rules/frontend-fsd.md` | rule | surface=FE — boundary matrix + features/{m}/ |
| `playwright-expert` | skill | test_construction_plan.playwright_required=true — POMs + Clerk auth + MSW + smoke debugging |
| `.claude/rules/e2e-testing.md` | rule | surface=FE E2E — Playwright config vitalia port 3002 |
| `tessl__fastapi` | tessl tile | BE endpoint nuevo |
| `tessl__pytest-api-testing` | tessl tile | BE tests nuevos |
| `tessl__react-patterns` | tessl tile | FE component nuevo |
| `tessl__shadcn-ui` | tessl tile | FE component Shadcn install/use |
| `tessl__tailwind` | tessl tile | FE component (tokens semánticos) |
| `tessl__zod` | tessl tile | FE form con validation |
| `tessl__vitest` | tessl tile | FE tests nuevos |
| `tessl__nextjs-app-router-modularization` | tessl tile | FE route nueva |
| `tessl__graceful-degradation` | tessl tile | BE saga payment+fiscal compensation + FE retry flows |

### NO required (explicit exclusion)

- `copilot-expert` — N/A (no agentic surface, Valeria.agenda es UI operativa)
- `sales-agent-expert` — N/A (idem)
- `tessl__langgraph` — N/A
- `claude-api` — N/A (no LLM call runtime)
- `metrics-expert` — Skill consultada por architect para decidir `vitalia_growth_studio_event` (A4); builder NO carga (no analytics ETL en F2-S1)

### reference_artifacts (re-read mid-build cuando surge ambigüedad)

- `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/01-spec.md` — 30 AC + 11 Gherkin SC
- `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/03-arch.md` — Decisiones técnicas + § Test Construction Plan
- `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/04-validators.yaml` — validators + test_construction_plan (orden + POMs + fixtures + scenario_to_test)
- `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/06-tickets.yaml` — ticket T-{n} entry + gherkin_coverage
- `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/mockups/*.html` — 10 mockups ratificados Chris (visual fidelity SSoT)
- `vitalia/.claude/rules/hipaa-lite.md` — overlay brand cardinal
- `vitalia/.claude/rules/shell-mockup-per-component.md` — visual fidelity gate
- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` — atomic design SSoT (§ 3 átomos/moléculas, § 7 routing, § 8 a11y, § 9 testing)
- `vitalia/docs/product/stories/vitalia-shell-organism/navigation-tree.md` § valeria.agenda

---

## Files in scope (builder PUEDE tocar)

### Backend NEW

```
vitalia/backend/src/modules/vitalia/scheduling/{__init__,domain/{__init__,agenda_filter,appointment_origin,agenda_view,agenda_slot,appointment_payment,slot_payment_status},infrastructure/{__init__,repositories/{__init__,agenda_grid_repository,agenda_grid_repository_impl,appointment_detail_repository,appointment_payment_repository,appointment_aggregates_repository}},application/{__init__,services/{__init__,agenda_grid_service,appointment_detail_service,appointment_status_service,create_appointment_service,charge_orchestrator,notify_service},ports/{__init__,payment_charge_port,fiscal_emit_port}},api/{__init__,agenda_router,dtos/{__init__,agenda_dtos,notify_dtos}},persistence/{__init__,models/{__init__,appointment_payment_model,appointment_clinic_map_model}}}.py
vitalia/backend/src/modules/vitalia/payments/{__init__,application/{__init__,payment_charge_port_impl,stubs/{__init__,stub_payment_charge_port}},api/{__init__,charge_router,dtos/{__init__,charge_dtos}}}.py
vitalia/backend/src/modules/vitalia/fiscal/{__init__,domain/{__init__,fiscal_document},infrastructure/{__init__,repositories/{__init__,fiscal_document_repository},models/{__init__,fiscal_document_model}},application/{__init__,fiscal_emit_port_impl,stubs/{__init__,stub_fiscal_emit_port}},api/{__init__,emit_router,dtos/{__init__,emit_dtos}}}.py
vitalia/backend/src/modules/vitalia/_shared/telemetry/{__init__,growth_studio_emitter,amount_bucket}.py
vitalia/backend/src/modules/vitalia/_shared/phi_masking.py
vitalia/backend/alembic/versions/XXXX_f2_s1_vitalia_agenda.py
```

### Backend MODIFY

```
vitalia/backend/src/modules/vitalia/_shared/auth/rbac.py             # add require_phi_access decorator
vitalia/backend/src/modules/vitalia/extensions.py                    # add scheduling router include si EP-required
vitalia/backend/src/main.py                                          # include new routers via include_router
```

### Backend tests NEW

```
vitalia/backend/tests/modules/vitalia/scheduling/{__init__,test_agenda_slot_domain,test_agenda_grid_repository,test_appointment_payment_repository,test_agenda_grid_service,test_appointment_detail_service,test_charge_orchestrator,test_notify_service,test_drawer_charge_flow,test_phi_url_protection,test_dual_filter_clinic_isolation,test_audit_log_drawer,test_notify_compliance_guard,test_create_appointment_router,test_patch_status_router}.py
vitalia/backend/tests/architecture/{test_scheduling_module_ddd,test_no_phi_in_url_params,test_audit_log_row_per_phi_endpoint}.py
```

### Frontend NEW

```
vitalia/frontend/src/app/[tenantId]/(shell-organism)/valeria/agenda/page.tsx
vitalia/frontend/src/features/valeria/components/agenda/{ValeriaAgendaView,AgendaHeader,AgendaCalendar,DayCalendar,WeekCalendar,MonthCalendar,AgendaSlot,AppointmentDrawer,AppointmentDrawerSkeleton,CobrarSaldoSubform,AgendaPresetFilters,CrearCitaButton,CrearCitaForm,PatientAutocomplete,FreshnessIndicator,MobileBottomSheet,SkeletonCalendar}.tsx
vitalia/frontend/src/features/valeria/components/agenda/__tests__/{ValeriaAgendaView,AgendaCalendar,AgendaSlot,AppointmentDrawer,CobrarSaldoSubform,AgendaPresetFilters,CrearCitaButton}.test.tsx
vitalia/frontend/src/features/valeria/api/{agenda,agenda-server,payments,fiscal,notify}.ts
vitalia/frontend/src/features/valeria/api/__tests__/agenda.test.ts
vitalia/frontend/src/features/valeria/hooks/{useAgendaFilters,useDrawerWidth,useFreshness}.ts
vitalia/frontend/src/features/valeria/store/{drawer-store,filters-store}.ts
vitalia/frontend/src/features/valeria/types/{agenda.types,agenda-schema}.ts
vitalia/frontend/src/components/ui/{sheet,accordion,calendar,popover,select,form,sonner}.tsx      # npx shadcn add
vitalia/frontend/src/lib/telemetry.ts
vitalia/frontend/src/test-utils/msw/handlers/agenda-handlers.ts
vitalia/frontend/e2e/regression/vitalia-fase2-valeria-agenda/{fixtures,poms}/*.ts
vitalia/frontend/e2e/regression/vitalia-fase2-valeria-agenda/valeria-agenda-*.spec.ts (11 files)
vitalia/frontend/e2e/a11y/valeria-agenda-a11y.spec.ts
vitalia/frontend/e2e/visual/valeria-agenda-visual.spec.ts
vitalia/frontend/e2e/__screenshots__/agenda/*.png (~14 visual goldens)
```

### Frontend MODIFY

```
vitalia/frontend/src/features/valeria/index.ts                        # public API exports
vitalia/frontend/src/lib/tenant-locale.ts                             # EXTEND if absent (useTenantLocale + formatTenantMoney)
```

### Frontend DELETE (post-merge)

```
vitalia/frontend/src/features/valeria/components/placeholders/AgendaPlaceholder.tsx         # replaced by real feature
vitalia/frontend/src/features/valeria/components/placeholders/AgendaPlaceholder.test.tsx
# Remove AgendaPlaceholder reference from SubTabContent.tsx PLACEHOLDER_MAP (replace with sentinel "moved to dedicated route")
```

---

## Files NEVER touch (HARD ban)

### Engine (read-only)

```
core/luana-core-*/src/**                                              # ALL engine packages — modify requires /pm-luana proposal
core/luana-core-scheduling/                                            # consumed via consumer pattern, NO mirror
core/luana-core-platform/                                              # base entities + datetime_utils consumed via import
core/luana-core-observability/                                         # sanitize_payload + sanitization consumed via import
core/luana-core-channels/                                              # template-only WhatsApp via ComplianceService
core/luana-core-compliance/                                            # ComplianceService consumed brand-local
core/luana-core-iam/                                                   # RBAC consumed brand-local
core/luana-core-billing/                                               # NO billing wiring this story
```

### Other brands

```
nicolify/**                                                            # HARD ban cross-brand
comunify/**
lupulo/**
```

### Default flag flips R31

```
vitalia/backend/src/core/config.py                                     # DO NOT flip USE_*_PATTERN_* / LITELLM_PROXY_ENABLED / USE_DEEPAGENTS_* — story does not require + would invalidate audit per anti-default-flip-audit.md
```

### Skills + rules + process

```
.claude/skills/**                                                      # meta-paradigm — escalate Chris
.claude/rules/**                                                       # idem
vitalia/.claude/rules/**                                               # idem (brand overlay rules)
docs/process/**                                                        # idem
docs/architecture/**                                                   # idem (workspace-level)
vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md                     # SSoT shell — escalate /pm-vitalia si visual diverge
vitalia/.claude/rules/shell-mockup-per-component.md                    # gate rule
```

### Other vitalia modules (NO cross-module SQL JOINs)

```
vitalia/backend/src/modules/vitalia/crm/                               # consume via API /api/v1/crm/patients only
vitalia/backend/src/modules/vitalia/clinics/                           # consume via service injection (clinic_id from JWT claims)
vitalia/backend/src/modules/vitalia/audit/                             # consume AsyncAuditWriter import — do NOT modify
vitalia/backend/src/modules/vitalia/compliance/                        # consume ComplianceService.validate_outbound_message — do NOT modify
vitalia/backend/src/modules/vitalia/payment/{stripe_connect_adapter,mercadopago_adapter,tokenized_recurring_adapter}.py  # consume via PaymentChargePort wrapper, do NOT modify scaffolds
```

---

## Patterns required

### Backend (surface=BE)

#### SQLAlchemy 2.0

```python
# ✅ CORRECT
result = await session.execute(
    select(AppointmentModel, VitaliaAppointmentClinicMapModel)
    .join(VitaliaAppointmentClinicMapModel,
          VitaliaAppointmentClinicMapModel.appointment_id == AppointmentModel.id)
    .where(
        VitaliaAppointmentClinicMapModel.tenant_id == tenant_id,
        VitaliaAppointmentClinicMapModel.clinic_id == clinic_id,
        VitaliaAppointmentClinicMapModel.deleted_at.is_(None),
    )
)
rows = result.all()

# ❌ PROHIBITED — SA 1.x legacy
rows = session.query(AppointmentModel).filter_by(tenant_id=tenant_id).all()
```

#### Dual filter HIPAA

```python
# ✅ CORRECT — heredar PhiRepositoryBase
class AgendaGridRepository(PhiRepositoryBase):
    async def list_grid(self, *, tenant_id: UUID, clinic_id: UUID, ...):
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)
        # ... query con dual filter ...

# ❌ PROHIBITED — skip dual filter "because single-clinic tenant"
async def list_grid(self, *, tenant_id: UUID):  # clinic_id missing
    ...
```

#### Audit log sync write

```python
# ✅ CORRECT — sync write BEFORE response
async def get_detail(self, ...) -> AppointmentDetailDTO:
    detail = await self.repo.get_by_id(...)
    if not detail:
        await self.audit.write(action="cross_clinic_attempt", ...)  # sync
        raise HTTPException(404)
    await self.audit.write(action="read_appointment_detail", ...)   # sync BEFORE return
    return project_phi_masked(detail)

# ❌ PROHIBITED — async fire-forget
asyncio.create_task(self.audit.write(...))  # NO acknowledgment
```

#### Pydantic v2

```python
# ✅ CORRECT
class ChargeRequestDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    amount_cents: int = Field(..., gt=0)

# ❌ PROHIBITED — inner class Config (v1 style)
class ChargeRequestDTO(BaseModel):
    class Config:
        orm_mode = True
```

#### structlog (no print/logging)

```python
# ✅ CORRECT
logger.info("agenda_grid_fetched", tenant_id=str(tenant_id), slot_count=len(slots))

# ❌ PROHIBITED
print(f"Fetched {len(slots)} slots")
logging.info(f"Patient {patient.name} loaded")  # NEVER — print PHI
```

#### Migrations idempotentes raw SQL

```python
# ✅ CORRECT
op.execute("CREATE TABLE IF NOT EXISTS vitalia_appointment_payments (...);")
op.execute("CREATE INDEX IF NOT EXISTS idx_vit_payment_tenant_clinic_apt ON ...;")

# ❌ PROHIBITED
op.create_table("vitalia_appointment_payments", ...)  # non-idempotent
op.create_index("idx_...", ...)                       # idem
sa.Enum(..., create_type=True)                        # broken SA 2.0.27
```

#### FastAPI

```python
# ✅ CORRECT
@router.post("/charge", response_model=ChargeResponseDTO, status_code=200)
async def charge(
    request: ChargeRequestDTO,
    user: User = Depends(require_phi_access()),
    tenant_id: UUID = Depends(get_tenant_id),
    clinic_id: UUID = Depends(get_clinic_id),
    orchestrator: ChargeOrchestrator = Depends(get_charge_orchestrator),
) -> ChargeResponseDTO:
    return await orchestrator.execute(tenant_id=tenant_id, clinic_id=clinic_id, request=request)

# ❌ PROHIBITED — missing response_model (PII leak risk)
@router.post("/charge")
async def charge(request: dict): ...
```

#### Date+time

```python
# ✅ CORRECT — use luana_core_platform utc_now() + DateTime(timezone=True)
from luana_core_platform.domain.datetime_utils import utc_now
created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

# ❌ PROHIBITED
created_at = datetime.utcnow()                # naive datetime
created_at: Mapped[datetime] = mapped_column(DateTime)  # no timezone
```

#### Currency

```python
# ✅ CORRECT — DTO field explicit
class ChargeRequestDTO(BaseModel):
    amount_cents: int
    currency: str = Field(..., min_length=3, max_length=3)

# ❌ PROHIBITED — hardcode + Pydantic default
class ChargeRequestDTO(BaseModel):
    amount_cents: int
    currency: str = "USD"   # NEVER — must come from data source
```

### Frontend (surface=FE)

#### React Server Components default

```tsx
// ✅ CORRECT — Server Component default page
// app/[tenantId]/(shell-organism)/valeria/agenda/page.tsx
export default async function ValeriaAgendaPage({ params, searchParams }) {
  const { tenantId } = await params;
  const initialData = await getInitialAgendaState({ tenantId, ... });
  return <ValeriaAgendaView initialData={initialData} />;
}

// ✅ CORRECT — 'use client' only in interactive components
// features/valeria/components/agenda/ValeriaAgendaView.tsx
"use client";
export function ValeriaAgendaView({ initialData }) {
  const query = useAgendaGrid({ initialData, ... });
  ...
}

// ❌ PROHIBITED — 'use client' en page (no SSR benefits)
"use client";
export default function ValeriaAgendaPage() { ... }
```

#### React Query keys + invalidation

```ts
// ✅ CORRECT — keys schema centralized
export const agendaKeys = {
  grid: (tenantId, clinicId, view, date, presetFilter) =>
    ["agenda", "grid", { tenantId, clinicId, view, date, presetFilter }] as const,
  appointment: (tenantId, clinicId, appointmentId) =>
    ["agenda", "appointment", { tenantId, clinicId, appointmentId }] as const,
};

useChargeMutation onSuccess: (data, vars) => {
  queryClient.invalidateQueries({ queryKey: agendaKeys.grid(tenantId, clinicId, view, date, presetFilter) });
  queryClient.invalidateQueries({ queryKey: agendaKeys.appointment(tenantId, clinicId, vars.appointment_id) });
}

// ❌ PROHIBITED — inline keys (drift risk)
useQuery({ queryKey: ["agenda-grid", view, date], ... })
```

#### RHF + Zod discriminated union

```ts
// ✅ CORRECT — discriminated union for multi-currency forms
export const chargeSchema = z.discriminatedUnion("currency", [
  z.object({ currency: z.literal("PEN"), fiscalDocType: z.enum(["boleta", "factura"]).optional(), ... }),
  z.object({ currency: z.literal("ARS"), fiscalDocType: z.enum(["factura_b", "factura_a", "recibo"]).optional(), ... }),
  ...
]).refine((d) => !d.emitInvoice || !!d.fiscalDocType, {
  message: "fiscalDocType requerido cuando emitInvoice=true",
  path: ["fiscalDocType"],
});

// ❌ PROHIBITED — any/unknown types
type ChargeFormValues = any;
```

#### Tailwind tokens

```tsx
// ✅ CORRECT — semantic tokens via CSS vars
<div className="border-l-[3px] border-l-[var(--color-success)] bg-card text-foreground">

// ❌ PROHIBITED — hex literals
<div className="border-l-[3px] border-l-[#10b981] bg-white text-black">
```

#### Spanish neutro LatAm

```tsx
// ✅ CORRECT — tuteo neutro
<button>Reintentar</button>
<p>Tomate un café o crea una cita walk-in.</p>
<dialog>¿Cancelar este turno?</dialog>

// ❌ PROHIBITED — voseo
<button>Reintentá</button>     // voseo
<p>Tomate un mate o creá...</p>  // voseo + léxico regional
```

#### PHI masking (never raw PHI)

```tsx
// ✅ CORRECT — consume server-masked DTO
<PHIMaskedText className="font-medium">{slot.patient_name_masked}</PHIMaskedText>
// patient_name_masked = "P. Hernández" from BE

// ❌ PROHIBITED — full name raw
<span>{patient.full_name}</span>  // contains PHI

// ❌ PROHIBITED — masking on frontend (defense-in-depth: BE projects masked)
<span>{maskClient(patient.full_name)}</span>
```

---

## Patterns forbidden

| ❌ Forbidden | ✅ Correct alternative |
|---|---|
| `datetime.utcnow()` | `utc_now()` from `luana_core_platform.domain.datetime_utils` |
| `'USD'` hardcoded default in DTO | `currency: str = Field(..., min_length=3, max_length=3)` |
| Cross-module SQL JOIN (e.g., scheduling JOIN crm.patients) | API call `/api/v1/crm/patients/{id}` or service injection |
| Cross-brand import (`from nicolify...`) | Lift to `core/luana-core-*` via `/pm-luana` proposal |
| `session.query(Model)` SA 1.x | `select(Model).where(...)` SA 2.0 |
| `sa.Enum(..., create_type=True)` | Raw SQL `IF NOT EXISTS` + `VARCHAR(N)` column |
| `op.create_table()` non-idempotent | `op.execute("CREATE TABLE IF NOT EXISTS ...")` |
| `// eslint-disable-next-line` without justification comment | Refactor — many violations = anti-pattern |
| `any` TypeScript type | `unknown` + type guard, or explicit type |
| `export default` (excepto Next.js pages) | Named exports |
| Hex colors literals `#10b981` | CSS vars `var(--color-success)` |
| PHI in URL query params | POST body or RBAC-derived from JWT |
| PHI in logs sin `sanitize_payload` | `sanitize_payload(payload, compliance_level='hipaa_lite')` |
| PHI in `localStorage` / `sessionStorage` | IDs hash only, fetch on-demand server-side |
| Audit log async fire-forget | Sync write via `AsyncAuditWriter` antes response |
| Mirror code from `core/luana-core-*` | Import + consume; lift requires `/pm-luana` proposal |
| `print()` / `logging.info()` | `structlog.get_logger()` + `logger.info(event, **kwargs)` |
| `console.log` in production code FE | Remove pre-commit (ESLint rule) |
| Inline React Query keys | Centralized `agendaKeys.{...}()` factory |
| `make e2e` / `make e2e-smoke` (Docker, crashes) | Native: `cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test` |
| Modify `core/luana-core-*/src/` | escalate `/pm-luana` promotion proposal |
| Skip `response_model=` on FastAPI endpoint | mandatory per arch test `test_response_model_required.py` |
| Bypass `FastAPI(redirect_slashes=False)` | Already enforced en `main.py`; leave alone |
| `from src.modules.X.domain import ...` cross-module | Use `shared/links/ports/` or domain events |

---

## Test discipline (TDD-mandatory per `.claude/rules/tdd-mandatory.md`)

**Order RED → GREEN → REFACTOR per layer:**

1. **Domain** RED: `test_agenda_slot_domain.py` (entity invariants + enums) → GREEN: implement domain
2. **Infrastructure** RED: `test_agenda_grid_repository.py` (dual filter + JOIN behavior) → GREEN: implement repo
3. **Application** RED: `test_charge_orchestrator.py` (saga happy + 503 + 409 + idempotency) → GREEN: implement service
4. **API** RED: `test_drawer_charge_flow.py` (end-to-end FastAPI testclient) → GREEN: wire router
5. **FE**: hook RED `agenda.test.ts` → component RED `CobrarSaldoSubform.test.tsx` → integration → smoke E2E

**Hook order (FE):** zustand store unit → React Query hook → component compose → page integration → E2E.

**No commit con tests rotos.** No `skip`/`xfail` para pasar CI. No reduce coverage sin justification.

---

## Service-deps gate (★ HARD pre-pickup)

| Story | State required | Current state | Builder action |
|---|---|---|---|
| `vitalia-payment-adapter-mvp` | `developed` | `refined` | Stub `vitalia/backend/src/modules/vitalia/payments/application/stubs/stub_payment_charge_port.py` + MSW handler |
| `vitalia-fiscal-emission-pe` | `developed` | `refining` | Stub `vitalia/backend/src/modules/vitalia/fiscal/application/stubs/stub_fiscal_emit_port.py` + MSW handler |

**Default action (Option A):** /dev-team uses stubs + MSW; production path implemented when service-blockers reach `developed`. Stubs annotated `# DEPRECATED: replace when story=done` + tracked in `06-tickets.yaml`. Architecture test `test_no_stub_in_prod_path.py` introduced post-merge ratchet enforces stub-free production wiring by story `done`.

**Escalate alternative (Option B):** If Chris/PM ratifies, /dev-team emits `state: blocked` + escalates `/pm-vitalia` to sequence service-blockers first.

---

## Mockup fidelity gate (★ vitalia/.claude/rules/shell-mockup-per-component.md)

- Cada componente NEW debe alinearse a su mockup HTML ratificado:
  - `agenda-week.html` → `WeekCalendar.tsx`
  - `agenda-day.html` → `DayCalendar.tsx`
  - `agenda-month.html` → `MonthCalendar.tsx`
  - `slot-states-matrix.html` → `AgendaSlot.tsx` (16 cells = 4 states × 3 origins + 4 interactive)
  - `appointment-drawer.html` → `AppointmentDrawer.tsx` (5 acordeones, resize handle, disabled tooltip)
  - `cobrar-saldo-subform.html` → `CobrarSaldoSubform.tsx` (10 states: collapsed/expanded × 4 currency + submitting + success + 2 errors + conflict-409)
  - `preset-filters.html` → `AgendaPresetFilters.tsx` (5 chips × 4 estados)
  - `crear-cita-dropdown.html` → `CrearCitaButton.tsx` + `CrearCitaForm.tsx` (3 variants)
  - `mobile-drawer-fullscreen.html` → `MobileBottomSheet.tsx`
- Visual goldens (Playwright `toHaveScreenshot`) `maxDiffPixelRatio: 0.001` (0.1% tolerance) side-by-side React component vs mockup-rendered HTML
- Ratchet shrink-only: una vez generado golden + ratificado, modificar requiere re-ratify explícito Chris

---

## Commit discipline (per `.claude/rules/git-safety.md`)

- Conventional Commits format: `<type>(<scope>): <desc>` — types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`, `wip`
- `<scope>` = `vitalia/f2-s1-agenda` or finer (e.g., `vitalia/f2-s1-agenda/charge`)
- Body must include `## Decisions honored` section citing decision IDs from § 12 of `03-arch.md` (e.g., D1, D5, A3, A6)
- Stage by exact filename — NUNCA `git add .` / `-A` / `-u`
- Branch destination: `wip/vitalia` (canonical worktree). Squash-merge to `main` post-auditor APPROVED + /pm-vitalia ratify
- Push >30min cumple M11
- Haiku delegation per `.claude/rules/git-haiku-delegation.md` cuando multi-file commits

---

## Definition of Done por ticket

Cada ticket `T-{n}` se considera done cuando:

1. ✅ Tests RED escritos primero (TDD) → GREEN tras impl
2. ✅ Validators de `04-validators.yaml` correspondientes a `acceptance.validator_ids` pasan GREEN
3. ✅ `gherkin_coverage` mapeo verificado en `06-tickets.yaml` (auditor Phase D ejecuta)
4. ✅ Spanish neutro pre-commit hook GREEN
5. ✅ HIPAA-lite checklist verificado (dual filter + audit log + sanitize + masking + RBAC)
6. ✅ Visual goldens generados (FE tickets touching UI)
7. ✅ Commit body cita `## Decisions honored` con D-IDs aplicables
8. ✅ `T-{n}-result.md` escrito con SHAs + `## Skills consulted (must_load enforcement v4.1)` section
9. ✅ Push wip/vitalia

