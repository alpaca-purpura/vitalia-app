# 05-guidelines.md — vitalia-auth-base-functional

> Patterns required / forbidden + files in scope + skills/rules a cargar por
> `/dev-team` builders. Consume junto a `01-spec.md` + `03-arch-brief.md` + `06-tickets.yaml`.

## § 1 — Skills/rules a cargar PRE-implementación

Cada builder (T-1..T-6) MUST cargar:

| Surface | Skill obligatorio | Rules obligatorias |
|---|---|---|
| T-1 FE middleware | `frontend-expert` | `frontend-fsd.md`, `tenant-isolation.md`, `spanish-text.md` |
| T-2 FE Clerk pages | `frontend-expert`, `claude-api` (Anthropic SDK NO aplica — usar Clerk SDK directo) | `frontend-fsd.md`, `frontend-quality.md`, `spanish-text.md` |
| T-3 FE dashboard | `frontend-expert`, `brand-expert` (design tokens) | `frontend-fsd.md`, `frontend-quality.md`, `spanish-text.md`, `tenant-isolation.md` |
| T-4 BE admin Streamlit | `backend-expert` | `admin-panel.md`, `backend-ddd.md`, `backend-quality.md`, `tenant-isolation.md`, `anti-duplication.md`, `vitalia/.claude/rules/hipaa-lite.md`, `spanish-text.md` |
| T-5 ops deploy | `backend-expert`, `git-manager` | `git-safety.md`, `parallel-safety.md` |
| T-6 Playwright e2e | `playwright-expert` ★ MANDATORY ★ | `e2e-testing.md` |

## § 2 — Files in scope (whitelist — touch ONLY these)

### FE files (T-1, T-2, T-3)

```
NEW:
  vitalia/frontend/src/middleware.ts
  vitalia/frontend/src/app/(dashboard)/layout.tsx              # only if absent
  vitalia/frontend/src/features/dashboard/index.ts
  vitalia/frontend/src/features/dashboard/components/DashboardWelcome.tsx
  vitalia/frontend/src/features/dashboard/components/SliceOneStubsRow.tsx
  vitalia/frontend/src/features/dashboard/api/useDashboardData.ts
  vitalia/frontend/src/features/dashboard/types/DashboardData.ts
  vitalia/frontend/src/features/dashboard/__tests__/DashboardWelcome.test.tsx

EDIT:
  vitalia/frontend/src/app/(auth)/sign-in/page.tsx
  vitalia/frontend/src/app/(auth)/sign-up/page.tsx
  vitalia/frontend/src/app/(dashboard)/page.tsx

DELETE:
  vitalia/frontend/src/app/onboarding/step-1/page.tsx
  vitalia/frontend/src/app/onboarding/step-2/page.tsx
  vitalia/frontend/src/app/onboarding/step-3/page.tsx
  vitalia/frontend/src/app/onboarding/step-1/
  vitalia/frontend/src/app/onboarding/step-2/
  vitalia/frontend/src/app/onboarding/step-3/
```

### BE files (T-4)

```
NEW:
  vitalia/backend/src/modules/vitalia/admin/__init__.py
  vitalia/backend/src/modules/vitalia/admin/app.py
  vitalia/backend/src/modules/vitalia/admin/pages/__init__.py
  vitalia/backend/src/modules/vitalia/admin/pages/tenants.py
  vitalia/backend/src/modules/vitalia/admin/pages/usuarios.py
  vitalia/backend/src/modules/vitalia/admin/modules/__init__.py
  vitalia/backend/src/modules/vitalia/admin/modules/tenants.py
  vitalia/backend/src/modules/vitalia/admin/modules/users.py
  vitalia/backend/src/modules/vitalia/admin/_shared/__init__.py
  vitalia/backend/src/modules/vitalia/admin/_shared/auth.py
  vitalia/backend/src/modules/vitalia/admin/_shared/db.py
  vitalia/backend/tests/admin/__init__.py
  vitalia/backend/tests/admin/test_admin_contract.py

EDIT:
  vitalia/backend/pyproject.toml          # add streamlit + passlib + clerk-backend-api deps
```

### Ops files (T-5)

