<!-- voseo-allowed: glosario reference + internal guidelines -->

---
story_id: vitalia-fase1-ribbon-6-tabs
brand: vitalia
type: ui-story
phase: fase-1
last_modified: 2026-05-25
architect_iter: 1
---

# F1-S7 `vitalia-fase1-ribbon-6-tabs` — 05-guidelines.md

## § 1 — Must-load skills (builder bootstrap obligatorio)

`builder-frontend` (Sonnet/opencode/qwen) MUST cargar estos skills en bootstrap ANTES de tocar código. Enforcement: `/dev-team` Step 0 verifica + builder report en `T-{n}-result.md` lista "Skills consulted" verbatim. Falta del report → auditor CHANGES_REQUESTED automático.

| Skill | Cuándo cargar | Por qué |
|---|---|---|
| `frontend-expert` | Bootstrap T-1 (siempre primero) | FSD-Lite boundaries (`shared/shell-organism/` vs `lib/` vs `stores/`), Server-First default + `'use client'` solo hojas con hooks/state/handlers, Shadcn primitive reuse, tokens Tailwind semánticos, Vitest unit patterns, runtime quality checklist (useEffect deps complete, no stale closures, hydration safety). |
| `tessl__react-patterns` | T-2 + T-3 (componentes con hooks) | React 19: `useState` + `useRef` + `useCallback` patterns, roving tabindex pattern (focus management imperativo vía refs array), event handlers `onKeyDown` con preventDefault, forwardRef + Radix Avatar/Tooltip composition. |
| `tessl__shadcn-ui` | T-2 (componentes que usan primitives) | REUSE primitives F1-S0: `Avatar` + `AvatarImage` + `AvatarFallback` (graceful PNG-404 onError via Radix), `Tooltip` + `TooltipTrigger` + `TooltipContent` (ConfigTab hint). NO usar Shadcn `<Tabs>` (Radix-based incompatible con route nav — arch test enforce). |
| `tessl__tailwind` | T-1 + T-2 + T-3 + T-4 (cualquier componente con classes) | Tokens semánticos via globals.css CSS vars (Design Contract §5.1). Permitidos: `bg-card`, `bg-muted`, `bg-muted/80`, `border-border`, `text-foreground`, `text-muted-foreground`, `ring-border`, `ring-ring`, `bg-agent-{slug}-soft`. NO hex literales. NO arbitrary values salvo `text-[10px]` (heredado F1-S6 role sub-label). Dynamic agent classes via `agentBgSoftClass(slug)` switch (JIT-safe). |
| `tessl__vitest` | T-1 + T-2 + T-3 + T-4 (todos unit tests) | RTL + `@testing-library/jest-dom` + `@testing-library/user-event`. Mock `next/navigation` via `vi.mock('next/navigation', () => ({ usePathname: vi.fn(), useRouter: vi.fn(), useParams: vi.fn() }))`. Reset mocks afterEach. |
| `playwright-expert` | T-5 (E2E specs + POM + visual goldens) | POM patterns en `e2e/regression/vitalia-fase1-ribbon-6-tabs/poms/` (NEW path canon F1-S7 per checkpoint), fixtures REUSE `shell-theme.fixture.ts` + `clerk-auth.fixture.ts`, port 3002 vitalia, freshness gate, axe-playwright ruleset wcag2aa, visual goldens `--update-snapshots --project=visual` iter 1 post Chris ratify side-by-side mockup `ribbon.html`, native Linux NUNCA docker. |
| `tessl__nextjs-app-router-modularization` | T-3 (boundary decisions) | `'use client'` boundaries: Ribbon root Client (hooks); RibbonTab + ConfigTab Client (forwardRef + event handlers). NO crear nuevas routes — Ribbon consume URL existente via `usePathname()` y dispara `router.push()` a paths F1-S9 implementará. App Router preserved. |
| `claude-md-management` | Cuando dudes project-level invariants | Tenant isolation upstream (useParams.tenantId never hardcode), Spanish neutro, native-first dev workflows, multibrand boundaries (zero engine touch, zero cross-brand import). |

### NO cargar (out-of-scope explícito)

`backend-expert`, `copilot-expert`, `sales-agent-expert`, `offer-expert`, `brand-expert`, `metrics-expert`, `offer-type-preset-expert`, `tessl__langgraph`, `tessl__zod` — story es FE only chrome UI sin BE/agentic/dominio negocio/forms/LLM real. Cargar genera ruido tokens y deriva en scope creep.

