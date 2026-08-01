# HANDOFF — vitalia-fase2-adrian-inbox (terminar en sesión nueva)

> **Escrito 2026-06-04** al llenar contexto. Story `state: developing` (fase `LIVE_VERIFY_BUGFIX`). Worktree: `~/Proyectos/luana-vitalia` (hub, `wip/vitalia`). **NO está `done`.** Branch al día: último commit `0e1fc458`.
>
> **★ INSTRUCCIÓN DE CHRIS:** cuando termines de DESARROLLAR (cerrar los pendientes técnicos de abajo) → **avisale a Chris para que él pruebe en dev-app ANTES de `/auditor`**. NO encadenar a `/auditor` sin su prueba + sign-off.

## TL;DR — dónde estamos

El inbox de Adrián **funciona live en dev-app** (verificado con Chrome MCP + e2e reales). El `developed` autónomo había sido falso; esta sesión cerró los blockers reales y los verificó. Falta: 1 decisión (telemetry-404), `/auditor`, demo sign-off de Chris, merge.

**Verificado live (dev-app, Clerk real dr.demo + backend real + seed, 0 mocks):** thread renderiza mensajes (AC-3/6) · 3-modos toggle (AC-4) · take-control · nudge (AC-8) · **compliance PHI real** (AC-9) · contacto phone/email (AC-10) · **activity stream** (AC-6/7) · `?conv=` deep-link (AC-3/RN-14) · full colapsa Valeria (AC-7/SC-5). **E2E sobre dominio dev: ~28 verdes.**

## Commits de esta sesión (wip/vitalia)

| SHA | Qué |
|---|---|
| `b678b1f4` | wire selección conversación (store + lead param) |
| `f8a88159` | **compound detail endpoint** (el fix headline — thread renderiza) + seed messages + contact wiring |
| `af4f94a2` | **AC-9 compliance** un-stub (ComplianceService(PhiChannelPolicy) en send/proactive/nudge) |
| `0e1fc458` | `?lead=`→`?conv=` rename + ActivityStream montado en InboxThread + T-6 e2e wireados+corridos live |

## LA decisión pendiente (es de Chris) — telemetry 404

3 e2e (`adrian-inbox-tenant.spec.ts:43/76/101`) quedan **rojas** por un 404 **pre-existente, transversal, NO del inbox**: `mateo/lib/telemetry.ts` hace `POST /api/telemetry/growth-studio-event` con `fetch` crudo, pero **ningún router BE sirve esa ruta**. El gate anti-burbuja (`e2e/fixtures/base.ts`) caza el 404 nativo de Chrome → falla el teardown "0 errores de consola". La lógica cross-tenant del inbox PASA; solo falla por el ruido del 404.

Documentado: `vitalia/docs/observed-bugs/2026-06-04-fe-telemetry-growth-studio-event-404.md`.

3 opciones (preguntar a Chris al arrancar):
- **(A) Arreglar ahora** — crear endpoint BE `POST /api/telemetry/growth-studio-event` (resuelve ctx vía ClinicResolver, valida event_type, delega a `GrowthStudioEmitter.emit_event`) + cambiar `telemetry.ts` a `fetchClient` (manda X-Tenant-ID + token). Desbloquea los 3 e2e + mata el 404 app-wide. Toca mateo/plataforma.
- **(B) Diferir** — dejar documentado; los 3 tenant e2e quedan rojos por causa externa; story dedicada mateo/plataforma lo arregla.
- **(C) Mínimo silenciar** — `telemetry.ts` early-return si endpoint no existe (no-op); mata el ruido sin crear el endpoint (telemetría sigue sin persistir).

`emit_event(*, event_type, tenant_id, clinic_id?, entity_id?, user_id?, props?)` — `vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py:117`.

## Pasos restantes hasta `done` (ordenados)

1. **Resolver telemetry-404** según decisión de Chris (arriba).
2. **Verificar live lo que falta** (Chrome MCP o e2e): AC-5 (composer respeta modo: manual envía / consulta draft) — no ejercido aún con write real; AC-12 (mobile 3-tabs — el fallback actual es single-panel, NO 3 tabs como pide el spec → posible gap).
3. **Correr suite e2e completa limpia** en dev-app (ver runbook) → confirmar verde salvo lo decidido en #1.
4. **★ AVISAR A CHRIS** → él prueba en dev-app paso a paso + da `demo_signoff` (DoD #37 / Rule #37). NO saltar este gate.
5. `/auditor vitalia vitalia-fase2-adrian-inbox` (Phase D gherkin-matrix + verifica `base.ts` importado + regression_guard).
6. `/pm-vitalia` merge → `done` + cap YAML `adrian.inbox` (cap_change_type=new) + `git mv` story a archive.

## RUNBOOK — cómo correr e2e en dev-app (crítico, costó descubrirlo)

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}; set -a; source vitalia/.env.dev 2>/dev/null; set +a
cd vitalia/frontend
export E2E_BASE_URL="https://dev-app.vitalialat.com"
export E2E_CLERK_USER_EMAIL="${DEV_APP_TEST_EMAIL:-dr.demo@vitalialat.com}"
export E2E_CLERK_USER_PASSWORD="${DEV_APP_TEST_PASSWORD}"

# 1. AUTH: el setup REUSA storageState viejo si "fresco" → si quedó de localhost, los specs
#    aterrizan en "Sign in to Vitalia". FORZAR re-auth contra dev-app:
rm -f playwright/.clerk/user.json
npx playwright test --project=setup        # "auth state saved" (no "skipping re-auth")