```
NEW:
  vitalia/deploy/Dockerfile.admin
  vitalia/deploy/k8s/admin-deployment.yaml
  vitalia/deploy/k8s/admin-service.yaml
  vitalia/deploy/k8s/admin-ingress.yaml

EDIT:
  vitalia/deploy/k8s/secrets.template.yaml     # add VITALIA_ADMIN_PASSWORD_HASH
  vitalia/.env.dev.template                    # add VITALIA_ADMIN_PASSWORD_HASH
```

### Tests files (T-6)

```
NEW:
  vitalia/frontend/e2e/auth/sign-in-redirect.spec.ts
  vitalia/frontend/e2e/auth/sign-in-form.spec.ts
  vitalia/frontend/e2e/dashboard/welcome.spec.ts
  vitalia/frontend/e2e/admin/tenants-users.spec.ts
```

### Out of scope — DO NOT TOUCH

- `core/luana-core-*/**` — engine, requires `/pm-luana` promotion gate (per `.claude/rules/anti-duplication.md` + `auditor-downstream-regression.md`)
- `nicolify/**`, `comunify/**`, `lupulo/**` — other brands
- `vitalia/backend/src/modules/vitalia/{copilot,sales_agent,agentic}/**` — `builder-agentic` jurisdiction
- `vitalia/frontend/src/app/(dashboard)/{offers,bookings,appointments,patients,treatments,brand-studio,medical-compliance}/**` — defer a Slice 1 stories
- `vitalia/backend/src/modules/vitalia/{iam,api,application,connections,crm,compliance,infrastructure}/**` excepto si T-4 admin requiere read-only via session factory shared

## § 3 — Patterns REQUIRED

### Patrón P1 — Clerk middleware shape

Single source per Clerk Next.js 16 docs: `clerkMiddleware` con `createRouteMatcher`
para públicas, `auth.protect()` para resto. NO redirect manual, NO chequeo RBAC en
middleware (defer).

Matcher config DEBE excluir `_next` + static assets per Clerk recipe oficial.

### Patrón P2 — Admin Streamlit registry-based

Per `.claude/rules/admin-panel.md`:
- Single `st.set_page_config` en `app.py`
- `st.navigation` con lista `PageSpec` dataclass
- Cada page `pages/{slug}.py` = wrapper thin que llama `modules.{name}.render_*()`
- Lógica vive SOLO en `modules/`
- Shared utilities en `_shared/`

### Patrón P3 — Tenant UUID determinista

Per `seed_fixture_clinics.py`:

```python
_FIXTURE_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # UUID_NAMESPACE_URL

def admin_tenant_id(clinic_slug: str) -> uuid.UUID:
    seed = f"vitalia:admin:tenant:{clinic_slug}"
    return uuid.uuid5(_FIXTURE_NAMESPACE, seed)
```

Mismo namespace + diferente seed string (`vitalia:admin:tenant:` vs
`vitalia:fixture:clinic:`) → tenants admin no colisionan con fixtures.

### Patrón P4 — Audit log mandatory cada admin action

Per `vitalia/.claude/rules/hipaa-lite.md` § audit log:

```python
from src.modules.vitalia.compliance.audit import log_admin_action

log_admin_action(
    action="admin.tenant.create",  # o "admin.user.create"
    resource_type="tenant",
    resource_id=str(tenant_id),
    actor="super-admin",
    payload_redacted={"clinic_name": clinic_name, "country": country},  # no PHI
)
```

Sync write antes response. NO fire-and-forget.

### Patrón P5 — Dashboard Server Component default

Per `.claude/rules/frontend-fsd.md`:
- `DashboardPage` (`app/(dashboard)/page.tsx`) = Server Component
- `DashboardWelcome` = Server Component si solo fetch + render
- `"use client"` SOLO si requiere hooks (useState, eventos)
- React Query hook `useDashboardData` SOLO si necesita refetch cliente (sino server fetch directo)

### Patrón P6 — Spanish neutro LatAm

Per `.claude/rules/spanish-text.md`:
- Tuteo, no voseo
- Tildes + ¿/¡ obligatorios
- Microcopy exact match `01-spec.md § 5`

### Patrón P7 — Anti-duplication cross-brand

Admin Streamlit Vitalia espejea PATTERN nicolify (estructura) PERO reescribe código
brand-specific. NO copy-paste:
- Tenants/users entities tienen schema DB distinto (Vitalia tiene clinic_id + medical_vertical, Nicolify no).
- Validator `nf-anti-duplication-scan` enforza diff ≥ 50 lines vs nicolify.

