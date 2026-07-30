---
story_id: vitalia-fase2-adrian-embudo
type: ui-story
agent_owner: adrian
map_zone: agentes
map_box: adrian
module: crm                          # ★ corregido 2026-06-03 (era sales_pipeline — duplicaba crm shipped; Chris ratificó EXTEND crm)
capability: crm/adrian-embudo
state: done                            # ★ 2026-06-11 MERGED (Fase F) — demo-fix loop cerrado (3 bugs root-fixed + re-verificado live 13/13) + chris_verify SATISFIED
defer_audit: false
defer_audit_reason: "[HISTÓRICO] 2026-06-10..06-11 deferido tras vitalia-shell-core-hardening (merge 3cb9d5a0, done 2026-06-11) + blocker inbox-gate. AMBOS RESUELTOS: shell-hardening mergeado · inbox merged a5682bda + archived → FE arch-fitness 187/187 verde. Defer levantado 2026-06-11."
reconciled: true
phase: MERGED                         # ★ 2026-06-11T21:00 — demo-fix resuelto (59894c99 + 13/13 live) → Chris re-demo SATISFIED → merge F
audit:
  verdict: APPROVED                    # técnico — CHECKPOINTS.md (C1 4/4 · C2 4/5 demo pendiente · C3 6/6 · C4 6/6)
  by: /auditor (Auditor Responsable v5)
  date: 2026-06-11
  artifacts: [CHECKPOINTS.md, 06-audit/gherkin-matrix.md, T-SYNC-review.md]
  carril_r: "sync-fix gaps cerrados: stale retract test fixed + regression test cross-invalidation NEW + live-verify board-live 9/9 dev-app"
  out_of_scope_findings:               # pre-existentes, NO regresiones del embudo (FE-only)
    - "HB-69 (MED): tests crm slice-1 rotos (asyncio.get_event_loop / MagicMock no-awaitable) — saneo slice-1"
    - "HB-70 (HIGH): treatment_plans.notes TEXT→BYTEA — PHI fidelizacion, stake-asimétrico, story dedicada"
  remaining_gate: "chris_verify.signoff (demo Chris contra dev-app) — /pm-vitalia REFUSE merge sin él"
chris_verify:
  required: true
  signoff:
    signed_by: Chris
    date: 2026-06-11
    result: SATISFIED
    notes: "Verificado live en localhost:3002 — re-demo post demo-fix loop: spinner crear-lead ✓ · canal aparece en detalle ✓ · /recuperar empty-state ✓ ('probé los 3 puntos, satisfecho, dale merge')"
    open_items: []
  rounds:
    - date: 2026-06-11
      found: "Demo Chris encontró 3 UX bugs: (1) crear lead sin loading state, (2) canal no persistía (root: LeadRepository.create sin kwargs funnel — TypeError 500), (3) /recuperar vacío"
      resolved: "(1) Loader2+disabled · (2) root-fix repo + passthrough service/funnel_service/router + regresión test_lead_repo_funnel_fields.py (59894c99) · (3) no-bug, empty-state correcto. Re-verificado: e2e 13/13 live + fila DB channel=whatsapp. Colateral: stack caído (store pnpm imagen FE + KEK compose) reparado (8ce72b0e)"

