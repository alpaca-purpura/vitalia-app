# vitalia-slice-1-inbox — 02-design-ui (component breakdown del mockup)

> **SSoT visual:** `02-design-ui-mockup.html` (ratificado Chris 2026-05-17, heredado del parent `vitalia-ux-discovery`).
> **Brand tokens:** `vitalia/frontend/src/app/globals.css` (cementados Story 11 T-arch-1).
> **FSD-Lite:** `vitalia/frontend/src/features/inbox/` + `vitalia/frontend/src/components/shared/{phi,agents,activity-stream,contact-sidebar,shell}/` (shared ya existen post Story 11).
> **Mockup status:** abre `02-design-ui-mockup.html` en navegador local — state switcher arriba permite previsualizar los 8 estados visuales.

## § 1 — Component tree

```
app/(app)/inbox/page.tsx                     # RSC entry · resuelve params · pasa a InboxPageClient
└── features/inbox/components/
    └── InboxPageClient.tsx                  # "use client" · wraps tree con nuqsAdapter
        └── InboxLayout                      # grid 3-pane: ConvList (320) · Thread (flex) · ContactSidebar (280 toggle)
            ├── ConversationListPanel
            │   ├── SearchInput              # debounce 300ms · nuqs `search`
            │   ├── FilterChips              # 4 primarios + 4 status + 2 destacados + dropdown "Más"
            │   ├── ConversationList         # virtualized list
            │   │   └── ConversationItem×N   # nombre + badge canal + 🔴/📎 + Stage chip + ultimo timestamp
            │   └── ListEmptyState           # 4 variantes: noConversations / noHelpNeeded / noMediaUnread / noResultsFilter
            ├── ConversationThread
            │   ├── ThreadHeader
            │   │   ├── PatientNameChannel    # nombre · canal pill · activa hace Xmin
            │   │   ├── SegmentedControl3Modes # Adrián decide · Adrián consulta · Yo escribo (NEW)
            │   │   ├── VoiceStyleChip        # 🟢 Estilo consultivo · sin presión (read-only chip)
            │   │   ├── PauseAdrianButton     # ⏸ Pausar Adrián (NEW)
            │   │   ├── ToolsSheetTrigger     # 🛠 Herramientas (abre AdrianToolsSheet)
            │   │   └── ContactSidebarToggle  # 👤 Ficha contacto
            │   ├── ThreadScrollContainer     # max-w-3xl mx-auto · auto-scroll on new
            │   │   └── MessageBubble×N      # render por msg.type
            │   │       ├── Avatar            # paciente foto / Adrián gradient_adrian / María etc
            │   │       ├── MessageContent    # text | audio (VoiceMessagePlayer) | image (ImageAnalysisCard stub) | system
            │   │       └── ActionReceiptUndoChip  # solo si msg.handler_mode=ai y dentro 5min (NEW)
            │   ├── ComposerArea
            │   │   ├── MessageInput          # textarea · placeholder dinámico per-modo
            │   │   ├── ComposerAttachButton  # 📎 filesystem upload (image/audio/file) (NEW)
            │   │   ├── ComposerVoiceButton   # 🎤 MediaRecorder API (reuse VoiceOverlay copilot Nicolify) (NEW)
            │   │   └── SendButton            # "Enviar como Adrián ➤" o "Enviar"
            │   └── AgentActivityStream       # sticky 32px expand 240px (NEW)
            └── ContactSidebar                # 280px collapsable · PHI-aware
                ├── ContactBasic              # 📱 ***-4567 🔓 (PiiMaskedSpan)
                ├── StageDecisionSection      # Stage decisión + Considerando
                ├── OfferLinkedSection        # Blanqueamiento Premium + [Ver oferta →]
                ├── NextAppointmentSection    # — o link
                ├── NPSHistorySection         # — o list
                └── FullProfileLink           # [Ver ficha 🔒] · RequireRole admin_clinic/doctor

# Modals / Sheets (rendered into portals)
├── AdrianToolsSheet                          # Sheet right 420px · read-only (NEW)
├── ProactiveOutboundModal                    # cross-link agenda+pipeline+marketing (NEW)
└── PauseAdrianConfirmModal                   # 60min pause (NEW)
```

## § 2 — Tokens consumed (paleta cementada)

CSS vars de `vitalia/frontend/src/app/globals.css` (NO HEX literales en TSX — arch fitness `test_no_hardcoded_colors.test.ts` bloquea):

| Token | Uso en /inbox |
|---|---|
| `--vitalia-cian #01B2F8` | hero accent + filters active border + composer focus ring |
| `--vitalia-purpura #7B2D91` | segmented active background (12% opacity) + Adrián avatar gradient stop |
| `--vitalia-amarillo #FEE209` | badges premium + highlight ProposalCard |
| `--vitalia-azul-marino #180D95` | app shell + sidebar bg + body text + primary CTA |
| `--vitalia-verde-lima #B8DC2A` | success soft + Lucas avatar gradient stop (NO usado en /inbox excepto Activity Stream icon Lucas si applicable) |
| `--vitalia-success #16A34A` | status verde paciente al día + deposit confirmed |
| `--vitalia-warning #D97706` | warning soft + pago pendiente |
| `--vitalia-danger #DC2626` | error · cancelado · 🔴 Adrián pide ayuda chip |

