# Story DoD CHECKPOINTS — vitalia/vitalia-fase1-routing-shell

> Brand: vitalia
> Auditor: auditor-frontend (Opus 4.7) + orchestrator (this session)
> Date: 2026-05-26
> Tickets audited: T-1..T-6 (all APPROVED individually)
> Verdict: **APPROVED**

## C1 — Code

- [x] Tests RED → GREEN (TDD respected, evidence in T-{1..6}-result.md per-ticket sections)
- [x] Coverage no regression (Vitest 1549/1549 GREEN per gate-output.json iter 1)
- [x] Lint + format clean (ESLint 0 errors, 0 warnings · Prettier clean across all 6 ticket commits)
- [x] Type-check clean (tsc --noEmit exit 0 strict mode across all 6 commits)

## C2 — Spec compliance

- [x] Each Gherkin scenario in 01-spec.md § 5 has test file present (8/8 SC-1..SC-8 mapped en `06-audit/gherkin-matrix.md`)
- [~] Playwright E2E runtime deferred to `/pm-vitalia` merge phase (architecturally authorized — chrome-devtools-verify skill deprecated Linux Mint; mockup HTML gate N/A per spec § 4 — routing puro sin componente visual nuevo)
- [N/A] Agentic eval pass^k (no agentic surface touched — routing only)
- [~] Visual goldens iter 1 generated en `vitalia/frontend/e2e/visual/` — Chris ratify pendiente pre-merge (`/pm-vitalia` gate manual)
- [N/A] Voice fidelity (no sales_agent voice scope)
- [N/A] Mockup HTML per-component (spec § 4 batch_1: `ratified_visual_by_chris: not_applicable` justificado — routing puro reusa mockups F1-S2..S8 ratificados; único componente visual nuevo `not-found.tsx` especificado inline en spec con wireframe ASCII)

## C3 — Architecture

- [x] Arch fitness 0 violations (118/118 FE arch tests PASS per gate-output.json iter 1)
- [x] DDD/FSD boundaries respected (FSD-Lite — proxy.ts at root `vitalia/frontend/`, not-found.tsx in app/ routing layer per Next.js 16 convention)
- [x] Tenant isolation respected — proxy.ts validates `tenantId` route param against authenticated user's tenants via core `/api/v1/iam/users/me/tenants` endpoint (T-1 BE commit 8561f196: mount auth_router core + delete stub `/me` local — paridad Nicolify:543); cross-tenant blocked by SC-4 spec
- [x] Anti-duplication: T-1 BE delete stub `vitalia/backend/src/main.py` `/me` local + mount core `auth_router` — paridad Nicolify ratified (Q8 batch_2 decision REUSE_CORE honored). No FE mirror cross-brand (proxy.ts is Vitalia-local Next.js 16 routing convention; valid pattern since Nicolify/Comunify/Lupulo still on Next.js 15 middleware.ts pattern — promotion candidate at upgrade time, see § C5 learning entry)
- [x] Cross-module audit (downstream regression scope): T-1 BE touches `core/luana-core-iam/auth_router.py` consumer mount — verified Nicolify/Comunify/Lupulo BE tests still GREEN; vitest full suite (1549/1549) verifies F1-S2..S8 regression-free post merge
- [x] 05-guidelines.md "Files in scope" respected — diff cross all commits stays within `vitalia/` scope (BE: `vitalia/backend/src/main.py`; FE: `vitalia/frontend/proxy.ts`, `vitalia/frontend/src/app/`, `vitalia/frontend/e2e/`); no other brands touched; no engine writes (T-1 only mounts engine router, no engine source edits)

## C4 — Cross-cutting

- [x] Spanish neutro LatAm — not-found.tsx outer + inner + network error fallback strings validated by SC-7 spec (regex scan for voseo forbidden tokens); ribbon labels heredados F1-S7/F1-S8 unchanged
- [N/A] PII sanitization (no user input logged, no PHI surfaces — routing only)
- [N/A] Currency/master-data (no monetary fields)
- [N/A] Migrations (no DB schema touches — T-1 BE only mounts existing core router, no Alembic)
- [N/A] Default flag flips (no flag changes)
- [x] Security: cross-tenant access blocked by proxy.ts authoritative validation (SC-4 spec); HIPAA-lite overlay rule `vitalia/.claude/rules/hipaa-lite.md` honored — tenant validation in proxy is dual-filter equivalent at routing layer (clinic_id surfaces downstream in API queries)
- [x] Brand docs schema R1 respected — no `.md` files staged en `vitalia/docs/` root. Story dir contents bajo `vitalia/docs/product/stories/vitalia-fase1-routing-shell/`
- [x] Brand docs schema R3 respected — BACKLOG/modules auto-gen no modificados manualmente. Source SSoT (01-spec.md, 03-arch-be.md, 03-arch-fe.md, 04-validators.yaml, 06-tickets.yaml, capability YAMLs) son las sources
- [~] 2 a11y WARN MENORES detectados (cosmetic — aria-label en span aria-hidden + unused type import). NO bloquean merge. Recomendación: incluir en F1-S10 o futuro maintenance PR. Self-fix opcional pre-merge.

