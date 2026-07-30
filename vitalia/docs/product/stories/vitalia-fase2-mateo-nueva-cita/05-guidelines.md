# 05-guidelines — Nueva cita usable (build guidelines)

> Para `builder-backend` + `builder-frontend`. Consume con `03-arch.md` + `03-arch-{be,fe}.md` + `04-validators.yaml`.

## must_load_skills (enforceable por ticket)

### Backend tickets
- `backend-expert` — DDD inside-out, arch fitness, idempotent migrations, master-data UTC.
- `vitalia hipaa-lite` rule (`vitalia/.claude/rules/hipaa-lite.md`) — dual filter, audit sync, `@require_phi_access`, pgcrypto, response_model.
- `.claude/rules/backend-migrations.md` — raw SQL idempotente.
- `.claude/rules/tenant-isolation.md` + `.claude/rules/pii-sanitisation.md`.

### Frontend tickets
- `frontend-expert` — FSD-Lite, Server-First, React Query keys, RHF+Zod.
- `vitalia-design-system` skill — shell organism + tokens + agente Mateo.
- `design-system-canon.md § 5` (Storybook = SSoT visual) — partir de Storybook, net-new = PROMOTE.
- `.claude/rules/frontend-visual-fidelity.md` (D1/D2/D3) + `.claude/rules/frontend-fsd.md`.
- `playwright-expert` — E2E autenticado Clerk + dev-app live-verify (Rule #37).
- `chrome-devtools-verify` — live-verify writes reales.

## Patterns REQUIRED

### Backend
- SQLAlchemy 2.0: `select(Model).where(Model.tenant_id == tid, Model.clinic_id == cid)`. NUNCA `session.query()`.
- Pydantic v2: `model_config = ConfigDict(from_attributes=True)`. `response_model=` en CADA route.
- Async everywhere (repos, services, handlers).
- Dual filter `tenant_id` AND `clinic_id` en TODA query PHI (availability, create, patient).
- `@require_phi_access(roles=["admin_clinic","doctor"])` (o el check `if user_role not in ALLOWED_PHI_ROLES: 403` como el create existente) en availability/create/patient endpoints.
- Audit log sync write ANTES de la respuesta en create + patient inline create.
- PHI masking server-side: `name_masked`/`phone_masked` (nunca raw fuera del create body). Availability/day-strip responses SIN PHI de paciente.
- Overlap = half-open `s1 < e2 AND s2 < e1` (back-to-back NO solapa).
- 23P01 (`orig.sqlstate == '23P01'`) → 409 `APPOINTMENT_OVERLAP`. Out-of-horario pre-insert → 422 `OUT_OF_HOURS`.
- Migración: `DO $$ IF NOT EXISTS (pg_constraint) $$`, `ADD COLUMN IF NOT EXISTS`, `CREATE EXTENSION IF NOT EXISTS btree_gist`.
- El create escribe `start_time`/`end_time`/`status` en `vitalia_appointment_clinic_map` (mirror para el EXCLUDE). Status updates (cancel) propagan a la columna mirror.
- `structlog`, no `print`/`logging`.
- TDD RED por capa: domain → infra → app → api/migration.

### Frontend
- Server Component default. `"use client"` solo en `NuevaCitaView` + hojas con state.
- Componentes del kit por superficie (ver `03-arch-fe.md § 0` — citar la story de Storybook). NO `<select>` nativo (RichSelect). NO `<div>` de layout donde hay primitiva (FormPageScaffold/PageContainer).
- React Query (server data) + Zustand (UI state ONLY) — sin mezclar.
- RHF + `zodResolver`. Submit explícito (FormActionBar sticky), no autosave.
- React Query keys `["mateo","nueva-cita",action,...stableFilters]`.
- `useAvailabilityCheck` debounced + revalida al cambiar franja/servicio/médico (SC-revalida-cambio).
- `tenant_id` via `useTenantId()` — NUNCA `useAuth().orgId`.
- tz: `useTenantLocale()` / `formatTenantDate*()`; envía UTC; `SmartDatetimePicker` convierte.
- Spanish neutro LatAm (tuteo, sin voseo) en strings + chip labels + errores.
- Crear deshabilitado hasta chip `AVAILABLE` + form válido (fail-closed RN-10).
- Paciente inline via `EntityPicker.createAction` (consume kit) — mini-form nombre+teléfono, preselecciona sin salir.
- Headers `// cap: scheduling.mateo-agenda` líneas 1-3 en archivos nuevos.

## Patterns FORBIDDEN

- ❌ Editar `core/luana-core-scheduling/src/` o `appointment_model.py` (engine boundary — D-A). El EXCLUDE va en `vitalia_appointment_clinic_map` (brand-local).
- ❌ Editar `core/@luana/ui-kit/src/` desde un ticket de marca (los 4 atoms = PROMOTE vía `/pm-luana`).
- ❌ Re-implementar FormActionBar / Badge success-warning / PageHeader back-pill / EntityPicker.createAction en `features/mateo/` (consumir del kit; net-new local = drift = CHANGES_REQUESTED).
- ❌ Stub de paciente con `uuid.uuid4()` (el bug actual — el create recibe `patient_id` real).
- ❌ Drawer/modal para Nueva cita (AC-9 — hoja full-page, data-safe). El `CrearCitaButton` Dialog MUERE → `router.push`.
- ❌ `op.create_table()` / `sa.Enum(create_type=True)` / migración no idempotente.
- ❌ PHI en URL/searchParams (`patient_id` nunca). PHI sin masking en response. Query sin dual filter.
- ❌ Chequear BUSY pre-insert en create (TOCTOU) — el EXCLUDE lo garantiza atómico; el chip FE es advisory.
- ❌ `<select>` nativo, colores hardcoded, `<div>` de layout, voseo.
- ❌ Cross-feature import (`features/A` → `features/B`). Cross-brand import (absolutamente).
- ❌ Mock del backend del surface bajo prueba en E2E (falso verde — Rule #37; la live-verify ejerce writes reales).

## Files in scope

### Backend
```
scheduling/domain/availability_check.py                              [NEW]
scheduling/application/services/availability_check_service.py        [NEW]
scheduling/application/ports/availability_source_port.py             [NEW]
scheduling/infrastructure/repositories/availability_query_repository.py [NEW]
scheduling/api/availability_router.py                                [NEW]
scheduling/api/dtos/availability_dtos.py                             [NEW]
scheduling/application/services/create_appointment_service.py        [MOD]
scheduling/application/services/appointment_status_service.py        [MOD]
scheduling/api/agenda_router.py                                      [MOD]
scheduling/persistence/models/appointment_clinic_map_model.py        [MOD]
crm/api/router.py                                                    [MOD]
crm/application/services/patient_service.py                         [MOD]
crm/application/dto/patient_dto.py                                  [MOD]
crm/infrastructure/persistence/patient_repository.py                [MOD]
offer/<catalog DTO + catalog_service> (BE-1)                        [MOD]
vitalia/backend/alembic/versions/050_vitalia_appointment_no_overlap.py [NEW]
vitalia/backend/src/main.py (include_router availability)           [MOD]
+ tests por capa (04-validators § test_construction_plan)
```

### Frontend
```
app/[tenantId]/(shell-organism)/mateo/agenda/nueva-cita/page.tsx    [NEW]
app/[tenantId]/(shell-organism)/mateo/agenda/nueva-cita/loading.tsx [NEW]
app/[tenantId]/(shell-organism)/mateo/agenda/nueva-cita/error.tsx   [NEW]
features/mateo/components/nueva-cita/NuevaCitaView.tsx               [NEW]
features/mateo/components/nueva-cita/ServicePicker.tsx               [NEW]
features/mateo/components/nueva-cita/DoctorPicker.tsx                [NEW]
features/mateo/components/nueva-cita/PatientPickerWithCreate.tsx     [NEW]
features/mateo/components/nueva-cita/AvailabilityChip.tsx            [NEW]
features/mateo/components/nueva-cita/DayAvailabilityStrip.tsx        [NEW · ◆ feature]
features/mateo/components/nueva-cita/FreeDoctorsList.tsx             [NEW]
features/mateo/components/nueva-cita/NuevaCitaActions.tsx            [NEW]
features/mateo/api/nueva-cita.ts                                     [NEW]
features/mateo/store/nueva-cita-store.ts                            [NEW]
features/mateo/types/agenda-schema.ts                              [MOD]
features/mateo/index.ts                                            [MOD]
features/mateo/components/agenda/CrearCitaButton.tsx               [MOD → router.push]
features/mateo/components/agenda/AgendaSlotInteractive.tsx         [MOD → push prefilled]
features/mateo/components/agenda/CrearCitaForm.tsx                 [REMOVE/migrate tests]
+ tests (04-validators § test_construction_plan)
```

### Forbidden to touch
```
core/luana-core-scheduling/src/**          (engine)
core/@luana/ui-kit/src/**                  (CORE — 4 atoms via /pm-luana)
otros features (lisa/, adrian/, etc.)
otras marcas (comunify/, nicolify/, lupulo/)
```

## HIPAA-lite checklist (todo ticket BE PHI)

1. Dual filter `tenant_id` AND `clinic_id` en CADA query.
2. `@require_phi_access` / role check en el endpoint.
3. `response_model=` whitelist (sin PHI fuera de campos permitidos).
4. Audit log sync write pre-response en create + patient create.
5. `name_masked`/`phone_masked` server-side; availability sin PHI de paciente.
6. Tests obligatorios (hipaa-lite.md § Tests requeridos): PHI no leaked, audit row, cross-tenant 404, cross-clinic 403, sanitize en traces, channel guard (N/A aquí).

## Live-verify (Rule #37 · funcional)

- `make dev-app-vitalia` → `dev-app.vitalialat.com` (Chrome DevTools MCP) o `localhost:3002`.
- Ejercer writes reales (autenticado `dr.demo@vitalialat.com` o equivalente admin_clinic): crear cita válida (201 + fila + grilla), crear paciente inline (201 + directorio), forzar solape (409). Leer logs BE + confirmar efecto DB.
- Registrar `dod_live_verified: true` + `dod_evidence` + `verified_at` en checkpoint.
- Chris firma en G (`chris_verify.signoff`) — funcional + demo.
