<!-- voseo-allowed: handoff interno -->
# HANDOFF — retomar `estabilizar-harness-e2e-lisa-marca` HASTA DONE

> Pegá la sección "PROMPT PARA PEGAR" en una conversación nueva. El resto es el detalle que ese prompt referencia.

---

## PROMPT PARA PEGAR

```
/dev-team vitalia estabilizar-harness-e2e-lisa-marca — retomar el REBUILD del layer e2e lisa-marca HASTA suite verde-determinista ×3 + DoD #37, en el worktree canónico luana-vitalia (wip/vitalia). Leé primero vitalia/docs/product/stories/estabilizar-harness-e2e-lisa-marca/HANDOFF-resume.md (mapa completo) + chris-input.md + T-1b-pom-rewrite-mandate.md + T-1b-phantom-testid-audit.txt. NO delegues la reescritura de POMs ni la iteración e2e a builders aislados (branchean de base divergente sin el de-mock + no corren live) — hacelo en este worktree con el stack UP. Verificación REAL (no GET-200): corré la suite live contra el stack y leé logs. Orden sugerido: (1) keystone autosave hydration race, (2) rewrite POMs fantasma restantes, (3) seed/write-then-assert, (4) suite ×3 + parent ×5 → 0 flaky, (5) DoD #37 + demo + 07-merge. Confirmá conmigo el sign-off del demo antes de done.
```

---

## ESTADO (al cierre 2026-06-03)

- **Branch:** `wip/vitalia` @ `ad412f02` (todo pusheado a origin). Worktree: `~/Proyectos/luana-vitalia`.
- **Story:** `developing`, phase `REBUILD_E2E_LAYER_MULTISESSION`. Tipo bugfix-lite. Módulo `brand_studio`.
- **Stack:** UP (`luana-dev-vitalia_{backend,frontend,cloudflared}_dev-1`). Si no: `make dev-vitalia`.
- **Tenant de test:** `e69a691d-070e-5caf-a053-6e74642ec100` (⚠️ identity VACÍO: `name:""`).

