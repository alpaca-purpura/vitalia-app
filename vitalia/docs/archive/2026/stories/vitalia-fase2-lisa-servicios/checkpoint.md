---
story_id: vitalia-fase2-lisa-servicios
type: ui-story
agent_owner: lisa
map_zone: agentes
map_box: lisa
module: offer
capability: lisa.servicios
state: done
phase: DONE    # ★ Fase F merge 2026-06-19: auditor APPROVED (CHECKPOINTS C1-C5) + chris_verify.signoff SATISFIED_WITH_FOLLOWUPS + 07-merge.md + cap offer.lisa-servicios→live + archived. Squash wip/vitalia→main = paso manual Chris-gated (staging deploy MANUAL). open_items = follow-ups visibles.
dod_live_verified: true          # DoD#37 core happy-path verified live (create+autosave+activate writes · BE logs · DB · keystone). dod_evidence abajo. NO fake.
dod_env: "make dev-app-vitalia → dev-app.vitalialat.com (Chrome DevTools MCP · LUANA_LANE=A) · tenant Sanaré LATAM e69a691d-… · dr.demo@vitalialat.com (owner)"
dod_evidence:
  - action: "Crear servicio personalizado 'Limpieza dental profunda' ARS 8000 (POST /api/v1/offer/servicios/custom)"
    observed: "redirect a workspace /[offer-id]/resumen · servicio renderiza con nombre/peldaño/modalidad"
    backend_log: "POST /offer/servicios/custom → 201 · products row id=83f6b6db-… status=draft currency=ARS amt=8000 (engine ProductModel · keystone D-1)"
  - action: "Autosave nombre en Resumen (PATCH /api/v1/offer/servicios/{id})"
    observed: "EntityPicker refleja nombre nuevo sin recargar · indicador autosave"
    backend_log: "PATCH /offer/servicios/83f6b6db-… → 200 · DB products.name = 'Limpieza dental profunda (live-verify · autosave)'"
  - action: "Activar servicio desde card del catálogo (POST /api/v1/offer/servicios/{id}/activate)"
    observed: "switch Activo togglea · card pasa a activo"
    backend_log: "POST /offer/servicios/83f6b6db-…/activate → 200 · growth_studio_event_emitted event_type=service_activated · DB products.status = active"
  - action: "KEYSTONE AC-6 — offer activo en la tabla engine 'products' (tenant-scoped) que lee TenantKnowledgeBuilder.build_identity"
    observed: "DB products status=active tenant=e69a691d-… (data shape correcta; path consume-only unit-tested test_keystone_offer_shape.py)"
    backend_log: "n/a (verificado por DB + unit test · build_identity live no ejercido — requiere contexto agente completo)"
  - action: "RECONCILE G round 1 (2026-06-16) — autosave de CAMPO RICO 'Descripción corta' (description_long) en Resumen (PATCH /api/v1/offer/servicios/{id})"
    observed: "workspace ahora = mockup: 6 grupos COLAPSABLES con contador (Identidad abierto, resto cerrado) · StatusBar (Activo + chip) · KnowledgePanel montado · campos hidratados. El campo rico es editable (antes placeholder muerto)."
    backend_log: "PATCH /offer/servicios/83f6b6db-… → 200 OK (NO 422) · request {description_long:...} · response devuelve description_long persistido + los 19 campos ricos (read-path) · sin traceback. Evidencia: .live-verify/live-servicio-workspace-after.png"
verified_at: 2026-06-16
dod_bugs_fixed_during_verify:
  - "POST /custom → 500 'relation products does not exist' → migration 046 (engine offer tables · metadata.create_all checkfirst). commit 9884d313"
  - "Resumen leaf crash (RichSelect/useFormContext null fuera de shadcn Form) → plain Select. commit 9884d313"
dod_open_findings:    # NO bloquean el happy-path; triage Chris/reconcile/auditor
  - "F1 (medium · wiring): ServiceStatusBar huérfano — layout.tsx renderiza ServicioWorkspaceShell directo, NO ServicioWorkspaceView (que monta ServiceStatusBar). El workspace NO tiene toggle Activo/ChipOrigen/FichaCompletenessChip. Activar SÍ funciona vía card del catálogo. RN-10/AC-19 parcial en workspace."
  - "F2 (HIGH · contrato BE / architect-gap): ServicePatchRequest sólo acepta {public_name, price, category, modality}. Los campos ricos de la ficha (descripción corta, qué incluye, procedimiento, resultados, riesgos, cuidados, RN-26 §6 'ficha completa editable') son textareas SIN onChange/persistencia (placeholders) porque el dominio/DTO offer no los modela. No-bug del builder; falta extender el contrato (reconcile)."
  - "F3 (low): tipo de cita inicial (appointment_type RN-32) no persiste (sin campo BE). Select renderiza pero el valor no se guarda."
