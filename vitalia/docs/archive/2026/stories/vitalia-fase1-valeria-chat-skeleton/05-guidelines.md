<!-- voseo-allowed: glosario reference + internal guidelines -->

---
story_id: vitalia-fase1-valeria-chat-skeleton
brand: vitalia
type: ui-story
phase: fase-1
last_modified: 2026-05-24
architect_iter: 1
---

# F1-S6 `vitalia-fase1-valeria-chat-skeleton` — 05-guidelines.md

## § 1 — Must-load skills (builder bootstrap obligatorio)

`builder-frontend` (Sonnet/opencode/qwen) MUST cargar estos skills en bootstrap ANTES de tocar código. Enforcement: `/dev-team` Step 0 verifica + builder report en `T-{n}-result.md` lista "Skills consulted" verbatim. Falta del report → auditor CHANGES_REQUESTED automático.

| Skill | Cuándo cargar | Por qué |
|---|---|---|
| `frontend-expert` | Bootstrap T-1 (siempre primero) | FSD-Lite boundaries (`shared/shell-organism/` vs `lib/` vs `stores/`), Server-First default + `'use client'` solo hojas con state/hooks, Shadcn reuse Textarea/Button/Badge, tokens Tailwind semánticos, Vitest unit patterns, runtime quality checklist (useEffect deps complete, no stale closures, hydration safety) |
| `tessl__react-patterns` | T-3 + T-4 + T-5 (componentes con hooks) | React 19: `e.isComposing` IME guard (composer), `useRef<HTMLTextAreaElement>` para auto-resize, `useEffect` cleanup deps complete, hooks contract (no stale closures en setTimeout-zustand) |
| `tessl__shadcn-ui` | T-3 + T-4 (componentes que usan primitives) | REUSE primitives F1-S0: `Textarea` (rows=1 + manual auto-resize), `Button` (variant default + ghost icon size), `Badge` (variant outline para Mode Pill). Versiones cementadas — NO upgrade |
| `tessl__tailwind` | T-1 + T-3 + T-4 + T-5 (cualquier componente con classes) | Tokens semánticos via globals.css CSS vars (Design Contract §5.1). Permitidos: `bg-card`, `bg-muted`, `border-border`, `text-foreground`, `text-muted-foreground`, `bg-agent-{slug}`, `bg-agent-{slug}-soft`, `bg-vitalia-success`. NO hex literales en componentes. NO arbitrary values salvo `max-h-[100px]` documentado |
| `tessl__vitest` | T-1 + T-2 + T-3 + T-4 + T-5 + T-6 (todos unit tests) | RTL + `@testing-library/jest-dom` + `@testing-library/user-event`. Mock `useChatStore` via `useChatStore.setState({...})` directo + `useChatStore.getState().clearMessages()` en afterEach. Time mocking via `vi.useFakeTimers()` para `setTimeout` 800ms sendMessage flow. NO `vi.mock('@/stores/chat-store')` |
| `playwright-expert` | T-7 + T-8 + T-9 (E2E specs + POM + visual goldens) | POM patterns en `e2e/shell-organism/poms/` (NEW path canon F1-S6 — F1-S5 usó `e2e/pages/` legacy), fixtures shared (`shell-theme.fixture.ts` REUSE F1-S5), Clerk auth fixture REUSE F1-S3 (public route bypassa gate), `page.addInitScript` determinismo seeding chat-store, port 3002 vitalia, freshness gate, axe-playwright ruleset wcag2aa, `page.on('dialog', ...)` listener para XSS spec, visual goldens `--update-snapshots` iter 1 protocol con Chris side-by-side |
| `tessl__nextjs-app-router-modularization` | T-3 + T-5 (boundary decisions) | `'use client'` boundaries: ChatHeader/ChatMessages/ChatComposer/MessageBubble/TypingIndicator/DelegateMarker todos Client por consistencia con padre `ValeriaChat`. Dynamic imports NO requeridos. App Router preserved (no nuevas routes) |
| `claude-md-management` | Cuando dudes project-level invariants | tenant isolation upstream, Spanish neutro, native-first dev workflows, multibrand boundaries (zero engine touch, zero cross-brand import) |

