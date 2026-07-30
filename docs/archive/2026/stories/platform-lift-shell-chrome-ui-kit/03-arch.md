---
story_id: platform-lift-shell-chrome-ui-kit
brand: platform
arch_version: 1
schema_version: v4.1
architecture_pattern: lift-to-core            # NO ADR-vitalia-004 (esa es para sub-tabs de feature; esto es chrome cross-brand)
adr_004_compliance: n/a                        # chrome wrapper, no es sub-tab de agente
verification_nature: tecnica                   # refactor move+parametrize — verde honesto = suite e2e existente vitalia contra chrome consumido del kit
demo_required: false                           # autonomous (Chris ratificó). DoD #37 live-verify SIGUE obligatoria (SC-8)
architect_run_on: 2026-06-11
surfaces: [FE]                                 # FE-only: core/@luana/ui-kit (TS) + vitalia/frontend + nicolify/frontend
core_lift_touch: true                          # ESTE lift es la ejecución del proposal accepted 2026-06-01-lift-shell-organism — autorización explícita /pm-luana
autonomous_mode: true                          # ratificado Chris 2026-06-11 verbatim (refinar→arch→build→audit→merge sin pausas)
---

# Contract: platform-lift-shell-chrome-ui-kit (consolidado)

> **LIFT del chrome del shell-organism hardened** desde `vitalia/frontend/src/components/shared/shell-organism/` a `core/@luana/ui-kit` como **organism brand-agnostic** + re-wire vitalia + **convergencia nicolify** (mata el mirror cross-brand). Es la ejecución del proposal `2026-06-01-lift-shell-organism-to-core` (accepted, ratificado Chris 2026-06-06 + sesión autónoma 2026-06-11).
>
> **Insumos:** `01-spec.md` (RN-1..9 + SC-1..9 + matriz, el contrato) + predecesor `vitalia-shell-core-hardening` (chrome hardened, 03-arch § Decisión A/B/C + T-5 patrón de migración + 07-merge § 5). Detalle por surface en `03-arch-fe.md` (FE consolidado — única superficie). Aprendizajes técnicos en `05-guidelines.md` (verbatim, sagrados RN-4).

## 0. Context Summary

- **Story ID:** platform-lift-shell-chrome-ui-kit · programa `design-system-homologation` (ADR-014, owner /pm-luana) · sin release brand.
- **Architect run on:** 2026-06-11 (Opus 4.8 cutoff Jan 2026; nada post-cutoff state-of-the-art requerido — es refactor de código propio + libs ya pinneadas).
- **Modules touched:** `shell` (único). `cross_module_scope: [shell]`. Bucket lock `code:shell` al build. `parallel_safe: false` (toca kit + 2 brands).
- **Surface → builder → auditor mapping** (/dev-team spawn):

  | Surface | Builder | Auditor |
  |---|---|---|
  | `core/@luana/ui-kit/src/**` (organism chrome brand-agnostic NUEVO + deps) | `builder-frontend` (model: inherit) | `auditor-frontend` (Opus) |
  | `vitalia/frontend/src/**` (re-wire imports al kit + borrado chrome local + thin brand wrappers) | `builder-frontend` (model: inherit) | `auditor-frontend` (Opus) |
  | `nicolify/frontend/src/**` (convergencia: retira máquina legacy + consume kit) | `builder-frontend` (model: inherit) | `auditor-frontend` (Opus) |

  **No hay surface BE. No hay surface AGENTIC** (R23 no aplica — el chat es chrome/layout, no comportamiento del agente: cero prompt/tool/state-graph/golden/voz). El `chat-store` que el chrome consume es un **mock UI-local** (ver § Store).

- **Skills consultados (decisión de cada uno):**
  - `frontend-expert` — FSD-Lite, Server-First, store SSR-safe, live-verify gate. Decisión: el chrome es organism del kit; el wrapper `ssr:false` (react-resizable-panels v4) vive en el kit; las brand-stores + agent-catalog entran por props.
  - `vitalia-design-system` (must_load en tickets vitalia) — SHELL-DESIGN-CONTRACT v1.4 (chrome hardened SSoT) + tokens `globals.css` + agent-colors. Decisión: tokens/avatares/labels = brand (props + CSS vars); el kit no conoce a "Valeria" ni a vitalia.
  - `nicolify-design-system` (must_load en ticket nicolify) — "portar verbatim re-temizado". Decisión: la máquina legacy `luanaState/LuanaRail/ShellModeToggle` se RETIRA; nicolify consume el chrome del kit con su catálogo (Luana sidebar + Abel/Brenda/Christian/Sara/Norvil) por props (RN-7).
  - `copilot-expert` / `sales-agent-expert` / `brand-expert` / `offer-expert` / `metrics-expert` — **consultados y descartados**: ninguna superficie agentic ni de dominio se toca. El "+" nueva-conversación es estado del mock chat-store, NO un turn del copilot ni persistencia BE. Confirmado leyendo `chat-store.ts` (`newConversation()` archiva mock no-PHI) + `ValeriaChat.tsx`.