sub_phase_a_progress:
  done: [T-1, T-2, T-3, T-4, T-5, T-6, "T-7-m0", "T-7-UI", "T-8-tests", "T-8-live-verify (core)"]    # all GREEN + committed + pushed
  remaining: ["chris_verify.signoff (funcional · G) — Chris ejerce el kit + triage F1/F2/F3", "visual goldens 8 (project=visual 0.001) — pendiente (opcional pre-merge · live-verify cubrió el render real)", "post-signoff: /auditor → STOP-2 /pm-luana Sub-phase B (RAG)"]
  last_commit: 9884d313
  resume: "/dev-team vitalia vitalia-fase2-lisa-servicios — G ROUND 2 fix-loop · ACTIVO: G2-F11 (autosave laggy). F1-F10 + PlanPago + PEN ya construidos+pusheados (commits en findings_round2*). G2-F11 per ADR-vitalia-009 (accepted): (1) migrar ~15 textareas ricos de ResumenView.tsx de value={servicio.X} a RHF (Controller/register · value del form · onChange=field.onChange + schedule · extender resumenSchema con los 15 campos · form.reset dep=servicio.offer_id ya existe); quitar TODO value={servicio.X} de inputs editables. (2) arch-fitness test FE nuevo `vitalia/frontend/src/__tests__/architecture/test-autosave-value-from-local-state.test.ts` (acotado a archivos que importan useAutosave · FLAG value={<obj>.<x>} cuyo obj-raíz ∉ {field,form,useState} · ratchet KNOWN_ allowlist shrink-only · ResumenView SALE de allowlist al mergear este fix). (3) regression RED SIN mockear use-autosave en ResumenView.test.tsx (tipear en description_long → assert value=lo tipeado, NO server). NumberWithUnit/Select/VariantsRepeater = nice-to-have no-bloqueante. Tras fix → re-live-verify autosave en stack dev real (tipeo fluido, servicios = Marca/Identidad) → re-live-verify visual F7 (dropdown sobre StatusBar) + F10 (confirmado) → chris_verify.signoff → /auditor. Amendment canon §2.6 = proposal /pm-luana aparte (no bloquea). Visual goldens 8 pendientes."
