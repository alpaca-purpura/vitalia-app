<!-- voseo-allowed: glosario reference + internal guidelines -->

---
story_id: vitalia-fase1-valeria-rail-history
brand: vitalia
type: ui-story
phase: fase-1
last_modified: 2026-05-24
architect_iter: 1
---

# F1-S5 `vitalia-fase1-valeria-rail-history` — 05-guidelines.md

## § 1 — Must-load skills (builder bootstrap obligatorio)

`builder-frontend` (Sonnet/opencode/qwen) MUST cargar estos skills en bootstrap ANTES de tocar código. Enforcement: `/dev-team` Step 0 verifica.

| Skill | Cuándo cargar | Por qué |
|---|---|---|
| `frontend-expert` | Bootstrap T-1 (siempre primero) | FSD-Lite boundaries, Server-First default, `'use client'` solo hojas con state/hooks, Vitest unit patterns, runtime quality checklist (useEffect deps complete, no stale closures, hydration safety con zustand persist) |
| `playwright-expert` | T-8 (E2E specs + visual goldens) | Clerk auth fixture REUSE F1-S3, POM patterns en `e2e/pages/`, addInitScript determinism para localStorage state, visual goldens `--update-snapshots` iter 1 protocol con Chris side-by-side, port 3002 vitalia, freshness gate, axe-playwright ruleset wcag2aa, anti-patterns |
| `tessl__react-patterns` | T-1 + T-5 (useKeyboardShortcuts + ValeriaSidebar) | React 19 IME composition handling (`e.isComposing`), hooks contract (cleanup useEffect obligatorio), focus trap pattern manual (Tab cycling sin focus-trap-react dep), focus restoration `useRef<HTMLElement>` |
| `tessl__shadcn-ui` | T-3 (ValeriaRail + ValeriaChatSlot) y T-6 (TopBarGlobal extend) | REUSE primitives `Button` (variant ghost + size icon h-9 w-9), `Input` (search), `Tooltip` (Radix con TooltipProvider envoltura), `Avatar` (chat header), `Separator`. Versiones cementadas F1-S0 — NO upgrade |
| `tessl__tailwind` | T-2/T-3/T-4/T-5/T-6 (cualquier componente que toca tokens shell) | Tokens semánticos via globals.css CSS vars (Design Contract §5.1). Permitidos: `bg-background`, `bg-card`, `bg-muted`, `text-foreground`, `text-muted-foreground`, `border-border`, `bg-agent-valeria`, `bg-agent-valeria-soft`. NO hex literales. NO arbitrary values salvo `data-testid` attrs |
| `tessl__vitest` | T-1/T-3/T-4/T-5/T-6/T-7 (todos unit tests) | RTL + `@testing-library/jest-dom` + `@testing-library/user-event`. Mock `useShellStore` via `useShellStore.setState({...})` directo + `useShellStore.persist?.clearStorage()` afterEach. NO `vi.mock('@/stores/shell-store')` |
| `claude-md-management` | Cuando dudes project-level invariants | tenant isolation upstream, Spanish neutro, native-first dev workflows |

### NO cargar (out-of-scope)

`backend-expert`, `copilot-expert`, `sales-agent-expert`, `offer-expert`, `brand-expert`, `metrics-expert`, `offer-type-preset-expert`, `tessl__langgraph`, `tessl__nextjs-app-router-modularization`, `tessl__zod` — story es FE only chrome UI sin BE/agentic/dominio negocio/forms.

## § 2 — Must-load rules (overlay vitalia + raíz)

| Rule | Trigger |
|---|---|
| `.claude/rules/frontend-fsd.md` (raíz) | shell-organism es `components/shared/` cross-feature — boundary matrix vital |
| `.claude/rules/frontend-quality.md` (raíz) | ESLint 60+ rules, TS strict, Vitest 20% coverage threshold |
| `.claude/rules/spanish-text.md` (raíz) | strings UI sin voseo — aria-labels + tooltips + 28 microcopy ratificados |
| `.claude/rules/tenant-isolation.md` (raíz) | URL `[tenantId]` propaga via Next routing — middleware Clerk gates upstream (no FE filter aquí) |
| `.claude/rules/anti-duplication.md` (raíz) | cross-brand mirror scan ejecutado pre-arch (§ 0.1 03-arch.md audit clean — 0 matches). `useKeyboardShortcuts` LIFT CANDIDATE post 2do consumer |
| `.claude/rules/tdd-mandatory.md` (raíz) | RED tests primero por capa: hook → mock data → átomos/moléculas → organism → integration MODIFY |
| `.claude/rules/e2e-testing.md` (raíz) | Playwright NATIVE Linux (no docker), port 3002 vitalia, preflight obligatorio |
| `vitalia/.claude/rules/shell-mockup-per-component.md` (overlay) | visual goldens side-by-side mockup HTML ratificado · ratchet shrink-only · 13 PNGs scope |
| `vitalia/.claude/rules/hipaa-lite.md` (overlay) | scope: `not_applicable` — UI shell sin PHI · mock data verbatim spec § 5 sin patient identifiers/diagnostics/dosages |

