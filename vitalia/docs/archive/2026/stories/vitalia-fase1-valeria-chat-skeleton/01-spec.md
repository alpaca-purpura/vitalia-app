---
story_id: vitalia-fase1-valeria-chat-skeleton
brand: vitalia
type: ui-story
state: refined
outcome: vitalia-mvp-ui-foundation
phase: fase-1
module: shell-organism
capability: shell.valeria-chat
agent_owner: shell
spawned_at: 2026-05-22
last_modified: 2026-05-24
po_ux_version: 3
ratified_by_chris: true
ratified_at: 2026-05-24T23:40:00Z
ratified_visual_by_chris: true
ratified_visual_at: 2026-05-24T23:40:00Z
ratified_visual_iter: 3
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-fase1-valeria-chat-skeleton/mockups/valeria-chat-sample.html
hipaa_lite_scope: not_applicable                  # shell chrome UI · mock data sin PHI
parallel_safe: true
priority: high
estimated_dev_days: 1-2
dependencies:
  hard: [vitalia-fase1-valeria-rail-history]      # done 2026-05-24 (archived)
  soft: []
blocks_hard: []
reuse_map_summary: "NEW estructura chat panel (ChatHeader EVOLUCIONA F1-S5 con Mode Pill · ChatMessages + ChatComposer + 4 sub-componentes NEW) · mock data 6 mensajes hardcoded · NO wire WebSocket real (Fase 2) · NO LLM calls"
next_action: "/architect vitalia vitalia-fase1-valeria-chat-skeleton → produce ready package (03-arch + 04-validators + 05-guidelines + 06-tickets) → state refined→ready"
ratification_decisions_implicit_batch_3:
  - "Mateo permanece en AGENT_CATALOG sin flag excludedFromChatSwitcher (selector futuro decide ocultarlo per UX necesidad)"
  - "MessageBubble bot Camila via Valeria mantiene estilo neutral (bg-card border-border) con identificación via footer pill+thumbnail (no border-l agent-camila accent en F1-S6, dejar para futuro si UX lo pide)"
---

# F1-S6 vitalia-fase1-valeria-chat-skeleton — 01-spec.md unificado

> **/po-ux fusión spec + UX/UI** · paradigm v4.1 · brand vitalia · type ui-story
> Owner spec: `/po-ux` · Pre-arch gate visual: `shell-mockup-per-component.md`

---

## § 0 — Context

### Outcome + módulo + insertion point

- **Outcome:** `vitalia-mvp-ui-foundation` (Fase 1 shell esqueleto)
- **Módulo:** `shell-organism` (UI chrome, brand-local, NO cross-brand, NO PHI)
- **Insertion point:** reemplaza el body + composer del `ValeriaChatSlot` placeholder (F1-S5) dentro de `ValeriaSidebar`. Se preserva el `ChatHeader` real del slot pero se le **agrega Mode Pill** "🤖 Modo agente" y el status pasa de `"En línea"` → `"En línea · Tu secretaria virtual"`.
- **Predecesores done:** F1-S0..S5 (stack stability → tokens → topbar → tenant-switcher → shell-layout 50/50 → valeria-rail-history).
- **Sucesor inmediato:** F1-S7 ribbon-6-tabs (independiente, no bloqueado por F1-S6).

### Goal (1-liner)

`ValeriaChat` organismo: panel chat dentro del slot derecho de `ValeriaSidebar`. Estructura completa **ChatHeader + ChatMessages + ChatComposer** con mock data de 6 mensajes (incluye bot, user, delegate marker a Camila, thinking dots animados). Composer NO envía a backend real; al apretar Enter agrega user-message al store local, simula `thinking` 800ms, agrega un bot-response canned. F1-S6 entrega el "look & feel" final del chat para que F2-S* pueda conectar WebSocket sales_agent sin re-diseño visual.

### Out-of-scope explícito (anti-creep)

- ❌ NO WebSocket real / SSE / streaming (Fase 2)
- ❌ NO LLM API calls (Fase 2)
- ❌ NO persistir conversaciones a DB / API `/api/conversations` (Fase 2)
- ❌ NO implementar `Cmd+K` focus handler (ya en F1-S5 `useKeyboardShortcuts`)
- ❌ NO modificar `shell-store.ts` schema (`valeriaState`, `shellMode` ya cementados F1-S3/S4)
- ❌ NO botones composer 📎/🎙️/⚡ funcionales — visual stubs con `title="próximamente"` (cobertura visual del MVP sin lógica)
- ❌ NO history items mock-relacionados (cada mensaje es standalone; F2 wire conv-id)
- ❌ NO tocar route group `(dashboard)/` legacy

### Pre-conditions cementadas (heredadas)

- `ValeriaChatSlot` F1-S5 vive en `vitalia/frontend/src/components/shared/shell-organism/ValeriaChatSlot.tsx`. F1-S6 lo **reemplaza** con `<ValeriaChat />` (ver § 4 Componentes — `MODIFY` ValeriaSidebar.tsx import).
- Tokens activos: `--agent-valeria: 287 53% 37%`, `--agent-valeria-soft`, `--agent-camila: 244 84% 32%`, `--agent-camila-soft`, `--vitalia-success` (status dot).
- `shell-store.ts` exporta `useShellStore()` con `valeriaState` (consumido por sidebar, no por chat).

