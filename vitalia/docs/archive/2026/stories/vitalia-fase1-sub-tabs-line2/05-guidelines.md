<!-- voseo-allowed: glosario reference + internal guidelines -->

---
story_id: vitalia-fase1-sub-tabs-line2
brand: vitalia
type: ui-story
phase: fase-1
last_modified: 2026-05-25
architect_iter: 1
---

# F1-S8 `vitalia-fase1-sub-tabs-line2` — 05-guidelines.md

## § 1 — Must-load skills (builder bootstrap obligatorio)

`builder-frontend` (Sonnet/opencode/qwen) MUST cargar estos skills en bootstrap ANTES de tocar código. Enforcement: `/dev-team` Step 0 verifica + builder report en `T-{n}-result.md` lista "Skills consulted" verbatim. Falta del report → auditor CHANGES_REQUESTED automático.

| Skill | Cuándo cargar | Por qué |
|---|---|---|
| `frontend-expert` | Bootstrap T-1 (siempre primero) | FSD-Lite boundaries (`shared/shell-organism/` vs `lib/` vs `stores/`), Server-First default + `'use client'` solo hojas con hooks/state/handlers, Shadcn primitive reuse (NO usar Tabs Radix-based — paridad F1-S7), tokens Tailwind semánticos, Vitest unit patterns, runtime quality checklist (useEffect deps complete, no stale closures, hydration safety). |
| `tessl__react-patterns` | T-2 + T-3 (componentes con hooks) | React 19: `useState` + `useRef` + `useCallback` patterns, roving tabindex pattern verbatim F1-S7 (focus management imperativo vía refs array), event handlers `onKeyDown` con preventDefault, forwardRef composition. Diferencia clave con F1-S7: cantidad de sub-tabs dinámica (2..5) + return null total cuando no activeAgent. |
| `tessl__shadcn-ui` | T-2 (componentes que potencialmente usan primitives) | F1-S8 NO requiere Shadcn primitive nuevo. `SubTab` es `<button>` raw con `cn()` classes propias (paridad F1-S7 RibbonTab). NO usar Shadcn `<Tabs>` Radix-based (su API asume `<TabsContent>` inline incompatible con Next.js route-based nav — patrón heredado F1-S7 `test-ribbon-no-shadcn-tabs.test.ts`). |
| `tessl__tailwind` | T-1 + T-2 + T-3 + T-4 (cualquier componente con classes) | Tokens semánticos via globals.css CSS vars (Design Contract §5.1). Permitidos: `bg-card`, `bg-muted`, `bg-muted/80`, `border-border`, `text-foreground`, `text-muted-foreground`, `bg-agent-{slug}-soft`, `text-agent-{slug}`, `min-h-[42px]` arbitrary (justificado spec § Estados visuales SubTabsBar contenedor). NO hex literales. NO arbitrary values fuera del allowlist heredado (`text-[10px]` F1-S6 · `min-h-[42px]` F1-S8 NEW justificado). Dynamic agent classes via `agentBgSoftClass(slug)` + NEW `agentTextClassSubTab(slug)` switch (JIT-safe). |
| `tessl__vitest` | T-1 + T-2 + T-3 + T-4 (todos unit tests) | RTL + `@testing-library/jest-dom` + `@testing-library/user-event`. Mock `next/navigation` via `vi.mock('next/navigation', () => ({ usePathname: vi.fn(), useRouter: vi.fn(), useParams: vi.fn() }))`. Reset mocks afterEach. Use `vi.fn()` para `router.push` spy. |
| `playwright-expert` | T-5 (E2E specs + POM + visual goldens) | POM patterns en `e2e/regression/vitalia-fase1-sub-tabs-line2/poms/` (NEW path canon F1-S8 per checkpoint, paridad F1-S7 e2e/regression/vitalia-fase1-ribbon-6-tabs/), fixtures REUSE `shell-theme.fixture.ts`, port 3002 vitalia, freshness gate, axe-playwright ruleset wcag2aa, visual goldens `--update-snapshots --project=visual` iter 1 post Chris ratify side-by-side mockup `sub-tabs.html`, native Linux NUNCA docker. |
| `tessl__nextjs-app-router-modularization` | T-3 (boundary decisions) | `'use client'` boundaries: SubTabsBar root Client (hooks); SubTab Client (forwardRef + event handlers). NO crear nuevas routes — SubTabsBar consume URL existente via `usePathname()` y dispara `router.push()` a paths F1-S9 implementará. App Router preserved. |
| `claude-md-management` | Cuando dudes project-level invariants | Tenant isolation upstream (useParams.tenantId never hardcode), Spanish neutro, native-first dev workflows, multibrand boundaries (zero engine touch, zero cross-brand import). |