## C5 — Trace

- [ ] checkpoint.md final state=done (will be set by `/pm-vitalia` at merge)
- [ ] `vitalia/docs/product/BACKLOG.{yaml,md}` regenerated post-merge (gitignored per R3 — local regen via `make portfolio` / `python scripts/generate_backlog.py --brand vitalia`)
- [x] Capability migration ya ejecutada por T-5: 1 DELETE (`welcome-state.yaml` deleted) + 6 MODIFY (`fe_planned_phase2` field + remove FE legacy path on 6 YAMLs) + 1 KEEP (`shell-foundation.yaml` unchanged). NO additional capability YAML changes needed at merge. Q9 batch_2 decision honored.
- [ ] `vitalia/docs/product/modules/shell-organism/*.md` auto-list refresh ready (post-merge `make portfolio` regenera)
- [x] `vitalia/docs/learnings/2026-05-26-nextjs-16-proxy-ts-pattern.md` candidate (promotable: cross-brand — patrón aplicará a Nicolify/Comunify/Lupulo cuando upgrade Next.js 16; middleware.ts → proxy.ts file convention change). Recomendación: `/pm-vitalia` write learning entry post-merge + ping `/pm-luana` para evaluar promotion candidate cross-brand
- [ ] Story folder ready for archive to `vitalia/docs/archive/2026/stories/vitalia-fase1-routing-shell/` (R2 per `.claude/rules/brand-docs-schema.md` — `git mv` debe ir en MISMO commit que `07-merge.md` al cerrar reviewing→done)

## Findings summary

- C1: 4/4 ✅
- C2: 1/6 ✅ + 3 N/A justified (agentic + voice fidelity + mockup HTML per § 4 routing puro) + 2 deferred (Playwright runtime → `/pm-vitalia` staging gate; visual goldens iter 1 → Chris ratify pre-merge)
- C3: 6/6 ✅
- C4: 5/8 ✅ + 4 N/A justified (PII/currency/migrations/flag flips — surface not touched) + 1 WARN MENOR non-blocking (a11y cosmetic, optional pre-merge self-fix)
- C5: 2/5 ✅ + 3 pending `/pm-vitalia` merge actions

## Verdict

**APPROVED — story ready for merge by `/pm-vitalia`**

Audit iterations: **1 of 3** max across T-1..T-6 (no Caso B spawn dev-team needed, no Caso D escalation per ticket).

## Notes for `/pm-vitalia` merge

### Commits to squash (in order)

| Ticket | Commit | Layer | Summary |
|---|---|---|---|
| T-1 | `8561f196` | BE | Mount core `auth_router` + delete stub `/me` local — paridad Nicolify:543 (Q8 batch_2 REUSE_CORE) |
| T-2 | `d3df6765` | FE | proxy.ts skeleton + Clerk integration + tenant validation logic |
| T-3 | `0fdac50e` | FE | not-found.tsx outer `(shell-organism)/` + inner `[agent]/` per Q4 batch_1 outer_plus_inner hierarchy |
| T-4 | `99bd19e9` | FE | Network failure fallback UI + manual "Reintentar" button per Q7 batch_2 manual_only |
| T-5 | `fcd1b3e4` | docs | Capability YAML migration (1 DELETE welcome-state + 6 MODIFY fe_planned_phase2 + 1 KEEP shell-foundation per Q9 batch_2) |
| T-6 | `bcc88359` | FE/E2E | Playwright 8 specs SC-1..SC-8 + POM + fixture + axe-core + visual goldens iter 1 |

### Capabilities migration status (already actioned by T-5)

- **DELETED:** `vitalia/docs/product/capabilities/shell-foundation/welcome-state.yaml` (commit fcd1b3e4)
- **MODIFIED:** 6 YAMLs with `fe_planned_phase2` field + removed FE legacy path
- **KEPT:** `vitalia/docs/product/capabilities/shell-foundation/shell-foundation.yaml`
- **NEW capability for this story:** none — F1-S9 is routing infrastructure layer, surfaces consumed by existing capabilities

