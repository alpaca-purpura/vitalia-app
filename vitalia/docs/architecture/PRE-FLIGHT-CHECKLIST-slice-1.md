---
created_at: 2026-05-20
created_by: /pm-vitalia (ratified Chris 2026-05-20 sesión replan Slice 1)
status: open
purpose: |
  Pre-flight gates HARD BLOCK antes de arrancar Ola 1 Slice 1 vitalia.
  Cada item debe estar checked y verificado para entrar a /architect refresh.
  Ratified Chris: Opción A — bloquear hasta verde.
---

# PRE-FLIGHT CHECKLIST — Slice 1 vitalia

> Hard block antes de Ola 1 (`/inbox` + `/fidelización`). Sin estos en verde,
> `/architect` NO refresha stories y `/dev-team` NO arranca build.

## § Bloque A — Clerk dashboard (manual Chris)

> **★ Decisión Chris 2026-05-20: NO usamos Clerk Organizations en esta etapa.**
> Multi-tenancy se maneja via tenants + users propios en engine `luana-core-iam` (tablas
> `tenants` + `users` + `user_tenants` junction). Clerk es solo identity provider.
> Ver `~/.claude/projects/-home-chalreme-Proyectos-luana-platform/memory/no-clerk-organizations.md`.

Clerk instance: `moral-gator-27.clerk.accounts.dev` (test).

- [ ] **A.1** — Verificar testing token fresco.
  Current: `CLERK_TESTING_TOKEN_VITALIA=<valor en vitalia/.env.dev — NUNCA pegarlo en este doc tracked>`
  Verify expiry: Clerk dashboard → Testing → Tokens → expiry date.
  Si <30 días → regenerar y reemplazar en `vitalia/.env.dev`.
  > ⚠ 2026-08-01: un token literal estuvo commiteado aquí — fue redactado y DEBE rotarse
  > (Clerk dashboard → Testing → Tokens → regenerate) antes de dar acceso al repo a terceros.

- [ ] **A.2** — Verificar Clerk webhook `VITALIA_CLERK_WEBHOOK_SECRET` configurado en `vitalia/.env.dev`.
  Sin secret → engine webhook handler no acepta payloads → no auto-sync user.created.
  Si missing → Clerk dashboard → Webhooks → endpoint dev-app → copiar signing secret.

## § Bloque B — Test users (vía Clerk CLI) + tenants (vía seed script)

> Usar pattern `clerk-cli-automation-pattern` (memoria reference). Automatizable via
> `npx clerk users create` tras `clerk auth login` 1 vez. **NO usar `organizations` commands**.

- [ ] **B.1** — Crear 3 test users (Clerk-side):
  ```bash
  # Passwords: NUNCA en este doc (tracked). Generar y guardar en vitalia/.env.dev
  # (DEV_APP_TEST_PASSWORD etc.). Los 3 passwords que estuvieron commiteados aquí
  # fueron redactados 2026-08-01 → rotar esos users si siguen existiendo.

  # Test user #1 — owner+doctor
  npx clerk users create \
    --email dr.demo@vitalia.test \
    --password "$DEV_APP_TEST_PASSWORD" \
    --first-name "Dr. Demo" \
    --last-name "Vitalia" \
    --public-metadata '{"vitalia_role":"doctor"}'

  # Test user #2 — recepción
  npx clerk users create \
    --email recepcion@vitalia.test \
    --password "<generar — guardar en .env.dev>" \
    --first-name "Recepción" \
    --last-name "Demo" \
    --public-metadata '{"vitalia_role":"recepcion"}'

  # Test user #3 — super_admin
  npx clerk users create \
    --email admin@vitalia.test \
    --password "<generar — guardar en .env.dev>" \
    --first-name "Admin" \
    --last-name "Demo" \
    --public-metadata '{"vitalia_role":"super_admin"}'
  ```

  Verify: `curl -H "Authorization: Bearer $CLERK_SECRET_KEY" https://api.clerk.com/v1/users` retorna 3 users.

- [ ] **B.2** — Sync automático Clerk → backend (`users` table).
  Al crear users en B.1, Clerk dispara `user.created` webhook hacia engine handler:
  `core/luana-core-iam/src/luana_core_iam/api/webhooks.py::_handle_user_sync` →
  `INSERT INTO users (clerk_id, email, full_name, role='admin')`.
  Vitalia ClerkWebhookAdapter (`vitalia/backend/src/modules/vitalia/infrastructure/adapters/clerk_webhook_adapter.py`)
  además dispara `OnboardingService.create_clinic_profile(user)` que crea tenant + user_tenant junction.

  **Verify post B.1:**
  ```bash
  docker exec luana-dev-luana_postgres_dev-1 psql -U postgres -d vitalia_dev \
    -c "SELECT id, email, clerk_id, role FROM users;"
  # Expected: 3 rows con los 3 clerk_id
  ```

  Si webhook NO disparó (dev-app no expuesto a Clerk webhook, o testing token override) →
  fallback B.3 manual.

