---
story_id: vitalia-fase2-adrian-embudo
surface: frontend
parent: 03-arch.md
owner_builder: builder-frontend
owner_auditor: auditor-frontend
must_load_skills: [frontend-expert, vitalia-design-system]
---

# 03-arch-fe.md — Frontend · Embudo de Adrián

> Detalle FE para `builder-frontend`. **Fiel al mockup `mockups/embudo-v3.html` + spec § Design specification D.0–D.16** (contrato visual ratificado Chris). FSD-Lite (ADR-vitalia-004 § 3.2). Tokens de `globals.css` — NUNCA hardcode HSL. REUSE > NEW.

## REUSE (NO recrear — ya shipped)

| Componente | Path | Uso |
|---|---|---|
| `EntitySubNavBar` | `components/shared/shell-organism/EntitySubNavBar.tsx` | workspace lead/nuevo (`rootHref=/adrian/embudo`, `leaves=[resumen,historial]`, `entity={lead}`, `activeLeaf`) — D.7 |
| `TogglePill` | `components/shared/shell-organism/TogglePill.tsx` | Kanban\|Lista + Modo Adrián\|Todos — D.2 |
| `EmptyState`/`EmptyStateInline` | `components/shared/shell-organism/` | board/lista/recuperar empty — D.14 |
| `PiiMaskedSpan` | `components/shared/phi/PiiMaskedSpan.tsx` | nombre masked en card/lista/workspace |
| `ChannelBadge` | `components/shared/shell-organism/ChannelBadge.tsx` | **EXTEND** (ver abajo) — D.6 |
| `@dnd-kit/core` + `/utilities` | instalado | drag override + KeyboardSensor (SC-10) |
| `fetchClient` / `useTenantId` / `useClinicId` | `lib/api`, `hooks/` | data layer |
| átomos Shadcn `components/ui/*` | Button, Badge, Card, Table, Tooltip, Select, Input, Textarea, Label, Avatar, Skeleton, ScrollArea, Separator, Command, Popover | reuse (NO `Dialog` salvo OverrideReasonDialog que SÍ usa overlay) |
| `useTelemetry` hook | shipped | eventos `embudo_*` |
| `EmbudoPlaceholder.tsx` | `features/adrian/components/placeholders/` | **retirar** en este PR (reemplazar por sentinel) |

## EXTEND

- **`ChannelBadge`** (`components/shared/shell-organism/ChannelBadge.tsx`): el spec lo lista "NEW compartida" pero **ya existe** (usa Tailwind token-classes + lucide). Se EXTIENDE para soportar **color de marca de la red social** (D.6) + canales faltantes (`meta`, `referido`, `tiktok`). Consume el nuevo registro `channel-meta`. Mantiene back-compat con consumers de inbox. `iconOnly`/`className` props intactos.

## NEW (justificado)

- **`lib/channels/channel-meta.ts`** — registro único `CHANNEL_META: Record<slug, {label, color (CSS var), softColor, glyph}>` (§ Registro de canales). Hogar reutilizable cross-solución (Embudo/Inbox/Outbound/Analytics). Colores de marca via CSS vars dedicadas en `globals.css` (NO hardcode inline → no rompe `test_no_hardcoded_colors`). Comentario `lift candidate /pm-luana` (igual que ChannelBadge.tsx ya tiene).
- **`components/shared/score/ScoreDonut.tsx`** — SVG donut compacto (D.5). `34×34`, `r=10 sw=4`, color por score (≥70 emerald / 40-69 amber / <40 red via tokens). Número centrado. Server Component (no state). a11y: número visible (no solo color).

## Routing (ADR-004 § 3.1 — Server Component + SSR)

```
app/[tenantId]/(shell-organism)/adrian/
├── embudo/page.tsx                          # board (V1) — Server Component, getEmbudoBoardInitialState()
├── embudo/[leadId]/page.tsx                 # redirect → ./resumen (default)
├── embudo/[leadId]/resumen/page.tsx         # workspace Resumen (V3)
├── embudo/[leadId]/historial/page.tsx       # workspace Historial (V3)
├── embudo/nuevo/page.tsx                    # alta (V5) — ruta-hoja, NO modal
└── recuperar/page.tsx                       # sub-tab hermana (V4)
```
- `embudo/page.tsx` Server Component → `AdrianEmbudoView` client root con `initialBoard` prop. SSR fetch `getEmbudoBoardInitialState({tenantId, searchParams})` (cookies forwarded).
- `[leadId]` = UUID (RN-16, `test_no_phi_in_url_params`). NO PHI en URL.
- `embudo/nuevo` precede a `[leadId]` (static segment > dynamic).
- `lib/shell-routes.ts`: verificar `AGENT_SUBTABS.adrian` incluye `embudo` + `recuperar` (agregar si falta). **NO** entries en `AGENT_SUBSUBTABS` (board = single panel; detalle = N3-dynamic vía página, opción C — NO SubSubTabsBar, NO Sheet).
- Edge-redirect convention: el redirect `[leadId]/page.tsx → ./resumen` — preferir edge-redirect (proxy.ts) o `redirect()` server-side. ⚠️ MEMORY: Next 16.2.3 soft-nav intra-route-group + `redirect()` puede disparar "Rendered more hooks" flake; el redirect de landing ya está en edge. Para `[leadId]→resumen`, usar `redirect()` server-side (es nav dura desde el board, no soft-nav intra-group) — pero el builder debe verificar live (DoD) que no flakea; si flakea, mover a edge.