architecture_pattern: ADR-vitalia-004
adr_004_compliance: full
ready_package_closed_at: '2026-06-15T20:00:00.000Z'
developing_started_at: '2026-06-15T20:30:00.000Z'
build_claim: 'released (live-verify done · pid573293)'
last_modified: '2026-06-19T00:00:00.000Z'
chris_verify:
  required: true                   # funcional (verification_nature: ambas · demo_required)
  signoff:                         # ★ formalizado en R (2026-06-19) registrando el sign funcional verbal de Chris
    by: Chris
    date: 2026-06-19
    result: SATISFIED_WITH_FOLLOWUPS   # severity ≤ medium → habilita merge (story-closure-gate Fase F)
    notes: >
      Chris ejerció live el workspace completo tras G2-F14b y confirmó funcional OK ("ya, queda, por fin").
      Los gates verdes NO cazaron la tanda de G — los cazó su live-verify (valor de G demostrado).
      Firma registrada por /pm-vitalia al cerrar la Fase R (Chris pidió hacer R + cobertura total docs/caps/
      gherkins/tests en conversación nueva ANTES del auditor). open_items = follow-ups NO bloqueantes (stories
      spawneadas + cobertura de tests deferida).
    open_items:
      - "Follow-up: vitalia-tenant-currency-config (kill ?? USD · primary/secondary ISO 4217 tenant-owned · absorbe G2-F9 + ARS/PEN)"
      - "Follow-up: vitalia-fase2-adrian-ficha-rica-knowledge (modelo de conocimiento del servicio para Adrián)"
      - "Follow-up: vitalia-accordion-dedup-cleanup (dedup de acordeones del workspace)"
      - "Deferred test coverage (04-validators § RECONCILE): E2E happy-path (VR-D1) + visual goldens 8 (VR-D2) + contract-test FE↔BE (VR-D3 · HB-42)"
      - "Sub-phase B RAG (VR-D4): engine-lift /pm-luana (STOP-2)"
      - "Promoción ADR-vitalia-009 → canon platform §2.6 (autosave value-binding contract): proposal /pm-luana (no bloquea)"
  rounds:
    - round: 1
      date: 2026-06-16
      trigger: "Chris ejerció live, vio el workspace 'horrible' (colapsables aplanados, campos muertos) → scope-delta ratificado"
      scope_delta: "extender contrato BE (ficha rica) + fidelidad mockup + molécula reutilizable CollapsibleSection (@luana/ui-kit · promotion accepted)"
      built: "T-R0 CollapsibleSection (ui-kit · 18) · T-R1 BE widen DTO read+write + routing (33 ticket · 154 offer · 342 arch) · T-R2 StatusBar en Shell + borrar View huérfano (11) · T-R3 ResumenView 6 colapsables + hidratar+autosave + KnowledgePanel (668 vitest). commits 286bb833→e1ee335e (pushed)"
      re_live_verified: "PATCH description_long → 200 (NO 422) · workspace = mockup · BE log + response confirman persistencia. .live-verify/live-servicio-workspace-after.png"
      resolved: [F1, F2, F3]
    - round: 2
      date: 2026-06-17
      trigger: "Chris ejerció live tras round 1 → 3 comentarios concretos. signoff NO firmado — round 2 fix-loop en /dev-team."
      scope_delta: "fidelidad padding cross-view + confirm dialog en activar + invalidate detail(offerId) + null-safety EntityPicker (core hardening Chris-ratified)"
      findings:
        - "G2-F1 (medium · fidelidad rule#34): views sin gutter horizontal — LisaServiciosView root <div space-y-4> sin px-*, layout shell no inyecta padding, KnowledgePanel mx-5 inconsistente. Contenido pegado a los costados en TODAS las vistas (catálogo·escalera·workspace). Esencia OK (aprovechar el ancho) — falta el respiro lateral."
        - "G2-F2a (low · UX add · Chris-pedido): activar servicio sin aviso — debe mostrar confirm dialog antes de activar."
        - "G2-F2b (medium · bug): useActivateServicio.onSuccess invalida lists()+escalera() pero NO detail(offerId) → StatusBar del workspace no refleja la activación hasta refresh full (el POST sí persiste · por eso al refrescar aparece activo)."
        - "G2-F3 (HIGH · crash): EntityPicker (core @luana/ui-kit) deriveInitials(value.name) revienta con name undefined; entity={name:servicio.public_name} → al marcar especialista el detail vuelve con public_name undefined → 'Cannot read properties of undefined (reading trim)'. Fix DOBLE ratificado Chris (AskUserQuestion 2026-06-17): (a) caller vitalia guard + diagnosticar por qué el detail pierde public_name al marcar especialista, (b) core hardening deriveInitials null-safe vía /pm-luana lift gate."
      decision_f3: "ambos (core + vitalia)"
      findings_round2b:    # 2026-06-17 segunda tanda de Chris ejerciendo G round 2
        - "G2-F4 (medium · bug 404): 'Ver detalle' del doctor en EspecialistasView linkeaba a /lisa/doctores/{id} (+ empty-state /lisa/doctores) — ruta inexistente → 404. El directorio/detalle de doctores vive en /lisa/staff. FIXEADO commit 2eabe9bd (2 hrefs + tests)."
        - "G2-F5 (medium · console runtime error): al entrar a un servicio → 'Failed to execute measure on Performance: OfferIdPage cannot have a negative time stamp' (Next 16.2.6 dev instrumentation). Root: [offer-id]/page.tsx hace redirect() in-render a /resumen; en soft-nav intra-route-group con shell ssr:false dispara el error del Router interno de Next (MISMA clase que learning 2026-06-03-next16-softnav-redirect). FIXEADO commit <pending>: regex [offer-id]→resumen agregada a N3_DEFAULT_LEAF (shell-routes.ts) + 5 tests (shellInRenderRedirectTarget ahora cubierto). El redirect() de page.tsx queda como fallback SSR."
      upstream_finding_currency:    # NO es bug de lisa-servicios → historia nueva /pm-vitalia
        - "Chris vio moneda ARS en los precios. NO es bug de esta story: lisa-servicios consume locale.currency correctamente (nunca hardcodea). El ARS sale de (1) useTenantLocale.ts VITALIA_DEFAULT_LOCALE.currency='ARS' hardcoded (story vitalia-fe-tenant-resolution 2026-06-01) + (2) seed Sanaré default_currency='ARS' + clerk-sync que NO pushea currency a publicMetadata. → historia nueva 'tenant currency config' (primary+secondary ISO 4217, tenant-owned, kill fallback ARS) + flip test tenants a PEN. Owner /pm-vitalia."
      built: "commit 9b3c0a13 (pushed) + 2eabe9bd (G2-F4). G2-F1 gutter p-5/p-6 (LisaServiciosView + ServicioWorkspaceShell leaf · StatusBar full-bleed) · G2-F2a AlertDialog confirm al activar (ServiceStatusBar) · G2-F2b useActivateServicio setQueryData(detail) con ServiceDetailDTO del BE · G2-F3 root cause sistémico: 7 hooks de mutación anidada (specialists/testimonials/cases/sales-brief) dejaban de corromper el cache (setQueryData(detail,<sub-DTO|204>) → invalidateQueries(detail) + tipado honesto) + core hardening deriveInitials null-safe (@luana/ui-kit · proposal 2026-06-17-ui-kit-entity-picker-null-safe accepted). Gates: ui-kit EntityPicker 7/7 + vitalia tsc 0 + eslint 0 + servicios 146/146 + arch 190/190. Regression tests: EntityPicker null-safe + ServiceStatusBar confirm."
      re_live_verified: "PENDIENTE Chris G exercise — /dev-team arregló root causes + gates verdes; NO se fingió dod_evidence (lane B = perfil Chrome sin auth Clerk; re-live-verify de los 4 = ejercicio de Chris en G). Stack live (core/ bind-mounted en FE container → HMR ya sirve los fixes)."
      resolved: []
  open_items: [G2-F1, G2-F2a, G2-F2b, G2-F3, G2-F4, G2-F5, G2-F6, "PlanPago-build", G2-F7, G2-F8, G2-F9, G2-F10, G2-F11, G2-F12, G2-F13, G2-F14]   # F1-F6 + F5 construidos+gate-green. PlanPago-build (decisión Chris 2026-06-17: separados + construir ahora) en curso. F7-F10 = cola "revisar al final". G2-F11 (autosave perf · BUILT e6f97173). G2-F12 (sales-brief faq/objections 500 · BUILT cc4a2ea9+54119aaf+5bfa7d4a). G2-F13 (Especialistas habilitados mostraba UUID no nombre · BUILT BE f40556ea + FE 8a51ad4b: SpecialistLinkDTO += display_name/specialty enriquecido vía DoctorRosterPort existente —NO-PHI, sin audit— + X-Clinic-ID opcional en detail (degrada grácil); FE renderiza nombre+especialidad+iniciales, fallback id-corto no-UUID. Gates BE offer 164 + arch 361 · FE 9 regression + servicios suite verde. useDoctor descartado=PHI-audit). G2-F14 (Plan de pago: montos desaparecen al cambiar + crash al recargar 'Cannot read undefined enabled' PlanPagoView:241 · BUILT FE c0e89ca1: useForm usaba SOLO values sin defaultValues → objetos anidados reservation/advance/financing undefined en el 1er render post-load → watch('reservation').enabled crashea + form.getValues() parcial → buildFullPricingFromForm mandaba pricing incompleto = no round-trip = desaparecen. Fix defaultValues full-shape + values re-sync + ?. defensivo. BE pricing round-trip OK —to_domain línea 431, no bug—. Regression sin-crash en transición undefined→defined. tsc 0+eslint 0+servicios 162/162. Otra vez falso verde: test (d) renderizaba pricing null en verde pero no reproducía el timing de values del runtime). ★ G2-F14b (2026-06-18 · Chris re-ejerció: montos ya no se borran en sesión pero VACÍOS al recargar): ROOT CAUSE determinístico (probado en el dato, no live —lane sin auth Clerk—): el BE serializa Decimal money como STRING JSON (`"amount":"100"` · confirmado corriendo el DTO real: jsonable_encoder(ReservationConfigDTO)→`"100"`); NumberWithUnit.tsx:73 hace `value={Number.isFinite(value)?String(value):""}` y `Number.isFinite("100")`=false (no coerciona) → input VACÍO al recargar. En sesión el valor es number (tipeado) → anda; al recargar viene string → vacío. El test (c) usaba fixture number → falso verde. FIX FE commit 2dc86a85: `toNum()` coerciona price+reservation.amount+advance.amount string→number en pricingToFormValues (borde wire→form). El BE manda string a propósito (precisión de plata) — el FE parsea. Regression con strings reales del wire. tsc 0+eslint 0+servicios 163/163. ⚠️ GAP infra: /pm-vitalia no puede live-verify (lane B sin auth Clerk) → el live lo ejerce Chris; flaggear como harness-issue (lane-auth para self-serve live-verify). signoff bloqueado.
  findings_round2c:    # 2026-06-17 · Chris agregó (revisar AL FINALIZAR lo pendiente: PlanPago build + PEN)
    - "G2-F6 (medium · bug): plan-pago price field quedaba 0/vacío tras guardar/refrescar (RHF defaultValues no re-hidrata). FIXEADO commit e7d5766f (values + regression test)."
    - "PlanPago-build (Chris ratificó 2026-06-17 AskUserQuestion): mantener reserva/anticipo SEPARADOS + construir Plan de pago completo al mockup ratificado (wire BE pricing ThreeChargePricing + canon UI + calculados ≈equivale/≈por mes). El BE ya modela todo; la FE era stub Sub-phase A. EN CURSO /dev-team."
    - "G2-F7 (medium · z-index): el popover del EntityPicker (cambio de servicio) renderiza DEBAJO/detrás del ServiceStatusBar (barra Activo/Estándar). Evidencia /tmp/101.png. Fix: z-index del popover > StatusBar (sticky z-10). COLA."
    - "G2-F8 (low · orden): KnowledgeSourcesPanel ('Fuente de conocimiento') montado al FONDO del workspace (ServicioWorkspaceShell) — debe ir ARRIBA de todo. COLA."
    - "G2-F9 (medium · currency): catálogo + escalera muestran un símbolo de moneda que NO es la del tenant (ServiceCard/RungColumn `?? USD`). Extiende el problema de currency a esas vistas → historia currency + el fast-track PEN. COLA."
    - "G2-F10 (medium · routing detalle): en el detalle de un servicio sigue apareciendo el SubSubTabsBar (Catálogo/Escalera N3) — NO debe. Y el root-pill back debe ser origin-aware: si entré desde Catálogo → botón 'Catálogo' (vuelve a catálogo); si desde Escalera → 'Escalera' (vuelve a escalera). Hoy siempre dice 'Servicios'. COLA."
    - "G2-F11 (HIGH · perf+correctness autosave · cross-module): en ResumenView los ~18 campos ricos tienen value={servicio.X} (atado a react-query) + onChange→schedule sin estado local → cada setStatus de useAutosave re-renderiza y fuerza el value al server atrasado → 'procesa cada letra, solo guarda la última'. Marca/Identidad anda porque usa RHF local (value del form, nunca del server). El hook use-autosave ya es compartido; lo NO estandarizado es el binding del value. Chris (AskUserQuestion 2026-06-17): camino FORMAL → /architect formaliza contrato de campo-autosave en ADR-vitalia + amendment canon §2.6 + diseña gate (arch-test/eslint + checklist auditor-frontend) → luego /dev-team migra los 18 campos a RHF. ★ ADR-vitalia-009-autosave-field-contract.md ESCRITO (accepted): contrato (value SIEMPRE de RHF local, prohibido value={queryData.x}) + gate arch-fitness FE acotado a archivos con useAutosave (ratchet, ResumenView en allowlist hasta fix) + checklist auditor-frontend + scope fix (~15 textareas ricos → RHF, 1 comp+schema+tests con regression RED sin mockear el hook) + nota promoción canon §2.6 vía /pm-luana (se alinea con ADR-012-autosave-primitive-platform). Insight clave: ResumenView.test.tsx MOCKEA use-autosave → status congelado idle → loop inexistente en test = falso verde. Decisión /pm-vitalia: fix va EN el fix-loop G round 2 (NO story separada — es finding live directo), gate en el mismo ticket, amendment canon = proposal async no-bloqueante. ★ G2-F12 (2026-06-18 · Chris ejerció 'Para Adrián'): 'Agregar pregunta'/'Agregar objeción' → nada + toast 'Error al guardar'. ROOT CAUSE = bug BE 500: PATCH /servicios/{id}/sales-brief con {faq:[{question,answer}]} → patch_sales_brief model_dump deja faq como list[dict] → sales_brief_service._apply hace setattr(brief,'faq',value) crudo (dominio espera list[FaqPair] VOs) → repo update faq_to_list(brief.faq) hace f.question sobre dict → AttributeError 500 → FE 'Error al guardar'. Campos texto (defaultValue, str) andan; solo faq/objections (VOs JSONB) revientan. Path nunca live-verificado con add real. 'No sucede nada' = FaqPairList value sale de brief?.faq (server) → add solo aparece tras refetch, que no ocurre por el 500. Chris (AskUserQuestion 2026-06-18): scope BE+FE. FIX: BE _apply coerce faq/objections list[dict]→VOs vía faq_from_list/objections_from_list (ya en serializers.py) + regression test (PATCH faq → RED AttributeError hoy); FE FaqPairList/ObjecionPairList a estado local per ADR-009 (tecleo fluido en pares). builder-backend + builder-frontend en paralelo. ★ G2-F12 BUILT (pushed): BE commit cc4a2ea9 (_apply coerce faq/objections list[dict]→VOs + 4 regression tests, isinstance FaqPair/ObjectionPair, 500→200) + FE commit 54119aaf (FaqPairList/ObjecionPairList estado local + key={offerId} re-hidrata + regression no-revert). Gates: BE ruff+pytest offer 15 verde + arch · FE tsc 0+eslint 0+vitest servicios 156/156 (re-run independiente /pm-vitalia). ★ G2-F12b (2026-06-18 · Chris re-ejerció): agregar par VACÍO → AÚN 'Error al guardar'. Docker logs (verdad live) = el fix BE cc4a2ea9 SÍ corre pero el par vacío revienta en FaqPair.__post_init__ (vos.py:108 _require_text) → ValueError 500. El VO exige ambos campos no-vacíos (INVARIANTE CORRECTO — no se debilita). Bug real = FE dispara autosave de un par vacío apenas se clickea Agregar. Lección: el test BE 'add par vacío no rompe' fue FALSO VERDE (no construyó el VO por el path real) — lo cazó la live-verify de Chris (otra vez ADR §1.3). FIX FE commit 5bfa7d4a (pushed): ParaAdrianView filtra pares INCOMPLETOS del payload + skip schedule si no cambió vs server → fila vacía queda local, guarda recién con el par completo (pedido literal de Chris). Regression ParaAdrianView.test.tsx (add vacío no schedulea + guarda solo con ambos campos). Gates tsc 0+eslint 0+vitest servicios 158/158. PENDIENTE: Chris re-live-verify 'Para Adrián' (agregar vacío = sin error/sin save · completar par = guarda · tecleo fluido). ★ BUILT commit e6f97173 (pushed): ResumenView 15 campos ricos value={servicio.X} → RHF Controller (value del form) + arch-test FE test-autosave-value-from-local-state.test.ts (PASS · 0 violations · ResumenView NO necesitó allowlist) + regression sin-mock (cycling status + rerender → assert value=lo tipeado, RED→GREEN per ADR §1.3). Gates verdes (tsc 0 · eslint 0 · vitest 22/22, re-run independiente /pm-vitalia). PENDIENTE: Chris re-live-verify autosave FLUIDO en dev-app (servicios = Marca). ⚠️ flag NO-G2F11: arch-test test-no-div-layout 305>301 baseline = deuda pre-existente (verificado git stash, NO de este fix) → harness-issue aparte."