### Decisiones cardinales batch 1 (defaults de v1 — sujeto a ratificación Chris)

| ID | Decisión default | Justificación |
|---|---|---|
| **D1** | `ChatHeader` evoluciona del slot F1-S5: PRESERVA avatar + name "Valeria" + status dot · AGREGA Mode Pill "🤖 Modo agente" right-aligned · ACTUALIZA status text `"En línea"` → `"En línea · Tu secretaria virtual"` | Sin disruptión visual del shell. Pill identifica modo agéntico para futuras stories que agreguen modos adicionales (e.g. "📊 Modo informe" en F2-S*) |
| **D2** | Mock send: user msg → 800ms `thinking` → canned bot response del set `MOCK_RESPONSES` (4-5 variantes rotativas, no random — deterministic para Playwright golden) | Tests visuales necesitan determinismo. Variantes rotan por contador `messageCount % responses.length` (predecible) |
| **D3** | Composer adornments 📎/🎙️/⚡ como **stubs visuales** (`title="próximamente"`, no `disabled`, sin handlers funcionales). Cobertura visual completa del composer final | Evita "shell vacío" en demo. F2-S* implementa función real sin re-mockup |
| **D4** | `DelegateMarker` formato: italic centered con `"→ delegando a [pill Camila] (modo Mantener)"`. "Mantener" = uno de los 3 modos Camila (Mantener / Reactivar / Multiplicar — cementados en Design Contract § 3.2 toggle-pill 3-modos) | Da contexto del handoff sin requerir tooltip. Lenguaje narrativo coherente con voz Valeria |
| **D5** | `TypingIndicator` rico (no solo 3 dots): bubble con texto `"{Agent} está {acción}"` + 3 dots animados al final (e.g., `"Camila está abriendo Voz del paciente ..."`). Para Valeria thinking propio: `"Valeria está escribiendo ..."` | Indica progresión sustantiva del agente, no solo "wait". Pattern observable en Slack/Telegram. Mock: la acción se hardcodea en `MOCK_MESSAGES` |
| **D6** | Spanish neutro hardcoded en `MOCK_MESSAGES` (tuteo `"Tienes 8 turnos"`). F2-S11 (camila-voz) integrará compilador voz tenant para reemplazo en runtime; F1-S6 solo entrega esqueleto visual | Mock no es output real del agente, es chrome/demo. Excepción `sales-agent-brand-voice.md` aplica cuando el chat se conecta a sales_agent real (Fase 2) |
| **D7** | Mensajes muestran timestamp `HH:MM` debajo del bubble (no dentro), font `text-[10px] text-muted-foreground`. Agent name visible debajo de bubbles bot ("Valeria · 09:01" o "Camila (via Valeria) · 09:02") | Mockup ratificado F1-S5 muestra timestamps. Coherencia. Bot messages con name; user messages solo time (ya están en su lado) |
| **D8** | Visual gate único: `mockups/valeria-chat-sample.html` con **2 variantes en mismo file**: (1) chat con 6 mensajes (estado feliz), (2) empty state (0 mensajes — onboarding ilustración + CTA copy) | Empty state cubre v4.1 sub-categoría obligatoria. Un solo file mantiene preview unificado para Chris |
| **D9** ★ | `ChatHeader` y `MessageBubble` parametrizados por `agent: AgentSlug` desde día 1 (no hardcoded "Valeria"). Catálogo canónico de 6 agentes (Lisa, Valeria, Adrián, Lucas, Camila, Mateo) en `_agent-catalog.ts`. Cada agente tiene `slug`, `name`, `role`, `color` (CSS var token), `thumbnail` path. F1-S6 NO implementa selector switch agente — el chat default conversa con Valeria. Pero la arquitectura del componente queda preparada para una sub-story futura ("AgentSwitcher en ChatHeader") que agregue dropdown/selector sin re-trabajo del componente | Chris ratifica futuro UX donde user puede cambiar contraparte conversacional (Valeria default · cambia a Lucas para tarea growth · vuelve a Valeria). Diseñar el contract ahora es zero-cost; implementar selector en F1-S6 sería scope-creep |

---

## § 1 — Gherkin scenarios (v4.1 — 4 base + sub-categorías mandatory)

### Coverage map sub-categorías v4.1

| Sub-categoría | Aplica? | Scenario # | Justificación si no aplica |
|---|---|---|---|
| race_condition | NO | — | `not_applicable_reason: "mock store sin unique constraint, no DB writes"` |
| concurrent_users | NO | — | `not_applicable_reason: "store local zustand, no shared state cross-tab"` |
| network_failure | NO | — | `not_applicable_reason: "mock setTimeout, no fetch real (Fase 2 cubre)"` |
| empty_state | SÍ | S5 | `chatStore.messages.length === 0` (nueva conversación) |
| large_dataset | NO | — | `not_applicable_reason: "6 mensajes hardcoded, sin pagination MVP (Fase 2 wire conv historia)"` |
| accessibility | SÍ | S6 | WCAG AA axe pass + keyboard composer + screen reader `aria-live` |
| i18n | SÍ | S7 | Spanish neutro renderizado correcto + tildes/eñes preservadas |

