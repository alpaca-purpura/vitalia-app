# T-7 impl-log — FE workspace (5 leaves + pickers + autosave)

story: vitalia-fase2-lisa-servicios · ticket: T-7 · surface: frontend · agent: builder-frontend (workhorse) · phase: A
status: **DONE — GREEN + pushed** — Milestone 0 (data/hooks) + Milestone 1 (workspace UI) both committed. tsc 0 · eslint 0 · vitest 271 files/2508 tests. See `T-7-result.md`. Next ticket: T-8.

## Milestone 1 — workspace UI  ✅ DONE (committed)
Shell (`workspace/ServicioWorkspaceShell` RED→GREEN 7 tests) + `ServicioWorkspaceView` + `ServiceStatusBar` + 5 leaves (Resumen/ParaAdrian/Especialistas/PlanPago/PruebaSocial) + 3 pickers (Biblioteca/EspecialistaLink/KnowledgeSources) + FieldTooltip + N3 routes `[offer-id]/{layout,page,[leaf]/page}` (segments resumen·para-adrian·doctores·plan-pago·prueba-social) + `nuevo/page`. Composed from `@luana/ui-kit` canon. Builder stalled at tool budget mid-fix; orchestrator finalized ~16 tsc + 6 eslint + 3 arch wiring fixes (Switch/Checkbox from ui-kit · T-5 molecule prop contracts · route→public-API · canon §2.7 grid→flex). 2 upstream deficiencies flagged in result (RungPicker casing · arch-fe leaf segment naming).

## Milestone 0 — workspace data layer + hooks + DTOs  ✅ DONE (committed)
Extended the T-6 feature data layer with the full workspace surface:
- `features/lisa/api/servicios.ts` (+~470 lines): workspace hooks — `useServicioDetail`, `usePatchField` (autosave), `useActivate`, `useDiscardDraft`, `useLinkSpecialist`/`useUnlinkSpecialist`, `useRoster`, `useProcessDocument` (extract A), `useBiblioteca` (typeahead), `useCreateFromTemplate`/`useCreateCustom`, `useSalesBriefPatch`, `useTestimonial`/`useCase`, `useServicioPickerSearchFn` (EntityPicker ▾ switcher).
- `features/lisa/types/servicios.types.ts` (+131): workspace DTOs (detail, patch requests, specialist link, case/testimonial, biblioteca, extraction prefill).
- `features/lisa/api/servicios-server.ts` (+45): SSR detail fetch.
- Gates: tsc 0 · eslint 0 · vitest 772/772 (orchestrator-verified after builder stalled at tool budget; fixed 3 trivial leftovers: `useRef` import, cursor null-coalesce, unused `PAGE_SIZE`).

## REMAINING (workspace UI — next session resume)
Build order (commit each green milestone by pathspec):
1. **Shell:** `ServicioWorkspaceView` (crear=editar RN-16) = `EntityWorkspaceLayout` + `EntitySubNavBar` (5-leaf nav, root-pill ‹ Servicios leaf-peer, `EntityPicker` ▾) + `ServiceStatusBar` (Activo Switch + chip-origen + FichaCompletenessChip + N-especialistas statuslink) + `use-autosave` hook (600ms, ONE FloatingAutosaveIndicator) + routes `app/[tenantId]/(shell-organism)/lisa/servicios/[offer-id]/{layout,page,[leaf]/page}.tsx`. → makes the stashed RED test GREEN (see `_t7-red-stash/ServicioWorkspaceShell.test.tsx.txt`, rebuild RED-first).
2. **Leaves A:** `ResumenView` (6 grupos: Identidad[RungPicker locked-if-estándar RN-30 · ChipOrigen · categoría Select disabled-if-estándar] · Qué es[voz-marca badge · VariantsRepeater] · El procedimiento · Resultados · Riesgos[safety banner] · Modalidad y agenda[ModalidadPicker discriminated · NumberWithUnit · RichSelect tipo-cita]) + `ParaAdrianView` (FaqPairList · ObjecionPairList · TagInput keywords + textareas + contraindicaciones/escalada safety).
3. **Leaves B:** `EspecialistasView` (linked list + `EspecialistaLinkPicker` roster-checklist autosave-on-mark + "Ver detalle ↗" deep-link + Desvincular) · `PlanPagoView` (3 cobros + calculated read-only + moneda read-only tooltip RN-23) · `PruebaSocialView` (TestimonialsList + Case uploader consent-gate RN-33).
4. **Create flow:** `BibliotecaPicker` (inline typeahead name+synonyms · template/personalizado · ↻ volver) + `app/.../lisa/servicios/nuevo/page.tsx` + `KnowledgeSourcesPanel` (extract-only · "Procesar con Lisa" prefill ✨ · RAG toggle DISABLED = Sub-phase B gated).
5. `FieldTooltip` (Shadcn Tooltip wrapper RN-18 dotted underline).

All T-5 primitives + T-6 data layer are committed & consumable. validator_ids pending: AC-2, RN-16, RN-18, RN-20, RN-23, RN-26, AC-4, AC-4.bis, AC-5, AC-11, AC-13, AC-14, AC-18.

## Then T-8 (separate): vitest+playwright real-backend + a11y + visual goldens 8 + BE pytest dual-tenant + arch + LIVE-VERIFY (DoD #37 · needs migration 045 applied to dev DB + dev-app-vitalia + Chrome MCP).