## § 3 — Patterns required (debe usarse)

1. **Server Components default.** Solo agregar `'use client'` en hojas que consumen `useShellStore` (hook → Client-only), useState/useEffect, event handlers DOM. Per § 2.10 03-arch.md decision tree. Arch test `test_server_first.test.ts` allowlist extend (shrink only — justify commit body).

2. **Named exports (no default exports)** salvo Next.js convention (no aplica F1-S5 — no nuevas pages.tsx/layout.tsx). Arch test ratchet enforce.

3. **Zustand store READ-ONLY consumer** — F1-S5 NO modifica `shell-store.ts` schema. Solo consume `valeriaState`, `shellMode`, `setValeriaState`, `setShellMode`, `cycleValeriaState` (último opcional, no se usa). Selector pattern: `const setValeriaState = useShellStore((s) => s.setValeriaState)` para evitar re-render por cambios irrelevantes. Arch test NEW `test-shell-store-schema-readonly-f1-s5.test.ts` enforce.

4. **`useKeyboardShortcuts` hook con hardened guard (D4 spec § 0)** — verbatim contract en 03-arch.md § 2.3:
   - skip si `e.isComposing` (IME composition guard — Scenario 3)
   - skip si focus en `INPUT`/`TEXTAREA`/`[contenteditable=true]`/`[role=textbox]` o cualquier ancestor (Scenario 2)
   - modifier shortcuts (`Cmd+K`, `Ctrl+K`) BYPASS focus guard (intencional para focus jump)
   - key matching bare lowercase (`c/r/f/n`) o `Escape` exact o `mod+k` cross-platform
   - cleanup `removeEventListener` en useEffect return

5. **Auto-coupling state invariant (D2 spec § 0)** — verbatim en 03-arch.md § 2.4 handlers contract:
   - `setValeriaState('collapsed')` desde keyboard/click → **AUTO** `setShellMode('web')` mismo handler
   - `setValeriaState('rail' | 'full')` desde keyboard/click → **AUTO** `setShellMode('agentic')` mismo handler
   - Mobile drawer cierre vía Esc/backdrop/X → NO auto-shellMode (preserva shellMode previo)
   - Estos handlers viven dentro de `ValeriaSidebar` + `TopBarGlobal` (no propagar lógica a otros componentes)

6. **Adversarial type guard runtime (Scenario 4)** — `ValeriaSidebar` valida `valeriaState` recibido del store:
   ```ts
   const validStates: ValeriaState[] = ['collapsed', 'rail', 'full']
   if (!validStates.includes(valeriaState)) {
     console.warn(`[ValeriaSidebar] Invalid valeriaState received: ${String(valeriaState)}. Falling back to 'rail'.`)
     return <ValeriaSidebar /* fallback render con rail */ />
   }
   ```
   Cero crash app. Cero white screen.

7. **Semantic tokens Tailwind** — `bg-card`, `border-border`, `text-foreground`, `text-muted-foreground`, `bg-muted`, `bg-agent-valeria`, `bg-agent-valeria-soft`. Tokens definidos en `globals.css` (F1-S1). NO hex (`#7b2d91`). NO arbitrary values salvo `data-testid` attrs.

8. **Aria-labels en Spanish neutro** — verbatim spec § 6 microcopy:
   - `<aside aria-label="Panel Valeria">`
   - Rail button aria-labels: "Mostrar historial", "Nueva conversación", "Buscar (Cmd+K)", "Cerrar Valeria"
   - History `<nav aria-label="Historial conversaciones">`
   - Search input `aria-label="Buscar conversación"`
   - ChatSlot `<section aria-label="Chat con Valeria (próximamente)">`
   - Hamburger TopBar `aria-label="Abrir panel Valeria"`
   - Drawer X button `aria-label="Cerrar panel Valeria"`
   - Live region `<span role="status" aria-live="polite" aria-atomic="true" className="sr-only">` con texto: "Valeria cerrada" / "Valeria abierta" / "Valeria con historial"
   - Sin voseo.