### NO cargar (out-of-scope explícito)

`backend-expert`, `copilot-expert`, `sales-agent-expert`, `offer-expert`, `brand-expert`, `metrics-expert`, `offer-type-preset-expert`, `tessl__langgraph`, `tessl__zod` — story es FE only chrome UI sin BE/agentic/dominio negocio/forms/LLM real. Cargar genera ruido tokens y deriva en scope creep.

## § 2 — Must-load rules (overlay vitalia + raíz)

| Rule | Trigger |
|---|---|
| `.claude/rules/frontend-fsd.md` (raíz) | shell-organism es `components/shared/` cross-feature — boundary matrix vital; `lib/agent-catalog.ts` consumido cross-shell |
| `.claude/rules/frontend-quality.md` (raíz) | ESLint 60+ rules, TS strict, Vitest 20% coverage threshold |
| `.claude/rules/spanish-text.md` (raíz) | strings UI sin voseo — 22 sub-tab labels + 6 nav aria-labels verbatim ratificados |
| `.claude/rules/tenant-isolation.md` (raíz) | URL `[tenantId]` propaga via Next routing — `useParams.tenantId` NUNCA hardcode |
| `.claude/rules/anti-duplication.md` (raíz) | cross-brand mirror scan pre-arch (§ 0.1 03-arch.md audit clean — 0 matches). Catalog SSoT EXTEND in-place (anti-duplication HARD per checkpoint Q1 — paridad F1-S7) |
| `.claude/rules/tdd-mandatory.md` (raíz) | RED tests primero por capa: catalog extend → molécula → organism → integration → e2e |
| `.claude/rules/e2e-testing.md` (raíz) | Playwright NATIVE Linux (no docker), port 3002 vitalia, preflight obligatorio |
| `.claude/rules/auditor-self-fix-policy.md` (raíz) | scope correcciones audit cycle — whitelist self-fix vs spawn dev-team |
| `vitalia/.claude/rules/shell-mockup-per-component.md` (overlay) | visual goldens side-by-side mockup `sub-tabs.html` ratificado · ratchet shrink-only · 13 PNGs scope. Gate visual ya ratificado en spec ratification fase (`ratified_visual_by_chris: true`). |
| `vitalia/.claude/rules/hipaa-lite.md` (overlay) | scope: `not_applicable` — SubTabsBar es chrome UI nav puro sin PHI |

## § 3 — Patterns required (debe usarse)

1. **Server Components donde posible.** F1-S8: SubTabsBar + SubTab son `'use client'` por hooks/handlers/forwardRef. Justified extension del allowlist `test_server_first.test.ts` con commit body explícito. AppPanelSlot SE MANTIENE Server Component (hospeda `<Ribbon />` + `<SubTabsBar />` Client via boundary natural Next.js).

2. **Named exports (no default exports)** — F1-S8 NO crea pages/layouts nuevas. Arch test enforce.

3. **Catalog SSoT EXTEND (anti-duplication HARD)** — `vitalia/frontend/src/lib/agent-catalog.ts` EXTEND in-place. NUNCA crear `lib/agents/subtabs.ts` paralelo (checkpoint Q1 cement). Anti-duplication enforced via checkpoint + spec § 0 + § 2.

4. **`RIBBON_SUBTABS` consumer pattern** — componentes leen `RIBBON_SUBTABS[activeAgent]` array directo (no `.find()` por agente). Lookup type-safe via Record<RibbonTabSlug, ...>. NUNCA hardcode `[{id:'marca', label:'Marca', icon:'🏥'}, ...]` fuera del catalog. Arch test heredado `test-agent-catalog-ssot.test.ts` enforce hex allowlist (no afecta porque emojis no son hex).

