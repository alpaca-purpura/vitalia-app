# 01-spec.md — vitalia-adopt-luana-core-iam

> Story: adopta engine `luana-core-iam` + brand-extension `vitalia_clinics` + Streamlit admin per-brand
> Brand: vitalia (Salud + Bienestar — HIPAA-lite overlay)
> State: refining
> Spec author: /pm-vitalia (autonomous E2E, /po-ux pattern inlined)
> Ratified: 2026-05-19 (Chris pre-authorized cadena completa)

## § 1 — Persona y objetivos

### Persona única: Chris (super-admin platform owner)

- Acceso exclusivo (NO clientes finales)
- Auth: bcrypt single super-admin password (`VITALIA_ADMIN_PASSWORD_HASH` env var)
- Necesita: crear tenants (clínicas reales), asignar usuarios a tenants con roles, banear usuarios, suspender tenants, crear sub-units brand-specific (clinics)
- Contexto: 1ª brand de las 10 universos donde se cementa el patrón canónico admin+IAM. Errores se replican a saasora/inmoflow/retailly/fixia/guestly/fitflow.

### Job-to-be-done

> "Como super-admin Vitalia necesito CRUD de tenants/users/clinics desde un panel
> simple (Streamlit puerto 8502) que consume el engine IAM compartido, registra
> audit log sync por cada mutación, y respeta dual filter HIPAA (tenant+clinic) en
> queries PHI — sin escribir SQL crudo ni recrear tablas que el engine ya define."

## § 2 — Scope (in / out)

### IN

