---
story_id: vitalia-fase2-mateo-nueva-cita
type: ui-story
agent_owner: mateo
module: scheduling
capability: mateo.agenda
state: developed                                     # ⤺ /dev-team cerró el build del delta (T-D1+T-D2+T-D3 pushed · gates verdes · wiring live OK). Pausa en G para que Chris ejerza el rediseño. Base de 9 tickets preservada.
phase: AWAIT_CHRIS_VERIFY                            # G · Chris ejerce el rediseño de disponibilidad live + firma chris_verify.rounds[1]/signoff (autonomous_mode:false → NO auto-auditor).
next_action: "Chris ejerce el rediseño live (G) → firma chris_verify.rounds[1] + signoff → /pm-vitalia reconcile (R) → /auditor"
delta_ready_package:                                 # ★ G round 1 — scope-delta (NO reemplaza el ready package base de 9 tickets)
  arch: 03-arch-delta-availability.md                # endpoint service-day (decisión A) + Fecha/Hora split + strip 1→N + §6 swimlane recomendado
  validators: 04-validators.yaml § delta_availability # SC nuevos + sub-categorías + seam_coverage + mutation/schemathesis
  tickets: 06-tickets.yaml § delta_tickets           # T-D1 (BE) + T-D2 (FE Fecha/Hora) + T-D3 (FE strip multi-doctor) — BUILT
  dispatch: dispatch-plan.md § "DELTA dispatch"      # DAG: T-D1+T-D2 ∥ → T-D3 ; autonomous_mode:false
  design_decision: "§6 — swimlane-por-médico + FreeDoctorsList re-roleada (filtrada-por-hora). Chris ratifica live en G."
  engine_boundary: "cero edit a core/luana-core-* salvo la extensión del kit ya migrada (SmartDateTimePicker showTime, @luana/ui-kit 0.8.0 — NO DatePicker nuevo · ratificado Chris). BE brand-local."
  build_commits: { T-D1: 0b2adb07, T-D2: f38e0978, T-D3: 82731018 }   # kit precursor (SmartDateTimePicker showTime) uncommitted en working-tree (verificado tsc/vitest 326) — shared commit, promote-to-main pendiente (pregunta a Chris)
