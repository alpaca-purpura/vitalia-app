<!-- voseo-allowed: glosario reference + internal architecture documentation -->

---
story_id: vitalia-fase1-valeria-chat-skeleton
brand: vitalia
type: ui-story
phase: fase-1
last_modified: 2026-05-24
architect_iter: 1
architect_run_on: 2026-05-24
surfaces: FE_ONLY
predecessor_done: vitalia-fase1-valeria-rail-history  # archived 2026-05-24
---

# F1-S6 · vitalia-fase1-valeria-chat-skeleton · 03-arch.md (consolidado FE)

## § 0 — Context Summary

- **Story:** `vitalia-fase1-valeria-chat-skeleton` · outcome `vitalia-mvp-ui-foundation` · phase `fase-1`.
- **PR folder:** `vitalia/docs/product/stories/vitalia-fase1-valeria-chat-skeleton/`
- **Architect run on:** 2026-05-24 (Step 0 `date -u +%Y-%m-%d` = 2026-05-24, `date -u +%Y-%m` = 2026-05). Opus 4.7 knowledge cutoff Jan 2026; library currency verified live via canonical docs as of 2026-05-24 (Next.js 16 App Router + React 19 + Zustand 5 patterns unchanged from F1-S4/S5 baseline 1-30 days old; Shadcn UI primitives Textarea/Button/Badge cementados F1-S0).
- **Modules touched:** `shell-organism` (brand-local Vitalia frontend chrome — módulo doc `vitalia/docs/product/modules/shell-organism.md`).
- **Surfaces:** FE_ONLY · ZERO BE · ZERO AGENTIC · ZERO engine touch. Mock data hardcoded (`setTimeout` mock send), NO WebSocket, NO LLM, NO persist DB.

### Surface → builder → auditor mapping (PM uses to spawn correct agents)

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/{ValeriaChat,ChatHeader,ChatMessages,ChatComposer,MessageBubble,TypingIndicator,DelegateMarker}.tsx` (NEW organism + moléculas + átomo) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/components/shared/shell-organism/_mock-messages.ts` (NEW data + types) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/lib/agent-catalog.ts` (NEW catalog SSoT 6 agentes) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/stores/chat-store.ts` (NEW zustand store) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/app/globals.css` (MODIFY: add `--agent-mateo-soft` light + dark) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.tsx` (MODIFY: swap `<ValeriaChatSlot />` por `<ValeriaChat />`) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/components/shared/shell-organism/{ValeriaChatSlot.tsx,ValeriaChatSlot.test.tsx}` (DELETE) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/__tests__/architecture/*.test.ts` (extend allowlists shrink-only + 1 NEW arch test agent-catalog SSoT) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |
| `vitalia/frontend/e2e/shell-organism/**` (NEW Playwright suite) | `builder-frontend` (Sonnet/opencode/qwen) | `auditor-frontend` (Opus) |

ZERO BE surface. ZERO AGENTIC surface. ZERO engine touch. R23 NO aplica (zero agentic, all FE production_code).

### Skills consulted (decisions ratified verbatim)

- **`frontend-expert`** — Server-First default; `'use client'` solo en hojas con state/hooks/event-handlers (zustand + composer onKeyDown + sendMessage handler). FSD-Lite: `components/shared/shell-organism/` correct para cross-feature chrome; `stores/` para zustand global; `lib/` para catalog SSoT cross-shell. Tests colocated `__tests__/` siblings. Runtime quality checklist: useEffect deps complete, no stale closures (sendMessage en zustand action no en useEffect), hydration safety con scrollIntoView guard `useEffect` post-mount.
- **`tessl__react-patterns`** — React 19 + Next.js 16 App Router: Server Components default; ChatHeader/HistoryGroup-like pure presentation puede ser Server pero como vive dentro de ValeriaChat ('use client'), heredando boundary. IME composition handling NO requerido (composer no es cross-language input — bare text). Hooks contract: scrollIntoView via useEffect con dep `[messages.length]` (sentinel pattern). Event handlers `onKeyDown` con `e.isComposing` guard mantenido por consistencia con F1-S5 useKeyboardShortcuts pattern.
- **`tessl__shadcn-ui`** — REUSE primitives ya instalados F1-S0: `Textarea` (auto-resize via ref + rows=1), `Button` (variant default + ghost icon size), `Badge` (variant outline para mode pill). No upstream upgrade — versiones cementadas F1-S0.
- **`tessl__tailwind`** — Semantic tokens ONLY (DC §5.1): `bg-background`, `bg-card`, `bg-muted`, `text-foreground`, `text-muted-foreground`, `border-border`, `bg-agent-{slug}`, `bg-agent-{slug}-soft`. Tokens vitalia para 6 agentes existen en `globals.css` (F1-S1) EXCEPT `--agent-mateo-soft` que F1-S6 agrega (light `53 90% 90%` + dark `53 80% 18%`). NO hex literales en componentes. NO arbitrary values salvo `data-testid` y `max-h-[100px]` (Tailwind canonical).
- **`tessl__vitest`** — Colocated `Component.test.tsx`. RTL + `@testing-library/jest-dom` + `@testing-library/user-event`. Mock `useChatStore` via `useChatStore.setState({...})` directo + `useChatStore.getState().clearMessages()` afterEach. NO `vi.mock('@/stores/chat-store')`. Time mocking para mock `setTimeout` via `vi.useFakeTimers()` + `vi.advanceTimersByTime(800)`.
- **`playwright-expert`** — REUSE F1-S5 patterns: POM en `e2e/shell-organism/poms/` (consistencia: F1-S5 usó `e2e/pages/` legacy, F1-S6 inaugura `e2e/shell-organism/` per spec § 13 ratificado), fixtures shared (`shell-theme.fixture.ts` REUSE — extend para chat-store seed/empty), public route `/test-stack/shell-layout` (no auth gate), addInitScript determinism para localStorage `vitalia-shell-state` + `vitalia-chat-state`, axe-playwright ruleset wcag2aa, visual goldens iter 1 via `--update-snapshots --project=visual` post Chris ratify side-by-side mockup HTML.
- **`tessl__nextjs-app-router-modularization`** — `'use client'` boundaries: ValeriaChat root es Client (zustand + onClick); sub-componentes que reciben handlers como props pueden ser Server (HistoryGroup pattern) — pero por simplicidad y consistencia uniforme con F1-S5 todo el árbol chat es Client. Dynamic imports NO requeridos (componentes pequeños, sin code-split benefit a este nivel).
- **`tessl__zod`** — NO aplica — no hay form schema, composer es textarea libre sin validación.
- **`backend-expert` / `copilot-expert` / `sales-agent-expert` / `offer-expert` / `metrics-expert` / `brand-expert` / `offer-type-preset-expert`** — NO cargar. Story es FE only chrome UI sin BE/agentic/dominio negocio (HIPAA-lite scope: `not_applicable`, mock data sin PHI verificado).

### CONTEXT-BRIEF source

Self-ran greps Path B + Read directos (CONTEXT-BRIEF.md absent — story-by-story sin Haiku context-builder):
- `vitalia/docs/product/stories/vitalia-fase1-valeria-chat-skeleton/{checkpoint.md,01-spec.md,mockups/valeria-chat-sample.html}`
- `vitalia/docs/product/modules/shell-organism.md`
- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- `vitalia/docs/archive/2026/stories/vitalia-fase1-valeria-rail-history/{01-spec.md,03-arch.md,04-validators.yaml,05-guidelines.md,06-tickets.yaml}` (predecessor pattern)
- `vitalia/frontend/src/components/shared/shell-organism/ValeriaChatSlot.tsx` (placeholder to DELETE — confirma ChatHeader signature que F1-S6 EVOLVE)
- `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.tsx` (consumer — 2 occurrences `<ValeriaChatSlot />` a swappear líneas 204 + 249)
- `vitalia/frontend/src/app/globals.css` (verificado `--agent-mateo-soft` ausente; los otros 5 agentes tienen `-soft` definidos)
- `vitalia/frontend/public/agents/{slug}/{thumbnail.png,transparent.png}` ×6 — verificados presentes
- `vitalia/frontend/src/__tests__/architecture/*.test.ts` (16 arch tests existentes — para extend)
- Cardinal rules: `frontend-fsd.md`, `spanish-text.md`, `tdd-mandatory.md`, `tenant-isolation.md`, `anti-duplication.md`, `shell-mockup-per-component.md`, `hipaa-lite.md`.

### capability YAML files affected (post-merge updates required, paradigma post 2026-05)

- **MODIFY** `vitalia/docs/product/capabilities/shell-organism/valeria-sidebar.yaml` — agregar mención `replaced ValeriaChatSlot placeholder → ValeriaChat real organism` en `Surfaces / Frontend` + KPI delta (visual goldens 13 → 17 — agregar 4 chat snapshots).
- **NEW** `vitalia/docs/product/capabilities/shell-organism/valeria-chat.yaml` — capability nueva F1-S6 (`vitalia.shell-organism.valeria-chat`, status `live` post-merge; descripción: chat panel chrome con 6 mensajes mock + composer interactivo mock + empty state + agent catalog 6 agentes).
- **AUTO-REGEN** `vitalia/docs/product/modules/shell-organism.md` — auto-list block via `scripts/reconcile_capabilities.py --brand vitalia` (R3 gitignored ok — list block es tracked).

### Architecture gates that must keep passing (extend, no break)