9. **Tooltips Shadcn pattern** — `<TooltipProvider>` envuelve el rail (puede ser root del ValeriaSidebar). Cada button: `<Tooltip><TooltipTrigger asChild>{button}</TooltipTrigger><TooltipContent side="right">{label · key}</TooltipContent></Tooltip>`. delayDuration default. NO custom positioning hardcoded.

10. **Focus management contract** (a11y mandatory):
    - Initial mount: NO auto-focus (respeta default browser, va a TopBar primero)
    - Mobile drawer abierto: auto-focus primer interactivo (input search si full, primer rail button si rail). Use `useEffect` con dep `[isExpanded]` + `isMobileViewport()` check.
    - Mobile drawer cerrado: focus restoration al hamburger button (guardar `previousActiveElement` en `useRef<HTMLElement | null>(null)` antes de abrir)
    - Cmd+K: focus al composer placeholder (`document.getElementById('valeria-composer-placeholder')?.focus()`)
    - Focus trap mobile: impl manual Tab cycling (NO añadir dep `focus-trap-react`) — selector `button:not([disabled]), input:not([disabled]), [tabindex="0"]`

11. **Reduced motion respect** — todas las transitions agregar `motion-reduce:transition-none`. Ej. `transition-[grid-template-columns] duration-[220ms] motion-reduce:transition-none`.

12. **`data-testid` selectors para Playwright** — verbatim:
    - `valeria-sidebar` (aside raíz)
    - `valeria-drawer-backdrop` (mobile backdrop)
    - `valeria-drawer-close` (X button mobile)
    - `topbar-hamburger` (TopBarGlobal NEW button)
    - `history-search` (input search)
    - `history-empty-state` (EmptyStateInline visible cuando 0 matches)
    - `rail-button-{toggle|new|search|close}` opcional (tests prefieren aria-label lookup, data-testid solo si necesario)
    - `valeria-composer-placeholder` (composer placeholder ChatSlot — id attr NO data-testid)

13. **Mockup HTML side-by-side iter 1 golden generation** — T-8 monta mockups en `python3 -m http.server 8888 vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/mockups/` y abre side-by-side con componente real `localhost:3002/test-stack/shell-layout` (asegurar `valeriaState` initial set via addInitScript para cada snapshot). Solo cuando Chris ratifica visual side-by-side: `npx playwright test --update-snapshots --project=visual`. Ratchet shrink-only post-ratify (per `shell-mockup-per-component.md`).

14. **TDD RED-first per ticket** — test falla ANTES de implementar GREEN. Verbatim orden 03-arch.md § 2.9:
    - T-1: `useKeyboardShortcuts.test.ts` RED → import fails / hook undefined → impl `useKeyboardShortcuts.ts` GREEN
    - T-3: `ValeriaRail.test.tsx` + `ValeriaChatSlot.test.tsx` RED → impl componentes GREEN
    - T-4: `ValeriaHistory.test.tsx` RED → impl `ValeriaHistory.tsx` GREEN
    - T-5: `ValeriaSidebar.test.tsx` RED → impl `ValeriaSidebar.tsx` GREEN
    - T-6: `TopBarGlobal.test.tsx` update assertions RED → edit `TopBarGlobal.tsx` GREEN
    - T-7: `test-shell-store-schema-readonly-f1-s5.test.ts` RED + `ShellOrganismLayout.test.tsx` update assertions RED → integration MODIFY GREEN + DELETE legacy files
    - T-8: Playwright specs RED (componente real existe pero no goldens snapshots) → all ON GREEN once T-1..T-7 mergeable + Chris ratifica side-by-side + `--update-snapshots`

15. **Spanish neutro check (pre-commit hook + arch test)** — todos los strings UI revisados verbatim contra glosario `.claude/rules/spanish-text.md`. NO usar magic comment `<!-- voseo-allowed -->` en source files (solo en docs/mockups/tests fixtures). Si arch test `test-vitalia-ui-strings-no-voseo.test.ts` falla → fix string, no marcar magic comment.

16. **Hydration safety** — zustand `persist` es sync on client mount (probado F1-S4); no SSR mismatch porque `'use client'` leaf renderiza después de hidratación inicial. Si Vitest test pasa SSR + CSR sin warning, safe.

