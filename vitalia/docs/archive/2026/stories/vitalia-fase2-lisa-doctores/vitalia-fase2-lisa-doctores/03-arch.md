---
story_id: vitalia-fase2-lisa-doctores
brand: vitalia
arch_version: 1
schema_version: v4.1
architecture_pattern: ADR-vitalia-004
adr_004_compliance: full
architect_run_on: '2026-05-31'
module: clinics
cap_target: lisa.doctores
cap_change_type: new
---

# 03-arch · vitalia-fase2-lisa-doctores — Directorio + Workspace de **Staff** (Lisa)

> **Consolidated arch.** Per-surface detail split: `03-arch-be.md` (backend) + `03-arch-fe.md` (frontend).
> Architect: Opus 4.8 single-shot. Knowledge cutoff Jan 2026; recurrence-expansion + presigned-upload patterns researched live (see § 15).

## § 0 — Context Summary

- **Story:** F2-S8 `vitalia-fase2-lisa-doctores` (ruta usuario = `lisa/staff`; entidad dominio = `doctor`).
- **Architect run on:** 2026-05-31 (`date -u`).
- **ADR-vitalia-004 citation (MANDATORY):** este arch sigue las **9 secciones** del patron cementado en `vitalia/docs/architecture/ADR-vitalia-004-shell-feature-architecture.md § 3` verbatim: (1) Routing route-group `(shell-organism)/lisa/staff/...`; (2) FSD-Lite `features/lisa/components/staff/`; (3) Client root `LisaStaffView.tsx`; (4) React Query + Zustand split; (5) RHF + Zod autosave 600ms (sin boton Guardar); (6) BE DDD Inside-Out + `PhiRepositoryBase` dual filter; (7) Migrations idempotent raw SQL; (8) Telemetria `vitalia_growth_studio_event`; (9) Tests 4-capa. **`adr_004_compliance: full`** — una sub-decision documentada (N3-dynamic = variante runtime de N3-static SubSubTabsBar, no divergencia del patron; ver § Architecture Decisions D-1).
- **Modules touched:** `clinics` (backend, EXTEND) · `features/lisa` (frontend, EXTEND) · `components/shared/shell-organism` (1 componente nuevo `EntitySubNavBar`) · consume engine `luana-core-assets` + `luana-core-scheduling`. NO toca `core/luana-core-*/src/`.
- **Surface -> builder -> auditor mapping** (PM/dev-team spawn):

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/clinics/{domain,infrastructure,application,api}/` | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| `vitalia/backend/src/modules/vitalia/clinics/application/bio_generation_service.py` (bio-gen determinista) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| `vitalia/backend/alembic/versions/036_*.py` (migration) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| `vitalia/frontend/src/features/lisa/components/staff/**` + `app/.../lisa/staff/**` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/components/shared/shell-organism/EntitySubNavBar.tsx` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |

- **Skills consulted (decision taken from each):**
  - `backend-expert` — Inside-Out DDD layering; `clinics` es modulo dueno del dato doctor; nuevo `vitalia_doctors` table dentro de `clinics`. SQLA 2.0 async, response_model mandatory.
  - `frontend-expert` — FSD-Lite `features/lisa/components/staff/`; Server-First page + client root view; React Query SSoT data, Zustand UI-only.
  - `brand-expert` — bio-gen consume voz de marca (`PersonalityProfile.system_instruction` como anchor de tono) pero NO escribe en aggregates brand; es servicio determinista que produce texto a partir de material aportado. NO toca `brand/domain`.
  - `vitalia-design-system` (FE builder lo carga) — shell-organism wrapper + SubSubTabsBar precedent + tokens agent-lisa.
  - `copilot-expert` / `sales-agent-expert` — **consultados para DESCARTAR R23**: bio-gen NO es un runtime agentic (no LangGraph node, no copilot/sales_agent surface). Es un servicio brand-BE que puede llamar 1 LLM single-shot (extractive). Vive en `clinics/application/`, NO en `copilot/` ni `sales_agent/`. **No dispara R23 -> Sonnet-eligible.** (ver § Architecture Decisions D-4).
- **CONTEXT-BRIEF source:** ausente (no brief). Self-ran greps (Path B) — ver § Existing Systems Audit.
- **capability YAML files affected (post-merge F.3):** `vitalia/docs/product/capabilities/clinics/lisa.doctores.yaml` (NEW) + lineage note en change_log (sucede a `clinics/clinics-brand-extension.yaml` deprecated + consume `booking/prepaid-booking-advisory-locks.yaml`). `modules/clinics.md` narrative update si existe.
- **Architecture gates que deben seguir verdes:** `test_phi_dual_filter.py`, `test_audit_log_sync_write.py`, `test_audit_log_row_per_phi_endpoint.py`, `test_response_model_required.py`, `test_pgcrypto_phi_columns.py`, `test_growth_studio_event_no_phi.py`, `test_no_phi_in_url_params.py`, `test_migrations_idempotent.py`, `test_clinics_domain_no_engine_imports.py`, `test_vitalia_no_query_without_tenant_filter.py` (BE) · `test_fsd_boundaries.test.ts`, `test_no_cross_feature_imports.test.ts`, `test-agent-subsubtabs-ssot.test.ts`, `test-ribbon-no-shadcn-tabs.test.ts`, `test_server_first.test.ts`, `test_no_hardcoded_subtab_keys.test.ts`, `test_no_voseo_in_copy.test.ts`, `test_phi_pii_components_used.test.ts` (FE).

---

## § Prior art audit (anti-duplication-refining)

Scan ejecutado per `.claude/rules/anti-duplication-refining.md` + `.claude/rules/anti-duplication.md`. Cross-brand (vitalia propio + comunify + core) + cross-module.

| Sistema candidato | Existe en | Decision |
|---|---|---|
| PHI dual-filter repo base | `vitalia/.../\_shared/repositories/phi_repository.py::PhiRepositoryBase` | **EXTEND** — `DoctorRepository` hereda |
| Audit log sync write | `vitalia/.../\_shared/repositories/audit_log_repository.py::AuditLogRepository` | **CONSUME** — sin recrear |
| RBAC decorator | `vitalia/.../\_shared/auth/rbac.py::require_phi_access` + `require_brand_owner_access` | **CONSUME** (admin_clinic gate) |
| pgcrypto KEK | `vitalia/.../\_shared/encryption/kek_client.py::KEKClient` | **CONSUME** — pgp_sym_encrypt en columnas sensibles |
| PHI masking (DNI/email/phone/name) | `vitalia/.../\_shared/phi_masking.py` | **CONSUME** — list + public serializer |
| Telemetria growth_studio | `vitalia/.../\_shared/telemetry/growth_studio_emitter.py` + `file_size_bucket.py` | **CONSUME** |
| Storage R2 | `core/luana-core-assets/.../storage/r2.py::R2StorageStrategy` + `assets_service.AssetsService.upload_asset` | **CONSUME via proxy upload** (ver D-3 — presign NO existe) |
| Recurrence expansion | **NINGUNO** en engine (commercial-calendar es calendario de marketing, no RRULE) | **NEW brand-local** via `python-dateutil.rrule` (ver D-2) |
| Doctor profile table | **NINGUNO** (`vitalia_doctor_extensions` solo guarda extensiones medicas con `doctor_id` colgante sin tabla padre) | **NEW** `vitalia_doctors` table en `clinics` |
| SubSubTabsBar N3 | `vitalia/.../shell-organism/SubSubTabsBar.tsx` (static catalog-driven) | **NEW variante** `EntitySubNavBar` (dynamic entity) — ver D-1 |
| Scheduling availability/slots | `core/luana-core-scheduling` + `vitalia/.../scheduling/` (`agenda_slot`, `create_appointment_service`) | **CONSUME** — materializa availability hacia scheduling |

**Cross-brand mirror check:** comunify no tiene equivalente staff/doctor (creator economy). nicolify snapshot frozen. No mirror. No lift required ahora (clinic/doctor son brand-local salud; si 2da brand salud aparece -> promotion EP futuro, flag en cap change_log).

---

## § Existing systems audit (NO NEW LAYER rule)

### Source of evidence
- [x] Self-run greps (Path B — no CONTEXT-BRIEF)

### Audit cross-module ejecutado
```bash
grep -rn "__tablename__.*doctor"  core/luana-core-scheduling/src vitalia/backend/src   # -> solo vitalia_doctor_extensions (extension, no perfil)
grep -rn "presign|generate_presigned" core/luana-core-assets/src                        # -> 0 resultados
grep -rln "recurr|rrule|biweekly" core/luana-core-commercial-calendar/src               # -> 0 (es calendario marketing)
grep -c 'name = "python-dateutil"' uv.lock                                              # -> 7 (disponible)
```

### Sistemas existentes encontrados (resumen)
| Sistema | Path | Estado | Decision |
|---|---|---|---|
| Storage proxy upload | `luana_core_assets.AssetsService.upload_asset` (multipart `POST /upload`) | active | **EXTEND-consume** (proxy, no presign) |
| Presigned upload | — | **no existe** | **NEW** brand-thin endpoint que usa proxy upload (D-3) |
| Recurrence engine | — | **no existe** | **NEW** brand-local `AvailabilityProjectionService` (dateutil.rrule) (D-2) |
| Doctor profile | `vitalia_doctor_extensions` (extension solo) | partial | **NEW** `vitalia_doctors` (D-5) |
| N3-static nav | `SubSubTabsBar.tsx` | active | **NEW** sibling `EntitySubNavBar` (D-1) |

### Decision por sistema -> ver § Architecture Decisions (D-1..D-6).

---

## § Integration design (CONN — anti-orphan)

**Home capability:** `lisa.doctores` (zona Agentes -> Lisa). El feature NO es isla — cumple las 4 contenciones:

- **C — Consumed:** los doctores creados son consumidos por (a) `scheduling` form "crear cita" de Valeria/Mateo (availability materializada), (b) endpoint publico `/api/public/clinic/{slug}/doctors` que alimenta landing (story futura `lisa-landing-public`), (c) bio publica consumida por sales_agent (campo `bio_public` leido en knowledge build).
- **O — On the map:** vive en cap YAML `vitalia/docs/product/capabilities/clinics/lisa.doctores.yaml` (zona derivada de SYSTEM-MAP: Agentes->Lisa).
- **N — Navigable:** reachability path concreto: `Ribbon[Lisa] -> SubTabsBar[Staff] (lisa/staff) -> StaffCard "Ver perfil" -> lisa/staff/[doctor-id]/perfil`. N3-dynamic `EntitySubNavBar` da navegacion entre Perfil/Horarios/Servicios. Deep-link + back/forward verificados por Playwright (SC-1c).
- **N — Notarized/registered:**
  - Backend: `doctors_router` registrado en `vitalia/backend/src/main.py` via `app.include_router(doctors_router, prefix="/api/v1/vitalia/clinics/doctors")` + `public_doctors_router` via `app.include_router(public_doctors_router, prefix="/api/public/clinic")` + `assets_proxy_router` via `app.include_router(assets_proxy_router, prefix="/api/v1/vitalia/assets")`.
  - Frontend: ruta `lisa/staff` en `AGENT_SUBTABS[lisa]` (whitelist) — verificar/agregar entry "staff". `AGENT_SUBSUBTABS["lisa.staff"]` NO se declara (N3-dynamic NO usa catalog estatico — `EntitySubNavBar` se renderiza desde la ruta `[doctor-id]`). El placeholder `SubTabContent.PLACEHOLDER_MAP[lisa.staff]` se reemplaza por sentinel "moved to dedicated route".

**Registration points (tickets owners):**
- `T-BE-1` registra `doctors_router` + `T-BE-7` registra `public_doctors_router` + `assets_proxy_router` en `main.py`.
- `T-FE-1` reemplaza placeholder + asegura `staff` en `AGENT_SUBTABS[lisa]`.

---

## § Architecture Decisions (resuelve los 4 escalados + 2 emergentes)

### D-1 — N3-dynamic entity nav -> `EntitySubNavBar` (componente nuevo, NO divergencia ADR-004)

**Decision: BUILD el componente generico `EntitySubNavBar` en `components/shared/shell-organism/` en ESTA story** (es el hogar reachable; sin el la navegacion del workspace no existe). Es un **sibling** de `SubSubTabsBar` — NO lo modifica ni lo reemplaza.

- `SubSubTabsBar` (existente) = N3-**static**: pills derivadas de catalog `AGENT_SUBSUBTABS["agent.subtab"]`, URL segment [3], todas siempre habilitadas. Sirve para `lisa/marca` (identidad/voz/presencia).
- `EntitySubNavBar` (nuevo) = N3-**dynamic**: `[raiz "‹ Staff"] | [avatar+nombre entidad] | [hojas Perfil·Horarios·Servicios]`. La entidad es dinamica (`[doctor-id]`), las hojas se habilitan solo dentro de un integrante (en el directorio estan disabled opacity .45). Sticky full-width, mismo tratamiento visual (pills, activo = fondo sutil agent-lisa).

**Props contract** (generico, cross-agent reusable):
```ts
interface EntitySubNavBarProps {
  rootHref: string;            // "/{tenantId}/lisa/staff"
  rootLabel: string;           // "Staff"
  entity: { id: string; name: string; avatarUrl?: string } | null; // null en directorio -> hojas disabled
  leaves: ReadonlyArray<{ slug: string; label: string; icon: string }>; // Perfil·Horarios·Servicios
  basePath: string;            // "/{tenantId}/lisa/staff/{doctor-id}"
  activeLeaf: string | null;   // derivado de URL
}
```
- WAI-ARIA: `nav role="tablist"`, roving tabindex, Arrow nav (copia patron de `SubSubTabsBar`). Disabled leaves: `aria-disabled=true`, `tabIndex=-1`, no clickeables.
- Renderiza dentro de `StaffWorkspaceShell` (layout de `[doctor-id]`) + en el directorio (`StaffDirectoryView` lo monta con `entity=null`).

**ADR addendum REQUERIDO (flag, NO build aca):** `ADR-vitalia-004 § 3.1.1` debe documentar `EntitySubNavBar` como patron N3-dynamic para workspaces de entidad (pacientes Mateo, leads Adrian). **Owner del addendum: `/pm-vitalia` en F.3 al merge.** Ticket `T-FE-2` produce el componente; el addendum es doc post-merge (no bloquea build). Esto mantiene `adr_004_compliance: full` (el componente respeta routing real por hojas, NO usa Shadcn `<Tabs>` internas).

### D-2 — Availability blocks + recurrence: `commercial-calendar` NO sirve -> NEW brand-local con `dateutil.rrule`

**Hallazgo critico (corrige premisa del spec):** la business rule `availability-projection-via-engine` asume que `luana-core-commercial-calendar` expande recurrencia. **NO lo hace** — es un calendario de eventos de marketing (feriados, campanas, cyber) indexado por semana ISO, sin RRULE/weekly/biweekly. `grep -rln "recurr|rrule|biweekly" core/luana-core-commercial-calendar/src` -> 0.

**Decision: NEW servicio brand-local `AvailabilityProjectionService` en `clinics/application/`** que usa `python-dateutil.rrule` (ya en `uv.lock` 2.9.0). NO se reimplementa "recurrencia from scratch" — `dateutil.rrule` ES la libreria de recurrencia estandar (RFC 5545 RRULE). NO viola anti-duplication: no existe abstraccion engine que cubra esto, y construir un nuevo paquete core para un solo consumidor brand seria sobre-ingenieria (KISS).

- **Domain `AvailabilityBlock`** (dataclass frozen): `kind ∈ {recurrent, one_off}`; recurrent -> `day_of_week`, `start_time`, `end_time`, `freq ∈ {weekly, biweekly}`, `end_condition ∈ {end_date(date) | occurrences(int) | open_ended(bool)}`; one_off -> `specific_date`, `start_time`, `end_time`.
- **Domain validation `recurrence-end-condition-required`:** recurrent SIN end_condition explicita -> `ValueError`. `open_ended` materializa horizonte rolling 90d (re-proyeccion por worker = follow-up fuera de scope MVP; documentado).
- **Service** expande el bloque a fechas via `dateutil.rrule(WEEKLY, interval=1|2, byweekday=..., until=end_date | count=occurrences)` -> materializa `vitalia_availability_slots` rows hacia scheduling (slot granularity = duracion de cita del tenant, default 30min).
- **Mutabilidad** (`availability-block-mutable`): PATCH/DELETE reproyectan SOLO futuro (`slot_date >= current_date`). `delete-block-preserves-confirmed-appointments`: DELETE retira slots futuros SIN cita; slots con cita confirmada se preservan. Pasado nunca se toca.

> **Anti-duplication note:** `availability-projection-via-engine` business rule en cap YAML debe **corregirse** post-merge: proyeccion brand-local via `dateutil.rrule`, NO commercial-calendar. Flag para `/pm-vitalia` F.3.

### D-3 — Assets/R2: presigned NO existe -> CONSUME proxy upload (`AssetsService.upload_asset`)

**Hallazgo:** `core/luana-core-assets/storage/r2.py::R2StorageStrategy` NO tiene `generate_presigned_upload`; `grep presign core/luana-core-assets/src` -> 0. La unica via de upload del engine es `AssetsService.upload_asset` (multipart proxied: browser -> `POST /api/v1/assets/upload` -> backend -> R2 via boto3 `put_object`). El spec asume "presigned POST direct browser->R2" — **ese patron no existe en el engine**.

**Decision: CONSUME el proxy upload existente** via router brand-thin `assets_proxy_router` montado en vitalia (copia wiring de `nicolify/backend/src/main.py` que monta `assets_gallery.router`). Avatar + bio-attachments suben por `POST /api/v1/vitalia/assets/upload` (multipart, max 10MB enforced brand-side, content-type allow-list image/* avatar, PDF/JPG/PNG/DOCX credential_doc). Backend forwarda a `AssetsService.upload_asset` -> R2. FE recibe `{key, url}` -> `PATCH doctor {avatar_key}`.

- **Por que NO presign:** construir presigned-POST requiere agregar `generate_presigned_upload` a `R2StorageStrategy` (engine change) -> `/pm-luana` promotion proposal. Out-of-scope. El proxy upload es funcionalmente equivalente para MVP (10MB cap). **Flag:** si volumen futuro lo amerita, lift presign a engine via `/pm-luana`.
- **Provisioning R2 (Chris manual action):** generar R2 S3 credentials (Cloudflare -> R2 -> Manage R2 API Tokens -> S3 credentials), crear bucket `vitalia-assets` + CORS, cargar `R2_*` env vars en `.env.dev` (gitignored). El `cfat_` token es CF API (wrangler), NO sirve como llave S3 boto3. **Tickets de codigo/tests proceden con storage mockeado** (`StorageStrategy` swappable -> LocalStorageStrategy en test); cred viva = Chris manual action (ticket `T-BE-7` marca `chris_manual_action`).
- **Rotacion:** el `cfat_` pegado en chat plano debe rotarse tras provisioning (flag seguridad).

### D-4 — bio-gen: servicio determinista BE, NO agentic (R23 NO aplica)

**Decision: `BioGenerationService` vive en `clinics/application/`, owner `builder-backend` (Sonnet).** Consultados `copilot-expert` + `sales-agent-expert`: el servicio NO crea LangGraph node, NO toca `copilot/` ni `sales_agent/` surface, NO es runtime conversacional. Es generacion single-shot extractiva: recibe material aportado (notas pegadas + metadatos archivos + links), produce 3 secciones editables (Resumen · Formacion · Enfoque) **solo a partir del material** (`bio-generated-from-inputs-no-invent`). Puede llamar 1 LLM single-shot via router LLM compartido (`luana_core_llm.router`) con prompt extractivo + guardrail "no inventes". NO eval-goldens, NO prompt-cache slots, NO state machine. **No dispara R23 -> Sonnet-eligible.**

- Guardrail anti-alucinacion: prompt instruye "usa SOLO el material provisto; si falta info, deja la seccion vacia con placeholder, no inventes". Output editable (contenteditable) -> human-in-the-loop.
- Tono: prompt puede leer `PersonalityProfile.system_instruction` del tenant como anchor de voz (consume `shared/links/ports/brand` si existe, o pasa tono como string) — NO escribe en brand aggregates.
- Resiliencia: LLM call con timeout + fallback (`tessl__graceful-degradation`); si falla, devuelve secciones vacias + mensaje "No pudimos generar la bio, intenta de nuevo" (no rompe autosave del resto del perfil).
- **NO PHI:** notas/archivos de bio son material promocional (diploma, CV) — NO datos clinicos de paciente. El doctor profile SI tiene PII (DNI, credencial, contacto) -> dual filter + pgcrypto aplican al perfil, no a la bio.

### D-5 — Doctor profile table: NEW `vitalia_doctors` en `clinics`

**Hallazgo:** no existe tabla de perfil de doctor. `vitalia_doctor_extensions` solo guarda extensiones medicas (specialty, treatment_room) con `doctor_id` colgante sin tabla padre. **Decision: NEW `vitalia_doctors`** (perfil staff) en modulo `clinics` (dueno del dato). `vitalia_doctor_extensions` se mantiene (consumido por booking/advisory-locks) — su `doctor_id` referenciara `vitalia_doctors.id` (FK logica, resuelta en application, sin JOIN cross-module hard).

Campos perfil: `id, tenant_id, clinic_id, first_name, last_name, dni(pgcrypto), email(pgcrypto), phone(pgcrypto), specialty, credential(pgcrypto), credential_country, years_experience, languages(jsonb), bio_inputs_notes, bio_links(jsonb), bio_public(jsonb), avatar_key, visible_en_landing, active, created_at, updated_at, deleted_at`. Unique `(tenant_id, dni)`.

### D-6 — Split recommendation (story LARGE 7-9d)

La story genera **3 grupos coherentes** + provisioning. Total tickets = **11** (ver `06-tickets.yaml`). **Recomendacion: NO split en N stories** — los 11 tickets forman un DAG cohesivo con dependencias fuertes (FE depende de BE endpoints; horarios depende de doctor CRUD). Splitear romperia el closure gate (WIP cap module-scoped) y forzaria stories parciales no-shippables (directorio sin workspace = isla). **Se mantiene como UNA story** con 11 tickets, ejecucion autonoma secuencial+paralela segun DAG. Si `/dev-team` detecta sobre-presupuesto, puede pausar y `defer_audit` el resto con ratificacion — pero el ready package entrega los 11 completos (no truncado).

---

## § 1-§ 8 Backend contract -> ver `03-arch-be.md`
## § FE contract -> ver `03-arch-fe.md`

---

## § 9 — Migration Notes

- Migration `036_f2_s8_vitalia_lisa_staff.py` en `vitalia/backend/alembic/versions/` (sigue 035, down_revision='035').
- Raw SQL idempotente: `CREATE TABLE IF NOT EXISTS vitalia_doctors (...)`, `CREATE TABLE IF NOT EXISTS vitalia_availability_blocks (...)`, `CREATE TABLE IF NOT EXISTS vitalia_availability_slots (...)`, `CREATE INDEX IF NOT EXISTS` (tenant_id, clinic_id, doctor_id), `CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_doctors_tenant_dni`.
- pgcrypto: columnas sensibles almacenan ciphertext (`BYTEA`); insert usa `pgp_sym_encrypt(:value,:key)`, read usa `pgp_sym_decrypt(col,:key)` — patron existente (`channel_sync_state.oauth_token_encrypted`). Extension `pgcrypto` ya presente (gate `test_pgcrypto_phi_columns.py`).
- NUNCA `op.create_table()` / `sa.Enum(create_type=True)`. Enums via String + validacion domain (preferido).
- FK `vitalia_availability_slots.doctor_id -> vitalia_doctors.id ON DELETE CASCADE`.
- Test idempotency: clone DB workflow (`docs/domains/migrations.md`) — aplicar 2x = no-op.

## § 9.5 — Tests audit (default flip)

- [x] **No aplica — CONTRACT no flipea defaults side-effect.** Esta story no toca feature flags. No hay flip de call-path con side-effect.

## § 10 — File Structure -> ver `03-arch-be.md § File Structure` + `03-arch-fe.md § File Structure`

## § 11 — Cross-Cutting Concerns

- **Tenant isolation + dual filter:** `DoctorRepository`/`AvailabilityBlockRepository` heredan `PhiRepositoryBase`, `validate_dual_filter(tenant_id, clinic_id)` en TODA query (incl. get_by_id). Cross-tenant -> 404 generico + audit `cross_tenant_attempt`.
- **Currency:** `servicios-pricing-currency-tenant-locale` (futuro). Esta story NO construye Servicios funcional -> currency diferida. DTO servicios futuro incluira `currency: str | None` desde `tenant_locale`.
- **Master data:** `DateTime(timezone=True)`, store UTC, slots en UTC, display via `useTenantLocale()`/`formatTenantDate*()`. Horarios FE formato 24h con check "Mostrar 24 horas" (base 07:00–21:00).
- **Spanish neutro LatAm:** microcopy table del spec § Microcopy es authoritative. Sin voseo. Gate `test_no_voseo_in_copy.test.ts`.
- **PII/PHI:** `response_model=` allowlist en todo endpoint. Listas + publico usan `phi_masking` (mask_dni/email/phone). Endpoint publico = allow-list explicita (NO deny-list) — channel guard arch test.
- **Native-first dev:** `cd vitalia/backend && ${WS}/.venv/bin/{ruff,pytest}` · `cd vitalia/frontend && npx {tsc,eslint,vitest,playwright}`. NUNCA docker exec. Ports BE 8002 / FE 3002.

## § 12 — Architecture Fitness Impact

Gates que corren (todos verdes; allowlists shrink-only):
- BE: `test_phi_dual_filter.py`, `test_audit_log_sync_write.py` + `test_audit_log_row_per_phi_endpoint.py`, `test_response_model_required.py`, `test_pgcrypto_phi_columns.py`, `test_growth_studio_event_no_phi.py`, `test_no_phi_in_url_params.py`, `test_migrations_idempotent.py`, `test_clinics_domain_no_engine_imports.py`, `test_vitalia_no_query_without_tenant_filter.py`.
- **Nuevo arch test (este story):** `test_public_doctors_allowlist.py` — channel guard: serializer publico NO puede emitir campos PHI/PII aunque el modelo los tenga (allow-list enforce). EXTEND, no shrink.
- FE: `test_fsd_boundaries.test.ts`, `test_no_cross_feature_imports.test.ts`, `test-ribbon-no-shadcn-tabs.test.ts`, `test_server_first.test.ts`, `test_no_voseo_in_copy.test.ts`, `test_phi_pii_components_used.test.ts`, `test-agent-subsubtabs-ssot.test.ts`.
- Allowlist updates: ninguna que crezca. `EntitySubNavBar` es componente nuevo legitimo.

## § 13 — capability YAML + modules MD updates (post 2026-05)

- NEW `vitalia/docs/product/capabilities/clinics/lisa.doctores.yaml` (schema ADR-004 § 5 + protocol v3.2: `scenarios[]` SC-1..SC-11 + `access` (RBAC admin_clinic) + `business_rules` (16 reglas del spec)). change_log: lineage (sucede `clinics-brand-extension` deprecated, consume `prepaid-booking-advisory-locks`) + correccion `availability-projection-via-engine` -> brand-local dateutil.
- `modules/clinics.md` narrative update si existe.
- Headers `# cap: clinics.lisa.doctores` en todo archivo Python nuevo; `// cap: clinics.lisa.doctores` en TS/TSX nuevo (lineas 1-3).

## § 14 — Test Surfaces (TDD RED-first) -> ver `04-validators.yaml § test_construction_plan`

Resumen capas:
- BE: domain (`AvailabilityBlock` validation RED) -> infrastructure (`DoctorRepository` dual-filter RED) -> application (`credential_validator`, `AvailabilityProjectionService`, `BioGenerationService` RED) -> api/E2E (cross-tenant, dni-race, response_model).
- FE: hook (`useStaffList`, `useDoctor`, `useAvailabilityBlocks`) -> component (`StaffCard`, `EntitySubNavBar`, `AvailabilityCalendar`, `BioRepoInputs`) -> store (UI store).
- E2E Playwright: SC-1, SC-1b, SC-1c, SC-1d, SC-2, SC-3, SC-3b, SC-4, SC-6, SC-7, SC-8, SC-9, SC-10, SC-11.
- Visual goldens: directorio + perfil + horarios × light/dark = 6 PNGs + servicios-pendiente 1 golden.

## § 15 — Research Notes (date-aware)

- **`python-dateutil.rrule` (RFC 5545 RRULE)** — `https://dateutil.readthedocs.io/en/stable/rrule.html` accessed 2026-05-31. Version 2.9.0.post0 (en `uv.lock`). Takeaway: `rrule(WEEKLY, interval=2, byweekday=[MO,WE,FR], until=date | count=N)` cubre weekly/biweekly + end_date/occurrences/open-ended nativamente. Elegido sobre reimplementar recurrencia o agregar paquete core (KISS, single brand consumer). dateutil rrule API estable desde 2015, sin riesgo de confabulacion.
- **Cloudflare R2 presigned POST** — `https://developers.cloudflare.com/r2/api/s3/presigned-urls/` accessed 2026-05-31. R2 soporta presigned via boto3 `generate_presigned_post`, PERO el engine `luana-core-assets` NO lo implementa (solo `put_object` proxy). Decision D-3: consumir proxy upload existente, diferir presign a engine lift. Researched live — Opus 4.8 cutoff Jan 2026; estado del engine code verificado por grep, no por memoria.
- **react-big-calendar vs FullCalendar vs custom grid** — ver `03-arch-fe.md § Calendar decision`. Recomendacion: **custom week grid + `@dnd-kit`** (drag-to-create) por columna angosta + control fino del popover de recurrencia + evitar peso de FullCalendar/react-big-calendar. `@dnd-kit` accessed `https://dndkit.com/` 2026-05-31.
- **Next.js 16 App Router async params** — `https://nextjs.org/docs/app/api-reference/file-conventions/page` accessed 2026-05-31. `params`/`searchParams` son `Promise<...>` (Next 16). Patron ya cementado en ADR-004 § 3.1.

## § 16 — Open Questions for PM

1. **ADR-004 § 3.1.1 addendum (`EntitySubNavBar`):** owner = `/pm-vitalia` F.3. ¿Addendum inline o ADR-vitalia-005 dedicado? Propuesta architect: addendum inline (KISS).
2. **`availability-projection-via-engine` business rule correccion:** proyeccion brand-local (`dateutil.rrule`), NO commercial-calendar. ¿`/pm-vitalia` corrige el wording al merge? (Architect: si — premisa de refining era erronea.)
3. **Presign diferido:** ¿`/pm-luana` proposal para lift `generate_presigned_upload` post-MVP, o proxy upload permanente? (Architect: proxy suficiente para volumen actual.)
4. **`open_ended` recurrence horizon:** MVP materializa 90d rolling. ¿Worker de re-proyeccion como follow-up, o 90d suficiente? (Architect: 90d MVP, worker follow-up.)
5. **R2 S3 creds (Chris manual):** generar credenciales S3 + bucket + CORS antes de E2E live. Ticket `T-BE-7` lo marca `chris_manual_action`. Code/tests proceden con storage mockeado.