### Scenario 1 — happy render mock messages

```yaml
type: happy
playwright_required: true
given: shell carga con valeriaState='full', chatStore.messages = MOCK_MESSAGES (6 items)
when: route /[tenantId]/(shell-organism)/lisa/marca renderiza
then:
  - ChatHeader visible con avatar Valeria + status "En línea · Tu secretaria virtual" + Mode Pill "🤖 Modo agente"
  - 6 mensajes renderizados en orden: bot, user, delegate, bot (Camila via Valeria), user, thinking
  - Bot bubbles usan bg-card + border-border + rounded-bl-sm (alineado start)
  - User bubbles usan bg-agent-valeria + text-white + rounded-br-sm (alineado end)
  - DelegateMarker italic centered con pill Camila + label "(modo Mantener)"
  - TypingIndicator bubble con texto "Camila está abriendo Voz del paciente" + 3 dots animados
  - Composer textarea visible al fondo con placeholder + 3 stubs (📎/🎙️/⚡) + Botón "Enviar" bg-agent-valeria
graders:
  - { type: e2e, path: "vitalia/frontend/e2e/shell-organism/valeria-chat-happy.spec.ts" }
  - { type: visual_state, screen: "valeria-chat-full", element: "[data-testid=valeria-chat]", expect: "matches mockup valeria-chat-sample.html (variante 6 mensajes)" }
```

### Scenario 2 — send mock message (composer interactivo)

```yaml
type: happy
playwright_required: true
given: chatStore.messages = MOCK_MESSAGES (6 items), composer focused
when: user escribe "¿Cuántos pacientes para mañana?" + presiona Enter
then:
  - Composer queda vacío
  - Aparece nuevo user bubble "¿Cuántos pacientes para mañana?" al fondo (mensaje #7)
  - Después de 800ms: aparece TypingIndicator "Valeria está escribiendo ..." (mensaje #8)
  - Después de ~600ms adicionales: TypingIndicator se reemplaza por bot bubble canned (`MOCK_RESPONSES[messageCount % responses.length]`)
  - chatStore.messages.length === 8 final
  - aria-live="polite" anuncia los nuevos mensajes
graders:
  - { type: e2e, path: "vitalia/frontend/e2e/shell-organism/valeria-chat-send.spec.ts" }
  - { type: state_check, target: zustand, query: "useChatStore.getState().messages.length", expect: 8 }
```

### Scenario 3 — Shift+Enter inserta newline

```yaml
type: edge
playwright_required: true
given: composer focused con texto "línea 1"
when: user presiona Shift+Enter, luego escribe "línea 2", luego Enter solo
then:
  - Después Shift+Enter: textarea contiene "línea 1\nlínea 2" (no envía)
  - Después Enter: mensaje user enviado con contenido "línea 1\nlínea 2" preservando salto
  - User bubble renderiza salto de línea visible (whitespace-pre-wrap o equivalente)
graders:
  - { type: e2e, path: "vitalia/frontend/e2e/shell-organism/valeria-chat-keys.spec.ts" }
```

### Scenario 4 — adversarial XSS guard

```yaml
type: adversarial
playwright_required: true
given: composer focused
when: user pega payload <script>alert('xss')</script> y envía
then:
  - Mensaje renderiza el contenido como texto plano (no ejecuta script)
  - DOM contiene texto literal "<script>alert('xss')</script>" escapado
  - Sin window.alert disparada (test escucha dialog event y no aparece)
graders:
  - { type: e2e, path: "vitalia/frontend/e2e/shell-organism/valeria-chat-xss.spec.ts" }
  - { type: state_check, target: dom, query: "document.querySelector('[data-testid=msg-bubble][data-role=user]').innerHTML", expect: "no <script> raw" }
```

### Scenario 5 — empty state (sub-categoría empty_state)

```yaml
type: empty_state
playwright_required: true
given: chatStore.messages = [] (nueva conversación / reset)
when: route renderiza
then:
  - ChatHeader presente (avatar + name + status + pill)
  - Área messages muestra ilustración avatar grande (h-12 w-12 bg-agent-valeria-soft con "V")
  - Heading "Empezá una conversación"
  - Subtexto "Preguntale a Valeria por la agenda de hoy, pacientes que faltan confirmar o cualquier tarea operativa de la clínica."
  - Composer disponible
  - NO mensajes renderizados (data-testid=msg-bubble count === 0)
graders:
  - { type: e2e, path: "vitalia/frontend/e2e/shell-organism/valeria-chat-empty.spec.ts" }
  - { type: visual_state, screen: "valeria-chat-empty", element: "[data-testid=valeria-chat]", expect: "matches mockup valeria-chat-sample.html (variante empty)" }
```

### Scenario 6 — accessibility (sub-categoría a11y)

