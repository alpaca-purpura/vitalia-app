# T-6 result — FE · catálogo + escalera + N3 routing + feature data layer

story: vitalia-fase2-lisa-servicios · ticket: T-6 · surface: frontend · agent: builder-frontend (workhorse · 2 continuations) · phase: A

## Verdict: GREEN (closed by orchestrator gate-run after builder hit tool budget pre-vitest)

## Scope delivered
- **Data layer:** `features/lisa/api/{servicios.ts (client · fetchClient → /api/v1/offer/*), servicios-server.ts (SSR)}`, `hooks/use-servicios-filters.ts`, `store/servicios-ui-store.ts` (Zustand UI-only), `types/{servicios.types.ts (mirror BE DTOs), servicios-schema.ts (Zod), servicios-labels.ts}`.
- **Routing (N3-static · ADR-vitalia-004 §3.1.1):** `lib/shell-routes.ts` APPEND `AGENT_SUBSUBTABS['lisa']['servicios'] = [catalogo, escalera]` + N3 default. `app/[tenantId]/(shell-organism)/lisa/servicios/{page.tsx (redirect default), [subsubtab]/page.tsx (Server Component SSR)}`.
- **Components:** `LisaServiciosView` (client root), `ServiciosDirectoryHeader` (title+search+filters[especialidad·activo·origen]+"+ Nuevo" nav), `CatalogoView` (grid + Skeleton + EmptyState invites biblioteca · AC-7), `ServiceCard`, `EscaleraView` (5 fixed médico rungs · layout full/3col/full per mockup) + `RungColumn` (filled cards+"crear aquí" / empty guía+biblioteca · AC-3/RN-2), @dnd-kit drag→`useMoveRung` (value_level autosave) · **KeyboardSensor WITH coordinateGetter** (a11y · the known silent-break bug averted) · estándar-origin LOCKED rung (RN-30).
- **Tests:** `__tests__/{CatalogoView,EscaleraView,ServiceCard}.test.tsx`.

## Canon divergence (documented for auditor)
- **ServiceCard = bespoke `<article>` composing ui-kit atoms** (Card/Badge/Avatar/Switch/DropdownMenu), NOT `EntityInfoCard`. Rationale: the ratified mockup footer (avatar-stack + ChipOrigen + Activo Switch) does not fit EntityInfoCard's closed `status` slot. Stayed under the no-div-layout ratchet via `space-y` / responsive `sm:flex` / grid token (no raw `flex-col gap` / `grid-cols`). Round-3 simplified card (no rung badge).

## Reconciliations (CONTEXT-BRIEF §11)
- escalera KeyboardSensor uses `sortableKeyboardCoordinates` coordinateGetter (the embudo a11y silent-break pattern, averted).
- useTenantId() for tenant_id — never useAuth().orgId (arch-test enforced).

## Gate results (orchestrator-run after builder stalled at "Now full vitest")
- `npx tsc --noEmit` → 0 errors
- `npx eslint src/features/lisa src/app` → 0 (builder-reported GREEN)
- `npx vitest run src/features/lisa src/__tests__/architecture` → **772/772 PASS** (91 files · incl div-layout ratchet, no-clerk-organizations, agent-subsubtabs-ssot, FSD boundaries). One caught happy-dom fetch-error path (test passes).

## Skills consulted (must_load enforcement v4.1)
frontend-expert ✅ · vitalia-design-system ✅ · frontend-visual-fidelity ✅ (canon §0/§2.7 + ServiceCard divergence) · frontend-fsd ✅ · playwright-expert ✅ (T-8 deferred) · spanish-text ✅ · tenant-isolation ✅ (useTenantId) · anti-duplication ✅ · tdd-mandatory ✅ · ADR-vitalia-004 ✅ (N3-static routing).

## Engine boundary
CERO edit @luana/ui-kit/src · components/ui untouched · shell-organism untouched · shell-routes APPEND-only · BE consumed via api client only.

## Remaining for T-7
The `[offer-id]` workspace + 5 leaves + pickers + autosave + knowledge panel (extract-only). "+ Nuevo" currently navigates; T-7 builds the workspace.

done -> T-6-result.md
