---
story_id: vitalia-fase1-valeria-chat-skeleton
outcome: vitalia-mvp-ui-foundation
phase: fase-1
type: ui-story
agent_owner: shell
module: shell-organism
capability: shell.valeria-chat
state: done
workflow_phase: MERGED_ARCHIVED
last_modified: 2026-05-25T02:45:00Z
pm_merge_completed_at: 2026-05-25T02:45:00Z
pm_merge_owner: /pm-vitalia
dev_team_started_at: 2026-05-25T00:00:00Z
dev_team_completed_at: 2026-05-25T02:35:00Z
dev_team_owner: claude-sonnet (builder-frontend, FE no-agentic — qwen-opencode fallback not available)
auditor_started_at: 2026-05-25T02:36:00Z
auditor_completed_at: 2026-05-25T02:40:00Z
auditor_verdict: APPROVED
audit_iterations: 1
self_fix_iter: 1
self_fix_summary: "F-1 unused eslint-disable directive removed (chat-store.test.ts:278) — whitelist cat #1 lint auto-fix"
ratified_by_chris: true
ratified_at: 2026-05-24T23:40:00Z
ratified_visual_by_chris: true
ratified_visual_at: 2026-05-24T23:40:00Z
ratified_visual_iter: 3
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-fase1-valeria-chat-skeleton/mockups/valeria-chat-sample.html
po_ux_version: 3
architect_iter: 1
architect_run_on: 2026-05-24T23:55:00Z
last_artifact: CHECKPOINTS.md
parallel_safe: true
priority: high
estimated_dev_days: 1-2
dependencies:
  hard: [vitalia-fase1-valeria-rail-history]
  soft: []
blocks_hard: []
reuse_map_summary: "NEW estructura chat panel · mock data 5 mensajes · sin sales_agent wiring real (Fase 2 wire)"
spawned_at: 2026-05-22
next_action: "story archived (post-merge) — see vitalia/docs/archive/2026/stories/vitalia-fase1-valeria-chat-skeleton/ for inmutable snapshot. Capability vitalia.shell-organism.valeria-chat live."

# Schema v2 migration (cement 2026-05-27)
release: F1   # release ID · ver releases/
cap_target: valeria-chat   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F1-S6 vitalia-fase1-valeria-chat-skeleton — checkpoint

## Goal

`ValeriaChat` organismo: panel chat dentro del ValeriaSidebar. Estructura completa (header + messages + composer) con mock data 5 mensajes ejemplo (incluyendo delegación a Camila + thinking dots animados). Composer NO envía a backend todavía (Fase 2 wire WebSocket sales_agent), solo agrega mensaje localmente al state.

## Anti-objetivos

- NO wire WebSocket real (Fase 2)
- NO LLM API calls (Fase 2)
- NO persist conversations a DB (Fase 2)
- NO implementar `Cmd+K` focus (ya en F1-S5)

## Scope verbatim

### § 1 — `ValeriaChat` organismo

`vitalia/frontend/src/components/shared/shell-organism/ValeriaChat.tsx`:

```tsx
'use client'
import { ChatHeader } from './ChatHeader'
import { ChatMessages } from './ChatMessages'
import { ChatComposer } from './ChatComposer'
import { useChatStore } from '@/stores/chat-store'

export function ValeriaChat() {
  return (
    <section
      role="region"
      aria-label="Chat con Valeria"
      data-testid="valeria-chat"
      className="grid grid-rows-[auto_1fr_auto] overflow-hidden"
    >
      <ChatHeader agent="valeria" status="online" mode="agent" />
      <ChatMessages />
      <ChatComposer />
    </section>
  )
}
```

### § 2 — `ChatHeader` molécula

Avatar Valeria (PNG `/agents/valeria/thumbnail.png` con fallback "V") + Name "Valeria" + Status "En línea · Tu secretaria virtual" + Pill "🤖 Modo agente".

### § 3 — `ChatMessages` molécula

Lista de mensajes scrollable con `aria-live="polite"`. Tipos:
- `bot` → MessageBubble bg-card border-border
- `user` → MessageBubble bg-agent-valeria text-white align-end
- `delegate` → DelegateMarker italic centered
- `thinking` → TypingIndicator dots animados

Mock 5 mensajes hardcoded `_mock-messages.ts`:

```ts
export const MOCK_MESSAGES = [
  { id: '1', role: 'bot', content: '¡Buenos días! Tienes 8 turnos hoy y 3 pacientes esperando confirmar mañana. ¿Por dónde empezamos?', time: '09:01' },
  { id: '2', role: 'user', content: '¿Cómo están las reseñas Google esta semana?', time: '09:02' },
  { id: '3', role: 'delegate', fromAgent: 'valeria', toAgent: 'camila' },
  { id: '4', role: 'bot', content: 'Esta semana ingresaron +3 reseñas Google (2× ⭐⭐⭐⭐⭐ y 1× ⭐⭐⭐⭐). El score subió de 4.6 a 4.7. Hay 1 reseña destacable de Marina Pérez sobre Dr. Juan García que sugiero pinear en landing. ¿La abro?', time: '09:02' },
  { id: '5', role: 'user', content: 'Sí, abrila', time: '09:03' },
  { id: '6', role: 'thinking', agent: 'camila', text: 'Camila está abriendo Voz del paciente' },
]
```