5. **`agentBgSoftClass(slug)` + `agentTextClassSubTab(slug)` Tailwind helpers** — switch pattern (heredado F1-S6 + NEW F1-S8). NUNCA template strings (`bg-agent-${slug}-soft`) — JIT no purga. EXCEPCIÓN tolerada (paridad F1-S7 Q16 WARN-1 LOW severity): template literal `hover:${agentBgSoftClass(color)}` para active:hover preserva tint — behavior correct porque active branch sin competing `hover:bg-muted`.

6. **Roving tabindex pattern verbatim F1-S7** — implementación in-line en `SubTabsBar.tsx`:
   - State `focusedIdx` parent component
   - Refs array `useRef<(HTMLButtonElement | null)[]>([])` para focus management imperativo
   - `tabIndex={focusedIdx === idx ? 0 : -1}` per sub-tab
   - `onKeyDown` handler con switch Arrow Right/Left/Home/End/Enter/Space
   - Wrap circular via modulo: `((idx % total) + total) % total`
   - Defensive `if (totalTabs === 0) return;` en focusTab + handleKeyDown (edge case post early-return null pero safety)
   - **No** auto-activate on focus — user must Enter/Space (WAI-ARIA decision rationale: route nav side-effect no debe disparar por mover focus)

7. **Active vs focused ortogonales (paridad F1-S7)** — `active = extractSubtabFromPath(usePathname()) match against subtab.id`. `focused = focusedIdx state`. NUNCA confundir.

8. **`forwardRef` mandatory en SubTab** — parent SubTabsBar necesita `tabRefs.current[idx]?.focus()` imperativo. `forwardRef<HTMLButtonElement, SubTabProps>`.

9. **`return null` total cuando no activeAgent (Q5 cement)** — early return en SubTabsBar `if (activeAgent === null || subtabs.length === 0) return null;`. NO render `<nav>` vacío + NO render placeholder div. Grid AppPanel colapsa fila naturalmente.

10. **XSS guard JSX text-children** — `{subtab.label}` + `{subtab.icon}`. NUNCA `dangerouslySetInnerHTML`. React 19 auto-escape. URL segment `subtab` raw via `extractSubtabFromPath` retorna string → SubTabsBar compara contra ids estáticos via `.find()`-equivalente (`st.id === activeSubtab`) → no match → no active (sub-tab inactive style). Auditor grep verifica cero `dangerouslySetInnerHTML`.

11. **Semantic tokens Tailwind ONLY** — `bg-card`, `bg-muted`, `bg-muted/80`, `border-border`, `text-foreground`, `text-muted-foreground`, `bg-agent-{slug}-soft` (via switch), `text-agent-{slug}` (via NEW switch). NO hex literales (allowlist heredado: `agent-catalog.ts` único permitido para `hex` field metadata). `min-h-[42px]` arbitrary value JUSTIFIED spec § Estados visuales SubTabsBar contenedor + paridad heredado `text-[10px]` F1-S6 allowlist (auditor verifica que no expandimos arbitrary values más allá).

12. **`router.push` con `useParams.tenantId`** — NUNCA hardcodear tenantId. Pattern paridad F1-S7:
    ```ts
    const params = useParams<{ tenantId: string }>();
    if (!params?.tenantId || activeAgent === null) return; // defensive early return
    router.push(`/${tenantId}/${activeAgent}/${subtabId}`);
    ```

13. **`extractSubtabFromPath` puro** — utility function en `lib/agent-catalog.ts` co-located con `extractAgentFromPath` (F1-S7). Pure (no hooks, no side effects). Retorna `string | null`. Defensive nullable input handling.

14. **WAI-ARIA tablist completo (paridad F1-S7)** — verbatim spec § Accessibility:
    - `<nav role="tablist" aria-label="Sub-secciones {AgentName}">` (dinámico per agente — Lisa/Lucas/Adrián/Valeria/Camila/Configuración)
    - per button: `role="tab"` + `aria-selected={active}` + `tabIndex={0 | -1}`
    - Emoji `<span>` adyacente al label `<span>` — emoji `aria-hidden="true"` para no leer "casa"/"stetoscopio" inconsistente per OS

15. **Focus-visible mandatory** — `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1` en SubTab. NO `focus:` (mouse-click focus visible distracts). NO outline default.