### NO cargar (out-of-scope explícito)

`backend-expert`, `copilot-expert`, `sales-agent-expert`, `offer-expert`, `brand-expert`, `metrics-expert`, `offer-type-preset-expert`, `tessl__langgraph`, `tessl__zod`, `claude-api` — story es FE only chrome UI sin BE/agentic/dominio negocio/forms/LLM real. Cargar genera ruido tokens y deriva en scope creep.

## § 2 — Must-load rules (overlay vitalia + raíz)

| Rule | Trigger |
|---|---|
| `.claude/rules/frontend-fsd.md` (raíz) | shell-organism es `components/shared/` cross-feature — boundary matrix vital; nuevo `lib/agent-catalog.ts` consumido cross-shell |
| `.claude/rules/frontend-quality.md` (raíz) | ESLint 60+ rules, TS strict, Vitest 20% coverage threshold |
| `.claude/rules/spanish-text.md` (raíz) | strings UI sin voseo — 30+ microcopy ratificados spec § 6 (incluye correcciones "Empezá"→"Empieza", "Preguntale"→"Pregúntale" tilde + clítico) |
| `.claude/rules/tenant-isolation.md` (raíz) | URL `[tenantId]` propaga via Next routing — middleware Clerk gates upstream (no FE filter aquí, no API calls F1-S6) |
| `.claude/rules/anti-duplication.md` (raíz) | cross-brand mirror scan ejecutado pre-arch (§ 0.1 03-arch.md audit clean — 0 matches). ValeriaChat + agent-catalog + chat-store LIFT CANDIDATES post 2do brand consumer |
| `.claude/rules/tdd-mandatory.md` (raíz) | RED tests primero por capa: catalog+token → store+mock → átomos/moléculas → composer → organism → integration MODIFY |
| `.claude/rules/e2e-testing.md` (raíz) | Playwright NATIVE Linux (no docker), port 3002 vitalia, preflight obligatorio |
| `vitalia/.claude/rules/shell-mockup-per-component.md` (overlay) | visual goldens side-by-side mockup HTML ratificado · ratchet shrink-only · 4 PNGs scope (populated/empty × light/dark) |
| `vitalia/.claude/rules/hipaa-lite.md` (overlay) | scope: `not_applicable` — UI shell sin PHI · mock data sin datos clínicos reales (Marina Pérez + Dr. Juan García son nombres ficticios del mockup ratificado, NO diagnósticos/dosis/labs) |

## § 3 — Patterns required (debe usarse)

1. **Server Components donde posible.** F1-S6 todo el árbol chat es `'use client'` por consistencia (zustand + hooks). Agregar `'use client'` en hojas — arch test `test_server_first.test.ts` allowlist extend shrink-only (justify commit body).

2. **Named exports (no default exports)** salvo Next.js convention. F1-S6 NO crea pages/layouts nuevas. Arch test ratchet enforce.

3. **Zustand `chat-store` separado de `shell-store`** — SoC strict. F1-S6 NO modifica `shell-store.ts` (invariant heredado F1-S5 — `test-shell-store-schema-readonly-f1-s5.test.ts`). `chat-store` sin persist middleware (chat ephemeral cross-reload).

4. **Agent catalog SSoT (`lib/agent-catalog.ts`)** — single source of truth 6 agentes. Componentes consumen via `AGENT_CATALOG[slug]`. NUNCA hardcode `'Valeria'` / `'Camila'` / hex `#7b2d91` fuera de catalog. Arch test NEW `test-agent-catalog-ssot.test.ts` enforce.