## FSD-Lite layout (`features/adrian/`)
```
features/adrian/
├── index.ts                                 # MODIFY — re-export AdrianEmbudoView, RecuperarView
├── components/
│   ├── placeholders/EmbudoPlaceholder.tsx   # RETIRAR (sentinel)
│   ├── embudo/
│   │   ├── AdrianEmbudoView.tsx             # client root ("use client" L1, props initialBoard)
│   │   ├── EmbudoHeader.tsx                 # título + chip Adrián + TogglePill + SortBySelect + +Nuevo lead (D.2)
│   │   ├── EmbudoFilters.tsx                # origen/doctor/etiquetas/fecha/score/operador
│   │   ├── EmbudoMetrics.tsx                # KPI strip (D.2)
│   │   ├── KanbanBoard.tsx                  # @dnd-kit DndContext (D.3)
│   │   ├── PipelineColumn.tsx               # droppable (D.3)
│   │   ├── LeadCard.tsx                     # draggable, anatomía D.4
│   │   ├── LeadsTable.tsx                   # vista Lista (D.9)
│   │   ├── SortBySelect.tsx                 # Ordenar por (RN-17)
│   │   ├── OverrideReasonDialog.tsx         # D.12 (overlay + textarea required)
│   │   ├── lead/
│   │   │   ├── LeadWorkspace.tsx            # EntitySubNavBar + render vista activa (D.7/D.8)
│   │   │   ├── ResumenView.tsx              # Datos + Estado agente + Score (D.8)
│   │   │   ├── HistorialView.tsx            # timeline (D.8)
│   │   │   ├── LeadSummaryHeader.tsx        # franja resumen (D.8)
│   │   │   └── ScoreBreakdown.tsx           # glass-box bloque (NO tab)
│   │   ├── nuevo/NewLeadPage.tsx            # RHF+Zod (D.10)
│   │   └── __tests__/
│   ├── recuperar/
│   │   ├── RecuperarView.tsx                # client root (D.11)
│   │   ├── FrozenLeadRow.tsx                # D.11
│   │   └── __tests__/
├── api/
│   ├── embudo-board.ts                      # use-embudo-board (RQ)
│   ├── embudo-server.ts                     # getEmbudoBoardInitialState (SSR)
│   ├── lead.ts                              # use-lead (RQ)
│   ├── lead-stage-mutation.ts              # use-lead-stage-mutation (RQ mutation → invalida board+lead)
│   ├── frozen.ts                            # use-frozen
│   ├── diagnose.ts                          # use-diagnose
│   ├── create-lead.ts                       # use-create-lead
│   └── _keys.ts                             # RQ keys (extend)
├── store/embudo-ui-store.ts                 # Zustand: drag state, view toggle, filtros UI
└── types/
    ├── embudo.types.ts                      # mirror DTOs (camelCase)
    └── embudo-schema.ts                     # Zod: newLeadSchema, overrideReasonSchema
```
- ❌ NO cross-feature import (`features/adrian` no importa `features/lisa|mateo|valeria`). Shared → `components/shared/`.
- ❌ NO Shadcn primitives en `features/` — solo `components/ui/`.

## Data layer (RQ + Zustand split — ADR-004 § 3.4)
- **React Query** (server): `["crm","board",{view,filters,sort}]`, `["crm","lead",id]`, `["crm","lead",id,"transitions"]`, `["crm","frozen"]`. Mutation `stage` → `invalidateQueries(["crm","board"])` + `(["crm","lead",id])`. Keys siguen `[module, subtab, action, ...filtersStable]` (`test_react_query_keys_convention`).
- **Zustand** (`embudo-ui-store.ts`): drag active id, drop target, view toggle, filtros UI ephemeral. NUNCA data fetched.
- **URL state**: `?view=kanban|lista`, `?sort=`, `?highlight={id}` vía `useSearchParams` + `router.replace()`.
- **Optimistic update**: `use-lead-stage-mutation` hace optimistic move; on 409 → rollback + refetch + toast "Este lead fue actualizado por otra persona." (SC-5). on 422 → rollback + toast salto (SC-2). on timeout → rollback + toast network (SC-7).