## § 2 — Must-load rules (overlay vitalia + raíz)

| Rule | Trigger |
|---|---|
| `.claude/rules/frontend-fsd.md` (raíz) | shell-organism es `components/shared/` cross-feature — boundary matrix vital; `lib/agent-catalog.ts` consumido cross-shell |
| `.claude/rules/frontend-quality.md` (raíz) | ESLint 60+ rules, TS strict, Vitest 20% coverage threshold |
| `.claude/rules/spanish-text.md` (raíz) | strings UI sin voseo — 11 microcopy ratificados (Mi Clínica · Atraer · Vender · Operar · Mantener · Configurar · Agentes + role labels) |
| `.claude/rules/tenant-isolation.md` (raíz) | URL `[tenantId]` propaga via Next routing — `useParams.tenantId` NUNCA hardcode |
| `.claude/rules/anti-duplication.md` (raíz) | cross-brand mirror scan pre-arch (§ 0.1 03-arch.md audit clean — 0 matches). Catalog SSoT EXTEND in-place (anti-duplication HARD per checkpoint) |
| `.claude/rules/tdd-mandatory.md` (raíz) | RED tests primero por capa: catalog extend → moléculas → organism → integration → e2e |
| `.claude/rules/e2e-testing.md` (raíz) | Playwright NATIVE Linux (no docker), port 3002 vitalia, preflight obligatorio |
| `.claude/rules/auditor-self-fix-policy.md` (raíz) | scope correcciones audit cycle — whitelist self-fix vs spawn dev-team |
| `vitalia/.claude/rules/shell-mockup-per-component.md` (overlay) | visual goldens side-by-side mockup `ribbon.html` ratificado · ratchet shrink-only · 11 PNGs scope |
| `vitalia/.claude/rules/hipaa-lite.md` (overlay) | scope: `not_applicable` — Ribbon es chrome UI nav puro sin PHI |

## § 3 — Patterns required (debe usarse)

1. **Server Components donde posible.** F1-S7: Ribbon + RibbonTab + ConfigTab son `'use client'` por hooks/handlers. Justified extension del allowlist `test_server_first.test.ts` con commit body explícito. AppPanelSlot SE MANTIENE Server Component (hospeda `<Ribbon />` Client via boundary natural Next.js).

2. **Named exports (no default exports)** — F1-S7 NO crea pages/layouts nuevas. Arch test enforce.

3. **Catalog SSoT EXTEND (anti-duplication HARD)** — `vitalia/frontend/src/lib/agent-catalog.ts` EXTEND in-place. NUNCA crear `lib/agents/catalog.ts` paralelo. Anti-duplication enforced via checkpoint + spec § 0.

4. **`AGENT_CATALOG` consumer pattern** — componentes leen `AGENT_CATALOG[slug].tabLabel` + `AGENT_CATALOG[slug].thumbnail` + `AGENT_CATALOG[slug].initial` + `AGENT_CATALOG[slug].defaultSubtab`. NUNCA hardcode `'Mi Clínica'` / `/agents/lisa/thumbnail.png` / `'L'` / `'marca'` fuera del catalog. Arch test `test-agent-catalog-ssot.test.ts` heredado F1-S6 enforce.

5. **`agentBgSoftClass(slug)` Tailwind helper REUSE** — `_agent-tw-classes.ts` switch pattern (heredado F1-S6). NUNCA template strings (`bg-agent-${slug}-soft`) — JIT no purga.

6. **Roving tabindex pattern manual** — implementación in-line en `Ribbon.tsx`:
   - State `focusedIdx` parent component
   - Refs array `useRef<(HTMLButtonElement | null)[]>([])` para focus management imperativo
   - `tabIndex={focusedIdx === idx ? 0 : -1}` per tab
   - `onKeyDown` handler con switch Arrow Right/Left/Home/End/Enter/Space
   - Wrap circular via modulo: `((idx % total) + total) % total`
   - **No** auto-activate on focus — user must Enter/Space (WAI-ARIA decision rationale: route nav side-effect no debe disparar por mover focus)

7. **Active vs focused ortogonales** — `active = extractAgentFromPath(usePathname())` (URL-derived). `focused = focusedIdx state` (keyboard interaction). NUNCA confundir.