reconciled: true                   # ★ /pm-vitalia R cerrado 2026-06-19: 01-spec §Gherkin RECONCILE §17-22 + §Matriz reconciliada · 04-validators §RECONCILE (VR-1..10 must_pass + VR-D1..D4 deferred HB-79) · cap offer.lisa-servicios (beta · scenarios/business_rules/access/test_coverage · cap-doctor 0) · modules/offer.md · chris_verify.signoff formalizado · 3 follow-up stories spawneadas (idea) · learning 2026-06-19-unit-green-not-runtime-truth (promotable:candidate). Precondición B (auditor) OK.
defer_audit: true                  # HB-79 spawn-ledger ratified: 3 follow-up stories in module:offer added to deferred-ledger; no auditor progression until parent merged (story-closure-gate § HB-33 exception). Ratify 2026-06-19.
agentic_reframe: 2026-06-06
input_spec_signed: true            # ✍ FIRMA 1 (intención) Chris 2026-06-06
mockup_final_signed: true          # ✍ FIRMA 2 (visual) Chris 2026-06-15 ("queda" + confirmó pasar a architect)
ratified_by_chris: true            # spec RONDA 2 (Gherkin + Matriz) ratificado Chris 2026-06-15
ratified_visual_by_chris: true     # shell-mockup-per-component (ADR-vitalia-003)
ratified_visual_at: '2026-06-15T18:00:00.000Z'
ratified_visual_iter: final
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-fase2-lisa-servicios/mockups/catalogo.html
  - vitalia/docs/product/stories/vitalia-fase2-lisa-servicios/mockups/escalera.html
  - vitalia/docs/product/stories/vitalia-fase2-lisa-servicios/mockups/servicio-workspace.html
  - vitalia/docs/product/stories/vitalia-fase2-lisa-servicios/mockups/nuevo-servicio.html
