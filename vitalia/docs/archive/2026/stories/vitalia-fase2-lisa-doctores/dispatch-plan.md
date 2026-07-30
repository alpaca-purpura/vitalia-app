# dispatch-plan · vitalia-fase2-lisa-doctores

> Architect Opus 4.8 · 2026-05-31 · architecture_pattern: ADR-vitalia-004 (full).
> Per `.claude/rules/architect-autonomous-mode.md`. Chris ratified `autonomous_mode: true`.

## autonomous_mode

```yaml
autonomous_mode: true            # ratified by Chris (caller prompt)
ratified_by: chris
flow: "/dev-team picks up T-1 -> builds DAG -> AUTO-HANDOFF /auditor -> APPROVED -> AUTO-HANDOFF /pm-vitalia merge (reviewing -> done)"
```

### Why safe for autonomous

- No agentic production runtime (bio-gen is deterministic BE service, D-4 confirmed — NO R23 Opus gate).
- No engine edits (all `core/luana-core-*/src/` consumed read-only).
- No default-flip side-effects (§ 9.5 N/A).
- All cross-cutting gates have arch fitness tests (PHI, audit, response_model, public allow-list, voseo, FSD).
- Visual goldens ratified-mockup-backed (`mockups/doctores.html` ratified by Chris).

### Caps (autonomous guardrails)

```yaml
caps:
  audit_iterations: 4           # per auditor-self-fix-policy v4.2
  self_fix_iter: 5              # Carril A mechanical only (lint/format/typo/import)
  wall_clock_per_ticket: 45min
  fix_loop_per_ticket: 2        # CHANGES_REQUESTED cap
escalate_to_chris_if:
  - "credential validators country-specific need a 5th country (out-of-table)"
  - "pgcrypto/KEK env not configured in dev stack (blocks BE tests)"
  - "R2 live creds needed for an E2E that cannot mock (T-BE-7 chris_manual_action)"
  - "any availability_block edge produces data loss of confirmed appointments (CRITICAL — Carril C)"
  - "ADR-004 divergence emerges (would change adr_004_compliance from full)"
```

## Ticket -> agent -> model -> cost matrix

| Ticket | Surface | Agent | Model | Est. cost band | Auditor |
|---|---|---|---|---|---|
| T-BE-1 | backend | builder-backend | sonnet | M | auditor-backend (Opus) |
| T-BE-2 | backend | builder-backend | sonnet | M | auditor-backend |
| T-BE-3 | backend | builder-backend | sonnet | M | auditor-backend |
| T-BE-4 | backend | builder-backend | sonnet | S | auditor-backend |
| T-BE-5 | backend | builder-backend | sonnet | S | auditor-backend |
| T-BE-6 | backend | builder-backend | sonnet | S | auditor-backend |
| T-BE-7 | backend-ops | builder-backend | sonnet | XS (+ Chris manual) | auditor-backend |
| T-FE-1 | frontend | builder-frontend | sonnet | L | auditor-frontend (Opus) |
| T-FE-2 | frontend | builder-frontend | sonnet | L | auditor-frontend |
| T-FE-3 | frontend | builder-frontend | sonnet | L | auditor-frontend |
| T-E2E | frontend-e2e | builder-frontend | sonnet | M | auditor-frontend |

> NO ticket is Opus-production (R23 not triggered — no agentic runtime). All builders Sonnet. Auditors Opus (standard).

## Execution DAG (autonomous order)

```
T-BE-1 (foundation: doctor domain/model/repo/CRUD/migration/wiring)
   |
   +-- T-BE-2 (availability domain + rrule service) -- T-BE-3 (block endpoints + materialize)
   +-- T-BE-4 (bio-gen)
   +-- T-BE-5 (public endpoint + allow-list arch test)
   +-- T-BE-6 (assets proxy) -- T-BE-7 (R2 provisioning · Chris manual)
   +-- T-FE-1 (directory + hooks + MSW)
            |
            +-- T-FE-2 (EntitySubNavBar + workspace + perfil/bio/avatar)  [needs T-FE-1 + T-BE-4/5/6]
                     |
                     +-- T-FE-3 (horarios calendar)  [needs T-FE-2 + T-BE-3]
                              |
                              +-- T-E2E (Playwright + axe + visual goldens)  [needs FE-1/2/3 + BE-3/5/6]
```