8. **`forwardRef` mandatory en RibbonTab + ConfigTab** — parent Ribbon necesita `tabRefs.current[idx]?.focus()` imperativo. `forwardRef<HTMLButtonElement, Props>`.

9. **Avatar fallback graceful (Radix automático)** — `<Avatar><AvatarImage src={thumbnail} /><AvatarFallback>{initial}</AvatarFallback></Avatar>`. Radix Avatar primitive maneja onError → swap automático. NO `useState [imgError]` manual + NO `<img onError>` raw.

10. **XSS guard JSX text-children** — `{descriptor.tabLabel}` + `{descriptor.initial}`. NUNCA `dangerouslySetInnerHTML`. React 19 auto-escape. Auditor grep verifica cero matches.

11. **Semantic tokens Tailwind ONLY** — `bg-card`, `bg-muted`, `bg-muted/80`, `border-border`, `ring-border`, `ring-ring`, `text-foreground`, `text-muted-foreground`, `bg-agent-{slug}-soft` (via switch). NO hex literales (allowlist heredado: `agent-catalog.ts` único permitido para `hex` field metadata). NO arbitrary values salvo `text-[10px]` heredado F1-S6.

12. **`router.push` con `useParams.tenantId`** — NUNCA hardcodear tenantId. Pattern:
    ```ts
    const params = useParams<{ tenantId: string }>();
    if (!params?.tenantId) return; // defensive early return
    router.push(`/${params.tenantId}/${slug}/${AGENT_CATALOG[slug].defaultSubtab}`);
    ```

13. **`extractAgentFromPath` puro** — utility function en `lib/agent-catalog.ts`. Pure (no hooks, no side effects). Retorna `RibbonTabSlug | null`. Defensive nullable input handling.

14. **WAI-ARIA tablist completo** — verbatim spec § Accessibility:
    - `<nav role="tablist" aria-label="Agentes">`
    - per button: `role="tab"` + `aria-selected={active}` + `tabIndex={0 | -1}`
    - ConfigTab: `aria-label="Configurar"` (sin label text visible → aria-label mandatory)
    - Avatar: `alt=""` decorativo (parent button anuncia tabLabel + role)
    - Tooltip Radix: `aria-describedby` automático via Radix primitive

15. **Focus-visible mandatory** — `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1` en RibbonTab + ConfigTab. NO `focus:` (mouse-click focus visible distracts). NO outline default.

16. **Spanish neutro LatAm verbatim** — 11 strings spec § Microcopy:
    - tabLabels: `"Mi Clínica"`, `"Atraer"`, `"Vender"`, `"Operar"`, `"Mantener"`
    - role labels: `"Lisa"`, `"Lucas"`, `"Adrián"`, `"Valeria"`, `"Camila"` (Adrián con tilde)
    - ConfigTab `aria-label`: `"Configurar"`
    - ConfigTab tooltip text: `"Configurar"`
    - nav `aria-label`: `"Agentes"`
    NO voseo (no "andá"/"configurá"/"fijate"/"dale"). Tildes correctas. Arch test `test-vitalia-ui-strings-no-voseo.test.ts` extend.

17. **`useCallback` para handlers** — `navigateTo`, `focusTab`, `handleKeyDown` envueltos en `useCallback([deps])`. Evita re-renders innecesarios de RibbonTab/ConfigTab children.

18. **`<Tooltip>` Radix `delayDuration={0}`** — heredado F1-S0 default. ConfigTab tooltip visible inmediato on hover (sin delay molesto).

## § 4 — Patterns forbidden (NUNCA usar)