16. **Spanish neutro LatAm verbatim** — 22 sub-tab labels + 6 nav aria-labels spec § 1 + § 6:
    - Sub-tab labels (22): `Marca`, `Doctores`, `Servicios`, `Compliance`, `Lanzar`, `En vuelo`, `Recursos`, `Resultados`, `Mercado`, `Inbox`, `Embudo`, `Outbound`, `Propuestas`, `Agenda`, `Pacientes`, `Voz del paciente`, `Reactivar`, `Multiplicar`, `Reputación` (con tilde), `Mi cuenta`, `Conexiones`, `Avanzado`
    - Nav aria-labels (6): `Sub-secciones Lisa`, `Sub-secciones Lucas`, `Sub-secciones Adrián` (con tilde), `Sub-secciones Valeria`, `Sub-secciones Camila`, `Sub-secciones Configuración` (con tilde)
    NO voseo (no "Reactivá"/"Multiplicalo"/"Configuralo"/"andá"). Tildes correctas. Arch test `test-vitalia-ui-strings-no-voseo.test.ts` EXTEND.

17. **`useCallback` para handlers (paridad F1-S7 D8)** — `navigateTo`, `focusTab`, `handleKeyDown` envueltos en `useCallback([deps])`. Evita re-renders innecesarios de SubTab children.

18. **Active state Lucas exception** — `agentTextClassSubTab(slug)` retorna `text-foreground` para `lucas` (NO `text-agent-lucas` saturated). Razón: agent-lucas hex `#111111` (near-black) sobre `bg-agent-lucas-soft` rgba ~10% black produce contrast pobre. Helper específico al uso SubTab (NO sobrescribir `agentTextClass` existente que tiene semántica saturated para TypingIndicator/DelegateMarker).

19. **Active state Config exception** — `color === "config"` branch en SubTab.tsx usa `bg-muted + text-foreground` neutral. Config NO es agente — no tiene color marca. Mockup ratificado verbatim.

20. **`whitespace-nowrap` HARD** — paridad F1-S7 RibbonTab Q15 cement. SubTab label NO wrap a 2 líneas en widths estrechos. Garantiza barra h-[42px] uniforme.

## § 4 — Patterns forbidden (NUNCA usar)