5. **`useChatStore` selector pattern** — `const sendMessage = useChatStore((s) => s.sendMessage)` para evitar re-render por cambios irrelevantes (e.g., status update no debe re-renderear ChatComposer si éste solo consume sendMessage action).

6. **Mock `sendMessage` flow verbatim** (D2 spec § 0):
   - Push user message + thinking message (sync)
   - Set status='thinking' (idempotency guard previene double-fire)
   - setTimeout 800ms → remove thinking + push bot canned
   - `MOCK_RESPONSES_BY_AGENT[activeAgent][count % len]` — determinista (NO `Math.random`)
   - Time format `new Date().toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' })`

7. **IME composition guard en ChatComposer** — `if (e.isComposing) return` en onKeyDown handler (consistency con F1-S5 useKeyboardShortcuts pattern). Solo Enter (no Shift, no isComposing) envía. Shift+Enter default newline. Tests cubren ambos casos.

8. **Auto-resize textarea pattern** — `useEffect [localValue]` adjust `style.height = 'auto'` + `style.height = Math.min(scrollHeight, 100) + 'px'`. `max-h-[100px]` Tailwind class adicional como hard cap. Reset height a 'auto' on send.

9. **Avatar onError fallback** — `useState [imgError]` + `onError={() => setImgError(true)}` en `<img>`. Si error: render `<span>{descriptor.initial}</span>` letter en círculo `bg-{colorToken}`. Scenario 4 implícito: PNG 404 → fallback graceful.

10. **XSS guard** — JSX text-children only (`{content}`). NUNCA `dangerouslySetInnerHTML` en componentes nuevos. React 19 auto-escape. Auditor grep verifica cero matches. E2E spec dispara payload `<script>alert('xss')</script>` + listener `page.on('dialog', ...)` verify no fires.

11. **Semantic tokens Tailwind** — `bg-card`, `border-border`, `text-foreground`, `text-muted-foreground`, `bg-muted`, `bg-agent-valeria`, `bg-agent-valeria-soft`, `bg-agent-camila`, `bg-agent-camila-soft`, `bg-vitalia-success`. Tokens definidos en `globals.css` (F1-S1 + F1-S6 adds `--agent-mateo-soft`). NO hex literales (`#7b2d91`) excepto agent-catalog.ts `hex` field como metadata. NO arbitrary values salvo `max-h-[100px]` y `data-testid` attrs.

12. **Tailwind dynamic classes pattern** — agent color classes NO se construyen con template literals (`bg-agent-${slug}` NO funciona con JIT). Usar:
    - **Opción A (preferida)**: switch/map explícito en componentes que retorna className conocido:
      ```ts
      const agentBgClass = (slug: AgentSlug): string => {
        switch (slug) {
          case 'lisa': return 'bg-agent-lisa'
          case 'valeria': return 'bg-agent-valeria'
          // ... 6 entries
        }
      }
      ```
    - **Opción B**: Tailwind safelist en `tailwind.config.ts` (más expansivo, evita switches en muchos lugares) — `safelist: ['bg-agent-lisa', 'bg-agent-valeria', ...]`
    - F1-S6 recomendación: **Opción A** (switch) por componente — explicit + JIT-safe. Auditor verifica.

13. **Aria-labels en Spanish neutro** — verbatim spec § 6 microcopy:
    - `<section role="region" aria-label="Chat con Valeria">`
    - `<div role="log" aria-live="polite" aria-label="Conversación con Valeria">`
    - Composer textarea: `<label className="sr-only" htmlFor="valeria-composer">Mensaje para Valeria</label>`
    - Composer textarea: `id="valeria-composer"` (matches F1-S5 Cmd+K target)
    - 3 stub buttons: `aria-label="Adjuntar archivo"` / `aria-label="Mensaje de voz"` / `aria-label="Comandos rápidos"` + `title="Adjuntar (próximamente)"` / `title="Voz (próximamente)"` / `title="Comandos (próximamente)"`
    - Send button: text "Enviar" visible (no aria-label necesario por texto visible)
    - Avatar: `aria-hidden="true"` (decorativo); name visible como texto
    - Status dot: `aria-hidden="true"` (decorativo); "En línea · Tu secretaria virtual" como texto
    - Mode pill: contenido textual visible "🤖 Modo agente", sin role interactive
    - TypingIndicator dots: `aria-hidden="true"`; texto "Camila está abriendo…" leído por SR

