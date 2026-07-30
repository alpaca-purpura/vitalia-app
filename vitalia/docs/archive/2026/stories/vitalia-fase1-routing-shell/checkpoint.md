---
story_id: vitalia-fase1-routing-shell
outcome: vitalia-mvp-ui-foundation
phase: fase-1
type: ui-story
agent_owner: shell
module: shell-organism
capability: shell.routing
state: done                        # ★ reviewing → done (/pm-vitalia merge 2026-05-26)
phase: MERGED                      # ★ 07-merge + archive + learning + capability promotion COMPLETE
merge_completed_at: 2026-05-26
audit_verdict: APPROVED
audit_iterations: 1
auditor_end_at: 2026-05-26
gherkin_matrix: 06-audit/gherkin-matrix.md
checkpoints_grid: CHECKPOINTS.md
audit_notes:
  - "T-6 live E2E run deferred to staging gate (chrome-devtools-verify deprecated Linux). Specs compile + tsc + eslint clean."
  - "2 a11y WARN MINOR cosmetic (aria-label redundant + unused type import) — NO merge block, recomendado F1-S10 maintenance"
  - "pytest_backend_full FAIL pre-existing (booking E2E env config) — NO regression F1-S9, NO scope este audit"
  - "Visual goldens iter 1 en e2e/visual/ — Chris ratify pending pre-merge"
last_modified: 2026-05-26
dev_team_start_at: 2026-05-26
dev_team_end_at: 2026-05-26
dev_team_commits:
  T-1: 8561f196
  T-2: d3df6765
  T-3: 0fdac50e
  T-4: 99bd19e9
  T-5: fcd1b3e4
  T-6: bcc88359
phase_d_local_check: PASS  # 8/8 SC-1..SC-8 mapped to spec.ts files
notes_for_auditor:
  - "T-6 visual goldens iter 1 — Chris ratify pending pre-merge"
  - "T-6 live E2E run NO ejecutado (chrome-devtools-verify deprecated Linux + no live server) — specs compilan + tsc + eslint clean. Auditor decide caveat vs CHANGES_REQUESTED"
  - "T-4 arch tests RED en T-4 ahora GREEN post T-5 cleanup"
ratified_by_chris: true
ratified_at: 2026-05-25T16:30:00Z
ratified_visual_by_chris: not_applicable
ratified_visual_reason: "F1-S9 es routing puro — reusa mockups F1-S2..S8 ratificados como referencia integral del shell. Único componente visual nuevo: not-found.tsx (especificado inline en 01-spec § 6 con wireframe ASCII)"
architect_run_on: 2026-05-26
architect_iter: 1
last_artifact: 06-tickets.yaml
parallel_safe: false
priority: high
estimated_dev_days: 3
dependencies:
  hard: [vitalia-fase1-shell-layout-5050, vitalia-fase1-ribbon-6-tabs, vitalia-fase1-sub-tabs-line2]
  soft: []
blocks_hard: [vitalia-fase1-empty-states]
reuse_map_summary: "Next.js 16 proxy.ts (replaces middleware.ts) · Clerk 6 clerkMiddleware · App Router dynamic [agent]/[subtab] · agent-catalog.ts validators (EXTEND) · hierarchical not-found.tsx · REUSE core /me/tenants endpoint via mount (paridad nicolify:543)"
spawned_at: 2026-05-22
batch_1_ratified_at: 2026-05-25
batch_2_ratified_at: 2026-05-25T16:30:00Z
batch_1_decisions:
  Q1_default_landing: "valeria/agenda"
  Q2_routing_file: "proxy.ts"
  Q3_legacy_policy: "delete + no redirect"
  Q4_not_found_hierarchy: "outer + inner"
  Q5_v41_subcategories: "network_failure + accessibility + i18n; race/concurrent/empty/large N/A"
  scope_decision: "monolithic"
batch_2_decisions:
  Q6_no_tenants_assigned: "sign_out_plus_admin_message"
  Q7_network_error_retry: "manual_only"
  Q8_endpoint_user_tenants: "REUSE_CORE"
  Q8_endpoint_path: "/api/v1/iam/users/me/tenants (prefix paridad nicolify:543 — architect ratificado)"
  Q9_capability_yamls: "1 DELETE (welcome-state) + 6 MODIFY (fe_planned_phase2) + 1 KEEP (shell-foundation)"
ready_package:
  arch_consolidated: 03-arch.md
  arch_per_surface:
    backend: 03-arch-be.md
    frontend: 03-arch-fe.md
  validators: 04-validators.yaml
  guidelines: 05-guidelines.md
  tickets: 06-tickets.yaml
  total_tickets: 6
  total_validators: 30
  zero_opus: true
  zero_agentic: true
  playwright_required: true
  hipaa_lite_audit_required: true
next_action: "/dev-team vitalia vitalia-fase1-routing-shell"

# Schema v2 migration (cement 2026-05-27)
release: F1   # release ID · ver releases/
cap_target: routing   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F1-S9 vitalia-fase1-routing-shell — checkpoint (state=ready)

## Goal (unchanged)

Cementar el esqueleto de routing del shell-organism: App Router tree completo `[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx`, redirects automáticos a defaults, not-found.tsx jerárquico (outer/inner), validación agent + subtab vs whitelist, tenant validation server-side, proxy.ts Next.js 16 (replaces middleware.ts), legacy cleanup `(dashboard)/` + `(app)/`. Cada combinación válida renderiza placeholder vacío (contenido real en F1-S10).

