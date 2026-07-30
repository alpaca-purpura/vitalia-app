---
story_id: vitalia-fase2-adrian-inbox
surface: frontend
builder: builder-frontend
auditor: auditor-frontend
architecture_pattern: ADR-vitalia-004
---

# 03-arch-fe — vitalia-fase2-adrian-inbox (frontend)

> **Naturaleza FE: consolidación + cableado.** ~40 comps shipped huérfanos (`features/inbox/`) → consolidar en `features/adrian/components/inbox/` (hogar canónico) + merge con la versión parity + crear las piezas NEW + ruta real + registro shell + DELETE huérfano.
> **Owner:** `builder-frontend` (Sonnet). **Auditor:** `auditor-frontend` (Opus). **MUST load:** `frontend-expert` + `vitalia-design-system` (★ SSoT shell/tokens/splitter).
> **NEVER touch:** `components/ui/**`, `components/shared/shell-organism/{ShellOrganismLayout,ValeriaSidebar,Ribbon,SubTabsBar,EmptyState,SubSubTabsBar}` (REUSE wrapper — solo consumir), `core/`, `sales_agent/`.

## 1. Routing (ADR-004 § 3.1)

```
vitalia/frontend/src/app/[tenantId]/(shell-organism)/adrian/inbox/page.tsx   NEW (RSC)
```

Mirror EXACTO de `mateo/agenda/page.tsx`:
- `export const metadata` (title "Inbox — Adrián | Vitalia", sin PHI).
- `params: Promise<{tenantId}>`, `searchParams: Promise<{conv?, filter?}>` (Next 16 async).
- Resuelve `conv` (UUID validado) + `filter` (whitelist: todos|sin-leer|asignadas|esperando|bot-activo|cerradas). **PHI nunca en URL** — solo `conv` (UUID), nunca nombre/datos.
- `const initialData = await getInitialInboxState({ tenantId, convId, filter })` — SSR, graceful degradation (retorna `{conversations:[], detail:null}` en error, NO throw).
- `return <AdrianInboxView initialData={initialData} initialConvId={conv} initialFilter={filter} tenantId={tenantId} />`.
- **Server Component** (sin `"use client"`). Auth la maneja el `(shell-organism)/layout.tsx`.

**Registro (★ N de CONN — sin esto la ruta es isla):**
- `lib/agent-catalog.ts`: `SHIPPED_STATIC_SUBTABS` += `"adrian.inbox"` (la ruta estática precede al dispatcher `[agent]/[subtab]`). `adrian.defaultSubtab='inbox'` + entry RIBBON_SUBTABS ya existen.
- `lib/shell-routes.ts`: **NO** agregar a `AGENT_SUBSUBTABS` (inbox = 1 panel coherente, no N3-static — ver ADR-004 § 3.1.1 tabla "single panel").

**Deep-link:** `?conv={id}` searchParam (RN-14). El `[conv-id]/page.tsx` N3-dyn = **DIFERIDO** (el thread es panel central siempre-visible del 3-pane; el searchParam cubre AC-3/RN-14; NO intercepting-route como embudo). Ver 03-arch.md § 16 Open Q #2.

## 2. FSD-Lite (ADR-004 § 3.2) — hogar canónico

```
vitalia/frontend/src/features/adrian/
├── index.ts                                  MODIFY — export AdrianInboxView + getInitialInboxState; quitar InboxPlaceholder del wiring activo
├── components/inbox/                          ← consolida features/inbox/ + parity
│   ├── AdrianInboxView.tsx                    NEW (client root 3-pane)
│   ├── InboxConvList.tsx                      MIGRATE+MERGE (ConversationList + parity ConversationItem)
│   ├── ConversationItem.tsx                   MERGE (rico + parity)
│   ├── InboxThread.tsx                        MIGRATE (ConversationThread + ToolCallCard inline)
│   ├── ThreadHeader.tsx                       MIGRATE+MERGE (+ ModeToggle + ConversationModeButton)
│   ├── MessageBubble.tsx                      MIGRATE+MERGE (por tipo: paciente/bot/humano/delegate/tool)
│   ├── ModeToggle.tsx                         MIGRATE (de SegmentedControl3Modes; + banner + Tomar control; map 3-modos)
│   ├── ConversationModeButton.tsx            NEW (★ ⛶full — colapsa Valeria)
│   ├── ContactSidebar.tsx                     MIGRATE (PHI-aware; tabs Datos/Actividad/Lead/Notas)
│   ├── ActivityStream.tsx                     MIGRATE (de AgentActivityStream)
│   ├── ToolCallCard.tsx                       NEW (colapsable inline)
│   ├── NudgeButton.tsx                        NEW (+ confirm)
│   ├── InboxFilters.tsx                       MIGRATE (FilterChips + SearchInput)
│   ├── Composer*.tsx (Area/Input/Attach/Voice/SendButton) MIGRATE
│   ├── PauseAdrian{Button,ConfirmModal}.tsx   MIGRATE
│   ├── ActionReceiptUndoChip.tsx              MIGRATE
│   ├── {VoiceMessagePlayer,ImageAnalysisCard,AdrianToolsSheet,ProposalCardBanner}.tsx MIGRATE
│   ├── TakeoverBanner.tsx                     REUSE (parity)
│   └── __tests__/                             MIGRATE (Vitest co-located — mantener verdes)
├── api/
│   ├── inbox.ts                               NEW — hooks RQ consolidados (useInboxConversations, useConversationDetail, useSetMode, useSendMessage, useActivityStream, usePauseAdrian, useRetractMessage, useNudge, ...)
│   ├── inbox-server.ts                        NEW — getInitialInboxState (SSR)
│   ├── _keys.ts                               MIGRATE — RQ keys ['adrian','inbox',action,...filters]
│   └── __tests__/                             MIGRATE
├── hooks/
│   ├── useValeriaReaccion.ts                  NEW (básica)
│   ├── use-activity-stream-poll.ts           MIGRATE
│   ├── use-conversation-filters.ts           MIGRATE
│   └── use-action-receipt-timer.ts           MIGRATE
├── store/inbox-store.ts                       MIGRATE+EXTEND (+ priorValeriaState, sidebarOpen, activityExpanded, attachQueue)
└── types/
    ├── inbox.types.ts                         MIGRATE+MERGE (mirror DTOs BE)
    └── inbox-schema.ts                        NEW (Zod — send/mode/nudge payloads)

vitalia/frontend/src/components/shared/shell-organism/ChannelBadge.tsx   NEW (reusable cross-feature)
vitalia/frontend/src/features/inbox/                                      DELETE (todo)
```