17. **Filter logic determinístico (ValeriaHistory)** — `useMemo` dependencies `[searchQuery]` (mock data es módulo-level constant, no needed en deps):
    ```ts
    const filtered = useMemo(
      () => MOCK_CONVERSATIONS.filter(c =>
        c.title.toLowerCase().includes(searchQuery.toLowerCase().trim())
      ),
      [searchQuery]
    )
    const grouped = useMemo(
      () => ({
        today: filtered.filter(c => c.group === 'today'),
        yesterday: filtered.filter(c => c.group === 'yesterday'),
        this_week: filtered.filter(c => c.group === 'this_week'),
      }),
      [filtered]
    )
    ```

18. **Escape key precedence en search input (Scenario 6)** — cuando focus en search + searchQuery no vacío:
    - Press Escape → primer trigger: `setSearchQuery('')` (NO colapsar Valeria)
    - Si searchQuery ya vacío → standard handler aplica (collapsed)
    - Implementación: handler `onKeyDown` local en `<Input>` + `e.stopPropagation()` si match

## § 4 — Patterns forbidden (NO usar)

1. **Hex literals** (`#01b2f8`, `#7b2d91`, `#22c55e`, `#ffffff`) en JSX/CSS — usar tokens semánticos (`bg-primary`, `bg-agent-valeria`, `bg-background`, `bg-card`). Arch test `test_no_hardcoded_colors.test.ts` bloquea.

2. **`any` TypeScript** — strict mode. Si necesitás escape, usa `unknown` + type guard (`if (typeof x === 'string')`).

3. **Default exports** salvo `page.tsx`/`layout.tsx` Next.js (no aplica F1-S5 — sin nuevas pages). Arch ratchet enforce.

4. **Modificar archivos REUSE F1-S0/S1/S2/S3** — `LogoMark.tsx`, `ThemeToggle.tsx`, `TenantSwitcher.tsx`, `TenantOption.tsx`, `TenantBadge.tsx`, `TenantStoreBootstrap.tsx`, `AddClinicPlaceholderModal.tsx`, `tenant-store.ts`, `useViewportGuard.ts`, `AppPanelSlot.tsx`, `ShellModeToggle.tsx`, `shell-store.ts` — todos PRESERVED intact. Si necesitás cambio, escala a `/pm-vitalia` → nueva story.

5. **Modificar `shell-store.ts` schema** — HARD BAN F1-S5. Arch test `test-shell-store-schema-readonly-f1-s5.test.ts` falla si cambia exports/defaults/setters.

6. **Modificar `components/ui/` Shadcn primitives** — copy-paste local, no upstream upgrade. Si tooltip/avatar/input necesita variant nueva → escala /pm-vitalia.

7. **Cross-feature imports en shell-organism** — `components/shared/shell-organism/*` NO debe importar `features/*`. FSD boundary matrix raíz (`frontend-fsd.md`). Arch test `test_fsd_boundaries.test.ts` enforce.

8. **Cross-brand imports** — vitalia frontend NUNCA importa `nicolify/`, `comunify/`, `lupulo/`. CopilotSidebar de Nicolify es pattern reference VISUAL solamente — NUNCA `import` de cross-brand. Arch test `test-no-cross-brand-shell-mirror.test.ts` enforce extended con nuevos nombres.

9. **Modificar `app/(dashboard)/` legacy** — coexiste paralelo per D3 SHELL-DESIGN-CONTRACT. Tocar = scope creep.

10. **Modificar `ShellOrganismLayoutClient.tsx` MÁS allá del diff verbatim de § 2.6** — único cambio permitido: `MIN_VALERIA_PX` ternary (620→580) + replace `<ValeriaSidebarSlot/>` import → `<ValeriaSidebar/>` real. NADA más (snap-up, ResizeObserver, useDefaultLayout, useGroupRef, layout structure, tokens, comments todos PRESERVED).

11. **Modificar `TopBarGlobal.tsx` MÁS allá del diff verbatim de § 2.6** — único cambio permitido: agregar hamburger Menu button visible `<md` con handler `setValeriaState('full') + setShellMode('agentic')`. NADA más (estructura header, LogoMark, TenantSwitcher, ThemeToggle todos PRESERVED).

12. **`useState` para shellMode/valeriaState** — usar `useShellStore` siempre. Local state duplicate inválida fuente verdad.