build_status:                          # ★ 2026-06-03 — 6/8 tickets DONE (resumido tras coordinación Chris)
  completed:                           # implementación COMPLETA, gates GREEN, committeado + pushed
    - {id: T-BE-1, commit: "811f01b6 (entangled inbox T-5)", gates: "60/60 unit + ruff"}
    - {id: T-FE-1, commit: 6dd578f4, gates: "vitest 30/30 + tsc + eslint"}
    - {id: T-BE-2, commit: 4fc84177, gates: "25/25 + ruff + 345 arch"}
    - {id: T-AG-1, commit: be7d9a08, gates: "10/10 wire + 33 sales_agent + ruff (Opus R23)"}
    - {id: T-FE-2, commit: a983f44d, gates: "vitest 53/53 + tsc + eslint (orch 1 fix mecánico)"}
    - {id: T-FE-3, commit: 3193463b, gates: "vitest 337/337 + tsc + eslint (orch 2 fixes mecánicos)"}
  pending: [T-E2E-1-deferred]           # T-DEMO-1/T-DEMO-2 DONE (writes live 2026-06-04). T-E2E-1 PARTIAL/DEFERRED: mocked-smoke (22 reds = fixture-overlay infra, NO producto) + visual goldens → follow-up (Chris ratificó proceed-on-live-verify 2026-06-04). SSoT: T-E2E-1-result.md. Pendiente humano: demo_signoff Chris
  live_smoke: "Migración 038 aplicada a dev DB (037→038 head). 6 endpoints funnel montados+reachable (/board→422 sin header, path /api/v1/crm confirmado — Open Q#1 architect). 3 tablas en DB (vitalia_leads ext + lead_stage_transition + lead_activity)."
  notes: "Build corrió EN SERIE compartiendo hub con sesión inbox concurrente (Chris ratificó). Commits por pathspec + STORY_CLOSURE_GATE_SKIP cross-módulo (embudo=crm vs inbox=inbox, ADR-009). T-BE-1 quedó entangled en commit inbox 811f01b6 (git add -A ajeno) — aceptado por Chris, código presente."
contract_repair:                       # ★ 2026-06-04 — live-verify (gate #37) destapó bug SISTÉMICO + reparado
  commit: 41e2eecb
  bug: "FE construido contra contrato IMAGINADO snake↔camel; board crasheaba LIVE (buyingSignals.slice undefined → burbuja Next). '6/8 GREEN' era 100% mockeado (component tests camelCase + BE tests snake nunca se encontraron)."
  fix: "FE keysToCamel en el borde (7 hooks, lib/api/keys-to-camel.ts) + BE board_dto/funnel_service exponen los 10 campos que el FE LeadCardDTO declara (incl. version p/ mutación optimista), sourced del dominio Lead. Cero gaps genuinos, sin migración."
  gates: "FE tsc+eslint clean + embudo vitest pass · BE 26/26 + 320 arch GREEN"
dod_live_verified: true                # ★ gate #37 — board RENDER + WRITES verified LIVE 2026-06-04 (T-DEMO2)
dod_live_verify:
  board_render: "✅ LIVE dev-app (Playwright board-live.spec.ts, project authenticated): board renderiza SIN burbuja Next + lead cards data real (cero undefined) + KPIs OK + GET /api/v1/crm/board 200. Bug sistémico MUERTO. Evidencia: T-DEMO1-live-verify-result.md"
  create_lead_post: "✅ LIVE 2026-06-04T04:26:38 — POST /api/v1/crm/leads → 201 Created (lead_id=0d2313ff-72fa-45be-9e8e-e14eb0c3633e). vitalia_leads count: 2→3. Fix: data-testid=lead-channel-select en SelectTrigger. Evidencia: T-DEMO2-writes-result.md"
  stage_transition_patch: "✅ LIVE 2026-06-04T04:26:21 — PATCH /api/v1/crm/leads/66afe78e-.../stage → 200 OK (interesado→calificando, version 1→2). vitalia_lead_stage_transition: 1 row (manual_override). Fix: move-stage button (data-testid=move-stage-{leadId}). Evidencia: T-DEMO2-writes-result.md"
  lead_detail_resumen: "✅ LIVE 2026-06-04T06:31 — Chris pegó crash en /{tenant}/adrian/embudo/{leadId}/resumen (ResumenView.tsx:184 autonomy.canDo undefined). Causa: FE imaginó canDo/needsApproval, BE emite can/needs_ok (AutonomyInfo — 2da instancia del contrato-imaginado HB-42 → HB-44). Fix: FE realineado a can/needsOk + guard ?? [] + AutonomyInfo agregado al contract-parity gate + use-lead-detail fixture corregido + resumen-live.spec.ts (live-verify). Verificado dev-app real: GET /api/v1/crm/leads/0d2313ff.../detail 200 + ResumenView render SIN burbuja Next + base.ts teardown verde (0 pageerror/console/4xx)."
  writes_pending: []
  next: "★ 2026-06-11 RECONCILE: blocker inbox RESUELTO (inbox merged a5682bda + archived; FE arch-fitness 187/187 verde) · blocker shell-hardening RESUELTO (merge 3cb9d5a0). Defer LEVANTADO. Pendiente cierre: EMBUDO-INBOX-SYNC-FIX (1 test stale RED + regression test + live-verify) → /auditor Carril R → demo Chris → merge."