14. **Reduced motion respect** — typing dots animation respeta `motion-reduce:animate-none` opcional en `.typing-dot` rule. Si Chris ratifica forma final del CSS, agregar `@media (prefers-reduced-motion: reduce) { .typing-dot { animation: none; } }` en `globals.css` mismo PR.

15. **Determinismo MOCK_MESSAGES IDs** — IDs estables `'1'..'6'` strings (NO `crypto.randomUUID()` en fixture data) para snapshots Playwright deterministas. Solo el store usa `crypto.randomUUID()` para mensajes NEW post-send.

16. **Spanish neutro hardcoded en mocks (excepción)** — D6 spec ratifica que `MOCK_MESSAGES` + `MOCK_RESPONSES` no pasan por compilador voz tenant (chrome mock). F1-S6 hardcodea tuteo neutro. F2-S11 wire sales_agent reemplaza con voz tenant runtime. Excepción documentada en commit body.

## § 4 — Patterns forbidden (NO usar)

1. **❌ Hex colors hardcoded en componentes.** Usar tokens semánticos (`bg-agent-valeria`) o CSS vars (`hsl(var(--agent-valeria))`). Excepción: `agent-catalog.ts` `hex` field como metadata. Arch test `test_no_hardcoded_colors.test.ts` bloquea.

2. **❌ Default exports.** FSD-Lite enforce — named exports only. Arch test ratchet.

3. **❌ Hardcoded agent name/color/thumbnail string fuera de `agent-catalog.ts`.** Componentes consumen via lookup `AGENT_CATALOG[slug]`. Allowlist: `_mock-messages.ts` puede mencionar nombres por mock data; tests pueden usar literales para assertions. Arch test NEW `test-agent-catalog-ssot.test.ts` bloquea fuera de allowlist.

4. **❌ `.vt-*` legacy utility classes** (deprecated DC §5.3). Arch test `test-no-vt-classes-in-new-features.test.ts` bloquea.

5. **❌ Voseo en MOCK_MESSAGES + MOCK_RESPONSES + microcopy.** Spanish neutro estricto (D6 spec). Glossary regex `vos|sos|tenés|podés|querés|sabés|dale|mirá|fijate|empezá|abrila|etc.` cero matches. Arch test `test-vitalia-ui-strings-no-voseo.test.ts` + e2e `valeria-chat-i18n.spec.ts` enforce. NOTA: el mockup HTML usa "Empezá" + "Preguntale" pero el spec § 6 explicita correcciones "Empieza" + "Pregúntale" — usar versiones corregidas en el código (no copiar verbatim del mockup HTML, usar spec § 6 microcopy).

6. **❌ `any` TypeScript.** Usar `unknown` + type guards o tipos explícitos del catalog (`AgentSlug`, `ChatMessage`, etc.). TS strict bloquea.

7. **❌ Modificar `ValeriaChatSlot.tsx`** — file será deleted en T-6. Solo touch para verificar import paths.

8. **❌ Modificar `ShellOrganismLayout*.tsx` / `TopBarGlobal.tsx` / `ValeriaRail.tsx` / `ValeriaHistory.tsx` / `useKeyboardShortcuts.ts`** — out of scope F1-S6. Heredado F1-S5 PRESERVED intacto.

9. **❌ Modificar `shell-store.ts`** — chat usa store separado `chat-store.ts`. Invariant heredado F1-S5 (`test-shell-store-schema-readonly-f1-s5.test.ts`) bloquea.