13. **`router.push()` / `redirect()` desde componentes F1-S5** — no necesario; routing está cementado F1-S4. Si surge necesidad → scope creep, escalar.

14. **Custom `useMediaQuery` o `useViewport` hooks NEW** — reusar `useViewportGuard.ts` heredado F1-S4 si se necesita viewport check. Para `isMobileViewport()` helper interno, usar `window.matchMedia('(max-width: 767px)').matches` directo dentro de useEffect post-mount (NO en render).

15. **`focus-trap-react` u otras deps a11y nuevas** — impl manual Tab cycling per § 3.10 arriba. Mantenemos surface lean.

16. **`window.matchMedia` / `window.innerWidth` durante render** — usar solo en `useEffect` (post-mount). Render branching solo via Tailwind responsive classes. Evitar hydration mismatch.

17. **`useMemo` for derived shellMode** sin razón concreta — premature optimization. Lectura zustand selector ya optimizada.

18. **Logging via `console.log`** — usar `console.warn` solo para edge cases adversariales (Scenario 4 setState invalid). Sin Sentry/structlog custom en F1-S5.

19. **Magic comment `<!-- voseo-allowed -->` en source `.tsx` files** — solo en docs/rules/tests fixtures donde se cita glosario. Source code prod sin voseo.

20. **Agregar `task_to_*` o sales_agent surface** — F1-S5 es chrome puro sin agentic. Cualquier mención de copilot/sales-agent en código = scope creep.

21. **Modificar mockups HTML** — `mockups/valeria-rail.html` y `mockups/valeria-history.html` ratificados iter 1. Si componente diverge del mockup post-implementation → STOP, escala Chris (no actualizar mockup salvo nueva ratificación visual dedicada).

22. **Crear capability YAML antes del merge** — `valeria-sidebar.yaml` lo crea `/pm-vitalia` post-done. Builders NO crean YAML capabilities.

## § 5 — Files in scope (dev-team puede tocar)

### Archivos NEW (sí permitido crear)

```
vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.tsx              # T-5
vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.test.tsx         # T-5
vitalia/frontend/src/components/shared/shell-organism/ValeriaRail.tsx                 # T-3
vitalia/frontend/src/components/shared/shell-organism/ValeriaRail.test.tsx            # T-3
vitalia/frontend/src/components/shared/shell-organism/ValeriaHistory.tsx              # T-4
vitalia/frontend/src/components/shared/shell-organism/ValeriaHistory.test.tsx         # T-4
vitalia/frontend/src/components/shared/shell-organism/ValeriaChatSlot.tsx             # T-3
vitalia/frontend/src/components/shared/shell-organism/ValeriaChatSlot.test.tsx        # T-3
vitalia/frontend/src/components/shared/shell-organism/HistoryItem.tsx                 # T-3
vitalia/frontend/src/components/shared/shell-organism/HistoryGroup.tsx                # T-3
vitalia/frontend/src/components/shared/shell-organism/EmptyStateInline.tsx            # T-3
vitalia/frontend/src/components/shared/shell-organism/_mock-conversations.ts          # T-2
vitalia/frontend/src/hooks/useKeyboardShortcuts.ts                                    # T-1
vitalia/frontend/src/hooks/__tests__/useKeyboardShortcuts.test.ts                     # T-1
vitalia/frontend/src/__tests__/architecture/test-shell-store-schema-readonly-f1-s5.test.ts  # T-7
vitalia/frontend/e2e/pages/ValeriaSidebarPage.ts                                       # T-8
vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/keyboard-cycle.spec.ts             # T-8 SC-1
vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/typing-guard.spec.ts               # T-8 SC-2
vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/ime-composition.spec.ts            # T-8 SC-3
vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/store-tampering.spec.ts            # T-8 SC-4
vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/click-collapse.spec.ts             # T-8 SC-5
vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/history-empty-search.spec.ts       # T-8 SC-6
vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/a11y-keyboard.spec.ts              # T-8 SC-7
vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/a11y-mobile-drawer.spec.ts         # T-8 SC-8
vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/i18n-spanish-neutro.spec.ts        # T-8 SC-9
vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/visual-goldens.spec.ts             # T-8 visual
vitalia/frontend/e2e/regression/vitalia-fase1-valeria-rail-history/visual-goldens.spec.ts-snapshots/*.png  # T-8 iter 1 (--update-snapshots, ratified Chris)
```

### Archivos MODIFY (sí permitido editar — diff verbatim § 2.6 03-arch.md)

