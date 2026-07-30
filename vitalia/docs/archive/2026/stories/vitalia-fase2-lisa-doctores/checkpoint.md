---
story_id: vitalia-fase2-lisa-doctores
type: ui-story
agent_owner: lisa
map_zone: agentes
map_box: lisa
module: clinics
capability: lisa.doctores
state: done                            # ★ MERGE 2026-06-12 (autonomous run completo) · delta v3 COMPLETO 12+5 tickets · Step 4.5 41/41 · Step 4.6 GREEN · 2026-06-11 REANUDADA ratificado Chris (gate shell-core-hardening DONE 2026-06-11) + scope extension entity-switcher folded (ver scope_extension_2026_06_11)
prior_state_before_park: developing
unparked_at: 2026-06-11T21:30:00-05:00
parked_at: 2026-06-10T00:00:00-05:00   # histórico
parked_reason: "Pausa ratificada Chris 2026-06-10 para liberar bucket clinics al build de vitalia-shell-core-hardening (consolidación chrome + lift @luana/ui-kit). ⚠️ KEYSTONE REGRESIÓN QUEDA VIVA en dev: /lisa/staff crashea (Maximum update depth — NuevoIntegranteModal.tsx:109-114 useEffect loop). NO es chrome (bug de feature Lisa) → NO lo cubre el hardening. Reanudar = primer trabajo post-hardening: fix modal TDD RED-first + live-verify FULL surface (5-day shell drift se vuelve mayor post-hardening → re-verify obligatorio contra el chrome nuevo)."
defer_audit: false
defer_audit_resolved_at: '2026-06-01'
defer_audit_resolution: >-
  Blocker del defer (fix de producción del dual-mount del shell) RESUELTO y mergeado
  a done 2026-06-01 (story vitalia-shell-dual-mount-a11y-fix, merge c9d2bd31:
  single-main + single-slot, live-verify GREEN, axe 0 duplicate-id/landmark).
  Reabierta reviewing→developing para el trabajo dev remanente: (1) fix doctors-500
  keystone (BE 422 guard UUID headers + FE useClinicId sin fallback Clerk-org +
  arch-test tightening — decisión Chris 2026-06-01), (2) quitar workaround POMs,
  (3) verificar asserts reales destrabados, (4) fix perf, (5) flujos workspace/calendar
  + i18n, (6) visual goldens → project=visual (requiere ratify Chris), (7) live-verify
  real → cap lisa.doctores + auditor. Work order detallado en chris-input.md.
architecture_pattern: ADR-vitalia-004
last_modified: '2026-06-07T02:53:00Z'
ready_package_by: /architect (Opus 4.8)
ready_package_at: '2026-05-31'
autonomous_mode: true
e2e_live_run: pending_stack  # specs written (3bce844c); live verify needs stack up + zustand fix + ADR-008 dev_app deploy
adr_004_compliance: full
ready_artifacts:
  - 03-arch.md
  - 03-arch-be.md
  - 03-arch-fe.md
  - 04-validators.yaml
  - 05-guidelines.md
  - 06-tickets.yaml
  - dispatch-plan.md
prior_art_scan_done: true
ratified_by_chris: true
ratified_visual_by_chris: true
parallel_safe: true
priority: high
estimated_dev_days: 3-4
dependencies:
  hard:
    - vitalia-fase1-empty-states
    - vitalia-fase1-routing-shell
  soft:
    - vitalia-fase2-lisa-marca
blocks_hard: []
blocks_soft:
  - vitalia-fase2-valeria-agenda
  - vitalia-fase2-lisa-servicios
model_mandate_2026_06_12: "★ ACTUALIZADO Chris 2026-06-12 ~00:40 (verbatim: 'los siguientes builders hazlos con sonnet, se están gastando muy rápido mis tokens, fable solo el auditor al final'): builders → SONNET · auditor final → FABLE 5. Histórico: architect + 3 primeros builders (T-CORE/occurrences-BE/switcher-FE) corrieron Fable 5 bajo el mandato original."
chris_verify:
  required: true
  signoff:
    by: Chris
    date: 2026-06-12
    result: SATISFIED_WITH_FOLLOWUPS
    notes: "Pre-autorizado verbal (chris-input 01:40: 'no esperes nada de mí, continúa hasta el done') — corrida autónoma ratificada en vivo durante la noche (rondas 1-6 de feedback + 'doy por aprobado todo')."
    open_items: ["self-test live con demo-script.md (14 pasos)", "ratificar goldens V-VIS-1..4 (ADR-003)"]
  rounds: ["delta v3 FIRMA 1 (3 ítems AskUserQuestion)", "v3.1 página en story + perfil rico + estado-driven", "v3.2 dominio env + sin CTA + Doctoralia + idiomas condicional", "FIRMA 2 'doy por aprobado todo'", "occurrences repro + vista mes + editor Google (ronda 5-6)"]