autonomous_mode: true              # Chris opt-in 2026-06-15 (architect→done autónomo); /architect ratifica criterios safe en dispatch-plan
parallel_safe: true
priority: high
estimated_dev_days: 5-6
dependencies:
  hard:
    - vitalia-fase1-empty-states
    - vitalia-fase1-routing-shell
  soft:
    - vitalia-fase2-lisa-doctores
    - vitalia-fase2-lisa-marca
blocks_hard: []
blocks_soft:
  - vitalia-fase2-adrian-propuestas
  - vitalia-fase2-valeria-agenda
reuse_map_summary: >-
  CONSUME Offer Studio engine (core/luana-core-offer-studio) vía Extension SDK EP-2 preset pack —
  servicios = Offer (NO Treatment/LadderSlot nuevo; el peldaño = OfferValueLevel del engine) ·
  EXTEND lisa-marca (voz para descripciones) + lisa-doctores (roster para link servicio↔doctor) ·
  NEW UI canvas escalera (drag-drop sobre value_level) + N3-dyn detalle servicio + ladder-slot
  workspace + link servicio↔doctor brand-level · CERO edit engine
spawned_at: 2026-05-22T00:00:00.000Z
ready_package:
  produced_by: /architect
  produced_at: '2026-06-15'
  files: [03-arch.md, 03-arch-be.md, 03-arch-fe.md, 03-arch-agentic.md, 04-validators.yaml, 05-guidelines.md, 06-tickets.yaml, dispatch-plan.md]
  phasing:
    sub_phase_A: "NO-RAG · autonomous · T-1..T-8 (8 buildable tickets) · builds to live-verified"
    sub_phase_B: "RAG · engine-lift /pm-luana · GATED (T-B1/B2/B3 blocked · dimension only)"
  hard_stops:
    - "STOP-1: chris_verify.signoff (funcional · merge gate)"
    - "STOP-2: /pm-luana engine-lift OK para Sub-phase B (RAG indexer + sales_agent retrieval tool)"
