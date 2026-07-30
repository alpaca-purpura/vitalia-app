# HANDOFF — vitalia-bugfix-shell-nav-scroll-errors (para sesión nueva)

**Fecha:** 2026-06-02 · **Branch:** `wip/vitalia` @ `c11ceec6` · **Story state:** `developing` · `dod_live_verified: true` (técnico, 6/6) · **module bucket:** `shell`

## TL;DR
Bugfix de 6 bugs del shell-organism. **Código completo + verificado LIVE contra el stack real (6/6) + committeado/pusheado.** Falta para `done`: (1) tu `demo_signoff`, (2) rework de 6 e2e regression specs, (3) opcional Bug #7 live-trigger, (4) `/auditor`. NO está `done` todavía.

## Cadena ejecutada esta sesión
`/pm-vitalia` (ratificó scope idea→refined) → `/architect` (mapa causa raíz + ready package, refined→ready) → `/dev-team` (build + recovery + gates + live-verify, ready→developing).

## Los 6 fixes (todos aplicados + verificados live · ver 03-arch.md para el mapa de causa raíz por bug)
| Bug | Fix | Live |
|---|---|---|
| #1 routing 404 | `DEFAULT_LANDING_SUBPATH="mateo/agenda"` en `lib/shell-routes.ts`, consumido en 3 redirects (`app/page.tsx`, `(shell-organism)/page.tsx`, `(shell-organism)/layout.tsx`). Regresión de paradigm-map-zones (agenda migró valeria→mateo, redirects no se actualizaron) | ✅ lands mateo/agenda |
| #2 selector tenant | `useStoreHydration(useTenantStore)` en `ShellOrganismLayoutClient.tsx:108` (nunca se llamaba) | ✅ visible |
| #3 títulos redundantes | removido `<SubTabHeader>` del dispatcher `SubTabContent.tsx` + h2-eco en Identidad/VozTono/Presencia views; `SubTabHeader.tsx` borrado | ✅ sin eco |
| #4 scroll (ALTA) | `AppPanelSlot.tsx:65` content wrapper `overflow-hidden → overflow-y-auto` | ✅ overflow-y auto |
| #5 banner landing | borrado `InfoBannerLandingDescoped.tsx` + render/import/exports | ✅ sin banner |
| #7 error boundary (ALTA) | nuevo `(shell-organism)/[agent]/error.tsx` genérico (aísla error al panel, nav viva) | ⚠️ code-verified, live-trigger NO ejercido |

**Bug #6** (lisa/staff infinite loop) NO es de esta story → folded a `vitalia-fase2-lisa-doctores` (developing).
**lisa/staff `StaffDirectoryHeader` h1 "Staff"** = mismo patrón #3 pero NO tocado (es de lisa-doctores · non-egoísmo). Flag para esa story.

## Commits en wip/vitalia (HEAD c11ceec6)
- `132d17f6` fix: los 6 fixes (32 files)
- `98061462` docs: ready package (03-arch/04-validators/05-guidelines/06-tickets/dispatch-plan)
- `770f7356` docs: findings primera corrida
- `411ded51` docs: nota chrome MCP
- `c11ceec6` test: live-verify limpia + dod_evidence + `_live-verify.spec.ts`

## Gates verdes
tsc 0 source errors (ignora ruido `.next/dev/types` del route `lisa/staff/[doctor-id]` — pre-existente) · eslint clean · **vitest 2493/2493** · arch fitness 171/171.

## ★ APRENDIZAJES CRÍTICOS (leer antes de seguir)

1. **node_modules del CONTAINER estaba stale** → faltaban `sonner`/`react-window`/`react-hook-form` (deps declaradas+committeadas por stories en developing, pero el volumen del container nunca se reinstaló). El Toaster global (`ui/sonner.tsx`) rompía TODA ruta incl. `/sign-in` → Clerk no cargaba → e2e/auth fallaba. **Fix aplicado:** `docker exec -w /app luana-dev-vitalia_frontend_dev-1 pnpm install` + `docker restart luana-dev-vitalia_frontend_dev-1`. **Esto es recurrente y es DOMINIO de la story `estabilizar-harness-e2e-lisa-marca`** (dev-env/harness). Si el dev-app vuelve a romper con "Module not found" → repetir ese fix.

