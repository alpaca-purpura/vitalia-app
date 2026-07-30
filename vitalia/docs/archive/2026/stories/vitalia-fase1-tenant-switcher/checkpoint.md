---
story_id: vitalia-fase1-tenant-switcher
outcome: vitalia-mvp-ui-foundation
phase: fase-1
type: ui-story
agent_owner: shell
module: shell-organism
capability: shell.tenant-switcher
state: done
phase_state: MERGED_ARCHIVED
last_modified: 2026-05-23
developing_started_at: 2026-05-23T02:10:00-05:00
developing_finished_at: 2026-05-23T03:10:00-05:00
developing_owner: /dev-team (autonomous Sonnet per R23 FE no-agentic) + /dev-team orchestrator self-fix (2 lint+tsc fixes post-builder-cutoff)
reviewing_started_at: 2026-05-23T01:38:00Z                    # iter 1 audit run
reviewing_finished_at: 2026-05-23T02:13:00Z                   # iter 2 APPROVED
reviewing_owner: /auditor-frontend (Opus 4.7) 2 iter — CHANGES_REQUESTED iter 1 estructural test-page missing → APPROVED iter 2 post dev-team T-FIX-1 fix
audit_iterations: 2
audit_verdict: APPROVED
audit_self_fix_iter: 1                                         # Cat 17 val-arch-no-clerk-orgs yaml validator delegate
auto_fix_commits: [0f012ad1]                                   # T-FIX-1 dev-team caso B handoff
implementation_commits: [d99b1fdd]                             # T-1..T-10 base
merged_at: 2026-05-23
merged_via: "wip/vitalia branch direct (per current chain F1-S0..S3 pattern)"
chain_position: "F1-S3 último de chain · F1-S0 done 69948873 · F1-S1 done 5c59e89b · F1-S2 done c3bb6546 · F1-S3 done 2026-05-23 (CHAIN COMPLETE)"
pending_chris_visual_ratify: true                              # 5-min next session — compare 7 PNG goldens vs mockups
validators_green: [tsc, eslint, vitest_908_pass, F1-S3_unit_65_pass]
build_notes: "Builder Sonnet completó 10 tickets de implementación (TenantBadge + TenantOption + TenantSwitcher + AddClinicPlaceholderModal + TenantStoreBootstrap + Zustand tenant-store + useTenants React Query + useSignOutCleanup + arch test no-clerk-organizations + 5 Shadcn primitives instalados: alert/dialog/scroll-area/separator/skeleton + 11 Playwright specs + POM + fixtures + integración TopBarGlobal + layout.tsx mount Bootstrap + DELETE TenantSwitcherSlot.tsx). Builder cortado mid-fix sobre eslint require() en TenantSwitcher.test.tsx — orchestrator /dev-team aplicó 2 self-fixes whitelist (1: replace require() con ES import; 2: cast ReactNode→ReactElement en Children.map signature). Post-fix: tsc 0 errors + eslint 0 errors + vitest 908/908 PASS + F1-S3 unit suites 65/65 PASS (TenantBadge 10 + TenantOption 13 + TenantSwitcher 20 + tenant-store 15 + TenantStoreBootstrap 7). Visual goldens Playwright NO ejecutado (pending /auditor T-10)."
ticket_status: "T-1..T-10 implementación pushed bundle commit pendiente. T-result.md files no escritos (builder cortado). Auditor revisará code directo + visual goldens generation."
ratified_by_chris: true                            # Chris ratificó whole-doc 01-spec.md iter 1
ratified_visual_by_chris: true                     # Chris ratificó ambos mockups HTML iter 1
ratified_visual_at: 2026-05-22T17:00:00-05:00
ratified_visual_iter: 1
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/mockups/tenant-switcher-closed.html
  - vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/mockups/tenant-switcher-open.html
po_ux_iter: 1                                      # batched G6 round 1 closed 4 decisions D1-D4
architect_iter: 1                                  # /architect produced ready package iter 1 (2026-05-22)
architect_run_on: 2026-05-22
parallel_safe: true                                # paralelo a F1-S4..F1-S10
priority: high
estimated_dev_days: 1-2
dependencies:
  hard: [vitalia-fase1-stack-stability, vitalia-fase1-design-tokens-theme, vitalia-fase1-topbar-global]
  soft: []