- **CONTEXT-BRIEF source:** ausente (no se generó brief para esta story platform) → self-ran reads + greps (Path B). R24 brief gate N/A.
- **capability YAML afectadas:** ninguna (`cap_target: null`, `cap_change_type: fix` — chrome transversal `map_zone: infraestructura`, sin cap user-visible; precedente `vitalia-shell-core-hardening`). El kit actualiza **CHANGELOG.md** + bump version. `SHELL-DESIGN-CONTRACT.md` (vitalia) actualiza § origen (chrome ahora vive en el kit). Proposal → `migrated`.
- **Architecture gates que deben seguir verdes** (NATIVE host):
  - `core/@luana/ui-kit` → `pnpm --filter @luana/ui-kit typecheck && pnpm --filter @luana/ui-kit test`
  - `vitalia/frontend` → `npx tsc --noEmit` · `npx eslint src/ --cache` · `npx vitest run src/` · `src/__tests__/architecture/` (FSD boundaries + **test-no-cross-brand-shell-mirror** + no-clerk-organizations) · e2e `e2e/regression/shell-core-hardening/` 68/68 + `resizer-matrix.spec.ts` 7/7
  - `nicolify/frontend` → `npx tsc --noEmit` · `npx vitest run src/` · `src/__tests__/architecture/`

## Prior art audit (anti-duplication-refining · Step prior-art-scan)

### Source of evidence
- [x] Self-run reads/greps (Path B — no CONTEXT-BRIEF)
- [x] `checkpoint.md § prior_art_scan` block ratificado
- [x] proposal `2026-06-01` § "Estado post hardening" (handoff /pm-luana)
- [x] predecesor `vitalia-shell-core-hardening` 03-arch § Prior art audit + T-5 (patrón de migración N3 exitoso)

### Audit cross-module ejecutado (greps reales 2026-06-11)
```bash
WS=$(git rev-parse --show-toplevel)
# 1. El chrome ¿ya vive en el kit? → NO (solo N3 + atoms + archetypes shipped en v0.3.0)
find core/@luana/ui-kit/src -maxdepth 1 -type f       # → flat: atoms shadcn + EntityWorkspaceLayout/EntitySubNavBar/EntityInfoCard/EntityPicker + layout/ archetypes/. CERO chrome (Shell*/Ribbon/Valeria*/TopBar).
# 2. Store factory SSR-safe ¿existe en engine? → SÍ, CONSUMIR
ls core/@luana/hooks/src/create-ssr-safe-persisted-store.ts use-store-hydration.ts   # presentes (ADR-vitalia-006)
# 3. Mirror cross-brand del chrome ¿concreto? → SÍ (vitalia origen + nicolify port verbatim re-temizado)
find {vitalia,nicolify}/frontend/src/components/shared/shell-organism -name "ShellOrganismLayoutClient.tsx"  # → 2 copias independientes
# 4. ¿react-resizable-panels + zustand en el kit deps? → NO (deliverable: agregarlos)
grep -E "react-resizable-panels|zustand" core/@luana/ui-kit/package.json   # → 0 matches
```

### Sistemas existentes encontrados

| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| Store factory SSR-safe | `@luana/hooks/create-ssr-safe-persisted-store` + `use-store-hydration` | active v0.x | **CONSUMIR** (el shell-store del kit lo usa — no recrear, ADR-vitalia-006) |
| N3 list/detail | `@luana/ui-kit` (`EntityWorkspaceLayout`/`EntitySubNavBar`) | active v0.3.0 | **FUERA DE SCOPE** (ya en kit, ya consumido por vitalia T-5; nicolify aún brand-local — su migración N3 NO es scope de esta story salvo que su shell la arrastre — ver § nicolify) |
| Chrome hardened vitalia | `vitalia/.../shell-organism/` (~67 files) | active (origen del lift) | **LIFT** (mover brand-agnostic al kit + re-wire + borrar local) |
| Chrome legacy nicolify | `nicolify/.../shell-organism/` (~44 files, máquina `luanaState`+`LuanaRail`+`ShellModeToggle`) | active (mirror cross-brand) | **RETIRE máquina legacy + CONVERGER al kit** (RN-7) |
| Brand stores (chat-store mock, tenant-store) | `vitalia/.../stores/`, `nicolify/.../stores/` | active | **QUEDA brand** (chat = mock conversacional; tenant = Clerk/IAM brand) — entra al kit por props/render-props |
| agent-catalog (AGENT_CATALOG/AGENT_RIBBON_ORDER/RIBBON_SUBTABS) | `vitalia/src/lib/agent-catalog.ts`, `nicolify/src/lib/agent-catalog.ts` | active | **QUEDA brand** (brand data — el kit lo recibe por props; los helpers `extractAgentFromPath`/`extractSubtabFromPath` se LIFTAN genéricos) |
| Tokens agent-colors `--agent-*`, `--vitalia-*` | `{brand}/.../globals.css` | active | **QUEDA brand** (cada marca su theme; el kit usa CSS vars `--shell-*`/`--agent-*` con fallback neutro) |
| Arch test mirror ratchet | `vitalia/.../test-no-cross-brand-shell-mirror.test.ts` (`KNOWN_SANCTIONED_SHELL_MIRROR`) | active | **ENCOGER allowlist a vacío** (shrink-only, RN-5; cada símbolo lifteado se remueve en su commit) |

