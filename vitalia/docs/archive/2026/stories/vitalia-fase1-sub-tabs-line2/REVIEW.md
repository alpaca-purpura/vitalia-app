<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Frontend Code Review · F1-S8 vitalia-fase1-sub-tabs-line2

**Date:** 2026-05-25
**Story:** `vitalia-fase1-sub-tabs-line2` (state=reviewing)
**Brand:** vitalia
**Tickets audited:** T-1..T-6 (single pass, story-level per F1-S7 pattern)
**Commits:** `09152867` · `8350d912` · `e2b68ad2` · `27fbf9db` · `76b66d62` · `33c2af59` · `7bcef820` (auditor self-fix iter 1)
**Files reviewed:** 16 (5 production · 5 vitest · 5 arch-extend · 11 e2e + POM in 06-audit/gherkin-matrix.md)
**Domains touched:** shell-organism (FE only — no BE, no agentic surface)
**Skills consulted:** frontend-expert · tessl__react-patterns · tessl__shadcn-ui · tessl__tailwind · tessl__vitest · tessl__nextjs-app-router-modularization · playwright-expert · brand-docs-schema · anti-duplication · spanish-text · auditor-self-fix-policy · auditor-downstream-regression
**Overlay rules consulted:** `vitalia/.claude/rules/shell-mockup-per-component.md` (gate visual ratificado mockup HTML iter 1 2026-05-25T09:05Z)
**Live-verified:** N (Playwright runtime deferred to /pm-vitalia merge phase per architect cement; mockup HTML ratified by Chris satisfies pre-arch gate)

## Verdict: **APPROVED**

5/5 gates GREEN (tsc · ESLint · prettier · Vitest unit 179/179 · arch fitness 118/118). Q1-Q5 batch_1_decisions honored verbatim. Anti-duplication F1-S7 pattern preserved (zero `lib/agents/` directory). Cross-brand mirror zero across nicolify/comunify/lupulo. 10 Playwright specs + POM + axe wcag2aa scoped. Self-fix iter 1 within whitelist #2 bounds (1 file · 4 lines · format only).

## /test-frontend Gate Status (consumed from gate-output.json iter 2)

| Gate | Step | Result | Detail |
|---|---|---|---|
| QUALITY | tsc --noEmit | **PASS** | 0 errors strict |
| QUALITY | ESLint (60+ rules) | **PASS** | 0 errors · 0 warnings added |
| QUALITY | Prettier | **PASS** | 10 F1-S8 files clean post self-fix iter 1 |
| FUNCTIONAL | Vitest unit (F1-S8 subset) | **PASS** | 179/179 (agent-catalog 83 + _agent-tw-classes 13 + SubTab 34 + SubTabsBar 36 + AppPanelSlot 13) |
| ARCHITECTURAL | Vitest arch fitness | **PASS** | 118/118 (incluye F1-S8 extensions: cross-brand mirror 5 names + voseo glossary 22 labels + 6 aria-labels) |

Independent re-verification (this auditor session, native Linux):
- `npx tsc --noEmit` → exit 0 ✅
- `npx eslint src/components/shared/shell-organism/SubTab.tsx SubTabsBar.tsx + src/lib/agent-catalog.ts` → exit 0 ✅
- `npx vitest run` 5 F1-S8 unit suites → 179/179 PASS ✅
- `npx vitest run` 2 F1-S8 arch suites → 56/56 PASS ✅
- Cross-brand grep `SubTabsBar|SubTab|RIBBON_SUBTABS|extractSubtabFromPath|agentTextClassSubTab` en `{nicolify,comunify,lupulo}/frontend/src` → 0 matches ✅

