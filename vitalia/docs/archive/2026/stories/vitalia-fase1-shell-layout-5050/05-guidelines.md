<!-- voseo-allowed: glosario reference + internal guidelines -->

---
story_id: vitalia-fase1-shell-layout-5050
brand: vitalia
type: ui-story
phase: fase-1
last_modified: 2026-05-23
architect_iter: 1
---

# F1-S4 `vitalia-fase1-shell-layout-5050` — 05-guidelines.md

## § 1 — Must-load skills (builder bootstrap obligatorio)

`builder-frontend` (Sonnet/opencode) MUST cargar estos skills en bootstrap ANTES de tocar código. Enforcement: `/dev-team` Step 0 verifica.

| Skill | Cuándo cargar | Por qué |
|---|---|---|
| `frontend-expert` | Bootstrap T-1 (siempre primero) | FSD-Lite boundaries, Server-First, "use client" solo hojas con state, Vitest unit patterns, runtime quality checklist (useEffect deps, stale closures, hydration safety) |
| `playwright-expert` | T-7 (E2E specs + visual goldens) | Clerk auth fixture pattern (REUSE F1-S3), POM patterns, addInitScript determinism, visual goldens `--update-snapshots` iter 1 protocol, port 3002 vitalia, freshness gate, anti-patterns |
| `tessl__react-patterns` | T-3 (ShellOrganismLayout) | Server vs Client Component decision tree, hydration safety con zustand persist (sync no SSR mismatch en client leaf), `useEffect` cleanup en `useViewportGuard` |
| `tessl__shadcn-ui` | T-3 (resize integration) | Shadcn `Resizable` underlying lib = `react-resizable-panels` v4 API: `PanelGroup`/`Panel`/`PanelResizeHandle`. Verify CLI versión + scaffolds. (See § Resize implementation contract.) |
| `tessl__tailwind` | T-2/T-3/T-5 (any component touching shell tokens) | Semantic tokens via globals.css CSS vars (Design Contract §5.1). Tokens permitidos: `bg-background`, `bg-card`, `bg-muted`, `text-foreground`, `text-muted-foreground`, `border-border`, `bg-primary`, `text-primary-foreground`, `ring-ring`, `bg-secondary`. NO hex literals. NO arbitrary values salvo aria-test surface |
| `tessl__vitest` | T-1/T-2/T-3/T-5/T-6 (todos los unit tests) | RTL + `@testing-library/jest-dom` + `vi.mock` patterns. Mock `useShellStore` via direct `useShellStore.setState` o `vi.mocked()`. Colocated test files `__tests__/` sibling |
| `tessl__nextjs-app-router-modularization` | T-4 (route group + dynamic [tenantId]) | Server Components default in app/, redirect() server-side semantics, route group naming (parens) conventions, dynamic segments (`[tenantId]`) propagation via params |
| `claude-md-management` | Cuando dudes en project-level invariants | Tenant isolation upstream, Spanish neutro |

### NO cargar (out-of-scope)

`backend-expert`, `copilot-expert`, `sales-agent-expert`, `offer-expert`, `brand-expert`, `metrics-expert`, `offer-type-preset-expert` — story es FE only chrome UI sin BE/agentic/dominio negocio.

## § 2 — Must-load rules (overlay vitalia + raíz)