- `test_fsd_boundaries.test.ts` — shell-organism NO importa features/*; nuevo `lib/agent-catalog.ts` se importa cross-shell sin violar FSD.
- `test-no-cross-brand-shell-mirror.test.ts` — extend con nombres NEW (`ValeriaChat`, `ChatHeader`, `ChatMessages`, `ChatComposer`, `MessageBubble`, `TypingIndicator`, `DelegateMarker`, `useChatStore`, `AGENT_CATALOG`).
- `test-shell-store-schema-readonly-f1-s5.test.ts` — invariant heredado F1-S5 (shell-store NO modificado, F1-S6 mantiene `chat-store` separado).
- `test_no_hardcoded_colors.test.ts` — tokens semánticos ONLY; hex literals en `agent-catalog.ts` permitidos como `hex` field SOLO si justificado (es metadata para mockup fallback, no consumido por Tailwind directamente — auditor verifica que componentes consumen `colorToken`/`colorSoftToken` no `hex`).
- `test-vitalia-ui-strings-no-voseo.test.ts` — Spanish neutro glossary regex extend para `MOCK_MESSAGES` + `MOCK_RESPONSES` + microcopy composer.
- `test_server_first.test.ts` — `'use client'` only en hojas (allowlist shrink-only — extend justificadamente con NEW client components).
- `test-no-vt-classes-in-new-features.test.ts` — NO `.vt-*` legacy utility classes en NEW code.
- `test-skip-link-target.test.ts` — `<main id="main-content">` NO afectado (out-of-scope).
- NEW: `test-agent-catalog-ssot.test.ts` — invariant: NO hardcoded agent name/color/thumbnail fuera de `agent-catalog.ts` (grep cross-shell-organism para `'valeria'|'camila'|'lisa'|'lucas'|'adrian'|'mateo'` strings fuera del catalog y del checkpoint hardcoded MOCK_MESSAGES).

## § 0.1 — Existing Systems Audit (NO NEW LAYER rule)

### Source of evidence

- [x] Self-run greps (Path B — context-builder fallback; CONTEXT-BRIEF.md absent for this story)

### Audit cross-module ejecutado

```bash
WS=/home/chalreme/Proyectos/luana-vitalia

# 1. Cross-brand mirror scan (anti-duplication.md cardinal rule)
for b in nicolify comunify lupulo; do
  for name in ValeriaChat ChatHeader ChatMessages ChatComposer MessageBubble TypingIndicator DelegateMarker useChatStore AGENT_CATALOG agent-catalog; do
    matches=$(grep -rln "$name" $WS/$b/frontend/src 2>/dev/null | grep -v node_modules | wc -l)
    if [ "$matches" -gt 0 ]; then echo "$b::$name → $matches matches"; fi
  done
done
# Result: nicolify::CopilotSidebar tiene MessageBubble + chat patterns similares pero implementación independiente.
#         Cero matches para nombres EXACTOS ValeriaChat/ChatHeader/etc en otras brands.
#         Nicolify CopilotSidebar es referenciable como pattern read-only — NO IMPORT.

# 2. Engine TS packages (core/@luana/*)
find $WS/core -name "*.tsx" 2>/dev/null | grep -E "Chat|Message" | head -5
# Result: 0 matches. Engine TS packages no exponen chat abstraction. ✅

# 3. Same-brand existing duplicates (vitalia/frontend/)
find $WS/vitalia/frontend/src -name "ChatHeader*" -o -name "MessageBubble*" -o -name "ChatComposer*" 2>/dev/null
# Result: 0 matches NEW names. ValeriaChatSlot existe (placeholder F1-S5 — to DELETE). ✅

# 4. Existing chat-store / agent-catalog
find $WS/vitalia/frontend/src -name "chat-store*" -o -name "agent-catalog*" 2>/dev/null
# Result: 0 matches. NEW correctly.

# 5. Nicolify CopilotSidebar (reference pattern, read-only)
ls $WS/nicolify/frontend/src/features/copilot/components/CopilotSidebar.tsx
# Result: EXISTE (read-only reference). Pattern similar pero scope distinto (Nicolify copilot tooltip
#         transversal, Vitalia ValeriaChat es agentic shell panel completo). NO IMPORT — cross-brand
#         HARD BAN per anti-duplication.md. Pattern documentado solo en arch notes.

# 6. Shadcn primitives ya instalados
ls $WS/vitalia/frontend/src/components/ui/{textarea,button,badge}.tsx
# Result: TODOS exist. ✅ REUSE sin upgrade.

# 7. Agent thumbnails verificados
ls $WS/vitalia/frontend/public/agents/{lisa,valeria,adrian,lucas,camila,mateo}/thumbnail.png
# Result: 6/6 thumbnails presentes + transparent variants verificadas (adrian transparent.jpeg, otros transparent.png).

# 8. CSS token --agent-mateo-soft gap verificado
grep "agent-mateo" $WS/vitalia/frontend/src/app/globals.css
# Result: --agent-mateo: 53 99% 51% existe.
#         --agent-mateo-soft NO existe. ★ GAP confirmado — F1-S6 lo agrega (D9 spec).

# 9. Lucide-react dependency
grep "lucide-react" $WS/vitalia/frontend/package.json
# Result: dependency presente. ✅ Icons disponibles (Paperclip, Mic, Zap NO requeridos — emoji stubs
#         per D3 spec).
```

### Sistemas existentes encontrados

| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| `useShellStore` zustand + persist | `vitalia/frontend/src/stores/shell-store.ts` | active F1-S4/S5 done | **NOT CONSUMED** por F1-S6 — chat-store separado por SoC. Arch test `test-shell-store-schema-readonly-f1-s5.test.ts` invariant heredado (NO modificar). |
| `ValeriaChatSlot` placeholder F1-S5 | `vitalia/frontend/src/components/shared/shell-organism/ValeriaChatSlot.tsx` + `.test.tsx` | active F1-S5 placeholder | **DELETE ambos** — reemplazado por `ValeriaChat` real F1-S6. ChatHeader del placeholder EVOLUCIONA (preserva avatar+name+status, agrega Mode Pill + status text largo per D1 spec). |
| `ValeriaSidebar` organism | `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.tsx` | active F1-S5 done | **MODIFY puntual**: import `ValeriaChatSlot` → `ValeriaChat` + 2 occurrences JSX swap (líneas 204, 249). NADA más. |
| Shadcn `Textarea`/`Button`/`Badge` | `vitalia/frontend/src/components/ui/` | active F1-S0 | **REUSE sin modificar** — primitives copy-paste local. |
| Lucide-react icons | `package.json` dep heredada | active | **NO USAGE F1-S6** — composer adornments son emojis (📎🎙️⚡) per D3 spec. Avatar fallback es texto "V". |
| Nicolify `CopilotSidebar` pattern | `nicolify/frontend/src/features/copilot/components/CopilotSidebar.tsx` | active read-only ref | **NO IMPORT** (cross-brand HARD BAN per anti-duplication.md). Pattern conceptualmente similar (chat bubbles + composer) pero implementación independiente — flag para futuro `/pm-luana` promotion candidate cuando ≥2 brands lo necesiten (LIFT CANDIDATE `core/@luana/shell-chat-organism/`). |
| Agent thumbnails public/ | `vitalia/frontend/public/agents/{slug}/{thumbnail.png,transparent.png}` | active (md5 sync 2026-05-24) | **REUSE READ-ONLY** — consumidos vía path string en `AGENT_CATALOG`. |
| `--agent-{slug}` CSS tokens 6 colores | `vitalia/frontend/src/app/globals.css` (F1-S1) | active EXCEPT `--agent-mateo-soft` | **MODIFY puntual** (D9 spec): agregar `--agent-mateo-soft` light `53 90% 90%` + dark `53 80% 18%`. Mismo PR. |
| `--agent-{slug}-soft` 5/6 | mismo file | active | REUSE — ya cementados F1-S1. |
| Tailwind theme.extend.colors.agent | `vitalia/frontend/tailwind.config.ts` | active (F1-S1) | **VERIFY ONLY** — `mateo` y `mateo-soft` entries deben existir en config (heredados F1-S1 según Design Contract §5.2). Si faltan: MODIFY puntual add entries. |

### Decisión por sistema

- **NEW components (7 archivos shell-organism + 1 catalog + 1 store + 1 mock)**: **NEW correctly** — primera ocurrencia, no mirror existente cross-brand. Pattern transposed conceptually del Nicolify CopilotSidebar pero adaptación significativa (organismo agéntico shell-panel vs floating tooltip copilot; 6 agentes catalog vs single copilot; delegate marker + thinking rich vs simple loading; mock interactive vs WebSocket real). DRY threshold = 2 consumers; F1-S6 es primera para vitalia agentic chat → NEW correcto. Future story que duplique en otra brand → triggerea `/pm-luana` promotion proposal para `core/@luana/shell-chat-organism/` (lift candidate, fuera scope F1-S6). Documentar en `vitalia/docs/learnings/2026-05-24-valeria-chat-promotion-candidate.md` post-merge.
- **NEW `chat-store.ts`**: **NEW correctly** — store separado de `shell-store.ts` por SoC (chat lifecycle vs shell layout state). Mismo brand-local. Patrón zustand idéntico a `shell-store.ts` (persist NOT REQUIRED — chat ephemeral cross-reload — spec § 11 implícito que MOCK_MESSAGES re-hidrata cada mount).
- **NEW `agent-catalog.ts`**: **NEW correctly** — SSoT canonical cross-shell-organism (consumido por ChatHeader F1-S6, futuros Ribbon/RailIconButtons F1-S7/S8). Vive en `lib/` (no en `components/shared/shell-organism/_agent-catalog.ts` per spec § 5.1 ratificación) porque será consumido cross-feature en F2-S* (sub-tabs per agente leen catalog). LIFT CANDIDATE `core/@luana/agent-catalog/` cuando otra brand defina catalog similar.
- **NEW `_mock-messages.ts`**: **NEW correctly** — fixtures hardcoded 6 mensajes + MOCK_RESPONSES rotativos. Vive bajo `components/shared/shell-organism/` (prefix `_` indica internal-only per FSD-Lite convention). NO promotable (data brand-specific Vitalia clínica).
- **MODIFY existing (2 archivos: `ValeriaSidebar.tsx`, `globals.css`)**: **EXTEND puntual ratificado** — diff verbatim spec § 13 + D9, NO scope creep adicional.
- **DELETE legacy (2 archivos: `ValeriaChatSlot.tsx` + `.test.tsx`)**: cleanup obligatorio del placeholder F1-S5. Ratificado spec § 13 + checkpoint.

**Cross-brand lift evaluation:** ValeriaChat + sus moléculas + agent-catalog son candidatos promotables cuando Nicolify/Comunify/Lupulo necesiten chat shell-panel pattern. Por ahora primera ocurrencia en Vitalia → NEW brand-local. Auditor flag `// LIFT CANDIDATE: cross-brand chat organism pattern, second consumer triggers /pm-luana proposal` en file headers de ValeriaChat + agent-catalog.

## § 1 — Surfaces involved (verbatim)

| Surface | Aplica | Owner |
|---|---|---|
| BE (FastAPI Python) | NO | — |
| AGENTIC (LangGraph / deepagents / sales_agent) | NO | — |
| FE (Next.js 16 App Router + Shadcn + Tailwind + Zustand + React 19) | **SÍ** | `builder-frontend` Sonnet/opencode/qwen |

## § 2 — FE Architecture Detail

### § 2.1 — Component tree (atomic design)

```
ValeriaSidebar (MODIFY F1-S5 — swap slot for real chat, 2 occurrences)
└── ValeriaChat (NEW organism, 'use client')
    ├── useChatStore consumer (READ active state)
    ├── ChatHeader (NEW molécula, 'use client')
    │   ├── consume AGENT_CATALOG[activeAgent] (default 'valeria')
    │   ├── avatar 9×9 (PNG thumbnail con onError fallback initial letra)
    │   ├── status dot bg-vitalia-success (decorative)
    │   ├── name + role/status text
    │   └── Mode Pill Badge "🤖 Modo agente"
    ├── ChatMessages (NEW molécula, 'use client')
    │   ├── role="log" aria-live="polite" aria-label
    │   ├── empty state branch (messages.length === 0)
    │   │   └── EmptyState inline (ilustración avatar grande + heading + subtexto)
    │   └── populated branch
    │       ├── auto-scroll sentinel useEffect [messages.length]
    │       └── messages.map per role:
    │           ├── bot   → MessageBubble role='bot'    (bg-card border per agent)
    │           ├── user  → MessageBubble role='user'   (bg-agent-valeria text-white)
    │           ├── delegate → DelegateMarker (italic centered con pill toAgent)
    │           └── thinking → TypingIndicator (bubble + texto + 3 dots animados)
    └── ChatComposer (NEW molécula, 'use client')
        ├── 3 IconButtons stubs (📎🎙️⚡) — type=button + title="próximamente"
        ├── <label sr-only for="valeria-composer">
        ├── Textarea Shadcn (id="valeria-composer", rows=1, max-h-100px)
        │   ├── onChange: setLocalValue
        │   ├── onKeyDown:
        │   │   ├── Enter (no Shift, no isComposing) → sendMessage(value) + clear
        │   │   └── Shift+Enter → newline (default)
        │   └── auto-resize: useEffect [value] adjust scrollHeight
        ├── Send Button (variant default bg-agent-valeria text-white "Enviar")
        └── kbd hint footer "Cmd+K enfoca el composer..."
```

Note: ChatMessages renderiza el "empty state" inline (no extracted como componente separado — D8 spec § 2 establece variante B en el mismo mockup; mantenemos lógica branch dentro de ChatMessages para evitar componente sub-utilizado).

### § 2.2 — Mock send flow (state machine)

```
Initial state:
  messages = MOCK_MESSAGES (6 items hardcoded)  ó  []  per test fixture
  status = 'idle'
  activeAgent = 'valeria' (default DEFAULT_CHAT_AGENT)

User types in composer + Press Enter (no Shift, no isComposing, value.trim() !== ''):
  1. sendMessage(value) en chat-store:
     a. Push { role: 'user', content: value, time: HH:MM_now }
     b. Push { role: 'thinking', agent: activeAgent, content: "${name} está escribiendo…" }
     c. Set status = 'thinking'
     d. clearTimeout previo (cleanup ref) si existe
     e. setTimeout(800ms):
        - Pop the thinking message (filter out role='thinking')
        - Push { role: 'bot', agent: activeAgent, content: MOCK_RESPONSES[count % len], time: HH:MM_now }
        - Set status = 'idle'

  Determinism: MOCK_RESPONSES rotativo (`count % len`) — NO random — Playwright snapshots
  pueden assert respuesta esperada. count = messages.filter(m => m.role === 'user').length
  (estable post-send).

  Idempotency: si status === 'thinking' al press Enter, ignorar input (no double-fire).
```

### § 2.3 — chat-store contract (zustand)

```ts
// vitalia/frontend/src/stores/chat-store.ts

import { create } from 'zustand'
import type { AgentSlug } from '@/lib/agent-catalog'
import { DEFAULT_CHAT_AGENT } from '@/lib/agent-catalog'
import { MOCK_MESSAGES, MOCK_RESPONSES_BY_AGENT } from '@/components/shared/shell-organism/_mock-messages'

export type MessageRole = 'bot' | 'user' | 'delegate' | 'thinking'

export interface ChatMessage {
  id: string
  role: MessageRole
  content?: string
  time?: string                // 'HH:MM' (calculado runtime es-PE locale)
  agent?: AgentSlug            // bot/thinking source (default activeAgent)
  fromAgent?: AgentSlug        // delegate only — quien delega
  toAgent?: AgentSlug          // delegate only — receptor delegación
  delegateMode?: string        // delegate only — etiqueta del modo ('Mantener', etc.)
}

export type ChatStatus = 'idle' | 'thinking' | 'streaming'

export interface ChatStore {
  messages: ChatMessage[]
  activeAgent: AgentSlug
  status: ChatStatus
  sendMessage(content: string): void
  clearMessages(): void
  setActiveAgent(agent: AgentSlug): void
}

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [...MOCK_MESSAGES],
  activeAgent: DEFAULT_CHAT_AGENT,
  status: 'idle',
  sendMessage: (content: string) => {
    const trimmed = content.trim()
    if (!trimmed) return
    if (get().status === 'thinking') return  // idempotency guard
    const activeAgent = get().activeAgent
    const userCount = get().messages.filter(m => m.role === 'user').length
    const responses = MOCK_RESPONSES_BY_AGENT[activeAgent] ?? MOCK_RESPONSES_BY_AGENT.valeria
    const replyContent = responses[userCount % responses.length].content
    const now = new Date().toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' })

    // 1. Push user + thinking (sync state update)
    set((s) => ({
      status: 'thinking',
      messages: [
        ...s.messages,
        { id: crypto.randomUUID(), role: 'user', content: trimmed, time: now },
        { id: crypto.randomUUID(), role: 'thinking', agent: activeAgent,
          content: `${activeAgent[0].toUpperCase() + activeAgent.slice(1)} está escribiendo…` },
      ],
    }))

    // 2. After 800ms: replace thinking with bot reply
    setTimeout(() => {
      const replyTime = new Date().toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' })
      set((s) => ({
        status: 'idle',
        messages: [
          ...s.messages.filter(m => m.role !== 'thinking'),
          { id: crypto.randomUUID(), role: 'bot', agent: activeAgent, content: replyContent, time: replyTime },
        ],
      }))
    }, 800)
  },
  clearMessages: () => set({ messages: [], status: 'idle' }),
  setActiveAgent: (agent: AgentSlug) => set({ activeAgent: agent }),
}))
```

**NO persist middleware** — chat ephemeral cross-reload (re-hidrata MOCK_MESSAGES on mount). F2-S* introducirá persist via API/DB cuando wire WebSocket real.

**Note `setActiveAgent`**: API expuesto pero NO consumido por UI F1-S6 (preparado para sub-story futura "AgentSwitcher dropdown en ChatHeader" — ratificado D9 spec).

### § 2.4 — Agent catalog contract

```ts
// vitalia/frontend/src/lib/agent-catalog.ts
//
// SSoT canonical 6 agentes Vitalia. Consumido cross-shell-organism (ChatHeader F1-S6,
// futuros Ribbon F1-S7, RailIconButtons F1-S8, sub-tabs F2-S*).
//
// LIFT CANDIDATE: cross-brand agent registry pattern. Second brand consumer triggers
// /pm-luana promotion proposal para core/@luana/agent-catalog/.

export type AgentSlug = 'lisa' | 'valeria' | 'adrian' | 'lucas' | 'camila' | 'mateo'

export interface AgentDescriptor {
  slug: AgentSlug
  name: string                    // display name con acentos
  role: string                    // 1-line rol para tooltip/header subtitle
  colorToken: string              // CSS var sin -- prefix (e.g. 'agent-valeria')
  colorSoftToken: string          // soft variant (e.g. 'agent-valeria-soft')
  hex: string                     // hex literal — METADATA SOLO (mockup fallback, NO consumido por Tailwind)
  thumbnail: string               // Next.js public/ path
  transparent: string             // Next.js public/ path
  initial: string                 // letra fallback si img onError fires
}

export const AGENT_CATALOG: Record<AgentSlug, AgentDescriptor> = {
  lisa:    { slug: 'lisa',    name: 'Lisa',    role: 'Estratega de marca y oferta',                    colorToken: 'agent-lisa',    colorSoftToken: 'agent-lisa-soft',    hex: '#00D084', thumbnail: '/agents/lisa/thumbnail.png',    transparent: '/agents/lisa/transparent.png',     initial: 'L' },
  valeria: { slug: 'valeria', name: 'Valeria', role: 'Tu secretaria virtual · coordinadora general',   colorToken: 'agent-valeria', colorSoftToken: 'agent-valeria-soft', hex: '#7b2d91', thumbnail: '/agents/valeria/thumbnail.png', transparent: '/agents/valeria/transparent.png',  initial: 'V' },
  adrian:  { slug: 'adrian',  name: 'Adrián',  role: 'Closer · califica leads y reactiva oportunidades', colorToken: 'agent-adrian',  colorSoftToken: 'agent-adrian-soft',  hex: '#01b2f8', thumbnail: '/agents/adrian/thumbnail.png',  transparent: '/agents/adrian/transparent.jpeg',  initial: 'A' },
  lucas:   { slug: 'lucas',   name: 'Lucas',   role: 'Estratega Growth · viraliza y consigue leads',   colorToken: 'agent-lucas',   colorSoftToken: 'agent-lucas-soft',   hex: '#111111', thumbnail: '/agents/lucas/thumbnail.png',   transparent: '/agents/lucas/transparent.png',    initial: 'L' },
  camila:  { slug: 'camila',  name: 'Camila',  role: 'Fidelización · sube CLTV y monitorea satisfacción', colorToken: 'agent-camila',  colorSoftToken: 'agent-camila-soft',  hex: '#180d95', thumbnail: '/agents/camila/thumbnail.png',  transparent: '/agents/camila/transparent.png',   initial: 'C' },
  mateo:   { slug: 'mateo',   name: 'Mateo',   role: 'Desarrollador · tecnología y diseño con IA',     colorToken: 'agent-mateo',   colorSoftToken: 'agent-mateo-soft',   hex: '#fee209', thumbnail: '/agents/mateo/thumbnail.png',   transparent: '/agents/mateo/transparent.png',    initial: 'M' },
} as const

export const DEFAULT_CHAT_AGENT: AgentSlug = 'valeria'

export const AGENT_SLUGS = ['lisa', 'valeria', 'adrian', 'lucas', 'camila', 'mateo'] as const
```

**Tailwind classnames pattern (NO dynamic class construction with template literals):**
- Tailwind safelist o explicit cn() use case. Componentes consumen via mapping explícito o via inline `style={{ backgroundColor: 'hsl(var(--agent-valeria))' }}` ONLY si Tailwind CSS-vars classes no funcionan.
- **Recomendado**: usar el utility class explícito conocido (`bg-agent-valeria`, `bg-agent-camila`, etc.) — son tokens pre-registrados en `tailwind.config.ts`. Componentes deben mapear `colorToken` a className via switch o lookup (no template literal).
- Safelist explicit en `tailwind.config.ts` si CSS dynamic name detected — auditor verifica.

**Hex field rationale**: solo metadata para mockup HTML reference o test inspection — componentes Tailwind consumen `colorToken`/`colorSoftToken`. Arch test `test-agent-catalog-ssot.test.ts` verifica que componentes NO importan `hex` field (sólo metadata).

### § 2.5 — Sub-component contracts (NEW)

#### ValeriaChat (organism root)

- File: `vitalia/frontend/src/components/shared/shell-organism/ValeriaChat.tsx`
- Type: `'use client'`
- Props: none (consume `useChatStore`)
- Renders `<section role="region" aria-label="Chat con Valeria" data-testid="valeria-chat" className="grid grid-rows-[auto_1fr_auto] overflow-hidden">`
- Children: `<ChatHeader />` + `<ChatMessages />` + `<ChatComposer />`

#### ChatHeader (molécula)

- File: `vitalia/frontend/src/components/shared/shell-organism/ChatHeader.tsx`
- Type: `'use client'` (consume useChatStore activeAgent)
- Props: opcional `{ agent?: AgentSlug, status?: 'online' | 'offline', mode?: 'agent' }` — defaults activeAgent del store + 'online' + 'agent'
- Render: `<header data-testid="chat-header" className="flex items-center gap-3 border-b border-border px-4 h-14 shrink-0">`
  - Avatar 9×9 rounded-full bg-{colorToken} + img PNG `thumbnail` con `onError` → mostrar `initial` letter fallback ("V" en círculo bg-agent-valeria)
  - Status dot bg-vitalia-success (decorative, aria-hidden)
  - Name + status text ("En línea · Tu secretaria virtual" para Valeria)
  - Mode Pill: `<Badge variant="outline" data-testid="chat-mode-pill">🤖 Modo agente</Badge>`

**Avatar onError pattern (Scenario 4):**

```tsx
const [imgError, setImgError] = useState(false)
return (
  <div className="relative shrink-0">
    <div className={cn("h-9 w-9 rounded-full overflow-hidden flex items-center justify-center", agentBgClass(agent))} aria-hidden="true">
      {imgError ? (
        <span className="text-sm font-semibold text-white select-none">{descriptor.initial}</span>
      ) : (
        <img src={descriptor.thumbnail} alt="" className="h-9 w-9 object-cover" onError={() => setImgError(true)} />
      )}
    </div>
    <span className="absolute bottom-0 right-0 h-2 w-2 rounded-full bg-vitalia-success ring-2 ring-card" aria-hidden="true" />
  </div>
)
```

Helper `agentBgClass(slug)` retorna className explícito via switch (no template literal — preserva Tailwind JIT).

#### ChatMessages (molécula)

- File: `vitalia/frontend/src/components/shared/shell-organism/ChatMessages.tsx`
- Type: `'use client'` (useEffect scroll sentinel + useChatStore.messages selector)
- Props: none
- Render: `<div data-testid="chat-messages" role="log" aria-live="polite" aria-label="Conversación con Valeria" className="flex-1 min-h-0 overflow-y-auto px-4 py-4 flex flex-col gap-3">`
- Branches:
  - `messages.length === 0` → empty state inline (ilustración + heading + subtexto verbatim spec § 6)
  - Else: messages.map → switch on role → render MessageBubble | DelegateMarker | TypingIndicator
- useEffect [messages.length]: scroll sentinel `<div ref={endRef} />` al final + `endRef.current?.scrollIntoView({ behavior: 'smooth' })` post-mount safe (only client)

#### MessageBubble (molécula)

- File: `vitalia/frontend/src/components/shared/shell-organism/MessageBubble.tsx`
- Type: `'use client'` (suficiente — pure presentation pero está dentro de árbol Client; mantenemos `'use client'` por consistencia con padres y para evitar accidental Server boundary cross)
- Props: `{ role: 'bot' | 'user', content: string, time?: string, agent?: AgentSlug, footerLabel?: string }`
- Render bot: `<div className="flex flex-col gap-1 self-start max-w-[80%]">`
  - bubble: `<div data-testid="msg-bubble" data-role="bot" className="bg-card border border-border text-foreground rounded-2xl rounded-bl-sm px-3 py-2 text-sm leading-relaxed whitespace-pre-wrap">{content}</div>`
  - footer: `<span className="text-[10px] text-muted-foreground px-1">{agentName} · {time}</span>`
- Render user: `<div className="flex flex-col gap-1 self-end max-w-[80%] items-end">`
  - bubble: `<div data-testid="msg-bubble" data-role="user" className="bg-agent-valeria text-white rounded-2xl rounded-br-sm px-3 py-2 text-sm leading-relaxed whitespace-pre-wrap">{content}</div>`
  - footer: `<span className="text-[10px] text-muted-foreground px-1">{time}</span>`

**XSS guard (Scenario 4):** content renderizado vía JSX text-children (`{content}`) — React auto-escapa. NUNCA `dangerouslySetInnerHTML`. Verificable por Playwright dialog event listener + DOM inspection del `<script>` literal escapado. Auditor verifica grep `dangerouslySetInnerHTML` en NEW files = 0 matches.

**Camila via Valeria styling (D batch_3 ratificado checkpoint):** bot Camila via Valeria mantiene `bg-card border-border` neutral. Footer label muestra "Camila (via Valeria) · HH:MM" con thumbnail Camila inline. NO border-l accent agent-camila en F1-S6 (futuro si UX lo pide).

#### TypingIndicator (átomo)

- File: `vitalia/frontend/src/components/shared/shell-organism/TypingIndicator.tsx`
- Type: `'use client'` (animación CSS-only; mantener Client para consistency con padre)
- Props: `{ agent?: AgentSlug, text?: string }` — defaults activeAgent + "Valeria está escribiendo…"
- Render: `<div data-testid="msg-thinking" className="flex flex-col gap-1 self-start max-w-[80%]"><div className="bg-{agent-colorSoft} ... flex items-center gap-2"><span className="font-medium text-{agent-color}">{agentName}</span><span className="text-muted-foreground">{actionText}</span><span aria-hidden="true" className="flex items-end gap-0.5 ml-1"><span className="typing-dot h-1.5 w-1.5 rounded-full bg-{agent-color}"></span><span className="typing-dot h-1.5 w-1.5 rounded-full bg-{agent-color}"></span><span className="typing-dot h-1.5 w-1.5 rounded-full bg-{agent-color}"></span></span></div></div>`
- CSS keyframes `@keyframes typing-dot` definidas en `globals.css` o componente con `<style jsx>` o Tailwind plugin. Por simplicidad: add `.typing-dot` rule a `globals.css` mismo PR (justificado en commit body — single small CSS rule, no merece plugin Tailwind).

#### DelegateMarker (molécula)

- File: `vitalia/frontend/src/components/shared/shell-organism/DelegateMarker.tsx`
- Type: `'use client'` (consistency)
- Props: `{ fromAgent: AgentSlug, toAgent: AgentSlug, mode?: string }`
- Render: `<div data-testid="msg-delegate" className="self-center text-xs italic text-muted-foreground flex items-center gap-1.5 py-1">→ delegando a <span className="inline-flex items-center gap-1"><thumbnail-circle /><span className="font-medium text-{toAgent-color}">{toAgentName}</span></span><span className="text-muted-foreground">(modo {mode})</span></div>`

#### ChatComposer (molécula)

- File: `vitalia/frontend/src/components/shared/shell-organism/ChatComposer.tsx`
- Type: `'use client'` (useState localValue + onKeyDown + useRef textarea)
- Props: none (consume `useChatStore.sendMessage`)
- Render: `<footer data-testid="chat-composer" className="border-t border-border bg-card px-3 py-2 shrink-0">` con:
  - 3 IconButtons stubs (📎🎙️⚡) — `<button type="button" aria-label="Adjuntar archivo" title="Adjuntar (próximamente)" className="h-8 w-8 rounded-md hover:bg-muted text-muted-foreground flex items-center justify-center text-base"><span aria-hidden="true">📎</span></button>` (no `disabled` per D3 spec)
  - `<label htmlFor="valeria-composer" className="sr-only">Mensaje para Valeria</label>`
  - Textarea Shadcn: `<Textarea id="valeria-composer" data-testid="composer-input" rows={1} placeholder="Escribe a Valeria… (Enter envía · Shift+Enter salto de línea)" value={localValue} onChange={...} onKeyDown={handleKeyDown} className="flex-1 resize-none max-h-[100px]" />`
  - Send Button: `<Button type="button" data-testid="composer-send" onClick={handleSend} className="h-9 px-3 rounded-md bg-agent-valeria text-white text-sm font-medium hover:opacity-90 shrink-0 self-end">Enviar</Button>`
  - kbd hint: `<p className="text-[10px] text-muted-foreground mt-1 px-1"><kbd>Cmd</kbd> + <kbd>K</kbd> enfoca el composer desde cualquier parte del shell.</p>`

**onKeyDown handler:**

```ts
const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
  if (e.isComposing) return                       // IME composition safety
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
  // Shift+Enter: default behavior (newline)
}

const handleSend = () => {
  const trimmed = localValue.trim()
  if (!trimmed) return
  sendMessage(trimmed)
  setLocalValue('')
  // Reset textarea height
  if (textareaRef.current) textareaRef.current.style.height = 'auto'
}
```

**Auto-resize:**

```ts
useEffect(() => {
  if (!textareaRef.current) return
  textareaRef.current.style.height = 'auto'
  const next = Math.min(textareaRef.current.scrollHeight, 100)
  textareaRef.current.style.height = `${next}px`
}, [localValue])
```

`id="valeria-composer"` matches F1-S5 `useKeyboardShortcuts` Cmd+K focus selector — flujo Cmd+K → focus composer textarea preservado.

### § 2.6 — _mock-messages.ts shape

```ts
// vitalia/frontend/src/components/shared/shell-organism/_mock-messages.ts

import type { AgentSlug } from '@/lib/agent-catalog'
import type { ChatMessage } from '@/stores/chat-store'

// IDs estables ('1'..'6') NO crypto.randomUUID() — Playwright snapshots determinismo.
// Spanish neutro verbatim spec § 6 (tuteo, sin voseo).
export const MOCK_MESSAGES: readonly ChatMessage[] = [
  { id: '1', role: 'bot',      agent: 'valeria', content: '¡Buenos días! Tienes 8 turnos hoy y 3 pacientes esperando confirmar mañana. ¿Por dónde empezamos?', time: '09:01' },
  { id: '2', role: 'user',                       content: '¿Cómo están las reseñas Google esta semana?',                                                       time: '09:02' },
  { id: '3', role: 'delegate', fromAgent: 'valeria', toAgent: 'camila',  delegateMode: 'Mantener' },
  { id: '4', role: 'bot',      agent: 'camila',  content: 'Esta semana ingresaron +3 reseñas Google (2 de 5★ y 1 de 4★). El score subió de 4.6 a 4.7. Hay una reseña destacable de Marina Pérez sobre Dr. Juan García que sugiero pinear en landing. ¿La abro?', time: '09:02' },
  { id: '5', role: 'user',                       content: 'Sí, ábrela.',                                                                                       time: '09:03' },
  { id: '6', role: 'thinking', agent: 'camila',  content: 'Camila está abriendo Voz del paciente…' },
] as const

// 4 canned responses per agente (F1-S6 solo hardcodea Valeria; otros con fallback empty array
// → store usa MOCK_RESPONSES_BY_AGENT.valeria default).
export const MOCK_RESPONSES_BY_AGENT: Record<AgentSlug, ReadonlyArray<{ content: string }>> = {
  valeria: [
    { content: 'Mañana tienes 12 turnos confirmados y 4 pendientes. ¿Quieres que envíe recordatorios?' },
    { content: 'Esta semana cerraste 23 turnos. Promedio diario: 4.6. Día más cargado: jueves (7 turnos).' },
    { content: 'Te confirmo: agendé el turno para Marina Pérez el viernes a las 10:30. ¿Algo más?' },
    { content: 'Faltan 3 pacientes por confirmar para mañana. ¿Quieres que los contacte ahora por WhatsApp?' },
  ],
  lisa:    [],
  adrian:  [],
  lucas:   [],
  camila:  [],
  mateo:   [],
} as const
```

**Anti-PHI verification:** "Marina Pérez" + "Dr. Juan García" son nombres ficticios del mockup ratificado por Chris (NO datos reales). Per `hipaa-lite.md`, PHI scope is `not_applicable` para shell chrome (UI mock data). Aún así, evitamos datos clínicos reales: nombres son del mockup ratificado, NO diagnósticos/dosis/labs. Validador `i18n` arch + e2e grep verifica no patterns medical real.

### § 2.7 — Side-effects MODIFY contract (scope discipline strict)

#### `ValeriaSidebar.tsx` (MODIFY puntual)

**ÚNICO cambio permitido — Diff verbatim:**

```diff
- import { ValeriaChatSlot } from "./ValeriaChatSlot";
+ import { ValeriaChat } from "./ValeriaChat";
```

```diff
- <ValeriaChatSlot />
+ <ValeriaChat />
```

(2 occurrences líneas 204 + 249 — actualizar AMBAS.)

**NADA más se toca**: state machine, mobile drawer, focus trap, keyboard handlers, todos preserved. Solo el delta arriba.

#### `globals.css` (MODIFY add-only D9)

**Cambio ADD-ONLY — agregar `--agent-mateo-soft` light + dark + typing-dot animation:**

```diff
  :root {
    ...
    --agent-mateo: 53 99% 51%;
+   --agent-mateo-soft: 53 90% 90%;
    --agent-config: 240 4% 46%;
  }

  .dark {
    ...
    --agent-camila-soft: 244 50% 20%;
+   --agent-mateo-soft: 53 80% 18%;
  }

+ /* Typing dots keyframes (F1-S6 TypingIndicator) */
+ @keyframes typing-dot {
+   0%, 60%, 100% { opacity: 0.25; transform: translateY(0); }
+   30%           { opacity: 1;    transform: translateY(-2px); }
+ }
+ .typing-dot { animation: typing-dot 1.2s infinite ease-in-out; }
+ .typing-dot:nth-child(2) { animation-delay: 0.15s; }
+ .typing-dot:nth-child(3) { animation-delay: 0.30s; }
```

**NADA más se toca** en globals.css — todos los demás tokens preserved (F1-S1/S2/S3/S4/S5 cementados).

**Verify `tailwind.config.ts`** — los entries `agent.mateo` y `agent['mateo-soft']` deben existir en `theme.extend.colors.agent` per Design Contract §5.2. Si faltan: agregar entries (MODIFY puntual mismo PR).

#### DELETE files (cleanup)

- `vitalia/frontend/src/components/shared/shell-organism/ValeriaChatSlot.tsx` — DELETE entero
- `vitalia/frontend/src/components/shared/shell-organism/ValeriaChatSlot.test.tsx` — DELETE entero

### § 2.8 — File tree (canonical)

```
vitalia/frontend/src/
├── components/shared/shell-organism/
│   ├── ValeriaChat.tsx                          NEW (T-5 organism)
│   ├── ValeriaChat.test.tsx                     NEW (T-5)
│   ├── ChatHeader.tsx                           NEW (T-3 molécula)
│   ├── ChatHeader.test.tsx                      NEW (T-3)
│   ├── ChatMessages.tsx                         NEW (T-5 molécula — covered en ValeriaChat.test.tsx)
│   ├── ChatComposer.tsx                         NEW (T-4 molécula)
│   ├── ChatComposer.test.tsx                    NEW (T-4)
│   ├── MessageBubble.tsx                        NEW (T-3 molécula)
│   ├── MessageBubble.test.tsx                   NEW (T-3)
│   ├── TypingIndicator.tsx                      NEW (T-3 átomo)
│   ├── DelegateMarker.tsx                       NEW (T-3 molécula)
│   ├── _mock-messages.ts                        NEW (T-2 data + types)
│   ├── ValeriaSidebar.tsx                       MODIFY (T-6 — swap import + 2 JSX occurrences)
│   ├── ValeriaChatSlot.tsx                      DELETE (T-6)
│   └── ValeriaChatSlot.test.tsx                 DELETE (T-6)
│
├── lib/
│   └── agent-catalog.ts                         NEW (T-1 SSoT 6 agentes)
│
├── stores/
│   └── chat-store.ts                            NEW (T-2 zustand)
│
├── app/
│   └── globals.css                              MODIFY (T-1 — add --agent-mateo-soft + typing-dot keyframes)
│
├── __tests__/architecture/
│   ├── test-no-cross-brand-shell-mirror.test.ts   MODIFY (T-6 — extend names shrink-only)
│   ├── test-shell-store-schema.test.ts             UNCHANGED (regression guard)
│   ├── test-shell-store-schema-readonly-f1-s5.test.ts  UNCHANGED (heredado F1-S5)
│   ├── test_no_hardcoded_colors.test.ts            UNCHANGED (verifica componentes — agent-catalog hex allowlisted como metadata)
│   ├── test_server_first.test.ts                   MODIFY (T-6 — extend 'use client' allowlist NEW files)
│   ├── test_no_voseo_in_copy.test.ts               UNCHANGED (grep glossary contra NEW code mismo)
│   ├── test-vitalia-ui-strings-no-voseo.test.ts    UNCHANGED (auto picks NEW components — grep extiende dirpath)
│   └── test-agent-catalog-ssot.test.ts             NEW (T-6 — invariant: no hardcoded agent name/color fuera de catalog)
│
└── (test for chat-store + agent-catalog)
    ├── stores/__tests__/chat-store.test.ts      NEW (T-2 — sendMessage flow + clearMessages + setActiveAgent)
    └── lib/__tests__/agent-catalog.test.ts      NEW (T-1 — completeness 6 agentes + shape + DEFAULT_CHAT_AGENT)

