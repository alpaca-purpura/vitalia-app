# HANDOFF — vitalia-fase2-adrian-embudo → `done` (Session 4 close)

> **Generado 2026-06-04 (sesión 4).** Reemplaza el handoff de sesión 3. El producto NO está `done`: la live-verify por-superficie (que faltaba) destapó **2 bugs reales nuevos** + una **decisión UX de producto**. Más: Chris pidió una **investigación forense del proceso** (por qué el `dod_live_verified: true` previo fue falso). El bloqueo estructural (gate FE compartido RED por la sesión inbox + `demo_signoff`) **sigue**.

---

## ★★ SESIÓN 5 UPDATE (2026-06-04 · /pm-vitalia → /dev-team fix-loop) — B1/B2/U1/U2 RESUELTOS + LIVE-VERIFIED

**Hechos esta sesión (lane `code:crm`, NO se tocó shell/inbox):**
- **U1 ratificado por Chris = nombre completo.**
- **B2 (BE `78a7ba52`):** `get_lead_detail` devuelve el score COMPUTADO (override read-side; el create vive en lane inbox). TDD 12/12. + `assigned_doctor_id` en `LeadResponse`.
- **B1 (FE `b1d32f83`):** ★ el handoff sesión 4 asumió "orden de hooks en recuperar" — **FALSO** (RecuperarView/FrozenLeadRow tienen hooks limpios). Reproduje el crash live: **el shell `dynamic({ssr:false})` cuelga en soft-nav** ("Cargando shell" stuck). Fix lane-safe: el chip `congelados` (único acceso a `/recuperar`) → **hard-nav `<a>`**. Live: `recuperar-live.spec` R-1 5/5. **Root-cause del shell (afecta otros soft-navs) ESCALADO a story shell** (junto a U3).
- **U1 (FE `b1d32f83`):** `PiiMaskedSpan` fuera del nombre en LeadCard+ResumenView+FrozenLeadRow → nombre completo (non_phi).
- **U2 (FE `b1d32f83`):** ResumenView muestra Nombre+Teléfono+Correo. Contract-safe: nuevo `LeadDetailLeadDTO` mirror de `LeadResponse` (NO se widenó LeadCardDTO/board) + `ContractPair` registrado.
- **Verify nativo:** tsc 0 · eslint adrian 0 · vitest embudo 20/20 · contract-parity 5/5 · BE funnel 12/12. **Live-verify dev-app:** recuperar-live R-1 5/5 · resumen-live D+E 4/4 (score==Σfactores · nombre completo · teléfono/correo). `dod_evidence` actualizado.
- Commits por pathspec: `78a7ba52` (BE) · `b1d32f83` (FE) · `9e31d1b7` (specs+docs). Pusheados a `wip/vitalia`.

**SIGUE BLOQUEADO (verificado 2026-06-04 14:43):** la sesión **inbox sigue `developing`**, sus arch-tests sin commitear, 6 unit RED → **gate FE compartido RED**. NO se puede: (a) agregar el entry embudo a `KNOWN_CROSS_FEATURE_INTERNAL_IMPORTS` (ese arch-test es WIP de inbox), (b) correr `/auditor` con gate verde, (c) mergear.

**CAMINO A done restante:** (1) **inbox aterriza** (su gate verde + commitea arch-tests) → entry embudo a `KNOWN_CROSS_FEATURE_INTERNAL_IMPORTS` → `gate-runner test-frontend` verde; (2) `/auditor`; (3) **demo Chris + `demo_signoff: APPROVED`** (probá: board → chip Congelados → Recuperar; Resumen de un lead = nombre completo + teléfono/correo + score correcto); (4) `/pm-vitalia merge`; (5) **FORENSE** (dod_live_verified falso · gate per-surface live-verify · HB-44). Story shell aparte: B1 root-cause (shell ssr:false) + U3 + P1-P5.

---

## TL;DR del estado

- **state:** `developed`. `dod_live_verified` quedó como **PARCIAL/engañoso**: board+writes SÍ verificados live; las sub-vistas (resumen/historial/nuevo/recuperar) NO se habían ejercido → al ejercerlas aparecieron crashes.
- **Sesión 4 cerró:** crash del Resumen (`autonomy.canDo`→`can/needsOk`, HB-44) FIXEADO + verificado live (board-live + resumen-live verdes contra dev-app). Pero la revisión UX live destapó MÁS.
- **Bloqueo estructural sin cambios:** (1) gate FE compartido RED por sesión **inbox** (viva, `developing`, no aterrizó); (2) `demo_signoff` de Chris pendiente.