```
vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx   # T-7 — MIN_VALERIA_PX 620→580 + replace slot import (verbatim diff § 2.6)
vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx                # T-6 — add hamburger button + 'use client' + useShellStore consumer (verbatim diff § 2.6)
vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.test.tsx           # T-6 — extend assertions hamburger button visible/handler
vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayout.test.tsx    # T-7 — replace ValeriaSidebarSlot assertions → ValeriaSidebar
vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts  # T-7 — extend names array (shrink only justify)
vitalia/frontend/src/__tests__/architecture/test_server_first.test.ts                 # T-7 — extend allowlist NEW client components (shrink only justify)
```

### Archivos DELETE (sí permitido eliminar — cleanup F1-S5)

```
vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.tsx          # T-7 reemplazado por ValeriaSidebar real
vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.test.tsx     # T-7 cleanup
```

### Archivos NEVER touch (HARD FAIL si tocás)

```
vitalia/frontend/src/components/shared/shell-organism/LogoMark.tsx            # F1-S2 done — REUSE
vitalia/frontend/src/components/shared/shell-organism/ThemeToggle.tsx         # F1-S1 done — REUSE
vitalia/frontend/src/components/shared/shell-organism/TenantSwitcher.tsx      # F1-S3 done — REUSE
vitalia/frontend/src/components/shared/shell-organism/TenantOption.tsx        # F1-S3 done — REUSE
vitalia/frontend/src/components/shared/shell-organism/TenantBadge.tsx         # F1-S3 done — REUSE
vitalia/frontend/src/components/shared/shell-organism/TenantStoreBootstrap.tsx # F1-S3 done — REUSE
vitalia/frontend/src/components/shared/shell-organism/AddClinicPlaceholderModal.tsx  # F1-S3 done — REUSE
vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx        # F1-S4 done — REUSE (placeholder F1-S7+)
vitalia/frontend/src/components/shared/shell-organism/ShellModeToggle.tsx     # F1-S4 done — REUSE (interactivo en F1-S5/S7 future)
vitalia/frontend/src/components/shared/shell-organism/useViewportGuard.ts     # F1-S4 done — REUSE
vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayout.tsx # F1-S4 done — wrapper dynamic, NO modify (Solo Client modifica)
vitalia/frontend/src/components/shared/shell-organism/types.ts                # F1-S4 done — REUSE
vitalia/frontend/src/stores/shell-store.ts                                    # F1-S4 done — READ-ONLY consumer
vitalia/frontend/src/stores/tenant-store.ts                                   # F1-S3 done — UNUSED en F1-S5
vitalia/frontend/src/components/ui/*                                          # Shadcn primitives — copy-paste local, no upstream upgrade
vitalia/frontend/src/app/(dashboard)/**                                       # LEGACY — coexiste paralelo (D3)
vitalia/frontend/src/app/(auth)/**                                            # LEGACY auth
vitalia/frontend/src/app/(app)/**                                             # LEGACY
vitalia/frontend/src/app/onboarding/**                                        # LEGACY onboarding
vitalia/frontend/src/app/marketing/**                                         # LEGACY public marketing
vitalia/frontend/src/app/public/**                                            # LEGACY public
vitalia/frontend/src/app/test-stack/**                                        # F1-S0/S1/S2/S3/S4 — public showcase routes, NO modify (E2E entry points)
vitalia/frontend/src/app/[tenantId]/**                                        # F1-S4 done — route group, NO modify
vitalia/frontend/src/app/layout.tsx                                           # F1-S2 deployed — root layout, NO modify (skip-link ya correcto)
vitalia/frontend/src/app/providers.tsx                                        # NO modify
vitalia/frontend/src/app/globals.css                                          # F1-S1 deployed tokens — NO modify (tokens --agent-valeria existen)
vitalia/frontend/src/components/shared/copilot-rail/**                        # LEGACY visual — orfano post F1-S5, NO modify (cleanup en story dedicada futura)
vitalia/frontend/src/components/shared/shell/**                               # LEGACY AppShell — coexiste, NO modify
vitalia/frontend/src/features/**                                              # OUT-OF-SCOPE FSD boundary — shell-organism no toca features
nicolify/**, comunify/**, lupulo/**                                          # CROSS-BRAND HARD BAN per anti-duplication.md
core/luana-core-*/**, core/@luana/**                                          # ENGINE — promotion gate /pm-luana required
vitalia/backend/**                                                            # BE out-of-scope
vitalia/.claude/**, .claude/**                                                # meta — no modify
vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md                            # touchable only por /pm-vitalia post-merge si DC necesita update
vitalia/docs/product/modules/shell-organism.md                                # tracked auto-list block — auto-regen via reconcile_capabilities post-merge
vitalia/docs/product/capabilities/shell-organism/*.yaml                       # NEW yaml lo crea /pm-vitalia post-merge (F1-S5 builder NO toca)
```