blocks_hard: []
reuse_map_summary: "REUSE 75% nicolify/frontend/src/components/shared/layout/TenantSwitcher.tsx (adaptado: solo horizontal variant + Vitalia tokens + path preservation redirect + Tenant data shape minimal {id, name, city}). CONSUME core/luana-core-iam API tenants list via /api/tenants (BE shipped Story 11). NEW TenantBadge átomo (hash determinístico palette 6 colors) + TenantOption molécula + tenantStore Zustand persist localStorage + useSignOutCleanup Clerk hook cross-user isolation. Replace placeholder TenantSwitcherSlot null de F1-S2 drop-in."
ready_package_artifacts:
  - vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/01-spec.md            # 12 scenarios + sub-categorías mandatory + 22 ACs (ratified iter 1)
  - vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/mockups/tenant-switcher-closed.html  # 4 states (ratified iter 1)
  - vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/mockups/tenant-switcher-open.html   # 5 states (ratified iter 1)
  - vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/03-arch.md            # FE-only architecture (no BE, no agentic, no PHI)
  - vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/04-validators.yaml    # 5 categorías · 27 validators · agentic_eval N/A justified
  - vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/05-guidelines.md      # must_load_skills + patterns required/forbidden + files in scope
  - vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/06-tickets.yaml       # 10 tickets atómicos · ZERO Opus · gherkin_coverage explícito
decisions_cementadas_iter1:
  D1_badge_color: "hash determinístico tenant.id → paleta 6 [cyan/purple/fuchsia/amber/lime/rose] con contrast fix forward (amber+lime usan text-amber-950/text-lime-950)"
  D2_subtitle: "solo ciudad (BE devuelve {id, name, city})"
  D3_trigger: "truncate max-w-[180px] desktop + max-w-[140px] tablet + hidden sm:inline mobile + tooltip nativo title={tenant.name}"
  D4_mockup_data: "Sonrisa Plena (Lima cyan SP) · Dermalia MX (CDMX purple DM) · ClíniCare Bogotá (Bogotá fuchsia CB)"
architect_decisions_iter1:
  builder_routing: "ZERO Opus — FE no-agentic puro. owner_eligibility=[qwen-opencode, claude-sonnet] en 10 tickets."
  auditor_routing: "auditor-frontend (Opus) cubre BE/FE/agentic surfaces relevantes (BE=N/A, agentic=N/A, scope solo FE)"
  no_phi_scope: "F1-S3 declarado scope no-PHI explícito en 03-arch § 9. hipaa-lite.md NO aplica funcionalmente este PR."
  cross_brand_mirror_status: "2 brands con TenantSwitcher (nicolify legacy + vitalia adapted 75%) = under threshold 3 brands o identical >50%. Documentado en 03-arch § 10 tabla diferencias clave. Si comunify/lupulo lo necesitan Fase 2 → escala /pm-luana lift to core."
  signOut_cleanup_strategy: "useSignOutCleanup hook watch Clerk isSignedIn flip true→false → clearStore + localStorage.removeItem. Mounted en TenantStoreBootstrap invisible component dentro QueryClientProvider scope en root layout."
  path_preservation: "pathname.replace(/^\\/[^/]+/, `/${newTenantId}`) — pure exported function buildRedirectPath para test independiente. window.location.href hard redirect garantiza React Query cache reset + Clerk JWT re-validation."
  arch_test_introduced: "test-no-clerk-organizations.test.ts NEW arch fitness enforces MEMORY no-clerk-organizations 2026-05-20 (greps src/ for useOrganization/orgId/Clerk.*Organization/OrganizationSwitcher)."
  test_construction_plan_orden: "T-1 (palette pure) → T-2 (TenantBadge) → T-3 (TenantOption) → T-4 (store+signOut hook) → T-5 (useTenants) → T-6 (modal) → T-7 (organismo) → T-8 (integration) → T-9 (E2E) → T-10 (visual goldens + arch test)"
spawned_at: 2026-05-22
next_action: "/pm-vitalia bootstrap detecta story=ready → handoff a /dev-team para autonomous build secuencial T-1..T-10 → state developing"
po_ux_iter_history:
  iter_1_2026-05-22: "G6 round 1 closed 4 decisions D1-D4 + mockups closed/open ratified Chris + state refining→refined"
architect_iter_history:
  iter_1_2026-05-22: "Architect produced ready package (03-arch + 04-validators + 05-guidelines + 06-tickets). 10 tickets · ZERO Opus · 27 validators · 12 scenarios mapped · 8 visual goldens · NEW arch test no-clerk-orgs. state refined→ready."

# Schema v2 migration (cement 2026-05-27)
release: F1   # release ID · ver releases/
cap_target: tenant-switcher   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F1-S3 vitalia-fase1-tenant-switcher — checkpoint

## State

**`ready`** — ready package autocontenido (4 archivos producidos por /architect iter 1 2026-05-22). Próximo paso: `/pm-vitalia` bootstrap detecta state=ready → handoff a `/dev-team` para autonomous build.

## Goal

`TenantSwitcher` molécula: dropdown con lista de clínicas accesibles para el usuario actual + 2 actions footer (Agregar clínica placeholder · Administrar cuenta link). Persiste tenant activo en localStorage `vitalia-tenant-state` (Zustand partialize). Cambio dispara `window.location.href` hard redirect preservando ruta actual via `pathname.replace(/^\/[^/]+/, '/' + newTenantId)`. Cross-user isolation via Clerk signOut hook listener.

## Ready package artifacts (4 archivos /architect iter 1)