10. **❌ Engine edits (`core/luana-core-*/src/`)** — HARD BAN per `anti-duplication.md` § Multibrand awareness. Lift requires `/pm-luana` promotion proposal — fuera scope F1-S6.

11. **❌ Cross-brand imports (`from '@/{other_brand}/...'`)** — HARD BAN. Nicolify `CopilotSidebar` es read-only reference, NO import.

12. **❌ `dangerouslySetInnerHTML`** — XSS guard mandatory. JSX text-children only para mensajes.

13. **❌ Editar `vitalia/frontend/src/components/ui/*` (Shadcn primitives)** — copy-paste local cementado F1-S0, NO modify. Reuse only.

14. **❌ Editar `vitalia/frontend/src/lib/api/fetchClient.ts`** — out of scope, no API calls F1-S6.

15. **❌ Editar `vitalia/.claude/` o `.claude/` raíz** — meta-paradigm, out of scope.

16. **❌ Crear archivos en `vitalia/docs/architecture/`, `docs/process/`, `docs/specs/`** — meta-paradigm out of scope. Si descubrís pattern promotable cross-brand, documentar en `vitalia/docs/learnings/2026-05-XX-{slug}.md` post-merge.

17. **❌ Llamadas a APIs externas** — `fetch()`, `axios`, `react-query` queries — out of scope. Mock chrome pure F1-S6.

18. **❌ Persist middleware en `chat-store.ts`** — ephemeral cross-reload (D6+D8 spec implícito). F2-S* introducirá persist real via DB.

19. **❌ `Math.random()` en mocks** — determinismo strict (D2). `MOCK_RESPONSES` rotativo `count % len`.

20. **❌ Template literal Tailwind dynamic classes** (`` `bg-agent-${slug}` ``) — JIT-incompatible. Switch/map o safelist explicit.

## § 5 — Files in scope (lista cerrada per spec § 13)

**13 paths brand-scoped FE:**

### NEW (10 archivos componentes + data + tests)

| Path | Owner ticket |
|---|---|
| `vitalia/frontend/src/lib/agent-catalog.ts` | T-1 |
| `vitalia/frontend/src/lib/__tests__/agent-catalog.test.ts` | T-1 |
| `vitalia/frontend/src/stores/chat-store.ts` | T-2 |
| `vitalia/frontend/src/stores/__tests__/chat-store.test.ts` | T-2 |
| `vitalia/frontend/src/components/shared/shell-organism/_mock-messages.ts` | T-2 |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaChat.tsx` | T-5 |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaChat.test.tsx` | T-5 |
| `vitalia/frontend/src/components/shared/shell-organism/ChatHeader.tsx` | T-3 |
| `vitalia/frontend/src/components/shared/shell-organism/ChatHeader.test.tsx` | T-3 |
| `vitalia/frontend/src/components/shared/shell-organism/ChatMessages.tsx` | T-5 |
| `vitalia/frontend/src/components/shared/shell-organism/ChatComposer.tsx` | T-4 |
| `vitalia/frontend/src/components/shared/shell-organism/ChatComposer.test.tsx` | T-4 |
| `vitalia/frontend/src/components/shared/shell-organism/MessageBubble.tsx` | T-3 |
| `vitalia/frontend/src/components/shared/shell-organism/MessageBubble.test.tsx` | T-3 |
| `vitalia/frontend/src/components/shared/shell-organism/TypingIndicator.tsx` | T-3 |
| `vitalia/frontend/src/components/shared/shell-organism/DelegateMarker.tsx` | T-3 |
| `vitalia/frontend/src/__tests__/architecture/test-agent-catalog-ssot.test.ts` | T-6 |
| `vitalia/frontend/e2e/shell-organism/poms/valeria-chat-page.pom.ts` | T-7 |
| `vitalia/frontend/e2e/shell-organism/fixtures/chat-store-seed.fixture.ts` | T-7 |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-happy.spec.ts` | T-8 |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-send.spec.ts` | T-8 |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-keys.spec.ts` | T-8 |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-xss.spec.ts` | T-8 |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-empty.spec.ts` | T-9 |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-a11y.spec.ts` | T-9 |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-i18n.spec.ts` | T-9 |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-visual.spec.ts` | T-9 |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-visual.spec.ts-snapshots/valeria-chat-populated-light-1280x800.png` | T-9 |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-visual.spec.ts-snapshots/valeria-chat-populated-dark-1280x800.png` | T-9 |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-visual.spec.ts-snapshots/valeria-chat-empty-light-1280x800.png` | T-9 |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-visual.spec.ts-snapshots/valeria-chat-empty-dark-1280x800.png` | T-9 |