**Reglas:** sin cross-feature imports (`features/adrian` NO importa `features/lisa`/`mateo`). ChannelBadge en `shared/shell-organism/` (cross-feature reusable). Sin Shadcn primitives en `features/` (usar `components/ui/`).

## 3. Client root (ADR-004 § 3.3)

`AdrianInboxView.tsx` (`"use client"` línea 1):
- Props: `initialData`, `initialConvId`, `initialFilter`, `tenantId`.
- Hidrata RQ con `initialData` (sin re-fetch en mount).
- Layout: `ResizablePanelGroup` (Shadcn `resizable.tsx`, REUSE) direction horizontal, 3 paneles:
  ```
  <ResizablePanelGroup direction="horizontal">
    <ResizablePanel defaultSize=24 minSize=18><InboxConvList/></ResizablePanel>
    <ResizableHandle/>
    <ResizablePanel defaultSize=52><InboxThread/></ResizablePanel>
    <ResizableHandle/>
    <ResizablePanel defaultSize=24 minSize=18><ContactSidebar/></ResizablePanel>
  </ResizablePanelGroup>
  ```
- Mobile (`<768px`): Tabs (Conversaciones · Thread · Detalles), default Thread (RN responsive). Valeria → drawer.
- 100% del panel sin `max-width` hard (RN-11). El splitter del shell ya da el ancho.
- Integra `useValeriaReaccion(convId)` (al abrir conv).

## 4. Data layer (ADR-004 § 3.4)

| Estado | Storage |
|---|---|
| Lista convs, detalle, activity-stream | React Query (`useInboxConversations`, `useConversationDetail`, `useActivityStream`) — SSoT |
| `valeriaState` (modo conversación) | `useShellStore` (REUSE — NO modificar) |
| UI inbox (sidebar abierto, activity expanded, `priorValeriaState`, attach queue) | Zustand `inbox-store` |
| Filtros bookmarkables (conv, filter) | `useSearchParams` + `router.replace()` |

RQ keys: `['adrian','inbox','conversations',filters]` · `['adrian','inbox','conversation',convId]` · `['adrian','inbox','activity-stream',convId]`.
Polling: lista `refetchInterval: 10_000`; activity-stream `refetchInterval: 5_000` solo cuando expandido.
Mutations optimistic: `useSetMode` + `usePauseAdrian` (rollback en 409 — SC-4). `invalidateQueries` explícito post-mutación.

## 5. 3-modos → backend mapping (★ ModeToggle)

`ModeToggle.tsx` (segmented control, 3 estados):

| UI | mutación `useSetMode` body |
|---|---|
| 🤖 Decide | `{mode:'ai', proposal_required:false, expected_updated_at}` |
| 🤝 Consulta | `{mode:'ai', proposal_required:true, expected_updated_at}` |
| 👤 Manual | `{mode:'human', proposal_required:false, expected_updated_at}` |

`PATCH /api/v1/vitalia/inbox/conversations/{id}/mode` (OCC). 409 → rollback + toast "Recarga e intenta". Banner autonomía + "Tomar control" en modo decide. **NO usar Shadcn `<Tabs>`** (eso es nav N3 anti-pattern — `test-ribbon-no-shadcn-tabs` valida); usar `RadioGroup`/segmented control.

## 6. Modo conversación (★ ConversationModeButton — RN-11/RN-12)