next_action: >-
  ★ R CERRADO 2026-06-19 (reconciled:true + chris_verify.signoff=SATISFIED_WITH_FOLLOWUPS). AUTO-HANDOFF
  → /auditor vitalia vitalia-fase2-lisa-servicios. El auditor lee docs RECONCILIADOS: 01-spec §Gherkin
  RECONCILE §17-22 + §Matriz reconciliada (G round → test real) · 04-validators §RECONCILE (VR-1..10
  must_pass:true · VR-D1..D4 deferred must_pass:false — NO correr como gate HARD) · cap offer.lisa-servicios
  · chris_verify.signoff.open_items = scope ratificado (3 follow-up stories idea + deferred test coverage +
  RAG sub-phase B + ADR-009 promoción). El hueco más grande para el auditor: E2E happy-path (VR-D1, owner
  Carril R un-skip + seed offer-id). Todo construido+pusheado+gates verdes; Chris confirmó funcional live.
release: F2
cap_target: lisa.servicios
cap_change_type: new
parent_story: null
---

# F2-S9 vitalia-fase2-lisa-servicios — checkpoint

## ⚠️ Re-refinamiento agéntico 2026-06-06 — el "Scope verbatim" de abajo está PARCIALMENTE OBSOLETO

La story se escribió 2026-05-22 bajo visión pre-agéntica. Re-refinada por `/pm-vitalia` 2026-06-06.
**SSoT del reframe + recomendación + prior-art completo: `00-research.md`.** El "Scope verbatim",
"Reuse map" y "Deliverables" de abajo se reescriben en `01-spec.md` vía `/po-ux`. Lo que cambia:
servicios = **Offer Studio offers** (no `Treatment`/`LadderSlot` engine nuevo) · el peldaño =
`OfferValueLevel` del engine · CERO edit engine (consume EP-2) · `module: treatments → offer`.

## Prior art scan (anti-duplication-refining · 2026-06-06)

| Fuente | Resultado | Decisión |
|---|---|---|
| `core/luana-core-offer-studio` (engine) | `OfferValueLevel` + `value_level_catalog` + `Offer`/`ServiceDetails` + `OFFER_LADDER_HINTS` (filas `PROFESIONAL_SALUD`) | **CONSUMIR vía EP-2** — catálogo + escalera YA existen como ontología engine. NUNCA recrear. |
| `core/luana-core-sales-agent/knowledge_builder.py` | `TenantKnowledgeBuilder.build_identity()` ya lee `offer_repo` + preset | El agente lee el catálogo **sin plomería nueva** (desbloquea canal-inbound RN-16) |
| `vitalia/treatments/` (propio) | followup de Camila (PHI), NO catálogo | NO reuse como catálogo (premisa original falsa, corregida) |
| `vitalia/` lisa-marca (done) | brand voice slot 5 | CONSUMIR (descripciones en voz de marca) |
| `vitalia/` lisa-doctores (developing) | `vitalia_doctors` + specialty | EXTENDER (link servicio↔doctor) |
| `comunify/` live | offer ladder creator (no clínico) | patrón análogo, confirma ontología transversal |

Detalle: `00-research.md § 2`.

## Decisión Chris 2026-06-06 (ratificada — AskUserQuestion)

1. **Alcance MVP = CANVAS COMPLETO** (drag-drop escalera + ladder-slot workspaces + analítica
   conversión + tabs Reseñas/Stats). Anti-objetivos que siguen fuera: A/B pricing · imports bulk ·
   AI suggested-pricing.
2. **Cableado agéntico:** `lisa-servicios` posee la **DATA** (Offers publicadas + link
   servicio↔doctor); el tool `match_service_and_specialist` vive en **canal-inbound**.
3. **Esta story es la KEYSTONE** del catálogo: desbloquea canal-inbound (refined, hard-dep),
   propuestas (F4) y landing-public (F6). DEBE entregar: (a) Offers publicables con campos
   agente-facing (§ 00-research) + (b) link servicio↔doctor persistido.

## Goal

Sub-tab Servicios de Lisa: **toggle Catálogo | Escalera de valor** (per `offer-expert` ontology). 

- **Catálogo:** vista tradicional CRUD treatments (nombre · descripción · duración · precio · doctores · imagen).
- **Escalera:** canvas visual con slots por rol estratégico (lead-magnet · tripwire · core · profit-maximizer · return-path) que mapean treatments → posiciones en escalera de valor con pricing override + cta_copy.

NEW model `LadderSlot` per `offer-expert` skill (ontology shipped en `core/luana-core-offer-studio`).

## Anti-objetivos

- NO duplicar `Treatment` model shipped
- NO tocar `core/luana-core-offer-studio` engine — usar Extension SDK EP-2 preset packs si LadderSlot domain está en engine
- NO implementar AI suggested-pricing (out-of-scope MVP)
- NO implementar A/B testing pricing (story future)
- NO implementar imports bulk (story future)

## Scope verbatim

### § 1 — Page + toggle view

`vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/servicios/page.tsx`:

```tsx
import { LisaServiciosView } from '@/features/lisa/components/servicios/LisaServiciosView'

export default async function Page({ params, searchParams }: PageProps) {
  const { view = 'catalogo' } = await searchParams  // 'catalogo' | 'escalera'
  return <LisaServiciosView initialView={view} />
}
```

### § 2 — `LisaServiciosView` toggle