Bucket locks (M14): BE tickets share `code:clinics` (serialize); FE tickets share `code:lisa` (serialize); BE and FE buckets run parallel. T-E2E last.

## Playwright visual scope (D3 discipline)

- **story_scope_routes:** `lisa/staff`, `lisa/staff/[doctor-id]/{perfil,horarios,servicios}`.
- **story_scope_components:** `features/lisa/components/staff/**` + `components/shared/shell-organism/EntitySubNavBar.tsx`.
- **forbidden_visual_changes:** `SubSubTabsBar.tsx`, `Ribbon.tsx`, `SubTabsBar.tsx`, `ValeriaSidebar.tsx`, `lisa/marca/**` (port wrapper verbatim, never modify).
- **out_of_mockup_scope:** Servicios funcional (placeholder only), KPIs (deferred), landing UI (deferred — toggle + endpoint only here).
- **non_egoismo_clause:** bugs in shell wrapper or lisa/marca -> document in `vitalia/docs/observed-bugs/`, do NOT fix here.
- Visual goldens: 6 (directorio/perfil/horarios × light/dark) + 1 (servicios-pendiente). `maxDiffPixelRatio: 0.001`. Side-by-side vs `mockups/doctores.html`.

## Post-merge actions (for /pm-vitalia F.3)

1. Write `vitalia/docs/product/capabilities/clinics/lisa.doctores.yaml` (v3.2: scenarios SC-1..SC-11 + access RBAC + 16 business_rules). change_log lineage + correct `availability-projection-via-engine` -> brand-local dateutil.
2. ADR-vitalia-004 § 3.1.1 addendum documenting `EntitySubNavBar` (N3-dynamic entity workspace pattern).
3. `git mv` story -> `vitalia/docs/archive/2026/stories/` (R2) in merge commit.
4. Create follow-up story stub "Mi Clinica · Servicios" (unblocks the servicios pendiente leaf).

## Invocation

```
/dev-team vitalia vitalia-fase2-lisa-doctores
```
Picks up T-BE-1 first (DAG root). Runs autonomous through APPROVED -> /pm-vitalia merge.

---

# DELTA v3 dispatch (D3-A..D3-F) · architect-orchestrator (Fable 5) · 2026-06-12

> Appends to the built ready package. `autonomous_mode: true` **retained from checkpoint** (unchanged), with TWO non-autonomous gates flagged below.

## autonomous_mode (delta)

```yaml
autonomous_mode: true            # unchanged from checkpoint
non_autonomous_gates:
  - "T-CORE-picker-slot merge: BLOCKED on /pm-luana promotion-proposal acceptance (edits core/@luana/ui-kit). Build is autonomous; MERGE is gated."
  - "Visual goldens (V-VIS-D3-1..5): Chris ratification in G (ADR-vitalia-003) — NOT autonomous, per existing story policy."
```

### Why still safe for autonomous (delta)
- No agentic runtime (bio-gen deterministic, D-4 holds — R23 N/A). Public page is read-only structured serialization.
- One core EXTEND (T-CORE-picker-slot) is **additive + back-compat + gated** by promotion proposal — not a silent engine edit.
- No default-flip side-effects (§ 10.5 N/A). All deltas additive (endpoints/columns/components).
- Cross-cutting gates have arch fitness tests (PHI dual-filter, public profile allow-list NEW, no-native-select for D3-F, response_model, FSD, voseo).

## Ticket -> agent -> model -> cost -> auditor matrix (delta)