1. ❌ **Crear `lib/agents/catalog.ts`** — anti-duplication HARD. Catalog SSoT vive en `lib/agent-catalog.ts` (F1-S6).
2. ❌ **`<Tabs>` / `<TabsList>` / `<TabsTrigger>` / `<TabsContent>` Shadcn Radix-based** — incompatible con route nav (asume `<TabsContent>` inline). Arch test `test-ribbon-no-shadcn-tabs.test.ts` NEW enforce.
3. ❌ **`bg-agent-${slug}-soft` template string** — Tailwind JIT no purga. Usar `agentBgSoftClass(slug)` switch.
4. ❌ **Hex literals en componentes** — `#7b2d91`, `#00D084`, etc. forbidden fuera de `agent-catalog.ts` hex metadata. Arch test enforce.
5. ❌ **Hardcoded agent thumbnail paths** — `/agents/lisa/thumbnail.png` etc. forbidden fuera de `agent-catalog.ts`. Consume `descriptor.thumbnail`.
6. ❌ **Hardcoded tabLabel/role/initial strings** — `'Mi Clínica'`, `'Lisa'`, `'L'` forbidden fuera de catalog. Consume `AGENT_CATALOG[slug].{tabLabel,name,initial}`.
7. ❌ **Hardcoded defaultSubtab strings** — `'marca'`, `'agenda'`, etc. forbidden fuera de catalog.
8. ❌ **Hardcoded tenantId en router.push** — usar `useParams<{ tenantId: string }>()`.
9. ❌ **`border-bottom` en active tab style** — decisión Batch 2 Q4: flat design con bg-soft tint únicamente.
10. ❌ **`avatar ring` en active state** — decisión Batch 4: avatar 28px circle sin border-ring en active (heredado: `<Avatar>` sin className adicional, solo `size-7`).
11. ❌ **`if (mode === 'web')` branching markup** — decisión Batch 1: misma horizontal en ambos modos.
12. ❌ **Auto-activate tab on focus** — focus mueve cursor, NO dispara `router.push`. Enter/Space activan explícito.
13. ❌ **`dangerouslySetInnerHTML`** — XSS attack vector. React JSX text-children + Spanish auto-escape suficiente.
14. ❌ **`useEffect` para focus inicial** — stale closure trap. Focus management sync en handler `onKeyDown`.
15. ❌ **`useState [imgError]` + `<img onError>` manual** — Shadcn Avatar primitive maneja onError automático.
16. ❌ **Cross-feature imports** — shell-organism NO importa `features/*`. `lib/agent-catalog.ts` consumible cross-feature por ser SSoT.
17. ❌ **Cross-brand imports** — vitalia NUNCA importa de `nicolify/comunify/lupulo`.
18. ❌ **Tocar `core/luana-core-*/`** — engine read-only. Si necesidad emerge → escalate `/pm-luana` promotion gate.
19. ❌ **Tocar `shell-store.ts`** — F1-S5 invariant. Ribbon es stateless (URL-derived active).
20. ❌ **Tocar otros archivos `shell-organism/*.tsx`** fuera del scope (ValeriaChat, ValeriaSidebar, etc.).
21. ❌ **`make e2e*`** — Docker, crashea. Native Linux `cd vitalia/frontend && npx playwright test ...`.
22. ❌ **Nuevas routes en `app/`** — Ribbon consume URL existente, NO crea pages/layouts.
23. ❌ **Telemetría wireada en F1-S7** — TODO Fase 2 (anotado spec § Telemetría como deuda). NO instrumentar.
24. ❌ **RBAC para ConfigTab** — visible siempre F1-S7 (TODO Fase 2).
25. ❌ **Bell icon notifications, Mateo en ribbon** — anti-creep explícito spec § Out-of-scope.

## § 5 — Files in scope (vitalia/frontend ONLY)

Builder está autorizado a tocar SOLO estos paths. Cualquier otro → STOP + report:

### NEW files

```
vitalia/frontend/src/components/shared/shell-organism/Ribbon.tsx
vitalia/frontend/src/components/shared/shell-organism/Ribbon.test.tsx
vitalia/frontend/src/components/shared/shell-organism/RibbonTab.tsx
vitalia/frontend/src/components/shared/shell-organism/RibbonTab.test.tsx
vitalia/frontend/src/components/shared/shell-organism/ConfigTab.tsx
vitalia/frontend/src/components/shared/shell-organism/ConfigTab.test.tsx
vitalia/frontend/src/__tests__/architecture/test-ribbon-no-shadcn-tabs.test.ts
vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/poms/ribbon-page.pom.ts
vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-nav.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-deeplink.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-config-nav.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-invalid-agent.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-mobile.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-xss-guard.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-keyboard.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-i18n.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-avatar-fallback.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-ribbon-6-tabs/ribbon-visual.spec.ts
vitalia/frontend/e2e/__screenshots__/shell/ribbon-active-lisa.png
vitalia/frontend/e2e/__screenshots__/shell/ribbon-active-lucas.png
vitalia/frontend/e2e/__screenshots__/shell/ribbon-active-adrian.png
vitalia/frontend/e2e/__screenshots__/shell/ribbon-active-valeria.png
vitalia/frontend/e2e/__screenshots__/shell/ribbon-active-camila.png
vitalia/frontend/e2e/__screenshots__/shell/ribbon-active-config.png
vitalia/frontend/e2e/__screenshots__/shell/ribbon-idle.png
vitalia/frontend/e2e/__screenshots__/shell/ribbon-dark.png
vitalia/frontend/e2e/__screenshots__/shell/ribbon-mobile-375.png
vitalia/frontend/e2e/__screenshots__/shell/ribbon-keyboard-focus.png
vitalia/frontend/e2e/__screenshots__/shell/ribbon-hover-inactive.png
```