## Forms (RHF + Zod — ADR-004 § 3.5)
- `NewLeadPage`: `newLeadSchema` (nombre* min 1, canal* enum, teléfono ∨ email ≥1 — refine, etapa default interesado, servicio autocomplete, etiquetas, notas). Submit-driven. Toast sonner. Submit → `router.push('/adrian/embudo?view=kanban&highlight={id}')`.
- `OverrideReasonDialog`: `overrideReasonSchema` (reason required min 1). Confirmar → mutation + toast "Adrián tomó nota y ajusta su próximo paso" + mensaje de Adrián en panel Valeria (D.12). Drag→reservado: NO abre dialog, toast warn "🔒 Reservado se alcanza con el depósito".

## Drag-drop (@dnd-kit — D.13)
- `DndContext` con `PointerSensor` + `KeyboardSensor` (SC-10 a11y: Space+flechas+Esc + `aria-live` anuncia movimiento). `useDraggable` en LeadCard, `useDroppable` en PipelineColumn.
- Drop válido adyacente → mutation directa. Drop salto → OverrideReasonDialog (confirm+reason). Drop reservado → toast warn (bloqueado). Drop misma columna → no-op (RN-17: drag solo cambia columna, NO reordena dentro).
- Highlight post-create/post-move → `outline 2px primary` + `ringpulse 1.1s ×3` + auto-scroll.

## Visual fidelity (D.0–D.16 — mockup embudo-v3.html)
El builder reproduce D.0 (tokens espejo globals.css) → D.16. Wrapper shell (TopBar/Ribbon/SubTabsBar/Valeria/splitter) = **portado verbatim** del shell shipped (NO reinventar — `shell-mockup-per-component.md § wrapper fidelity`). Solo `panel-content` (board/lista/lead/nuevo/recuperar) es propiedad de la story. ScoreDonut D.5, LeadCard D.4, EntitySubNavBar D.7 verbatim.

## MSW (`mocks/handlers/embudo.ts`)
Mock board (dataset canónico §spec — 11 leads PEN), `PATCH /stage` (200/409/422), `GET /frozen` (2 frozen), `POST /reservado-side-effect` (STUB → flip deposit_status pending→received), `POST /leads`, `GET /leads/{id}`, `GET /transitions`.

## Tests (FE — RED first; base.ts anti-burbuja)
- Vitest: `LeadCard.test.tsx`, `ScoreDonut.test.tsx`, `ChannelBadge.test.tsx` (extend), `KanbanBoard.test.tsx` (drag keyboard), `OverrideReasonDialog.test.tsx`, `EmbudoHeader.test.tsx`, `LeadWorkspace.test.tsx`, `use-embudo-board.test.ts`, `use-lead-stage-mutation.test.ts` (MSW 200/409/422).
- Playwright (import `e2e/fixtures/base.ts`, NO `@playwright/test`): `embudo-board.spec.ts` (SC-1/8/9), `embudo-lead-workspace.spec.ts` (SC-detalle/deeplink/10), `embudo-nuevo-lead.spec.ts` (SC-nuevo), `embudo-override-drag.spec.ts` (SC-1b/2/5), `recuperar.spec.ts` (SC-freeze) + visual goldens light+dark (D.16 map: kanban, lead-card, lista, lead-resumen, lead-historial, nuevo, recuperar, override-dialog) + axe (SC-10).
- POMs: `EmbudoBoardPage`, `LeadWorkspacePage`, `NewLeadPage`, `RecuperarPage`.

## playwright_visual_scope
- `story_scope_routes`: `/adrian/embudo`, `/adrian/embudo/[leadId]/resumen`, `/adrian/embudo/[leadId]/historial`, `/adrian/embudo/nuevo`, `/adrian/recuperar`.
- `story_scope_components`: `features/adrian/components/embudo/**`, `recuperar/**`, `components/shared/score/ScoreDonut.tsx`, `components/shared/shell-organism/ChannelBadge.tsx` (extend), `lib/channels/channel-meta.ts`.
- `forbidden_to_touch`: `components/ui/**` (Shadcn primitives), `components/shared/shell-organism/{EntitySubNavBar,TopBarGlobal,Ribbon,SubTabsBar,ValeriaSidebar}.tsx` (reuse, NO modificar salvo bug visible), otros `features/{lisa,mateo,valeria,lucas,camila}/**`.
- `non_egoismo_clause`: si el builder ve un bug en un wrapper shipped (EntitySubNavBar, etc.) → documentar en `vitalia/docs/observed-bugs/`, NO arreglar fuera de scope.