**Nota Spanish neutro:** mockup HTML usa "Tienes" (tuteo) en el mensaje bot. **DECISIÓN:** los mensajes de Valeria respetan voz tenant (excepción `sales-agent-brand-voice.md`). Tenant LatAm neutro default cumple tuteo. Documentar en /po-ux refining si tenant Argentina opta por voseo.

### § 4 — `ChatComposer` molécula

Textarea Shadcn con auto-resize (max 100px) + IconButtons (📎 adjuntar · 🎙️ voz · ⚡ comandos) + Botón "Enviar" variant default bg-agent-valeria.

Enter (sin Shift) envía. Shift+Enter newline. ID `valeria-composer` para Cmd+K focus.

### § 5 — `chatStore` zustand

`vitalia/frontend/src/stores/chat-store.ts`:

```ts
interface ChatStore {
  messages: ChatMessage[]
  status: 'idle' | 'thinking' | 'streaming'
  sendMessage: (content: string) => void  // mock: agrega user message + simula bot response
  clearMessages: () => void
}
```

Mock `sendMessage`: agrega user message, setTimeout 800ms thinking, agrega bot response random.

### § 6 — `MessageBubble` molécula

```tsx
interface Props {
  role: 'bot' | 'user'
  content: string
  time?: string
}
```

Styles per role (Design Contract § 3.1).

### § 7 — `TypingIndicator` átomo

3 dots animados con keyframes Tailwind `animate-pulse` o custom.

### § 8 — `DelegateMarker` molécula

Centered italic "→ delegando a 🟦 Camila (Mantener)".

### § 9 — Replace ValeriaChatSlot in ValeriaSidebar

Update F1-S5 ValeriaSidebar para usar `<ValeriaChat />` real.

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | ChatHeader visible con avatar Valeria + status + mode pill |
| AC-2 | Mensajes 6 renderizados en orden correcto |
| AC-3 | Bot bubbles bg-card · user bubbles bg-agent-valeria |
| AC-4 | DelegateMarker italic centered |
| AC-5 | TypingIndicator dots animados |
| AC-6 | Composer textarea funciona · Enter envía · Shift+Enter newline |
| AC-7 | Click "Enviar" agrega mensaje al store · render aparece |
| AC-8 | aria-live="polite" en messages container |
| AC-9 | Avatar fallback "V" si PNG load falla (onError) |
| AC-10 | Visual golden chat con 6 mensajes mock |
| AC-11 | Vitest unit ChatHeader, MessageBubble, ChatComposer |
| AC-12 | Spanish neutro respetado en mensajes default (tenant LatAm) |

## Gherkin scenarios

### Scenario 1 — happy render mock

**Given:** Shell carga con valeriaState `rail`

**When:** Página renderiza

**Then:**
- ChatHeader visible
- 6 mensajes mock rendered en orden
- Composer al fondo

### Scenario 2 — send mock message

**Given:** Composer focused, theme cualquiera

**When:** Type "test message" + press Enter

**Then:**
- Mensaje user "test message" aparece al fondo
- Composer queda vacío
- Despues de 800ms: thinking dots aparecen
- Despues de ~2s: bot response random aparece (mock)

### Scenario 3 — Cmd+K focus

**Given:** Focus en cualquier elemento NO input

**When:** Press Cmd/Ctrl+K

**Then:**
- Focus salta a composer textarea
- (handler implementado en F1-S5 useKeyboardShortcuts)

### Scenario 4 — avatar fallback

**Given:** PNG `/agents/valeria/thumbnail.png` 404

**When:** Página carga

**Then:**
- Avatar muestra fallback "V" en círculo bg-agent-valeria
- No layout shift

### Scenario 5 — visual golden parity mockup

**Given:** Chat rendered con 6 mensajes mock

**When:** Playwright `toHaveScreenshot()`

**Then:**
- Pixel match con mockup HTML chat section

## Deliverables

| File | Acción |
|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaChat.tsx` | NEW |
| `vitalia/frontend/src/components/shared/shell-organism/ChatHeader.tsx` | NEW |
| `vitalia/frontend/src/components/shared/shell-organism/ChatMessages.tsx` | NEW |
| `vitalia/frontend/src/components/shared/shell-organism/ChatComposer.tsx` | NEW |
| `vitalia/frontend/src/components/shared/shell-organism/MessageBubble.tsx` | NEW |
| `vitalia/frontend/src/components/shared/shell-organism/TypingIndicator.tsx` | NEW |
| `vitalia/frontend/src/components/shared/shell-organism/DelegateMarker.tsx` | NEW |
| `vitalia/frontend/src/components/shared/shell-organism/_mock-messages.ts` | NEW |
| `vitalia/frontend/src/stores/chat-store.ts` | NEW |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.tsx` | MODIFY (replace ChatSlot) |
| `vitalia/frontend/e2e/shell-organism/valeria-chat.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/shell/valeria-chat-{light,dark}.png` | NEW |

## Próximo paso post-done

Valeria panel completo. F1-S7 ribbon-6-tabs arranca (independiente).