```ts
// al pulsar ⛶full:
const prior = useShellStore.getState().valeriaState;   // 'rail' | 'full'
inboxStore.setPriorValeriaState(prior);
useShellStore.getState().setValeriaState('collapsed');
// inbox ocupa 100% (Valeria collapsed)
// al re-pulsar:
useShellStore.getState().setValeriaState(inboxStore.priorValeriaState ?? 'rail');
```
`useShellStore` = SSoT (REUSE, NO modificar). `inbox-store` guarda `priorValeriaState`. Nunca pierde el estado de Valeria.

## 7. Valeria-reacciona (básica)

`useValeriaReaccion(convId)`: al abrir conv → POST best-effort al chat de Valeria con contexto del lead (stage, canal, oferta — non-PHI) → recibe 1-2 acciones sugeridas pintadas en `ValeriaChat`/sidebar. **Graceful degradation:** si falla, NO rompe el thread (try/catch + log silencioso). MVP.

## 8. ChannelBadge (NEW reusable)

`components/shared/shell-organism/ChannelBadge.tsx` — badge por canal (WhatsApp 🟢 · IG 📷 · Email 📧 · Web 💬). Props `{channel: string}`. Tokens del design system (sin colores hardcoded — `test_no_hardcoded_colors`). Lift candidate brand-local; NO liftar a `/pm-luana` ahora (regla ≥2 brands).

## 9. Forms (ADR-004 § 3.5)

Composer no es form complejo. `inbox-schema.ts` (Zod) valida payloads: `sendMessageSchema`, `setModeSchema` (discriminated por mode), `nudgeSchema`. Submit-driven (send/mode/nudge atómicos). Toasts `sonner`. Sin autosave.

## 10. Estados visuales (spec § Estados visuales)

`idle/loading` (skeleton 3-pane) · `success` (doctor/recepcion con PHI masked) · `empty` (EmptyState shell REUSE) · `error` (banner "No pudimos cargar…" + Reintentar) · `agent-thinking` (TypingIndicator + composer disabled) · `agent-waiting-approval` (composer pre-lleno + banner sugerencia + Aprobar/Editar/Descartar) · `agent-failed` (banner "🔴 Adrián pide ayuda" + auto-switch manual) · `full` (Valeria collapsed + inbox 100%).

## 11. Telemetría (ADR-004 § 3.8)

`useTelemetry` → `vitalia_growth_studio_event`: `adrian_inbox_viewed`, `adrian_inbox_conv_opened`, `adrian_inbox_mode_changed`, `adrian_inbox_takeover`, `adrian_inbox_nudge_sent`, `adrian_inbox_conversation_mode`. Sin PHI/montos en props (`test_growth_studio_event_no_phi`).

## 12. Tests (ADR-004 § 3.9)

- **Vitest unit:** hooks RQ migrados (mantener verdes), `ModeToggle` (mapping 3-modos), `ConversationModeButton` (colapso/restore valeriaState), `ToolCallCard`, `ChannelBadge`, `NudgeButton`, `AdrianInboxView` (3-pane render).
- **Playwright funcional** (importan `e2e/fixtures/base.ts` — anti-burbuja): SC-1..SC-10. Specs en `e2e/shell-organism/adrian-inbox-*.spec.ts`.
- **Visual golden ×12:** `e2e/__screenshots__/inbox/{layout}-{mode}-{light|dark}.png` (3 modos × 2 themes × 2 split/full). Ratchet shrink-only.
- **axe a11y:** SC-9 (tab order: búsqueda→filtros→conv→toggle→composer; aria-current/aria-selected; Esc en composer; wcag2aa).
- **MSW handlers:** `src/mocks/handlers/inbox.ts` (mock backend per spec). **PERO** e2e live-verify NO mockea el backend del surface bajo prueba (DoD #37).

**Comandos (native, host):**
```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend && npx tsc --noEmit
cd ${WS}/vitalia/frontend && npx eslint src/features/adrian/ src/components/shared/shell-organism/ChannelBadge.tsx --cache
cd ${WS}/vitalia/frontend && npx vitest run src/features/adrian/
cd ${WS}/vitalia/frontend && npx vitest run src/__tests__/architecture/
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/shell-organism/adrian-inbox
```

## 13. Anti-patterns (NO hacer)

- ❌ Dejar `features/inbox/` + `features/adrian/.../inbox/` coexistiendo (DELETE el huérfano en T-4).
- ❌ Modificar el wrapper shell (`ShellOrganismLayout`, `ValeriaSidebar`, `Ribbon`, `SubTabsBar`) — REUSE.
- ❌ Modificar `useShellStore` (consume `setValeriaState`, no cambia el store).
- ❌ Shadcn `<Tabs>` para los 3-modos o sub-secciones (anti-pattern N3/N4). Segmented control / RadioGroup.
- ❌ Colores hardcoded (usar tokens `--agent-adrian`/`--agent-adrian-soft`).
- ❌ PHI en URL/searchParams (solo `conv` UUID).
- ❌ Olvidar `SHIPPED_STATIC_SUBTABS += adrian.inbox` → la ruta sería isla (dispatcher → placeholder).
- ❌ Voseo en chrome (neutro). Output de Adrián respeta voz tenant.
- ❌ e2e que mockea el backend del surface presentado como live-verify (DoD #37 — falso verde).