- [ ] **B.3** — Fallback: seed 3 tenants fixture + asociar 3 users via SQL.
  Si B.2 no auto-sincronizó, usar fixture seed:
  ```bash
  docker exec luana-dev-vitalia_backend_dev-1 bash -c "
    cd /workspace/vitalia/backend && uv run python scripts/seed_fixture_clinics.py --apply
  "
  # Crea 3 tenants: Aurora (AR/dental) + Mindful (CL/psychology) + Sanaré (MX/psychiatry)
  ```

  Y crear NEW script `seed_test_users_link.py` (en proceso T-preflight-1):
  ```bash
  docker exec luana-dev-vitalia_backend_dev-1 bash -c "
    cd /workspace/vitalia/backend && uv run python scripts/seed_test_users_link.py
  "
  # Link: dr.demo + recepcion → Sanaré (tenant primario tests)
  #       admin → todos 3 (super_admin)
  ```

  Verify:
  ```bash
  docker exec luana-dev-luana_postgres_dev-1 psql -U postgres -d vitalia_dev \
    -c "SELECT u.email, t.slug, ut.role FROM users u JOIN user_tenants ut ON u.id=ut.user_id JOIN tenants t ON t.id=ut.tenant_id;"
  ```

- [ ] **B.4** — (NO usar Clerk Organizations). Skip — modelo legacy ya validado.

## § Bloque C — Playwright storage state

- [ ] **C.1** — Asegurar `vitalia/frontend/playwright/.clerk/` existe:
  ```bash
  mkdir -p vitalia/frontend/playwright/.clerk
  ```

- [ ] **C.2** — Generar storage state via Playwright auth fixture:
  ```bash
  cd vitalia/frontend
  E2E_BASE_URL=http://localhost:3002 \
  E2E_USER_EMAIL=dr.demo@vitalia.test \
  E2E_USER_PASSWORD="$DEV_APP_TEST_PASSWORD" \
  npx playwright test --grep "@auth-setup" --project=smoke
  ```

  Verify: `vitalia/frontend/playwright/.clerk/user.json` existe + contiene token Clerk válido + cookie session.

- [ ] **C.3** — Verify freshness: token Clerk dentro de TTL 5 días. Si >4 días → re-run C.2.

## § Bloque D — Suite smoke verification

- [ ] **D.1** — Local smoke suite 23 specs GREEN:
  ```bash
  cd vitalia/frontend
  E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke
  ```
  Verify: All 23 specs PASS, 0 RED, 0 SKIP (excepto si tienen `test.skip` documentado).

- [ ] **D.2** — Live smoke suite 23 specs GREEN:
  ```bash
  cd vitalia/frontend
  E2E_BASE_URL=https://dev-app.vitalialat.com npx playwright test --project=smoke
  ```
  Verify: All 23 specs PASS contra live deploy.

- [ ] **D.3** — Mobile smoke GREEN:
  ```bash
  cd vitalia/frontend
  E2E_BASE_URL=https://dev-app.vitalialat.com npx playwright test --project=mobile
  ```

- [ ] **D.4** — A11y smoke critical+serious cero:
  ```bash
  cd vitalia/frontend
  npx playwright test e2e/a11y/a11y-smoke.spec.ts
  ```

## § Bloque E — Core promotion lift (paralelo a D)

- [ ] **E.1** — `/pm-vitalia` ping `/pm-vitalia` con draft `PROPOSAL-DRAFT-core-platform-extensions-slice-1.md`.
- [ ] **E.2** — `/pm-vitalia` crea proposal real en `docs/promotion-protocol/proposals/2026-05-20-core-platform-extensions-slice-1.md`.
- [ ] **E.3** — Engine implementation:
  - `core/luana-core-platform/src/luana_core_platform/workers/cron_envelope.py` + tests
  - `core/luana-core-platform/src/luana_core_platform/repositories/compound_scope_repository.py` + tests
- [ ] **E.4** — Version bump 0.2.0 → 0.3.0 + CHANGELOG entry.
- [ ] **E.5** — Vitalia consumer refactor 11 callers (imports + constructor changes).
- [ ] **E.6** — Engine + vitalia full test suite GREEN.
- [ ] **E.7** — Proposal state migrated.

## § Bloque F — Admin Streamlit bugs handoff cleanup

Reference: `vitalia/docs/archive/2026/stories/vitalia-auth-base-functional/HANDOFF-next-session.md`.

- [x] **F.1** Bug #1 (`$` literal en `.env.dev`) — FIXED en sesión origen
- [x] **F.2** Bug #2 (`Settings` 14 vars) — MITIGATED via container exec
- [x] **F.3** Bug #3 (puerto 8501 no exposed) — WORKAROUND TCP forwarder activo
- [x] **F.4** Bug #4 (phantom `vitalia_clinics`) — RESUELTO (migration 023 crea `vitalia_clinic_branches` real)
- [ ] **F.5** Bug #5 (Redis container DNS) — no crítico para Slice 1 UI. Decisión Chris: ¿Vitalia necesita Redis en Slice 1 (caching agenda views o tools_sheet read-only)? Si sí, agregar a `vitalia/docker-compose.dev.yml`.

## § Bloque G — Smoke vitalia stack actual (sanity check)

- [x] **G.1** Stack vitalia 8002 BE /health 200 — VERIFIED 2026-05-20
- [x] **G.2** FE 3002 /sign-in 200 — VERIFIED 2026-05-20
- [x] **G.3** Postgres 5435 vitalia_dev alembic head=023 — VERIFIED 2026-05-20
- [x] **G.4** Cloudflared tunnel dev-app.vitalialat.com — VERIFIED 2026-05-20

## § Exit criteria → Ola 1 unlock

Todos los items § A + § B + § C + § D + § E + § F.5 (decisión) deben estar [x].
Cuando todos verde → `/pm-vitalia` actualiza brand checkpoint con `preflight_gates: GREEN` y dispara `/architect refresh vitalia-slice-1-inbox` + `/architect refresh vitalia-slice-1-fidelizacion` en paralelo.