### Decisión por sistema → § Architecture Decisions (A/B/C/D). **EXTEND/CONSUMIR > NEW** en todos los casos. NET-NEW justificado: solo el organism `ShellLayout` del kit (composición de piezas ya existentes en vitalia, movidas + parametrizadas — net-new para el KIT, no para la plataforma) + el `createShellStore` factory genérico del kit. **Cero pieza inventada desde cero** — es move+parametrize.

## Architecture Decisions

> Las 4 decisiones que el caller delegó cerradas con tradeoffs (sin preguntar).

### Decisión A — Corte file-by-file (KIT genérico | BRAND queda | BORRAR)

**Criterio:** máquina de estados + layout splitter + chrome primitives genéricos = **KIT**. Brand data (agent-catalog, avatares, tokens, mock de conversación, Tenant*, AddClinic/AddAgencyModal) + lo acoplado a stores de marca = **BRAND**. Piezas grises (chat sub-tree, TopBar, Ribbon/SubTabs) resueltas con slots/props/render-props (ver tabla detallada en § 10 + `03-arch-fe.md § File map`).

**Regla de oro para grises (coupling-driven, evidencia del grep matrix):** una pieza que importa `useChatStore`/`useShellStore`/`AGENT_CATALOG` directamente NO se liftea con el import hardcoded. Dos sub-estrategias:
- **store-shape genérico:** el kit define el **type** del store (ej. `ShellStoreApi`, `ChatStoreApi`) + lo recibe por prop/context (render-prop o `StoreProvider`). La brand instancia el store concreto con su factory y lo inyecta. → aplica a TODO el chat sub-tree + ValeriaCollapsedStrip + ValeriaHistory + ValeriaSidebar + TopBar.
- **catalog genérico:** las piezas que leen `AGENT_CATALOG` reciben `agentCatalog: AgentDescriptor[]` por prop. → Ribbon/RibbonTab/SubTabsBar/SubTab/MessageBubble/ChatHeader/_agent-tw-classes.

**Resumen del corte** (detalle file-by-file en § Inventario corte):

| Clase | Componentes | Destino |
|---|---|---|
| Layout máquina | `ShellOrganismLayout`(+Client), `useViewportGuard`, `AppPanelSlot` | **KIT** (genérico, props) |
| Sidebar supervisora | `ValeriaSidebar`→`SupervisorSidebar`, `ValeriaCollapsedStrip`→`SupervisorCollapsedStrip`, `ValeriaHistory`→`SupervisorHistory` | **KIT** (genérico, store por prop, label/avatar por prop) |
| Chat skeleton | `ValeriaChat`→`ChatPanel`, `ChatHeader`, `ChatComposer`, `ChatMessages`, `MessageBubble`, `TypingIndicator`, `DelegateMarker`, `HistoryGroup`, `HistoryItem`, `StatusDot`, `TogglePill`, `EmptyStateInline`, `ChannelBadge` | **KIT** (genérico, chat-store + catalog por prop) |
| Navegación | `Ribbon`, `RibbonTab`, `SubTabsBar`, `SubTab`, `SubSubTabsBar`, `SubTabContent`, `ConfigTab`, `EmptyState`, `PlaceholderCard` | **KIT** (catalog + routing helpers por prop) |
| TopBar shell | `TopBarGlobal`→`TopBarShell` | **KIT como SHELL con slots** (`logoSlot`, `rightClusterSlot`, `onBurgerClick`); el contenido brand (LogoMark/ThemeToggle/TenantSwitcher) se inyecta |
| Routing/store helpers | `extractAgentFromPath`/`extractSubtabFromPath`/`isValidAgent`/`isValidSubtab`/`SubTabMeta`, `createShellStore` factory + machine + migrate | **KIT** (genéricos) |
| Brand data | `agent-catalog.ts` (AGENT_CATALOG/ORDER/SUBTABS/SHIPPED_STATIC), `shell-routes.ts` (DEFAULT_LANDING_SUBPATH), `_mock-*`, tokens | **BRAND queda** |
| Brand chrome glue | `LogoMark`, `ThemeToggle`, `TenantSwitcher`(+Badge/Option/StoreBootstrap), `AddClinicPlaceholderModal`(vitalia)/`AddAgencyPlaceholderModal`(nicolify) | **BRAND queda** (acoplados a stores/IAM/Clerk/marca) |
| Brand store instances | `chat-store.ts` (mock), `tenant-store.ts`, `shell-store.ts` (instancia del factory del kit con key brand) | **BRAND queda** (instancian el factory/type del kit) |

> **TenantSwitcher/ThemeToggle/LogoMark se quedan BRAND** porque: TenantSwitcher consume `tenant-store` + IAM + Clerk (brand); ThemeToggle usa `next-themes` (OK genérico, pero el toggle visual cita tokens brand); LogoMark es el logo de la marca. El `TopBarShell` del kit los recibe por slots (`logoSlot`/`rightClusterSlot`/`burgerSlot`) — ver Decisión B.

### Decisión B — API brand-agnostic del organism (contrato TS)