## Category Summary (12 categories + downstream + phase D + decisions cite)

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | FSD-Lite (boundaries · barrels · cross-feature ban) | **PASS** | `shell-organism/` componentes consumen `@/lib/agent-catalog`, `@/lib/utils` (cn), internal helper `./_agent-tw-classes`. No cross-feature deep import. No default export (named only — paridad F1-S7). |
| 2 | Server/Client correctness | **PASS** | `AppPanelSlot.tsx` Server Component (NO `"use client"`); hosts `<Ribbon />` + `<SubTabsBar />` Client Components — patrón Next 15 App Router natural Server→Client boundary correcto. `SubTab.tsx` + `SubTabsBar.tsx` declaran `"use client"` (consumen `useState`/`useRef`/`useCallback`/`usePathname`/`useRouter`/`useParams` + event handlers `onClick`/`onFocus`/`onKeyDown`). `agent-catalog.ts` lib pura (no hooks, no "use client"). |
| 3 | React patterns baseline (tessl__react-patterns) | **PASS** | `SubTabsBar` con stable keys (`subtab.id`, no array index); `useCallback` correcto para `navigateTo` + `focusTab` + `handleKeyDown` con deps array completo. `useRef<(HTMLButtonElement \| null)[]>` para imperative focus management (roving tabindex). `forwardRef` en `SubTab`. Q5 early-return guard antes de hooks-dependent work. Loading/error/empty states N/A (UI navegacional pura sin async). |
| 4 | Code quality (gates 2/3/5/6/7 + warning baselines) | **PASS** | tsc + ESLint + prettier clean. No `// @ts-expect-error`, no `eslint-disable`. No new `any`. No jscpd-detectable duplication (cross-brand mirror grep zero). |
| 5 | Accessibility (WCAG AA · roving tabindex · aria-* · focus visible) | **PASS** | `role="tablist"` + dynamic `aria-label="Sub-secciones {name}"` (config → "Configuración" with tilde). `role="tab"` + `aria-selected`. Roving tabindex verbatim from Ribbon: focus ring `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1` (no plain `focus:` classes). Emoji `aria-hidden="true"` (decorative). Keyboard: ArrowL/R + Home/End + Enter/Space + circular wrap. Axe wcag2aa scoped `[data-testid=sub-tabs-bar]` (sub-tabs-keyboard.spec.ts SC-8-axe). |
| 6 | Forms (RHF + Zod) | **N/A** | Story is UI nav-only — no forms, no inputs, no Zod schemas. |
| 7 | Multitenancy (X-Tenant-ID injection) | **N/A → PASS** | No API calls (FE static data). `params?.tenantId` extraction guarded with null-check + early return — no cross-tenant leak risk. Route shape `/{tenantId}/{agent}/{subtab}` honored. |
| 8 | Master-data / Spanish neutro LatAm | **PASS** | 22 RIBBON_SUBTABS labels verbatim Spanish neutro (Marca · Doctores · Servicios · Compliance · Lanzar · En vuelo · Recursos · Resultados · Mercado · Inbox · Embudo · Outbound · Propuestas · Agenda · Pacientes · Voz del paciente · Reactivar · Multiplicar · Reputación · Mi cuenta · Conexiones · Avanzado). Tildes correctas (Reputación · Configuración · Adrián). Zero voseo verbs (validated by `test-vitalia-ui-strings-no-voseo.test.ts` F1-S8 describe block). |
| 9 | Security / dependencies | **PASS** | XSS guard: extractSubtabFromPath devuelve segmento raw, comparado contra ids estáticos `RIBBON_SUBTABS[agent].find(t => t.id === activeSubtab)` → no match → no active. React JSX auto-escape on render. No `dangerouslySetInnerHTML`. No `eval`. No deps added. |
| 10 | Tests / TDD-mandatory | **PASS** | RED→GREEN per layer: agent-catalog tests written T-1 BEFORE constant exports validated (30 new F1-S8 tests); SubTab tests written T-3 BEFORE component shape stabilized (34 tests); SubTabsBar tests written T-4 BEFORE roving tabindex behavior validated (36 tests); AppPanelSlot tests UPDATED T-5 con mount real `<SubTabsBar />` (13 tests). Coverage threshold ≥20% — gate verde. Playwright 10 specs + POM correspondientes a SC-1..SC-10. |
| 11 | Domain alignment / agentic UI hygiene | **PASS** | No agentic touches. Brand-local shell-organism. No FE hardcoded archetype/format/preset labels. RIBBON_SUBTABS consume agents catalog SSoT — no mirror. |
| 12 | Architecture fitness (18 FE arch tests) | **PASS** | All 18 tests PASS. F1-S8 EXTENDED 3 tests: (1) `test-no-cross-brand-shell-mirror.test.ts` +5 nuevos asserts (SubTabsBar · SubTab · RIBBON_SUBTABS · extractSubtabFromPath · SubTabMeta) zero matches cross-brand; (2) `test-vitalia-ui-strings-no-voseo.test.ts` +F1-S8 describe block (2 file voseo scans + 22 label verbatim + 6 aria-label tilde checks); (3) `test_server_first.test.ts` continues PASS (allowlist not grown). No allowlist growth requiring justification. |
| 13 | Mirror detection (cross-feature + cross-brand) | **PASS** | Q1 cement enforcement: NO `vitalia/frontend/src/lib/agents/subtabs.ts` exists. NO `vitalia/frontend/src/lib/agents/routing.ts` exists. Directory `src/lib/agents/` does NOT exist at all. RIBBON_SUBTABS + extractSubtabFromPath live in `agent-catalog.ts` per Q1 batch_1_decisions verbatim. Anti-duplication F1-S7 pattern preserved (R3 + 05-guidelines § Existing systems audit honored). Cross-brand mirror grep across nicolify/comunify/lupulo = 0 matches for all 5 new identifiers. |
| 14 | Decisions honored cite (R6) | **PASS** | Each of 6 ticket commits cites Q1-Q5 + D18/D19 cement decisions in commit body. T-1: Q1 SSoT path extend agent-catalog. T-2 + T-3: D18 Lucas exception + D19 Config exception. T-4: Q4 height + Q5 return null + Q3 roving tabindex. T-5: F1-S7 anti-duplication pattern extension. T-6: SC-1..SC-9 + visual goldens deferral architecturally authorized. |