## § 6 — Reference artifacts (consulta on-demand)

| Artifact | Path | Cuándo consultar |
|---|---|---|
| 01-spec.md (contract Gherkin + AC + microcopy + Wireframes ASCII) | `vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/01-spec.md` | Antes empezar cada ticket — re-leer scenario relevante + AC + microcopy SSoT |
| 03-arch.md (this doc consolidado FE-only) | `vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/03-arch.md` | Decisiones ambiguas (state machine, handlers contract, focus trap, file tree, server vs client) |
| 04-validators.yaml § test_construction_plan | mismo path | Orden creation + poms + fixtures + scenario_to_test mapping |
| Mockup HTML rail+collapsed | `vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/mockups/valeria-rail.html` | Visual goldens side-by-side T-8 iter 1 + microcopy verbatim |
| Mockup HTML history+empty+drawer | `vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/mockups/valeria-history.html` | Visual goldens history-full + empty-state + drawer-mobile |
| SHELL-DESIGN-CONTRACT.md | `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` | §3.4 (`ShellOrganismLayout` template) + §5.1 (tokens CSS vars) + §6.1 (`shellStore` ya cementado) + §8 (a11y per organism) + §9 (testing strategy) + §10 (story → component mapping) |
| Predecessor F1-S4 03-arch / 04-validators / 05-guidelines / 06-tickets | `vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/` | Patterns reference (POM ShellLayoutPage.ts, fixture shell-theme.fixture.ts, visual goldens iter protocol, route /test-stack/shell-layout) |
| Nicolify CopilotSidebar (pattern reference READ-ONLY) | `nicolify/frontend/src/features/copilot/components/CopilotSidebar.tsx` | Reference pattern transposed (2-col asymmetric, keyboard handler, mobile drawer). NUNCA import — solo lectura referencia |
| ADR worktree shell mockup protocol | `vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md` | Visual goldens iter protocol + ratchet shrink-only rules |
| HIPAA-lite rule overlay | `vitalia/.claude/rules/hipaa-lite.md` | scope: `not_applicable` declaration justify + verificar mock data sin PHI fields canónicos |
| Spanish neutro glossary | `.claude/rules/spanish-text.md` | 28 strings ratificados spec § 6 |

## § 7 — Verification commands (reproducible local)

Cuando termines un ticket, corré local antes commit:

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend

# Per-ticket fast feedback:
npx tsc --noEmit
npx eslint src/components/shared/shell-organism src/hooks src/__tests__/architecture --cache

# Per-ticket Vitest (sufijos según ticket scope):
# T-1 hook:
npx vitest run src/hooks/__tests__/useKeyboardShortcuts.test.ts --reporter=default
# T-3 átomos+moléculas low-level:
npx vitest run src/components/shared/shell-organism/{ValeriaRail,ValeriaChatSlot}.test.tsx --reporter=default
# T-4 ValeriaHistory:
npx vitest run src/components/shared/shell-organism/ValeriaHistory.test.tsx --reporter=default
# T-5 ValeriaSidebar:
npx vitest run src/components/shared/shell-organism/ValeriaSidebar.test.tsx --reporter=default
# T-6 TopBarGlobal extend:
npx vitest run src/components/shared/shell-organism/TopBarGlobal.test.tsx --reporter=default
# T-7 integration:
npx vitest run src/components/shared/shell-organism/ShellOrganismLayout.test.tsx src/__tests__/architecture/test-shell-store-schema-readonly-f1-s5.test.ts --reporter=default

# Full vitest pre-handoff:
npx vitest run src/components/shared/shell-organism src/hooks src/__tests__/architecture --reporter=default --coverage --coverage.thresholds.lines=20 --coverage.thresholds.functions=20

# T-8 E2E (asume make dev-vitalia corriendo background):
bash ${WS}/scripts/e2e-preflight.sh
E2E_BASE_URL=http://localhost:3002 npx playwright test regression/vitalia-fase1-valeria-rail-history/
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=visual regression/vitalia-fase1-valeria-rail-history/visual-goldens.spec.ts