| Rule | Trigger |
|---|---|
| `.claude/rules/frontend-fsd.md` (raíz) | shell-organism es `components/shared/` cross-feature — boundary matrix vital |
| `.claude/rules/frontend-quality.md` (raíz) | ESLint 60+ rules, TS strict, Vitest threshold |
| `.claude/rules/spanish-text.md` (raíz) | strings UI sin voseo (glosario referencial) — aria-labels + tooltips |
| `.claude/rules/tenant-isolation.md` (raíz) | URL `[tenantId]` propaga via Next routing — middleware Clerk gates upstream (no FE filter aquí) |
| `.claude/rules/anti-duplication.md` (raíz) | cross-brand mirror scan ya ejecutado pre-arch (§ 0.1 audit clean — 0 matches) |
| `.claude/rules/tdd-mandatory.md` (raíz) | RED tests primero por capa: store → slots → layout → page → mode toggle |
| `.claude/rules/e2e-testing.md` (raíz) | Playwright NATIVE Linux (no docker), port 3002 vitalia, preflight obligatorio |
| `vitalia/.claude/rules/shell-mockup-per-component.md` (overlay) | visual goldens side-by-side mockup HTML ratificado · ratchet shrink-only |
| `vitalia/.claude/rules/hipaa-lite.md` (overlay) | scope: declarar `hipaa_lite_scope: not_applicable` — UI shell sin PHI |

## § 3 — Patterns required (debe usarse)

1. **Server Components default.** Solo agregar `'use client'` en hojas que consumen `useShellStore` (hook → Client-only), event handlers DOM (resize drag), o effects con `window` (`useViewportGuard`). Per § 2.10 03-arch.md decision tree.

2. **Named exports (no default exports)** salvo Next.js pages (`page.tsx`, `layout.tsx`) que requieren default export por convention App Router. Arch ratchet `test-no-default-export.test.ts` enforce.

3. **Zustand persist con `partialize` ambos campos** — `valeriaState` + `shellMode` AMBOS persistidos (no transient state). Mirror del template F1-S3 `tenant-store.ts`. Storage key `vitalia-shell-state` (const exportada).

4. **react-resizable-panels v4 API** — `PanelGroup` + `Panel` + `PanelResizeHandle`. Pass `id` to every Panel + `autoSaveId="vitalia-shell-split-agentic"` to PanelGroup → lib auto-persiste split via `localStorage`. NO custom drag handler — usar lib built-in keyboard nav (ArrowLeft/Right step 16px native).

5. **Semantic tokens Tailwind** — solo `bg-background`/`bg-card`/`bg-muted`/`text-foreground`/`text-muted-foreground`/`border-border`/`bg-primary`/`text-primary-foreground`/`ring-ring`/`bg-secondary`. Tokens definidos en `globals.css` (Design Contract §5.1). NO hex (`#01b2f8`) ni arbitrary values salvo si requerido por aria-test data-attr fixture.

6. **Aria-labels en Spanish neutro** — `aria-label="Redimensionar paneles"`, `aria-label="Panel Valeria (placeholder — F1-S5/S6 lo construirá)"`, `aria-label="Panel aplicación (placeholder — F1-S7/S8/S10 lo construirá)"`, `aria-label="Contenido principal"`, `aria-label="Modo de shell: {agentic|web} activo"`. Sin voseo (`tú`/`tienes`, no `vos`/`tenés`).

7. **Skip-link target invariant** — `<main id="main-content" tabIndex={-1} aria-label="Contenido principal">`. Root layout (`app/layout.tsx`) ya tiene `<a href="#main-content">Saltar al contenido</a>` — esta story provee el target. Arch test `test-skip-link-target.test.ts` enforce.

8. **CSS-driven viewport branching (no JS detection inicial)** — usar Tailwind `md:hidden`/`md:block`/`md:grid` para alternar entre 3 `<main>` mutually-exclusive. Solo UN `<main>` visible per viewport. Evita hydration mismatch SSR/CSR cuando viewport difiere.

9. **`useViewportGuard` hook one-way force** — guard SOLO degrada `'full' → 'rail'` cuando viewport [768-1023]. NO restore automatic cuando viewport vuelve a >=1104 — eso queda explicit decisión del user (rail button F1-S5). Debounced via `requestAnimationFrame` (no lodash dep).

10. **Default `valeriaState: 'full'`** — override de DC §6.1 (que dice `'rail'`). Razón en 03-arch.md § 2.5.1. `/pm-vitalia` actualiza DC §6.1 post-merge.