## Lo que hizo la sesión 4 (commits en wip/vitalia, pusheados)

1. `efcd7d9a` — STOP /pm-vitalia: Blocker 1 sigue (inbox viva, no aterrizó). Diagnóstico del hub.
2. `ce7f0437` — **fix Resumen crash (HB-44):** FE `AutonomyInfo` realineado a contrato real BE (`operatedBy/can/needsOk`) + guard `?? []` · `AutonomyInfo` agregado a `CONTRACT_PAIRS` (gate anti-contrato-imaginado) · fixture `use-lead-detail.test.ts` corregido · `resumen-live.spec.ts` (live-verify del Resumen).
3. `98be10ff` — HB-44 en harness-backlog (reflex, SCOPE_GATE_SKIP documentado).
4. `49b8f773` — `resumen-live.spec` acepta `RESUMEN_LEAD_ID` (pin de lead agent-operated).
5. `dbb24cce` — chris-input: crash Juan Perez = bundle viejo en browser + forense agendada.

**Verificado live (dev-app real, Playwright authed):** board-live 9/9 (writes+DB) · resumen-live verde en lead `0d2313ff` Y `ba41e886` (Juan Perez, agent-operated → ejerce la rama de autonomía) · `base.ts` anti-burbuja verde · backend `GET /detail 200` sin Traceback.

---

## ★ HALLAZGOS ABIERTOS (lo que falta resolver — esto es el corazón del próximo trabajo)

### 🔴 BUGS reales (defectos, no "mejoras") — embudo lane (`code:crm`)

**B1 · `Recuperar` crashea entero.** `/{tenant}/adrian/embudo/recuperar` → `PAGEERROR: "Rendered more hooks than during the previous render"` → pantalla "This page couldn't load". Es el bug Next-16 soft-nav documentado en `docs/learnings/2026-06-03-next16-softnav-redirect-rendered-more-hooks.md` ([[next16-softnav-redirect-rendered-more-hooks]]) — hooks condicionales / orden de hooks que cambia entre renders. Superficie SHIPPEADA y rota; misma clase que el crash del Resumen. **Fix esperado:** estabilizar el orden de hooks de la vista Recuperar (`features/adrian/components/embudo/recuperar/` + su `page.tsx`); si es un `redirect()`/early-return in-render, mover el guard antes de cualquier hook o a edge. Repro: `RESUMEN_LEAD_ID` no aplica — navegar directo a `/recuperar` (soft-nav desde el board lo dispara).

**B2 · Score miente (10 vs 0).** Dominio computa `score=10` (docker `lead_score_computed score=10 lead_id=ba41e886`) pero el Resumen pinta `0` grande en "Puntuación del lead". Hipótesis: el número usa `lead.score` (almacenado, stale=0 para lead nuevo) mientras el breakdown usa los factores recién computados en `get_lead_detail` → glass-box inconsistente. **Fix esperado:** que el Resumen muestre el score COMPUTADO (mismo origen que los factores), no el stored. Ver `crm/application/services/funnel_service.py::get_lead_detail` (`self._scorer.compute(lead)` devuelve `(score, factors)` — el `score` computado debe ir al DTO/score, no `lead.score`). Verificar `LeadResponse.score` vs el computado. TDD: test que un lead con factores que suman 10 reporte 10 en el detail, no 0.

### 🟠 DECISIÓN UX de producto (necesita ratificación de Chris)

**U1 · Nombres del prospecto enmascarados en un embudo de ventas.** Cards `J*** P***`; Resumen rotula `Contacto: J*** P***`. Pero el checkpoint declara `phi_classification: non_phi` (lead = prospecto marketing, NO paciente). Un vendedor no puede operar un pipeline sin distinguir leads. **Recomendación (Claude):** mostrar **nombre completo** del prospecto en card + Resumen; el masking PHI real recién aplica cuando el lead se convierte en paciente (otra superficie). **Chris debe ratificar** antes de tocar (es revertir una decisión de masking, puede haber un motivo). Si ratifica → quitar el masking del nombre en `LeadCard` + `ResumenView` (probablemente `PiiMaskedSpan` sobre el nombre — cambiar por texto plano para el rol operador).

**U2 · Resumen sin datos de contacto.** En `/nuevo` se cargan teléfono + correo, pero el Resumen no los muestra → el vendedor entra al detalle y no tiene cómo contactar. **Fix esperado:** agregar teléfono + email a "Datos del lead" en `ResumenView` (con el masking real que corresponda al rol, NO sobre el nombre). Verificar que el DTO `LeadDetail`/`LeadResponse` exponga esos campos (si no, contract drift — agregar + registrar en `CONTRACT_PAIRS`).

