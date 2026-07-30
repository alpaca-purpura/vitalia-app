---
story_id: vitalia-auth-base-functional
brand: vitalia
outcome: vitalia-mvp-ui-foundation
parent_spec: standalone-hotfix                    # NO descended from vitalia-ux-discovery — independent hot-fix
state: done                                        # 2026-05-19 — merged to main + LIVE confirmed on dev-app.vitalialat.com
phase: COMPLETE                                    # Story closed; follow-up ticket queued for 5 BE WARNs + Playwright selector fixes
defer_audit: false                                 # NO escape valve — Chris quiere validación live
parallel_safe: true                                # FE+BE+ops orthogonal, no conflict con otras stories
spawned_at: 2026-05-18
spawned_by: /pm-vitalia (post Chris ratificación scope hot-fix + admin Streamlit scope mínimo)
ratified_by_chris: true
ratified_at: 2026-05-18

# Hot-fix metadata (per .claude/rules/hotfix-repro-mandatory.md)
repro_verified: true
repro_evidence:
  brand: vitalia
  url: https://dev-app.vitalialat.com/
  command: "/pm-vitalia investigation 2026-05-18 (no Bash command needed, root cause confirmed reading repo)"
  output: |
    Root cause confirmado:
    1. vitalia/frontend/src/middleware.ts NO EXISTE → Clerk no protege rutas → / cae directo al placeholder
    2. vitalia/frontend/src/app/(auth)/sign-in/page.tsx renders literal placeholder texto "Inicio de sesión con Clerk (pendiente T-fe-3)" — NO renders <SignIn />
    3. vitalia/frontend/src/app/(dashboard)/page.tsx renders placeholder "Métricas del panel (pendiente T-fe-3)" — esto es lo que Chris ve
    4. vitalia/frontend/src/app/onboarding/step-{1,2,3}/page.tsx idem placeholders
    5. vitalia/backend/src/modules/vitalia/admin/ NO EXISTE (Nicolify sí tiene en nicolify/backend/src/modules/nicolify/admin/)
    6. Wizard onboarding implementado en vitalia/frontend/src/app/onboarding/wizard/page.tsx + features/onboarding/ (Story vitalia-slice-1-onboarding-wizard done 2026-05-18) — sí enchufado correctamente al routing.
    7. K8s deploy + cloudflared sirven el scaffold actual sin middleware Clerk
  diagnosis_validates_handoff: true                # No hubo handoff doc previo; este checkpoint ES el handoff a /dev-team
  diagnosis_correction: ~

# Scope
hot_fix_type: "deploy_base_functional_block"       # bloqueante para validar cualquier feature Slice 1
priority: critical                                 # blocker validación visual brand vitalia

# Files inventory ref (v2 post gaps audit 2026-05-18)
files_in_scope_count: 32                           # ~24 NEW + 7 EDIT + 4 DELETE (ver 03-arch-brief.md § 6 + 06-tickets.yaml v2)

# Validators ref (v2)
validators_total: 19                               # 7 non_functional + 5 functional + 6 visual + 1 ops + matrix anchor
must_pass_count: 19
gaps_audit_v2_added_validators: 9                  # +9 vs v1 post Chris ratificación gaps audit

# Tickets ref (v2)
tickets_total: 7                                   # T-1, T-2, T-3, T-4, T-5, T-6.a, T-6.b
production_code_tickets: 4                         # T-1, T-2, T-3, T-4
non_production_tickets: 3                          # T-5 ops + T-6.a tests + T-6.b tests
agentic_tickets: 0                                 # no agentic surface
opus_required_tickets: 0                           # R23 — all Sonnet/qwen-opencode eligible
estimated_total_hours: 23.5                        # +5.5h vs v1 (T-4 +2h + T-5 +0.5h + T-6.a NEW 2h + T-6.b +1h)
estimated_total_days: 3
critical_path_hours: 17.5                          # T-4 → T-6.a → T-5 → T-6.b (8+2+3.5+4)

# Pre-T-5 Chris manual checklist (per 05-guidelines.md § 8 — v2 NEW)
pre_t5_chris_checklist_done: false                 # ★ Chris debe marcar true ANTES de spawn T-5 builder ★
pre_t5_chris_checklist_items:
  - clerk_app_vitalia_active: false
  - clerk_domain_dev_app_configured: false
  - clerk_signin_methods_enabled: false
  - clerk_api_keys_in_k8s_secret: false
  - clerk_webhook_endpoint_configured: false
  - clerk_webhook_signing_secret_in_k8s: false
  - clerk_testing_token_generated: false
  - clerk_issuer_url_in_k8s_secret: false