11. **`data-testid` selectors para Playwright** — `topbar-global` (heredado F1-S2), `valeria-sidebar-slot`, `app-panel-slot`, `shell-mode-toggle`. react-resizable-panels expone `[data-resize-handle="true"]` nativo — usar ese, no inventar `data-testid`.

12. **Mockup HTML side-by-side iter 1 golden generation** — T-7 monta mockups en `python3 -m http.server 8888 vitalia/docs/product/stories/vitalia-fase1-shell-layout-5050/mockups/` y abre side-by-side con componente real `localhost:3002`. Solo cuando Chris ratifica visual: `npx playwright test --update-snapshots --project=visual`. Ratchet shrink-only post-ratify (per `shell-mockup-per-component.md`).

13. **TDD RED-first per ticket** — test falla ANTES de implementar GREEN. Orden:
    - T-1: `shell-store.test.ts` RED → import fails → impl `shell-store.ts` GREEN
    - T-2: `ValeriaSidebarSlot.test.tsx` + `AppPanelSlot.test.tsx` RED → impl Server Components GREEN
    - T-3: `useViewportGuard.test.ts` + `ShellOrganismLayout.test.tsx` RED → impl hook + layout GREEN
    - T-4: page.tsx redirect test (next/navigation mock) RED → impl page GREEN
    - T-5: `ShellModeToggle.test.tsx` RED → impl chip GREEN
    - T-7: Playwright specs RED (route 404 antes de page.tsx ready) → all ON GREEN once T-1..T-5 mergeable

14. **Spanish neutro check (pre-commit hook)** — todos los strings UI revisados verbatim. Si commit hook bloquea, ver glosario `.claude/rules/spanish-text.md`. NO usar magic comment `<!-- voseo-allowed -->` en source files (solo en mockups/docs/tests).

15. **Hydration safety** — zustand `persist` es sync on client mount; no SSR mismatch porque `'use client'` leaf renderiza después de hidratación inicial. Si Vitest test pasa SSR + CSR sin warning, safe.

## § 4 — Patterns forbidden (NO usar)

1. **Hex literals** (`#01b2f8`, `#7b2d91`, `#ffffff`) en JSX/CSS — usar tokens semánticos (`bg-primary`, `bg-accent`, `bg-background`).

2. **`any` TypeScript** — strict mode. Si necesitás escape, usa `unknown` + type guard.

3. **Default exports** salvo `page.tsx`/`layout.tsx` Next.js (App Router requirement).

4. **Editar archivos REUSE F1-S1/S2/S3** — `TopBarGlobal.tsx`, `LogoMark.tsx`, `ThemeToggle.tsx`, `TenantSwitcher.tsx`, `TenantOption.tsx`, `TenantBadge.tsx`, `TenantStoreBootstrap.tsx`, `AddClinicPlaceholderModal.tsx`, `tenant-store.ts` — todos PRESERVED intact. Si necesitás cambio, escala a /po-ux → nueva story.

5. **Editar `components/ui/` Shadcn primitives** — copy-paste local, no upstream upgrade en este story. Si la version v4 de react-resizable-panels requiere update de algún Shadcn component (no necesario por scope F1-S4), se hace en story separada.

6. **Cross-feature imports en shell-organism** — `components/shared/shell-organism/*` NO debe importar `features/*`. FSD boundary matrix raíz (`frontend-fsd.md`). Arch test `test-fsd-imports.test.ts` enforce.

7. **Cross-brand imports** — vitalia frontend NUNCA importa `nicolify/`, `comunify/`, `lupulo/`. Arch test `test-no-cross-brand-shell-mirror.test.ts` enforce.

8. **Editar `app/(dashboard)/` legacy** — coexiste paralelo per D3 SHELL-DESIGN-CONTRACT. Phase 2 lo deprecate. Tocar = scope creep.