**U3 · Splitter chat 55% fijo castiga el board.** El chat de Valeria ocupa ~55% fijo → el workspace del Embudo queda en ~40% (3 columnas kanban + scroll horizontal). Es shell-level (no embudo-específico) → **decisión + posible cambio cross-cutting** (afecta a todos los agentes). Default de splitter o memoria del último estado. NO meter en el batch del embudo sin pensar el impacto cross-tab. Probablemente → story shell aparte.

### 🟡 PULIDO (story separada — NO bloquea `done`)

- P1 · KPIs del board crípticos (`activos/humano/hot/cold/0% depósitos/congelados` — iconos minúsculos, sin tooltips/conteo claro).
- P2 · Empty-states honestos: score `0`→"Sin puntuación aún"; breakdown vacío sin texto; "Consulta agendada" sin badge de conteo (las otras sí).
- P3 · Chips "Etapa cambiada…" truncados en las cards.
- P4 · `+ Nuevo lead` perdido al final de la fila de filtros (acción primaria).
- P5 · Tab `Resumen/Historial` arriba-derecha texto chico, baja jerarquía.

(Screenshots de evidencia UX, untracked, en `vitalia/frontend/e2e/regression/vitalia-fase2-adrian-embudo/ux-shots/` — regenerables, ver receta abajo.)

### 🔵 BLOQUEO estructural (sin cambios desde sesión 3)

**Blocker-inbox · gate FE compartido RED.** La sesión **inbox** (`code:inbox`, viva, `developing`) no aterrizó: 6 unit ClerkProvider rojos (`AdrianInboxView`×5 + `ChannelBadge`×1) + FSD `AdrianInboxView → @/features/crm-shared` (su entry en `KNOWN_FSD_BOUNDARY_VIOLATIONS`) + sus 2 arch-tests **sin commitear** (`test_no_cross_feature_imports.test.ts`, `test_fsd_boundaries.test.ts`). El embudo necesita 1 entry propio en `KNOWN_CROSS_FEATURE_INTERNAL_IMPORTS` (`adrian/embudo/page.tsx → @/features/adrian/api/embudo-server`, Server-only) pero **no se puede landear sin enredar el WIP de inbox** (índice compartido). Chris decidió 2026-06-04: **inbox aterriza primero**. NO cruzar la lane inbox.

**demo_signoff** · Chris debe ejercer `demo-script.md` contra dev-app y firmar `demo_signoff: APPROVED` en checkpoint.

### 🔬 FORENSE del proceso (pedido Chris — al final, antes de cerrar todo)

Chris: *"me dijiste que lo verificaste pero realmente no fue así"*. Causa raíz preliminar:
1. La live-verify se declaró sobre la **superficie principal** (board+writes) y NUNCA cubrió las sub-vistas (resumen/historial/nuevo/recuperar) → 2 crashes vivían ahí.
2. Ni `/dev-team` (developed-boundary) ni `/auditor` (Phase D) enforced **"toda superficie user-reachable"** — la rule #37 lo dice en prosa pero ningún gate lo verifica por-superficie.
3. Contrato-imaginado (HB-42/44): registry de contract-parity manual → DTOs anidados (AutonomyInfo) invisibles.
**Entregable forense:** learning en `docs/learnings/tooling/` + fix de proceso (¿cómo el gate fuerza per-surface live-verify? p.ej. `04-validators` lista TODAS las rutas user-reachable de la story + dev-team/auditor deben ejercer cada una). HB-44 ya es el ancla.

---

## CAMINO A `done` (orden recomendado para la sesión nueva)

1. **Step 0 + hub:** `git log --oneline -6`, `git status --short`, `ls ~/Proyectos/luana-platform/.session-locks/`, `ps aux | grep claude`. Re-adquirir `code:crm`. Chequear si la **inbox aterrizó** (`cd vitalia/frontend && npx vitest run src/features/adrian/ src/__tests__/architecture/`).
2. **Bugs embudo (independientes del gate inbox — se pueden hacer YA):**
   - **B1 recuperar crash** (P0). Fix orden de hooks. Live-verify: navegar `/recuperar` (soft-nav desde board) → sin "Rendered more hooks" → `base.ts` verde. Agregar el caso a `resumen-live.spec` o un `recuperar-live.spec`.
   - **B2 score 10-vs-0** (P0/P1). Fix `get_lead_detail` para exponer score computado. TDD BE.
   - **U2 contacto en Resumen** + **U1 nombre sin masking** (SOLO si Chris ratificó U1). Si U1 toca el DTO → registrar el par en `CONTRACT_PAIRS`.
   - Re-correr gates: `tsc` + `eslint` + `vitest src/features/adrian/` + contract-parity + arch-fitness BE. Live-verify cada superficie tocada.