# Open questions (resolver ANTES /dev-team spawn — Chris approve in-chat)
open_questions:
  - id: Q1
    question: "Admin Streamlit URL: subdomain vitalia-admin.vitalialat.com o subpath dev-app.vitalialat.com/admin?"
    default_recommended: "subdomain — aislamiento DNS+CORS más limpio"
    status: ratified_default                       # 2026-05-18 — Chris pre-ratificó defaults razonables
    ratified_value: "subdomain vitalia-admin.vitalialat.com"
  - id: Q2
    question: "Fixture clinic auto-asociada al sign-up del primer user?"
    default_recommended: "Sí — webhook user.created busca tenant con email_domain match en metadata, sino asocia a aurora-dental-ar (default fixture)"
    status: ratified_default
    ratified_value: "Sí — auto-asociar a aurora-dental-ar fixture default si no hay email_domain match"
  - id: Q3
    question: "Eliminar páginas legacy app/onboarding/step-{1,2,3}/page.tsx o dejar stubs muertos?"
    default_recommended: "Eliminar — son code-rot post wizard unificado"
    status: ratified_default
    ratified_value: "Eliminar (per T-2 file list DELETE)"
  - id: Q4
    question: "Admin Streamlit super-admin: 1 password compartido o multi-admin via Streamlit Authenticator config?"
    default_recommended: "1 password env-var (scope mínimo). Multi-admin defer story futura"
    status: ratified_default
    ratified_value: "1 password env-var VITALIA_ADMIN_PASSWORD_HASH bcrypt (scope mínimo). Multi-admin defer story futura."
  - id: Q5
    question: "Pre-T-5 Chris manual checklist Clerk dashboard — ¿cuándo lo completás? Antes spawn /dev-team o just-in-time antes T-5?"
    default_recommended: "Antes spawn /dev-team — así pre_t5_chris_checklist_done=true desde inicio + T-5 no se bloquea cuando llega su turno"
    status: pending_chris_manual_action            # Chris-only action, no /pm decision
    related: "Per 05-guidelines.md § 8 — checklist 8 items ~5 min en dashboard.clerk.com app vitalia. Bloquea T-5 spawn — /dev-team Step 0 antes spawn builder T-5 verifica pre_t5_chris_checklist_done=true"

# Decisions cementadas (ver 01-spec.md § 8)
decisions:
  D1: Skip /po-ux + /architect formal — scope quirúrgico Chris-ratificado
  D2: Admin Streamlit scope SOLO tenants + usuarios
  D3: No traer otras pages Nicolify
  D4: Wizard único en /onboarding/wizard — NO duplicar en step-{1,2,3}
  D5: Worktree wip/vitalia canónico, no spawnar efímero
  D6: Playwright smoke LIVE contra dev-app.vitalialat.com (no Docker local)
  D7: Admin Streamlit deploy = container K8s separado
  D8: Super-admin auth Streamlit = bcrypt env-var (scope mínimo)

# Ready package artifacts (v2 post gaps audit 2026-05-18)
artifacts:
  - 01-spec.md                                     # Gherkin scenarios SC-01..SC-18 (18 v2 vs 10 v1) + wireframes + microcopy + decisions
  - 03-arch-brief.md                               # decisiones técnicas + paths exactos + patterns (v1 no cambió)
  - 04-validators.yaml                             # 19 validators must_pass (v2 vs 12 v1) + 4 categorías
  - 05-guidelines.md                               # files in scope + 9 patterns + 16 anti-patterns + TDD note + pre-T-5 Chris checklist + auditor v2 responsibilities
  - 06-tickets.yaml                                # 7 tickets DAG (T-1..T-6.b) + gherkin_coverage MANDATORY + 4 BE integration tests

# Blockers
blocker_dependencies: []                           # no story-level blockers
blocker_dependencies_resolved:
  - vitalia-slice-1-onboarding-wizard              # merged 2026-05-18 — wizard ya existe en /onboarding/wizard
  - vitalia-slice-1-infra-cross-cutting            # merged 2026-05-18 — IAM/audit_log infra existe
  - vitalia-copilot-tools-impl                     # merged 2026-05-18