### Commits de esta saga (en orden)
- `ea2bd5c0` T-1 de-mock lisa-marca + BE addendum (trust-signals/trust-catalog X-User-ID opcional)
- `8ec083d0` identidad POM phantom-testid fixes + T-1b mandate/audit
- `40ab8475` **identity/visuals/contact autosave PATCH + actor real (sub-bug #2 completo)**
- (T-2 `4bf94366` FE personality actor · T-3 `5ef8cdd4` BE sub-bug #1+#2b — anteriores en la cadena)

## YA HECHO + VERIFICADO (no rehacer)

- **BE T-3:** `get_prohibited_phrases` X-User-ID opcional (sub-bug #1) + `_resolve_audit_actor` (helper DRY, resuelve Clerk userId→users.id vía `iam/application/services/user_resolver.py::resolve_user_uuid_from_clerk_id`) en los 11 endpoints que auditan. 13 tests GREEN contra DB real + arch 335.
- **BE addendum:** `get_trust_signals` + `get_trust_catalog` → X-User-ID opcional (eran reads que exigían el header → 422 en browser). Verificado live 200. (⚠️ `get_initial_state` SIGUE exigiendo X-User-ID pero el FE NO lo llama → no bloquea; decidir si se deja o se hace opcional.)
- **FE T-2 + 40ab8475:** las 4 mutations de guardado mandan PATCH + `buildMutationHeaders` (X-User-ID = Clerk userId real, X-User-Role) + los 4 hooks (personality/identity/visuals/contact autosave) cablean `userId` de `useAuth()`. tsc+eslint+vitest 53/53.
- **T-1 de-mock:** forwarding lifteado a `e2e/fixtures/real-backend-forward.fixture.ts` (mergeTests base.ts+auth), 11 specs de-mockeados, voice-preview-mock borrado, `base.ts` anti-burbuja adoptado, M1 grep-gate `sc2` corregido en 04-validators.
- **POM parcial:** `lisa-marca-page.pom.ts` (SubSubTabsBar: `sub-sub-tabs-bar` + `sub-sub-tab-{id}` + `aria-current=page`; marcaContent → unión `identidad-view`/`voz-tono-section-root`/`presencia-view`) + `identidad-section.pom.ts` (nameInput/taglineInput → getByLabel real; sectionRoot → `identidad-view`) + `PresenciaView.tsx` (+`data-testid="presencia-view"`).

## PENDIENTE (el rebuild — HACER HASTA DONE)

### 1. KEYSTONE — autosave no dispara el PATCH en e2e
Síntoma: `fillName(...)` → badge nunca llega a `data-state="saved"`, NO aparece `PATCH /identity` en logs BE.
Hipótesis: race de hidratación RHF — el spec llena el campo ANTES de que el GET puble el form → `reset()` del GET pisa el valor → sin dirty → sin autosave. (El tenant devuelve `name:""`, así que el form arranca vacío + se rehidrata vacío.)
Fix probable (test-side): esperar la hidratación del GET antes de escribir (ej. `await page.waitForResponse(/lisa\/marca\/identity.*GET/)` o un signal de "form listo" en el POM `waitForLoaded`). Verificar en `IdentidadView`/`IdentityCard` si hace `reset(data)` on GET success. Confirmar live (Chrome DevTools MCP o trace) que el PATCH dispara post-fix.

### 2. Rewrite POMs fantasma restantes (≈60 testids)
`T-1b-phantom-testid-audit.txt` = inventario. **El FE usa ARIA real, NO data-testids.** Por cada locator de los POMs `voz-tono-section.pom.ts`, `presencia.pom.ts` (si existe), + las secciones logo/contact/trust/voice: LEER el componente FE (`src/features/lisa/components/marca/{voz-y-tono,presencia}/*.tsx`) y reescribir a **getByRole > getByLabel > getByText > getByTestId** (playwright-expert).
Testids REALES confirmados (usar): `identidad-view`, `voz-tono-section-root`, `presencia-view`, `sub-sub-tabs-bar`, `sub-sub-tab-{id}` (+`aria-current="page"` activo), `autosave-badge` (+`data-state`). Inputs identidad: `getByLabel(/Nombre de la clínica/)`, `getByLabel(/Tagline/)` (id `brand-name-input`/`tagline-input`+`<Label htmlFor>`).

### 3. Tests dependientes de data → write-then-assert
Tenant vacío. Los tests "datos cargan al montar" (`not.toHaveValue("")`) fallan sin seed. Convertir a write-then-reload-then-assert (determinista, sin seed). Los autosave ya escriben.

### 4. Suite ×3 + parent ×5 → 0 flaky
```
WS=$(git rev-parse --show-toplevel); set -a; source ${WS}/vitalia/.env.dev; set +a
cd ${WS}/vitalia/frontend
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke e2e/regression/vitalia-fase2-lisa-marca/ --repeat-each=3 --workers=1
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke e2e/regression/arreglar-guardado-voz-y-tono/ --repeat-each=5
```
Iterar hasta 0 flaky · 0 failed. Specs corren en `--project=smoke` (testMatch `/e2e/regression/.*\.spec\.ts/`, storageState `playwright/.clerk/user.json`, dep `setup`).

### 5. DoD #37 + cierre
- `dod_live_verified: true` + `dod_evidence` (writes ejercidos + efecto en DB + logs sin traceback) en checkpoint.
- `demo-script.md` + `demo_signoff` de Chris (gate Fase F `/pm-vitalia`).
- T-4 (docs): re-cablear cap `lisa-marca.yaml` `e2e_test` → specs honestos + `verified_real`.
- `/auditor` → `/pm-vitalia merge` (07-merge + archive).

## SETUP env para tests (CRÍTICO)
```
# BE pytest native (DB real):
WS=$(git rev-parse --show-toplevel); cd ${WS}/vitalia/backend
set -a; source ${WS}/vitalia/.env.dev; set +a
export POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=5435
export POSTGRES_DSN="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5435/${POSTGRES_DB}"
${WS}/.venv/bin/pytest tests/modules/vitalia/brand_studio/ -k "prohibited or audit_actor" -p no:randomly
```
(⚠️ tests integration usan `@pytest.mark.integration` → skipean si POSTGRES_DSN no responde. Sin el export → skip silencioso = falso "verde".)

## TRAMPAS / NOTAS
- ⚠️ **Builders aislados branchean de base divergente** (sin el de-mock) + no corren live → NO delegar la reescritura de POMs ni la iteración e2e. Hacelo en este worktree.
- Suite `brand_studio` BE tiene 1 fallo pre-existente (`test_marca_cross_tenant` usa `AsyncClient(app=app)` httpx-0.28 incompat) + flakiness orden-random (contención asyncpg). NO es de esta story.
- mypy no está en el venv local (limitación); los files nuevos pasan `--strict` vía `uvx`.
- Footgun cross-worktree (rule #37): correr `make dev-vitalia` desde ESTE worktree antes de verificar.
- `bidirectional SOFT_DRIFT drift=1` en pre-commit = advisory, no bloquea.