El organism del kit expone **un** componente raíz `ShellLayout` + sub-componentes nombrados, todos parametrizados. **Cero `'Valeria'`/`'vitalia'`/`#01B2F8` en lógica del kit** (RN-2/SC-7). Defaults de props NEUTROS (`supervisorName` SIN default brand). Colores agente vía CSS vars que cada brand define en su `globals.css`; el kit referencia `--agent-{slug}`/`--shell-*` con fallbacks neutros.

**Contrato TS verbatim** (ver § API contract organism kit más abajo para la firma completa).

**Store por inyección (no por import):** el kit NUNCA importa `@/stores/chat-store` ni `@/stores/shell-store`. Define los **types** (`ShellStore`, `ChatStoreApi`) + un **factory genérico** `createShellStore({ storageKey, version })` que usa `@luana/hooks/createSsrSafePersistedStore`. La brand crea su instancia (`useShellStore = createShellStore({ storageKey: 'vitalia-shell-state', ... })`) y la pasa al `ShellLayout` por prop `useShellStore`. El chat-store (mock) lo pasa la brand igual (prop `useChatStore`). → SC-6 localStorage compat (key conservada) + RN-8 (consume `@luana/hooks`, no recrea).

### Decisión C — ssr:false wrapper (¿kit o brand?)

**El wrapper `dynamic({ssr:false})` vive en el KIT.** El kit exporta `ShellLayout` (el wrapper público que internamente hace `dynamic(() => import('./ShellLayoutClient'), { ssr:false, loading: SkeletonFromProps })`) + `ShellLayoutClient` (no exportado público — solo vía el wrapper).

**Por qué en el kit y no en cada brand:**
1. El bug que motiva `ssr:false` (react-resizable-panels v4 bare-name `localStorage` default param crashea el SSR pass de Next) es **propiedad del organism**, no de la brand. Si cada brand re-implementara el wrapper, duplicaríamos el patrón frágil → exactamente lo que el lift mata.
2. El kit es un **package TS consumido por el Next de cada brand** (no tiene su propio runtime Next, pero `next/dynamic` es un import de `next` que es peerDep `>=14` — válido). El `ssr:false` se evalúa en el contexto Next del consumidor.
3. El skeleton SSR (store-free TopBar) se parametriza: `ShellLayout` recibe `skeletonSlot?` (o usa un default neutro). Vitalia/nicolify pasan su skeleton con su LogoMark.

**Tradeoff aceptado:** el kit importa `next/dynamic` (acopla el kit a Next como peerDep — ya lo es). Alternativa descartada: exportar solo `ShellLayoutClient` y que cada brand haga el `dynamic` wrapper → re-duplica el patrón frágil + el skeleton store-free + el comentario de causa raíz en N brands. NO.

### Decisión D — SEMVER

**0.3.0 → 0.4.0 (minor).** El organism chrome es **additivo**: nuevos exports (`ShellLayout`, `SupervisorSidebar`, `Ribbon`, `createShellStore`, `extractAgentFromPath`, etc.) que NO existían en v0.3.0. Cero breaking en exports existentes (atoms + N3 + archetypes intactos). Deps nuevas (`react-resizable-panels`, `zustand`) se agregan a `dependencies` — additivo.

**Riesgo de colisión de nombres detectado y mitigado:** el kit YA exporta `Group` (form-group, NO react-resizable-panels). El organism usa el `Group` de `react-resizable-panels` **internamente** (no se re-exporta). El barrel del kit NO debe re-exportar el `Group` de react-resizable-panels. Si el organism necesita exponer algo con nombre potencialmente colisionable, prefijar `Shell*` (ej. el separator si se expone → `ShellResizeHandle`). **Verificación en ticket T-K: grep del barrel post-add que no duplique `Group`/`Separator`/`Panel` exports.**

Documentar la decisión minor en el CHANGELOG del kit + en el proposal al migrar.

## Inventario corte file-by-file

> Detalle completo en `03-arch-fe.md § File map`. Aquí el resumen autoritativo (NEW kit / RENAME→kit / BRAND queda / BORRAR / RETIRE nicolify). `kit src/` destino propuesto: **`core/@luana/ui-kit/src/organism/shell/`** (sub-dir nuevo — el kit hoy es flat pero ya tiene `layout/` + `archetypes/` sub-dirs como precedente; un organism merece su carpeta + su barrel `organism/shell/index.ts` re-exportado desde `src/index.ts`).