reconciled: true   # spec § Delta v3.0-3.2 + ledger + cap = realidad construida (reconciliación continua durante el run)
auto_chain_2026_06_12: "Chris: al terminar architect → /dev-team → /auditor (ambos fable). G (chris_verify) sigue vigente — autonomous hasta developed, pausa AWAIT_CHRIS_VERIFY salvo que checkpoint diga autonomous_mode true (está true — PERO el delta incluye goldens/demo: G aplica igual por demo_required true)."
dod_live_verified: true
dod_env: "localhost:3002 (Playwright headless storageState Clerk real · tenant sanare-latam-mx · dr.demo) — dev-app tunnel UP equivalente"
dod_evidence:
  - action: "Switcher: doctor abierto en Horarios → picker ▾ → buscar → elegir otro doctor (T-FE-switcher-wire builder)"
    observed: "URL /staff/{otro}/horarios — hoja PRESERVADA + contenido renderiza + e2e SC-D3A 6/6 real-backend"
    backend_log: "GET /clinics/doctors?q= 200 · 0 console errors"
  - action: "Recurrencia bug Chris: bloque weekly occurrences=2 creado vía UI real (T-FE-occurrences-consume builder)"
    observed: "calendario pinta EXACTAMENTE 2 semanas — semanas: 0,1,1,0 (semana 4 vacía; antes: infinito). Bloque test borrado"
    backend_log: "GET availability-occurrences 200 por rango · delete {deleted:true}"
  - action: "Editor Google: drag-create → Personalizado (interval=2 + chips L+J + después de 8 reps) → guardar → eliminar (orchestrator live)"
    observed: "resumen humano EXACTO 'Se repite cada 2 semanas el lunes y jueves, 8 veces' + pinta semana/mes + delete limpio"
    backend_log: "POST /availability-blocks 201 (daysOfWeek/interval) · GET occurrences 200 · 0 errors"
  - action: "Bio-docs: PDF real subido vía dropzone hoja Página (orchestrator live)"
    observed: "POST assets/upload 200 + register 201 + fila renderiza (nombre/tamaño/fecha) — destapó 3 capas latentes (URL fantasma + FK engine + tabla assets ausente) hoy fixeadas"
    backend_log: "POST /api/v1/vitalia/assets/upload 200 · POST bio-files 201 · GET bio-files 200"
  - action: "Página pública: generar perfil (write) + Publicar (PATCH visibleEnLanding) + abrir /d/sanare-principal/dra-ana-garcia-mendoza SIN auth viewport 390x844"
    observed: "200 + og:title/description/image presentes + badge Colegiatura 12345 (PE) + Consultorio Sanaré LATAM + sin CTA/stats + slug inexistente y toggle-OFF → 'Perfil no disponible' idéntico (anti-enum) + sin overflow-x mobile"
    backend_log: "POST generate-profile 200 (LLM down → fallback extractivo, graceful) · PATCH 200 · GET público 200 · public_profile+bio_generated_at+public_slug persistidos (DB verificado)"
verified_at: 2026-06-12
phase: MERGED
prework_reverify_2026_06_12:
  # ★ parked_reason exigía re-verify FULL surface vs chrome nuevo post-hardening
  done: true
  evidence: "Playwright headless autenticado (storageState fresco 06-11) localhost:3002 tenant sanare: directorio 4 cards → perfil (Identidad+Contacto) → horarios (calendar renderiza) → servicios. 0 pageerror/console-error, 0 HTTP>=400, 0 'Maximum update depth' (regresión modal CONFIRMADA fixed). Screenshots /tmp/staff-reverify*.png"
  verified_at: 2026-06-12T02:30:00-05:00