vitalia/frontend/e2e/shell-organism/
├── poms/
│   └── valeria-chat-page.pom.ts                  NEW (T-7 POM)
├── fixtures/
│   └── chat-store-seed.fixture.ts                NEW (T-7 fixtures chatStoreSeed + chatStoreEmpty)
├── valeria-chat-happy.spec.ts                    NEW (T-8 SC-1)
├── valeria-chat-send.spec.ts                     NEW (T-8 SC-2)
├── valeria-chat-keys.spec.ts                     NEW (T-8 SC-3)
├── valeria-chat-xss.spec.ts                      NEW (T-8 SC-4)
├── valeria-chat-empty.spec.ts                    NEW (T-8 SC-5)
├── valeria-chat-a11y.spec.ts                     NEW (T-9 SC-6 + axe)
├── valeria-chat-i18n.spec.ts                     NEW (T-9 SC-7)
└── valeria-chat-visual.spec.ts                   NEW (T-9 visual — 4 PNGs)
```

### § 2.9 — Test construction order (canonical TDD RED-first)

```
T-1 — agent-catalog.ts + globals.css agent-mateo-soft + typing-dot (foundation)
  RED: lib/__tests__/agent-catalog.test.ts (cases: 6 agentes presentes, DEFAULT_CHAT_AGENT='valeria', shape complete, hex literal field present)
  GREEN: lib/agent-catalog.ts + app/globals.css MODIFY (agent-mateo-soft + typing-dot)
  (tailwind.config.ts verify si faltan entries mateo: MODIFY add)