### MODIFY (3 archivos puntuales)

| Path | Owner ticket | Scope diff verbatim |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.tsx` | T-6 | swap `import { ValeriaChatSlot } from "./ValeriaChatSlot"` → `import { ValeriaChat } from "./ValeriaChat"` + 2 JSX occurrences `<ValeriaChatSlot />` → `<ValeriaChat />` (líneas 38, 204, 249) |
| `vitalia/frontend/src/app/globals.css` | T-1 | add `--agent-mateo-soft` light + dark + `.typing-dot` keyframes/rule per 03-arch.md § 2.7 |
| `vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` | T-6 | extend names list shrink-only |
| `vitalia/frontend/src/__tests__/architecture/test_server_first.test.ts` | T-6 | extend 'use client' allowlist shrink-only (justify commit body) |

### DELETE (2 archivos legacy F1-S5)

| Path | Owner ticket |
|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaChatSlot.tsx` | T-6 |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaChatSlot.test.tsx` | T-6 |

### Verify (no edits, just check)

| Path | Verificación |
|---|---|
| `vitalia/frontend/tailwind.config.ts` | si `agent.mateo` y `agent['mateo-soft']` entries faltan en `theme.extend.colors.agent` → agregar (MODIFY puntual T-1 mismo PR si necesario). Heredado F1-S1 según Design Contract §5.2. |

## § 6 — Files NEVER touches (HARD BAN)

| Path | Razón |
|---|---|
| `core/luana-core-*/` | Engine — promotion gate `/pm-luana` required |
| `nicolify/**`, `comunify/**`, `lupulo/**` | Cross-brand HARD BAN (anti-duplication.md) |
| `vitalia/frontend/src/components/ui/*` | Shadcn primitives — REUSE only, no edit |
| `vitalia/frontend/src/lib/api/fetchClient.ts` | API client — out of scope (no API calls F1-S6) |
| `vitalia/frontend/src/stores/shell-store.ts` | shell-store invariant heredado F1-S5 (chat usa store separado) |
| `vitalia/frontend/src/components/shared/shell-organism/{TopBarGlobal,ValeriaSidebarSlot,ValeriaRail,ValeriaHistory,ShellOrganismLayoutClient,ShellModeToggle,AppPanelSlot,LogoMark,TenantSwitcher,ThemeToggle,EmptyStateInline,HistoryItem,HistoryGroup}.tsx` | F1-S1..S5 cementados — out of scope (excepto `ValeriaSidebar.tsx` puntual swap) |
| `vitalia/frontend/src/hooks/useKeyboardShortcuts.ts` | F1-S5 cementado |
| `vitalia/frontend/src/app/(shell-organism)/**`, `(dashboard)/**` | Routes — out of scope |
| `vitalia/frontend/src/__tests__/architecture/test-shell-store-schema-readonly-f1-s5.test.ts` | invariant heredado F1-S5 |
| `vitalia/frontend/src/__tests__/architecture/{test_fsd_boundaries,test-shell-store-schema,test_no_voseo_in_copy,test-skip-link-target,test-no-clerk-organizations,test_no_cross_feature_imports,test_page_padding,test_phi_pii_components_used,test_no_hardcoded_strings,test_no_hardcoded_strings_inbox}.test.ts` | arch tests heredados — NO modificar (extend solo los listados en § 5 MODIFY) |
| `vitalia/.claude/`, `.claude/` raíz | meta-paradigm out of scope |
| `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` | SSoT atomic design — out of scope (referenciado, no editado) |
| `vitalia/docs/specs/templates/**`, `docs/process/**`, `docs/specs/**`, `docs/architecture/**` | meta-paradigm out of scope |
| `vitalia/docs/portfolio/`, `vitalia/docs/learnings/` (excepto post-merge nuevo file documentando promotion candidate) | out of scope during build |

## § 7 — TDD discipline obligatoria

Per `.claude/rules/tdd-mandatory.md`: RED tests → impl GREEN → REFACTOR. Por ticket:

- **T-1**: RED `agent-catalog.test.ts` cases (6 agentes, DEFAULT_CHAT_AGENT, shape complete) → GREEN `agent-catalog.ts` + `globals.css` MODIFY (--agent-mateo-soft + typing-dot).
- **T-2**: RED `chat-store.test.ts` cases (sendMessage flow, MOCK_RESPONSES rotativo, idempotency, time mocking 800ms) → GREEN `chat-store.ts` + `_mock-messages.ts`.
- **T-3**: RED `MessageBubble.test.tsx` + `ChatHeader.test.tsx` cases (bot/user variants, XSS guard, avatar onError fallback) → GREEN componentes + TypingIndicator/DelegateMarker.
- **T-4**: RED `ChatComposer.test.tsx` cases (Enter sends, Shift+Enter newline, isComposing guard, idempotency, 3 stubs no disabled) → GREEN ChatComposer.
- **T-5**: RED `ValeriaChat.test.tsx` cases (render 6 msgs, empty state branch, aria-live, auto-scroll) → GREEN ValeriaChat + ChatMessages.
- **T-6**: RED arch tests extend + NEW test-agent-catalog-ssot.test.ts → GREEN ValeriaSidebar swap + DELETE legacy + arch allowlists extended.
- **T-7..T-9**: Playwright POM + 8 specs + visual goldens. RED initial (componente real ya green via T-1..T-6) → GREEN cuando dev stack levantado + Chris ratifica side-by-side visual iter 1.

## § 8 — Exit criteria por ticket

Cada ticket cierra con:
- [ ] Tests RED → GREEN (target validators per `06-tickets.yaml::tickets[ticket_id].acceptance.validator_ids`)
- [ ] Lint + Prettier + TSC clean (val-fe-{lint,prettier,tsc})
- [ ] Arch tests verdes (val-fe-arch-*)
- [ ] Spanish neutro verificado (no voseo, no PHI real)
- [ ] No engine edit, no cross-brand import, no out-of-scope file touched
- [ ] `T-{n}-result.md` escrito con "Skills consulted" verbatim list + delta resumido
- [ ] `T-{n}-impl-log.md` capturado si hubo iteraciones >2

## § 9 — Story-level exit criteria

Story `developed → reviewing → done`:
- [ ] T-1..T-9 todos GREEN
- [ ] 100% scenarios cubiertos (7/7 mapped per 04-validators.yaml::scenario_coverage)
- [ ] 4 visual goldens generados + Chris ratificó side-by-side (--update-snapshots iter 1)
- [ ] axe wcag2aa 0 violations populated + empty light + dark
- [ ] capability YAML files updated post-merge (`valeria-chat.yaml` NEW + `valeria-sidebar.yaml` MODIFY + module auto-list regen via `scripts/reconcile_capabilities.py --brand vitalia`)
- [ ] `vitalia/docs/learnings/2026-05-XX-valeria-chat-promotion-candidate.md` NEW post-merge documentando LIFT CANDIDATE (cross-brand chat organism pattern, agent catalog, chat store)
- [ ] `07-merge.md` con 5 secciones cementadas per `.claude/rules/story-closure-gate.md`