Composición:
1. `<ServiciosHeader>` — Toggle Catálogo|Escalera (Shadcn `Tabs`) + "+ Nuevo servicio" + filter especialidad
2. Variant `<CatalogoView>` o `<EscaleraCanvas>` según view

### § 3 — `CatalogoView` (vista tradicional)

`vitalia/frontend/src/features/lisa/components/servicios/CatalogoView.tsx`:

Grid cards treatments:
- Imagen (S3 upload)
- Nombre + especialidad badge
- Duración + precio
- Doctores asignados (avatars)
- Stats tiny (sessions/mes · revenue/mes)
- Click card → workspace N3-dyn `[treatment-id]`

### § 4 — `EscaleraCanvas` (★ value ladder)

`vitalia/frontend/src/features/lisa/components/servicios/EscaleraCanvas.tsx`:

Canvas visual con 5 columns (slots) per ontology offer-expert:

```
┌─────────────────────────────────────────────────────────────────┐
│ LEAD-MAGNET │ TRIPWIRE  │   CORE     │ PROFIT-MAX │ RETURN-PATH │
│   (gratis)  │  (low $)  │  (anchor)  │  (premium) │  (recurring)│
├─────────────┼───────────┼────────────┼────────────┼─────────────┤
│ Evaluación  │ Limpieza  │  Implante  │  Carillas  │  Mantenim.  │
│  gratuita   │   $25     │   $1500    │   $2500    │   anual     │
└─────────────────────────────────────────────────────────────────┘
```

Cada slot card:
- Drag-drop treatments existentes desde panel lateral derecho ("Treatments sin escalera")
- Slot card muestra: rol + treatment_ref + pricing_override + cta_copy
- Click slot → drawer detalle inline para editar overrides

Sin escalera obligatoria — slots vacíos permitidos. Drop treatment a slot: backend POST `/api/treatments/ladder-slot` con role + treatment_id + tenant_id.

### § 5 — N3-dyn workspace `[treatment-id]`

`vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/servicios/[treatment-id]/page.tsx`:

Tabs:
- **Detalle** — Nombre · especialidad · descripción (alimentado por voice brand) · duración · precio base · imágenes
- **Doctores** — Multi-select doctors disponibles para este treatment
- **Plan pago default** — Si treatment >$X → default plan installments
- **Reseñas** — Lista público-visible reviews (consume F2-S11 voz signals · read-only)
- **Stats** — Sessions/mes · revenue · LTV per patient

### § 6 — N3-dyn workspace `ladder/[slot-id]`

`vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/servicios/ladder/[slot-id]/page.tsx`:

Detalle slot escalera:
- Rol estratégico
- Treatment referenciado (link al treatment workspace)
- Pricing override (vs base price)
- CTA copy (texto botón / mensaje promo)
- Performance: conversion rate slot anterior → este slot

### § 7 — Catalog Version + arch fitness

Per `offer-expert` rule:
- Cualquier change LadderSlot domain → bump `_CATALOG_VERSION` en `core/luana-core-offer-studio` (escalate `/pm-luana` si engine touch)
- Arch fitness test corre ambos stacks

Vitalia consume LadderSlotDef via Extension SDK EP-2 preset packs — sin tocar engine.

## Acceptance criteria

| AC | Verificación |
|---|---|
| AC-1 | Toggle Catálogo|Escalera persiste URL `?view=X` |
| AC-2 | CatalogoView grid cards funciona |
| AC-3 | EscaleraCanvas drag-drop treatment → slot funciona |
| AC-4 | Slot detalle drawer edita override + cta_copy |
| AC-5 | Workspace `[treatment-id]` tabs funcionan |
| AC-6 | Workspace `ladder/[slot-id]` muestra stats slot |
| AC-7 | "+ Nuevo servicio" crea treatment + redirect |
| AC-8 | Multi-select doctors funciona |
| AC-9 | Visual goldens × 10 (catalogo + escalera + 2 workspaces × 2 themes) |
| AC-10 | a11y axe pass · drag-drop keyboard alternative |
| AC-11 | Cross-tenant query bloqueada |
| AC-12 | RBAC: solo admin_clinic edita pricing · staff read-only |
| AC-13 | Catalog version arch fitness pass |
| AC-14 | Vitest + Playwright + a11y pass |

## Gherkin scenarios

### Scenario 1 — happy: drag treatment a slot core

**Given:** Treatment `Implante dental $1500` en panel "Sin escalera". 5 slots vacíos.

**When:**
1. User drag implante card → drop en slot CORE
2. Drawer abre con default pricing_override = base price

**Then:**
- Backend POST `/api/treatments/ladder-slot` { role: 'core', treatment_id: X, override: 1500 }
- Slot CORE muestra implante card
- Treatments sin escalera reduce N-1
- Audit log row

### Scenario 2 — negative: drop fail invalid role

**Given:** User intenta drop treatment con role que no existe

**When:** Custom drag-drop interception attempt

**Then:**
- Backend valida role contra catalog version
- Si role inválido → 422 + UI alerta + rollback drag

### Scenario 3 — edge: treatment ya en otro slot

**Given:** Treatment `Implante` ya en slot CORE

**When:** User drag desde CORE → drop PROFIT-MAX

**Then:**
- Drag intra-canvas — backend mueve slot (delete old + create new)
- Audit log: `ladder_slot_moved`
- Conversion stats recomputed background

### Scenario 4 — adversarial: pricing override negativo

**Given:** User intenta override $-50

**When:** Save submit

**Then:**
- Zod validation + backend validation reject
- UI muestra "Precio debe ser >= 0"

### Scenario 5 — keyboard-a11y drag canvas

**Given:** Foco en treatment card panel

**When:**
1. Space → entra modo select
2. Arrow → cycle slots
3. Space → confirma drop

**Then:**
- Screen reader anuncia transitions · aria-live region · visual focus ring