```yaml
type: accessibility
playwright_required: true
given: chat renderizado con 6 mensajes mock
when: axe-core scan + keyboard navigation
then:
  - axe ruleset wcag2aa pass (0 violations)
  - Tab order: composer textarea es focusable; 3 botones stubs son focusables; "Enviar" botón es focusable
  - Composer textarea tiene `<label class="sr-only">` asociada
  - Messages container tiene `role="log"` + `aria-live="polite"` + `aria-label`
  - Mode pill no es interactivo (no rol button) — solo decorativo con aria-hidden si necesario
  - ChatHeader avatar tiene `aria-hidden="true"` (decorativo); name visible como texto
  - Contrast ratio: user bubble text-white sobre bg-agent-valeria ≥ 4.5:1 (verificable via axe)
graders:
  - { type: axe, ruleset: "wcag2aa" }
  - { type: e2e, path: "vitalia/frontend/e2e/shell-organism/valeria-chat-a11y.spec.ts" }
```

### Scenario 7 — i18n Spanish neutro (sub-categoría i18n)

```yaml
type: i18n
playwright_required: true
given: locale es-LA / es-419 default, chat renderizado
when: grep textContent del chat (mensajes mock + microcopy)
then:
  - Sin voseo: no aparecen tokens `vos|sos|tenés|podés|dale|mirá|fijate` (regex check)
  - Tildes y eñes preservadas: "También", "Día", "Año" si presentes renderizan correcto
  - Empty state copy `"Empezá"` → REVISAR (es voseo; Spanish neutro tuteo sería "Empieza una conversación") · ★ Open Q7
  - Composer placeholder: "Escribe a Valeria…" (tuteo correcto)
  - Send button label: "Enviar"
  - Mode pill: "🤖 Modo agente"
graders:
  - { type: e2e, path: "vitalia/frontend/e2e/shell-organism/valeria-chat-i18n.spec.ts" }
  - { type: state_check, target: dom, query: "regex /vos|sos|tenés|podés|dale|fijate/i contra body textContent", expect: "no match" }
```

---

## § 2 — Wireframe inline (HTML mockup)

**Ratified visual gate file (single SSoT mockup):**

`vitalia/docs/product/stories/vitalia-fase1-valeria-chat-skeleton/mockups/valeria-chat-sample.html`

Contiene 2 variantes en mismo file (toggle dark mode botón superior):

- **Variante A — conversación con 6 mensajes:** estado feliz, full conversation flow (bot greeting → user pregunta → delegate marker → bot respuesta vía Camila → user confirma → thinking dots Camila).
- **Variante B — empty state:** 0 mensajes, ilustración avatar grande + heading + subtexto + composer disponible.