dod_evidence:
  - action: "POST /api/v1/crm/leads — crear lead dental LatAm (dr.demo@vitalialat.com, tenant Sanaré)"
    observed: "lead_id=0d2313ff-72fa-45be-9e8e-e14eb0c3633e creado. Redirect a /embudo?highlight=0d2313ff... . vitalia_leads count 2→3."
    backend_log: "POST /api/v1/crm/leads HTTP/1.1 201 Created · lead_created lead_id=0d2313ff · sin Traceback"
  - action: "PATCH /api/v1/crm/leads/66afe78e-.../stage — mover etapa interesado→calificando (move-stage button, version=1)"
    observed: "lead version=1→2, stage=calificando. vitalia_lead_stage_transition: 1 fila (manual_override). Board renderizó sin crash post-reload."
    backend_log: "PATCH /api/v1/crm/leads/66afe78e.../stage HTTP/1.1 200 OK · funnel_transition_complete from_stage=interesado to_stage=calificando · sin Traceback"
  - action: "GET lead-detail Resumen — navegar /{tenant}/adrian/embudo/0d2313ff.../resumen (Playwright authed dr.demo, backend REAL, sin MSW) — repro exacto del crash que pegó Chris"
    observed: "ResumenView renderiza, bloque 'Estado del agente' visible, SIN burbuja Next; base.ts teardown verde (0 pageerror / console.error / /api 4xx-5xx). resumen-live.spec 3/3 (setup+test)."
    backend_log: "GET /api/v1/crm/leads/0d2313ff-72fa-45be-9e8e-e14eb0c3633e/detail HTTP/1.1 200 OK · lead_score_computed score=10 stage=interesado · sin Traceback"
  - action: "B1 — click chip 'congelados' (board → /adrian/recuperar) ×15 ciclos (recuperar-live.spec R-1, Playwright authed dr.demo, backend REAL)"
    observed: "5/5 PASS. Recuperar monta (recuperar-view/empty) SIN quedar en 'Cargando shell'; base.ts teardown verde (0 pageerror/console/4xx, sin Next overlay). El hard-nav elimina el hang del shell ssr:false en soft-nav."
    backend_log: "GET /api/v1/crm/board + frozen list 200 · sin Traceback"
  - action: "B2/U1/U2 — abrir Resumen del lead (resumen-live.spec E, Playwright authed, backend REAL)"
    observed: "score grande == Σ(deltas del breakdown) (B2, ya no miente 0-vs-10) · 0 elementos data-phi[type=name] → nombre completo (U1) · filas Teléfono + Correo presentes (U2). base.ts teardown verde."
    backend_log: "GET /api/v1/crm/leads/{id}/detail 200 · lead_score_computed · sin Traceback"