| Origen (vitalia) | Destino kit | Acción | Nota |
|---|---|---|---|
| `ShellOrganismLayout.tsx` | `organism/shell/ShellLayout.tsx` | RENAME→KIT | wrapper `ssr:false` + skeleton por prop (Decisión C) |
| `ShellOrganismLayoutClient.tsx` | `organism/shell/ShellLayoutClient.tsx` | RENAME→KIT | **fixes v4 SAGRADOS RN-4** (key-remount, retry-rAF, collapsedSize px, push ±histPct, grid implícito) — portar verbatim; `SHELL_GROUP_ID`/store por prop |
| `ValeriaSidebar.tsx` | `organism/shell/SupervisorSidebar.tsx` | RENAME→KIT | store + label/avatar/keyboard por prop |
| `ValeriaCollapsedStrip.tsx` | `organism/shell/SupervisorCollapsedStrip.tsx` | RENAME→KIT | avatar/label por prop |
| `ValeriaHistory.tsx` | `organism/shell/SupervisorHistory.tsx` | RENAME→KIT | chat-store por prop |
| `ValeriaChat.tsx` | `organism/shell/ChatPanel.tsx` | RENAME→KIT | **grid implícito `grid-cols-[minmax(0,1fr)]`+`min-w-0` SAGRADO RN-4** |
| `ChatHeader.tsx` | `organism/shell/ChatHeader.tsx` | →KIT | **container query `@[24rem]` SAGRADO RN-4** + catalog/store por prop |
| `ChatComposer.tsx`, `ChatMessages.tsx`, `MessageBubble.tsx`, `TypingIndicator.tsx`, `DelegateMarker.tsx`, `StatusDot.tsx`, `TogglePill.tsx`, `EmptyStateInline.tsx`, `ChannelBadge.tsx`, `HistoryGroup.tsx`, `HistoryItem.tsx`, `EmptyState.tsx`, `PlaceholderCard.tsx` | `organism/shell/*` | →KIT | catalog/store por prop donde aplique |
| `Ribbon.tsx`, `RibbonTab.tsx`, `SubTabsBar.tsx`, `SubTab.tsx`, `SubSubTabsBar.tsx`, `SubTabContent.tsx`, `ConfigTab.tsx` | `organism/shell/*` | →KIT | catalog + routing helpers por prop; `ConfigTab` label por prop |
| `TopBarGlobal.tsx` | `organism/shell/TopBarShell.tsx` | RENAME→KIT (SHELL) | slots `logoSlot`/`rightClusterSlot`/`onBurgerClick`/`variant` |
| `AppPanelSlot.tsx`, `useViewportGuard.ts`, `_agent-tw-classes.ts` | `organism/shell/*` | →KIT | `_agent-tw-classes` toma `agentCatalog` por arg |
| `types.ts` (tenant types) | parcial | SPLIT | tipos genéricos (`AgentDescriptor`, `SubTabMeta`, store types) → KIT; `Tenant`/`TenantStore` types → BRAND queda |
| `stores/shell-store.ts` (machine+migrate) | `organism/shell/create-shell-store.ts` (factory) | RENAME→KIT factory | la **instancia** queda brand (key `vitalia-shell-state`) |
| `lib/agent-catalog.ts` helpers (`extractAgentFromPath`, `extractSubtabFromPath`, `isValidAgent`, `isValidSubtab`) | `organism/shell/routing.ts` | →KIT | genéricos (toman catalog por arg) |
| **BRAND queda vitalia** | — | KEEP | `lib/agent-catalog.ts` (AGENT_CATALOG/ORDER/SUBTABS/SHIPPED_STATIC) · `lib/shell-routes.ts` (DEFAULT_LANDING_SUBPATH) · `stores/chat-store.ts` (mock) · `stores/tenant-store.ts` · `_mock-*` · `LogoMark`/`ThemeToggle`/`TenantSwitcher`(+Badge/Option/StoreBootstrap)/`AddClinicPlaceholderModal` · `globals.css` tokens |
| **BRAND nuevo vitalia** | — | NEW | `stores/shell-store.ts` (thin: instancia `createShellStore({storageKey:'vitalia-shell-state', ...})` del kit) · un `ShellLayout` mount-wrapper que arma props (supervisorName='Valeria', agentCatalog=AGENT_CATALOG, slots=Logo/Theme/Tenant) |
| **BORRAR vitalia** | — | DELETE | todos los archivos del chrome lifteado de `components/shared/shell-organism/` + sus `.test.tsx` (tests migran al kit) — RN-3 |
| **RETIRE nicolify** | — | RETIRE+REWIRE | `LuanaSidebar/LuanaRail/LuanaChat/LuanaHistory/ShellModeToggle/SubSubTab.tsx` + máquina legacy `luanaState/shellMode/splitState` en `stores/shell-store.ts` → reemplazar por instancia del factory del kit (key `nicolify-shell-state`) + mount-wrapper con su catálogo (Luana + Abel/Brenda/Christian/Sara/Norvil) — RN-7. Nicolify mantiene `lib/agent-catalog.ts` brand + tokens. |

## API contract — organism kit (TS verbatim)

> Vive en `core/@luana/ui-kit/src/organism/shell/types.ts` + barrel `index.ts`. camelCase, defaults neutros, cero brand hardcode.