scope_extension_2026_06_11:
  # ★ Delta v3 ratificado Chris 2026-06-11 — FIRMA 1 funcional (AskUserQuestion ×3) · spec § "Delta v3" appended
  delta_spec_section: "01-spec.md § ★ Delta v3"
  firma_1_funcional: true            # 3 ítems ratificados vía AskUserQuestion 2026-06-11
  firma_2_mockup: true               # ★ FIRMA 2 Chris 2026-06-12 ("doy por aprobado todo para que pases a architect") — mockup v3.2 Doctoralia + picker verificado headless
  items:
    - slug: entity-switcher-n3
      ratified: "canon §2.4 tal cual — preserva hoja actual al cambiar"
      note: >-
        EntityPicker YA EXISTE en core/@luana/ui-kit (core-ds-foundation T-6, canon §2.4) —
        el "acuerdo de los mockups" que Chris recordaba ES el design-system-canon (2026-06-08).
        Falta: integrarlo a EntitySubNavBar (chip estático hoy) vía prop opcional (EXTEND core →
        promotion proposal liviana /pm-luana) + cablear doctores 1er consumidor real
        (GET /clinics/doctors?q= existente; navegar preservando hoja).
    - slug: bio-docs-upload-funcional
      ratified: "funcional completa ahora (no solo visual)"
      note: >-
        Audit 2026-06-11: BioRepoInputs dropzone onFilesChange NO-OP (archivos no persisten),
        sin lista de subidos, DoctorDetail sin bioFiles; <textarea>/<button> crudos (D1);
        emojis autosave inline (viola canon §2.6). Delta: subida REAL a R2 (proxy assets,
        patrón useAvatarUpload) + lista filas (icono tipo/nombre/tamaño/fecha/descargar/eliminar)
        + estados subiendo/error/empty + homologación átomos + contrato BE bioFiles[] + DELETE.
    - slug: horarios-casuistica-recurrencia
      ratified: "revisar TODA la casuística desde cero — tests muy detallados"
      repro_evidence:
        repro_verified: true
        reproduced_local: false
        trace_evidence:
          source: chris-live-dev-app + code-inspection
          ref: "occurrences=2 repite indefinido · root cause CONFIRMADO: AvailabilityCalendar.tsx::recurrentBlockVisibleInWeek (~L93-115) ignora occurrences (solo evalúa end_date, retorna true siempre) — BE projection rrule(count) CORRECTO. Render FE, no BD. Spec § D3-C.1"
    - slug: horarios-recurrencia-google-editor
      ratified: "Chris 2026-06-12 ronda 6 — editor de recurrencia clon Google Calendar (repetir cada N + chips días específicos L-D + termina nunca/fecha/N-repeticiones + resumen humano) + display ocurrencias con resumen del patrón. Dominio: days_of_week lista + interval (migración compat). Spec § D3-F"
    - slug: horarios-vista-mes
      ratified: "Chris 2026-06-11 ronda 5 — vista de mes NEW (hoy solo week grid); consume proyección BE (mata expansión client-side, coherente con fix D3-C)"
      note: >-
        Sospecha Chris: occurrences no respetado en calendario. Código: lógica SÍ existe en
        availability_projection_service.py → bug sutil probable. Mandato: repro live sistemático
        8 casos (semanal×N exacto, quincenal×N=14d, end_date inclusivo, open_ended ventana,
        edición sin reinicio, solape puntual+recurrente, borrado total, TZ midnight) + batería
        exhaustiva proyección + regression RED first si confirma. Cero cambio visual.
  ready_package_delta_required:
    - "03-arch delta: contrato prop picker core + cableado vitalia + contrato BE bioFiles + reconcile ubicación EntitySubNavBar (arch dice shell-organism local; HOY vive en core/@luana/ui-kit post-lift)"
    - "04-validators BACKFILL schema v5/D-X4: verification_nature + technical_gates + demo_required + business_rules + regression_guard (audit /pm-vitalia 2026-06-11: ausentes, schema v4.1 pre-proceso-v5) + validators D3-A/B/C"
    - "06-tickets: tickets nuevos T-FE-switcher + T-FULL-bio-docs + T-FULL-pagina-publica (route /d/ + perfil estructurado BE) + T-FIX-horarios-occurrences (regression RED first) + T-FE-vista-mes + assignment per ticket"
reuse_map_summary: >-
  REUSE patients+staff models shipped · NEW UI CRUD perfiles + N3-dyn workspace
  [doctor-id] · NEW personal-branding bio + horarios + KPIs · doctors-as-faces
  preview
spawned_at: 2026-05-22T00:00:00.000Z
next_action: "★ RESUME 2026-06-11 (orden ratificado Chris): (1) /po-ux mini-round delta entity-switcher (spec § + mockup patch N3 dropdown-open, firma Chris — ADR-003) → (2) /architect delta: switcher arch (EXTEND EntitySubNavBar core prop opcional + proposal /pm-luana) + BACKFILL 04-validators a schema v5/D-X4 (verification_nature/technical_gates/demo_required/business_rules/regression_guard — audit 2026-06-11) + reconcile ubicación EntitySubNavBar (hoy core/@luana/ui-kit) + ticket T-FE switcher → (3) /dev-team resume: re-verify FULL surface /lisa/staff contra chrome nuevo (parked_reason flaggea drift post-hardening; regression modal marcada FIXED pero re-verificar live) + build switcher + honest-RED secundarios + demo-script + dod_evidence → (4) G (Chris self-test + ratificar goldens V-VIS-1..4) → R reconcile → /auditor → merge."
regression_2026-06-06:
  id: nuevo-integrante-modal-infinite-loop
  severity: critical
  surface: /{tenantId}/lisa/staff (directorio)
  symptom: "Maximum update depth exceeded — Next.js error bubble (botando error)"
  root_cause: >-
    NuevoIntegranteModal.tsx:109-114 useEffect deps [open, form, createDoctor].
    createDoctor = useCreateDoctor() (react-query useMutation) devuelve ref nueva
    cada render → effect re-dispara → form.reset()+createDoctor.reset() → re-render → loop.
    Probablemente latente desde build; expuesto/agravado por drift del shell (lift @luana/ui-kit
    256517a3 + squash-merges embudo/proceso-v5/shell-valeria en últimos 5 días).
  fix_owner: /dev-team (TDD RED-first)
  status: "✅ FIXED + live-verified dev-app (no max-depth, page renders, 3/3 unit)"
  also_check: ["WebsiteCard.tsx:103 (RHF form stable — OK)", "BloquePopover.tsx:201 (RHF reset stable — OK)"]