T-2 — chat-store.ts + _mock-messages.ts (foundation data + state)
  RED: stores/__tests__/chat-store.test.ts (cases: initial state messages=MOCK_MESSAGES, sendMessage flow user+thinking+800ms bot, clearMessages, setActiveAgent, idempotency status==='thinking' guard, MOCK_RESPONSES rotativo determinista)
  GREEN: stores/chat-store.ts + components/shared/shell-organism/_mock-messages.ts
  Depends: T-1 (consume AgentSlug type + DEFAULT_CHAT_AGENT)

T-3 — Átomos + moléculas low-level (MessageBubble + TypingIndicator + DelegateMarker + ChatHeader)
  RED: MessageBubble.test.tsx + ChatHeader.test.tsx (TypingIndicator + DelegateMarker cubiertos por ValeriaChat.test.tsx integradores)
  GREEN: MessageBubble.tsx + ChatHeader.tsx + TypingIndicator.tsx + DelegateMarker.tsx
  Depends: T-1 (consume AGENT_CATALOG + AgentSlug)

T-4 — ChatComposer (composer interactivo con sendMessage)
  RED: ChatComposer.test.tsx (cases: Enter sends + clears, Shift+Enter newline, IME guard, idempotency status==='thinking', emoji stubs no disabled, Cmd+K focus via id)
  GREEN: ChatComposer.tsx
  Depends: T-2 (consume useChatStore.sendMessage)