verified_at: 2026-06-04T14:40:00Z
open_findings:                         # ★ 2026-06-04 sesión 5 — B1/B2/U1/U2 RESUELTOS + live-verified (commits 78a7ba52 BE + b1d32f83 FE)
  bugs:                                # defectos reales, embudo lane (code:crm)
    - {id: B1, sev: P0, surface: recuperar, status: RESOLVED, fix_commit: b1d32f83, detail: "RESUELTO (band-aid lane-safe): el chip frozen-kpi-badge (único entry point a /adrian/recuperar) pasa a hard-nav (<a>) → reload completo → el shell ssr:false monta limpio. Live: recuperar-live.spec R-1 ×3 (15 ciclos) 5/5 PASS. ★ ROOT CAUSE = shell dynamic({ssr:false}) cuelga en soft-nav (NO era orden de hooks del componente recuperar como asumía el handoff — RecuperarView/FrozenLeadRow tienen hooks limpios). El flake del shell en OTROS soft-navs (goBack/otros tabs) sigue latente → ESCALADO shell/inbox lane (junto a U3)."}
    - {id: B2, sev: P1, surface: resumen, status: RESOLVED, fix_commit: 78a7ba52, detail: "RESUELTO: get_lead_detail ahora devuelve el score COMPUTADO en el response (override sobre _lead_to_response). Fix read-side en mi lane crm (el write-side/create vive en lead_service lane inbox). TDD: test_funnel_service 12/12. Live: resumen-live.spec E (score == Σfactores) PASS."}
  ux_product_decision:                 # U1/U2 RESUELTOS; U3 → story shell aparte
    - {id: U1, surface: board+resumen+recuperar, status: RESOLVED, decision: "nombre completo (Chris 2026-06-04)", fix_commit: b1d32f83, detail: "RESUELTO: PiiMaskedSpan removido del nombre en LeadCard + ResumenView + FrozenLeadRow (3 surfaces) → nombre completo. non_phi marketing lead; masking PHI aplica al convertir lead→paciente. Live: resumen-live.spec E (0 elementos data-phi[name]) PASS."}
    - {id: U2, surface: resumen, status: RESOLVED, fix_commit: b1d32f83, detail: "RESUELTO: ResumenView muestra Nombre + Teléfono + Correo (plain, non_phi). Contract-safe: nuevo FE LeadDetailLeadDTO mirror de BE LeadResponse (no se widenó LeadCardDTO/board) + ContractPair registrado (contract-parity 5/5). BE assigned_doctor_id agregado a LeadResponse. Live: resumen-live.spec E (filas Teléfono+Correo) PASS."}
    - {id: U3, surface: shell, status: OPEN_SEPARATE_STORY, detail: "Splitter chat 55% fijo castiga el board. Shell-level cross-cutting → story aparte (junto al root-cause shell ssr:false de B1)."}
  polish_separate_story: [P1-KPIs-cripticos, P2-empty-states, P3-chips-truncados, P4-nuevo-lead-perdido, P5-tab-jerarquia]
  forensic:                            # pedido Chris — al final, antes de cerrar todo
    detail: "dod_live_verified=true previo fue FALSO para sub-vistas (solo board+writes ejercidos). Raíz: live-verify NO per-surface + auditor confió en self-report + contract-parity manual. Entregable: learning tooling/ + fix gate per-surface live-verify. Ancla HB-44."
architecture_pattern: ADR-vitalia-004
adr_004_compliance: full               # ★ 03-arch.md § Architecture Decisions
autonomous_mode: true                  # ★ Chris ratificó (architect→dev-team→auditor→[demo_signoff]→merge)
ready_package:                         # ★ 6 artifacts /architect
  - 03-arch.md
  - 03-arch-be.md
  - 03-arch-fe.md
  - 04-validators.yaml
  - 05-guidelines.md
  - 06-tickets.yaml
  - dispatch-plan.md
last_modified: '2026-06-04T04:26:38.000Z'
ratified_by_chris: true                # ★ "go al spec" (Chris 2026-06-03)
parallel_safe: true
priority: critical
estimated_dev_days: 8-11               # 1 story; si se parte S4a/S4b baja (§ Decisiones abiertas #3)
dependencies:
  hard:
    - vitalia-fase1-empty-states
    - vitalia-fase1-routing-shell
    - vitalia-payment-adapter-mvp       # solo para el side-effect real → en esta story = STUB MSW
  soft:
    - vitalia-fase2-adrian-inbox
    - vitalia-fase2-valeria-agenda
blocks_hard: []
blocks_soft:
  - vitalia-fase2-adrian-propuestas
  - vitalia-fase2-camila-reactivar