9. **Hardcodear `tenantId`** — siempre via `params.tenantId` (server) o URL pathname parsing (client si necesario; en F1-S4 no necesario).

10. **`router.push()` cuando un redirect** server-side — usar `redirect()` desde `next/navigation` en Server Components. Hard refresh consistente per pattern F1-S3 (tenant-switcher).

11. **Custom resize hook reinventando react-resizable-panels** — adoptamos lib (option A 03-arch.md § 2.9). Si la lib falla, escalate antes de reinventar.

12. **`window.matchMedia` / `window.innerWidth` durante render** — usar solo en `useEffect` (post-mount). Render branching solo via Tailwind responsive classes. Reglar evitar hydration mismatch.

13. **`useState` para shellMode/valeriaState** — usar `useShellStore` siempre. Local state duplicate inválida fuente verdad.

14. **`useMemo` for derived shellMode** sin razón concreta — premature optimization. Lectura zustand selector `useShellStore(s => s.shellMode)` ya optimizado por la lib.

15. **Logging via `console.log`** — usar `console.warn` solo para edge cases dev (Scenario hostile minViewport detected). No `Sentry` custom span en F1-S4.

16. **Magic comment `<!-- voseo-allowed -->` en source `.tsx` files** — solo en mockups/rules/tests fixtures donde se cita glosario. Source code prod sin voseo.

## § 5 — Files in scope (dev-team puede tocar)

### Archivos NEW (sí permitido crear)

```
vitalia/frontend/src/app/[tenantId]/(shell-organism)/layout.tsx                      # T-4
vitalia/frontend/src/app/[tenantId]/(shell-organism)/page.tsx                        # T-4
vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayout.tsx        # T-3
vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.tsx         # T-2
vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx               # T-2
vitalia/frontend/src/components/shared/shell-organism/ShellModeToggle.tsx            # T-5
vitalia/frontend/src/components/shared/shell-organism/useViewportGuard.ts            # T-3
vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayout.test.tsx   # T-3
vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.test.tsx    # T-2
vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.test.tsx          # T-2
vitalia/frontend/src/components/shared/shell-organism/ShellModeToggle.test.tsx       # T-5
vitalia/frontend/src/components/shared/shell-organism/useViewportGuard.test.ts       # T-3
vitalia/frontend/src/stores/shell-store.ts                                            # T-1
vitalia/frontend/src/stores/__tests__/shell-store.test.ts                             # T-1
vitalia/frontend/src/__tests__/architecture/test-skip-link-target.test.ts             # T-6
vitalia/frontend/src/__tests__/architecture/test-shell-store-schema.test.ts           # T-6
vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts  # T-6
vitalia/frontend/e2e/pages/ShellLayoutPage.ts                                         # T-7
vitalia/frontend/e2e/fixtures/shell-theme.fixture.ts                                  # T-7
vitalia/frontend/e2e/regression/vitalia-fase1-shell-layout-5050/render-agentic-default.spec.ts  # T-7
vitalia/frontend/e2e/regression/vitalia-fase1-shell-layout-5050/mobile-collapse.spec.ts          # T-7
vitalia/frontend/e2e/regression/vitalia-fase1-shell-layout-5050/resize-and-state.spec.ts         # T-7
vitalia/frontend/e2e/regression/vitalia-fase1-shell-layout-5050/a11y-keyboard.spec.ts            # T-7
vitalia/frontend/e2e/regression/vitalia-fase1-shell-layout-5050/visual-goldens.spec.ts           # T-7
vitalia/frontend/e2e/__screenshots__/shell-layout-5050/*.png                                       # T-7 iter 1 (--update-snapshots, ratified Chris)
```

### Archivos MODIFY (sí permitido editar puntualmente)