T-5 — ValeriaChat organism + ChatMessages branch logic
  RED: ValeriaChat.test.tsx (cases: render con messages mock 6 items, empty state cuando messages.length===0, role variants render correcto, auto-scroll sentinel useEffect, aria-live polite)
  GREEN: ValeriaChat.tsx + ChatMessages.tsx
  Depends: T-2 + T-3 + T-4

T-6 — Integration: MODIFY ValeriaSidebar + cleanup + arch tests extend
  RED: extend test-no-cross-brand-shell-mirror.test.ts + NEW test-agent-catalog-ssot.test.ts (RED inicial sin componentes)
  GREEN: ValeriaSidebar.tsx MODIFY (2 line diff) + DELETE ValeriaChatSlot{,.test}.tsx + extend test_server_first.test.ts allowlist + NEW test-agent-catalog-ssot.test.ts
  Depends: T-5

T-7 — Playwright POM ValeriaChatPage + fixtures (chatStoreSeed + chatStoreEmpty)
  RED: skeleton spec files importan POM/fixtures (TS check)
  GREEN: e2e/shell-organism/poms/valeria-chat-page.pom.ts + e2e/shell-organism/fixtures/chat-store-seed.fixture.ts
  Depends: T-6

T-8 — Playwright behavior specs (4 functional scenarios)
  RED: valeria-chat-{happy,send,keys,xss}.spec.ts (todos rojo inicial sin componente real corriendo)
  GREEN: pasa post T-6 deploy local
  Depends: T-7