### Downstream regression scope (Step 4.5 · auditor-downstream-regression.md)

- **Engine edits?** NO. Zero touch to `core/luana-core-*/src/`.
- **Cross-brand mirror?** Verified zero — independent grep across nicolify/comunify/lupulo `frontend/src/`.
- **Brand extension agentic?** NO (no `vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/` touched).
- **Cross-feature FE consumer?** Path `vitalia/frontend/src/lib/agent-catalog.ts` is consumed by F1-S6 ChatHeader, F1-S7 Ribbon + ConfigTab + RibbonTab — gate-output.json `command: test-frontend (vitalia FE suite)` cubre vitest run de TODA la suite (179 unit F1-S8 + 118 arch + F1-S6/S7 regressions implícitas via full vitest run). Gate verde verifica que extensión retro-compatible (sin breaking change a AgentSlug, RibbonTabSlug, AGENT_CATALOG, extractAgentFromPath, agentBgSoftClass, agentTextClass).
- Verdict: no downstream regression risk identified.

### Phase D (gherkin matrix)

Full matrix written to `06-audit/gherkin-matrix.md`. Summary:
- 10/10 scenarios with test file present
- 9 Playwright behavior specs runtime-deferred to /pm-vitalia merge phase (architecturally authorized; mockup HTML ratified Chris satisfies pre-arch gate)
- SC-9 i18n partially covered by Vitest arch suite (22 labels + 6 aria-labels verbatim)
- SC-10 visual goldens iter-1 deferred (architect cement — require live app + Chris re-ratify post-implementation)
- 5 mandatory sub-categories (race_condition · concurrent_users · network_failure · empty_state · large_dataset) marked `not_applicable` con razones justificadas en spec § 10 último cuadro

## Warning baseline movement

Not applicable to this story — vitalia/frontend mantiene su propio ratchet (no shared baselines `check-file 323` / `jsdoc 616` / `react-perf 1509` heredados del root paradigm, son para nicolify legacy). Vitalia FE arch suite: 118/118 PASS sin growth. F1-S8 ratchet:
- cross-brand mirror allowlist: shrink-only — F1-S8 ADD 5 new guarded names · no allowlist entries added
- voseo allowlist: shrink-only — F1-S8 ADD 22 label + 6 aria-label assertions · no allowlist entries added
- server-first allowlist: unchanged (0 entries — baseline empty since T-infra-4)

## Findings

**Zero FAIL findings. Zero WARN findings.**

## Self-fix iter 1 verification