# Visual goldens iter 1 (post Chris ratify side-by-side):
# 1. Servidor mockups:
python3 -m http.server 8888 --directory ${WS}/vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/mockups &
# 2. Chris abre http://localhost:8888/valeria-rail.html y /valeria-history.html
# 3. Chris abre http://localhost:3002/test-stack/shell-layout
# 4. Side-by-side ratify
# 5. --update-snapshots:
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=visual --update-snapshots regression/vitalia-fase1-valeria-rail-history/visual-goldens.spec.ts

# Full validators (pre-handoff a /auditor):
cd ${WS} && make ci-parity  # opcional pre-push main
```

## § 8 — Auditor handoff expectations

When `state: developed`, `/dev-team` emits AUTO-HANDOFF to `/auditor` (per `story-closure-gate.md`). Auditor will:

1. **Re-run `gate-runner`** con todos los validators (§ 04-validators.yaml).
2. **C1 Code review** — Cat 1 FSD-Lite imports (shell-organism NO importa features), Cat 9 PII (N/A here, declared `hipaa_lite_scope: not_applicable` + mock data verbatim audit), Cat 10 tests/TDD (RED→GREEN evidence per ticket), Cat 12 anti-duplication (cross-brand mirror scan extended + useKeyboardShortcuts LIFT CANDIDATE comment present), Cat 17 SSoT artifact integrity (visual goldens path match arch + spec mockup_ref).
3. **C2 Spec coverage** — Phase D Gherkin verification matrix (`06-audit/gherkin-matrix.md`): 9 scenarios → tests pasados con scenario_id labeling.
4. **C3 Architecture coverage** — § Architectural fitness § 3.3 03-arch.md + new arch test `test-shell-store-schema-readonly-f1-s5.test.ts` GREEN.
5. **C4 Cross-cutting** — Spanish neutro check (pre-commit hook + manual review en 28 strings + i18n-spanish-neutro.spec.ts regex grader), HIPAA-lite N/A declaration cited + mock data audit (8 conversaciones zero PHI fields), a11y axe wcag2aa zero violations light+dark+mobile.
6. **C5 Trace** — visual goldens 13 PNGs match mockups ratificados Chris (side-by-side check vía `python3 -m http.server 8888 vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/mockups/`).
7. **Scope discipline check** — verifica NO touch otros componentes shell ya cementados (LogoMark, ThemeToggle, TenantSwitcher, AppPanelSlot, ShellModeToggle, useViewportGuard, ShellOrganismLayout wrapper). `git diff --stat origin/main..HEAD` debe coincidir con `files in scope § 5` arriba.

Auditor self-fix policy (`.claude/rules/auditor-self-fix-policy.md`): whitelist trivial fixes (typo Spanish, missing aria-label, import order, prettier format) OK. Lógica/branch/refactor → spawn dev-team Caso B.

## § 9 — Anti-creep (post-story scope)

When `state: done` and merged:

- **F1-S6** (`valeria-chat-skeleton`) reemplaza body+composer del `ValeriaChatSlot` con chat real (mensajes + textarea con id `valeria-composer-placeholder` connected). F1-S5 deja `ChatHeader` (avatar+nombre+status) construido — F1-S6 lo RESPETA intacto.
- **F1-S7** (`ribbon-6-tabs`) REPLACE `AppPanelSlot.tsx` con Ribbon real (no afecta F1-S5).
- **F1-S5/S7** futuro activa `ShellModeToggle` interactivo (remove `disabled` attr, wire `setShellMode`).
- **F2+** conectarán API real `/api/conversations` reemplazando `_mock-conversations.ts`. Filter/grouping logic preservada — solo data source cambia.
- **`useKeyboardShortcuts` LIFT** — cuando 2do consumer (Nicolify/Comunify/Lupulo) necesite hook similar → `/pm-luana` promotion proposal para `core/@luana/hooks/use-keyboard-shortcuts/`. Documentar caso en `vitalia/docs/learnings/2026-05-24-useKeyboardShortcuts-promotion-candidate.md` post-merge (NO ahora).
- **`EmptyStateInline` LIFT** — átomo presentational generic candidato cross-brand. Mismo principio: lift al 2do consumer.

Si necesitás algo que cae fuera de § 5 files in scope → STOP, escalar a `/pm-vitalia` para crear ticket adicional o re-decompose.