```typescript
// ── Generic agent descriptor (brand injects its catalog) ──────────────────────
export interface ShellAgentDescriptor {
  slug: string;                  // 'lisa' | 'abel' | ... — brand-defined, NOT an enum in the kit
  name: string;
  role: string;
  /** CSS var token name for the agent color, e.g. "agent-lisa". The brand's
   *  globals.css defines `--agent-lisa`; the kit references it via the token. */
  colorToken: string;
  colorSoftToken: string;
  initial: string;
  /** Avatar: a slot/ReactNode OR an image src — brand decides. */
  avatar?: React.ReactNode;
  thumbnail?: string;
  tabLabel: string;
  defaultSubtab: string;
}

export interface ShellSubTabMeta {
  id: string;
  label: string;
  icon: string;                  // emoji (parity ribbon catalog) — brand-provided
}

// ── Shell store contract (brand instantiates via createShellStore) ────────────
export type SupervisorOpen = "closed" | "chat";   // generic — NOT "valeria*"
export interface ShellStoreState {
  supervisorOpen: SupervisorOpen;   // A=closed (strip) · B=chat (split)
  historyOpen: boolean;             // additive push (C)
  splitPct: number | null;          // null = default 30 via useDefaultLayout
  mobileDrawerOpen: boolean;
  // ...actions: setSupervisorOpen, openSupervisor, collapseSupervisor,
  //    openHistory, closeHistory, toggleHistory, setSplitPct, setMobileDrawerOpen
}

/** Generic chat store API the chat sub-tree reads (brand provides the impl;
 *  vitalia's is a MOCK conversational store today). */
export interface ShellChatStoreApi { /* messages, conversations, status, newConversation, ... */ }

// ── Factory (consumes @luana/hooks/createSsrSafePersistedStore) ───────────────
export function createShellStore(opts: {
  storageKey: string;            // brand passes 'vitalia-shell-state' / 'nicolify-shell-state' (SC-6 compat)
  version?: number;              // default 1; brand passes its migrate() if legacy shape differs
  migrate?: (persisted: unknown, version: number) => Partial<ShellStoreState>;
}): UseBoundStore</* ShellStore */>;

// ── Root organism ─────────────────────────────────────────────────────────────
export interface ShellLayoutProps {
  children: React.ReactNode;
  // Brand identity (NO defaults that name a brand) ----------------------------
  supervisorName: string;             // e.g. "Valeria" | "Luana" — REQUIRED, no default
  supervisorAvatar?: React.ReactNode; // slot; falls back to <initial> circle
  supervisorInitial?: string;         // e.g. "V" | "L"
  agentCatalog: ShellAgentDescriptor[];
  ribbonOrder: string[];              // agent slugs in ribbon order
  subTabsByAgent: Record<string, readonly ShellSubTabMeta[]>;
  shippedStaticSubtabs?: ReadonlySet<string>;
  // Store injection (brand instantiates) -------------------------------------
  useShellStore: UseBoundStore</* ShellStore */>;
  useChatStore: UseBoundStore</* ShellChatStoreApi */>;
  // Group/layout persistence keys (SC-6 compat — brand passes its key) --------
  splitGroupId: string;               // e.g. "vitalia-shell-split-agentic"
  // TopBar slots (brand injects Logo/Theme/Tenant) ---------------------------
  logoSlot: React.ReactNode;          // brand LogoMark
  rightClusterSlot: React.ReactNode;  // brand [ThemeToggle][TenantSwitcher]
  // SSR skeleton (brand provides store-free header) --------------------------
  skeletonSlot?: React.ReactNode;     // default = neutral inert header
  // Copy / labels (Spanish neutro — brand may override) ----------------------
  labels?: Partial<{
    openSupervisor: string; collapseSupervisor: string;
    newConversation: string; history: string; mainContent: string;
  }>;
  // Routing helpers (or kit defaults from agentCatalog) ----------------------
  onNavigate?: (href: string) => void;
}

export function ShellLayout(props: ShellLayoutProps): JSX.Element;   // public wrapper (ssr:false inside)

// ── Named sub-exports (for tests / advanced composition) ──────────────────────
export { SupervisorSidebar, SupervisorCollapsedStrip, SupervisorHistory,
         ChatPanel, ChatHeader, ChatComposer, ChatMessages, MessageBubble,
         Ribbon, RibbonTab, SubTabsBar, SubTab, SubSubTabsBar, TopBarShell,
         AppPanelSlot } from "./components";
export { extractAgentFromPath, extractSubtabFromPath, isValidAgent, isValidSubtab } from "./routing";
export { createShellStore } from "./create-shell-store";
// NOTE: do NOT re-export react-resizable-panels' Group/Panel/Separator from the
// kit barrel — the kit already exports a form `Group` (collision). If a handle
// must be public, name it ShellResizeHandle.
```

## Store + localStorage strategy

- **Factory in kit, instance in brand.** `createShellStore` lives in the kit; it wraps `@luana/hooks/createSsrSafePersistedStore` (CONSUME — RN-8, ADR-vitalia-006). The brand's `stores/shell-store.ts` becomes a THIN file: `export const useShellStore = createShellStore({ storageKey: 'vitalia-shell-state', version: 1, migrate: migrateShellState })`.
- **Storage key CONSERVED (SC-6 hard).** The e2e harness hardcodes two keys: `vitalia-shell-state` (store) and `vitalia-shell-split-agentic` (react-resizable-panels Group id). The brand passes BOTH (`storageKey` + `splitGroupId`) → the existing 68+7 e2e suite stays green **without touching any assert** (RN-1/Bif-3). Nicolify passes `nicolify-shell-state` / `nicolify-shell-split` (its own keys).
- **Legacy shape migration (SC-6/Bif-5).** The kit factory accepts a `migrate` fn. Vitalia's machine is ALREADY the hardened `closed|chat`+`historyOpen` (v1) so vitalia passes its existing `migrateShellState` (v0 collapsed/rail/full → v1). **Nicolify** still has the legacy `luanaState: collapsed|history|full` + `shellMode` + `splitState` (v0) → nicolify passes a `migrate` mapping `luanaState→supervisorOpen` (collapsed→closed; history/full→chat) and DROPS `shellMode`/`splitState`. Existing-user localStorage hydrates to defaults without crash (`merge`/`sanitize` in the factory). Documented in the kit CHANGELOG.
- **Naming generic in kit:** `supervisorOpen` (not `valeriaOpen`), `splitPct` (not `valeriaPct`). The brand's thin store re-exports with whatever local alias it wants, but the kit type is generic (RN-2).