```
vitalia/frontend/package.json                            # T-3 — add `react-resizable-panels: ^4.11.1` dep
vitalia/frontend/pnpm-lock.yaml                          # T-3 — lockfile auto-update
vitalia/frontend/src/__tests__/architecture/test-fsd-imports.test.ts        # T-6 — extend allowlist (shrink only, justify)
vitalia/frontend/src/__tests__/architecture/test-no-default-export.test.ts  # T-6 — extend allowlist (shrink only, justify)
```

### Archivos NEVER touch (HARD FAIL si tocás)

```
vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx        # F1-S2 done — REUSE
vitalia/frontend/src/components/shared/shell-organism/LogoMark.tsx            # F1-S2 done — REUSE
vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.tsx         # F1-S1 done — REUSE
vitalia/frontend/src/components/shared/shell-organism/TenantSwitcher.tsx      # F1-S3 done — REUSE
vitalia/frontend/src/components/shared/shell-organism/TenantOption.tsx        # F1-S3 done — REUSE
vitalia/frontend/src/components/shared/shell-organism/TenantBadge.tsx         # F1-S3 done — REUSE
vitalia/frontend/src/components/shared/shell-organism/TenantStoreBootstrap.tsx  # F1-S3 done — REUSE
vitalia/frontend/src/components/shared/shell-organism/AddClinicPlaceholderModal.tsx  # F1-S3 done — REUSE
vitalia/frontend/src/stores/tenant-store.ts                                   # F1-S3 done — REUSE
vitalia/frontend/src/components/ui/*                                          # Shadcn primitives — copy-paste local, no upstream upgrade
vitalia/frontend/src/app/(dashboard)/**                                       # LEGACY — coexiste paralelo (D3)
vitalia/frontend/src/app/(auth)/**                                            # LEGACY auth
vitalia/frontend/src/app/(app)/**                                             # LEGACY
vitalia/frontend/src/app/onboarding/**                                        # LEGACY onboarding
vitalia/frontend/src/app/marketing/**                                         # LEGACY public marketing
vitalia/frontend/src/app/public/**                                            # LEGACY public
vitalia/frontend/src/app/layout.tsx                                           # F1-S2 deployed — root layout, NO modify (skip-link ya correcto)
vitalia/frontend/src/app/providers.tsx                                        # NO modify
vitalia/frontend/src/app/globals.css                                          # F1-S1 deployed tokens — NO modify
nicolify/**, comunify/**, lupulo/**                                          # CROSS-BRAND HARD BAN per anti-duplication.md
core/luana-core-*/**                                                          # ENGINE — promotion gate /pm-luana required
vitalia/backend/**                                                            # BE out-of-scope
vitalia/.claude/**, .claude/**                                                # meta — no modify
vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md                            # touchable only por /pm-vitalia post-merge (DC §6.1 default update)
```

## § 6 — Reference artifacts (consulta on-demand)

| Artifact | Path | Cuándo consultar |
|---|---|---|
| 01-spec.md (contract Gherkin + acceptance) | `vitalia/docs/product/stories/vitalia-fase1-shell-layout-5050/01-spec.md` | Antes empezar cada ticket — re-leer scenario relevante + AC table |
| 03-arch.md (architecture + decisions) | `vitalia/docs/product/stories/vitalia-fase1-shell-layout-5050/03-arch.md` | Decisions ambiguas (default valeriaState, resize lib, viewport guard, ShellModeToggle mount, file tree) |
| 04-validators.yaml § test_construction_plan | mismo path | Orden creation + poms + fixtures + scenario_to_test mapping |
| Mockup HTML agentic | `vitalia/docs/product/stories/vitalia-fase1-shell-layout-5050/mockups/shell-layout-agentic.html` | Visual goldens side-by-side T-7 iter 1 + microcopy verbatim |
| Mockup HTML web | mismo dir | Visual goldens web mode |
| SHELL-DESIGN-CONTRACT.md | `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` | §3.4 (`ShellOrganismLayout` template) + §5.1 (tokens CSS vars) + §6.1 (`shellStore`) + §8 (a11y per organism) + §9 (testing strategy) + §10 (story → component mapping) |
| ADR worktree shell mockup protocol | `vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md` | Visual goldens iter protocol + ratchet shrink-only rules |
| Prior F1-S3 ticket template | `vitalia/docs/archive/2026/stories/vitalia-fase1-tenant-switcher/06-tickets.yaml` | Reference para ticket format (acceptance.validator_ids, gherkin_coverage, files structure) |