reuse_map_summary: >-
  EXTEND crm (Lead/lead_service/lead_dto/lead_repository + FE crm-shared/use-leads
  ya shipped) · CONSUME sustrato agéntico engine (closer-studio + AgentStateCheckpoint
  + transitions + diagnose + KPIs) vía Extension SDK · reuse EntitySubNavBar (de
  doctores) · @dnd-kit/core ya instalado · NEW funnel clínico 6 etapas + SLA dental
spawned_at: 2026-05-22T00:00:00.000Z
supersedes:
  - vitalia-slice-1-pipeline
next_action: "★ 2026-06-11 RECONCILE (proceso v5 R · /pm-vitalia): ambos blockers RESUELTOS (shell-hardening merge 3cb9d5a0 · inbox merged a5682bda+archived → FE arch 187/187 verde) + defer LEVANTADO. Sesión actual aplicó EMBUDO-INBOX-SYNC-FIX (7 archivos FE, uncommitted): cross-namespace RQ invalidation embudo↔inbox + alineación de keys a ['crm','conversation',id] + staleTime 5s. Estado verify del tree: tsc✅ eslint✅ arch-fitness✅ 187/187 · vitest 1 RED (use-retract-message: fixture stale seed legacy key — el hook quedó CORRECTO, alineado a la key renderizada). Orden restante: (1) /auditor Carril R → fix test stale + regression test cross-invalidation (use-lead-stage-mutation.test.ts) + live-verify embudo↔inbox sync dev-app + gate-runner verde + CHECKPOINTS; (2) demo Chris (demo-script.md) → chris_verify.signoff; (3) /pm-vitalia merge → cap crm/adrian-embudo planned→live (scenarios SC-1..11 + e2e_test) + 07-merge + git mv archive + portfolio; (4) FORENSE HB-44 (gate per-surface live-verify). Escalado a story shell aparte: B1 root-cause shell ssr:false + U3 splitter + P1-P5 pulido. SSoT: checkpoint § Reconcile 2026-06-11 + EMBUDO-INBOX-SYNC-FIX.md."
spec_artifact: 01-spec.md             # ★ SSoT funcional (v3). El detalle vive AQUÍ, no en este checkpoint.
po_ux_version: 3
detail_pattern: page_entitysubnavbar  # opción C ratificada UX (Chris 2026-06-03)
lead_detail_scope: core_2_tabs        # ★ v3: Resumen[Datos+Score] · Historial — vistas EN la barra (EntitySubNavBar, como Staff), NO Shadcn Tabs en body
new_lead_surface: route_workspace     # ★ v3: /adrian/embudo/nuevo (hoja con URL, no modal)
frozen_surface: subsubtab_recuperar   # ★ v3: V4 = sub-sub-tab /adrian/embudo/recuperar (no sección del board); Adrián corto plazo, Camila largo plazo
pipeline_model: conversation_first    # propuesta (confirmar)
ratified_visual_by_chris: true        # ★ Chris vio + aprobó mockup embudo-v3.html + § Design specification D.0-D.16 (ADR-003)
ratified_visual_at: 2026-06-03
design_spec_complete: true            # § Design specification D.0-D.16 (contrato visual fiel al mockup)
phi_classification: non_phi           # Lead = marketing prospect (crm/domain/lead.py); hipaa-lite full-set NO aplica
release: F4                          # ★ corregido al merge 2026-06-11 (F4.yaml lista la story; F3 era stale)
cap_target: crm/adrian-embudo
cap_change_type: fix
parent_story: null
---

# F2-S4 vitalia-fase2-adrian-embudo — checkpoint

> **★ Cuerpo adelgazado 2026-06-03.** El `Scope verbatim` viejo (§1-§9, 6 etapas `considerando/listo`, lead-detail 6 tabs, "Nuevo lead modal", paths `sales_pipeline/...`) fue **superado por `01-spec.md` v3** y removido por estar stale + contradictorio. Este checkpoint = tablero de control liviano (lo lee el cockpit). **El detalle funcional vive en `01-spec.md`** (vistas · reglas RN-1..18 · gherkin · dataset · componentes).