1. ❌ **Crear `lib/agents/subtabs.ts`** — anti-duplication HARD (Q1 cement). Catalog SSoT vive en `lib/agent-catalog.ts` (F1-S6 + F1-S7). EXTEND in-place mandatory.
2. ❌ **`<Tabs>` / `<TabsList>` / `<TabsTrigger>` / `<TabsContent>` Shadcn Radix-based** — incompatible con route nav (asume `<TabsContent>` inline). Arch test `test-ribbon-no-shadcn-tabs.test.ts` heredado F1-S7 enforce (lista no extiende a SubTabsBar/SubTab pero voluntary acoplamiento mismo pattern verificable code review).
3. ❌ **`bg-agent-${slug}-soft` template string** — Tailwind JIT no purga. Usar `agentBgSoftClass(slug)` switch. EXCEPCIÓN tolerada: `hover:${agentBgSoftClass(slug)}` para active:hover preserva tint (Q16 cement paridad F1-S7 WARN-1 LOW).
4. ❌ **Hex literals en componentes** — `#7b2d91`, `#00D084`, etc. forbidden fuera de `agent-catalog.ts` hex metadata. Arch test enforce.
5. ❌ **Hardcoded sub-tab labels/ids/icons** — `'Doctores'`, `'marca'`, `'🏥'` forbidden fuera del catalog. Consume `RIBBON_SUBTABS[agent]` array.
6. ❌ **Hardcoded tenantId en router.push** — usar `useParams<{ tenantId: string }>()`.
7. ❌ **Hardcoded activeAgent en router.push** — usar derivado `extractAgentFromPath(usePathname())`.
8. ❌ **Auto-activate sub-tab on focus** — focus mueve cursor, NO dispara `router.push`. Enter/Space activan explícito.
9. ❌ **`dangerouslySetInnerHTML`** — XSS attack vector. React JSX text-children + auto-escape suficiente.
10. ❌ **`useEffect` para focus inicial** — stale closure trap. Focus management sync en handler `onKeyDown`.
11. ❌ **`useState [imgError]` + `<img onError>`** — sub-tabs usan emoji nativo, no PNG. Sin avatar fallback.
12. ❌ **Cross-feature imports** — shell-organism NO importa `features/*`. `lib/agent-catalog.ts` consumible cross-feature por ser SSoT.
13. ❌ **Cross-brand imports** — vitalia NUNCA importa de `nicolify/comunify/lupulo`.
14. ❌ **Tocar `core/luana-core-*/`** — engine read-only. Si necesidad emerge → escalate `/pm-luana` promotion gate.
15. ❌ **Tocar `shell-store.ts`** — F1-S5 invariant. SubTabsBar es stateless (URL-derived active + local state focusedIdx).
16. ❌ **Tocar otros archivos `shell-organism/*.tsx`** fuera del scope (ValeriaChat, ValeriaSidebar, Ribbon, RibbonTab, ConfigTab, etc.). El único MODIFY permitido en `shell-organism/` es `AppPanelSlot.tsx` (swap skeleton) + `_agent-tw-classes.ts` (EXTEND agentTextClassSubTab helper).
17. ❌ **`make e2e*`** — Docker, crashea. Native Linux `cd vitalia/frontend && npx playwright test ...`.
18. ❌ **Nuevas routes en `app/`** — SubTabsBar consume URL existente, NO crea pages/layouts.
19. ❌ **Telemetría wireada en F1-S8** — TODO Fase 2 (spec § Out-of-scope `sub_tab_clicked` queda anotado). NO instrumentar.
20. ❌ **RBAC para `compliance` (Lisa) o `avanzado` (Config)** — visibles siempre F1-S8 (TODO Fase 2 per spec § Out-of-scope).
21. ❌ **Redirect `/{tenantId}/{agent}` → `/{tenantId}/{agent}/{defaultSubtab}`** — eso es F1-S9 routing-shell scope, NO F1-S8.
22. ❌ **if-statements `mode === 'web'` branching** — decisión spec § 0 cementada: SubTabsBar renderiza idéntico en modos `agentic` y `web`.
23. ❌ **Sub-tabs para Mateo** — Mateo transversal, excluido del Ribbon F1-S7 → consecuentemente excluido del SubTabsBar F1-S8. `RIBBON_SUBTABS` es `Record<RibbonTabSlug, ...>` (excluye mateo por construcción).
24. ❌ **Breadcrumb "vía Valeria" indicator** — postponed.
25. ❌ **Mockup HTML edit post-ratify Chris** — gate visual ya ratificado (`ratified_visual_by_chris: true`). Cualquier cambio visual significativo requiere re-ratificación explícita Chris (no se renueva silencioso).

## § 5 — Files in scope (vitalia/frontend ONLY)

Builder está autorizado a tocar SOLO estos paths. Cualquier otro → STOP + report:

### NEW files

```
vitalia/frontend/src/components/shared/shell-organism/SubTabsBar.tsx
vitalia/frontend/src/components/shared/shell-organism/SubTabsBar.test.tsx
vitalia/frontend/src/components/shared/shell-organism/SubTab.tsx
vitalia/frontend/src/components/shared/shell-organism/SubTab.test.tsx
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/poms/sub-tabs-bar-page.pom.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-nav.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-agent-change.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-deeplink.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-null-agent.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-invalid-subtab.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-mobile-overflow.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-xss-guard.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-keyboard.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-i18n.spec.ts
vitalia/frontend/e2e/regression/vitalia-fase1-sub-tabs-line2/visual-goldens.spec.ts
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-lisa-light.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-lisa-dark.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-lucas-light.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-lucas-dark.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-adrian-light.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-adrian-dark.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-valeria-light.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-valeria-dark.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-camila-light.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-camila-dark.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-config-light.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-config-dark.png
vitalia/frontend/e2e/__screenshots__/shell/sub-tabs-mobile-lucas-375.png
```

### MODIFY files