- Migration nueva (#022) que crea tablas engine: `users`, `tenants`, `user_tenants`
- Migration nueva (#023) que crea tabla brand-extension: `vitalia_clinics` (FK a `tenants.id`)
- Aplicar `alembic upgrade head` (001 → 023) sobre `vitalia_dev`
- REWRITE `vitalia/backend/src/modules/vitalia/admin/modules/tenants.py` consumiendo `luana_core_iam.TenantRepository`
- REWRITE `vitalia/backend/src/modules/vitalia/admin/modules/users.py` consumiendo `luana_core_iam.{UserRepository, UserTenantRepository}`
- NEW `vitalia/backend/src/modules/vitalia/admin/modules/clinics.py` consumiendo brand-local `ClinicRepository`
- NEW `vitalia/backend/src/modules/vitalia/clinics/` (domain + infrastructure + application layers, DDD)
- NEW service `vitalia-admin` en `vitalia/docker-compose.dev.yml` exposing port 8502
- NEW Makefile target `dev-vitalia-admin`
- Comment en `vitalia/.env.dev.template` re single-quote requirement
- Audit log sync write antes return en TODA mutación (HIPAA-lite §audit_log rule)
- HIPAA dual filter `(tenant_id, clinic_id)` decorator helper `@require_clinic_access`
- Playwright admin-smoke project + 5 spec files
- Tests pytest cubriendo SC-01..SC-14 backend + integration

### OUT

- Clerk auth para admin (Decision D5: bcrypt only, admin NO es flow customer-facing)
- Multi-super-admin (D5: Chris only, single password)
- LLM consumption reports (defer story posterior)
- Billing manual payments page (defer story posterior)
- vitalia_clinics admin para editar PHI directamente (admin solo CRUD identity fields)
- Promotion EP-19 `TenantSubUnit` (defer hasta 2da brand replique patrón)

## § 3 — Acceptance criteria (Gherkin AI-resistant, 14 scenarios)

### SC-01 — Admin login con bcrypt password OK → dashboard

```gherkin
Given el admin Streamlit está corriendo en http://127.0.0.1:8502
  And VITALIA_ADMIN_PASSWORD_HASH está set en el container env
  And la password en plain text es "7BFinws7Irux4wUGAzQ4" (matching el hash)
When Chris navega a http://127.0.0.1:8502
  And ingresa la password en el campo de login
  And presiona el botón "Ingresar"
Then el sistema verifica bcrypt password contra el hash
  And la sesión queda autenticada en st.session_state["admin_authenticated"] = True
  And el dashboard renderiza con sidebar: Tenants / Users / Clínicas / Salir
  And NO se ejecuta query a vitalia_clinics (eso es contenido sidebar, post-auth)
```

### SC-02 — Admin crea tenant nuevo

```gherkin
Given Chris está autenticado en admin
  And navega a página "Tenants"
  And tab "Crear nuevo tenant" está activa
When ingresa name="Clínica Aurora Dental"
  And slug="aurora-dental-ar"
  And plan_tier="clinic"
  And country="AR"
  And presiona "Crear tenant"
Then el sistema invoca TenantRepository.create(...) del engine luana_core_iam
  And se ejecuta INSERT INTO tenants (id, name, slug, plan_tier, country, is_active=true, created_at) ...
  And se escribe sync row en vitalia_audit_log con action="tenant.create", resource_type="tenant"
  And UI muestra success "Tenant 'Clínica Aurora Dental' creado correctamente"
  And listado de tenants en tab "Listado" muestra el nuevo registro
```

### SC-03 — Admin lista tenants

```gherkin
Given existen 3 tenants en la tabla tenants
When Chris navega a página "Tenants" → tab "Listado"
Then se ejecuta SELECT * FROM tenants ORDER BY created_at DESC
  And UI renderiza tabla con columnas: ID (short UUID), Nombre, Slug, Plan, País, Estado (activo/suspendido), Creado
  And cada row tiene botón "Editar" y toggle "Activo/Suspendido"
  And NO se ejecuta query a vitalia_clinics (los tenants no se cargan con clinics inline — eso es página clínicas)
```

### SC-04 — Admin crea user + asigna a tenant

```gherkin
Given Chris está en página "Users" → tab "Crear nuevo user"
  And existe tenant "Clínica Aurora Dental" (id=T1)
When ingresa email="director@aurora-dental.ar"
  And full_name="Dra. María Vega"
  And selecciona tenant dropdown="Clínica Aurora Dental"
  And selecciona role="admin"
  And presiona "Crear usuario y asignar"
Then se ejecuta INSERT INTO users (id, email, full_name, is_active=true) ...
  And se ejecuta INSERT INTO user_tenants (user_id, tenant_id, role, created_at) ...
  And se escribe row en vitalia_audit_log con action="user.create_and_link" payload_redacted={email_hash, tenant_id}
  And UI muestra success "Usuario 'Dra. María Vega' creado y asignado a 'Clínica Aurora Dental' con rol 'admin'"
```

### SC-05 — Admin lista users con role per tenant

```gherkin
Given existen 5 users con asignaciones a múltiples tenants
When Chris navega a página "Users" → tab "Listado"
Then se ejecuta SELECT con JOIN: users LEFT JOIN user_tenants LEFT JOIN tenants
  And UI renderiza tabla con columnas: ID, Email, Nombre, Tenants (lista "Aurora Dental (admin)", "Clinic Sur (doctor)"), Estado, Último login
  And cada row tiene botón "Editar" y toggle "Banear/Activar"
  And users sin tenant asignado aparecen con badge "Sin tenant"
```

### SC-06 — Admin banea user (toggle is_active=false)

```gherkin
Given Chris está en página "Users" → tab "Listado"
  And existe user "director@aurora-dental.ar" con is_active=true
When Chris presiona toggle "Banear" en el row del user
  And confirma en dialog "¿Banear usuario? Acción reversible."
Then se ejecuta UPDATE users SET is_active=false, updated_at=NOW() WHERE id=$user_id
  And se escribe row en vitalia_audit_log con action="user.ban" payload_redacted={user_id, reason="manual_admin_action"}
  And UI muestra row con badge "Baneado" en gris
  And próximo login del user retorna 403 (auth path checks is_active)
```

### SC-07 — Admin suspende tenant (toggle is_active=false)

```gherkin
Given Chris está en página "Tenants" → tab "Listado"
  And existe tenant "Clínica Aurora Dental" con is_active=true
When Chris presiona toggle "Suspender" en el row del tenant
  And confirma en dialog "¿Suspender tenant? Sus usuarios perderán acceso. Reversible."
Then se ejecuta UPDATE tenants SET is_active=false, updated_at=NOW() WHERE id=$tenant_id
  And se escribe row en vitalia_audit_log con action="tenant.suspend" payload_redacted={tenant_id}
  And UI muestra row con badge "Suspendido" en gris
  And todas las requests con X-Tenant-ID=$tenant_id retornan 403 a partir de ese momento
```

### SC-08 — Admin crea clinic asociada a tenant

```gherkin
Given Chris está en página "Clínicas" → tab "Crear nueva clínica"
  And existe tenant "Clínica Aurora Dental" (id=T1)
When ingresa name="Sede Centro"
  And selecciona tenant dropdown="Clínica Aurora Dental"
  And address="Av. Corrientes 1234, CABA"
  And timezone="America/Argentina/Buenos_Aires"
  And presiona "Crear clínica"
Then se ejecuta INSERT INTO vitalia_clinics (id, tenant_id=T1, name, address, timezone, is_active=true, created_at) ...
  And se escribe row en vitalia_audit_log con action="clinic.create" payload_redacted={clinic_id, tenant_id, name}
  And UI muestra success "Clínica 'Sede Centro' creada bajo tenant 'Clínica Aurora Dental'"
  And listado de clinics filtrado por tenant muestra la nueva
```

### SC-09 — User-tenant dropdown switch → re-fetch data filtrada

```gherkin
Given Chris está en página "Users" → tab "Listado"
  And dropdown "Filtrar por tenant" tiene 3 opciones: All / Tenant A / Tenant B
  And actualmente está seleccionado "All" (5 users visibles)
When Chris selecciona "Tenant A" en el dropdown
Then se ejecuta nueva query SELECT con WHERE user_tenants.tenant_id = $tenant_a_id
  And UI re-renderiza listado con SOLO los users asignados a Tenant A (2 visibles)
  And st.session_state["selected_tenant_filter"] = $tenant_a_id (persistente entre tabs)
```

### SC-10 — HIPAA cross-clinic query bloqueada

```gherkin
Given existe user U1 con asignación: tenant T1, clinic C1 (rol="doctor")
  And existe clínica C2 distinta de C1 (mismo tenant T1)
  And U1 está autenticado con session token válida
When U1 invoca endpoint GET /api/v1/vitalia/patients?clinic_id=$C2
Then el decorator @require_clinic_access(clinic_id=$C2) verifica user_tenants + clinics scope
  And detecta que U1 NO tiene asignación a clinic C2 (solo C1)
  And retorna HTTP 403 con body {"error": "Forbidden", "message": "Cross-clinic access denied"}
  And se escribe row en vitalia_audit_log con action="phi.access_denied" payload_redacted={user_id, attempted_clinic_id, reason="cross_clinic"}
  And NO se filtra ningún dato PHI en la response
```

### SC-11 — HIPAA dual filter query PHI

```gherkin
Given existen 100 patients distribuidos en T1/C1 (40) + T1/C2 (35) + T2/C3 (25)
  And user U1 está autenticado con scope tenant=T1, clinic=C1 (rol="doctor")
When U1 invoca endpoint GET /api/v1/vitalia/patients (sin query params extras)
Then el repositorio aplica dual filter: WHERE tenant_id=$T1 AND clinic_id=$C1
  And retorna SOLO los 40 patients de T1/C1 (no leak T1/C2 ni T2/C3)
  And arch fitness test test_phi_dual_filter.py enforces que TODA query a tablas PHI incluya ambos filters
  And se escribe row en vitalia_audit_log con action="phi.read.list" payload_redacted={user_id, tenant_id, clinic_id, count=40}
```

### SC-12 — Admin logout → session destroyed → redirect login

```gherkin
Given Chris está autenticado en admin Streamlit
  And st.session_state["admin_authenticated"] = True
When Chris presiona botón "Salir" en sidebar
Then st.session_state.clear() o explícito st.session_state["admin_authenticated"] = False
  And la página redirige a /admin (login form)
  And próxima request a cualquier página (tenants/users/clinics) muestra login form (no dashboard)
  And NO hay residual de session state ni cookies leak
```

### SC-13 — Phantom tables DELETED (cero queries SQL crudo residual)

```gherkin
Given el rewrite admin está completo (T-be-admin-rewrite + T-be-admin-deletion)
When ejecutamos grep en vitalia/backend/src/modules/vitalia/admin/
  And buscamos referencias SQL crudo a tablas phantom
Then grep "vitalia_user_profiles" en admin/modules/ retorna 0 hits
  And grep "vitalia_tenants" en admin/modules/ retorna 0 hits (canónica es "tenants" engine)
  And grep "session.execute(.*SELECT" en admin/modules/{tenants,users}.py retorna 0 hits
  And grep "session.execute(.*INSERT" en admin/modules/{tenants,users}.py retorna 0 hits
  And TODA query pasa por engine repositories (UserRepository/TenantRepository/UserTenantRepository)
  And el único módulo brand-specific permitido es admin/modules/clinics.py (consume brand-local ClinicRepository)
  And grep "vitalia_clinics" SÍ encuentra refs en modules/clinics.py + modules/vitalia/clinics/ (legítimo brand-extension)
```

### SC-14 — Migrations pending 002-023 aplicadas

```gherkin
Given DB vitalia_dev está en alembic revision 001_vitalia (estado pre-story)
  And existen migrations en código hasta 023_vitalia (post-story: 022 = engine IAM tables, 023 = vitalia_clinics)
When ejecutamos docker exec luana-dev-vitalia_backend_dev-1 alembic upgrade head
Then alembic aplica secuencialmente 002 → 003 → ... → 023
  And migration 014 (tenants_columns) ya no falla porque tenants table existe post-022
  And migration 023 crea vitalia_clinics con FK válida a tenants(id)
  And alembic current retorna "023_vitalia (head)"
  And SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' retorna ≥ 25 tablas
  And existen: users (engine), tenants (engine), user_tenants (engine), vitalia_clinics (brand-ext) + 21 tablas vitalia_* medical
```

## § 4 — Wireframes admin Streamlit (texto, port 8502)

### Login screen

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              Vitalia Admin — Acceso restringido           ║
║                                                           ║
║                  ┌───────────────────┐                    ║
║                  │ Contraseña        │                    ║
║                  │ ●●●●●●●●●●●●      │                    ║
║                  └───────────────────┘                    ║
║                                                           ║
║                  ┌───────────────────┐                    ║
║                  │     Ingresar      │                    ║
║                  └───────────────────┘                    ║
║                                                           ║
║  Versión: 0.3.0 · Engine luana-core-iam · Brand vitalia   ║
╚═══════════════════════════════════════════════════════════╝
```

### Dashboard post-login (sidebar layout)

```
┌──────────────────┬───────────────────────────────────────┐
│  Vitalia Admin   │  Tenants                              │
│                  │                                       │
│  → Tenants       │  [Listado] [Crear nuevo]              │
│    Users         │                                       │
│    Clínicas      │  ─────────────────────────────────────│
│                  │  ID    │ Nombre        │ Plan │ ⚙️    │
│  ─────────────   │  ─────────────────────────────────────│
│                  │  t1... │ Aurora Dental │ clin │ [...] │
│  Versión 0.3.0   │  t2... │ Sur SRL       │ solo │ [...] │
│  Salir           │  t3... │ Bienestar SA  │ mult │ [...] │
│                  │  ─────────────────────────────────────│
└──────────────────┴───────────────────────────────────────┘
```

### Tab "Crear nuevo tenant"

```
Crear nuevo tenant
─────────────────────────────────────
Nombre:       [Clínica Aurora Dental_____]
Slug:         [aurora-dental-ar___________]
Plan tier:    (•) solo_doctor  ( ) clinic  ( ) multi_site
País:         [AR ▾]
─────────────────────────────────────
              [Cancelar]  [Crear tenant]
```

### Tab "Listado users" con filtro por tenant

```
Users
─────────────────────────────────────
Filtrar por tenant: [Todos ▾]
─────────────────────────────────────
Email                        │ Nombre        │ Tenants                       │ Estado    │ ⚙️
─────────────────────────────────────────────────────────────────────────────────────────────
director@aurora-dental.ar    │ Dra. M. Vega  │ Aurora Dental (admin)         │ Activo    │ [Banear]
recepcion@sur.com.ar         │ Lic. R. Pérez │ Sur SRL (recepcionista)       │ Activo    │ [Banear]
test@bienestar.com           │ Test User     │ (sin tenant)                  │ Baneado   │ [Activar]
─────────────────────────────────────────────────────────────────────────────────────────────
```

## § 5 — Microcopy Spanish neutro

Tabla canónica de strings UI (Spanish neutro LatAm, NO voseo per `.claude/rules/spanish-text.md`):

| Contexto | String UI |
|---|---|
| Login title | "Vitalia Admin — Acceso restringido" |
| Login button | "Ingresar" |
| Login error | "Contraseña incorrecta. Intenta de nuevo." |
| Sidebar logout | "Salir" |
| Create tenant button | "Crear tenant" |
| Create tenant success | "Tenant '{name}' creado correctamente" |
| Create tenant error | "No se pudo crear el tenant: {reason}" |
| Ban user confirm | "¿Banear usuario? Acción reversible." |
| Ban user success | "Usuario '{email}' baneado." |
| Suspend tenant confirm | "¿Suspender tenant? Sus usuarios perderán acceso. Reversible." |
| Suspend tenant success | "Tenant '{name}' suspendido." |
| Empty tenants list | "Aún no existen tenants. Crea el primero en la pestaña 'Crear nuevo'." |
| Empty users list | "Aún no existen usuarios." |
| Empty clinics list (per tenant) | "Este tenant no tiene clínicas registradas." |
| Cross-clinic forbidden | "Acceso denegado: no tienes permiso sobre esta clínica." |
| Filter dropdown placeholder | "Filtrar por tenant" |
| Filter "all" option | "Todos" |

## § 6 — Estados visuales

| Estado | Comportamiento |
|---|---|
| Loading | `st.spinner("Cargando...")` mientras query DB |
| Empty | Mensaje claro + CTA (ver microcopy) |
| Error | `st.error("...")` con mensaje user-friendly + log estructurado al backend |
| Success | `st.success("...")` ephimerial (auto-fade no implementado, pero visible 2s) |
| Confirm dialog | `st.dialog(...)` con título + body + 2 botones (Cancelar / Confirmar) |
| Read-only badge | "Activo" (verde) / "Baneado"/"Suspendido" (gris) |

## § 7 — HIPAA-lite invariantes (refuerzo vitalia)

Por `vitalia/.claude/rules/hipaa-lite.md`, esta story refuerza:

1. **Audit log sync write**: TODA mutación (tenant/user/clinic create/update/ban/suspend) escribe row en `vitalia_audit_log` ANTES de retornar response success. NO async fire-forget.
2. **Dual filter en queries PHI**: el módulo `clinics/` introduce el patrón. Queries a tablas que en futuro contengan PHI (patients, treatments) DEBEN filtrar por `(tenant_id, clinic_id)` simultáneamente. Decorator `@require_clinic_access(clinic_id_from)` enforces.
3. **Sanitization en audit_log.payload_redacted**: NUNCA loguear PHI plaintext. Usar email hash, IDs, no nombres de pacientes/diagnósticos.
4. **NO PHI en URLs (GET query params)**: usar POST body. Aplica a futuros endpoints `/patients`, no a admin (admin no toca PHI directamente).
5. **RBAC strict para roles PHI**: solo roles `doctor`, `nurse`, `admin_clinic` ven PHI. Admin platform (Chris) ve identity fields, NO PHI (admin pages don't query patients/treatments).

## § 8 — Engine boundary (CRITICAL)

Esta story **NO toca** `core/luana-core-iam/src/`. Cero edits engine. Cero promotion proposal needed.

- Solo CONSUME engine via `from luana_core_iam.infrastructure.repositories import {UserRepository, TenantRepository, UserTenantRepository}`
- Migration 022 ejecuta DDL `CREATE TABLE users/tenants/user_tenants` matching engine ORM models (schema-mirror exception per `.claude/rules/backend-ddd.md`)
- Schema verbatim desde nicolify migration 001 (proven canonical, auditable)

## § 9 — Validation matrix preview (Phase B architect detalla)

Categories esperadas en `04-validators.yaml`:

| Category | Examples |
|---|---|
| non_functional | ruff check + ruff format + arch fitness (DDD boundaries, dual filter enforcement) + tsc strict (Playwright TS) |
| functional | pytest unit cubriendo SC-01..SC-14 + pytest integration con DB real |
| visual | Playwright admin-smoke project (5 spec files) en `vitalia/frontend/e2e/admin/` apuntando port 8502 |
| agentic_eval | N/A (story sin agentic touchpoints) |

Playwright specs targeting:
- `admin-login.spec.ts` → SC-01, SC-12
- `admin-tenants-crud.spec.ts` → SC-02, SC-03, SC-07
- `admin-users-crud.spec.ts` → SC-04, SC-05, SC-06
- `admin-clinics-extension.spec.ts` → SC-08, SC-13
- `admin-hipaa-dual-filter.spec.ts` → SC-09, SC-10, SC-11

Cada spec ASSERT (no solo screenshot):
- DOM elements visibles esperados (`getByText`, `getByRole`)
- Network requests (interceptar con `page.route`)
- DB state changes via API verification call
- Audit log row creado via API query

## § 10 — Open questions (ratify Phase A → Phase B)

> NINGUNA. Chris pre-autorizó cadena completa. Decisiones cementadas en parent platform outcome D1-D5.
> Auto-ratify → state refining → refined.

## § 11 — Definition of Done

- [ ] 14 Gherkin scenarios SC-01..SC-14 con tests PASS (gherkin-matrix.md auditor Phase D)
- [ ] Playwright admin-smoke 5 specs PASS (run output en 07-merge.md §2)
- [ ] Arch fitness PASS (DDD + dual filter + spanish-text + anti-duplication)
- [ ] alembic upgrade head exitoso (001 → 023 en DB vitalia_dev)
- [ ] Phantom code DELETED (grep SC-13 cero hits residuales)
- [ ] Capability YAMLs NEW: `vitalia/docs/product/capabilities/{admin,iam,clinics}/*.yaml`
- [ ] Modules MD refreshed: admin + iam + clinics (auto-list regen)
- [ ] 07-merge.md 5 secciones cementadas escritas
- [ ] Squash-merge wip/vitalia → main
- [ ] State reviewing → done
