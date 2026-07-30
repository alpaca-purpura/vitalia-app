# T-FE-2 result — Board (Kanban+Lista) + LeadCard + drag override + OverrideReasonDialog

> **Nota orquestador:** el builder-frontend completó la implementación (21+ tests GREEN) pero el agent cortó justo antes de correr la suite full + escribir este result. El orquestador (a) verificó gates en el hub, (b) aplicó UN fix mecánico (TS2352: `error as unknown as ApiErrorLike` en `use-lead-stage-mutation.test.ts` líneas 77/87 — cast a través de `unknown`), (c) confirmó GREEN, (d) commiteó por pathspec.

## Estado
`tests-passing` — tsc 0 · eslint 0 · vitest **53/53** (adrian/embudo + api).

## Archivos (in-place hub)
NEW:
- `features/adrian/components/embudo/{KanbanBoard,PipelineColumn,LeadCard,OverrideReasonDialog}.tsx` + `__tests__/`
- `features/adrian/api/{_embudo-keys,embudo-board,embudo-server,lead-stage-mutation}.ts` + `__tests__/{use-embudo-board,use-lead-stage-mutation}.test.ts`
- `features/adrian/store/embudo-ui-store.ts` (Zustand UI state — filtros/vista)
- `app/[tenantId]/(shell-organism)/adrian/embudo/page.tsx` (+ scaffolding `[leadId]/{page,resumen,historial}`, `nuevo/page.tsx`, `../recuperar/page.tsx` — stubs que T-FE-3 completa)

MODIFIED:
- `features/adrian/index.ts` (export embudo public API)

## Decisiones
- Componentes en `features/adrian/components/embudo/` (consistente con `features/adrian/components/inbox/`, NO `features/crm/` — sigue convención del codebase donde los componentes viven en el feature del agente).
- Drag override con @dnd-kit (PointerSensor + KeyboardSensor a11y); soltar en otra columna → `OverrideReasonDialog` (RHF) → `useLeadStageMutation` PATCH /stage (optimistic + 409/422 handling, SC-5/SC-2).
- React Query keys en `_embudo-keys.ts`; server prefetch en `embudo-server.ts` (Server-First); Zustand SOLO UI state.

## Skills consulted (must_load v4.1)
| Skill/Rule | Status |
|---|---|
| frontend-expert · vitalia-design-system | loaded |
| frontend-fsd · frontend-visual-fidelity · spanish-text · tenant-isolation · tdd-mandatory | loaded |

## Pendiente (otros tickets)
- Visual goldens (D.16 map) + axe + POMs e2e → T-E2E-1.
- Lead page Resumen/Historial real + nuevo lead real + Recuperar real → T-FE-3 (T-FE-2 dejó stubs de ruta).