```
vitalia/frontend/src/lib/agent-catalog.ts                                      # EXTEND: SubTabMeta interface + RIBBON_SUBTABS Record + extractSubtabFromPath helper
vitalia/frontend/src/lib/__tests__/agent-catalog.test.ts                        # EXTEND: tests F1-S8 fields + helper + 22 sub-tab labels verbatim
vitalia/frontend/src/components/shared/shell-organism/_agent-tw-classes.ts     # EXTEND: agentTextClassSubTab(slug) helper (Lucas exception)
vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx         # MODIFY: skeleton sub-tabs (líneas 45-54) → <SubTabsBar /> real, slot label "F1-S10"
vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.test.tsx    # EXTEND: verify <SubTabsBar /> renders + skeleton sub-tabs REMOVED del DOM + content skeleton preserved
vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts # EXTEND: 5 NEW names (SubTabsBar, SubTab, RIBBON_SUBTABS, extractSubtabFromPath, SubTabMeta)
vitalia/frontend/src/__tests__/architecture/test_server_first.test.ts           # EXTEND allowlist 2 NEW client components (SubTabsBar, SubTab — justify commit body)
vitalia/frontend/src/__tests__/architecture/test-vitalia-ui-strings-no-voseo.test.ts # EXTEND glossary check NEW microcopy (22 sub-tab labels + 6 nav aria-labels)
```

### DELETE files

```
(ninguno — F1-S8 NO elimina archivos; reemplaza JSX inline en AppPanelSlot.tsx solamente)
```

### Out-of-scope (NUNCA tocar en F1-S8)

```
vitalia/backend/**                                                            # ZERO BE surface
core/**                                                                       # engine read-only
nicolify/** comunify/** lupulo/**                                             # cross-brand forbidden
vitalia/frontend/src/components/shared/shell-organism/{Ribbon,RibbonTab,ConfigTab,Valeria*}.tsx  # F1-S5/F1-S6/F1-S7 invariant
vitalia/frontend/src/stores/shell-store.ts                                    # F1-S5 readonly invariant
vitalia/frontend/src/stores/chat-store.ts                                     # F1-S6 readonly invariant
vitalia/frontend/src/app/globals.css                                          # bg-agent-{slug}-soft + text-agent-{slug} tokens ya definidos F1-S1/F1-S6
vitalia/frontend/src/app/layout.tsx                                           # skip-link target preserved
vitalia/frontend/src/components/ui/**                                         # Shadcn primitives cementadas F1-S0 (no Shadcn primitive needed por F1-S8)
.claude/skills/** .claude/rules/**                                            # meta-paradigm out-of-scope build
docs/** vitalia/docs/architecture/** vitalia/docs/process/**                  # docs out-of-scope (CHECKPOINT y per-story checkpoint OK)
vitalia/docs/product/stories/vitalia-fase1-sub-tabs-line2/mockups/sub-tabs.html  # gate visual YA ratificado — NO modificar post-ratify Chris
```

## § 6 — Testing strategy (TDD RED→GREEN per layer)

Per `tdd-mandatory.md`, tests primero RED → componentes GREEN. Orden cementado por dependencias:

```
Layer 1: lib/agent-catalog.ts EXTEND
  RED → lib/__tests__/agent-catalog.test.ts extend (SubTabMeta shape + RIBBON_SUBTABS 22 sub-tabs distribution + extractSubtabFromPath)
  GREEN → lib/agent-catalog.ts EXTEND

Layer 2: _agent-tw-classes.ts EXTEND
  RED → optional unit test (inline en SubTab.test.tsx via helper import)
  GREEN → _agent-tw-classes.ts EXTEND (agentTextClassSubTab Lucas exception)

Layer 3: Molécula SubTab (consume Layer 1 SubTabMeta + Layer 2 helper)
  RED → SubTab.test.tsx
  GREEN → SubTab.tsx

Layer 4: Organism SubTabsBar (consume Layer 3 molécula + Layer 1 RIBBON_SUBTABS + extractSubtabFromPath + Ribbon ya existente F1-S7 indirectamente)
  RED → SubTabsBar.test.tsx
  GREEN → SubTabsBar.tsx

Layer 5: Integration + arch (consume Layer 4 organism)
  RED → AppPanelSlot.test.tsx extend + test-no-cross-brand-shell-mirror.test.ts extend + test_server_first.test.ts extend + test-vitalia-ui-strings-no-voseo.test.ts extend
  GREEN → AppPanelSlot.tsx MODIFY

Layer 6: E2E behavior + visual
  RED → POM sub-tabs-bar-page.pom.ts + 8 Playwright spec files + visual-goldens.spec.ts setup
  GREEN → assertions vs componente running en dev stack vitalia (port 3002) + visual goldens iter 1 (--update-snapshots) post Chris ratify side-by-side mockup sub-tabs.html (ya ratificado)
```