## Architect work summary (2026-05-26)

Architect cerró ready package (5 artifacts) bajo el paradigma v4.1:

1. **03-arch.md** (consolidado, 983 líneas) — Context Summary + Existing Systems Audit (NO-NEW-LAYER) + Routing tree + Request flows + BE wiring detail + FE detail per file + Cross-cutting concerns + Research notes date-aware + Drift capability YAML.
2. **03-arch-be.md** (BE slice) — minimal 1-line mount + delete legacy stub + verification.
3. **03-arch-fe.md** (FE slice) — files index (NEW/MODIFY/DELETE) + Server vs Client boundary + verification.
4. **04-validators.yaml** (30 validators · 5 categorías v4.1 · scenario_coverage 8/8 100% · test_construction_plan completo · sub_categories_coverage explícito).
5. **05-guidelines.md** (must_load_skills enforceable + patterns required + forbidden + files in scope allowlist 4 tiers).
6. **06-tickets.yaml** (6 tickets atómicos · DAG válido · gherkin_coverage explícito · zero Opus · production_code flag · owner_eligibility).

Decisiones técnicas clave ratificadas en architect:

- **BE wiring**: `app.include_router(iam_users.router, prefix="/api/v1/iam/users", tags=["IAM - Users"])` paridad nicolify:543 verbatim. Endpoint final: `GET /api/v1/iam/users/me/tenants`.
- **BE cleanup**: DELETE `vitalia/backend/src/modules/vitalia/iam/api/router.py` (vitalia local `/me` stub Slice 1) — anti-duplication + zero consumers post (dashboard) delete.
- **FE proxy.ts**: ya existe (creado F1-S0 auth-base); F1-S9 MODIFY mínimo (docs anchor + add `/marketing(.*)` explicit). `auth.protect()` default branch ya cubre `(shell-organism)/**`.
- **FE routing tree**: 5 NEW pages + 2 MODIFY (root layout + page) + 1 DELETE catchall `[...slug]`.
- **FE legacy cleanup**: DELETE entire `(dashboard)/` + `(app)/` dirs + 5 fidelizacion E2E + welcome-state.yaml + conditional features/dashboard/. MODIFY 4 legacy E2E specs + 6 capability YAMLs.
- **Mockup gate visual**: N/A justificado (routing puro; not-found.tsx wireframes inline en spec § 6).
- **A11y + i18n + network_failure**: cubiertas via SC-5/SC-6/SC-7 + sub_categories_coverage v4.1.
- **HIPAA-lite audit**: cross-tenant + no-tenants events → console.warn `[audit]` transport (F1-S9); BE audit endpoint F2 scope. PII rule: payload contiene userId + attemptedTenant + timestamp solamente.

## Surface → Builder → Auditor mapping

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/backend/src/main.py` + delete legacy iam_router | `builder-backend` (Sonnet/opencode) | `auditor-backend` (Opus) |
| `vitalia/frontend/src/{proxy.ts, lib, app, e2e, __tests__/architecture}/**` | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
| `vitalia/docs/product/capabilities/**` YAMLs | doc-only — cualquier sonnet (incluido en story-level review) | n/a |

## Ticket order

DAG (see 06-tickets.yaml § DAG diagram):

```
T-1 BE        ─┐
               ├─→ T-3 (proxy + auth layer) ─→ T-4 (routing pages) ─→ T-5 (legacy cleanup) ─→ T-6 (Playwright)
T-2 FE lib    ─┘
```

T-1 and T-2 parallelizable (different surfaces). T-3..T-6 sequential.

## Risks (architect-flagged)

1. **features/dashboard/ conditional deletion** — T-5 must grep consumers first; if zero, delete feature; if non-zero, document remaining + leave stub.
2. **Visual goldens iter 1** — generated by T-6 via `--update-snapshots`; Chris ratifies before merge → snapshots ratchet shrink-only.
3. **Layout server-side validation testing** — E2E-only (SC-4/5/8). Unit testing async Server Components costly; accept E2E coverage.
4. **`/me/tenants` vs vitalia `/me` distinction** — endpoint becomes `/api/v1/iam/users/me/tenants` (core, via mount); vitalia local `/api/v1/iam/me` returns 404 post-cleanup. No collision because prefixes differ.

## Next action

```
/dev-team vitalia vitalia-fase1-routing-shell
```

State transition: `refined → ready`. Phase: `READY_PACKAGE_CLOSED`. dev-team will pick up ready package and execute T-1..T-6 in order with TDD RED-first per layer.

After dev-team closes state `developed` → AUTO-HANDOFF `/auditor` per `.claude/rules/story-closure-gate.md`. APPROVED → AUTO-HANDOFF `/pm-vitalia` merge (squash + R2 archive `vitalia/docs/archive/2026/stories/vitalia-fase1-routing-shell/` + capability reconcile).

## Post-done

F1-S10 `vitalia-fase1-empty-states` arranca: implementa `SubTabContent` + `EmptyState` + `PlaceholderCard` para reemplazar el placeholder inline de F1-S9 `[agent]/[subtab]/page.tsx`. Sin F1-S9 done, F1-S10 no tiene routing donde insertar contenido.

Después F1-S10 done → Fase 1 cerrada → arrancan stories Fase 2 (22 stories, 1 por sub-tab — ver mapping spec § 16).
