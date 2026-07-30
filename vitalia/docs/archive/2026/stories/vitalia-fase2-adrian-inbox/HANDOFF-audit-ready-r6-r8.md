# HANDOFF — `vitalia-fase2-adrian-inbox`: rondas UI r6–r8 + AMPLIACIÓN DE SCOPE → listo para auditar y cerrar `done`

> **Escrito 2026-06-04.** Branch `wip/vitalia` @ `358ba0c4` (= `origin/wip/vitalia`). Worktree hub `~/Proyectos/luana-vitalia`. Story **`developing`**.
> **Chris dio sign-off funcional** (2026-06-04): probó el inbox live, lo da por **revisado/aprobado**; quedan solo **detalles estéticos menores** diferidos.
> **Esta es la misión de la PRÓXIMA conversación** (esta se llenó de contexto): reconciliar TODA la documentación con lo que realmente se construyó (el scope creció), escribir los **E2E reales** que monitoreen el comportamiento, correr `/auditor vitalia`, y `/pm-vitalia` merge → **`done`**. Todo **autónomo** (Chris ya aprobó).

---

## 0 · TL;DR de qué pasó y qué falta

- El inbox de Adrián recibió **8 rondas de comentarios de Chris**. Las r1–r5 fueron estética (ya commiteadas, ver chain). **r6–r8** (este handoff) mezclaron estética + **3 bombas de bugs de wiring FE↔BE que nunca se habían ejercido** → el scope se **amplió** de "UI polish" a "hacer que el inbox realmente funcione" (modo, pausa, composer, RBAC, query-keys, repo BE).
- **Todo está commiteado + pusheado + live-verified** contra `dev-app.vitalialat.com` (writes reales `/mode` + `/pause` → 200, logs BE limpios). Chris lo probó y firmó.
- **Falta para `done`:** (1) reconciliar docs (spec/arch/validators/tickets) con el scope ampliado para que el auditor NO revierta, (2) E2E reales (reemplazar los desechables + reescribir el spec de modos a 2-modos + actualizar POMs), (3) `/auditor vitalia`, (4) `/pm-vitalia` merge → `done` (cap YAML v3.2 + archive).

---

## 1 · ⚠️ SCOPE AMPLIADO — lo que el auditor DEBE tratar como comportamiento NUEVO INTENCIONAL (no revertir)

La story arrancó como "pulir el inbox" pero terminó cambiando modelo + RBAC + BE. **El `01-spec.md` todavía describe el modelo VIEJO (3 modos, etc.). Si el auditor corre la gherkin-matrix contra el spec viejo, va a marcar MISSING/FAIL y puede intentar revertir.** Por eso hay que actualizar la doc ANTES de auditar. Cambios intencionales:

| # | Cambio | Antes | Ahora | Impacto doc |
|---|---|---|---|---|
| Modos | Toggle de atención | 3 modos (Adrián decide / consulta / **Yo escribo**) | **2 modos** (Adrián decide / consulta). "Yo escribo" eliminado; escribir manual = **Pausar**. Activo = **verde**. | **AC-4/AC-5 CAMBIAN.** `SegmentedModeValue` 2 valores. |
| Composer | Caja de texto | nunca se montaba (ComposerArea existía pero `InboxThread` no lo renderizaba → "no sale nada") | **montado** al pie (dock); operador escribe como humano; texto enviable | AC composer NUEVO |
| Pausa | Popup | reason textarea + 1 botón "60 min"; **path roto `/pause-adrian` (404)**; nunca funcionó | **2 botones** [Pausar 60 min][Pausar permanente] (rojo), **sin reason**; barra al pie; permanente = far-future (~100 años) | AC pausa CAMBIA |
| RBAC | Quién puede actuar el inbox | mutaciones gateadas a `_PHI_ROLES` {doctor,nurse,admin_clinic} → **owner 403** | `_INBOX_OPERATOR_ROLES` = `_PHI_ROLES ∪ {owner, receptionist}` (mismo set ratificado para list/detail; el inbox es la herramienta del operador). marketing/sales/patient siguen denegados | regla RBAC en arch/hipaa-lite |
| Privacidad lead | Datos contacto | TODO enmascarado con `***` por defecto | **leads visibles por defecto** (interim ratificado Chris); `PiiMaskedSpan` ganó prop `masked` (default true → resto app intacto); ContactSidebar pasa `masked={false}`. Wrapper + `data-phi` se conservan (FE-A6 OK) | AC privacidad + FOLLOW-UP "Máxima seguridad" |
| Query-keys | Reflejo en UI | mutaciones invalidaban `["adrian","inbox",…]` pero el thread lee `["crm","conversation",id]` → el 200 nunca reflejaba | mode/pause/send migrados a keys **crm-shared** | nota arch |
| BE | repo + redis stub | `ConversationRepository` sin `set_pause_until`; `_NoOpRedisClient` sin `setex` → pausa 500 | ambos agregados | nota arch (BE) |
| UI varios | — | — | wallpaper crema **fijo** (no scrollea), dot verde intermitente, Pausar rojo tenue, `cursor-pointer` global + explícito, ícono 🛠 herramientas **eliminado** del header (la actividad vive en el ActivityStream inferior), campo "**Estado**" duplicado eliminado (queda "Etapa de la venta"), "Servicio de interés" **siempre visible** ("Aún no detectado" si vacío) | AC menores |