Commit `7bcef820` · auditor self-fix Caso C per `.claude/rules/auditor-self-fix-policy.md`:
- **Whitelist category #2**: format-only (`prettier auto-fix`)
- **Files modified**: 1 (`AppPanelSlot.test.tsx`)
- **Lines modified**: 4 (1 insertion, 3 deletions) — within HARD limit ≤10 lines
- **Logic change**: 0 (formatting only — verified by git diff inspection)
- **Whitelist boundary**: WITHIN (≤2 files · ≤10 lines · format only)
- **Cap usage**: self_fix_iter=1 of 4 max · audit_iterations=1 of 3 max
- **Verdict**: VALID self-fix · post-fix prettier PASS · zero functional regression risk

## Batch_1_decisions Q1-Q5 verification per item

| Q | Decisión | Honored? | Verification |
|---|---|---|---|
| **Q1** | EXTEND `agent-catalog.ts` (NO crear `lib/agents/subtabs.ts`) | ✅ verbatim | `src/lib/agents/` directory does not exist · RIBBON_SUBTABS + SubTabMeta + extractSubtabFromPath live in `agent-catalog.ts` lines 180-274 (single file, single SSoT). |
| **Q2** | Emojis (paridad ribbon catalog) | ✅ verbatim | All 22 RIBBON_SUBTABS entries usan emojis (🏥 👨‍⚕️ 🩺 🛡️ 🚀 📡 📚 📈 🌍 💬 🎯 📣 💼 📆 👥 🎤 🪃 🤝 📊 🏢 🔌 🔬) — no lucide imports. |
| **Q3** | Roving tabindex (paridad F1-S7 Ribbon) | ✅ verbatim | `SubTabsBar.tsx` líneas 77-139: `useState` focusedIdx + `useRef` tabRefs[] + `focusTab` callback + `handleKeyDown` switch (ArrowLeft/Right/Home/End/Enter/Space) con circular wrap mathematically safe (modulo positive). SubTab.tsx prop `tabIndex: 0 \| -1`. Comportamiento idéntico al Ribbon.tsx F1-S7. |
| **Q4** | `min-h-[42px]` + container className | ✅ verbatim | `SubTabsBar.tsx` línea 152: `"min-h-[42px] bg-card border-b border-border flex items-center px-4 gap-1 overflow-x-auto"` — coincide spec § 2 SubTabsBar wireframe exacto. |
| **Q5** | `return null` total cuando activeAgent null o subtabs empty | ✅ verbatim | `SubTabsBar.tsx` líneas 141-144: `if (activeAgent === null \|\| subtabs.length === 0) return null;` — antes del JSX render. Cobre caso mateo (RIBBON_SUBTABS.mateo = []) + invalid agent (extractAgentFromPath returns null). |

### Cement decisions adicionales (architect-level)

- **D18 Lucas excepción** (active state → `text-foreground` no `text-agent-lucas`): ✅ honored en `_agent-tw-classes.ts` `agentTextClassSubTab("lucas")` línea 102-103 + comentario explicativo near-black hex #111111.
- **D19 Config excepción** (active state → `bg-muted` + `text-foreground` no agent color): ✅ honored en `SubTab.tsx` líneas 77-80 (rama isConfig) + `agentTextClassSubTab("config")` línea 108-110.

## Contract / UI-SPEC compliance

- [x] TypeScript types (`SubTabMeta`, `SubTabProps`, `SubTabsBarProps` implicit) match 03-arch.md § 2.4 spec verbatim
- [x] Components from `01-spec.md § 2` implemented (`SubTabsBar.tsx` + `SubTab.tsx` + `AppPanelSlot.tsx` MODIFY)
- [x] Server/Client boundaries match (AppPanelSlot Server hosts SubTabsBar/Ribbon Client per Next 15 App Router pattern)
- [x] Data flow matches (URL-derived via `extractAgentFromPath` + `extractSubtabFromPath` — no API, no React Query, no forms)
- [x] Interaction patterns (click → router.push · keyboard roving tabindex · focus management)
- [x] Test surfaces from UI-SPEC § 12 exist (Vitest unit per file · Playwright POM + 10 specs · arch fitness extensions)
- [x] Capability YAML pendiente · F1-S8 merge phase (`/pm-vitalia` write `vitalia/docs/product/capabilities/shell-organism/sub-tabs.yaml` per spec § 13)