## ssr:false decision

See **Decisión C**. Wrapper lives in the kit (`ShellLayout` does `dynamic(() => import('./ShellLayoutClient'), { ssr:false, loading })`). `next` is already a peerDep `>=14` of the kit. The skeleton is brand-parameterized via `skeletonSlot`. This is the ONLY place `ssr:false` is declared post-lift → kills the per-brand duplication of the frágil pattern.

## SEMVER

See **Decisión D**: **0.3.0 → 0.4.0 (minor, additive organism layer)**. New deps `react-resizable-panels` + `zustand` added to kit `dependencies`. Zero breaking on existing exports. Group-name collision mitigated (no react-resizable-panels Group re-export). Documented in CHANGELOG + proposal at migrate.

## Integration design (CONN — anti-orphan)

Esta story es **lift de chrome existente** — no nace funcionalidad isla. Las 4 contenciones:

- **Consumed:** el `ShellLayout` del kit tiene ≥2 consumidores reales el día del merge: `vitalia/.../(shell-organism)/layout.tsx` lo monta + `nicolify/.../(shell-organism)/layout.tsx` lo monta. Cero export huérfano.
- **On the map:** zona Infraestructura → caja `plataforma-tecnica` (`map_zone: infraestructura`, chrome no-funcional). `cap_target: null` correcto (chrome transversal sin cap user-visible; precedente shell-core-hardening). El organism habilita las superficies de agente de ambas brands pero el patrón vive en el kit.
- **Navigable/reachable:** sin ruta nueva. Reachability = el `ShellLayout` ya es el wrapper de TODAS las rutas `(shell-organism)/**` en ambas brands. **Reachability path concreto (vitalia):** usuario → `/{tenantId}` → (proxy 307) → `/{tenantId}/{DEFAULT_LANDING_SUBPATH}` → server layout valida tenant → `<ShellLayout supervisorName="Valeria" agentCatalog={AGENT_CATALOG} useShellStore={useShellStore} ...>` (del kit) → ribbon/subtabs/SupervisorSidebar/ChatPanel → click sub-tab → page content en AppPanelSlot.
- **Notarized/registered:** el chrome se registra al importar `ShellLayout` de `@luana/ui-kit` en el `layout.tsx` del route group de cada brand (re-wire en el mismo ticket que borra el local — AC-9 equivalente). Barrel export del kit (`src/index.ts` → `organism/shell`). Cero `include_router` nuevo (FE-only). El arch test `test-no-cross-brand-shell-mirror` allowlist ENCOGE a vacío (el mirror muere — la métrica de que el registro es correcto).

## Cross-Cutting Concerns

- **Tenant isolation:** N/A en chrome (sin queries). El server `layout.tsx` de cada brand sigue validando tenant (Clerk + fetchUserTenants) — NO se toca. `tenant_id` del FE vía `useTenantId()`, NUNCA Clerk org (arch-test `test-no-clerk-organizations` debe seguir verde). El `[entityId]` N3 es UUID, NUNCA PHI en URL.
- **Currency / Master data:** N/A (chrome sin montos/fechas nuevas).
- **Spanish neutro LatAm:** microcopy del chrome neutro sin voseo. El kit recibe `labels?` por prop con defaults neutros ("Nueva conversación", "Historial", "Colapsar"). El kit NO hardcodea copy brand. (Excepción sales_agent NO aplica — el chat es chrome, no output del agente.)
- **PII / HIPAA-lite:** chrome no toca PHI. No se introduce PHI en localStorage (shell-store es no-phi-scope, mock chat-store). El kit no persiste PHI. El audit-log del server layout (brand) no cambia.
- **Native-first:** todo lint/tsc/vitest/playwright corre NATIVE host. `pnpm --filter @luana/ui-kit ...` native. NUNCA `docker exec`. **pnpm symlink-war (RN del checkpoint):** host-install para vitest/tsc, container-install para e2e — ver `05-guidelines.md`.
- **Engine boundary:** `core/@luana/ui-kit` (package TS) es editable por la **autorización explícita /pm-luana** de esta story (proposal accepted = ejecución del lift). NO es `core/luana-core-*/src/` (Python engine — ese sigue prohibido). El edit es el lift sancionado.
- **Cross-brand:** vitalia + nicolify se tocan AMBAS (sancionado por la proposal — convergencia RN-7). CERO import cross-brand (vitalia↛nicolify): ambos importan de `@luana/ui-kit` (arch-test CHECK A zero-tolerance debe seguir verde).
- **Tailwind content scan (Decisión transversal — deliverable real):** ver § Tailwind abajo.