Servir local para revisión Chris:

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/docs/product/stories/vitalia-fase1-valeria-chat-skeleton/mockups
python3 -m http.server 8888
# Chris abre http://localhost:8888/valeria-chat-sample.html
```

**ASCII abreviado (referencia rápida):**

```
┌────────────────────────────────────────────────┐  ChatHeader (h-14 px-4)
│ ◯V●  Valeria                  🤖 Modo agente   │  avatar + name + status + mode pill (right)
│      En línea · Tu secretaria virtual          │
├────────────────────────────────────────────────┤
│                                                │  ChatMessages (flex-1 overflow-y-auto)
│  ┌────────────────────────────┐               │   role="log" aria-live="polite"
│  │ ¡Buenos días! Tienes 8 ... │               │   bot bubble bg-card border-border
│  └────────────────────────────┘               │   timestamp "Valeria · 09:01"
│                                                │
│               ┌──────────────────────────────┐ │   user bubble bg-agent-valeria
│               │ ¿Cómo están las reseñas...?  │ │   alineado self-end
│               └──────────────────────────────┘ │   timestamp "09:02"
│                                                │
│       → delegando a 🟦Camila (modo Mantener)   │   delegate marker italic centered
│                                                │
│  ┌────────────────────────────────────┐       │   bot bubble (Camila respondiendo)
│  │ Esta semana ingresaron +3 reseñas..│       │   timestamp "Camila (via Valeria) · 09:02"
│  └────────────────────────────────────┘       │
│                                                │
│                          ┌──────────────────┐ │   user bubble
│                          │ Sí, ábrela.      │ │
│                          └──────────────────┘ │
│                                                │
│  ┌────────────────────────────────────┐       │   thinking bubble
│  │ Camila está abriendo Voz del ...  ●●●│     │   bg-agent-camila-soft + dots animados
│  └────────────────────────────────────┘       │
│                                                │
├────────────────────────────────────────────────┤  ChatComposer (border-t bg-card)
│ 📎🎙️⚡  [Escribe a Valeria…           ] [Enviar]│  3 stubs + textarea + send button
│  Cmd+K enfoca el composer desde el shell.      │  kbd hint
└────────────────────────────────────────────────┘
```

---

## § 3 — Estados visuales

| Estado | Trigger | Componentes visibles | Componentes ocultos |
|---|---|---|---|
| `populated` | `messages.length > 0` | ChatHeader, ChatMessages (bubbles), ChatComposer | EmptyState |
| `empty` | `messages.length === 0` | ChatHeader, EmptyState (ilustración + copy), ChatComposer | bubbles |
| `thinking` | último mensaje role==='thinking' o `status==='thinking'` | ChatHeader, ChatMessages incluyendo TypingIndicator, ChatComposer | — |
| `composer-typing` | textarea con texto, < max-height | ChatHeader, ChatMessages, ChatComposer expandible (max 100px height) | — |

NO se modela estado `error` (Fase 2 wire real cubre fallos network).

---

## § 4 — Componentes (reuse > inventar)

| Componente | Path repo | Acción |
|---|---|---|
| `Textarea` Shadcn | `vitalia/frontend/src/components/ui/textarea.tsx` | REUSE (instalado F1-S0) |
| `Button` Shadcn | `vitalia/frontend/src/components/ui/button.tsx` | REUSE |
| `Badge` Shadcn (mode pill) | `vitalia/frontend/src/components/ui/badge.tsx` | REUSE (F1-S0) — variant `outline` |
| `cn()` util | `vitalia/frontend/src/lib/utils.ts` | REUSE |
| `ValeriaChat` organismo | `vitalia/frontend/src/components/shared/shell-organism/ValeriaChat.tsx` | **NEW** — root chat (replaces ValeriaChatSlot) |
| `ChatHeader` molécula | `vitalia/frontend/src/components/shared/shell-organism/ChatHeader.tsx` | **NEW** — evoluciona header del slot F1-S5 (preserva avatar + name + status, agrega Mode Pill + status text largo) |
| `ChatMessages` molécula | `vitalia/frontend/src/components/shared/shell-organism/ChatMessages.tsx` | **NEW** — lista scrollable con `role="log"` `aria-live` |
| `ChatComposer` molécula | `vitalia/frontend/src/components/shared/shell-organism/ChatComposer.tsx` | **NEW** — Textarea + 3 stubs + Send button |
| `MessageBubble` molécula | `vitalia/frontend/src/components/shared/shell-organism/MessageBubble.tsx` | **NEW** — variant per `role: bot \| user` |
| `TypingIndicator` átomo | `vitalia/frontend/src/components/shared/shell-organism/TypingIndicator.tsx` | **NEW** — bubble con texto opcional + 3 dots animados |
| `DelegateMarker` molécula | `vitalia/frontend/src/components/shared/shell-organism/DelegateMarker.tsx` | **NEW** — italic centered "→ delegando a [pill] (modo X)" |
| `_mock-messages.ts` fixture | `vitalia/frontend/src/components/shared/shell-organism/_mock-messages.ts` | **NEW** — 6 mensajes hardcoded + `MOCK_RESPONSES_BY_AGENT['valeria']` (4 canned) |
| `agent-catalog.ts` registry | `vitalia/frontend/src/lib/agent-catalog.ts` | **NEW** — 6 agentes canónicos (slug, name, role, color, thumbnail, transparent, initial) + `DEFAULT_CHAT_AGENT='valeria'` |
| `chat-store.ts` zustand | `vitalia/frontend/src/stores/chat-store.ts` | **NEW** — `messages`, `activeAgent` (default valeria), `status`, `sendMessage()` mock, `clearMessages()`, `setActiveAgent()` (sin UI consumer F1-S6) |
| `globals.css` | `vitalia/frontend/src/app/globals.css` | **MODIFY** — agrega `--agent-mateo-soft` (light + dark) que falta del set inicial |
| `ValeriaSidebar` | `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.tsx` | **MODIFY** — reemplaza `<ValeriaChatSlot />` por `<ValeriaChat />` |
| `ValeriaChatSlot.tsx` | idem path | **DELETE** post-merge (F1-S5 placeholder cumplió su rol) |

**Cross-brand reuse check:** ningún componente vive en `core/`. Pattern chat agéntico podría aparecer en otras brands (Nicolify ya tiene `CopilotSidebar` parecido pero re-implementado) — flag para futuro `/pm-luana` promotion candidate cuando ≥2 brands lo necesiten. F1-S6 NO escala (es vitalia-only, mock-only).

---

## § 5 — Data flow (conceptual) + Agent catalog canónico

### § 5.1 — Agent catalog (NEW — 6 agentes ratificados Chris 2026-05-24)

Archivo canónico: `vitalia/frontend/src/lib/agent-catalog.ts` (o `components/shared/shell-organism/_agent-catalog.ts` si /architect prefiere local). Single source of truth cross-shell-organism (consumido por `ChatHeader`, `MessageBubble`, `Ribbon`, `RailIconButtons`).

```ts
export type AgentSlug = 'lisa' | 'valeria' | 'adrian' | 'lucas' | 'camila' | 'mateo'

export interface AgentDescriptor {
  slug: AgentSlug
  name: string                    // display name con acentos
  role: string                    // 1-line rol para tooltip/header subtitle
  colorToken: string              // CSS var token e.g. 'agent-valeria' (sin --)
  colorSoftToken: string          // soft variant para backgrounds e.g. 'agent-valeria-soft'
  hex: string                     // hex literal para mockups / fallback
  thumbnail: string               // path Next.js public/ e.g. '/agents/valeria/thumbnail.png'
  transparent: string             // path Next.js public/ e.g. '/agents/valeria/transparent.png'
  initial: string                 // letra fallback si img load falla
}

