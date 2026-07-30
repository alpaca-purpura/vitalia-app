# T-2 result — Chrome layout (vitalia-shell-core-hardening)

**Ticket:** T-2 · **Surface:** FE · **Brand:** vitalia · **Agent:** builder-frontend (sonnet)
**State:** `pushed` · **Date:** 2026-06-10
**Branch:** `wip/vitalia`
**Commits:** `b19a227d` (TopBar block #1, sesión previa) + `b522043a` (layout/guard/historial/retire, esta sesión)

---

## Deliverables (06-tickets T-2)

| # | Deliverable | Estado | Dónde |
|---|---|---|---|
| 1 | ShellOrganismLayoutClient: máquina nueva; quitar ShellModeToggle/web-grid/rail 60px; historial empuja 260; ssr:false conservado; gate desktop↔mobile CSS | ✅ | `ShellOrganismLayoutClient.tsx` — single always-mounted `<Group>`; web-grid ternary + 60px rail + ShellModeToggle import REMOVIDOS; ssr:false preservado; Separator `hidden lg:block` + isLg matchMedia snap-up (gate CSS, no JS conditional mount → evita "Rendered more hooks") |
| 2 | TopBarGlobal: cluster derecho [ThemeToggle][TenantSwitcher]; sin chip; skeleton variant conservado | ✅ | `TopBarGlobal.tsx` (commit `b19a227d`) — TenantSwitcher tras ThemeToggle, chip eliminado, skeleton variant intacto |
| 3 | RETIRE ShellModeToggle.tsx | ✅ | `git rm` ShellModeToggle.tsx + ShellModeToggle.test.tsx |
| 4 | useViewportGuard: clamp 320; drawer 1024; sin 620/rail | ✅ | `useViewportGuard.ts` — store-inert no-op; exporta `VALERIA_MIN_PX=320` / `DRAWER_BREAKPOINT=1024` / `INLINE_SPLIT_MIN_VIEWPORT=1280`; legacy `FULL_STATE_MIN_VIEWPORT=1104` + `MOBILE_BREAKPOINT=768` eliminados |
| 5 | ValeriaHistory: 260px fijo empuja | ✅ | `ValeriaHistory.tsx` — nav `lg:w-[260px] shrink-0` (empuja inline desktop ≥lg; `w-full` apilado en drawer mobile <lg) |

---

## Acceptance checks (06-tickets T-2)

| Check | Resultado |
|---|---|
| `vitest: TopBar orden + useViewportGuard clamp/drawer + ValeriaHistory empuja` | ✅ TopBarGlobal 24/24 · useViewportGuard 11/11 · ValeriaHistory +2 SC-14 (w-[260px] + shrink-0) |
| `arch grep shellMode/ShellModeToggle = 0` | ✅ 0 refs en código de producción. Único hit: `shell-store.ts:108` `shellMode?` dentro de `LegacyPersistedState` (shape de input del `migrateShellState()` v0→v1 que lo DROPea) — correcto, no es regresión |
| `tsc + eslint verde` | ✅ tsc 0 errores · eslint shell-organism clean |

---

## Gates output

```
tsc --noEmit ............................ GREEN (0 errors)
eslint src/components/shared/shell-organism/ ... GREEN (0)
vitest src/components/shared/shell-organism/ ... 515/515 PASS (32 files)
  · ShellOrganismLayout.test.tsx .......... 21/21
  · useViewportGuard.test.ts .............. 11/11
  · ValeriaHistory.test.tsx ............... 22/22 (+2 SC-14 T-2)
  · TopBarGlobal.test.tsx ................. 24/24 (block #1)
  · shell symbol ratchet ................. GREEN (unsanctioned mirrors = 0)
arch grep shellMode/ShellModeToggle (prod) ..... 0
```

**Fuera de scope (no bloquean T-2):** 4 fallos en `src/__tests__/architecture/test_fsd_boundaries.test.ts` + `test_no_cross_feature_imports.test.ts` — todos en `features/inbox/` (bucket `code:inbox`, sesión concurrente; el dir ni existe en disco, allowlist referencia files aún no creados). Ninguno toca `components/shared/shell-organism/`. T-2 no edita `features/inbox/` (cross-bucket pollution prohibido).

---

## gherkin_coverage

SC-2 · SC-3 · SC-6 · SC-9 · SC-10 · SC-14 (declarados en 06-tickets; cobertura unit a nivel componente; verificación funcional live = fase orchestrator/auditor)

---

## Decisiones de scope

- **ValeriaSidebar (T-1 legacy bridge):** sin cambio de código. El "empuja 260" lo implementa el ancho propio de `ValeriaHistory` (`lg:w-[260px] shrink-0`), NO la columna del grid del bridge. La migración del grid del bridge + tira-avatar 44px son **T-3** (confirmado en 06-tickets). Se dejó un comentario de scope en `ValeriaSidebar.tsx` documentando por qué el grid del bridge queda en 280 (diferido a T-3). Net code = idéntico a T-1 baseline.
- **No se tocó:** `components/ui/`, `fetchClient.ts`, `nicolify/`, `core/luana-core-*/src/`, `core/@luana/ui-kit/src/**`, contenido de sub-tabs (`features/*/components/**`).
- **GUARD respetados:** ssr:false conservado · gate desktop↔mobile via CSS (no JS) · sin bump de Next · sin nuevos edge-redirects (eso es T-4) · historial NO persiste conversaciones reales (mock data, no-PHI).

---

## Skills consulted

| Skill / Rule | Por qué invocada | Decisión tomada (cita) |
|---|---|---|
| `frontend-expert` (`references/runtime-quality-checklist.md`) | always-on FE | Group SIEMPRE montado + gate CSS (no mount condicional) per checklist "useEffect deps / stale closures / Rendered more hooks"; useViewportGuard store-inert (no deriva state en effect) |
| `vitalia-design-system` | wrapper chrome del shell-organism | TopBar cluster + ValeriaSidebar/History se arman de átomos `components/ui/` existentes (Button/Input); tokens semánticos `border-border`; sin reinventar primitivas |
| `.claude/rules/frontend-visual-fidelity.md` (D1/D2/D3) | FE build | D1 design-system-first (reutilizar Shadcn `components/ui/`); D3 scope discipline (solo deliverables T-2; ValeriaSidebar grid + tira-avatar = T-3, NO construidos) |
| `.claude/rules/frontend-fsd.md` | boundary matrix | shell-organism vive en `components/shared/`; named exports (no default); 0 cross-feature imports en mi set |
| `.claude/rules/tdd-mandatory.md` | tests-first | RED→GREEN por bloque: useViewportGuard.test (contrato constantes + store-inert) RED antes de quitar legacy consts; ValeriaHistory SC-14 RED antes de `w-[260px]` |
| `.claude/rules/spanish-text.md` | microcopy chrome | strings UI neutro LatAm (sin voseo): "Conversaciones", "Buscar conversación...", aria-labels |
| Shadcn UI conventions | átomos | Button/Input de `components/ui/` reutilizados; cero recreación de primitivas |
| Tailwind conventions | estilo | utility-first + `cn()`; responsive `lg:w-[260px]` / `hidden lg:block`; sin inline `style={{}}` |
| `ADR-vitalia-004` / `ADR-vitalia-006` | patrón shell | shell-organism wrapper (no sub-tab), N3-static aplica a T-3; ssr:false conservado |

**Live verification:** NO ejercida en esta fase (chrome wrapper sin write/endpoint; verificación live del shell completo = fase orchestrator → auditor-frontend → demo Chris en G). El render del layout se cubre por vitest a nivel componente (515/515). Si el orchestrator requiere live-verify del shell montado → `chrome-devtools-verify` sobre dev-app.vitalialat.com.

---

## Archivos tocados (9)

```
M  ShellOrganismLayoutClient.tsx        (block #2)
M  ShellOrganismLayout.test.tsx         (block #2 — mock constants + drop ShellModeToggle test)
M  useViewportGuard.ts                  (block #2)
M  useViewportGuard.test.ts             (block #2)
M  ValeriaHistory.tsx                   (block #2)
M  ValeriaHistory.test.tsx              (block #2 — +2 SC-14)
M  ValeriaSidebar.tsx                   (block #2 — comentario de scope; net code = T-1)
D  ShellModeToggle.tsx                  (RETIRE)
D  ShellModeToggle.test.tsx             (RETIRE)
+ block #1 (commit b19a227d): TopBarGlobal.tsx + .test.tsx + __tests__/no-store-in-ssr-skeleton.test.tsx
```