## Reconcile 2026-06-11 (proceso v5 · R · /pm-vitalia)

Chris pidió cerrar la story. `/pm-vitalia` reconcilió docs↔realidad antes del `/auditor`:

**Blockers RESUELTOS** (eran las dos razones del `defer_audit`):
- **shell-core-hardening** → mergeado + archivado (`3cb9d5a0`, done 2026-06-11). El rebase del chrome ya ocurrió.
- **inbox gate FE compartido** → `vitalia-fase2-adrian-inbox` merged (`a5682bda`) + archived; la reconciliación fsd/allowlists inbox→adrian aterrizó → **FE arch-fitness 187/187 verde** (verificado esta sesión).

**Drift de docs corregido:** el código FE del embudo vive en `features/adrian/components/embudo/` (post-rename inbox→adrian), NO en `features/crm/components/embudo/` como decían cap + spec. Cap `dev_preview` corregido.

**Cambio de programación ratificado (in-scope, `cap_change_type: fix`)** → `EMBUDO-INBOX-SYNC-FIX.md`:
- Bug: al mover etapa en Embudo, la etapa del lead en el thread de Inbox quedaba stale (~10s). Causa: dos namespaces RQ sin cross-invalidación.
- Fix: `useLeadStageMutation.onSuccess` invalida `['crm','conversation']` + `['adrian','inbox']`; `use-retract/send/set-mode/pause` alineadas a la key **renderizada** `['crm','conversation',id]` (consistente con `crm-shared/useConversationDetail`); keys centralizadas en `_keys.ts`; `staleTime` 10s→5s.
- Está en `chris_verify.rounds` (allowlist de scope ratificado).

**Estado del tree con el sync-fix (verificado 2026-06-11):** `tsc --noEmit` ✅ · `eslint` (adrian + crm-shared) ✅ · FE arch-fitness ✅ 187/187 · **`vitest` 1 RED** → `use-retract-message.test.ts`: el fixture siembra la key LEGACY `['adrian','inbox','conversation',id]` mientras el hook (correctamente) optimistic-updatea la key renderizada `['crm','conversation',id]` → el test lee null. **El hook quedó CORRECTO** (alineado con send/set-mode + crm-shared); el **test está stale**. Fix = Carril R (actualizar el fixture a la key renderizada). Falta además: regression test del cross-invalidation en `use-lead-stage-mutation.test.ts` + live-verify embudo↔inbox sync contra dev-app.

**Handoff:** `/auditor vitalia vitalia-fase2-adrian-embudo` (Auditor Responsable v5, Carril R) cierra esos 3 gaps (todos determinísticos / gate-captured, ninguno stake-asimétrico) + ejerce ≥1 write live + produce CHECKPOINTS. Luego: demo Chris → `chris_verify.signoff` → `/pm-vitalia merge`.

## Goal

Sub-tab **Embudo** de Adrián = **superficie de supervisión** sobre Adrián (empleado-IA que vende). Adrián conversa/califica/puntúa/mueve leads por un funnel clínico dental (Interesado → Calificando → Consulta agendada → Plan presentado → **Reservado=depósito** → Decidió no); la coordinadora supervisa (tomar control · instrucción oculta · override de etapa · recuperación); Valeria coordina. Embudo con SubSubTabsBar **Tablero** (Kanban|Lista, solo HOT) · **Recuperar** (congelados + diagnose, corto plazo Adrián; largo plazo = Camila). Detalle del lead = **página con URL propia** (vistas Resumen·Historial EN la barra EntitySubNavBar, como Staff — sin tabs en el body). Alta de lead = **ruta-hoja** `/nuevo` → redirect+highlight. Card = **proyección read-only** de estado+log (señales/micro-log/badges, no texto libre). Módulo `crm` (EXTEND), Lead **non-PHI**.

## Anti-objetivos (anti-creep)