Gradients:
- `--vitalia-gradient-adrian`: `linear-gradient(135deg, #7B2D91 0%, #180D95 100%)` → Adrián avatar
- `--vitalia-gradient-agent`: `linear-gradient(135deg, #01B2F8 0%, #7B2D91 100%)` → Valeria avatar
- `--vitalia-gradient-lucas`: `linear-gradient(135deg, #B8DC2A 0%, #01B2F8 100%)` → Lucas avatar

## § 3 — Estados visuales (8 totales)

Cada estado tiene representación clickable en `02-design-ui-mockup.html`:

| Estado | Trigger | Componentes visibles | Componentes ocultos |
|---|---|---|---|
| `idle` | Mount inicial, antes de fetch | Skeleton 3-pane (List + Thread + Sidebar placeholders) | Conversaciones + composer activo |
| `loading` | Fetch convs en curso | Skeleton list items + thread placeholder | Mensajes reales |
| `success` (authenticated dr.demo) | Fetch OK + role=doctor + tenant Sanaré MX | ConversationList + Thread + ContactSidebar + Composer + Activity Stream | Skeletons + empty state |
| `success` (authenticated recepcion) | role=recepcion · ContactSidebar PHI fields MASKED por default (click 🔓 audita reveal) | idem · PHI fields wrapped en `<PiiMaskedSpan>` | reveal-on-default fields |
| `error` | Fetch falla | Error banner "No pudimos cargar este inbox" + Retry button + Activity Stream colapsado | List + Thread normal |
| `empty` | Fetch OK + 0 convs (o 0 resultados filtro) | Empty state illustration (gradient-agent avatar) + heading + body + CTA limpiar filtros | List items |
| `agent-thinking` | `handler_mode='ai'` + Adrián procesando turn | TypingIndicator en thread + chip "Confianza: calculando…" · Composer disabled (placeholder "Adrián está respondiendo…") | — |
| `agent-waiting-approval` | `handler_mode='ai'` + `proposal_required=true` (modo "Adrián consulta") | Composer pre-llenado con draft + banner "✨ Adrián te sugiere esta respuesta…" + botones [Aprobar y enviar]/[Editar]/[Descartar] | ActionReceipt undo chip (no aplica antes de enviar) |
| `agent-failed` | Adrián escaló por fallo (transcripción · tool error · prompt injection detected) | Banner top thread "🔴 Adrián te pide ayuda · {razón}" + composer auto-switch a "Yo escribo" + chip ⚠ en lista | Mensaje auto Adrián (no se envió) |
| `proactive-outbound-modal-open` | User abre desde /agenda /pipeline /marketing | `ProactiveOutboundModal` con picker contacto + picker template (5 HSM Meta-approved) + preview WA | — |

## § 4 — Wireframe-to-component map (mockup section → archivo)

Lectura del mockup HTML por sección:

| Sección mockup HTML | Archivo destino |
|---|---|
| Header app + sidebar `<aside class="...sidebar 240px">` | `components/shared/shell/AppShell.tsx` + `Sidebar.tsx` (existen Story 11) |
| Topbar `<header>` | `components/shared/shell/TopBar.tsx` (existen Story 11) |
| Panel izquierda `<aside class="conv-list 320px">` | `features/inbox/components/ConversationListPanel.tsx` (NEW) |
| Search + filter chips primarios + collapsible "Más ▼" | `features/inbox/components/FilterChips.tsx` (NEW) |
| Lista conv items | `features/inbox/components/ConversationList.tsx` + `ConversationItem.tsx` (REUSE adapter) |
| Header thread + segmented control + voice style chip | `features/inbox/components/ThreadHeader.tsx` (NEW) + `SegmentedControl3Modes.tsx` (NEW) + `VoiceStyleChip.tsx` (NEW) |
| Botones thread header `[⏸][🛠][👤]` | `features/inbox/components/{PauseAdrianButton,ToolsSheetTrigger,ContactSidebarToggle}.tsx` (NEW) |
| Thread scroll container + messages | `features/inbox/components/ConversationThread.tsx` (REUSE adapter) |
| Audio message bubble (player + transcript) | `features/inbox/components/VoiceMessagePlayer.tsx` (NEW) |
| Image bubble (stub análisis Adrián) | `features/inbox/components/ImageAnalysisCard.tsx` (NEW stub) |
| Action receipt undo chip debajo msg Adrián | `features/inbox/components/ActionReceiptUndoChip.tsx` (NEW) |
| Composer area | `features/inbox/components/MessageInput.tsx` (REUSE adapter) |
| Composer attach + voice record buttons | `features/inbox/components/ComposerAttachButton.tsx` + `ComposerVoiceButton.tsx` (NEW) |
| Activity Stream sticky bottom | `features/inbox/components/AgentActivityStream.tsx` (NEW) |
| ContactSidebar derecha (PHI) | `features/inbox/components/ContactSidebar.tsx` (REUSE adapter + envolver con PHI) |
| Tools Sheet derecha 420px | `features/inbox/components/AdrianToolsSheet.tsx` (NEW · Shadcn Sheet) |
| Proactive outbound modal | `features/inbox/components/ProactiveOutboundModal.tsx` (NEW · Shadcn Dialog) |