Coverage threshold: ≥20% lines/functions global. Cobertura attendida en F1-S8: ≥80% en `SubTabsBar.tsx` (logic-heavy con roving tabindex + null returns + early returns), ≥80% en `extractSubtabFromPath` (puro testeable trivial).

## § 7 — Commit + push protocol

- **Conventional Commits** obligatorio: `feat(vitalia/f1-s8): {summary}` para production code. `test(vitalia/f1-s8): {summary}` para test-only commits. `refactor(vitalia/f1-s8): ...` si solo refactor. `docs(vitalia/f1-s8): ...` si solo docs.
- **Stage por nombre exacto** — `git add path/to/file.tsx`. NUNCA `git add .` ni `-A`.
- **Push frecuente** — wip/{branch} autosave. M11: nunca >30 min sin push si hay cambios significativos.
- **Co-Authored-By line** mandatory en commit body:
  ```
  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  ```
- **Pre-commit hook** native lint check — debe pasar (NO `--no-verify`).
- **Allowlist EXTEND justifications** en commit body para arch tests modificados (test_server_first.test.ts EXTEND con SubTabsBar/SubTab, test-no-cross-brand-shell-mirror.test.ts EXTEND con NEW names, test-vitalia-ui-strings-no-voseo.test.ts EXTEND con 22 NEW labels).

## § 8 — Native dev workflow

```bash
WS=$(git rev-parse --show-toplevel)

# Unit tests
cd ${WS}/vitalia/frontend && npx tsc --noEmit
cd ${WS}/vitalia/frontend && npx eslint src/components/shared/shell-organism src/lib src/__tests__/architecture --cache
cd ${WS}/vitalia/frontend && npx vitest run src/components/shared/shell-organism src/lib src/__tests__/architecture --coverage

# E2E Playwright
cd ${WS} && bash scripts/e2e-preflight.sh          # preflight obligatorio
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test regression/vitalia-fase1-sub-tabs-line2/

# Visual goldens (iter 1 — post Chris ratify side-by-side mockup — ya ratificado pre-arch)
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=visual regression/vitalia-fase1-sub-tabs-line2/visual-goldens.spec.ts --update-snapshots
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
| Arch cross-brand mirror (EXTEND) | `... test-no-cross-brand-shell-mirror.test.ts` | ✅ |
| Arch agent-catalog SSoT | `... test-agent-catalog-ssot.test.ts` | ✅ |
| Arch shell-store readonly | `... test-shell-store-schema-readonly-f1-s5.test.ts` | ✅ |
| Arch ribbon-no-Shadcn-Tabs (heredado F1-S7) | `... test-ribbon-no-shadcn-tabs.test.ts` | ✅ |
| Arch server-first (EXTEND) | `... test_server_first.test.ts` | ✅ |
| Arch no-hex | `... test_no_hardcoded_colors.test.ts` | ✅ |
| Arch no-vt-classes | `... test-no-vt-classes-in-new-features.test.ts` | ✅ |
| Arch no-voseo (EXTEND) | `... test-vitalia-ui-strings-no-voseo.test.ts` | ✅ |
| Arch skip-link | `... test-skip-link-target.test.ts` | ✅ |
| Playwright functional | `npx playwright test regression/vitalia-fase1-sub-tabs-line2/sub-tabs-{nav,agent-change,deeplink,null-agent,invalid-subtab,mobile-overflow,xss-guard,keyboard,i18n}.spec.ts` | ✅ 9/9 |
| Playwright visual | `npx playwright test --project=visual regression/.../visual-goldens.spec.ts` | ✅ 13/13 PNGs |
| Playwright axe | `npx playwright test sub-tabs-keyboard.spec.ts --grep '@axe'` | ✅ 0 wcag2aa critical |

Stop on first failure. Auditor APPROVED requires ALL green.