### Tailwind content scan (deliverable verificado)

**Hallazgo:** vitalia usa Tailwind v4 con `@config "../../tailwind.config.ts"` cuyo `content` array escanea `./src/components/**`, `./src/app/**`, `./src/features/**` — **NO** `core/@luana/ui-kit`. El chrome usa clases **arbitrary/JIT** (`@[24rem]:inline-flex`, `grid-cols-[minmax(0,1fr)]`, `@container`) que SOLO se generan si el archivo que las contiene está en el scan. Hoy viven en `src/components/shared/shell-organism/**` (escaneado). **Al mover el chrome al kit, esas clases JIT dejan de escanearse en vitalia → el shell se rompe visualmente (RN-4 grid implícito/pill).**

**Deliverable (ticket vitalia re-wire):** agregar el scan del kit al pipeline Tailwind de vitalia. Dos opciones:
- **Opción A (preferida, v4 idiomática):** en `vitalia/frontend/src/app/globals.css` agregar `@source "../../../../core/@luana/ui-kit/src/organism/shell";` (Tailwind v4 `@source` directive — escanea el organism del kit). Ruta relativa desde globals.css.
- **Opción B (fallback v3-config):** agregar `"../../core/@luana/ui-kit/src/**/*.{ts,tsx}"` al `content` array de `tailwind.config.ts` (resolviendo la ruta relativa correcta desde el config).

**Nicolify NO necesita deliverable de scan:** nicolify NO tiene `tailwind.config.ts` → usa Tailwind v4 auto-source-detection (`@import "tailwindcss"` escanea el workspace incl. node_modules symlinks del kit). Verificar en el ticket nicolify que las clases JIT del shell aparecen (render-verify); si no, agregar `@source` igual.

**Verificación:** SC-5 `resizer-matrix.spec.ts` + live-verify SC-8 (el pill `@[24rem]` + el grid implícito visibles) son el gate real de que el scan funciona — NO basta tsc verde.

## Test Construction Plan

> Detalle ejecutable en `04-validators.yaml § test_construction_plan`. Orden TDD (RED→GREEN) por surface:

- **Kit (T-K, primero):** vitest del organism — `createShellStore` (transiciones máquina A/B/C, migrate legacy genérico, no-clobber hydration SC-6) · `ShellLayout` render con catalog mock genérico (NO 'Valeria'/'vitalia') · `extractAgentFromPath`/`extractSubtabFromPath` genéricos · `TopBarShell` slots · `_agent-tw-classes` con catalog por arg. **Tests migran desde los `.test.tsx` de vitalia, re-parametrizados a props genéricas.** + grep gate brand-token=0 (SC-3/SC-7).
- **Vitalia re-wire (T-V):** la suite EXISTENTE es el contrato — `npx tsc --noEmit && npx eslint src/ --cache && npx vitest run src/` (0 fail) + e2e `e2e/regression/shell-core-hardening/` 68/68 + `resizer-matrix.spec.ts` 7/7 + arch `test-no-cross-brand-shell-mirror` (allowlist encogida) + `test-no-clerk-organizations` verde. **CERO assert nuevo/modificado** (RN-1/Bif-3). Vitest de los componentes movidos se BORRAN de vitalia (viven en el kit).
- **Nicolify converge (T-N):** `npx tsc --noEmit && npx vitest run src/` (0 fail — tests legacy de `LuanaSidebar`/máquina vieja ACTUALIZADOS a la conducta del kit o RETIRADOS) + arch fitness + render-verify (component-level o e2e :3001 si levanta, Bif-2).
- **Gates finales:** grep `#01B2F8|vitalia|valeria` en lógica del kit = 0 · allowlists shrink · live-verify #37 vitalia (SC-8).

## Open Questions for PM

1. **N3 nicolify divergente (fuera de scope, pero el shell lo arrastra):** nicolify tiene su `EntityWorkspaceLayout.tsx`/`EntitySubNavBar.tsx` **brand-local** (NO consume el del kit — vitalia ya migró en T-5, nicolify no). El chrome del shell NO depende del N3 directamente (son surfaces de agente, no chrome). **Resolución del architect:** la convergencia del chrome (este lift) NO requiere migrar el N3 de nicolify — son ortogonales. Si el ticket nicolify descubre que su `ShellOrganismLayoutClient` legacy importa su N3 local de forma que bloquea el re-wire → parquear esa pieza (Bif-1/SC-9) + HANDOFF, NO inflar a migrar el N3 nicolify acá. La migración N3 nicolify es otra story (candidato lift análogo a vitalia T-5).
2. **`SubSubTab.tsx` solo existe en nicolify** (vitalia usa `SubSubTabsBar` sin `SubSubTab` átomo separado). Al liftar `SubSubTabsBar` genérico, verificar que cubra el caso nicolify (N3-static con subsubtab) o parquear (Bif-1). El kit `SubSubTabsBar` debe ser superset.
3. **Avatares finales:** vitalia/nicolify usan SVG/PNG placeholder (`public/agents/{slug}/`). El kit los recibe por `agentCatalog[].avatar` (slot/src) — cero asset en el kit. Confirmado: cero asset brand se liftea.