Si pattern admin (app.py + st.navigation + _shared/auth.py + contract test) es genuinamente
compartible cross-brand → flagear como promotion candidate `/pm-luana` POST-story
(no en este story).

## § 4 — Anti-patterns PROHIBIDOS

### A1 — Scope creep admin Streamlit

❌ Agregar pages adicionales (calendario, planes-billing, costo-agentes, etc.) "porque ya estás en el admin".

✅ Solo `tenants.py` + `usuarios.py`. Otras pages = story propia futura.

### A2 — Implementar offers/bookings/etc en este story

❌ "Ya que tocás dashboard, implementemos también offers tabla".

✅ Esas son stories Slice 1 separadas (`vitalia-slice-1-{inbox,pipeline,agenda,fidelizacion,marketing}`). Mantener placeholders como están.

### A3 — Modificar engine `core/luana-core-*/`

❌ Cualquier edit a engine packages.

✅ Si necesitás cambiar engine → ESCALATE `/pm-luana` con promotion proposal. Story PARK hasta resolver.

### A4 — Cross-brand import

❌ `from nicolify.backend.src.modules.nicolify.admin.modules.tenants import ...`

✅ Reescribir código brand-specific Vitalia. Inspirarse en pattern pero no importar.

### A5 — `git add .` / `git add -A`

❌ Stage masivo durante implementación.

✅ `git add <path/exact>` por archivo. Per `.claude/rules/git-safety.md` + `parallel-safety.md`.

### A6 — Saltar Playwright live

❌ "Tests unit pasan, declaramos PASS sin Playwright real".

✅ T-6 obligatorio. Yo (`/pm-vitalia`) ejecuto Playwright LIVE contra `dev-app.vitalialat.com` ANTES de declarar story done.

### A7 — PHI en admin Streamlit

❌ Mostrar `diagnosis`, `treatment_plan`, `medical_notes`, fechas tratamiento, etc., en pages admin.

✅ Solo identity fields (tenant_id, clinic_name, country, plan_tier, user email, user role). Per `vitalia/.claude/rules/hipaa-lite.md` § PHI fields.

### A8 — Hardcodear admin password

❌ `if password == "admin123": ...`

✅ `bcrypt.verify(password, os.environ["VITALIA_ADMIN_PASSWORD_HASH"])`. Hash en K8s secret.

### A9 — Voseo en UI

❌ "Configura tu clínica", "Haz clic acá", "Ingresa tu email"

✅ "Configura tu clínica", "Haz clic aquí", "Ingresa tu email"

### A10 — Skip middleware test edge case `/api/v1/vitalia/webhooks/clerk`

❌ Middleware protege webhook → Clerk POST falla → user.created event perdido → no profile created.

✅ Webhook route EXPLÍCITAMENTE en `isPublicRoute` matcher.

### A11 — Reimplementar tenant_id generation random

❌ `tenant_id = uuid.uuid4()` para admin tenants.

✅ UUIDv5 determinista (P3). Re-creación idempotente.

### A12 — Olvidar reload K8s secrets post update

❌ `kubectl apply secrets` sin restart deployment → secret nueva no carga.

✅ Post `kubectl apply secrets` → `kubectl rollout restart deployment/vitalia-{backend,admin,frontend}` para forzar reload.

### A13 — Skip Playwright LOCAL pre-deploy ★ v2 NEW ★

❌ "Pasamos directo de T-4 BE a T-5 deploy sin correr T-6.a local smoke porque el commit compila".

✅ T-6.a es GATE de calidad obligatorio. Sin local smoke GREEN, T-5 deploy bloqueado. Per `.claude/rules/hotfix-repro-mandatory.md` — repro positivo (comportamiento esperado funciona) DEBE verificarse local antes de prod.

### A14 — Console.error silencioso en trace Playwright ★ v2 NEW ★

❌ "Test pasó GREEN, ignoramos console.error en trace porque 'no afecta funcionalidad'".

✅ `scripts/playwright_console_network_audit.sh` exit 1 si CUALQUIER `console.error|warn` o 4xx/5xx no esperado. Cero tolerancia errores silenciosos en runtime.

### A15 — Audit_log async fire-and-forget ★ v2 NEW ★

❌ `asyncio.create_task(write_audit_log(...))` post admin action — riesgo de pérdida si proceso crashea.