export const AGENT_CATALOG: Record<AgentSlug, AgentDescriptor> = {
  lisa:    { slug: 'lisa',    name: 'Lisa',    role: 'Estratega de marca y oferta',                                colorToken: 'agent-lisa',    colorSoftToken: 'agent-lisa-soft',    hex: '#00D084', thumbnail: '/agents/lisa/thumbnail.png',    transparent: '/agents/lisa/transparent.png',    initial: 'L' },
  valeria: { slug: 'valeria', name: 'Valeria', role: 'Tu secretaria virtual · coordinadora general',               colorToken: 'agent-valeria', colorSoftToken: 'agent-valeria-soft', hex: '#7b2d91', thumbnail: '/agents/valeria/thumbnail.png', transparent: '/agents/valeria/transparent.png', initial: 'V' },
  adrian:  { slug: 'adrian',  name: 'Adrián',  role: 'Closer · califica leads y reactiva oportunidades',           colorToken: 'agent-adrian',  colorSoftToken: 'agent-adrian-soft',  hex: '#01b2f8', thumbnail: '/agents/adrian/thumbnail.png',  transparent: '/agents/adrian/transparent.jpeg', initial: 'A' },
  lucas:   { slug: 'lucas',   name: 'Lucas',   role: 'Estratega Growth · viraliza y consigue leads',               colorToken: 'agent-lucas',   colorSoftToken: 'agent-lucas-soft',   hex: '#111111', thumbnail: '/agents/lucas/thumbnail.png',   transparent: '/agents/lucas/transparent.png',   initial: 'L' },
  camila:  { slug: 'camila',  name: 'Camila',  role: 'Fidelización · sube CLTV y monitorea satisfacción',          colorToken: 'agent-camila',  colorSoftToken: 'agent-camila-soft',  hex: '#180d95', thumbnail: '/agents/camila/thumbnail.png',  transparent: '/agents/camila/transparent.png',  initial: 'C' },
  mateo:   { slug: 'mateo',   name: 'Mateo',   role: 'Desarrollador · tecnología y diseño con IA',                  colorToken: 'agent-mateo',   colorSoftToken: 'agent-mateo-soft',   hex: '#fee209', thumbnail: '/agents/mateo/thumbnail.png',   transparent: '/agents/mateo/transparent.png',   initial: 'M' },
}

export const DEFAULT_CHAT_AGENT: AgentSlug = 'valeria'
```

**Tokens CSS verificados:** los 6 colores ya existen en `vitalia/frontend/src/app/globals.css` (`--agent-{lisa,valeria,adrian,lucas,camila,mateo}` + soft variants en light + dark mode). **EXCEPT** `--agent-mateo-soft` que NO está definido en globals.css — **F1-S6 agrega** `--agent-mateo-soft: 53 90% 90%` (light) + `--agent-mateo-soft: 53 80% 18%` (dark) en mismo PR.

### § 5.2 — Imágenes en `public/agents/`

```
vitalia/frontend/public/agents/
├── lisa/{thumbnail.png, transparent.png}
├── valeria/{thumbnail.png, transparent.png}
├── adrian/{thumbnail.png, transparent.jpeg}    # NOTE: adrian transparent es .jpeg (source original)
├── lucas/{thumbnail.png, transparent.png}
├── camila/{thumbnail.png, transparent.png}
└── mateo/{thumbnail.png, transparent.png}
```

Source originales viven en `/home/chalreme/Trabajo/Vitalia/agentes/{Agent}-{Rol}/{Agent}-Cuadrado.png` (no commitable). Sync verificado 2026-05-24 (md5 match).

### § 5.3 — chatStore zustand shape (extendido a 6 agentes)

```ts
import type { AgentSlug } from '@/lib/agent-catalog'

type MessageRole = 'bot' | 'user' | 'delegate' | 'thinking'

interface ChatMessage {
  id: string
  role: MessageRole
  content?: string                     // bot/user/thinking text
  time?: string                        // 'HH:MM' (calculado runtime es-PE locale)
  agent?: AgentSlug                    // bot/thinking source. Default: 'valeria' (DEFAULT_CHAT_AGENT)
  fromAgent?: AgentSlug                // delegate only — quien delega
  toAgent?: AgentSlug                  // delegate only — receptor delegación
  delegateMode?: string                // delegate only — etiqueta del modo ('Mantener', etc.)
}