T-9 — Playwright visual + a11y + i18n
  RED: valeria-chat-{empty,a11y,i18n,visual}.spec.ts
  GREEN: --update-snapshots iter 1 post Chris ratifica side-by-side mockup HTML
  Depends: T-8

DAG visualization:
  T-1 ─┐
       │
  T-2 ─┼─> T-3 (átomos+moléculas low-level) ─┐
                                              ├─> T-5 (ValeriaChat + ChatMessages) ─> T-6 (Integration MODIFY) ─> T-7 (POM+fixtures) ─> T-8 (4 behavior specs) ─> T-9 (visual + a11y + i18n)
  T-2 ────> T-4 (ChatComposer) ──────────────┘

T-3 + T-4 parallelizable (no comparten files).
T-5 sequential post T-3 + T-4.
T-6 sequential post T-5.
T-7..T-9 sequential post T-6.
```

### § 2.10 — Server vs Client decision tree (FSD-Lite)

| Component | Type | Justificación |
|---|---|---|
| `ValeriaChat` | 'use client' | useChatStore selector + children consumers |
| `ChatHeader` | 'use client' | useChatStore.activeAgent selector + useState imgError |
| `ChatMessages` | 'use client' | useChatStore.messages selector + useEffect scroll sentinel |
| `ChatComposer` | 'use client' | useState localValue + onKeyDown + useRef textarea + onClick send |
| `MessageBubble` | 'use client' | Pure presentation pero dentro del árbol Client — mantener boundary unified (consistencia con F1-S5 patrón) |
| `TypingIndicator` | 'use client' | CSS animation only pero dentro del árbol Client |
| `DelegateMarker` | 'use client' | Pure presentation pero dentro del árbol Client |
| `_mock-messages.ts` | n/a (data) | Pure module export |
| `agent-catalog.ts` | n/a (data) | Pure module export |
| `chat-store.ts` | n/a (zustand) | Solo se usa dentro client components |
| `ValeriaSidebar` (MODIFY) | 'use client' | Heredado F1-S5 — NO change |

### § 2.11 — Skill decisions referenced

- **`frontend-expert`**: FSD-Lite shared/shell-organism correct para chrome cross-feature; agent-catalog en `lib/` correct (cross-feature shared SSoT); chat-store en `stores/` correct (zustand global); tests colocated; Server-First-ish with full 'use client' boundary en chat tree por consistencia; runtime quality checklist verificado (useEffect deps complete, no stale closures, no race en setTimeout cleanup).
- **`tessl__react-patterns`**: React 19 IME composition guard via `e.isComposing` en ChatComposer (consistency con F1-S5); useEffect cleanup setTimeout en chat-store sendMessage NO requerido (zustand state set in callback es safe — pero arch best-practice: capturar ref `setTimeoutRef` y limpiar on store reset — implementación opcional, F1-S6 deja simple por brevedad).
- **`tessl__shadcn-ui`**: REUSE Textarea + Button + Badge primitives F1-S0 cementados — sin upgrade. Textarea con `rows=1` + manual auto-resize via useEffect.
- **`tessl__tailwind`**: tokens semánticos ONLY; `--agent-mateo-soft` agregado (single gap del catalog 6 agentes). `bg-agent-{slug}` resolved via Tailwind config existing entries — auditor verifica safelist o explicit usage.
- **`playwright-expert`**: POM en `e2e/shell-organism/poms/` (path canon F1-S6 ratificado spec § 13); fixtures en `e2e/shell-organism/fixtures/`; addInitScript determinismo para chat-store seed (MOCK_MESSAGES) vs empty ([]); visual goldens 4 snapshots (light+dark × populated+empty); axe ruleset wcag2aa.

## § 3 — Tests architecture

### § 3.1 — Vitest unit suite (T-1..T-6)

Cobertura por archivo (target):

| Test file | Cobertura sujeto | Cases |
|---|---|---|
| `lib/__tests__/agent-catalog.test.ts` | catalog SSoT | 6 cases: 6 agentes presentes en AGENT_CATALOG · DEFAULT_CHAT_AGENT='valeria' · shape completo per agente (slug/name/role/colorToken/colorSoftToken/hex/thumbnail/transparent/initial) · AGENT_SLUGS array contiene 6 entries · hex literal field present (metadata) · paths thumbnails coherentes con `/agents/{slug}/thumbnail.png` |
| `stores/__tests__/chat-store.test.ts` | chat-store zustand | 10 cases: initial state messages=MOCK_MESSAGES + activeAgent='valeria' + status='idle' · sendMessage flow user push + thinking push + status=thinking · setTimeout 800ms removes thinking + adds bot · MOCK_RESPONSES rotativo determinista (count % len) · clearMessages resets to [] + status='idle' · setActiveAgent updates active · idempotency status==='thinking' bloquea segundo send · empty string send no-op · whitespace-only trimmed → no-op · time format HH:MM via toLocaleTimeString es-PE |
| `ChatHeader.test.tsx` | molécula header | 7 cases: render avatar img con thumbnail valeria · onError fallback "V" initial letter · status dot bg-vitalia-success aria-hidden · name "Valeria" + status text "En línea · Tu secretaria virtual" · Mode Pill "🤖 Modo agente" data-testid="chat-mode-pill" · custom agent prop renders catalog entry · aria-hidden en avatar |
| `MessageBubble.test.tsx` | molécula bubble | 8 cases: bot bubble bg-card border-border align-start · user bubble bg-agent-valeria text-white align-end · timestamp footer Valeria · 09:01 (bot) y 09:02 only (user) · whitespace-pre-wrap preserva \n · XSS payload `<script>` renders como text-children (NO ejecutado) · data-testid="msg-bubble" + data-role attr · max-w-80% applied · Camila via Valeria footer "Camila (via Valeria) · HH:MM" |
| `ChatComposer.test.tsx` | molécula composer | 9 cases: Enter (no Shift) sends + clears localValue · Shift+Enter inserts newline preserved · isComposing skip handler · idempotency status==='thinking' ignora Enter · click Enviar dispatcha sendMessage · 3 emoji stubs render con title "próximamente" y aria-label · sr-only label for valeria-composer · Textarea id="valeria-composer" matches Cmd+K target · empty string Enter no-op |
| `ValeriaChat.test.tsx` | organism root + ChatMessages | 12 cases: render section role="region" aria-label data-testid · 6 mensajes mock orden correcto · empty state render cuando messages=[] · empty state heading "Empieza una conversación" + subtexto verbatim spec § 6 · auto-scroll sentinel useEffect dispara scrollIntoView · aria-live="polite" en messages container · TypingIndicator render cuando role='thinking' · DelegateMarker render cuando role='delegate' · MessageBubble bot/user variants · ChatHeader + ChatMessages + ChatComposer todos presentes · grid grid-rows-[auto_1fr_auto] overflow-hidden · chat-store integration sendMessage flow E2E (user + thinking + 800ms bot) |
| `__tests__/architecture/test-agent-catalog-ssot.test.ts` | arch invariant | 4 cases: grep cross shell-organism components — no hardcoded agent name string (`'Valeria'|'Camila'|...`) fuera de catalog + MOCK_MESSAGES (allowlist) · no hex literal cross-component (excepto agent-catalog.ts hex field) · no hardcoded thumbnail path string fuera de catalog · MOCK_MESSAGES allowlist exception documented |

**Mock pattern (zustand chat-store):**

```ts
import { useChatStore } from '@/stores/chat-store'
import { MOCK_MESSAGES } from '@/components/shared/shell-organism/_mock-messages'