## § 5 — Hooks (React Query) y store

```
features/inbox/api/
├── use-conversations.ts                 # GET /api/v1/vitalia/crm/conversations · paginated + filters
├── use-conversation-detail.ts           # GET /api/v1/vitalia/crm/conversations/{id}
├── use-send-message.ts                  # POST /api/v1/vitalia/inbox/conversations/{id}/messages
├── use-retract-message.ts               # POST /api/v1/vitalia/inbox/conversations/{id}/messages/{msg}/revert
├── use-set-mode.ts                      # POST /api/v1/vitalia/inbox/conversations/{id}/mode
├── use-pause-adrian.ts                  # POST /api/v1/vitalia/inbox/conversations/{id}/pause-adrian
├── use-activity-stream.ts               # GET /api/v1/vitalia/inbox/conversations/{id}/activity-stream
├── use-tools-state.ts                   # GET /api/v1/vitalia/inbox/conversations/{id}/tools
├── use-transcribe-audio.ts              # POST /api/v1/vitalia/inbox/conversations/{id}/transcribe-audio
├── use-proactive-outbound.ts            # POST /api/v1/vitalia/inbox/proactive-outbound
└── use-attach-media.ts                  # POST (multipart) /api/v1/vitalia/inbox/conversations/{id}/attach

features/inbox/store/
└── inbox-store.ts                       # Zustand · UI state: { expandedActivityStream, contactSidebarOpen, attachQueue, retractingMessages: Set<string> }
```

React Query keys + invalidation:
- `['inbox','conversations', filters]` → invalidated on `conversation:updated` SSE event
- `['inbox','conversation', leadId]` → invalidated on `message:sent`, `message:retracted`, `mode:changed`
- `['inbox','activity-stream', leadId]` → polled every 5s when ActivityStream expanded
- Optimistic updates: `setMode` + `pauseAdrian` (rollback on 409 Conflict)

## § 6 — Microcopy SSoT

`vitalia/frontend/src/features/inbox/copy.ts` exporta `INBOX_COPY` const. Cero strings hardcoded en JSX. Spanish neutro LatAm (NO voseo · `spanish-text.md` § R2). Magic comment `// voseo-allowed:` solo en allowlist (no copy real).

Detalle del object completo en `01-spec-extract.md § 10` y reference parent `01-spec.md` líneas 882-1052.

## § 7 — Accesibilidad

Cementada en `01-spec-extract.md § 15`. Tests en `04-validators.yaml::visual::a11y_axe_inbox`.

## § 8 — Performance budgets

- LCP `/inbox` < 2.5s (skeleton inicial + first conv list batch)
- INP < 200ms (segmented control switch · filter chip click · message send)
- CLS < 0.1 (composer fixed bottom · sticky activity stream no shift)
- Virtualization en ConversationList si > 50 items
- Memoization en ConversationItem (React.memo + selector React Query slice)

## § 9 — Storybook stories obligatorias (per ticket T-inbox-fe-storybook)

Cada componente NEW Slice 1 tiene story con variants:
- `SegmentedControl3Modes`: default (Adrián decide) · consulta · yo escribo · disabled (Adrián pausado)
- `FilterChips`: all clear · multi-active · "Más filtros" expanded · 0 results state
- `VoiceMessagePlayer`: with-transcription · transcription-failed · playing · paused
- `ImageAnalysisCard`: stub-loading · stub-loaded-with-mock · phi-flagged-future
- `AdrianToolsSheet`: with-offer · no-offer · disabled-tool-with-explanation
- `AgentActivityStream`: collapsed · expanded · empty-state · 8-events-scrollable
- `ActionReceiptUndoChip`: 4:30-countdown · expiring · expired
- `ProactiveOutboundModal`: contact-picker · template-picker · preview-WA · sent-success

## § 10 — Referencias

- `02-design-ui-mockup.html` (SSoT visual)
- `vitalia/docs/architecture/design-system.md` (tokens cementados Story 11)
- `vitalia/frontend/src/app/globals.css` (CSS vars)
- `vitalia/frontend/src/components/shared/{shell,phi,agents,activity-stream,contact-sidebar}/` (shared scaffolding ya existe Story 11)
- `nicolify/frontend/src/features/closer-studio/components/inbox/` (REUSE adapter source)
- `nicolify/frontend/src/features/copilot/components/composer/VoiceOverlay.tsx` (REUSE source voice recorder)