### MODIFY files

```
vitalia/frontend/src/lib/agent-catalog.ts                                     # EXTEND: tabLabel + defaultSubtab + AGENT_RIBBON_ORDER + extractAgentFromPath
vitalia/frontend/src/lib/__tests__/agent-catalog.test.ts                       # EXTEND: tests F1-S7 fields + helper
vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx        # MODIFY: skeleton ribbon → <Ribbon /> real, slot label "F1-S8/S10"
vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.test.tsx   # EXTEND: verify <Ribbon /> renders + skeleton sub-tabs/content preserved
vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts # EXTEND: 5 NEW names
vitalia/frontend/src/__tests__/architecture/test_server_first.test.ts          # EXTEND allowlist NEW client components (justify commit body)
vitalia/frontend/src/__tests__/architecture/test-vitalia-ui-strings-no-voseo.test.ts # EXTEND glossary check NEW microcopy
```

### DELETE files

```
(ninguno — F1-S7 NO elimina archivos)
```

### Out-of-scope (NUNCA tocar en F1-S7)

```
vitalia/backend/**                                            # ZERO BE surface
core/**                                                       # engine read-only
nicolify/** comunify/** lupulo/**                             # cross-brand forbidden
vitalia/frontend/src/components/shared/shell-organism/Valeria* # other shell organisms preserved
vitalia/frontend/src/stores/shell-store.ts                    # F1-S5 readonly invariant
vitalia/frontend/src/stores/chat-store.ts                     # F1-S6 readonly invariant
vitalia/frontend/src/app/globals.css                          # bg-agent-{slug}-soft tokens ya definidos
vitalia/frontend/src/app/layout.tsx                           # skip-link target preserved
vitalia/frontend/src/components/ui/{avatar,tooltip,button}.tsx # Shadcn primitives versiones cementadas F1-S0
vitalia/frontend/src/components/shared/shell-organism/_agent-tw-classes.ts # bg-soft helpers ya cover lisa/lucas/adrian/valeria/camila
.claude/skills/** .claude/rules/**                            # meta-paradigm out-of-scope build
docs/** vitalia/docs/architecture/** vitalia/docs/process/**  # docs out-of-scope (CHECKPOINT y per-story checkpoint OK)
```

## § 6 — Testing strategy (TDD RED→GREEN per layer)

Per `tdd-mandatory.md`, tests primero RED → componentes GREEN. Orden cementado por dependencias:

```
Layer 1: lib/agent-catalog.ts EXTEND
  RED → lib/__tests__/agent-catalog.test.ts extend (tabLabel/defaultSubtab/AGENT_RIBBON_ORDER/extractAgentFromPath)
  GREEN → lib/agent-catalog.ts EXTEND

Layer 2: Moléculas low-level (consume Layer 1 catalog)
  RED → RibbonTab.test.tsx + ConfigTab.test.tsx
  GREEN → RibbonTab.tsx + ConfigTab.tsx

Layer 3: Organism root (consume Layer 2 moléculas + Layer 1 helper)
  RED → Ribbon.test.tsx
  GREEN → Ribbon.tsx

Layer 4: Integration + arch (consume Layer 3 organism)
  RED → AppPanelSlot.test.tsx extend + test-ribbon-no-shadcn-tabs.test.ts NEW + test-no-cross-brand-shell-mirror.test.ts extend + test_server_first.test.ts extend
  GREEN → AppPanelSlot.tsx MODIFY

Layer 5: E2E behavior + visual
  RED → 9 Playwright spec files + ribbon-visual.spec.ts + POM + fixtures setup
  GREEN → assertions vs componente running en dev stack vitalia (port 3002) + visual goldens iter 1 (--update-snapshots) post Chris ratify side-by-side mockup
```