beforeEach(() => {
  useChatStore.setState({
    messages: [...MOCK_MESSAGES],
    activeAgent: 'valeria',
    status: 'idle',
  })
})

afterEach(() => {
  // No persist storage to clear (chat-store sin persist middleware)
  vi.useRealTimers()
})

// Time-mocked tests:
test('sendMessage 800ms thinking → bot reply', () => {
  vi.useFakeTimers()
  useChatStore.setState({ messages: [], status: 'idle' })
  useChatStore.getState().sendMessage('test')
  expect(useChatStore.getState().status).toBe('thinking')
  vi.advanceTimersByTime(800)
  expect(useChatStore.getState().status).toBe('idle')
  expect(useChatStore.getState().messages.filter(m => m.role === 'bot')).toHaveLength(1)
})
```

### § 3.2 — Playwright E2E suite (T-7..T-9)

POM `vitalia/frontend/e2e/shell-organism/poms/valeria-chat-page.pom.ts` métodos:

- `goto()` — navigate to `/test-stack/shell-layout` (public route, no Clerk auth)
- `seedChatStore(messages: ChatMessage[])` — addInitScript pre-nav setting `window.__chatStoreSeed__` + chat-store reads on mount
- `seedChatStoreEmpty()` — convenience: seed con []
- `getMessage(index: number)` — Locator for nth `[data-testid=msg-bubble]`
- `getDelegateMarker()` — Locator for `[data-testid=msg-delegate]`
- `getThinkingIndicator()` — Locator for `[data-testid=msg-thinking]`
- `getChatHeader()` — Locator for `[data-testid=chat-header]`
- `getModePill()` — Locator for `[data-testid=chat-mode-pill]`
- `getComposer()` — Locator for `[data-testid=composer-input]`
- `getSendButton()` — Locator for `[data-testid=composer-send]`
- `sendMessage(text: string)` — focus composer + type + press Enter
- `getActiveAgent()` — page.evaluate window.useChatStore.getState().activeAgent
- `clearMessages()` — page.evaluate window.useChatStore.getState().clearMessages()
- `getEmptyState()` — Locator for empty state heading "Empieza una conversación"

Fixtures:

- `e2e/shell-organism/fixtures/chat-store-seed.fixture.ts` — `chatStoreSeed` (6 messages) + `chatStoreEmpty` ([]) helpers usando `page.addInitScript` para hidratar zustand store antes de mount
- `e2e/fixtures/shell-theme.fixture.ts` (REUSE F1-S5) — para light/dark toggle
- `e2e/fixtures/clerk-auth.fixture.ts` (REUSE F1-S3) — public route bypassa auth

Specs mapping 1:1 con Scenarios:

- `valeria-chat-happy.spec.ts` ← SC-1 (render 6 messages)
- `valeria-chat-send.spec.ts` ← SC-2 (composer interactivo)
- `valeria-chat-keys.spec.ts` ← SC-3 (Shift+Enter newline)
- `valeria-chat-xss.spec.ts` ← SC-4 (XSS guard + dialog event listener verify no alert)
- `valeria-chat-empty.spec.ts` ← SC-5 (empty state) — incluye visual snapshot
- `valeria-chat-a11y.spec.ts` ← SC-6 (axe wcag2aa + keyboard Tab order)
- `valeria-chat-i18n.spec.ts` ← SC-7 (regex voseo cero matches + Spanish neutro)
- `valeria-chat-visual.spec.ts` ← Variants visual (4 snapshots):
  - `valeria-chat-populated-light-1280x800.png`
  - `valeria-chat-populated-dark-1280x800.png`
  - `valeria-chat-empty-light-1280x800.png` (overlapping con valeria-chat-empty.spec.ts visual_state grader)
  - `valeria-chat-empty-dark-1280x800.png`

Total: 4 PNG snapshots desktop 1280x800. NO mobile drawer snapshot dedicated F1-S6 — mobile drawer cubierto heredado F1-S5 (chat slot dentro del drawer rendered by ValeriaSidebar — F1-S5 ya lo cubrió genericamente).

### § 3.3 — Architectural fitness

**Tests existentes que extend (allowlists shrink only):**

1. `test-no-cross-brand-shell-mirror.test.ts` — agregar 9 nombres NEW: `ValeriaChat`, `ChatHeader`, `ChatMessages`, `ChatComposer`, `MessageBubble`, `TypingIndicator`, `DelegateMarker`, `useChatStore`, `AGENT_CATALOG`. Cada uno cero matches en nicolify/comunify/lupulo.
2. `test_server_first.test.ts` — extender allowlist `'use client'` files con ValeriaChat + ChatHeader + ChatMessages + ChatComposer + MessageBubble + TypingIndicator + DelegateMarker (justificación inline en commit).

**Tests NEW (1 archivo):**

3. `test-agent-catalog-ssot.test.ts` — invariant: NO hardcoded agent name/color/thumbnail string fuera de `agent-catalog.ts`. Implementación referencia:

```ts
import { describe, it, expect } from 'vitest'
import { glob } from 'glob'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const ROOT = path.resolve(__dirname, '../../..')