## Allowlist movement

- Cross-brand mirror allowlist: **shrunk effectively** — 5 new guarded names added, 0 allowlist entries added (ratchet positive).
- Voseo allowlist: **shrunk effectively** — 28 new assertions (22 labels + 6 aria-labels), 0 allowlist entries added.
- Server-first allowlist: **unchanged** — baseline 0 entries since T-infra-4, F1-S8 components correctly declare "use client" where needed.

## Native-First audit

- [x] No `docker exec ... tsc|eslint|vitest|playwright` in commits 09152867..33c2af59
- [x] No `make e2e` / `make e2e-smoke` in commits (E2E specs NOT executed in this gate; deferred to merge phase per architect)
- [x] No `git add .` / `git add -A` / `git add -u` in commits (all use `git add <file>` exact paths)
- [x] Self-fix commit 7bcef820 uses native `npx prettier --write` per whitelist #2 protocol

## Live verification audit

- **User-facing change?** YES (SubTabsBar visible debajo Ribbon en AppPanelSlot)
- **`chrome-devtools-verify` evidence cited?** NO — but architecturally substituted by:
  - Mockup HTML `sub-tabs.html` (503 LOC, 6 agent variants × light/dark × 4 SubTab states) ratificado Chris 2026-05-25T09:05Z (gate visual obligatorio `shell-mockup-per-component.md` ya cumplido)
  - 10 Playwright specs + POM written (runtime deferred to /pm-vitalia merge phase)
  - Vitest arch suite F1-S8 describe block verifies Spanish neutro labels verbatim
- **Verdict**: ACCEPTABLE. The story explicitly authorizes deferral in `03-arch.md` + checkpoint frontmatter `ratified_visual_by_chris: true iter 1`. Auditor flags for /pm-vitalia merge phase: invoke `chrome-devtools-verify` OR Chris staging gate manual to validate runtime behavior against mockup HTML before transitioning state to done.

## Verdict math

Mechanical application:
- Any FAIL Cat 1/2/3/7/11/12/14: NO → NO overall FAIL
- Allowlist or warning baseline grew without justified commit: NO → NO overall FAIL
- Any /test-frontend blocker (2/3/4) FAIL: NO → NO overall FAIL
- Any 20 arch fitness tests FAIL: NO → NO overall FAIL
- Downstream regression scope tests FAIL: NO → NO overall FAIL
- Decisions honored cite (Cat 14) FAIL: NO → NO overall FAIL
- Two or more category WARNs: NO → NO overall WARN
- Otherwise: **PASS**

## Recommendations for /pm-vitalia merge

1. **Phase E (capability YAML)**: write `vitalia/docs/product/capabilities/shell-organism/sub-tabs.yaml` per spec § 13. status `live` + date_introduced + story_introduced + surfaces (config: agent-catalog.ts · frontend: SubTabsBar + SubTab · tests: 5 vitest + 10 e2e specs + POM) + dependencies (agent-catalog.ts F1-S7 SSoT · Ribbon.tsx · AppPanelSlot.tsx).
2. **Phase F (07-merge.md)**: 5 secciones cementadas per story-closure-gate.md schema (story summary · capability shipped · ratchet movements · learnings · next steps F1-S9 routing-shell + F1-S10 empty-states).
3. **Story archive**: `git mv vitalia/docs/product/stories/vitalia-fase1-sub-tabs-line2 vitalia/docs/archive/2026/stories/vitalia-fase1-sub-tabs-line2` in same squash-merge commit (per R2 brand-docs-schema.md).
4. **E2E runtime gate (BEFORE merge)**: `cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=regression e2e/regression/vitalia-fase1-sub-tabs-line2/ --update-snapshots=false` cuando dev-app live. Si dev-app unavailable → Chris staging gate manual con screenshot side-by-side mockup vs implementation (12 PNGs target).
5. **Capability rollout next stories**: F1-S9 routing-shell consume `defaultSubtab` field from agent-catalog (already there F1-S7) + `RIBBON_SUBTABS` for 404 / redirect logic. F1-S10 empty-states use 22 sub-tab placeholders per spec.

---

**Last line magic comment for orchestrator parsing:**