Coverage threshold: ≥20% lines/functions global. Coverage attendido en F1-S7: ≥80% en `Ribbon.tsx` (logic-heavy con roving tabindex), ≥80% en `extractAgentFromPath` (puro testeable trivial).

## § 7 — Commit + push protocol

- **Conventional Commits** obligatorio: `feat(vitalia/f1-s7): {summary}` para production code. `test(vitalia/f1-s7): {summary}` para test-only commits. `refactor(vitalia/f1-s7): ...` si solo refactor. `docs(vitalia/f1-s7): ...` si solo docs.
- **Stage por nombre exacto** — `git add path/to/file.tsx`. NUNCA `git add .` ni `-A`.
- **Push frecuente** — wip/{branch} autosave. M11: nunca >30 min sin push si hay cambios significativos.
- **Co-Authored-By line** mandatory en commit body:
  ```
  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  ```
- **Pre-commit hook** native lint check — debe pasar (NO `--no-verify`).
- **Allowlist extend justifications** en commit body para arch tests modificados (test_server_first.test.ts extend con Ribbon/RibbonTab/ConfigTab, test-no-cross-brand-shell-mirror.test.ts extend con NEW names).

## § 8 — Native dev workflow

```bash
WS=$(git rev-parse --show-toplevel)

# Unit tests
cd ${WS}/vitalia/frontend && npx tsc --noEmit
cd ${WS}/vitalia/frontend && npx eslint src/components/shared/shell-organism src/lib src/__tests__/architecture --cache
cd ${WS}/vitalia/frontend && npx vitest run src/components/shared/shell-organism src/lib src/__tests__/architecture --coverage

# E2E Playwright
cd ${WS} && bash scripts/e2e-preflight.sh          # preflight obligatorio
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test regression/vitalia-fase1-ribbon-6-tabs/

# Visual goldens (iter 1 — post Chris ratify side-by-side mockup)
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=visual regression/vitalia-fase1-ribbon-6-tabs/ribbon-visual.spec.ts --update-snapshots
```

Stack arriba (`make dev-vitalia`). NEVER `docker exec` para lint/tests/playwright. Port 3002 vitalia (NO 3001 nicolify).

## § 9 — Quality gates summary

| Gate | Comando | must_pass |
|---|---|---|
| TypeScript strict | `npx tsc --noEmit` | ✅ |
| ESLint | `npx eslint src/...` | ✅ |
| Prettier | `npx prettier --check '...'` | ✅ |
| Vitest unit | `npx vitest run ... --coverage` | ✅ ≥20% |
| Arch FSD boundaries | `npx vitest run src/__tests__/architecture/test_fsd_boundaries.test.ts` | ✅ |
| Arch cross-brand mirror | `... test-no-cross-brand-shell-mirror.test.ts` | ✅ |
| Arch agent-catalog SSoT | `... test-agent-catalog-ssot.test.ts` | ✅ |
| Arch shell-store readonly | `... test-shell-store-schema-readonly-f1-s5.test.ts` | ✅ |
| Arch ribbon-no-Shadcn-Tabs (NEW) | `... test-ribbon-no-shadcn-tabs.test.ts` | ✅ |
| Arch server-first | `... test_server_first.test.ts` | ✅ |
| Arch no-hex | `... test_no_hardcoded_colors.test.ts` | ✅ |
| Arch no-vt-classes | `... test-no-vt-classes-in-new-features.test.ts` | ✅ |
| Arch no-voseo | `... test-vitalia-ui-strings-no-voseo.test.ts` | ✅ |
| Arch skip-link | `... test-skip-link-target.test.ts` | ✅ |
| Playwright functional | `npx playwright test regression/vitalia-fase1-ribbon-6-tabs/ribbon-{nav,deeplink,config-nav,invalid-agent,mobile,xss-guard,keyboard,i18n,avatar-fallback}.spec.ts` | ✅ 9/9 |
| Playwright visual | `npx playwright test --project=visual regression/.../ribbon-visual.spec.ts` | ✅ 11/11 PNGs |
| Playwright axe | `npx playwright test ribbon-keyboard.spec.ts --grep '@axe'` | ✅ 0 wcag2aa critical |

Stop on first failure. Auditor APPROVED requires ALL green.