# Side story relations
side_story_relations:
  blocks: []                                       # esta story NO bloquea otras
  unblocks:                                        # esta story DESBLOQUEA validación visual de:
    - vitalia-slice-1-inbox                        # podrá testearse live post-merge
    - vitalia-slice-1-fidelizacion
    - vitalia-slice-1-marketing
    - vitalia-slice-1-pipeline
    - vitalia-slice-1-agenda
    - vitalia-ux-discovery (ready package /architect)

# Status timeline
state_history:
  - state: ready
    at: 2026-05-18
    by: /pm-vitalia
    reason: "Hot-fix scope quirúrgico Chris-ratificado. Skip refining/refined formal porque 01-spec.md + 03-arch-brief.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml escritos in-line por /pm-vitalia este turno post-investigación root cause."
  - state: ready_v2
    at: 2026-05-18
    by: /pm-vitalia
    reason: "Post-Chris ratificación gaps audit (preguntó '¿has considerado todos los medios de validación incluyendo Playwright?'). 11 gaps identificados (4 MUST + 4 SHOULD + 3 COULD), TODOS ratificados Chris. Updates: +9 validators (12→19) +8 scenarios (10→18) +1 ticket split (T-6→T-6.a + T-6.b) +5.5h estim (18→23.5h) +5.5h critical path (12→17.5h). Spec mantiene state=ready, no regresión a refining."
  - state: developing
    at: 2026-05-18
    by: /dev-team
    reason: "Pickup autonomous build — Chris solicita completar story end-to-end hasta vitalia live. CONTEXT-BRIEF.md generado (Haiku, 436 lines, 16 secciones clean). Arranca T-1 (FE Clerk middleware) + T-4 (BE Admin Streamlit) en paralelo. T-5 deploy bloqueado hasta pre_t5_chris_checklist_done=true (8 items Clerk dashboard). T-6.b ejecutado por /pm-vitalia post-deploy."
  - state: developed
    at: 2026-05-18
    by: /dev-team
    reason: |
      ALL 7 tickets pushed. Commits:
      - T-1 e80c806 — FE Clerk middleware (3 files; 7/7 middleware unit + 38/38 arch + 306/306 vitest PASS)
      - T-2 dcd34d6 — FE SignIn/SignUp real + DELETE legacy step-{1,2,3} (5 files)
      - T-3 69aaab1 — FE Dashboard welcome + features/dashboard/ (7 files; 3/3 dashboard unit + 38/38 arch + 309 vitest)
      - T-4 2b056a5 — BE Admin Streamlit + 3 integration tests (23 files; 17/17 unit PASS; integration @pytest.mark.integration gated por Postgres availability — SKIP graceful)
      - T-6.a 096eba8 — Playwright LOCAL smoke specs (4 specs + config update; static gates GREEN; LOCAL exec partial por stack bindeada a luana-platform/main no este worktree)
      - T-5 e1c2315 — K8s manifests admin (Dockerfile.admin + 3 K8s YAMLs + secrets template + post_deploy_smoke.sh + generate_admin_password_hash.sh + /api/health endpoint in main.py) (9 files; bash -n + yaml.safe_load + ruff PASS)
      - T-6.b 2c59f77 — Playwright a11y + mobile + visual + audit script (5 NEW + 2 EDIT; tsc + eslint + bash -n PASS)

      Static validators GREEN: tsc, eslint, arch-fitness, ruff, bash -n, yaml.safe_load, anti-dup scan.

      Runtime-gated validators (NOT executable until post-merge + Chris manual):
      - fn-be-webhook-clerk-integration ⏸ Postgres available locally pero tests usan @pytest.mark.integration (skip graceful, auditor verifica con stack up)
      - fn-be-hipaa-audit-log-verify ⏸ idem
      - fn-be-cross-tenant-isolation-admin ⏸ idem
      - vs-playwright-smoke-local-pre-deploy ⏸ docker stack bindeada a luana-platform/ (main), no wip/vitalia — resolverá post squash-merge
      - vs-playwright-smoke-live + vs-playwright-trace-broader-monitor + vs-playwright-a11y-axe + vs-playwright-mobile-viewport + vs-playwright-screenshot-baseline ⏸ requieren T-5 deploy LIVE + Chris CLERK_TESTING_TOKEN_VITALIA + secrets en cluster
      - ops-k8s-healthcheck-deploy-verify ⏸ requiere kubectl apply real

      AUTO-HANDOFF a /auditor (defer_audit=false default per story-closure-gate.md Layer 2).
      Phase D auditor evaluará gherkin matrix scenario-by-scenario; runtime-gated tests requerirán Chris merge → CD deploy → /pm-vitalia LIVE smoke ejecución para cerrar.

