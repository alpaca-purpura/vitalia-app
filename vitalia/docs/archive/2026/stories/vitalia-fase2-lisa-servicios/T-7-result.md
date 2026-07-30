# T-7 result — FE workspace (shell + 5 leaves + pickers + autosave)

story: vitalia-fase2-lisa-servicios · ticket: T-7 · surface: frontend · agent: builder-frontend (workhorse) + orchestrator finalize · phase: A
status: **DONE — GREEN + pushed** (Sub-phase A FE workspace complete; T-8 next)

## What was built (workspace UI · milestone-0 data layer already committed in 10557a2f)

| File | Acción |
|---|---|
| `components/servicios/workspace/ServicioWorkspaceShell.tsx` | NEW — EntityWorkspaceLayout + EntitySubNavBar (root-pill ‹ Servicios + EntityPicker ▾ + 5 leaves) |
| `components/servicios/ServicioWorkspaceView.tsx` | NEW — client root (ServiceStatusBar + shell · crear=editar RN-16) |
| `components/servicios/ServiceStatusBar.tsx` | NEW — Activo Switch (AC-19 nunca bloqueado) + ChipOrigen + FichaCompletenessChip |
| `components/servicios/leaves/ResumenView.tsx` | NEW — 6 grupos (Identidad·Qué es·Procedimiento·Resultados·Riesgos·Modalidad-y-agenda) · RHF+Zod discriminated · autosave |
| `components/servicios/leaves/ParaAdrianView.tsx` | NEW — argumentario · FaqPairList · ObjecionPairList · TagInput · safety |
| `components/servicios/leaves/EspecialistasView.tsx` | NEW — linked list + EspecialistaLinkPicker (roster checklist, autosave on-mark) |
| `components/servicios/leaves/PlanPagoView.tsx` | NEW — 3 cobros (RN-6) + derived read-only + moneda read-only |
| `components/servicios/leaves/PruebaSocialView.tsx` | NEW — testimonios (read-only list + add form) + casos consent-gate (RN-33) |
| `components/servicios/BibliotecaPicker.tsx` | NEW — inline typeahead (plantilla/personalizado · NO modal RN-16/25) |
| `components/servicios/EspecialistaLinkPicker.tsx` | NEW — roster checklist autosave-on-mark |
| `components/servicios/KnowledgeSourcesPanel.tsx` | NEW — extract-only ✨ (RAG toggle DISABLED · Sub-phase B gated) |
| `components/servicios/FieldTooltip.tsx` | NEW — Shadcn Tooltip wrapper (RN-18 dotted underline) |
| `components/servicios/__tests__/ServicioWorkspaceShell.test.tsx` | NEW — RED→GREEN locked shell contract (7 tests) |
| `app/[tenantId]/(shell-organism)/lisa/servicios/[offer-id]/{layout,page,[leaf]/page}.tsx` | NEW — N3 routing (5 static leaves) |
| `app/[tenantId]/(shell-organism)/lisa/servicios/nuevo/page.tsx` | NEW — BibliotecaPicker create flow |
| `features/lisa/index.ts` | MODIFY — workspace public API exports + `getServicioDetail` |

Leaf segments: `resumen · para-adrian · doctores · plan-pago · prueba-social` (labels Resumen/Para Adrián/Especialistas/Plan de pago/Prueba social). Consume committed T-5 moléculas + T-6/T-7-m0 data layer (api/servicios.ts hooks + servicios.types.ts). `useTenantId()` (never orgId). Composed from `@luana/ui-kit` canon (EntityWorkspaceLayout/EntitySubNavBar/EntityPicker/Group/Switch/Checkbox/FloatingAutosaveIndicator).

## Gate output (literal)

```
npx tsc --noEmit        → exit 0
npx eslint (servicios + app/servicios + hooks) → exit 0
npx vitest run (FULL FE suite) → 271 files passed · 2508 tests passed (exit 0)
  ├─ ServicioWorkspaceShell.test.tsx → 7/7 (shell contract RED→GREEN)
  ├─ arch test_no_cross_feature_imports (FE-A4) → pass (route pages use @/features/lisa public API)
  └─ arch test-no-div-layout (canon §2.7 ratchet) → pass (303→301; new form-rows use flex, not grid-cols)
```

## Orchestrator finalize note (builder continuation)

`builder-frontend` (sonnet) built all files but hit tool budget mid-fix ("Multiple errors…", agentId af855dca4be646277). Orchestrator (no SendMessage available) continued per continuation pattern — partial work was in tree, no commits lost. Fixed ~16 tsc + 6 eslint + 3 vitest (arch) wiring issues directly:
- Switch/Checkbox imported from `@luana/ui-kit` (canon), not `@/components/ui/*` (not installed there).
- T-5 molecule prop contracts wired correctly (ChipOrigen `origen`, FichaCompletenessChip `title`, FaqPair/ObjecionPair wire↔local mapping, TestimonialsList replaced by read-only inline list since ServiceTestimonial has `rating`/`text` the molecule doesn't render).
- RungPicker UPPERCASE↔lowercase casing bridge in ResumenView.
- Route pages → feature public API; canon §2.7 form-rows `grid grid-cols-2` → `flex gap-3 [&>div]:flex-1`.

## Skills consulted (must_load enforcement v4.1)

| Skill / Rule | Status | When |
|---|---|---|
| frontend-expert · frontend-fsd · frontend-visual-fidelity | ✅ | build + finalize (FSD boundary, canon) |
| vitalia-design-system · design-system-canon.md | ✅ | compose @luana/ui-kit primitives |
| ADR-vitalia-004 (shell-feature) | ✅ | N3 routing + leaf segments |
| tenant-isolation (FE) | ✅ | useTenantId, no orgId, no PHI in URL |
| spanish-text · currency-handling | ✅ | neutro copy · currency from data |
| tdd-mandatory · playwright-expert | ✅ | shell RED test first; e2e deferred to T-8 |
| anti-duplication | ✅ | consume ui-kit canon (no primitive recreation) |

## § Upstream deficiency (route to architect/CIL — auditor to confirm)

1. **RungPicker (T-5) enum casing diverges from data layer.** `RungPicker.tsx::OfferValueLevel` is UPPERCASE (`LEAD_MAGNET`…) while canonical `types/servicios.types::OfferValueLevel` (= wire) is lowercase (`lead_magnet`…). ResumenView bridges via `.toUpperCase()`. T-5 should consume the canonical lowercase type. Low severity (display only; onChange is the documented value_level no-op). Candidate: harden RungPicker in T-8 or a follow-up.
2. **03-arch-fe §1 wrote leaf segment `especialistas`; locked shell test uses `doctores`.** Test won (it is the RED-first contract); routes use `doctores`. Arch doc to be reconciled in R.

## Remaining (T-8)
BE pytest dual-tenant + mutation + RBAC/consent/keystone · arch fitness EXTEND · FE leaf/use-autosave vitest + Playwright real-backend (auth fixture + base.ts anti-burbuja) + a11y axe + visual goldens 8 (4 mockups × light/dark · 0.001) + LIVE-VERIFY DoD #37 (migration 045 → dev-app → Chrome MCP writes).