chris_verify:
  required: true
  signoff: null                                      # → {by: Chris, date, result: SATISFIED|SATISFIED_WITH_FOLLOWUPS|REJECTED, notes, open_items}
  rounds:                                            # allowlist de scope ratificado para el auditor
    - round: 1
      date: 2026-06-25
      ratified_by: Chris
      status: built                                  # construido (T-D1/2/3 pushed · gates verdes · wiring live OK) → Chris ejerce + firma en G
      delta: >
        Disponibilidad día-driven multi-doctor (comentario G #1). (1a) Separar Fecha de Hora
        (TimePicker/TimeRangePicker recién en @luana/ui-kit). (1b) Día + servicio → auto-listar
        disponibilidad de TODOS los médicos del servicio en el grafiquito (DayAvailabilityStrip
        pasa de 1 a N médicos, swimlanes) SIN elegir médico antes. (1c) Hora → filtra a los
        disponibles a esa hora (FreeDoctorsList = resultado filtrado, no marcar a mano). (1d)
        Cambio de día → auto-refresh. SSoT del requisito: chris-input.md comentario G #1.
        Decisión de diseño abierta (la resuelve /architect, Chris ratifica en G): visualización
        N-médicos del strip (swimlane recomendado) + fate de la columna derecha.
reconciled: false                                    # /pm-vitalia lo pone true en R (precondición del auditor)
build_started: 2026-06-22                           # /pm-vitalia ready→developing + handoff /dev-team
dod_live_verified: true                             # ★ happy path core ejercido live (cita-create 201 + patient-create 201, filas reales). Falta G de Chris (full functional + 409 + toast + demo) + auditor de los 9 fixes
dod_env: "localhost:3002 (FE) + localhost:8002 (BE docker) · dr.demo@vitalialat.com · Chrome DevTools MCP"
dod_evidence:
  - action: "crear paciente inline (nombre 'Sofia', sin teléfono) desde el picker de nueva-cita (autenticado dr.demo)"
    observed: "POST /api/v1/crm/patients → 201 · vitalia_patients count 29→30 (fila real, masked)"
    backend_log: "POST /api/v1/crm/patients HTTP/1.1 201 Created"
    verified_at: 2026-06-23
  - action: "crear cita: Botox · 29-jun 09:00 · Dr.2464fad7 (chip 'Médico disponible') · paciente Sofia · Crear cita"
    observed: "POST /api/v1/scheduling/appointments → 201 · vitalia_appointments fila SCHEDULED (slot 2026-06-29T12:00Z=09:00 tz UTC-3, dur 30, origin walk_in, offer/clinic/patient set) + vitalia_appointment_clinic_map mirror 12:00→12:30 SCHEDULED (EXCLUDE anti-solape activo)"
    backend_log: "POST /api/v1/scheduling/appointments HTTP/1.1 201 Created"
    verified_at: 2026-06-23
  - action: "auditoría UX live (Chrome MCP, dr.demo, :3002) + fix-loop de 16 hallazgos (commit 8075cd86) + re-verify live de los fixes"
    observed: "H1 Hora-fin 09:00+30min → 09:30 (era 12:30, UTC bug) · H3 mini-día con header+eje 08–20+leyenda (era barra pelada) · H2 motivo de bloqueo 'Selecciona un paciente para continuar' · M1 columna intro '¿Qué verás aquí?' · M3 'Viene del servicio · editable' · M4 hint oculto en mobile (no colisiona FAB) · M6 warning controlled/uncontrolled GONE de consola · L1 'Sin cita'/'Teléfono' · L6 contador 0/500. Console 0 errores. Happy path intacto."
    backend_log: "sin tracebacks; sin writes nuevos (verificación de presentación/cómputo client-side)"
    verified_at: 2026-06-24
  - action: "L1 revert (commit fa8572d4) + L3 raíz (commit e4d1f170: list_active_doctors JOIN vitalia_doctors) — re-verify live"
    observed: "L1 canal de vuelta a '🚶 Walk-in'/'📞 Teléfono' (mockup ratificado). L3: picker de médico muestra 'Ana Garcia Mendoza' (nombre real) — era 'Dr. 2b0d9466' placeholder; el nombre estaba en la DB, el query no lo joineaba. Era CÓDIGO (no seed)."
    backend_log: "free-doctors endpoint ahora resuelve CONCAT(first_name,last_name) vía JOIN; 272/272 scheduling + 5/5 nuevos tests real-DB"
    verified_at: 2026-06-24
  - action: "DELTA G#1 build (T-D1 service-day + T-D2 Fecha/Hora + T-D3 strip N-médicos) — sanity de wiring live (orchestrator; ejercicio funcional completo = G de Chris)"
    observed: "BE GET /availability/service-day → 422 (registrado, idéntico al day-strip existente, NO 404) · FE /mateo/agenda/nueva-cita compila+renderiza 200 (sin chunk-error). Contrato FE↔BE cubierto por contract-test del builder (verde)."
    backend_log: "service-day en availability_router; sin tracebacks. Tests: scheduling 285/285 (T-D1 +13 real-DB) · mateo FE 425/425 (T-D3)."
    verified_at: 2026-06-26
  pending_at_G: "Rediseño G#1 ejercer live: servicio+día → strip multi-doctor (N swimlanes) · poner hora → filtra · cambiar día → refetch · ratificar §6 (swimlane + columna derecha re-roleada) · + base pendiente (409 solape · toast 'Cita creada'+grilla) · demo-script.md · firma Chris"
live_verify_findings:                               # Chrome DevTools MCP (dr.demo · localhost:3002) 2026-06-22/23 — detalle en chris-input.md
  - "bug1 render token-isLoaded → skeleton eterno · FIXED+verificado (/offer/servicios 200, pickers pueblan)"
  - "bug2 token 60s cacheado → writes 307 · FIXED 1d63734f (free-doctors POST 200, era 307)"
  - "bug3 BE channel_first/notes columnas inexistentes → 500 · FIXED 0ff94f55 mig051 (crm GET 200, 29 pacientes)"
  - "bug4 nested <form> hydration → submit tragado · FIXED faa643f7 (form→div, hydration limpio)"
  - "bug5 inline-create no POSTeaba · FIXED faa643f7 (phone '' → null) · ★ el 'no POST' era ARTEFACTO del click Chrome-MCP (sintético no dispara onClick React) — native .click() → patient POST 201 (DB 29→30). Feature sana."
  - "VERIFICADO live (native-click): login·shell·pickers·servicios·free-doctors POST 200·chip Médico-disponible·day-strip(AC-8)·reasignar 1-clic(AC-5)·patient search-by-name(decrypt)·patient CREATE 201(real)·Crear-cita se habilita"
  - "bug6 cita-create 500 'notes_internal no existe' · FIXED 9feb302c (mig052 + test real-schema, scheduling 236/236)"
  - "bug6b RESUELTO: INSERT llena clinic_id (contexto) + offer_id (FE manda selectedServiceId). BE 86b90904 + FE 453ea164"
  - "bug8 cita-create 500 NoReferencedTableError (FK ORM mirror) · FIXED 2de80705 (fix-loop holístico + test integración real end-to-end 7/7, smoke-insert real)"
  - "bug9 cita-create 500 AppointmentDetailDTO.currency requiere str pero es None · FIXED 193f1a7b (currency str|None, currency-handling rule). El INSERT+mirror YA funcionaban; fallaba la serialización de la respuesta"
  - "✅ HAPPY PATH VERIFICADO LIVE (2026-06-23): cita-create 201 (fila vitalia_appointments SCHEDULED + mirror clinic_map 12:00→12:30) · patient-create 201 (DB 29→30). Núcleo funciona end-to-end tras 9 fixes"
  - "★ patrón: 9 bugs en cascada en el create-path, NINGUNO agarrado por unit (mockean DB/Clerk). El test holístico cazó #8 pero no #9 (no probó el response DTO del router con currency null). Recomendación durable: test integración real-DB del ROUTER (no solo service) + contract FE↔BE (HB-42)"
  - "pendiente live (G de Chris): 409 solape (cubierto por integration test) · toast + grilla refleja (sesión expiró tras el 201) · demo-script.md"
  - "infra: scripts/git-hooks/pre-commit (+1655 sin commitear) tiene MARCADORES DE CONFLICTO git → rompió sweep-guard HB-31 (contaminación cross-sesión) → reparar"
  - "e2e runner roto platform-wide (clerk.setup.ts:31 describe.configure, pre-existente) → HB pendiente"
verify_battery_2026_06_24:                          # /dev-team VERIFY_BATTERY — correr TODA la batería del architect ANTES del auditor (Chris opt-A). Estado por gate:
  be_suite: "✅ GREEN 632/632 (scheduling+crm). Incluye real-DB EXCLUDE/half-open/cancelled-reuse + adversarial (cross-clinic/cross-tenant/rbac/phi)."
  fixed_be_test: "test_migration_050_exclude.py — estaba RED y descartado como 'flake pre-existente'. 2 bugs reales del TEST: (1) async_engine module-scoped vs loop function-scoped (pytest-asyncio) → usar conftest db_session; (2) INSERT al mirror con appointment_id huérfano → FK violation (helper _insert_map: parent vitalia_appointments primero). Ahora 18/18 GREEN real-DB."
  mutation: "✅ wrapper ARREGLADO + corrido. scripts/mutation_gate.py portado a mutmut 3.x (config-only [mutmut] en setup.cfg temp del dir backend + also_copy=src + addopts sin -x + parse mutmut results + cleanup finally + degrade HONESTO). Validado: availability_check.py (domain) = 0 survivors, exit 0. HB-97 → ✅. (Los otros 3 targets: el wrapper ya corre; full HARD-sweep de los 4 = corrida larga DB-heavy, follow-up.)"
  schemathesis: "✅ instalado (4.21.10) + corrido sobre availability/check + free-doctors. Resultado: ambos 403 unauth (auth-gating PHI correcto). Hallazgo menor: el OpenAPI no documenta el 403 (schema-doc gap). Fuzzing profundo necesita Clerk-JWT de BE (auth plumbing, follow-up)."
  e2e_smoke: "✅ 5/5 GREEN (dev :3002, env completo). happy-path + form-render + back-pill + a11y."
  e2e_regression: "✅ 11/11 GREEN (dev :3002). ERA HUÉRFANO (path no-colectado, 9 SC fantasma HB-96) + mocks contra contrato IMAGINADO (paths inexistentes: scheduling/services·free-doctors·availability·day-strip·crm/patients/search) + testids inventados. ARREGLADO: movido a e2e/regression/mateo/ + 5 paths de mock corregidos a los reales (offer/servicios, availability/{check,free-doctors,day-strip}, crm/patients) + SC-mini-vista selecciona médico (strip es por-doctor) + patient-picker→patient-picker-trigger (testId del kit) + limpieza dead-var."
  a11y_verified: "✅ 0 VIOLACIONES axe wcag2aa (manual-poll 3× + en specs). 4 reales arregladas: (1) aria-valid-attr-value CanalPicker (Tabs sin TabsContent → radiogroup); (2) button-name ServicePicker/DoctorPicker (aria-label); (3) scrollable-region-focusable ChatMessages @luana/ui-kit (tabIndex={0}, /pm-luana, promovido a main bd5bace1); (4) color-contrast CanalPicker inactivo (text-foreground/80)."
  prod_build: "✅ `next build` LIMPIO (13/13 static). Bug real arreglado: /onboarding/wizard useSearchParams sin <Suspense> (CSR-bailout, deploy-blocker que solo next build caza) → envuelto en Suspense. next.config: distDir+output env-gated (NEXT_DISTDIR/NEXT_NO_STANDALONE) para prod-build en host sin tocar el .next del contenedor docker. (Nota: e2e contra el prod-server tuvo un confound de env-injection [0 vars vs 82 en dev] → la verificación e2e canónica se corrió en dev con env completo: smoke 5/5 + regr 11/11.)"
  e2e_dev_flake: "`next dev --webpack` resetea intermitente chunks de boundary → SyntaxError en el gate anti-burbuja (falsos rojos en corridas largas tipo a11y). El shell es SANO (dsr='true'). NO es producto. Mitigado: prod-build ahora compila limpio (verificación determinística posible); las corridas dev pasan cuando la ruta está warm. HB pendiente (estabilizar dev o e2e-vs-prod en CI)."
  fixed_e2e_helper: "assertShellMounted (base.ts, HB-68) chequeaba div[aria-label='Interfaz principal Vitalia'] del AppShell MUERTO (pre-migración @luana/ui-kit). Verde-fantasma latente que el runner roto (HB-98) ocultó. Reapuntado a main#main-content[data-shell-ready='true'] (señal del kit) + timeout 20s (cold-compile dev)."
  ci_parity: "Docker (`--target test`) DEFERIDO por diseño (sentinel + Dockerfile sin stage test). Gate dev-phase real = NATIVO, corrido: BE ruff ✅ · FE eslint ✅ · FE vitest ✅ 2662/2662 · BE scheduling+crm ✅ 632. ÚNICOS rojos = ajenos a mateo (sales_agent EP3/inbound-seam + pgcrypto = WIP no-commiteado de adrian-canal-inbound). Cero código sales_agent tocado por mateo."
  next: "Batería COMPLETA verde. Listo para G (Chris ejerce live + firma chris_verify.signoff) → R (reconcile) → /auditor."
input_spec_signed: true                             # ✍ FIRMA 1 funcional (Chris 2026-06-21)
mockup_final_signed: true                           # ✍ FIRMA 2 mockup FINAL (Chris 2026-06-22)
ratified_by_chris: true
architecture_pattern: ADR-vitalia-004
adr_004_compliance: full
arch_run_on: 2026-06-22                             # /architect cerró ready package
verification_nature: funcional
autonomous_mode: false                              # architect propone; Chris ratifica
ready_package:
  arch: 03-arch.md (+ 03-arch-be.md + 03-arch-fe.md)
  validators: 04-validators.yaml
  guidelines: 05-guidelines.md
  tickets: 06-tickets.yaml                          # 9 tickets (5 BE + 4 FE)
  dispatch: dispatch-plan.md
promotion_precursor:                                # 4 atoms del canon → @luana/ui-kit
  gate: /pm-luana
  proposal: docs/promotion-protocol/proposals/2026-06-22-ui-kit-nueva-cita-atoms.md
  atoms: [FormActionBar, "Badge success|warning", "PageHeader back-pill", "EntityPicker.createAction"]
  soft_dep: true
  state: migrated                                   # ✅ 2026-06-22 · @luana/ui-kit 0.7.0 · consumible (workspace:*) → FE desbloqueado
created: 2026-06-21T00:00:00Z
priority: high
estimated_dev_days: 4-5                             # creció: + endpoint disponibilidad + constraint DB + chip + mini-vista + reasignar
dependencies:
  hard: []
  soft: [vitalia-scheduling-mateo-review, vitalia-fase2-mateo-pacientes]   # nace de live-QA D11 · reusa alta de paciente de D10
blocks_hard: []
blocks_soft: []
release: F2
cap_target: scheduling.mateo-agenda
cap_change_type: extend                          # mejora el form de create dentro de la cap agenda
parent_story: null

# Zona/caja del mapa (paradigm-arquitectura · derivada de SYSTEM-MAP.yaml)
zone: agentes
box: mateo
functional_area: mateo.agenda
---

# vitalia-fase2-mateo-nueva-cita — idea

**Origen:** D11 de la live-QA `vitalia-scheduling-mateo-review` (2026-06-21). El form "Nueva cita" funciona pero es inusable: médico = textbox de UUID a mano, servicio = texto libre, hora-fin manual.

**Goal:** Form "Nueva cita" usable sobre la agenda de Mateo.

**Scope candidato:**
- Médico → dropdown de `vitalia_doctors` (no UUID a mano).
- Servicio → dropdown de `vitalia_appointment_clinic_map.service_label` (no texto libre).
- Hora-fin → autocalc desde hora-inicio + duración del servicio (no manual).
- El form ya existe en `features/mateo` (abre vía botón "Crear nueva cita", `haspopup=menu`) — se cambian inputs, NO se crea pantalla de cero.

**Constraints:** CONSUME scheduling + `vitalia_doctors` + `clinic_map` · Select de `@luana/ui-kit` (no `<select>` nativo) · ENFORCE-CHECKLIST · Spanish neutro LatAm · NO toca core ni otras marcas.

**Next action:** `ready` (2026-06-22). `/architect` cerró el ready package: `03-arch.md` (+ `03-arch-be.md` + `03-arch-fe.md`) · `04-validators.yaml` (100% de los 28 SC + mutation HARD en create/EXCLUDE/availability + playwright_visual_scope + dev_app_verified) · `05-guidelines.md` · `06-tickets.yaml` (9 tickets: 5 BE + 4 FE, con assignment per ticket) · `dispatch-plan.md` (autonomous_mode:false · DAG 6 waves).
**Decisiones del architect:** RN-9 (dedup paciente) **FOLD** (ticket BE-5 liviano, cierra hueco PHI · D-C). EXCLUDE constraint en `vitalia_appointment_clinic_map` brand-local (mirror cols start/end/status) → **NO toca engine** (D-A/D-E.1). DayAvailabilityStrip = componente feature scheduling, lift-candidate core NO ahora. 4 átomos del canon = **PROMOTE** vía `/pm-luana` (precursora P-0, soft-dep de los tickets FE) · contrato en `mockups/PROPOSED-CANON-ATOMS.md`. `CrearCitaForm`/`CrearCitaButton` modal MUERE (D-G · AC-9 hoja full-page).
→ **Próximo: `/dev-team` build EN CURSO** (2026-06-22). P-0 ✅ cerrado (`/pm-luana`, ui-kit 0.7.0 migrated, FE desbloqueado). `/pm-vitalia` transicionó `ready→developing` + handoff `/dev-team vitalia`. DAG 6 waves (9 tickets: 5 BE + 4 FE). `autonomous_mode:false` → dev-team pausa en **G** (`AWAIT_CHRIS_VERIFY`) para live-verify de Chris en dev-app (Rule #37) antes del auditor.