## § 7 — Verification commands (reproducible local)

Cuando termines un ticket, corré local antes commit:

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend

# Per-ticket fast feedback:
npx tsc --noEmit
npx eslint src/components/shared/shell-organism src/stores src/app/[tenantId] src/__tests__/architecture --cache

# Per-ticket Vitest:
npx vitest run src/components/shared/shell-organism src/stores src/__tests__/architecture --reporter=default

# T-7 E2E (asume make dev-vitalia corriendo background):
bash ${WS}/scripts/e2e-preflight.sh
E2E_BASE_URL=http://localhost:3002 npx playwright test regression/vitalia-fase1-shell-layout-5050/
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=visual regression/vitalia-fase1-shell-layout-5050/visual-goldens.spec.ts

# Full validators (pre-handoff a /auditor):
make ci-parity                                                                              # opcional pre-push main
```

## § 8 — Auditor handoff expectations

When `state: developed`, `/dev-team` emits AUTO-HANDOFF to `/auditor` (per `story-closure-gate.md`). Auditor will:

1. Re-run `gate-runner` con todos los validators (§ 04-validators.yaml).
2. **C1 Code review** — Cat 1 FSD-Lite imports, Cat 9 PII (N/A here, declared), Cat 10 tests/TDD, Cat 12 anti-duplication (cross-brand mirror scan), Cat 17 SSoT artifact integrity (visual goldens path match arch + spec).
3. **C2 Spec coverage** — Phase D Gherkin verification matrix (`06-audit/gherkin-matrix.md`): 4 scenarios → tests pasados.
4. **C3 Architecture coverage** — § Architectural fitness § 4 03-arch.md + new arch tests.
5. **C4 Cross-cutting** — Spanish neutro check (pre-commit hook + manual review en aria-labels), HIPAA-lite N/A declaration cited.
6. **C5 Trace** — visual goldens 6 PNGs match mockups ratificados Chris (side-by-side check vía `python3 -m http.server 8888 vitalia/docs/product/stories/vitalia-fase1-shell-layout-5050/mockups/`).

Auditor self-fix policy (`.claude/rules/auditor-self-fix-policy.md`): whitelist trivial fixes (typo Spanish, missing aria-label) OK. Lógica/branch/refactor → spawn dev-team Caso B.

## § 9 — Anti-creep (post-story scope)

When `state: done` and merged:

- **F1-S5** (`valeria-rail-history`) REPLACE `ValeriaSidebarSlot.tsx` con `ValeriaSidebar.tsx` real (rail buttons + history fetch + keyboard shortcuts). Importa `useShellStore`.
- **F1-S6** (`valeria-chat-skeleton`) extiende ValeriaSidebar interno con ChatHeader + messages + composer.
- **F1-S7** (`ribbon-6-tabs`) REPLACE `AppPanelSlot.tsx` con Ribbon + ContentArea real.
- **F1-S8** (`sub-tabs-line2`) extiende AppPanelSlot.
- **F1-S9** (`routing-shell`) crea `app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx` consumiendo whitelist `shell-routes.ts`.
- **F1-S10** (`empty-states`) populates 22 sub-tab pages cada una con su EmptyState.
- **F1-S5/S7** activan `ShellModeToggle` interactivo (remove `disabled` attr, wire `setShellMode`).

Si necesitás algo que cae fuera de § 5 files in scope → STOP, escalar a `/pm-vitalia` para crear ticket adicional o re-decompose.

