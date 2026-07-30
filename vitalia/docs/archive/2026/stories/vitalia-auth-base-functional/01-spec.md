# 01-spec.md — vitalia-auth-base-functional

> **Story type:** hot-fix scope-acotado (≤2 días dev) · service + UI mixto
> **Owner spec:** `/pm-vitalia` (skip `/po-ux` formal, scope quirúrgico ratificado Chris)
> **Repro:** ver `checkpoint.md::repro_evidence` (placeholders T-fe-3 visibles en dev-app.vitalialat.com 2026-05-18)
> **State:** ready (skip refining→refined formal porque scope claro)
> **Cement-date:** 2026-05-18

## § 1 — Problem statement

Al entrar a `https://dev-app.vitalialat.com/` el usuario ve placeholders literales
("Sidebar — pendiente T-fe-3", "Header — pendiente T-fe-3", "Métricas del panel
(pendiente T-fe-3)") **en lugar del login Clerk + dashboard funcional**. Causa raíz
confirmada en repo:

1. **Sin Clerk middleware** (`vitalia/frontend/src/middleware.ts` no existe). Rutas
   no protegidas → entrar a `/` cae directo al placeholder dashboard.
2. **Páginas Clerk son stubs literal** ("Inicio de sesión con Clerk (pendiente T-fe-3)").
   `<SignIn />` y `<SignUp />` de `@clerk/nextjs` nunca fueron renderizados.
3. **Dashboard `/` + offers + bookings + appointments + onboarding/step-{1,2,3}** son
   stubs scaffolding T-fe-3 de Story 11 nunca implementados.
4. **Vitalia no tiene admin Streamlit** (Nicolify sí, en
   `nicolify/backend/src/modules/nicolify/admin/`). No hay forma de crear tenants
   + users por UI propia — solo CLI `seed_fixture_clinics.py`.

Bloqueo de validación: Chris no puede loguearse, ver wizard ni dashboard, ni
crear primer tenant+user real para probar Slice 1 onboarding-wizard (already
shipped 2026-05-18).

## § 2 — Goal (functional)

Tener una base mínima funcional **deployed en `dev-app.vitalialat.com`** donde Chris
pueda:

1. Entrar a `/` y ser redirigido a `/sign-in` (no autenticado).
2. Loguearse con Clerk real (form `<SignIn />`).
3. Ver dashboard mínimo post-login (no placeholder).
4. Abrir `/onboarding/wizard` y completar el wizard ya implementado (Story
   `vitalia-slice-1-onboarding-wizard` done 2026-05-18, capability
   `wizard_brand_studio_slice_1`).
5. Como super-admin, abrir admin Streamlit `vitalia-admin.vitalialat.com` (o subpath),
   crear un tenant + crear un user Clerk asociado.
6. Validar todo lo anterior con Playwright smoke E2E live (yo, antes de declarar PASS).

**Lo que NO entra (defer):**

- Implementar offers/bookings/appointments/patients reales (eso es las 6 stories Slice 1
  refined ya en backlog: `vitalia-slice-1-{inbox,pipeline,agenda,fidelizacion,marketing}`).
- Admin Streamlit completo (espejo de los 22 pages Nicolify). Solo `tenants` + `usuarios`.
- Onboarding `step-1/step-2/step-3` páginas separadas (wizard único en `/onboarding/wizard`).
- Sales agent / copilot conversaciones (Slice 1 features stories).
- Audio Whisper (deferred a Slice 2).

## § 3 — Gherkin scenarios (verification matrix anchor)

> Estos scenarios son SSoT de la story. Cada ticket en `06-tickets.yaml::gherkin_coverage`
> mapea a un subset. `/auditor` Phase D ejecuta tests citados → matrix verdict por scenario.

### SC-01 — Root redirige a sign-in cuando no autenticado

```gherkin
Feature: Clerk middleware proteger rutas autenticadas

  Scenario: SC-01 — Unauthenticated user accessing dashboard root
    Given Chris is not authenticated (no Clerk session cookie)
    When he visits "https://dev-app.vitalialat.com/"
    Then the server responds 307 redirect to "/sign-in"
    And the browser navigates to "/sign-in"
    And he sees the Clerk SignIn form (email + password inputs visible)
```

### SC-02 — Public routes accesibles sin auth

```gherkin
  Scenario: SC-02 — Public landing route is not protected
    Given Chris is not authenticated
    When he visits "https://dev-app.vitalialat.com/public/aurora-dental-ar"
    Then the server responds 200
    And the page renders public clinic landing (no Clerk redirect)
```

### SC-03 — Sign-in renderiza form Clerk real

```gherkin
Feature: Clerk SignIn page implementada

  Scenario: SC-03 — Sign-in page renders Clerk form
    Given Chris visits "/sign-in"
    Then he sees the Clerk <SignIn /> component fully rendered
    And the form has visible inputs for email + password
    And NO placeholder text "pendiente T-fe-3" is visible
    And the page styling matches design-system tokens (no broken layout)
```

### SC-04 — Sign-up renderiza form Clerk real

```gherkin
  Scenario: SC-04 — Sign-up page renders Clerk form
    Given Chris visits "/sign-up"
    Then he sees the Clerk <SignUp /> component fully rendered
    And the form has visible inputs for email + password + name
    And NO placeholder text "pendiente T-fe-3" is visible
```

### SC-05 — Sign-up flow dispara webhook + crea perfil

```gherkin
  Scenario: SC-05 — User completes sign-up triggers webhook
    Given Chris is on "/sign-up"
    When he submits valid credentials (email "chris-test@vitalialat.com" + password)
    Then Clerk creates the user account
    And Clerk POST "user.created" to "https://dev-app.vitalialat.com/api/v1/vitalia/webhooks/clerk"
    And the backend webhook adapter `clerk_webhook_adapter.py` validates HMAC signature
    And the backend creates a UserProfile row associated with one of the seeded fixture clinics
    And Chris is redirected to "/" post sign-up
    And the dashboard renders welcome state (not placeholder)
```

### SC-06 — Dashboard mínimo post-login

```gherkin
Feature: Dashboard mínimo welcome (Slice 0 — pre Slice 1)

  Scenario: SC-06 — Authenticated user lands on welcome dashboard
    Given Chris is authenticated with a tenant assigned
    When he visits "/"
    Then the dashboard renders:
      | element | visible | content |
      | Welcome heading | yes | "Hola, {nombre}" |
      | Tenant context badge | yes | "{clinic_name} · {plan_tier}" |
      | Onboarding CTA | yes (if !is_onboarded) | "Configurar tu clínica" → /onboarding/wizard |
      | Slice 1 stubs row | yes | "Próximamente: Inbox · Pipeline · Agenda · Fidelización · Marketing" |
    And NO placeholder text "Métricas del panel (pendiente T-fe-3)" is visible
```

### SC-07 — Wizard onboarding accesible (capability ya shipped)

```gherkin
  Scenario: SC-07 — Authenticated user can open onboarding wizard
    Given Chris is authenticated with a tenant assigned and is_onboarded=false
    When he clicks "Configurar tu clínica" on the dashboard
    Then the browser navigates to "/onboarding/wizard"
    And the WizardOnboardingLayout component renders fully
    And the wizard shows step 1 (perfil clínica) — already shipped 2026-05-18
```

### SC-08 — Admin Streamlit accesible y crear tenant

```gherkin
Feature: Admin Streamlit Vitalia (scope mínimo: tenants + users)

  Scenario: SC-08 — Super-admin opens admin app and creates a tenant
    Given Chris is a super-admin with admin credentials
    When he visits the admin Streamlit URL (TBD — vitalia-admin subdomain or subpath)
    Then he sees the Streamlit navigation with 2 options: "Tenants" + "Usuarios"
    When he clicks "Tenants"
    And he submits the create-tenant form with:
      | field | value |
      | clinic_name | "Test Clínica Demo" |
      | country | "AR" |
      | locale | "es-AR" |
      | timezone | "America/Argentina/Buenos_Aires" |
      | vertical | "dental" |
      | plan_tier | "solo_doctor" |
    Then a new tenant row is inserted in vitalia_dev DB with UUIDv5 tenant_id
    And the page shows success message + new tenant in the list
```

### SC-09 — Admin Streamlit crear user Clerk asociado a tenant

```gherkin
  Scenario: SC-09 — Super-admin creates Clerk user associated to tenant
    Given the tenant "Test Clínica Demo" exists
    And Chris is on the admin "Usuarios" page
    When he submits the create-user form with:
      | field | value |
      | email | "owner-demo@vitalialat.com" |
      | name | "Owner Demo" |
      | tenant_id | "{tenant_id_of_Test_Clinica_Demo}" |
      | clinic_id | "{clinic_id}" |
      | role | "clinic_owner" |
    Then the Clerk Backend API is called to create the user
    And a UserProfile row is inserted associating the Clerk user_id to the tenant
    And the page shows success message + magic sign-in link for the new user
```

### SC-10 — Playwright smoke live VERDE (yo valido antes de PASS)

```gherkin
Feature: Playwright live verification against deployed environment

  Scenario: SC-10 — Full smoke suite passes against dev-app.vitalialat.com
    Given the redeploy to dev-app.vitalialat.com is complete
    And K8s secrets VITALIA_CLERK_* are set with real values (not REPLACE_ME)
    And fixture clinics are seeded (Aurora dental AR + Mindful CL + Sanaré MX)
    When Playwright runs the full suite (base + a11y + mobile + visual):
      | spec | scenarios covered |
      | e2e/auth/sign-in-redirect.spec.ts | SC-01, SC-02 |
      | e2e/auth/sign-in-form.spec.ts | SC-03, SC-04 |
      | e2e/dashboard/welcome.spec.ts | SC-06, SC-07 |
      | e2e/admin/tenants-users.spec.ts | SC-08, SC-09 |
      | e2e/a11y/a11y-smoke.spec.ts | SC-14 |
      | e2e/mobile/mobile-smoke.spec.ts | SC-15 |
      | e2e/visual/visual-smoke.spec.ts | SC-16 |
    Then all specs pass (≥ 18/18 PASS, 0 FAIL)
    And total duration < 90 seconds
    And `scripts/playwright_console_network_audit.sh` exit 0 (no console.error|warn, no 4xx/5xx no esperados)
```

### SC-11 — Cross-tenant isolation enforced post admin create (HIPAA dual filter) ★ v2 NEW ★

```gherkin
Feature: HIPAA-lite dual filter (tenant_id + clinic_id) prevents cross-tenant data leaks

  Scenario: SC-11 — Tenant A user cannot read Tenant B data via dual filter
    Given super-admin created Tenant A with clinic_id_A and Tenant B with clinic_id_B
    And user U_A is associated with tenant_id_A + clinic_id_A
    When U_A authenticates and queries with X-Tenant-ID=tenant_id_A but clinic_id of Tenant B
    Then the backend returns 404 (no leak — dual filter enforced per hipaa-lite.md)
    And no log entry exposes data of clinic_id_B
    When U_A queries with X-Tenant-ID=tenant_id_B (header mismatch with auth token)
    Then the backend returns 403 (tenant mismatch detected)
```

### SC-12 — Webhook HMAC validation rejects invalid signatures ★ v2 NEW ★

```gherkin
Feature: Clerk webhook adapter HMAC security gate (Svix standard)

  Scenario: SC-12 — Invalid HMAC signature is rejected, no DB write occurs
    Given the backend exposes /api/v1/vitalia/webhooks/clerk
    And VITALIA_CLERK_WEBHOOK_SECRET is configured (whsec_...)
    When a POST arrives with valid payload but invalid svix-signature header
    Then the backend returns 401 Unauthorized
    And no UserProfile row is created
    And no audit_log row is created
    And the rejection is logged with structlog warning (signature mismatch)

  Scenario: SC-12.bis — Unsupported event types are accepted as no-op
    Given the backend webhook adapter handles only user.created
    When Clerk POSTs a user.deleted event with valid HMAC
    Then the backend returns 200 OK (no error)
    And no UserProfile row is created (no-op)
    And no audit_log row is created (no-op)
```

### SC-13 — Admin audit_log row created post action (HIPAA compliance) ★ v2 NEW ★

```gherkin
Feature: HIPAA-lite audit_log mandatory (per vitalia/.claude/rules/hipaa-lite.md § audit log)

  Scenario: SC-13 — Admin tenant.create writes audit_log row synchronously
    Given super-admin is authenticated in admin Streamlit
    When super-admin submits create-tenant form for "Test Clínica Demo" (AR, dental)
    Then a row is INSERTED in vitalia_audit_log table with:
      | column | value |
      | action | "admin.tenant.create" |
      | actor | "super-admin" |
      | resource_type | "tenant" |
      | resource_id | "{tenant_uuid_v5}" |
      | payload_redacted | JSON contains clinic_name + country + plan_tier (NO PHI) |
      | timestamp | within last 5 seconds |
    And the row is written SYNCHRONOUSLY before the success response
    And payload_redacted does NOT contain any PHI fields (diagnosis, medical_notes, etc.)

  Scenario: SC-13.bis — Admin user.create writes audit_log row synchronously
    Given a tenant exists
    When super-admin submits create-user form
    Then a row is INSERTED in vitalia_audit_log with action="admin.user.create"
    And payload_redacted contains email + role (identity only, NO PHI)
```

### SC-14 — A11y axe smoke pass (sign-in + sign-up + dashboard + wizard) ★ v2 NEW ★

```gherkin
Feature: A11y compliance smoke (axe-core) — vertical médica stakes altas

  Scenario: SC-14 — All public + post-login pages pass axe critical + serious checks
    Given Playwright + @axe-core/playwright is configured
    When axe.run() is invoked on each page:
      | page | URL |
      | sign-in | /sign-in |
      | sign-up | /sign-up |
      | dashboard | / (authenticated) |
      | wizard | /onboarding/wizard (authenticated) |
    Then ZERO critical violations are reported
    And ZERO serious violations are reported
    And the test passes (moderate + minor violations logged but non-blocking)
```

### SC-15 — Mobile viewport (iPhone 13) responsive ★ v2 NEW ★

```gherkin
Feature: Mobile responsive smoke (devices['iPhone 13'])

  Scenario: SC-15 — Dashboard + sign-in render correctly on mobile
    Given Playwright project=mobile uses devices['iPhone 13']
    When the test visits /sign-in on mobile viewport
    Then the Clerk SignIn form is fully visible without horizontal scroll
    And tap targets (buttons + inputs) have height ≥ 44px (iOS tappable minimum)
    When the test visits / (authenticated) on mobile viewport
    Then DashboardWelcome renders without overflow
    And SliceOneStubsRow wraps to 2-column grid (no horizontal scroll)
    And "Configurar tu clínica" CTA is visible + tappable (≥ 44px)
```

### SC-16 — Visual screenshot baseline (regression detection) ★ v2 NEW ★

```gherkin
Feature: Visual regression baseline (toHaveScreenshot)

  Scenario: SC-16 — Screenshot baselines established + regression detected on future runs
    Given Playwright visual specs in e2e/visual/
    When the test runs `expect(page).toHaveScreenshot('signin-baseline.png')`
    Then on FIRST RUN: baseline .png is created in e2e/visual/screenshots/
    And on SUBSEQUENT RUNS: pixel diff vs baseline computed
    And if diff > 0.2 threshold (allow minor Clerk dev mode UI updates): test FAILS
    And the baselines cover: /sign-in, /sign-up, / (dashboard welcome)
    And baselines are git-tracked (committed in T-6.b first push)
```

### SC-17 — Broader trace monitor (console + network) ★ v2 NEW ★

```gherkin
Feature: Broader trace monitor post-Playwright run (replaces narrow Clerk grep)

  Scenario: SC-17 — Playwright trace.zip audit detects any error
    Given Playwright runs all specs with --trace=on
    When scripts/playwright_console_network_audit.sh parses trace.zip
    Then the script verifies:
      | check | expected |
      | console.error count | 0 |
      | console.warn count | 0 (allowlist Clerk dev mode if applicable) |
      | HTTP 4xx responses | 0 (excepto 401 ESPERADO en pre-auth validations) |
      | HTTP 5xx responses | 0 |
      | uncaught promise rejections | 0 |
    And exit code 0 if all checks pass, exit 1 if any violation detected
```

### SC-18 — Local smoke pre-deploy gate ★ v2 NEW ★

```gherkin
Feature: Playwright LOCAL smoke as gate de calidad antes del deploy

  Scenario: SC-18 — Local smoke must pass before T-5 deploy proceeds
    Given the developer ran `make dev-vitalia` and stack is up (postgres + backend:8002 + frontend:3002)
    And optionally admin Streamlit local on port 8501
    And scripts/e2e-preflight.sh PASS
    When Playwright runs `--project=smoke` with E2E_BASE_URL=http://localhost:3002
    Then base scenarios SC-01..SC-09 pass against local stack
    And the result gates T-5 deploy (T-5 blocked until T-6.a LOCAL smoke GREEN)
    And this prevents wire-up bugs from being discovered in production dev environment
```

## § 4 — Wireframes (compactos, scope acotado)

### Sign-in page (`/sign-in`)

```
┌─────────────────────────────────────────────────────────┐
│                                                          │
│                  [Vitalia logo]                          │
│                                                          │
│           ┌─────────────────────────────┐                │
│           │       Iniciar sesión        │                │
│           ├─────────────────────────────┤                │
│           │  [Clerk SignIn component]   │                │
│           │   - Email                   │                │
│           │   - Password                │                │
│           │   - [Continuar]             │                │
│           │   - "¿No tienes cuenta? →   │                │
│           │      Crear una"             │                │
│           └─────────────────────────────┘                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Dashboard `/` mínimo post-login

```
┌─────────────────────────────────────────────────────────┐
│ [Vitalia logo]                          [UserButton ▾]  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Hola, {first_name} 👋                                   │
│  {clinic_name} · {plan_tier}                             │
│                                                          │
│  ┌──────────────────────────────────────────────┐        │
│  │ Aún no configuraste tu clínica.              │        │
│  │ [Configurar tu clínica →]                    │        │
│  │  (visible solo si is_onboarded=false)        │        │
│  └──────────────────────────────────────────────┘        │
│                                                          │
│  Próximamente en Vitalia (Slice 1):                      │
│  ┌────────┬─────────┬────────┬───────────┬───────────┐  │
│  │ Inbox  │Pipeline │ Agenda │Fideliz.   │ Marketing │  │
│  │  📥    │  🎯     │  📅    │  💚       │  📢       │  │
│  │ pronto │ pronto  │ pronto │ pronto    │ pronto    │  │
│  └────────┴─────────┴────────┴───────────┴───────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Admin Streamlit Vitalia (scope mínimo)

```
┌──── Sidebar ─────┐  ┌──── Main panel ─────────────────────┐
│ 🛠 Vitalia Admin │  │  Tenants                              │
│                  │  │  ────────────────────────────────────│
│ 🏥 Tenants       │  │  Crear nuevo tenant:                  │
│ 👤 Usuarios      │  │   [Clinic name]      [Test Clínica D] │
│                  │  │   [Country]          [AR ▾]           │
│                  │  │   [Locale]           [es-AR ▾]        │
│                  │  │   [Timezone]         [Argentina/BA ▾] │
│                  │  │   [Vertical]         [dental ▾]       │
│                  │  │   [Plan tier]        [solo_doctor ▾]  │
│                  │  │   [Crear tenant]                      │
│                  │  │                                       │
│                  │  │  Tenants existentes:                  │
│                  │  │   • aurora-dental-ar (AR, dental)     │
│                  │  │   • mindful-cl (CL, psychology)       │
│                  │  │   • sanare-mx (MX, psychiatry)        │
│                  │  │   • test-clinica-demo (AR, dental) ★  │
└──────────────────┘  └───────────────────────────────────────┘
```

## § 5 — Microcopy Spanish neutro

| Componente | Texto |
|---|---|
| Sign-in heading | "Iniciar sesión" |
| Sign-up heading | "Crear cuenta" |
| Dashboard welcome | "Hola, {first_name} 👋" |
| Tenant badge | "{clinic_name} · {plan_tier}" |
| Onboarding CTA | "Configurar tu clínica" |
| Stubs Slice 1 heading | "Próximamente en Vitalia" |
| Stub items | "Inbox", "Pipeline", "Agenda", "Fidelización", "Marketing" |
| Stub footer | "pronto" |
| Admin Streamlit title | "Vitalia Admin" |
| Admin tenants page | "Tenants" |
| Admin users page | "Usuarios" |
| Tenant create success | "Tenant creado: {tenant_id}" |
| User create success | "Usuario creado. Magic link enviado a {email}" |

**No voseo** (per `.claude/rules/spanish-text.md`). LatAm neutro tuteo.

## § 6 — Out-of-scope explícito

- ❌ Implementar otras pages dashboard (offers/bookings/appointments/patients): defer a stories Slice 1 existentes refined.
- ❌ Admin Streamlit con +2 pages (sales / metrics / billing / etc.): scope creep — defer a story propia futura.
- ❌ Onboarding step-{1,2,3} páginas separadas (legacy scaffold): el wizard único en `/onboarding/wizard` ya cubre el flow. Las páginas step-N quedan como stubs (no se tocan) o se eliminan en T-2 si conviene.
- ❌ Multi-clinic UI (defer Slice 2/3).
- ❌ Webhooks adicionales (solo `user.created` ya implementado).
- ❌ Sales agent / copilot conversaciones live.
- ❌ Cualquier modificación a `core/luana-core-*` (engine). Hot-fix solo `vitalia/` brand.

## § 7 — Compliance + cross-cutting

- **HIPAA-lite** (per `vitalia/.claude/rules/hipaa-lite.md`):
  - Admin Streamlit NO debe mostrar PHI (diagnósticos, treatment_plan, medical_notes). Solo identity fields (tenant_id, clinic_name, country, plan_tier, user email).
  - Admin audit_log row por cada creación tenant/user.
  - RBAC: admin Streamlit requiere super-admin role (no clinic_owner — eso es para users dentro del SaaS).
- **Tenant isolation**: cada tenant creado via admin → UUIDv5 determinista (mismo pattern que `seed_fixture_clinics.py`).
- **Spanish neutro**: todos los textos UI sin voseo.
- **No cross-brand mirror**: el admin Streamlit es brand-aislado (per `.claude/rules/admin-panel.md`). NO importar nada de `nicolify/`. Espejar el PATTERN (st.navigation registry, contract test, pages+modules split) reescribiendo el código brand-specific Vitalia. Si pattern se vuelve compartido entre 2+ brands → lift candidate `/pm-luana` futuro.

## § 8 — Decisions

| ID | Decisión | Razón |
|---|---|---|
| D1 | Skip `/po-ux` + `/architect` formal | Scope quirúrgico ratificado Chris. Hot-fix per `.claude/rules/hotfix-repro-mandatory.md`. |
| D2 | Admin Streamlit scope = SOLO tenants + usuarios | Chris ratificó "espejo nicolify sacando solo creación tenant + usuarios". Anti scope creep. |
| D3 | No traer otras pages Nicolify (campaigns/metrics/billing/etc.) | Idem D2. Cada page = ~200 LOC overhead — ban sin necesidad shipped. |
| D4 | Wizard ya está en `/onboarding/wizard` — NO duplicar en step-{1,2,3} | Wizard es shipped capability `wizard_brand_studio_slice_1`. Step-N legacy scaffold. |
| D5 | Worktree `wip/vitalia` canónico, no spawnar efímero | Per `.claude/rules/parallel-safety.md` M12. Story scope acotado, branch estable. |
| D6 | Playwright smoke LIVE contra `dev-app.vitalialat.com` (no Docker local) | Validar real deploy. `make e2e` Docker prohibido per `playwright-expert` skill. |
| D7 | Admin Streamlit deploy = container K8s separado (no merge con backend container) | Aislamiento. Espejar pattern nicolify si existe deploy nicolify-admin K8s separado; sino, agregar Dockerfile.admin + K8s Deployment + Service + Ingress nuevo. T-5 confirma. |
| D8 | Super-admin auth Streamlit = Streamlit Authenticator (basic auth) con bcrypt | Scope mínimo. Defer Clerk integration admin a story futura. Variable `VITALIA_ADMIN_PASSWORD_HASH` en K8s secret. |

## § 9 — Open questions (resolver ANTES `/dev-team` spawn)

| ID | Pregunta | Default recomendado |
|---|---|---|
| Q1 | Admin Streamlit URL: subdomain `vitalia-admin.vitalialat.com` o subpath `dev-app.vitalialat.com/admin`? | **Subdomain** — aislamiento DNS+CORS más limpio + alineado pattern nicolify si existe |
| Q2 | Fixture clinic auto-asociada al sign-up del primer user? | **Sí** — webhook `user.created` busca tenant con email_domain match en metadata, sino asocia a `aurora-dental-ar` (default fixture) |
| Q3 | Eliminar páginas legacy `app/onboarding/step-{1,2,3}/page.tsx` o dejar stubs muertos? | **Eliminar** — son code-rot post wizard unificado |
| Q4 | Admin Streamlit super-admin: 1 password compartido o multi-admin via Streamlit Authenticator config? | **1 password env-var** (scope mínimo). Multi-admin defer story futura |

## § 10 — Estimación (v2 post gaps audit)

| Ticket | Surface | Estim hours | Notas v2 |
|---|---|---|---|
| T-1 FE middleware Clerk | FE | 1h | sin cambios v1 |
| T-2 FE pages Clerk + cleanup legacy step pages | FE | 2h | sin cambios v1 |
| T-3 FE dashboard mínimo welcome | FE | 3h | sin cambios v1 |
| T-4 BE admin Streamlit + 3 integration tests | BE | 8h | **+2h v2** (webhook + audit_log + cross-tenant integration tests) |
| T-5 ops K8s deploy + post_deploy_smoke.sh | ops | 3.5h | **+0.5h v2** (auto smoke script) |
| T-6.a tests Playwright LOCAL pre-deploy gate | tests | 2h | **NEW v2 split** |
| T-6.b tests Playwright LIVE + a11y + mobile + screenshots + trace monitor | tests | 4h | **+1h v2** (3 new specs) |
| **TOTAL** | | **~23.5h (~3 días dev)** | **+5.5h vs v1** |

**Critical path:** T-4 (8h) → T-6.a (2h) → T-5 (3.5h) → T-6.b (4h) = **17.5h wall clock**.

## § 11 — Acceptance (story-level v2)

Story PASS cuando:

1. Todos los **18 scenarios** SC-01..SC-18 ejecutados (Playwright + backend integration tests) contra `dev-app.vitalialat.com` y entorno local → 18/18 PASS.
2. `/auditor` Phase D `06-audit/gherkin-matrix.md` → 18/18 scenarios con test PASS.
3. `04-validators.yaml` **19 validators** `must_pass: true` → todos GREEN.
4. **T-6.a local smoke GREEN** ANTES de T-5 deploy (gate de calidad).
5. **T-6.b LIVE smoke + a11y + mobile + screenshots + broader trace monitor** GREEN post-T-5.
6. Yo (`/pm-vitalia` orchestrator) corro Playwright LIVE T-6.b ANTES de declarar PASS y reporto evidencia.
7. Chris puede loguearse efectivamente y abrir wizard + admin sin asistencia técnica.
8. Chris completó pre-T-5 manual checklist (Clerk dashboard webhook config + signing secret) — ver `05-guidelines.md § 8`.

## § 12 — Handoff next

Post ratificación spec Chris → `/dev-team vitalia-auth-base-functional` arranca T-1..T-6.b en orden DAG:

```
T-1 + T-4 (parallel) → T-2 + T-3 → T-6.a LOCAL (gate) → T-5 ops → T-6.b LIVE
```

Tras `state=developed` GREEN → **AUTO-HANDOFF** `/auditor` (default per
`.claude/rules/story-closure-gate.md`).
Tras APPROVED → **AUTO-HANDOFF** `/pm-vitalia merge`.

`defer_audit: false` (NO escape valve — Chris quiere validación live antes de cerrar).
