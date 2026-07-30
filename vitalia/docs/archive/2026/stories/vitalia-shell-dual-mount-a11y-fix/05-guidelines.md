# 05-guidelines — vitalia-shell-dual-mount-a11y-fix

> Bugfix arquitectónico FE (ADR-011). Surface: shell-organism core. Builder: `builder-frontend` (Sonnet). Auditor: `auditor-frontend` (Opus).

## Files in scope (ÚNICOS editables)

| File | Acción |
|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx` | MODIFY — single-main + single-slot + D1-D5 |
| `vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayout.test.tsx` | REWRITE — borrar asserts triple-main; asertar single-main + single-slot |
| `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.test.tsx` | REVIEW/light — preservar contrato; opcional single-mount |
| `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx` | TOCAR SOLO SI el approach D2 lo requiere (probable: no) |

## Patterns REQUIRED

- **Single `<main id="main-content" tabIndex={-1} aria-label="Contenido principal">`** envolviendo TODAS las variantes (patrón nicolify D1). `containerRef` + `data-shell-ready` en ese `<main>` único.
- **`<AppPanelSlot>{children}</AppPanelSlot>` renderizado UNA sola vez** en el árbol (D2). Criterio duro: `querySelectorAll('[data-testid="app-panel-slot"]').length === 1` y `querySelectorAll('#main-content').length === 1` en CUALQUIER viewport/shellMode.
- **TODOS los hooks al tope, incondicionales, antes de cualquier branch** (D3). `useStoreHydration`, `useShellStore` selectors, `useViewportGuard`, `useRef`, `useState`×2, `useEffect`×2, `useGroupRef`, `useDefaultLayout`.
- **Gate desktop↔mobile por CSS `md:`** (no JS) — igual que nicolify (D4/D5).
- **`<Group>` resizable montado SIEMPRE** (oculto por CSS en mobile), nunca condicional por viewport JS.
- Header del componente: borrar "Triple-main pattern", documentar approach elegido (A o B de 03-arch § D2) + citar la lección nicolify (líneas 14-19 de su `ShellOrganismLayoutClient`).
- TDD: RED primero (reescribir test asertando single-main → falla contra triple-main actual) → GREEN (fix).
- Spanish neutro: preservar aria-labels existentes (tuteo, sin voseo).

## Patterns FORBIDDEN

- ❌ **Mount/unmount condicional del `<Group>` detrás de `isDesktop`/`useMediaQuery`/`useSyncExternalStore`** → React "Rendered more hooks than during the previous render" (CRASH probado por nicolify). Esta es LA prohibición central.
- ❌ Usar `useMediaQuery` para gobernar el layout del shell (D4 — NO se introduce `isDesktop` JS).
- ❌ Cualquier hook dentro de una rama JSX condicional (rompe hook-count).
- ❌ Dejar el `<AppPanelSlot>` en 2 ramas (lo que hace nicolify — vitalia debe ir más allá: single-slot).
- ❌ Múltiples `<main id="main-content">` (HTML inválido + a11y landmark dup).
- ❌ Tocar OTROS componentes/features: `useMediaQuery.ts`, `useViewportGuard.ts`, `ValeriaSidebar.tsx`, `Ribbon.tsx`, cualquier `features/*`.
- ❌ Tocar primitivas `components/ui/`.
- ❌ Tocar `core/luana-core-*/` (engine — fuera de alcance, requiere lift gate).
- ❌ Tocar `nicolify/` — aplicar el PATRÓN, NO compartir el archivo (arch gate mirror=0 debe seguir verde).
- ❌ Modificar `ShellOrganismLayout.tsx` (wrapper) salvo necesidad justificada — el skip-link arch test lo lee.
- ❌ Declarar "verificado" por GET 200 / suite mockeada — la verificación real exige ejercer lisa + valeria en dev-app y leer consola (test-design-doctrine § verificación REAL + ADR-008).

## must_load_skills

- `frontend-expert` — FSD-Lite, Server-First, live-verify gate, runtime-quality-checklist (useEffect deps, stale closures).
- `vitalia-design-system` — shell SSoT: 5 agentes Ribbon + Valeria supervisora, tokens, SHELL-DESIGN-CONTRACT. (★ canal único del builder-frontend; no hereda overlay.)
- `playwright-expert` — re-verificación transversal (5 agentes × 3 modos), axe, dev-app autenticado.
- `tessl__react-patterns` — hook-count stability / Rules of Hooks.
- `tessl__vitest` — jsdom window.matchMedia mock (solo si el componente lo consulta; D4 dice que no debería).
- `chrome-devtools-verify` — live verification dev-app (Chrome MCP) antes de cerrar developed.

## Rules a respetar

- `.claude/rules/frontend-fsd.md` (boundaries), `frontend-visual-fidelity.md` (D1/D2/D3 scope discipline), `frontend-quality.md` (tsc/eslint/vitest/arch).
- `.claude/rules/tdd-mandatory.md` (RED→GREEN), `tenant-isolation.md` (shell renderiza para todos los tenants), `spanish-text.md` (aria-labels neutro).
- `.claude/rules/definition-of-done-live-verify.md` (ADR-008 dev-app gate — superficie user-reachable).
- `.claude/rules/test-design-doctrine.md` (verificación real ≠ HTTP 200).

## Verification bar (DONE — del checkpoint)

1. 1 solo `<main id="main-content">` por viewport (no 3).
2. Cada `data-testid` del panel resuelve a 1 (E2E doctores sin `.filter({visible:true})`).
3. axe wcag2aa sin id-dup / landmark.
4. 5 agentes + valeria renderizan OK en agentic/web/mobile (vitest + visual smoke).
5. dev-app live: lisa + valeria desktop+mobile, consola sin hooks/hydration error, single main-content en DOM real.
6. Sin "more hooks than previous render" (lección nicolify).