# 2. Correr specs (project=smoke; los adrian-inbox-* fueron wireados al smoke testMatch):
npx playwright test e2e/shell-organism/adrian-inbox-modes.spec.ts --project=smoke --reporter=line --workers=1
# Suite completa inbox: modes nudge phi-redirect states tenant (+ a11y→project=a11y, visual→project=visual)
```

**Gotchas confirmados:**
- **Seed dev:** `vitalia/backend/scripts/seed_inbox_conversations.sql` (2 convs) + `seed_inbox_messages.sql` (3+5 msgs). Aplicar vía **stdin** (el path /app difiere en el container postgres):
  `sg docker -c "docker exec -i luana-dev-luana_postgres_dev-1 psql -U postgres -d vitalia_dev" < vitalia/backend/scripts/seed_inbox_messages.sql`
  Tenant Sanaré `e69a691d-070e-5caf-a053-6e74642ec100` · clinic `f035be5b-0ac4-5210-8fc3-395650ca2b83`.
- **Mounts (footgun):** backend container `luana-dev-vitalia_backend_dev-1` monta este worktree en **`/workspace`**; frontend `luana-dev-vitalia_frontend_dev-1` monta en **`/app/vitalia/frontend`**. Ambos = worktree `luana-vitalia`. Si el stack se levantó de otro worktree, sirve código viejo → re-`make dev-app-vitalia` desde acá.
- **Stale-bundle HMR:** a veces un `reload` simple no agarra el cambio FE; hizo falta `touch <archivo>` + hard-reload (ignoreCache). Con e2e Playwright esto no aplica (cada run es fresco), pero al verificar con Chrome MCP sí.
- **`docker` necesita `sg docker -c "..."`** (grupo docker, ver MEMORY docker-group).

## Chrome MCP (Chris lo cerró → cayó)

El server `chrome-devtools` sigue sano a nivel CLI (`claude mcp list` → ✓ Connected, lo respawnea on-demand), pero el **binding de tools de la sesión** no se re-registra desde adentro. Para recuperarlo en sesión nueva: arranca normal (re-registra al inicio) o `/mcp` reconnect. **Alternativa = e2e Playwright vía Bash (más fuerte, DoD #37).** Skill `chrome-devtools-verify` para verify conversacional.

## Mapa de cambios clave (para entender el código)

- **Compound detail endpoint** (headline): `vitalia/backend/src/modules/vitalia/crm/api/router.py` `get_conversation_detail` ahora devuelve `ConversationDetailResponse` (`crm/application/dto/conversation_detail_dto.py`) = `{conversation, lead(decrypted), messages, action_receipts, tools_state}`. Antes devolvía `ConversationListItem` lean → `detail.messages` undefined → thread crasheaba ("no aparece nada").
- **AC-9 compliance:** `inbox/api/router.py` `_build_compliance_service()` = `ComplianceService(policies=[PhiChannelPolicy()])` inyectado en `_get_send_service` (+ `activity_event_repo`), `_get_proactive_service`, nudge inner. Borrado `_NoOpComplianceService`. Policy: `inbox/application/policies/phi_channel_policy.py` (bloquea PHI keywords en whatsapp/sms → portal redirect).
- **`?conv=` rename:** schema `features/adrian/lib/url-state.ts` (`lead`→`conv`) + consumers AdrianInboxView (`searchParams.get("conv")`), ConversationListPanel (`setUrlState({conv})`, `urlState.conv`), InboxPageClient, use-activity-stream-poll, url-state.test.
- **ActivityStream montado** en `InboxThread.tsx` (estaba solo en el root muerto `InboxPageClient`).
- **2 roots inbox:** `AdrianInboxView` (ACTIVO, lo renderiza page.tsx) vs `InboxPageClient` (legacy de la migración, NO usado). Ojo al editar — el activo es AdrianInboxView.

## Aprendizajes cross-cutting (candidatos a learning formal — confirmar con Chris)

1. **Specs escritos ≠ specs que corren.** Los T-6 inbox specs (a) tenían import path roto (`../../fixtures`→`../fixtures`) y (b) **no matcheaban ningún `project` del playwright.config** → nunca ejecutaron, nunca fueron verdes. Un "tengo e2e" sin verificar que corren es falso verde. Extiende [[verification-real-not-200]].
2. **storageState Clerk es por-origin.** El `setup` reusa `playwright/.clerk/user.json` si es "fresco" aunque sea de otro baseURL (localhost) → specs aterrizan en sign-in contra dev-app. Forzar `rm` del storageState al cambiar de baseURL.
3. **`waitForLoadState("networkidle")` post-click es race en SPA soft-nav.** El thread (React) monta después del networkidle → asserts fallan flaky. Fix determinista: `await page.locator('[data-testid="conversation-thread"]').waitFor({state:"visible"})`.

## Estado de verificación por AC (resumen honesto)

✅ live: AC-1, AC-2, AC-3, AC-4, AC-6, AC-7, AC-8, AC-9, AC-10, AC-13 · 🟡 parcial/sin ejercer write: AC-5 (composer modo), AC-11 (axe sin correr aislado), AC-12 (mobile = single-panel, no 3-tabs → revisar spec). Matriz completa: `SELF-REVIEW-compliance.md`.