- **`01-spec.md`** (870 líneas) — 12 Gherkin scenarios + 22 ACs (ratified Chris 2026-05-22 iter 1)
- **`mockups/tenant-switcher-closed.html`** (4 states) + **`mockups/tenant-switcher-open.html`** (5 states) — visual contract ratified
- **`03-arch.md`** — FE-only architecture (surface mapping, types verbatim, code esqueleto componentes, React Query/Zustand configs, path preservation algorithm, palette + contrast fix, test plan, research notes 2026-05-22)
- **`04-validators.yaml`** — 5 categorías · 27 validators ejecutables (3 non_functional + 11 functional E2E + 8 visual + 5 architectural · agentic_eval N/A justified)
- **`05-guidelines.md`** — must_load_skills (frontend-expert + 5 tessl skills + playwright-expert) · 17 patterns required · 16 patterns forbidden · files in scope whitelist exhaustivo · DoD per ticket + per story
- **`06-tickets.yaml`** — 10 tickets atómicos · ZERO Opus · owner_eligibility=[qwen-opencode, claude-sonnet] · gherkin_coverage explícito per ticket

## Decisiones cementadas iter 1 (Chris ratify + architect close)

- **D1 Badge color** — hash determinístico `tenant.id` → paleta 6 colors (cyan/purple/fuchsia/amber/lime/rose) con contrast fix forward (amber+lime dark text)
- **D2 Subtitle** — solo city (BE shape `{id, name, city}`)
- **D3 Trigger** — truncate responsive + tooltip nativo
- **D4 Mockup data** — 3 clínicas LatAm realistic (Lima/CDMX/Bogotá)
- **D5 (architect)** — ZERO Opus FE no-agentic puro
- **D6 (architect)** — no-PHI-scope explicit (HIPAA-lite NO aplica funcional)
- **D7 (architect)** — cross-brand mirror under threshold (2 brands), documented adaptation diff vs nicolify reference
- **D8 (architect)** — useSignOutCleanup hook strategy para Scenario 6 isolation
- **D9 (architect)** — NEW arch test `test-no-clerk-organizations.test.ts` enforces MEMORY 2026-05-20

## Build sequence (10 tickets · estimated 1-2 dev_days)

```
T-1 (palette pure) ──────────────────────┐
T-2 (TenantBadge átomo) ────┐            │
T-3 (TenantOption molécula) ┤            │
T-4 (store + signOut hook) ─┤            │
T-5 (useTenants) ───────────┤            ├─→ T-7 (TenantSwitcher organismo)
T-6 (modal Dialog) ─────────┘            │       ↓
                                         │   T-8 (TopBarGlobal replace + layout mount + DELETE slot)
                                         │       ↓
                                         │   T-9 (E2E 11 specs + POM + fixtures)
                                         │       ↓
                                         └→  T-10 (Visual goldens 8 + NEW arch test no-clerk-orgs)
                                                 ↓
                                         state: developed → AUTO-HANDOFF /auditor
```

## Anti-objetivos (recap del spec)

- NO crear nueva API BE `/api/tenants` (shipped engine luana-core-iam Story 11)
- NO implementar "Agregar clínica" full flow (placeholder modal "Próximamente" — Fase 2)
- NO implementar "Administrar cuenta" full screen (link a `/{tenantId}/config/cuenta` — F2-S20 construye)
- NO usar Clerk Organizations (per MEMORY no-clerk-organizations 2026-05-20)
- NO search input dropdown (1-3 clínicas típicas; ≥5 escala F2)
- NO drag-reorder / favorite / recent-used tenants
- NO tocar `(dashboard)/` legacy
- NO instalar Shadcn primitives nuevos (F1-S0 instaló dropdown-menu + button + dialog + alert + skeleton)

## Próximo paso

`/pm-vitalia` (skill bootstrap detecta state=ready en backlog scan) → handoff explícito a `/dev-team` con prompt:

```
/dev-team brand: vitalia

Story: vitalia-fase1-tenant-switcher (F1-S3 Fase 1 shell-organism)
State: ready → developing (autonomous build)
Pr_folder: vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/

Toma 06-tickets.yaml ticket-por-ticket T-1..T-10 secuencial.
Builder agent: builder-frontend (Sonnet/opencode — ZERO Opus per architect iter 1).
Skills must_load per 05-guidelines § 1.
Rules must_load per 05-guidelines § 2.
Files in scope whitelist per 05-guidelines § 5.

Loop per ticket:
1. RED test primero (TDD)
2. GREEN implementation minimal
3. Run validators del ticket
4. Lint + typecheck clean
5. Commit Conventional + push wip/vitalia
6. T-{n}-result.md update

On all GREEN T-1..T-10:
- state developing → developed
- AUTO-HANDOFF /auditor (default — sin defer_audit)

Cap: 5 iter fix-loop por ticket. Si excede → blocked + escalate Chris.
```