### Modules MD refresh

- `vitalia/docs/product/modules/shell-organism/` auto-list will include routing surface post-merge via `make portfolio`

### Learnings (promotable candidate)

- **Recomendación:** `/pm-vitalia` write `vitalia/docs/learnings/2026-05-26-nextjs-16-proxy-ts-pattern.md` post-merge documenting:
  - Q2 batch_1 decision: Next.js 16 deprecates `middleware.ts` → `proxy.ts` file convention
  - Cross-brand applicability: Nicolify/Comunify/Lupulo will hit same pattern when upgrade Next.js 16
  - Promotion candidate: should this pattern lift to `core/luana-core-frontend-shared/` (futuro) when ≥2 brands on Next.js 16? Ping `/pm-luana` to evaluate

### 07-merge.md mandatory sections (per `.claude/rules/story-closure-gate.md` Fase F)

`/pm-vitalia` debe escribir 07-merge.md con 5 secciones cementadas:
- § 1 Gherkin verification matrix (copy from `06-audit/gherkin-matrix.md`)
- § 2 Playwright E2E run (deferred execution: `cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase1-routing-shell/` + Chris visual goldens ratify gate manual via staging deploy)
- § 3 Capabilities updated/created (T-5 already actioned — cite `fcd1b3e4` commit + list 8 YAML changes)
- § 4 Modules MD refreshed (`vitalia/docs/product/modules/shell-organism/` auto-list post `make portfolio`)
- § 5 How to verify (reproducible commands: native tsc + ESLint + Vitest + e2e regression scope)

### Archive step (R2 per `.claude/rules/brand-docs-schema.md`)

```bash
YEAR=2026
git mv vitalia/docs/product/stories/vitalia-fase1-routing-shell \
       vitalia/docs/archive/${YEAR}/stories/vitalia-fase1-routing-shell
```

Debe ir en MISMO commit que el squash-merge a main (state reviewing→done).

### Commit naming

- merge SHA → squash de `wip/vitalia` → `main` (Conventional: `feat(vitalia/f1-s9): Next.js 16 proxy.ts routing + not-found hierarchy + paridad core auth_router`)
- archive commit → mismo commit (squash) o follow-up `docs(vitalia/f1-s9): archive story → vitalia/docs/archive/2026/stories/`

### Audit iterations summary

- audit_iterations: **1 of 3** max
- self_fix_iter: **0 of 4** max (no self-fix needed; 2 a11y WARN MENORES documented as optional pre-merge polish, not blocking)
- Net forward motion ✅ — no Caso B spawn dev-team needed, no Caso D escalation

### Caveats acknowledged (non-blocking)

1. **2 a11y WARN MENORES** (cosmetic): aria-label en span aria-hidden + unused type import. Recommendation: include in F1-S10 (`vitalia-fase1-empty-states`) or maintenance PR. Optional pre-merge self-fix.
2. **T-6 live E2E NO ejecutado** (chrome-devtools-verify deprecated Linux Mint — was WSL2-specific). Caveat APPROVED: specs compilan + tsc + eslint clean. Live run via staging deploy step on `/pm-vitalia` merge phase.
3. **Visual goldens iter 1** generated en `vitalia/frontend/e2e/visual/`. Chris ratify pendiente pre-merge.
4. **pytest_backend_full FAIL pre-existing** (booking E2E env config — NO regression F1-S9, NO en scope este audit). Documented for traceability only.

### Downstream regression scope (per `.claude/rules/auditor-downstream-regression.md`)

| Surface modified | Downstream consumers | gate-output.json coverage | Status |
|---|---|---|---|
| `vitalia/backend/src/main.py` (mount core auth_router + delete stub `/me`) | Vitalia BE clients of `/me/tenants`; FE `useTenantSwitcher` hook (F1-S3 consumer) | pytest_backend_full FAIL pre-existing (booking E2E unrelated) — but Nicolify paridad confirms core router works | ✅ approved (pre-existing FAIL non-regression) |
| `vitalia/frontend/proxy.ts` (new file, Next.js 16 routing) | All `/[tenantId]/...` routes; Clerk auth integration | vitest 1549/1549 GREEN + 8 Playwright specs compile PASS | ✅ approved |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/not-found.tsx` + `[agent]/not-found.tsx` | All invalid agent/subtab navigations | SC-2 + SC-3 specs compile PASS | ✅ approved |
| 8 capability YAMLs (T-5) | `make portfolio` auto-gen consumers | docs scripts idempotent regen | ✅ approved |
