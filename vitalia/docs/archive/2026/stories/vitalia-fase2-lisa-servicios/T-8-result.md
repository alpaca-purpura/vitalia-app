# T-8 result — tests + arch + (live-verify BLOCKED)

story: vitalia-fase2-lisa-servicios · ticket: T-8 · surface: backend+frontend · production_code: false · phase: A
status: **DONE (core) — test battery GREEN+pushed · LIVE-VERIFY (DoD#37) core happy-path verified live 2026-06-16 → story `developed` · AWAIT_CHRIS_VERIFY (funcional). 3 secondary findings open (see § UPDATE).**

## UPDATE 2026-06-16 — LIVE-VERIFY DONE (core happy-path) · Chrome MCP via LUANA_LANE=A

Chris reset the Chrome MCP env (`export LUANA_LANE=A` + killed stale `chrome-devtools-mcp`). Live-verify run vs `dev-app.vitalialat.com` (Chrome DevTools MCP, dr.demo owner, tenant Sanaré LATAM):

**2 blocking bugs caught + fixed (commit `9884d313`):**
1. `POST /offer/servicios/custom → 500 'relation products does not exist'` — offer module persists offer-core via engine `OfferRepository` (D-1) but no migration ever created the engine offer-studio tables in vitalia's DB (045 deferred `products` to "keystone", never built; BE tests passed on metadata.create_all test DB). → **migration 046** materializes the 6 engine tables (`metadata.create_all(checkfirst=True)`, idempotent, FK-ordered).
2. Workspace **resumen leaf crashed** (`useFormContext()` null) — ui-kit `RichSelect` hard-renders `<FormControl>` which needs a shadcn `<Form>` stack, but the leaf uses bare `<Controller>`. → replaced RichSelect with plain ui-kit `Select` (same label+description UI, no form context). (ui-kit forbidden to edit.)

**3 real writes verified live (DB + BE logs):**
- CREATE `POST /custom → 201` → `products` row (status=draft, ARS 8000).
- AUTOSAVE name `PATCH → 200` → DB `products.name` updated.
- ACTIVATE `POST /activate → 200` → `status=active` + `growth_studio_event: service_activated`.
- KEYSTONE AC-6: active offer in engine `products` (tenant-scoped — table `build_identity` reads) + unit `test_keystone_offer_shape.py`.
Evidence: `checkpoint.md::dod_evidence` + `.live-verify/*.png`.

**3 open findings (→ chris_verify triage / reconcile / auditor):**
- **F1 (medium · wiring):** `ServiceStatusBar` orphaned — `layout.tsx` mounts `ServicioWorkspaceShell` directly (not `ServicioWorkspaceView`), so the workspace has no Activo toggle / chip-origen / completeness chip. Activate works via the catalogo card. RN-10/AC-19 partial in workspace.
- **F2 (HIGH · BE contract / architect gap):** `ServicePatchRequest` only accepts `{public_name, price, category, modality}`. The rich ficha fields (descripción, qué incluye, procedimiento, resultados, riesgos, cuidados — RN-26 §6 "ficha completa editable") are unwired placeholder textareas because the offer domain/DTO doesn't model them. Not a builder bug — the contract needs extending.
- **F3 (low):** `appointment_type` (RN-32 tipo de cita) doesn't persist (no BE field).

**Still pending (technical, not demo):** visual goldens 8 (project=visual 0.001) — not generated; real render verified live instead. Sub-phase B (RAG) gated /pm-luana.

---
### (earlier this ticket — pre-live-verify)

## ✅ DONE + GREEN + pushed

### FE vitest (commit 995ba147)
5 leaf tests (ResumenView 8 · ParaAdrianView 6 · PlanPagoView 7 · PruebaSocialView 9 · EspecialistasView 6) + 3 picker tests (BibliotecaPicker 7 · EspecialistaLinkPicker 9 · KnowledgeSourcesPanel 8). **Full FE suite: 279 files / 2568 tests GREEN** · tsc 0 · eslint 0.

### BE pytest + arch (commit 995ba147)
- `offer/` module suite GREEN (121 tests from T-1..T-4 — dual-tenant, RBAC 403, case consent gate, keystone offer-shape covered).
- NEW arch test `test_offer_no_engine_edit.py` GREEN (offer consumes engine ONLY via `luana_core_platform.links.ports.offer`, no direct `luana_core_offer_studio.domain` import).
- BE arch suite GREEN **except 1 pre-existing OUT-OF-SCOPE failure** (`test_pgcrypto_phi_columns`: `treatment_plans.notes` TEXT not BYTEA — **fidelizacion** module, PHI encryption tech debt, NOT offer/lisa-servicios; never touched by this story). → route to CIL L3 tech-debt.

### Playwright real-backend specs + POMs (commits 995ba147, f73ccf03)
4 specs (crear · autosave · especialistas · escalera-drag) + 4 POMs + visual golden spec authored. Registered in `playwright.config.ts` (smoke project testMatch — were orphan/no-project). Fixed fixture/POM import depth (`../../`→`../`). Migration 045 confirmed at head in dev DB.

## ❌ LIVE-VERIFY (DoD #37) — BLOCKED (honest, not faked)

`verification_nature: ambas` + `demo_required: true` → Step 4.6 is a HARD gate. It is NOT met. Two independent blockers:

### Blocker 1 — Chrome DevTools MCP environment collision (HB-73 recurrence · environment, needs Chris)
The canonical funcional live-verify (Chrome DevTools MCP vs dev-app.vitalialat.com) is unusable: the `luana-vitalia-solo` MCP profile is held by competing chrome-devtools-mcp **server instances** (overlapping sessions). Tool calls alternate between two unrecoverable errors:
- `Protocol error (Browser.setContentsSize): Restore window to normal state before setting content size` (one instance, bad window state)
- `The browser is already running for .../luana-vitalia-solo. Use --isolated` (the other, can't attach)
`isolatedContext` + lock clearing + killing the chrome tree all failed (a live MCP server keeps respawning chrome). Env vars (`LUANA_LANE`) are fixed at session start → cannot reset from inside. **Fix (Chris):** `export LUANA_LANE=<unique>` before launching claude (per HB-73) + kill stale `chrome-devtools-mcp` processes, then resume.

### Blocker 2 — Playwright create-flow POMs assume modal dialog; real flow is inline route
Pivoted to Playwright real-backend (separate browser, NOT blocked by MCP). The dev stack authenticates + renders LIVE (preflight READY; **2/5 `crear` scenarios passed** against localhost:3002 with Clerk storageState — auth + nav + render confirmed working). But the create-flow POMs (`ServiciosCatalogoPage.openNuevoServicio`) wait for `getByRole('dialog', {name:/Nuevo servicio/i})` — there is NO dialog: per RN-16/25 the create flow is an **inline route** (`/lisa/servicios/nuevo` → `BibliotecaPicker` inline). Builder authored POMs without running against the live app (the specs carried a stale `★ STACK-STATUS: PENDING-LIVE-VERIFICATION` + a non-existent `--project=shell` hint). Real write evidence not yet captured.

**Remaining for `developed` (next session):**
1. Resolve Chrome MCP env (Chris) OR finish via Playwright.
2. Rework create-flow POMs to the inline-route reality (+ add `data-testid` to BibliotecaPicker/NuevoServicioPage/workspace leaves as needed — test-enablement).
3. Run crear/autosave/especialistas specs → exercise a REAL write (create servicio + activate + autosave PATCH) → read BE docker logs (`luana-dev-vitalia_backend_dev-1`) confirming POST/PATCH `/api/v1/offer/servicios` + DB rows.
4. Generate 8 visual goldens (project=visual, 0.001) against the 4 mockups.
5. KEYSTONE AC-6 live: activate servicio → confirm it enters `TenantKnowledgeBuilder.build_identity` (Adrián cites it).
6. Record `dod_live_verified: true` + `dod_evidence` in checkpoint → then `developed` → auditor.

## Skills consulted (must_load enforcement v4.1)
playwright-expert (preflight + project registration) · frontend-expert · backend-expert (pytest) · test-design-doctrine (coverage by nature) · tdd-mandatory · definition-of-done-live-verify (the gate — honored, not bypassed) · tenant-isolation · hipaa-lite.

## § Harness HB candidates (CIL L1)
1. **HB — Chrome DevTools MCP multi-instance collision** (recurrence of HB-73): overlapping sessions spawn duplicate `chrome-devtools-mcp` servers on the same `luana-vitalia-solo` profile → both unusable; no in-session recovery. Need a lane-guard / pre-flight that detects + refuses, or per-session profile that doesn't require `LUANA_LANE` set before launch.
2. **HB — builder-frontend authors Playwright POMs/specs without running them live** (recurrence of the embudo "imagined contract" class, HB-42): POMs assumed modal dialog vs inline route; specs referenced a non-existent project + wrong import depth + orphan (no project testMatch). A real-backend e2e authored blind is a false artifact. Candidate gate: builder must run ≥1 authored spec against the live stack before claiming the e2e ticket.