| Ticket | Surface | Agent | Model | Cost band | Auditor |
|---|---|---|---|---|---|
| T-CORE-picker-slot | core-ui-kit | builder-frontend | sonnet | S (+ /pm-luana lift) | auditor-frontend (Opus) + /pm-luana |
| T-FE-switcher-wire | frontend | builder-frontend | sonnet | M | auditor-frontend |
| T-BE-bio-docs | backend | builder-backend | sonnet | M | auditor-backend (Opus) |
| T-FE-bio-docs | frontend | builder-frontend | sonnet | M | auditor-frontend |
| T-BE-occurrences-endpoint | backend | builder-backend | sonnet | M (regression RED) | auditor-backend |
| T-FE-occurrences-consume | frontend | builder-frontend | sonnet | M | auditor-frontend |
| T-FE-vista-mes | frontend | builder-frontend | sonnet | M | auditor-frontend |
| T-BE-pagina-publica | backend | builder-backend | sonnet | L (domain+migration+public+arch test) | auditor-backend |
| T-FE-pagina-publica | frontend | builder-frontend | sonnet | L (leaf+editor+public route) | auditor-frontend |
| T-BE-recurrencia-domain | backend | builder-backend | sonnet | M | auditor-backend |
| T-FE-recurrencia-editor | frontend | builder-frontend | sonnet | M | auditor-frontend |
| T-E2E-delta | frontend-e2e | builder-frontend | sonnet | M | auditor-frontend |

> NO Opus-production ticket (R23 not triggered — no agentic runtime). All builders Sonnet; auditors Opus.

## Execution DAG (delta autonomous order)

```
[parallel-ish roots, code:clinics serializes BE per M14]
  T-CORE-picker-slot ──► T-FE-switcher-wire
  T-BE-bio-docs ──► T-FE-bio-docs ──┐
        └──────────► T-BE-pagina-publica ──► T-FE-pagina-publica
  T-BE-occurrences-endpoint ──► T-FE-occurrences-consume ──► T-FE-vista-mes
        └──► T-BE-recurrencia-domain ──► T-FE-recurrencia-editor
  ALL FE ──► T-E2E-delta
```
- **Critical path:** T-BE-occurrences-endpoint → T-BE-recurrencia-domain → T-FE-recurrencia-editor → T-E2E-delta.
- **Order decision (mandate):** D3-C BE endpoint lands before D3-F BE domain (both edit `availability_projection_service.py` — serialize `code:clinics`). Migrations 040/041/042 additive; no shared-row conflict (D3-C endpoint reads only).
- Bucket locks M14: BE `code:clinics` serialize; FE `code:lisa` serialize; core `core:ui-kit` separate; buckets run parallel.

## Playwright visual scope (delta)

- **+routes:** `lisa/staff/[doctor-id]/pagina`, `/d/[clinica-slug]/[doctor-slug]` (public), horarios vista Mes.
- **+components:** `app/d/[clinica-slug]/[doctor-slug]/**`; `core/@luana/ui-kit/{EntitySubNavBar,EntityWorkspaceLayout}.tsx` (T-CORE only).
- **+forbidden:** `features/adrian/**`, `app/layout.tsx`, `components/ui/**`, `core/@luana/ui-kit/**` (except T-CORE).
- **Goldens (delta):** switcher-open, pagina, horarios-mes, recurrencia-editor (×light/dark) + public doctor-page (light). `maxDiffPixelRatio: 0.001`. Chris-ratified in G.

## Post-merge actions (delta · /pm-vitalia F.3 + /pm-luana)
1. `/pm-luana`: accept promotion proposal `2026-06-12-lift-entitysubnavbar-picker-slot.md` → mark migrated.
2. Update `capabilities/clinics/lisa-doctores.yaml`: scenarios SC-D3A/B/C/D/E/F + business_rules RN-D3A..F + access (public route unauthenticated read) + `dev_preview` (Página leaf + public route).
3. `modules/clinics.md` narrative if public doctor page is surfaced.