- NO recrear el engine agéntico — CONSUMIR `core/luana-core-sales-agent/closer_studio` vía Extension SDK.
- NO editor de customización de etapas per-vertical (defaults dental sirven MVP — story dedicada futura).
- NO side-effect real de pago/agenda en `→Reservado` (STUB MSW; `payment-adapter-mvp` solo `refined`).
- NO AI-suggest next-stage automático · NO bulk-action · NO lead-merge.
- NO intercepting-route overlay del detalle (esta story = página C directa).

## SSoT funcional → `01-spec.md` v3

| Necesitás… | Sección del spec |
|---|---|
| Qué muestra cada vista (board · lista · página lead 2 tabs · congelados · nuevo lead) | § Vistas (V1-V5) |
| Reglas de negocio (SLA, override manual, auto-freeze, orden de columnas, board scope) | § Reglas RN-1..18 |
| Data realista para el mockup | § Dataset canónico |
| Scenarios Gherkin + matriz de cobertura | § Gherkin + § Matriz |
| Componentes + átomos + paths FSD | § Componentes |
| Endpoints + RQ keys + forms | § Data flow |
| Lo que falta cerrar | § Decisiones abiertas (#1-7) |

## Gates pendientes pre-`refined`

1. **Cerrar § Decisiones abiertas** (#1-7): consumir sustrato engine · conversation-first · alcance 1-story vs S4a/S4b · dataset · board-scope RN-18 · nuevo-lead ruta vs subsubtab · números SLA RN-11/13.
2. **Gate ADR-vitalia-003** — mockup-per-component (KanbanBoard+LeadCard+drag · SubSubTabsBar `Tablero·Recuperar` · LeadsTable · LeadWorkspace cabecera EntitySubNavBar + Resumen/Historial · NewLeadPage `/nuevo` · RecuperarView · Header/Filters/Metrics) dentro del wrapper-shell portado verbatim → `ratified_visual_by_chris: true`. **Bloqueante.**
3. **ADR-vitalia-004** ya citado en `01-spec.md` frontmatter ✓.

## Dependencies (resumen — detalle en spec § Prior art / Data flow)

- **Hard:** `vitalia-fase1-empty-states` (shell sub-tab nav) · `vitalia-fase1-routing-shell` (App Router incluye `adrian/embudo` + `[leadId]` + `/nuevo`) · `vitalia-payment-adapter-mvp` (solo para el side-effect real — STUB aquí).
- **Soft:** `vitalia-fase2-adrian-inbox` (leads de conversación) · `vitalia-fase2-valeria-agenda` (slot al `→Consulta agendada`/`→Reservado`).
- **Desbloquea:** `vitalia-fase2-adrian-propuestas` · `vitalia-fase2-camila-reactivar`.

## Riesgos

| Riesgo | Prob | Impacto | Mitigación |
|---|---|---|---|
| @dnd-kit/core × React 19 | Baja | Alto | ya instalado + verificar smoke |
| Stage transition race (2 operadores) | Media | Medio | optimistic lock `version` → 409 (SC-5, RN-4) |
| Side-effect cascade `→Reservado` falla parcial | Media | Alto | STUB MSW en esta story; saga real en payment-adapter |
| Drag-drop mobile pobre | Alta | Medio | long-press + KeyboardSensor + tests `@mobile` |
| SLA dental no fit todos los clinics | Alta | Bajo | story dedicada per-vertical futura — dental sirve MVP |

## Referencias

- **Spec (SSoT):** `01-spec.md`
- **Research:** `research/{00-propuesta-embudo-agentico, 01-legacy-pipeline, 02-core-engine, 03-agentic-best-practices, 04-detail-entry-pattern, 05-lead-detail-benchmark, 06-pipeline-sla-benchmark}.md`
- **Mockups:** `mockups/` (A panel · B drawer · C página ratificada · D híbrido) — regenerar C con dataset canónico tras "go al spec"
- **Bitácora:** `chris-input.md`
- **ADRs:** ADR-vitalia-003 (mockup-per-component) · ADR-vitalia-004 (shell-feature)
- **HIPAA-lite:** `vitalia/.claude/rules/hipaa-lite.md` (Lead non-PHI → solo tenant-isolation + audit)