3. **Blocker-inbox:** cuando la inbox aterrice (sus tests verdes + arch-tests committeados) → agregar el entry embudo a `KNOWN_CROSS_FEATURE_INTERNAL_IMPORTS` → `gate-runner test-frontend` → `any_fail=false`. Si la inbox NO aterrizó, NO cruzar su lane — avisar a Chris.
4. **`/auditor` vitalia vitalia-fase2-adrian-embudo** (con gate verde): Phase D gherkin-matrix sobre la verificación REAL (board-live + resumen-live + recuperar-live + BE units). Auditor ejerce ≥1 write live. `CHECKPOINTS.md`.
5. **Avisar a Chris → demo** (`demo-script.md` contra dev-app, hard-reload primero) → `demo_signoff: APPROVED`.
6. **`/pm-vitalia merge`** → `07-merge.md` + cap `crm/adrian-embudo` (`cap_change_type: fix`/`extend`) + `git mv` story a `vitalia/docs/archive/2026/stories/` (mismo commit) + state `reviewing→done` + `make portfolio`. REFUSE si falta `dod_evidence` / gherkin MISSING / `demo_signoff` no APPROVED.
7. **FORENSE del proceso** (antes de cerrar): learning + fix de gate per-surface live-verify.
8. **Story de PULIDO UX** (P1-P5) + **U3 splitter** (shell) = stories separadas, NO bloquean este `done`.

## Reglas (sin cambios)

- Commit SOLO por pathspec exacto (`git commit -m "..." -- <rutas>`, mensaje ANTES del `--`). NUNCA `git add -A/-u/.` (índice compartido, sesión inbox viva). Archivo nuevo → `git add <ruta-exacta>` primero.
- `board-live.spec` + `resumen-live.spec` (real backend, `e2e/regression/`) = la verificación REAL. La mocked-smoke (`e2e/specs/.../embudo-*.smoke.spec.ts`) sigue DEFERIDA (overlay fixture authed-runtime, ver `T-E2E-1-result.md`).
- dev-app UP (`https://dev-app.vitalialat.com`). Creds en `vitalia/.env.dev` (`DEV_APP_TEST_*`, `CLERK_TESTING_TOKEN_VITALIA`, `E2E_TENANT_ID=e69a691d-070e-5caf-a053-6e74642ec100`). e2e contra dev-app (storageState es de ese dominio). FE container bind-montea ESTE worktree (footgun verificado OK).
- Chrome DevTools MCP: el browser está **lockeado por otra sesión** (userDataDir `luana-vitalia`) → usar Playwright authed para live-verify (no colisiona).
- "done" = gate verde REAL + `/auditor` APPROVED + `demo_signoff` APPROVED + merge. No marcar done sin los tres.

## Live-verify recipe (Playwright authed, real backend)

```bash
cd vitalia/frontend && set -a; source ../.env.dev; set +a
# Resumen de un lead específico:
RESUMEN_LEAD_ID=<lead-uuid> E2E_BASE_URL=https://dev-app.vitalialat.com \
  npx playwright test e2e/regression/vitalia-fase2-adrian-embudo/resumen-live.spec.ts --project=smoke --timeout=90000
# Board + writes:
E2E_BASE_URL=https://dev-app.vitalialat.com \
  npx playwright test e2e/regression/vitalia-fase2-adrian-embudo/board-live.spec.ts --project=smoke --timeout=90000
# Backend log check:
docker logs luana-dev-vitalia_backend_dev-1 --tail 40 2>&1 | grep -iE 'crm|ERROR|Traceback'
```

## Referencias
- `checkpoint.md` — frontmatter (state=developed, dod_live_verify con resumen ya agregado, open findings).
- `chris-input.md` — bitácora (tail = revisión UX + crash Juan Perez = bundle viejo).
- `T-E2E-1-result.md` — deferral mocked-smoke + gherkin coverage basis.
- `T-DEMO2-writes-result.md` — evidencia live de writes.
- `demo-script.md` — guion demo Chris.
- `docs/process/harness-backlog.md` — HB-44 (contrato-imaginado 2da instancia + per-surface live-verify gap).
- `docs/learnings/2026-06-03-next16-softnav-redirect-rendered-more-hooks.md` — B1.
- `ux-shots/` (untracked) — screenshots UX 5 superficies.