2. **El `Rendered more hooks` en mateo/agenda ERA artefacto del build roto** (deps faltantes → árbol React roto), NO un bug de React real. Con build limpio corre console-limpio. **Lección: cuando el build está roto (missing deps), los errores de React son red herrings — arreglá el build primero.**

3. **Chrome DevTools MCP ya está registrado** (user-scope `~/.claude.json`, `claude mcp list` = Connected, perfil persistente headful en `/home/chalreme/.cache/chrome-devtools-mcp/luana-vitalia`). PERO sus tools **no cargaron en la sesión resumida** (resume ≠ full restart). **En una conversación NUEVA (fresh start) los tools `mcp__chrome-devtools__*` SÍ deberían cargar** → podés hacer verify conversacional. Si no cargan: `ToolSearch "select:mcp__chrome-devtools__navigate_page"`; si vacío, el MCP no se cargó (revisar `/mcp`).

4. **e2e hybrid-mock = inválido.** Los 6 specs `bug{1,2,3,4,5,7}-*.spec.ts` mockean `/api/tenants` cliente mientras el shell resuelve tenants server-side → artefactos. **El patrón LIMPIO es `real-backend-forward.fixture.ts`** (real auth + forward `/api/v1/**` → :8002, sin mock) — usado en `_live-verify.spec.ts` que PASA 6/6. El rework debe convertir los 6 specs a ese patrón.

5. **builder-frontend corrió en worktree aislado + se colgó a mitad.** Recuperé su trabajo via patch scoped (`git apply`). Si volvés a spawnear builder + se cuelga: `git -C <worktree> diff HEAD` → patch → apply en luana-vitalia.

6. **Ruido residual pre-existente (NO de este fix):** backend 404 en `/api/v1/lisa/marca/{visuals,identity,contact,trust-catalog/PE,locations}` para el test tenant. Gaps reales del BE. Separado de esta story.

## QUÉ FALTA PARA `done` (orden sugerido)

1. **Rework de los 6 e2e regression specs** (`vitalia/frontend/e2e/regression/shell-nav-scroll/bug*.spec.ts`): convertir de hybrid-mock (`_fixture.ts` mockTenants) al patrón real-backend (`real-backend-forward.fixture.ts`, template = `_live-verify.spec.ts`). Para que el `runtime_error_gate` del auditor sea señal real. → builder-frontend (Sonnet). Borrar el `_fixture.ts` mockTenants si queda huérfano.
2. **(Opcional) Bug #7 live-trigger:** forzar un error client real en una hoja + verificar que `[agent]/error.tsx` renderiza el fallback en el panel con nav viva. Con Chrome MCP es más fácil (navegar + inyectar error).
3. **`/auditor vitalia vitalia-bugfix-shell-nav-scroll-errors`** — review técnico (Phase D gherkin-matrix + las 6 reglas RN-1..RN-6 de `04-validators.yaml`). Verificará `dod_evidence` (ya poblado).
4. **`demo_signoff` de Chris** (`demo-script.md`): Chris ejerce los 6 bugs en dev-app + firma. Gate de NEGOCIO §5, separado del auditor. Ambos requeridos para done.
5. **`/pm-vitalia merge`** → `reviewing → done`: 07-merge.md + cap ledger (cap_change_type=fix → change_log en `shell-organism.shell-vitalia` + `brand_studio.lisa-marca` para #3/#5) + `git mv` story a `vitalia/docs/archive/2026/stories/`.

## Verificación rápida del stack (correr al arrancar)
```bash
cd ~/Proyectos/luana-vitalia
git log --oneline -3                      # HEAD debe ser c11ceec6 (o más)
docker ps | grep vitalia                  # stack up?
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3002/sign-in   # 200 = build OK; si build error → pnpm install en container (aprendizaje #1)
# Live-verify (re-correr para confirmar): el storageState Clerk expira (>1h) → la setup re-autentica sola si /sign-in buildea
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/shell-nav-scroll/_live-verify.spec.ts --project=smoke --workers=1
```

## Archivos clave de la story
`vitalia/docs/product/stories/vitalia-bugfix-shell-nav-scroll-errors/`: `checkpoint.md` (estado + dod_evidence) · `03-arch.md` (causa raíz) · `04-validators.yaml` (RN-1..6 + scenario_coverage) · `06-tickets.yaml` (T-1..T-6) · `VERIFICATION-FINDINGS.md` (resultados live) · `BUILD-LOG.md` · `demo-script.md` (para Chris) · `chris-input.md` (conversación).