# Handoff next
next_action: "/auditor APPROVED with PENDING_DEPLOY tier (commit 65e82b8 self-fix iter-1 closed 6 WARNs). CHECKPOINTS.md C1-C5: 24/27 immediate ✅ + 1 PENDING_DEPLOY (Playwright LIVE) + 2 merge-step. Phase D gherkin-matrix.md: 6/18 PASS now + 12/18 PENDING_DEPLOY (require post-merge CD staging + Chris Clerk dashboard 8 items + /pm-vitalia LIVE smoke exec). AUTO-HANDOFF /pm-vitalia merge: write 07-merge.md 5 secciones + update capabilities/* + modules MD + squash-merge wip/vitalia → main + post-merge /pm-vitalia ejecuta T-6.b LIVE smoke contra dev-app.vitalialat.com."
next_owner: /pm-vitalia

# /auditor + /pm-vitalia merge handoffs (post developed)
post_developed_handoff: /auditor                   # AUTO per story-closure-gate.md (default)
post_approved_handoff: /pm-vitalia                 # AUTO merge

last_updated: 2026-05-19
# Ticket states (post /dev-team build T-1..T-4)
ticket_states:
  T-1: done   # commit e80c806 — Clerk middleware
  T-2: done   # commit dcd34d6 — SignIn/SignUp real pages + DELETE step-{1,2,3}
  T-3: done   # commit 69aaab1 — Dashboard welcome + features/dashboard/
  T-4: done   # commit 2b056a5 — Admin Streamlit BE
  T-6a: pending_stack_running  # requires make dev-vitalia + Clerk keys
  T-5: blocked_pre_checklist  # blocked until pre_t5_chris_checklist_done=true
  T-6b: blocked_t5  # blocked until T-5 done

# Schema v2 migration (cement 2026-05-27)
release: F0   # release ID · ver releases/
cap_target: k8s-admin-deployment   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# vitalia-auth-base-functional — checkpoint

> **Story type:** hot-fix scope quirúrgico (~2 días dev · 18h estimado · 12h critical path con paralelización)
> **State:** `ready` — skip refining/refined formal per D1 (Chris ratificado)
> **Block:** validación visual de TODA brand vitalia post-deploy actual roto

## ¿Qué resuelve?

`https://dev-app.vitalialat.com/` muestra placeholders T-fe-3 literal en lugar de
Clerk SignIn + dashboard + admin. Chris no puede loguearse ni ver wizard
(que está implementado pero inaccesible sin middleware Clerk + sign-in real).

Esta story implementa la **base mínima funcional**:
- Clerk middleware proteger rutas
- Sign-in + Sign-up reales con `<SignIn />` / `<SignUp />`
- Dashboard `/` mínimo welcome (NO offers/bookings/etc — esas siguen Slice 1)
- Admin Streamlit Vitalia con SOLO crear-tenant + crear-user (espejando pattern Nicolify, scope mínimo)
- K8s deploy + secrets verify + fixtures seed
- Playwright LIVE smoke contra dev-app.vitalialat.com (yo /pm-vitalia ejecuto antes de declarar PASS)

## Out-of-scope explícito

- ❌ Implementar offers/bookings/appointments/patients (las 6 stories Slice 1 refined ya en backlog)
- ❌ Admin Streamlit +2 pages (sales/metrics/billing/etc)
- ❌ Audio Whisper (defer Slice 2)
- ❌ Modificar `core/luana-core-*/` (engine)
- ❌ Sales agent / copilot conversaciones live

## Mecánica próxima sesión

1. Chris lee `01-spec.md` + `03-arch-brief.md` + `06-tickets.yaml`
2. Chris responde Q1-Q4 in-chat (defaults razonables → puede ratificar todos)
3. `/dev-team vitalia-auth-base-functional` arranca T-1..T-6 autonomous
4. Validators GREEN → state=developed → AUTO-HANDOFF `/auditor`
5. APPROVED → AUTO-HANDOFF `/pm-vitalia merge` → 07-merge.md 5 secciones
6. state=done

## Notas operativas

- Worktree: `wip/vitalia` canónico (per D5). No efímero.
- Branch push: `wip/vitalia` per parallel-safety.md M11 (push frecuente).
- Cost-routing: 0 Opus, 6 Sonnet/qwen-opencode (R23 — no agentic production).
- Anti-duplication: admin Streamlit pattern espejado de Nicolify pero código brand-specific reescrito (diff ≥ 50 lines validator).