regression_2026-06-06_bug2:
  id: staff-client-absolute-base-cors
  severity: critical
  surface: /{tenantId}/lisa/staff (directorio + workspace · TODO client fetch)
  symptom: "StaffErrorBanner ('No pudimos cargar el equipo') pese a BE GET 200"
  root_cause: >-
    staff.ts + StaffWorkspaceShell.tsx (ambos "use client") usaban base ABSOLUTA
    http://localhost:8002 → browser cross-origina → CORS block (No Access-Control-Allow-Origin).
    El /api/*→BE lo routea el tunnel Cloudflare (deploy/cloudflared/dev-config.yml ^/api/.*),
    NO next.config (sin rewrites). Convención app (adrian/fidelizacion/crm) = base RELATIVA
    same-origin. Masked por SSR initialData (server-to-server, absoluto OK) que pintaba el 1er render.
  fix: "API_BASE = '' (relativo) en staff.ts + StaffWorkspaceShell.tsx (client). staff-server.ts SSR mantiene absoluto."
  status: "✅ FIXED + live-verified dev-app (GET 200 {items:[...]}, console errors=[], directorio renderiza)"
regression_2026-06-06_bug3:
  id: staff-mutations-403-no-user-role-header
  severity: high
  surface: POST/PATCH/DELETE /clinics/doctors* (crear/editar/desactivar/bio/bloques)
  symptom: "POST /clinics/doctors → 403 Forbidden (no 201) · modal no redirige"
  root_cause_3a: >-
    staff.ts/StaffWorkspaceShell NO mandan X-User-Role (ni X-User-ID). require_brand_owner_access
    lee el rol del header → ausente → 403 en toda mutación. marca.ts SÍ lo manda (buildMutationHeaders).
    El create por el modal real NUNCA funcionó (los 3 doctores 06-01 vía path que inyectaba header).
  decision_3b: >-
    DECISIÓN CHRIS PENDIENTE. doctores exige _ADMIN_CLINIC_ROLES={admin_clinic} ÚNICAMENTE
    (AC-12 + hipaa-lite: owner NO es PHI-role). dr.demo es rol owner (verificado Clerk) → 403 by design.
    marca permite {owner,admin_clinic}; doctores no. ¿Ensanchar doctores a {owner,admin_clinic} (owner
    gestiona staff) o admin_clinic-only (necesita user admin_clinic de prueba + bootstrap del 1er admin)?
  fix_3a: "✅ DONE — staff.ts buildStaffMutationHeaders → 8 mutations send X-User-Role+X-User-ID (mirror marca)"
  decision_3b_resolved: "Chris 2026-06-06: WIDEN a {owner, admin_clinic}. BE _STAFF_MUTATION_ROLES widened + test_doctor_mutation_rbac.py 10/10. ✅ DONE"
  status: "✅ #3a+#3b DONE (gated green) · write live-verify BLOCKED by bug #4"
regression_2026-06-06_bug4:
  id: usecurrentuser-global-role-not-per-tenant
  severity: high
  scope: SYSTEMIC (shared hook src/hooks/useCurrentUser.ts · 8 consumers)
  surface: all tenant-scoped RBAC + PHI gating via useCurrentUser
  symptom: "write POST 403 con X-User-Role:'doctor' pese a dr.demo=owner en el tenant"
  root_cause: >-
    DB: users.role (GLOBAL) = doctor · user_tenants.role (per-tenant Sanaré) = owner.
    GET /api/v1/iam/users/me (engine core/luana-core-iam) devuelve el perfil GLOBAL
    (role: doctor, no toma X-Tenant-ID). El engine está bien (existe /me/tenants con rol
    por-tenant). El bug es de marca: useCurrentUser lee el rol de /me (global) para RBAC
    tenant-scoped; su docstring afirma per-tenant pero NO lo es. dr.demo es doctor de
    profesión + owner de la clínica → 1-rol-por-tenant pierde esa dualidad.
  phi_implication: >-
    useCurrentUser.hasPhiAccess = role ∈ {doctor,nurse,admin_clinic}. Cambiar a per-tenant
    flipea dr.demo hasPhiAccess true→false (owner∉PHI) → puede romper UI PHI-gated en 8
    consumers (fidelizacion×3, inbox, usePiiRoleGate, staff). Decisión de modelo de roles + PHI.
  decision_resolved: "Chris 2026-06-06: opción B (targeted staff.ts). ✅ DONE"
  fix_applied: >-
    staff.ts useStaffMutationHeaders: rol = per-tenant (tenant-store activeTenant/availableTenants
    role) NO el global; X-User-ID = DB user UUID (meData.id del /me cache, NO Clerk id —
    los endpoints doctors tipan X-User-ID:UUID + lo usan como actor de audit). useCurrentUser
    compartido NO tocado (hasPhiAccess intacto). systemic useCurrentUser per-tenant → carril aparte.
  status: "✅ FIXED + live-verified (write 201)"
write_live_verified_2026-06-06:
  action: "crear doctor vía modal real (autenticado dr.demo owner) en dev-app.vitalialat.com"
  post_status: 201
  x_user_role_sent: owner   # per-tenant (no global doctor)
  x_user_id_sent: "527050c3 (DB UUID, no Clerk id)"
  db_effect: "vitalia_doctors id=88c931f3 (PHI cifrada pgcrypto, active=t)"
  audit_effect: "vitalia_audit_log action=doctor.created actor=527050c3 (DB user id correcto)"
  telemetry: "growth_studio_event lisa_staff_doctor_created"
  redirect: "/lisa/staff/88c931f3.../perfil (modal router.push OK)"
rescate_2026_06_06_dod_live_verified: true  # histórico rescate (bloque renombrado 06-12: keys top-level únicas)
rescate_2026_06_06_dod_env: "make dev-app-vitalia → dev-app.vitalialat.com (Playwright autenticado live, dr.demo owner)"
rescate_2026_06_06_dod_evidence:
  - action: "GET /clinics/doctors (directorio) autenticado"
    observed: "200 {items:[Ana Garcia Mendoza...]}, directorio renderiza, console errors=[], cero max-depth, sin error banner"
    backend_log: "GET /clinics/doctors 200 OK"
  - action: "POST /clinics/doctors (crear doctor vía modal real, owner)"
    observed: "201 + redirect a /lisa/staff/{id}/perfil"
    backend_log: "doctor_created + POST 201 · DB vitalia_doctors fila cifrada + vitalia_audit_log doctor.created actor=DB-UUID + telemetry lisa_staff_doctor_created"
  - action: "abrir perfil de un doctor (GET /clinics/doctors/{id} detail)"
    observed: "200 (X-User-ID=DB-UUID) · doctor-perfil-view renderiza · SIN 'No se pudo cargar el perfil' · sin overlay error Next"
    backend_log: "GET /clinics/doctors/{id} 200 OK"
  - action: "workspace tabs horarios + servicios"
    observed: "ambas cargan sin error · horarios calendar renderiza (sin 'filter is not a function') · sin overlay error Next · sin loop"
    backend_log: "GET /availability-blocks 200 · GET detail 200"
regression_2026-06-06_bug5:
  id: doctor-perfil-422-no-x-user-id
  severity: high
  surface: /lisa/staff/{id}/perfil (+ workspace shell)
  symptom: "'No se pudo cargar el perfil. Vuelve a intentarlo.' (Chris lo reportó)"
  root_cause: >-
    GET /{doctor_id} (detail) exige X-User-ID:UUID (audit-on-PHI-read; la LIST no).
    useDoctor + StaffWorkspaceShell (mismo query key) NO mandaban X-User-ID → 422.
    Yo había agregado headers SOLO a mutaciones, no a los reads de detail. (La live-verify
    del write asertó el redirect URL pero NO que el perfil renderizara → el miss.)
  fix: "useDoctor + StaffWorkspaceShell mandan actor headers (useStaffActorHeaders) + enabled gate hasta X-User-ID listo (mata race 422-then-200)"
  status: "✅ FIXED + live-verified (GET 200, perfil renderiza)"
regression_2026-06-06_bug6:
  id: availability-blocks-envelope-mismatch
  severity: high
  surface: /lisa/staff/{id}/horarios (AvailabilityCalendar)
  symptom: "'(blocks ?? []).filter is not a function' → overlay error Next en horarios"
  root_cause: >-
    BE devuelve AvailabilityBlocksResponse {blocks:[...]} (envelope) pero useAvailabilityBlocks
    fetchaba como AvailabilityBlock[] (array pelado) → blocks era objeto → .filter crash.
    Misma clase que el {items} del directorio. Masked: horarios e2e era mock.
  fix: "useAvailabilityBlocks desempaqueta res.blocks ?? []"
  status: "✅ FIXED + live-verified (horarios renderiza)"
rescate_2026_06_06_verified_at: 2026-06-06
remaining_for_developed:
  - "demo-script.md (story funcional)"
  - "honest-RED secundarios: SC-1b/c/d calendar recurrence, SC-9 pagination, SC-11 i18n credencial país (mock→real o scope per #37)"
  - "visual goldens V-VIS-1..4 → ratificación Chris (ADR-003, NO autonomous)"
  - "G: Chris self-test live en dev-app (core read+write ya verde) → R reconcile → /auditor"
flagged_carriles:
  - "L3 tech-debt: test_doctor_cross_tenant.py usa asyncio.get_event_loop() (roto Py3.12, pre-existente)"
  - "L2/L3 systemic: useCurrentUser devuelve rol GLOBAL no per-tenant + expone Clerk id no DB id (8 consumers) — carril aparte"
  - "L2 contract: X-User-ID inconsistente BE (marca=str+resuelve Clerk · doctors=UUID directo) — homologar"
session_2026-06-06_summary: >-
  Retomada tras 5d. Diagnosticada la 'botando error' (loop) + descubiertos 2 bugs más de
  integración real (CORS read, RBAC write) que el '6/8 done' enmascaró. Bugs #1 (loop) y #2 (CORS)
  FIXED + live-verified en dev-app (read path 100% verde). Bug #3 write path: #3a (X-User-Role
  header faltante, fix mecánico mirror marca) + #3b (RBAC owner vs admin_clinic, DECISIÓN Chris).
  Story sigue developing; write path pausado en decisión #3b. NO developed aún.
blocker_2026-06-01:
  id: clerk-choose-organization-task
  kind: clerk-instance-config (no-código)
  status: ✅ RESUELTO 2026-06-01
  detail: >-
    Clerk dev instance tenía Organizations + force_organization_selection:true. Al borrar
    la Clerk org en sesión 1, dr.demo quedó sin org → todo sign-in colgado en
    /sign-in/tasks/choose-organization (login real + e2e rotos platform-wide).
    FIX aplicado: PATCH /v1/instance/organization_settings {force_organization_selection:false}
    (Clerk Backend API). Login restaurado (setup 2/2 GREEN, dev-app /sign-in 200). Setting vive
    en la instancia Clerk, NO en git. Doc:
    vitalia/docs/observed-bugs/2026-06-01-clerk-choose-organization-task-blocks-signin.md
t_fix_2_progress:
  a_seed_by_write: "✅ GREEN-real (3 doctores DB + 3 audit rows · evidencia DoD confirmada orchestrator)"
  b_pom_workarounds: "✅ committeado fd512f33 (re-verificación asserts bloqueada por Clerk)"
  d_perf_measurement: "✅ committeado fd512f33"
  c_visual_goldens: "✅ 7 baselines committed (directorio×2 + perfil×2 + horarios×2 + servicios×1) — commits d206fd7b+ebe7d524. Awaiting Chris ratification ADR-vitalia-003."
  e_deep_flows: "⚠️ partial: 24 GREEN / 12 honest-RED documented (SC-11 i18n modal default, SC-1/SC-1b/SC-1c/SC-1d/SC-3/SC-3b workspace-calendar, SC-9 pagination race) — T-FIX-2-result.md § deep flows"
chris_decisions_2026-06-01:
  - id: a-seed
    decision: seed-by-WRITE-real
    detail: >-
      /dev-team ejerce el flujo create real (POST /doctors → 201 + fila DB cifrada
      pgcrypto + audit) para 2-3 doctores en tenant e69a691d / clinic
      f035be5b-0ac4-5210-8fc3-395650ca2b83 (Sanaré LATAM — Sede Principal, verificada
      existe). Cuenta como Scenario 1 happy-path + evidencia DoD más fuerte + seedea
      datos para flujos (e). NO raw-SQL (pgcrypto frágil).
  - id: c-goldens
    decision: relocate-regen-ratify-now
    detail: >-
      Reubicar V-VIS-1..4 (de staff-large-dataset.spec.ts smoke) a project=visual con
      snapshotPathTemplate + maxDiffPixelRatio, regenerar baselines limpios, mostrar a
      Chris para ratificación (ADR-vitalia-003) ANTES de merge. doctores done incluye
      AC-9 completo. Borrar baselines basura untracked (staff-large-dataset.spec.ts-snapshots/ + _shots/).
release: F2
cap_target: lisa.doctores
cap_change_type: new
parent_story: null
---

# F2-S8 vitalia-fase2-lisa-doctores — checkpoke

## Goal

Sub-tab Doctores de Lisa: directorio + CRUD perfiles doctor + N3-dyn workspace per doctor con tabs (Bio · Horarios · Servicios · KPIs). Personal-branding salud-overlay (foto · especialidad · credenciales · años experiencia · idiomas · bio · reseñas público-visibles).

## Anti-objetivos

- NO implementar editor avanzado de horarios recurrentes (solo template básico day-of-week · F2-S20 config-cuenta puede extender)
- NO implementar peer-review entre doctors (out-of-scope)
- NO duplicar `Doctor` model shipped en `vitalia/backend/src/modules/vitalia/staff/`
- NO tocar engine

## Scope verbatim

### § 1 — Page directorio

`vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/doctores/page.tsx`:

`<DoctorsDirectoryView>` con grid de cards doctor (no table — visual emphasis personal-branding):

- Avatar grande + nombre + especialidad badge
- Bio truncada (3 líneas)
- Stats tiny (años exp · pacientes atendidos · rating NPS)
- "Ver perfil" button → N3-dyn workspace

Header: "+ Nuevo doctor" + search + filter especialidad.

### § 2 — N3-dyn workspace `[doctor-id]`

`vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/doctores/[doctor-id]/page.tsx`:

Tabs:
- **Bio** — Avatar upload S3 · nombre · especialidad · credenciales · años exp · idiomas · bio textarea · reseñas público-visibles toggle
- **Horarios** — Template semanal (day-of-week × time-slots) + excepciones (vacaciones · días libres) · backend genera availability_slots para Agenda Valeria
- **Servicios** — Multi-select treatments doctor puede ofrecer (consume F2-S9 catalog) · default pricing override per doctor opcional
- **KPIs** — Stats: total pacientes · sessions/mes · NPS · revenue generado · time-in-stage avg (read-only · consume analytics)

### § 3 — "+ Nuevo doctor" modal

Form fields: Nombre + Apellido + DNI · Email + Phone · Especialidad · Credencial colegio médico (obligatorio salud) · Foto upload optional · Active toggle.

Submit → POST `/api/staff/doctors` → audit log + redirect a workspace.

### § 4 — Doctors-as-faces public preview

Backend expone endpoint `/api/public/clinic/{tenant}/doctors` (read-only · PHI masked) que landing pública consume. Permite/excluye doctors via toggle "Visible en landing" per doctor.

### § 5 — Trust signals validation

Backend valida credencial colegio médico format country-specific:
- PE: CMP (Colegio Médico Perú) format `12345`
- AR: matrícula nacional + provincial
- MX: cédula profesional
- CL: registro nacional médicos

`vitalia/backend/src/modules/vitalia/staff/application/credential_validator.py`.

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | Directorio renderiza cards doctor |
| AC-2 | Filter especialidad + search funcionan |
| AC-3 | "+ Nuevo doctor" crea perfil + redirect workspace |
| AC-4 | Workspace tabs (Bio · Horarios · Servicios · KPIs) funcionan |
| AC-5 | Horarios template genera availability_slots backend |
| AC-6 | Credencial colegio médico valida country-specific |
| AC-7 | Visible-en-landing toggle controla preview público |
| AC-8 | Avatar upload S3 + preview |
| AC-9 | Visual goldens × 8 (directorio + 4 tabs × 2 themes) |
| AC-10 | a11y axe pass |
| AC-11 | Cross-tenant query bloqueada |
| AC-12 | RBAC: solo role `admin_clinic` puede editar doctors (otros read-only) |
| AC-13 | Vitest + Playwright + a11y pass |

## Gherkin scenarios

### Scenario 1 — happy: crear doctor + horarios

**Given:** User admin_clinic en Lisa→Doctores

**When:**
1. "+ Nuevo doctor" → modal → fields obligatorios + CMP 12345 PE
2. Submit
3. Workspace abre tab Bio
4. Tab Horarios → marca lunes-viernes 9-13 + 15-19
5. Save

**Then:**
- Doctor creado · audit log
- Horarios persisten · backend genera availability_slots para próximos 90d
- Agenda Valeria reconoce nuevo doctor en form "crear cita"

### Scenario 2 — negative: credencial inválida

**Given:** Form nuevo doctor con CMP `abc` (no número)

**When:** Submit

**Then:**
- Validator backend rejecta 422 "Credencial CMP debe ser numérico"
- UI muestra error inline + foco en field
- NO persiste

### Scenario 3 — edge: doctor desactivado

**Given:** Doctor existente con citas futuras agendadas

**When:** Toggle "Activo" → off

**Then:**
- Backend: doctor.active = false
- Slots futuros del doctor: backend NO cancela (preserva data) pero excluye en form crear-cita
- Alert UI "Doctor desactivado. {N} citas futuras siguen vigentes. Re-asignar manualmente?"

### Scenario 4 — adversarial: cross-tenant doctor view

**Given:** Adversarial intenta ver doctor de tenant B

**When:** Navega `/{tenant-A}/lisa/doctores/{doctor_B_id}`

**Then:**
- Backend dual filter bloquea
- 404 genérico
- Audit log `cross_tenant_attempt`

### Scenario 5 — keyboard-a11y tabs workspace

**Given:** Foco en primer tab Bio

**When:** Arrow → cycle tabs

**Then:** aria-selected actualiza · screen reader anuncia · Tab fields ordenados lógicamente

## Deliverables

| File | Acción |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/doctores/page.tsx` | MODIFY |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/doctores/[doctor-id]/page.tsx` | NEW (N3-dyn) |
| `vitalia/frontend/src/features/lisa/components/doctores/DoctorsDirectoryView.tsx` | NEW |
| `vitalia/frontend/src/features/lisa/components/doctores/DoctorCard.tsx` | NEW |
| `vitalia/frontend/src/features/lisa/components/doctores/NuevoDoctorModal.tsx` | NEW |
| `vitalia/frontend/src/features/lisa/components/doctores/DoctorWorkspace.tsx` | NEW |
| `vitalia/frontend/src/features/lisa/components/doctores/tabs/{Bio,Horarios,Servicios,Kpis}Tab.tsx` | NEW (4 files) |
| `vitalia/frontend/src/features/lisa/api/doctores.ts` | NEW |
| `vitalia/frontend/src/features/lisa/types/doctor.types.ts` | NEW |
| `vitalia/frontend/src/features/lisa/types/doctor-schema.ts` | NEW (Zod) |
| `vitalia/backend/src/modules/vitalia/staff/api/doctors_router.py` | NEW or MODIFY |
| `vitalia/backend/src/modules/vitalia/staff/application/credential_validator.py` | NEW |
| `vitalia/backend/src/modules/vitalia/staff/application/horarios_to_slots_service.py` | NEW |
| `vitalia/backend/src/modules/vitalia/staff/persistence/migrations/XXXX_doctor_horarios.py` | NEW |
| `vitalia/frontend/e2e/shell-organism/lisa-doctores-crud.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/doctores/{view}-{light\|dark}.png` (×8) | NEW |
| `vitalia/backend/tests/modules/vitalia/staff/test_credential_validator.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/staff/test_horarios_to_slots.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/staff/test_doctor_cross_tenant.py` | NEW |

## Reuse map

| Origen | Componente / pattern | Adaptación |
|---|---|---|
| Vitalia shipped — `vitalia/backend/src/modules/vitalia/staff/` | Doctor/StaffMember model | REUSE + extend |
| Vitalia shipped — `patients` PHI masking utils | Email/Phone/DNI masking | REUSE |
| Shadcn primitives | `Card` · `Dialog` · `Tabs` · `Form` · `Checkbox` · `Select` · `Upload` | npx install |
| Vitalia archived — patients FE pattern | CRUD directory layout | TRANSPONER |

## Dependencies map

### Hard
- `vitalia-fase1-empty-states` + `vitalia-fase1-routing-shell`

### Soft
- `vitalia-fase2-lisa-marca` — voice brand alimenta bio default

### Esta historia desbloquea
- `vitalia-fase2-valeria-agenda` — form crear-cita usa doctors disponibles
- `vitalia-fase2-lisa-servicios` — doctor-treatment assignment matrix
- `vitalia-fase2-valeria-pacientes` — paciente assignment doctor

## Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Credencial validators country-specific incompletos | Media | Bajo | Tabla extendible cuando bootstrap nueva region |
| Doctor desactivado rompe citas futuras | Media | Medio | Soft-deactivate + alert + manual re-assign flow |
| Horarios template no maneja casos complejos | Alta | Bajo | MVP: weekly template básico · story future para shift management |

## Definición de "Done"

1. AC verificados
2. Visual goldens × 8
3. Backend tests credential + horarios + cross-tenant pass
4. Story pushed + handoff `/auditor`
5. Auditor APPROVED → merge → capability `lisa.doctores` registrada

## Próximo paso post-done

- F2-S1 valeria-agenda consume doctors disponibles
- F2-S9 lisa-servicios mapea treatments → doctors

## Prior art scan (2026-05-30 · `/pm-vitalia`)

> Ejecutado per `.claude/rules/anti-duplication-refining.md`. Corrige asunciones del scope original.

### Correcciones al scope original (el checkpoint asumía paths que no existen)

| Asunción original | Realidad en código | Acción para `/po-ux` + `/architect` |
|---|---|---|
| `module: staff` · Doctor model en `vitalia/backend/src/modules/vitalia/staff/` | **NO existe `staff/`**. Doctor vive como `VitaliaDoctorExtensionModel` en `infrastructure/models/doctor_extension_model.py` + `DoctorExtensionRepository` (`# cap: booking.prepaid-booking-advisory-locks`). El módulo de negocio salud es **`clinics`**. | Corregido `module: clinics`. El backend de perfiles doctor **extiende `clinics` + doctor-extension existente**, NO crea `staff/`. |
| "Horarios → genera `availability_slots` para Agenda Valeria" (parecía build nuevo) | **`scheduling/` ya tiene** `agenda_slot` (domain), `create_appointment_service`, `agenda_grid_service`, `agenda_router`, appointment repos. + engine `luana-core-scheduling` + `luana-core-commercial-calendar`. | Horarios del doctor **cablea hacia `scheduling/` + engine existente** (CONSUME, no recrea). Tab Horarios → escribe availability que `scheduling` ya consume. |
| Reuse "patients PHI masking utils" genérico | `booking/prepaid-booking-advisory-locks.yaml` (deprecated) define `advisory_locks` + slots por doctor + consent modal ya shipped. | KPIs tab + slots disponibles reusan endpoints `bookings/available-slots` existentes. |

### Engine a consumir (NO recrear)
- `luana-core-scheduling` — availability/slots base.
- `luana-core-commercial-calendar` — calendario comercial.

### Capability decision (ratificada Chris 2026-05-30)
- `cap_target: lisa.doctores` · `cap_change_type: new` (mapa: zona **Agentes → Lisa**).
- Caps relacionadas **deprecated** que esta story sucede:
  - `clinics/clinics-brand-extension.yaml` (`replaced_by_story: vitalia-fase2-lisa-doctores`).
  - `booking/prepaid-booking-advisory-locks.yaml` (slots/locks — se consume, no se recrea).
- En Fase F.3: crear `capabilities/staff/` NO — la cap vive bajo agente Lisa. Doc el linaje (clinics-brand-extension → sucedida por lisa.doctores) en el change_log de la cap nueva.

### Decisión: net-new UI + extend backend
- **NEW**: UI `features/lisa/components/doctores/` + rutas `lisa/doctores/` + `lisa/doctores/[doctor-id]` (hoy `features/lisa/` solo tiene `marca` + `placeholders`).
- **EXTEND**: backend doctor profiles sobre `clinics` + `doctor_extension` + CONSUME `scheduling`/engine para horarios.

## Referencias

- **Design Contract:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- **Navigation tree:** § lisa.doctores
- **HIPAA-lite:** `vitalia/.claude/rules/hipaa-lite.md`
- **Prior art:** `clinics/` module · `scheduling/` module · `infrastructure/models/doctor_extension_model.py` · engine `luana-core-scheduling`

## Ready package (`/architect` Opus 4.8 · 2026-05-31)

`refined → ready`. 7 artefactos. `adr_004_compliance: full`. 11 tickets, DAG sin ciclos, `autonomous_mode: true`.

**4 decisiones arquitectónicas resueltas (03-arch § Architecture Decisions):**
- **D-1** `EntitySubNavBar` (N3-dynamic) = componente nuevo sibling de `SubSubTabsBar` (no lo modifica). Addendum ADR-004 § 3.1.1 → owner `/pm-vitalia` F.3.
- **D-2** ⚠️ `commercial-calendar` NO expande recurrencia (es calendario marketing). Proyección = brand-local `dateutil.rrule`. La business rule `availability-projection-via-engine` parte de premisa errónea → corregir wording al merge.
- **D-3** ⚠️ presigned upload NO existe en `luana-core-assets` (solo proxy `upload_asset`). Se consume proxy upload; presign diferido a `/pm-luana` lift futuro.
- **D-4** bio-gen = servicio determinista BE (`clinics/application`), NO agentic → R23 NO aplica → Sonnet.
- **D-5** NEW tabla `vitalia_doctors` (no existía perfil; `vitalia_doctor_extensions` solo guarda extensiones).
- **D-6** NO split (11 tickets DAG cohesivo).

**Chris manual action (T-BE-7):** generar R2 S3 creds + bucket + CORS + rotar `cfat_`. Code/tests proceden mockeados.

**Open questions for PM:** ver `03-arch.md § 16` (5 ítems — addendum ADR, corrección business rule, presign lift, open_ended horizon, R2 creds).

**Next:** `/dev-team vitalia vitalia-fase2-lisa-doctores` → T-BE-1.