interface ChatStore {
  messages: ChatMessage[]
  activeAgent: AgentSlug               // default: 'valeria'. Setter NO expuesto en UI F1-S6 (preparado para sub-story selector futura)
  status: 'idle' | 'thinking' | 'streaming'
  sendMessage(content: string): void   // mock: agrega user + setTimeout thinking + canned bot del activeAgent
  clearMessages(): void                // para tests empty state
  setActiveAgent(agent: AgentSlug): void  // existe en API pero NO se llama desde UI F1-S6 (preparado para futuro)
}
```

### § 5.4 — Mock `sendMessage` flow

1. Push `{ role: 'user', content, time: HH:MM }`
2. Set `status='thinking'` + push `{ role: 'thinking', agent: activeAgent, content: "${name} está escribiendo…" }`
3. setTimeout 600-800ms → remove thinking msg + push `{ role: 'bot', agent: activeAgent, content: MOCK_RESPONSES[count % len], time: HH:MM }`
4. Set `status='idle'`

`MOCK_RESPONSES` es per-agente (e.g., `MOCK_RESPONSES_BY_AGENT[activeAgent]`). En F1-S6 solo se hardcodea para Valeria (default). F2-S* agrega responses per Lucas/Camila/etc. cuando wire real.

### § 5.5 — Composición con shell

- **NO React Query** (no API). NO mutations server. NO invalidation. NO event bus.
- **NO Server Component**: `ValeriaChat` y descendants son `'use client'` (zustand + event handlers).
- `ChatHeader` consume `useChatStore(state => state.activeAgent)` + `AGENT_CATALOG[agent]` → renderiza avatar + name + role.
- `MessageBubble` para `role='bot'` consume `AGENT_CATALOG[message.agent ?? DEFAULT_CHAT_AGENT]` → colorea con `bg-${descriptor.colorSoftToken}` o `border-${descriptor.colorToken}` opcional para diferenciar bot Valeria vs bot Camila vs etc.

---

## § 6 — Microcopy (Spanish neutro LatAm)

<!-- voseo-allowed: glosario reference within examples below -->

| Lugar | Copy v1 (default) | Sustento |
|---|---|---|
| ChatHeader name | "Valeria" | — |
| ChatHeader status | "En línea · Tu secretaria virtual" | tuteo |
| ChatHeader mode pill | "🤖 Modo agente" | — |
| Composer placeholder | "Escribe a Valeria… (Enter envía · Shift+Enter salto de línea)" | tuteo, hint visible |
| Composer send button | "Enviar" | — |
| Composer kbd hint | "Cmd+K enfoca el composer desde cualquier parte del shell." | tuteo |
| Composer adjuntar `title` | "Adjuntar (próximamente)" | — |
| Composer voz `title` | "Voz (próximamente)" | — |
| Composer comandos `title` | "Comandos (próximamente)" | — |
| Empty state heading | "Empieza una conversación" ★ **CHANGED** del mockup ("Empezá" es voseo) | tuteo neutro |
| Empty state subtexto | "Pregúntale a Valeria por la agenda de hoy, pacientes que faltan confirmar o cualquier tarea operativa de la clínica." ★ **CHANGED** ("Preguntale" → "Pregúntale" tilde + clítico) | tuteo neutro |
| MOCK_MESSAGES bot msg 1 | "¡Buenos días! Tienes 8 turnos hoy y 3 pacientes esperando confirmar mañana. ¿Por dónde empezamos?" | tuteo |
| MOCK_MESSAGES user msg 2 | "¿Cómo están las reseñas Google esta semana?" | neutral |
| MOCK_MESSAGES bot msg 4 | "Esta semana ingresaron +3 reseñas Google (2 de 5★ y 1 de 4★). El score subió de 4.6 a 4.7. Hay una reseña destacable de Marina Pérez sobre Dr. Juan García que sugiero pinear en landing. ¿La abro?" | tuteo "abro" 1ª persona OK |
| MOCK_MESSAGES user msg 5 | "Sí, ábrela." | tuteo correcto |
| Delegate marker | "→ delegando a Camila (modo Mantener)" | — |
| Typing texts | "Valeria está escribiendo…" / "Camila está abriendo Voz del paciente…" | tuteo |
| MOCK_RESPONSES (canned) | TBD — 4-5 strings cortas. Sugerencia v1: ver § 8 abajo. Chris confirma o reescribe. | — |

**Spanish neutro check:** ✅ NO voseo después de las correcciones marcadas. ✅ Tildes + ñ + apertura `¿/¡` correctos. **Excepción documentada:** `MOCK_MESSAGES` no pasa por compilador voz tenant (es chrome mock). F2-S11 (camila-voz) introduce sustitución runtime cuando wire real.

---

## § 7 — Responsive breakpoints

| Breakpoint | Comportamiento ChatPanel |
|---|---|
| `< md` (768px) | ValeriaSidebar entera es drawer slide-in (F1-S5 cementado). ChatPanel ocupa 100% del drawer. Composer fixed-bottom dentro del drawer. |
| `md - lg` (768-1024px) | Chat ocupa 100% del slot `[1fr]` del grid de ValeriaSidebar. Rail/History en columna izquierda según `valeriaState`. |
| `> lg` (1024+) | Idéntico md-lg. Layout natural 50/50 con ChatPanel ocupando casi todo el panel Valeria. |

**No overflow horizontal:** bubbles `max-w-[80%]` (bot/user) y `max-w-[85%]` (Camila via Valeria) para evitar bubble-completo-ancho. `whitespace-pre-wrap` en bubble text para preservar saltos de línea.

---

## § 8 — MOCK_RESPONSES (canned bot answers) — sugerencia v1

Set rotativo determinístico (modulo por `messageCount`):

```ts
export const MOCK_RESPONSES: { content: string }[] = [
  { content: 'Mañana tienes 12 turnos confirmados y 4 pendientes. ¿Quieres que envíe recordatorios?' },
  { content: 'Esta semana cerraste 23 turnos. Promedio diario: 4.6. Día más cargado: jueves (7 turnos).' },
  { content: 'Te confirmo: agendé el turno para Marina Pérez el viernes a las 10:30. ¿Algo más?' },
  { content: 'Faltan 3 pacientes por confirmar para mañana. ¿Quieres que los contacte ahora por WhatsApp?' },
]
```

Spanish neutro verificado (tuteo). Time se calcula al runtime con `new Date().toLocaleTimeString('es-PE', {hour:'2-digit', minute:'2-digit'})` para que el timestamp del bot reply matchee la hora real del envío del user — coherencia visual demo.

---

## § 9 — Accessibility (resumen)

- `<section role="region" aria-label="Chat con Valeria">` wrapper
- Messages container: `<div role="log" aria-live="polite" aria-label="Conversación con Valeria">`
- Composer textarea: `<label class="sr-only" for="valeria-composer">Mensaje para Valeria</label>` + `id="valeria-composer"` (para Cmd+K focus de F1-S5)
- Avatar: `aria-hidden="true"` (decorativo); name visible como texto
- Status dot: `aria-hidden="true"` (decorativo); "En línea" como texto
- Mode pill: contenido textual visible, sin role interactive
- TypingIndicator dots: `aria-hidden="true"`; texto "Camila está abriendo…" leído por SR
- DelegateMarker: texto visible, pill Camila no es link
- Botones composer stubs (📎/🎙️/⚡): `aria-label` explícito + emoji wrapped en `<span aria-hidden="true">` o equivalente para evitar lectura redundante
- Send button "Enviar": foco visible (`focus:ring-2 focus:ring-ring`)
- **Contrast:** white sobre `bg-agent-valeria` (hsl 287 53% 37%) ≥ 4.5:1 (verificar con axe; ratio nominal ~6.5:1 OK)
- **Focus management:** Cmd+K focus al composer (handler ya en F1-S5). Enter envía. Shift+Enter newline. Esc cierra Valeria (handler F1-S5).

---

## § 10 — Telemetría (opcional)

Fase 1 NO emite eventos analytics (lo definirá story de telemetría aparte cuando wire real). Stub PostHog se mantiene no-op.

---

## § 11 — Brand voice / sales_agent integration

F1-S6 NO consume `personality_profiles.system_instruction` (mock chrome, no agent real). F2-S* (camila-voz / valeria-voz) introducirán compilador voz tenant cuando wire WebSocket sales_agent. F1-S6 deja el placeholder visual y los hooks para ese wire (ver § 5 chatStore — `sendMessage` mockea el shape final del callback Fase 2).

---

## § 12 — Visual gate (cement `shell-mockup-per-component.md`)

| Mockup HTML | Componentes ratificados | Próximo gate |
|---|---|---|
| `mockups/valeria-chat-sample.html` (Variante A 6-msgs + Variante B empty) | ChatHeader, ChatMessages, ChatComposer, MessageBubble, TypingIndicator, DelegateMarker, EmptyState | Chris ratifica visualmente vía `python3 -m http.server 8888` → checkpoint frontmatter agrega `ratified_visual_by_chris: true` + `ratified_visual_at` + lista `ratified_visual_mockups` |

Sin `ratified_visual_by_chris: true` en checkpoint → `/architect` REFUSE arrancar.

---

## § 13 — Deliverables

| File | Acción | Owner downstream |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaChat.tsx` | NEW | `/dev-team` builder-frontend |
| `vitalia/frontend/src/components/shared/shell-organism/ChatHeader.tsx` | NEW | idem |
| `vitalia/frontend/src/components/shared/shell-organism/ChatMessages.tsx` | NEW | idem |
| `vitalia/frontend/src/components/shared/shell-organism/ChatComposer.tsx` | NEW | idem |
| `vitalia/frontend/src/components/shared/shell-organism/MessageBubble.tsx` | NEW | idem |
| `vitalia/frontend/src/components/shared/shell-organism/TypingIndicator.tsx` | NEW | idem |
| `vitalia/frontend/src/components/shared/shell-organism/DelegateMarker.tsx` | NEW | idem |
| `vitalia/frontend/src/components/shared/shell-organism/_mock-messages.ts` | NEW | idem |
| `vitalia/frontend/src/stores/chat-store.ts` | NEW | idem |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebar.tsx` | MODIFY (replace `<ValeriaChatSlot />` por `<ValeriaChat />`) | idem |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaChatSlot.tsx` | DELETE (F1-S5 placeholder cumplió rol) | idem |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaChatSlot.test.tsx` | DELETE (obsoleto) | idem |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-happy.spec.ts` | NEW | idem |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-send.spec.ts` | NEW | idem |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-keys.spec.ts` | NEW | idem |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-xss.spec.ts` | NEW | idem |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-empty.spec.ts` | NEW | idem |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-a11y.spec.ts` | NEW | idem |
| `vitalia/frontend/e2e/shell-organism/valeria-chat-i18n.spec.ts` | NEW | idem |
| `vitalia/frontend/src/components/shared/shell-organism/ChatHeader.test.tsx` | NEW (Vitest unit) | idem |
| `vitalia/frontend/src/components/shared/shell-organism/MessageBubble.test.tsx` | NEW (Vitest unit) | idem |
| `vitalia/frontend/src/components/shared/shell-organism/ChatComposer.test.tsx` | NEW (Vitest unit) | idem |
| `vitalia/frontend/e2e/__screenshots__/shell/valeria-chat-{light,dark}-{populated,empty}.png` | NEW (Playwright generates) | idem |

---

## § 14 — Próximo paso post-done

ValeriaSidebar 100% funcional (rail+history+chat). F1-S7 ribbon-6-tabs arranca independiente del Valeria panel (toca el AppPanel derecho).