// Allowlist: archivos que pueden mencionar agent names hardcoded (catalog SSoT + mock fixtures)
const ALLOWLIST = [
  'lib/agent-catalog.ts',
  'lib/__tests__/agent-catalog.test.ts',
  'components/shared/shell-organism/_mock-messages.ts',
  // tests files allowed to use literal strings for assertions
]

describe('arch: agent-catalog SSoT invariant', () => {
  it('no hardcoded agent name strings outside agent-catalog + _mock-messages', async () => {
    const files = await glob('src/components/shared/shell-organism/**/*.{ts,tsx}', { cwd: ROOT })
    const violations: Array<{ file: string; matches: string[] }> = []
    const pattern = /["']\b(Lisa|Valeria|Adrián|Lucas|Camila|Mateo)\b["']/g

    for (const file of files) {
      const rel = file.replace(/^src\//, '')
      if (ALLOWLIST.some(allow => rel.includes(allow))) continue
      if (rel.endsWith('.test.tsx') || rel.endsWith('.test.ts')) continue  // tests can use literal strings

      const content = readFileSync(path.join(ROOT, file), 'utf-8')
      const matches = content.match(pattern)
      if (matches && matches.length > 0) {
        violations.push({ file: rel, matches })
      }
    }
    expect(violations).toEqual([])
  })

  it('no hardcoded agent thumbnail path strings outside catalog', async () => {
    // similar pattern: grep /'\/agents\//
  })

  it('no hex literal cross-component (excepto agent-catalog.ts)', async () => {
    // similar pattern: hex regex against components but exclude catalog
  })
})
```

## § 4 — Cross-cutting concerns (resolution)

| Concern | Resolution |
|---|---|
| **Tenant isolation** | N/A — chrome UI sin queries BE. URL `[tenantId]` ya propagada por F1-S4 ShellOrganismLayout. Middleware Clerk gates upstream. |
| **Currency / monetary** | N/A — no monetary fields. |
| **PII / HIPAA-lite** | **scope: not_applicable** — declared en checkpoint frontmatter. Mock data 6 mensajes contiene nombres ficticios del mockup ratificado por Chris ("Marina Pérez", "Dr. Juan García") — no PHI real (no diagnósticos clínicos, no dosis, no labs results, no DNI). Verbatim del mockup HTML que Chris ratificó. Test i18n grep validara no patterns medical específicos (diagnosticos enumerados, dosis pattern). |
| **Spanish neutro LatAm** | 30+ strings ratificados spec § 6. Pre-commit hook (raíz) verifica voseo. Arch test `test-vitalia-ui-strings-no-voseo.test.ts` se extiende auto a NEW components (grep glossary regex). i18n-spanish-neutro.spec.ts E2E grader verifica runtime DOM strings. Spec § 6 incluye correcciones explícitas (e.g., "Empezá" → "Empieza", "Preguntale" → "Pregúntale" tilde). |
| **Native-first dev** | Lint/tests/playwright NATIVE Linux host. NUNCA `docker exec ruff/pytest/tsc/vitest`. Stack docker compose para runtime sólo (`make dev-vitalia`). |
| **A11y mandatory** | aria-label + aria-live="polite" + sr-only label composer + axe wcag2aa enforcement. Contrast ratios validados (text-white sobre bg-agent-valeria HSL `287 53% 37%` ≥ 6:1 light; ≥ 4.5:1 dark con HSL `287 53% 50%`). Reduced motion respect (typing dots con `motion-reduce:animate-none` opcional — agregar en CSS rule). |
| **PWA / responsive** | Heredado F1-S5: `<md` drawer · `md+` desktop. Visual goldens cubren 1280x800 (4 snapshots). Mobile drawer del chat heredado del ValeriaSidebar wrapper (F1-S5 ya cubrió). |
| **XSS guard** | React text-children auto-escape. NUNCA `dangerouslySetInnerHTML` en NEW code. Auditor grep verifica. E2E spec dispara `<script>alert('xss')</script>` payload + listener dialog event no fires. |

## § 5 — Resize integration impact

`ValeriaSidebar` consume `valeriaState` para grid columns. F1-S6 NO modifica `MIN_VALERIA_PX` ni ResizeObserver logic — solo swap del child `<ValeriaChatSlot />` → `<ValeriaChat />`. Chat ocupa el slot derecho del grid 2-col (rail/history) cuando expandido. Sin impacto en resize logic heredado F1-S5.

## § 6 — Telemetría / observability

N/A F1-S6 — mock-only chrome. F2-S* (camila-voz, valeria-voz) introducirá events analytics cuando wire WebSocket real (out-of-scope F1-S6).

## § 7 — Brand voice / sales_agent integration

F1-S6 NO consume `personality_profiles.system_instruction` (mock chrome, no agent real). F2-S* introducirán compilador voz tenant cuando wire WebSocket sales_agent. F1-S6 deja placeholders visuales y los hooks (chat-store.sendMessage shape) para ese wire. `MOCK_MESSAGES` + `MOCK_RESPONSES` son hardcoded Spanish neutro per D6 spec — excepción documentada porque mock chrome NO pasa por compilador voz tenant.

**Promotion candidate flag**: ValeriaChat + agent-catalog + chat-store son LIFT CANDIDATES cuando ≥2 brands lo necesiten → `/pm-luana` promotion proposal para `core/@luana/shell-chat-organism/` y `core/@luana/agent-catalog/`. Por ahora primera ocurrencia Vitalia, mantenemos brand-local. Auditor flag inline en file headers.

## § 8 — Cross-stack handoff

FE only. ZERO BE/AGENTIC dependencies. Tenant isolation upstream Clerk middleware (preserved).

## § 9 — Open questions for PM

Ninguna. Decisiones D1-D9 ratificadas spec § 0 + D batch_3 implícito (Mateo en catalog sin flag exclusión, MessageBubble Camila via Valeria estilo neutral). Mockup visual ratificado iter 3. Autonomous build requested.

## § 10 — Anti-creep boundary

When `state: done` and merged:

- **F2-S* (camila-voz / valeria-voz / sales_agent wire)** reemplazan `chat-store.sendMessage` mock con WebSocket real + sales_agent backend. ChatHeader/MessageBubble/ChatComposer **PRESERVED** intactos (solo body de `sendMessage` muta). API expuesta del store es contract estable.
- **Sub-story futura "AgentSwitcher dropdown en ChatHeader"** consumirá `setActiveAgent` ya expuesto en F1-S6. Agregar dropdown en ChatHeader, sin re-trabajo del componente.
- Si surge necesidad de tocar componentes shell ya existentes (ValeriaSidebar más allá del slot swap, ShellOrganismLayoutClient resize, ShellModeToggle, AppPanelSlot, TopBarGlobal hamburger) → STOP, escalar `/pm-vitalia` nueva story.
- **`shell-store.ts` HARD READ-ONLY** — heredado F1-S5 invariant. F1-S6 mantiene separación chat-store vs shell-store (no merge).

## § 11 — Research notes (DATE-AWARE)

- **`tessl__shadcn-ui` Textarea primitive** — accessed 2026-05-24 via canonical path; Textarea = Radix slot wrapper, `rows` prop default 3 (override a `1` para auto-resize manual via useEffect). Cementado F1-S0 versión unchanged.
- **`tessl__react-patterns` IME composition + useRef textarea pattern** — accessed 2026-05-24; `KeyboardEvent.isComposing` standard property (W3C UI Events spec). Auto-resize textarea via `style.height = 'auto'` + `style.height = scrollHeight + 'px'` con `max-h-[100px]` cap es pattern canónico React 19 + Next.js 16 — verified via WebSearch "textarea auto-resize react 2026 best practice" cross-validated en docs canonicos.
- **Zustand 5 sin persist middleware** — accessed 2026-05-24 docs.pmnd.rs/zustand; default behavior `create()` sin persist es ephemeral state — correcto para F1-S6 chat ephemeral. Re-hidrata MOCK_MESSAGES on mount sin localStorage.
- **`setTimeout` cleanup en zustand action** — researched 2026-05-24; zustand actions retain closure on `set/get` — setTimeout que dispara `set()` después del unmount es safe (zustand state es process-level, no component-bound). NO requiere cleanup explicit, pero best-practice doc recomienda capturar ref si store puede re-mount/test. F1-S6 omite cleanup (simple), arch best-practice flagged si causa flake.
- **React 19 XSS protection** — accessed 2026-05-24 react.dev docs; text-children auto-escape (standard since React legacy). `dangerouslySetInnerHTML` es opt-in explicit. Auditor verifica grep cero matches en NEW code.
- **Tailwind 4 dynamic class names** — accessed 2026-05-24 tailwindcss.com/docs/content-configuration; dynamic class names (template literal `bg-agent-${slug}`) NO funcionan con JIT engine — Tailwind safelist o explicit class usage requerido. Decision F1-S6: explicit class via switch/map en componentes (no template literal interpolation).
- **Anthropic prompt caching** — N/A (no LLM calls F1-S6).
- **Knowledge cutoff disclosure**: Opus 4.7 cutoff = Jan 2026; researched live on 2026-05-24 via WebSearch + canonical docs. F1-S5 patterns reused verbatim (1 day old). Tailwind 4 + Next.js 16 + React 19 + Shadcn UI versions cementadas F1-S0 (~30 days old) unchanged.