---

## 2 · Inventario por ronda (evidencia detallada en `checkpoint.md` § `ui_polish_dod_evidence_2026_06_04_pm2..pm9`)

- **r6** (`1a6be139`): montar composer + ModeToggle 3→2 + Pausar al dock + wallpaper crema + cursor global + delete VoiceStyleChip.
- **r7** (`edc3caec`): logos 50% opacity + activo verde + dot verde intermitente + cursor explícito + Pausar rojo + **wallpaper fijo**.
- **r7 #6** (`893bbdcb`): leads desenmascarados (interim) vía `PiiMaskedSpan.masked`.
- **r8** (`cff97820`): **los 2 bugs grandes** — #1 modo (3 capas: POST→PATCH + OCC en body + RBAC owner + query-key crm) + #4 pausa (3 capas: path `/pause` + NoOp `setex` + repo `set_pause_until`) + ícono herramientas fuera + "Estado" dup fuera + servicio-interés empty-state + send query-key fix. Regression test `test_set_mode_200_owner_operator`.
- **docstring** (`358ba0c4`): limpieza ThreadHeader docstring.

### "ToolsSheetTrigger is not defined" (2026-06-04) — RESUELTO, era cache
El source/commit siempre estuvo limpio (sólo quedaba en un docstring). Era **chunk stale de Turbopack** (gotcha #1) en la sesión tibia de Chris. Fix = wipe `.next` + restart FE. Verificado live: conv 22222222 renderiza perfecto, 0 error.

---

## 3 · Archivos tocados r6–r8 (todos commiteados)

**FE** (`vitalia/frontend/src/`):
- `app/globals.css` (cursor global + `--vt-watermark-ink`)
- `features/adrian/api/{use-set-mode,use-pause-adrian,use-send-message}.ts` (+ sus `__tests__`)
- `features/adrian/lib/copy.ts`
- `features/adrian/hooks/use-mode-toggle.ts`
- `features/adrian/types/inbox.types.ts`
- `features/adrian/components/inbox/{ModeToggle,ThreadHeader,InboxThread,ComposerArea,PauseAdrianButton,PauseAdrianConfirmModal,NudgeButton,ToolsSheetTrigger,ContactSidebarToggle,ContactSidebar}.tsx` (+ `__tests__` de los relevantes)
- `components/shared/phi/PiiMaskedSpan.tsx` (prop `masked`)
- **borrados:** `VoiceStyleChip.tsx` + su test

**BE** (`vitalia/backend/src/modules/vitalia/`):
- `inbox/api/router.py` (RBAC `_INBOX_OPERATOR_ROLES` + `_NoOpRedisClient.setex`)
- `crm/infrastructure/persistence/conversation_repository.py` (`set_pause_until`)
- `tests/modules/vitalia/inbox/api/test_router_mode.py` (regression owner)

---

## 4 · TODO-A · RECONCILIAR DOCUMENTACIÓN (hacer ANTES de `/auditor`)

> Objetivo: que el spec/arch/validators describan lo que SE CONSTRUYÓ, para que la gherkin-matrix del auditor matchee y no revierta.

- [ ] **`01-spec.md`** — actualizar § Mapa funcional + § Business rules + Gherkin + § Matriz de cobertura:
  - 2 modos (no 3); "Yo escribo" → estado Pausar. **Marcar AC-4/AC-5 como modificadas.**
  - Composer montado + envío de texto humano.
  - Pausa: 60 min / permanente, sin reason.
  - Privacidad: leads visibles por defecto + RN para "Máxima seguridad" (follow-up).
  - RBAC: operador del inbox (owner/receptionist + clínicos) puede actuar.
  - ActivityStream (glass-box) + "Dar empujón" (nudge re-engagement) + "Servicio de interés" siempre visible + "Etapa de la venta" única (sin "Estado").
- [ ] **`03-arch.md`** — `architecture_pattern: ADR-vitalia-004` sigue; documentar en § Architecture Decisions: `_INBOX_OPERATOR_ROLES` (RBAC), `ConversationRepository.set_pause_until`, `_NoOpRedisClient.setex`, query-keys crm-shared (mode/pause/send), `PiiMaskedSpan.masked`, ThreadComposerDock (dock al pie), wallpaper fijo. § Integration design (CONN) sigue válida.
- [ ] **`04-validators.yaml`** — `verification_nature: funcional`; `business_rules` matrix (regla→`@tag`→scenario) para CADA comportamiento nuevo; `demo_required: true` (firmado, ver §6); `runtime_error_gate` (base.ts); `regression_guard`; `playwright_visual_scope` (rutas/componentes inbox).
- [ ] **`06-tickets.yaml`** — registrar los FOLLOW-UPS (§7) como tickets/notas o rutearlos a `/pm-vitalia` backlog. NO bloquean este `done`.
- [ ] **`checkpoint.md`** — `demo_signoff` ya registrado (ver §6); hygiene de estado.

## 5 · TODO-B · E2E REALES (lo que Chris pide para "monitorear que todo esté bien")

> Los `_zz-*.spec` desechables YA fueron borrados. Hay que dejar goldens REALES (base.ts anti-burbuja, dev-app, backend real, 0 mocks del surface bajo prueba).

- [ ] **Reescribir `e2e/shell-organism/adrian-inbox-modes.spec.ts`** (hoy ` M` uncommitted, modelo 3-modos VIEJO) → 2-modos. **No commitear el actual; reescribirlo.**
- [ ] **POMs**: `e2e/pages/AdrianInboxPage.ts` + `e2e/pages/inbox.page.ts` — quitar locators muertos (`segment-yo-escribo`, `voice-style-chip`, `/pause-adrian`); agregar `pause-modal-60` / `pause-modal-permanent` / `pause-modal-cancel`; `thread-composer-dock`.
- [ ] **Specs nuevos/actualizados** (importan `e2e/fixtures/base.ts`, NO `@playwright/test` directo; contra dev-app; tenant `e69a691d-070e-5caf-a053-6e74642ec100`; convs `11111111…` whatsapp Carlos / `22222222…` instagram):
  - **Modo**: click "Adrián consulta" → `PATCH …/mode` 200 → `aria-checked` refleja; volver a "decide" 200. (owner real).
  - **Pausa**: abrir modal → 2 botones, sin `pause-reason-input` → click 60 min → `POST …/pause` 200 → estado pausado.
  - **Composer**: montado + enviar texto → `POST …/messages` → mensaje aparece en el thread.
  - **Privacidad lead**: ContactSidebar muestra nombre/teléfono/correo reales (sin `***`).
  - **UI**: sin `tools-sheet-trigger`, activo verde, Pausar rojo, sin "Estado", "Servicio de interés" siempre, wallpaper presente, cursor-pointer.
- [ ] Estos specs son los **goldens de monitoreo** que el cap `adrian.inbox` referenciará.

## 6 · Demo sign-off (registrado)
`checkpoint.md::demo_signoff` = `APPROVED_WITH_NOTES` (Chris 2026-06-04): inbox revisado live + aprobado; open_items = detalles estéticos menores (severity low, diferidos). Falta producir `demo-script.md` (4 secciones, derivado de los scenarios Gherkin actualizados) — TODO-A del nuevo conv.

## 7 · FOLLOW-UPS (rutear a `/pm-vitalia` backlog — NO bloquean este `done`)
1. **"Máxima seguridad"** config (flag tenant BE + toggle en Plataforma/Configuración + `masked` lee el flag) — PHI/seguridad → pasa por `/architect`. Terreno listo (`PiiMaskedSpan.masked`).
2. **nudge/retract/proactive** mismo mismatch de query-key (legacy `adrian` keys) que arreglé en mode/pause/send → sus efectos no reflejan hasta migrar a keys crm-shared (1 línea c/u).
3. **Pausa permanente real**: hoy far-future (~100 años); flag indefinido real = cambio BE (`PauseAdrianService` + `_PauseRequest`).
4. **Consolidar `_INBOX_OPERATOR_ROLES`** (mirror en crm + inbox routers) → constante shared vitalia.
5. **Detalles estéticos** que Chris mencionó (no enumerados) — pedirle la lista o capturar al hacer el demo-script.
6. Carlos (conv `11111111`) quedó **pausado 60 min** por el live-test (auto-expira; demuestra que la pausa anda).

## 8 · PRE-EXISTENTES en baseline — NO son de esta story (auditor NO debe atribuirlos ni revertir)
- **FE vitest 4 fails** (git status limpio en esos archivos, no importados por mis cambios): `test_fsd_boundaries` (`AdrianInboxView→crm-shared` — cross-feature ACEPTADO; necesita allowlist correcto, no revertir), `test_no_cross_feature_imports`, `test_phi_pii_components_used` (`recuperar/FrozenLeadRow[diagnosis]`), `audited-section.test` (spy). El "208/208" de handoffs previos era un subset scoped.
- **BE arch**: `test_pgcrypto_phi_columns` (`treatment_plans.notes` TEXT no BYTEA) — deuda HIPAA real, separada; no toqué models/migrations.
- Pertenecen a otras sesiones / stories separadas. Documentar; **no arreglar acá**.

## 9 · GOTCHAS (nos mordieron repetido — el nuevo conv DEBE respetarlos)
1. **Chunk stale Turbopack** (mordió 3×): tras CUALQUIER edit FE → `docker stop luana-dev-vitalia_frontend_dev-1` + wipe `.next` (`docker run --rm -v "$(pwd)/vitalia/frontend:/fe" alpine sh -c 'rm -rf /fe/.next'`) + start + `sleep 10`. Browser de Chris: **Empty-Cache + Hard-Reload**. ★ Mi live-verify (Playwright cold) NO cazaba el serve stale a sesión tibia → **verificar también con cache caliente / hard-reload antes de declarar**.
2. **Footgun dev-app** (#37): el FE container bind-montea el worktree desde el que se corrió `up` por última vez. Verificá `docker inspect … --format '{{range .Mounts}}…'` = tu worktree ANTES de verificar.
3. **Live-verify**: Chrome MCP inestable → Playwright desechable (`@playwright/test` directo, `--project=smoke --no-deps --workers=1`, viewport **1920** para evitar el squeeze de Valeria que deja el thread en 0px). Borrar `_zz-*` + `test-results/_zz-*` al terminar. dark = setear `localStorage` `theme` Y `vitalia-theme` = "dark".
4. **arch no-hardcoded-colors (FE-A1)**: cero hex/`hsl(`/`rgb(` literal en `.tsx`. Usar clases globals.css o `var(--token)`/`color-mix(var())`. Para `bg-[var()]` usar las wrapped `--vitalia-X-color` (NO los canales crudos `--vitalia-X`).
5. **RBAC inbox** = `_INBOX_OPERATOR_ROLES` (owner+receptionist+clínicos). `dr.demo` = **owner**.
6. **Query-keys**: thread/list leen crm-shared (`["crm","conversation",id]` / `["crm","conversations"]`). Las mutaciones DEBEN tocar esos.
7. **Hub compartido**: commit **por pathspec** + `STORY_CLOSURE_GATE_SKIP=1` (embudo hermano `developed`) + delegar a Haiku si >2 files. **NUNCA** `git add .`/`-A`/`-u`. Hay sesiones concurrentes (embudo, canal-inbound).
8. **`adrian-inbox-modes.spec.ts` está ` M`** (3-modos viejo) — el nuevo conv lo REESCRIBE, no lo commitea como está.

## 10 · Comandos clave
```bash
WS=$(git rev-parse --show-toplevel)
# Stack + dev-app
make dev-app-vitalia                 # o verificar containers up
curl -s -o /dev/null -w "%{http_code}\n" https://dev-app.vitalialat.com/api/health
# Wipe FE tras editar (gotcha #1)
docker stop luana-dev-vitalia_frontend_dev-1; docker run --rm -v "$(pwd)/vitalia/frontend:/fe" alpine sh -c 'rm -rf /fe/.next'; docker start luana-dev-vitalia_frontend_dev-1; sleep 10
# FE gates
cd ${WS}/vitalia/frontend && npx tsc --noEmit && npx eslint src/ --cache && npx vitest run src/__tests__/architecture/test_no_hardcoded_colors.test.ts
# BE gates
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/ruff check src/ && ${WS}/.venv/bin/pytest tests/modules/vitalia/inbox/api/ -q
# E2E (dev-app)
cd ${WS}/vitalia/frontend && set -a; source ../.env.dev; set +a; export E2E_BASE_URL="https://dev-app.vitalialat.com"; npx playwright test e2e/shell-organism/<spec> --project=smoke --no-deps --workers=1
```

## 11 · SSoT del estado
- `checkpoint.md` § `ui_polish_dod_evidence_2026_06_04_pm2..pm9` + `demo_signoff`.
- Este handoff (`HANDOFF-audit-ready-r6-r8.md`).
- Chain: `1a6be139` → `edc3caec` → `893bbdcb` → `cff97820` → `358ba0c4` (= `origin/wip/vitalia`).