## Deliverables

| File | Acción |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/servicios/page.tsx` | MODIFY |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/servicios/[treatment-id]/page.tsx` | NEW (N3-dyn) |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/servicios/ladder/[slot-id]/page.tsx` | NEW (N3-dyn) |
| `vitalia/frontend/src/features/lisa/components/servicios/LisaServiciosView.tsx` | NEW |
| `vitalia/frontend/src/features/lisa/components/servicios/CatalogoView.tsx` | NEW |
| `vitalia/frontend/src/features/lisa/components/servicios/EscaleraCanvas.tsx` | NEW (★) |
| `vitalia/frontend/src/features/lisa/components/servicios/LadderSlot.tsx` | NEW |
| `vitalia/frontend/src/features/lisa/components/servicios/TreatmentCard.tsx` | NEW |
| `vitalia/frontend/src/features/lisa/components/servicios/NuevoServicioModal.tsx` | NEW |
| `vitalia/frontend/src/features/lisa/components/servicios/treatment-detail/TreatmentWorkspace.tsx` | NEW |
| `vitalia/frontend/src/features/lisa/components/servicios/treatment-detail/tabs/{Detalle,Doctores,PlanPago,Resenas,Stats}Tab.tsx` | NEW (5 files) |
| `vitalia/frontend/src/features/lisa/components/servicios/ladder-detail/LadderSlotWorkspace.tsx` | NEW |
| `vitalia/frontend/src/features/lisa/api/servicios.ts` | NEW |
| `vitalia/frontend/src/features/lisa/types/treatment.types.ts` | NEW |
| `vitalia/frontend/src/features/lisa/types/ladder-slot.types.ts` | NEW |
| `vitalia/frontend/src/features/lisa/types/servicios-schema.ts` | NEW (Zod) |
| `vitalia/backend/src/modules/vitalia/treatments/api/treatments_router.py` | MODIFY |
| `vitalia/backend/src/modules/vitalia/treatments/api/ladder_slots_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/treatments/application/ladder_slot_service.py` | NEW |
| `vitalia/backend/src/modules/vitalia/treatments/extensions.py` | MODIFY (register LadderSlotDef via EP-2) |
| `vitalia/backend/src/modules/vitalia/treatments/persistence/migrations/XXXX_ladder_slots.py` | NEW |
| `vitalia/frontend/e2e/shell-organism/lisa-servicios-toggle.spec.ts` | NEW |
| `vitalia/frontend/e2e/shell-organism/lisa-servicios-escalera-drag.spec.ts` | NEW |
| `vitalia/frontend/e2e/__screenshots__/servicios/{view}-{light\|dark}.png` (×4) | NEW |
| `vitalia/frontend/e2e/__screenshots__/servicios/treatment-detail-{tab}-{light\|dark}.png` (×10) | NEW |
| `vitalia/backend/tests/modules/vitalia/treatments/test_ladder_slot_service.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/treatments/test_ladder_slot_arch_fitness.py` | NEW |
| `vitalia/backend/tests/modules/vitalia/treatments/test_servicios_cross_tenant.py` | NEW |

## Reuse map

| Origen | Componente / pattern | Adaptación |
|---|---|---|
| Vitalia shipped — `vitalia/backend/src/modules/vitalia/treatments/` | Treatment model + repository | REUSE + extend |
| `core/luana-core-offer-studio` (engine) | Catalog DAG + LadderSlotDef ontology | CONSUME via Extension SDK EP-2 |
| `offer-expert` skill ontology | Lead-magnet / Tripwire / Core / Profit-max / Return-path roles | APPLY as canvas columns |
| Shadcn primitives | `Tabs` · `Dialog` · `Card` · `Drawer` · `Select` | npx install |
| `@dnd-kit/core` | DnD canvas | REUSE (also F2-S4 embudo) |
| Vitalia archived — brand_studio offer-studio FE | Patterns toggle view | TRANSPONER |

## Dependencies map

### Hard
- `vitalia-fase1-empty-states` + `vitalia-fase1-routing-shell`

### Soft
- `vitalia-fase2-lisa-doctores` — doctor-treatment assignment
- `vitalia-fase2-lisa-marca` — voice brand para descripciones default

### Esta historia desbloquea
- `vitalia-fase2-adrian-propuestas` — propuestas consumen catalog + LadderSlot
- `vitalia-fase2-valeria-agenda` — crear cita selecciona treatment
- `vitalia-fase2-camila-reactivar` — return-path slots para cohorte recall

## Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| LadderSlot ontology cambia frecuente | Media | Medio | Engine versioned + brand override slot copy local |
| Canvas drag UX confuso para clinic owners | Alta | Bajo | Tooltips + tutorial primer-uso · default presets vertical |
| Stats slot performance no real-time | Media | Bajo | Background worker recompute cada 1h |
| Engine catalog version mismatch | Baja | Alto | Arch fitness test estrato ambos stacks |

## Definición de "Done"

1. AC verificados
2. Visual goldens × 14 (catalog + escalera + workspaces tabs × 2 themes)
3. Backend tests ladder + catalog version + cross-tenant pass
4. Story pushed + handoff `/auditor`
5. Auditor APPROVED → merge → capability `lisa.servicios` registrada

## Próximo paso post-done

- F2-S6 adrian-propuestas consume catalog + LadderSlot para builder
- F2-S1 valeria-agenda form crear-cita selecciona treatment + duración auto-fill

## Referencias

- **Design Contract:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- **Navigation tree:** § lisa.servicios
- **offer-expert skill:** value ladder ontology
- **HIPAA-lite:** `vitalia/.claude/rules/hipaa-lite.md`
- **Engine catalog SSoT:** `core/luana-core-offer-studio/src/luana_core_offer_studio/domain/`