✅ Audit log write SÍNCRONO antes de response. Per `vitalia/.claude/rules/hipaa-lite.md` § audit log. `fn-be-hipaa-audit-log-verify` validator enforce.

### A16 — Commitear screenshots baseline sin revisión visual ★ v2 NEW ★

❌ "Push baselines `e2e/visual/screenshots/*.png` sin mirarlas — confío que están bien".

✅ Pre-commit revisión visual obligatoria: abrir cada baseline `.png` + verificar contenido esperado (no Clerk dev errors, no console overlay, layout correct). Baselines incorrectas perpetuán bug visual indefinidamente.

## § 5 — Test invariants

- ALL tests pass NATIVE Linux (host) — NUNCA `make e2e*` Docker (crashea per `playwright-expert`).
- BE venv = `$WS/.venv/bin/{ruff,pytest}` desde workspace root.
- FE = `cd vitalia/frontend && npx {tsc,eslint,vitest,playwright}`.
- Playwright LIVE = `E2E_BASE_URL=https://dev-app.vitalialat.com` (no localhost).

## § 6 — Decisions honored (cite in commit body)

Cada commit body MUST incluir sección "Decisions honored" citando D# de `01-spec.md § 8`
que aplica al ticket. Ej:

```
feat(vitalia/admin): T-4 admin Streamlit tenants + users scope mínimo

## Decisions honored
- D2 — Admin Streamlit scope SOLO tenants + usuarios (no scope creep)
- D3 — No traer otras pages Nicolify (anti scope creep)
- D7 — Container K8s separado (Dockerfile.admin + admin-deployment.yaml en T-5)
- D8 — Super-admin auth basic auth bcrypt

## Anti-duplication
- Pattern espejado de nicolify/admin (st.navigation registry + pages/modules split)
- Código brand-specific reescrito (diff ≥ 50 lines vs nicolify tenants.py + users.py)
```

Auditor Cat 11 (Cross-cutting) verifica cite presence.

## § 7 — TDD note explicit por ticket ★ v2 NEW ★

Per `.claude/rules/tdd-mandatory.md` — **tests PRIMERO, implementación DESPUÉS**. Aplica a TODOS los tickets FE/BE de esta story (T-1, T-2, T-3, T-4):

| Ticket | Test RED first | Implementation GREEN after |
|---|---|---|
| T-1 FE middleware | Unit test mock requests públicas/protegidas en `middleware.test.ts` (si arch FE lo soporta) | `middleware.ts` con clerkMiddleware + createRouteMatcher |
| T-2 FE Clerk pages | Snapshot Vitest sign-in/sign-up con `<SignIn />` / `<SignUp />` mocked | Replace placeholders con componentes Clerk reales |
| T-3 FE dashboard | `DashboardWelcome.test.tsx` RED: renders heading + tenant badge + CTA | Implementar DashboardWelcome.tsx + SliceOneStubsRow.tsx |
| T-4 BE admin | `test_admin_contract.py` + `test_clerk_webhook_integration.py` + `test_audit_log_verify.py` + `test_cross_tenant_isolation.py` RED | Implementar admin Streamlit modules + audit_log writes + tenant isolation runtime |
| T-6.a/b Playwright | Specs son inherentemente tests (no aplica RED→GREEN, son el GREEN target) | n/a |

**Ejemplo flow T-4** (per `.claude/rules/tdd-mandatory.md`):
1. Escribir `test_audit_log_verify.py::test_admin_tenant_create_writes_audit_log` → RED (función no existe)
2. Implementar `modules/tenants.py::create_tenant()` con `log_admin_action(...)` sync write
3. Run test → GREEN
4. Escribir siguiente test (e.g., payload_no_phi) → RED → GREEN
5. Refactor mientras GREEN

NUNCA escribir implementación primero y "después le pongo el test cuando termine".

## § 8 — Pre-T-5 manual checklist Chris (Clerk dashboard) ★ v2 NEW ★

ANTES de que `/dev-team` arranque T-5 ops deploy, Chris MUST completar este checklist manual en
Clerk dashboard Vitalia (`https://dashboard.clerk.com` → app "vitalia"):

### Checklist (Chris-only, ~5 min)

- [ ] **App Clerk Vitalia creada y activa** (verificar dashboard).
- [ ] **Domain configurado**: `dev-app.vitalialat.com` agregado en Clerk dashboard → Settings → Domains.
- [ ] **Métodos de inicio de sesión habilitados**:
  - Email + contraseña (mínimo)
  - Google OAuth (opcional — recomendado para conversión)
- [ ] **API Keys obtenidas** (Settings → API Keys):
  - `VITALIA_CLERK_PUBLISHABLE_KEY` (pk_test_... o pk_live_...) → cargado en K8s secret
  - `VITALIA_CLERK_SECRET_KEY` (sk_...) → cargado en K8s secret
- [ ] **Webhook endpoint configurado** (Webhooks → + Add Endpoint):
  - URL: `https://dev-app.vitalialat.com/api/v1/vitalia/webhooks/clerk`
  - Evento: `user.created` (activo) — más eventos defer Slice 2
- [ ] **Signing Secret webhook obtenido** (whsec_...) → cargado en K8s secret `VITALIA_CLERK_WEBHOOK_SECRET`
- [ ] **CLERK_TESTING_TOKEN generado** (Settings → Testing → Generate testing token) → exportar como `CLERK_TESTING_TOKEN_VITALIA` env var para T-6.a + T-6.b Playwright runs
- [ ] **CLERK_ISSUER URL identificada** (Settings → API Keys → "Frontend API URL") → cargado en K8s secret como `CLERK_ISSUER`

Sin este checklist completo, T-5 ops deploy NO procede. `/dev-team` Step 0 antes de spawn builder T-5 debe verificar checklist done (Chris confirma in-chat o marca campo en `checkpoint.md::pre_t5_chris_checklist_done: true`).

## § 9 — Patrones adicionales v2 ★ NEW ★

### Patrón P8 — Playwright visual screenshot baseline storage ★ v2 NEW ★

Estructura baselines:
```
vitalia/frontend/e2e/visual/
├── visual-smoke.spec.ts
└── screenshots/
    ├── signin-baseline.png         (git tracked)
    ├── signup-baseline.png         (git tracked)
    └── dashboard-baseline.png      (git tracked)
```

Convención:
- Threshold `{ threshold: 0.2, maxDiffPixels: 100 }` — permite minor pixel drift Clerk dev mode UI
- `expect(page).toHaveScreenshot('name.png', {...})`
- Primer run en T-6.b CI → genera baselines automáticamente
- Runs subsecuentes → pixel diff vs baseline → FAIL si excede threshold
- Git commit baselines con T-6.b push inicial

Si Chris cambia design tokens o Clerk publica UI update → re-generate baselines manualmente con
`npx playwright test e2e/visual/ --update-snapshots` + commit baselines nuevos.

### Patrón P9 — Backend integration test fixtures ★ v2 NEW ★

Estructura tests integración:
```
vitalia/backend/tests/integration/admin/
├── conftest.py                          # fixtures
│   - fake_clerk_webhook_payload (valid HMAC)
│   - fake_clerk_webhook_payload_invalid_hmac
│   - admin_session_authenticated
│   - tenant_a_factory / tenant_b_factory (UUIDv5 deterministic)
├── test_clerk_webhook_integration.py
├── test_audit_log_verify.py
└── test_cross_tenant_isolation.py
```

Patrones:
- Use `httpx.AsyncClient` + FastAPI `TestClient` para POSTear webhooks
- Use SQLAlchemy session fixture con transaction rollback (no pollute DB)
- Verify rows via `select(Model).where(...)` post action
- HMAC signature: compute con `hmac.new(secret, payload, hashlib.sha256).hexdigest()` para fake valid sig

## § 10 — Auditor responsibilities v2 ★ NEW ★

`/auditor` Phase D `06-audit/gherkin-matrix.md` post-developed:

- Verify 18/18 scenarios SC-01..SC-18 mapped → test → PASS
- Verify 19 validators must_pass = GREEN
- Verify pre-T-5 Chris checklist done (cita `checkpoint.md::pre_t5_chris_checklist_done: true`)
- Verify cross-brand anti-mirror enforced (`nf-anti-duplication-scan` GREEN)
- Verify TDD respetada (commits muestran test commit antes impl commit per ticket — sample 1 ticket)
- Verify visual baselines commitead + revisadas (no console errors visibles en .png)

Si todos GREEN → AUTO-HANDOFF `/pm-vitalia merge`.
