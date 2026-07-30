<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Code Review — vitalia-stub-caps-scenario-backfill (Conv 3, independent)

**Date:** 2026-05-30
**Brand:** vitalia
**Story:** vitalia-stub-caps-scenario-backfill — technical-story (cap scenario+e2e backfill, stub→verified-live honest)
**Files reviewed:** 38 (scripts/ tooling + 2 backend + 20 cap YAMLs + story docs + e2e specs)
**Diff:** a6a4d86f^..HEAD (7993c3f3 head)
**Verdict:** **APPROVED**

All checks were re-run independently by the auditor (not trusted from the result files).

## Verdict math
- Anti-teatro / relevance (SC-4 key category): PASS — zero irrelevant proxies
- Authoritative gates (compute_status + bidirectional --strict cross_check_3): PASS
- Fix-to-green db-state (ratified exception): APPROVED — real bug, correct pattern, ruff clean, live 200
- Boundaries (no engine, no cross-brand): PASS
- T-0 regression (validator path-aware): PASS
- 6 partial honesty: PASS — correct anti-teatro, NOT a defect
→ overall **APPROVED**

---

## 1. Anti-teatro / relevance (SC-4) — PASS (key category)

Re-parsed the frontmatter of all 20 target cap YAMLs and cross-checked every
`e2e_test` against the filesystem + test-fn presence:

```
ISSUES (irrelevant/missing/no-test wired e2e_test): NONE
  → every wired e2e_test exists AND contains a test fn
  (.py contains `def test`, .ts contains `test(` / `test.describe`)
```

Spot-checked ≥4 caps across groups, reading scenario given/when/then vs the wired test body:

| cap (group) | wired e2e_test | genuinely exercises the scenario? |
|---|---|---|
| `topbar-global` (G1) | `e2e/regression/topbar-global/topbar-interaction.smoke.spec.ts` | YES — 6 tests assert role=banner + data-testid, logo aria-label='Vitalia inicio' + href='/', `html[data-theme=dark]` toggle, 48px height, zero console errors. Matches scenario verbatim. |
| `hipaa-dual-filter-decorator` (G4 pytest) | `tests/architecture/test_phi_dual_filter.py` | YES — AST-scans PHI repos for tenant_id AND clinic_id in `.where()`, 4 tests, runs GREEN. Matches scenario. |
| `playwright-smoke-suite` (G3) | `e2e/regression/topbar-global/topbar-interaction.smoke.spec.ts` | YES — RE-POINTED (T-D) to the GREEN topbar smoke, NOT the failing sign-in. The scenario given/when/then is honestly written around the topbar spec. Correct per brief. |
| `admin-streamlit-service` (G2) | `e2e/admin/admin-login.spec.ts` | YES — 3 tests (login bcrypt → sidebar Tenants/Usuarios, session-destroyed → login form). |
| `api-health-endpoint` (G3) | `tests/integration/test_api_health_endpoint.py` | YES — ASGI httpx contract test, asserts 200 + body `{status:ok, brand:vitalia}` + `/health` alias. NOT a "curl 200" proxy. |
| `public-clinic-landing` (G1, partial) | `e2e/public/public-clinic-landing.smoke.spec.ts` | YES — asserts no redirect to /sign-in, `<main>` visible, slug renders, 200. The two patient-journey scenarios are honestly `e2e_test: null`. |

Ran the G4 backend battery independently — all GREEN:
`test_phi_dual_filter` (4), `test_migrations_idempotent` (8), `test_audit_log_sync_write` (7),
`test_audit_log_row_per_phi_endpoint` (12), `test_cron_envelope_used` (4), `test_arq_settings` (10),
`test_no_observability_mirror_copilot` (10), `test_otel_setup` (2 pass + SKIPs = graceful degradation by design, exactly as the cap scenario states).

No `e2e_test` is a proxy passing-but-unrelated test. No `.py` lacks `def test`; no `.ts` lacks `test(`.

## 2. Authoritative gates — PASS

```
compute_capability_status.py --brand vitalia:
  20 target caps → 14 verified-live + 6 partial (zero still stub). Matches brief exactly.
  (partials: iam-scaffold-slice-1, public-clinic-landing, tenants-crud, users-crud,
   clinics-crud, streamlit-tenants-users)

validate_code_cap_bidirectional.py --brand vitalia --strict:
  cross_check_3 (HARD): total=90 pass=90 drift=0
  cross_check_4 (advisory): total=12 pass=11 drift=1 (PRE-EXISTING RBAC gap, not this story)
  Verdict: SOFT_DRIFT · drift in HARD checks=0 · exit=0
```

Note: VERIFICATION-REPORT.md prose lists `sign-in-sign-up-pages` + `admin-streamlit-service`
as "partial", but the computed status (authoritative cap YAMLs) shows both as verified-live,
and the 6 actual partials match the brief's expected set exactly. The report prose is slightly
stale vs the final YAMLs — cosmetic, non-blocking (the cap YAMLs + gate output are SSoT).

## 3. Honesty of the 6 partials — PASS (this is CORRECT, not a defect)

Every partial cap has ≥1 scenario with `e2e_test: null` + honest rationale:

```
tenants-crud           : tenant-write-ui-e2e-pendiente-hardening
users-crud             : user-write-ui-e2e-pendiente-hardening
clinics-crud           : clinic-write-ui-e2e-pendiente-hardening
streamlit-tenants-users: tenant-user-link-write-ui-e2e-pendiente-hardening
iam-scaffold-slice-1   : iam-routing-nav-e2e-pendiente-hardening
public-clinic-landing  : paciente-ve-landing-clinica + paciente-inicia-reserva-desde-landing
```

Rationale is honest in each case (fragile Streamlit write selectors → dedicated hardening story;
ribbon testid-duplicate nav POM bug; 3-clinic fixture excluded from this story). No partial was
forced to false verified-live. This is exactly the anti-teatro behavior the bar requires.

## 4. Fix-to-green db-state (ratified exception) — APPROVED

Commit `882f9f49` touched feature code `vitalia/backend/src/modules/vitalia/admin/api/admin_helpers_router.py`.
Real bug fix: 5 helper endpoints used `async for db in get_db()` with the engine SYNC `get_db`
(`luana_core_platform.core.database`) → `'async for' requires __aiter__` (500).

- **Correctness:** fix swaps to `get_async_session` from `src.db` (verified: `AsyncGenerator[AsyncSession]`),
  the same pattern already used by payments (`charge_router`) + scheduling (`agenda_router`, `notify_router`). Correct.
- **ruff:** `All checks passed!` on the changed file.
- **No engine edit:** still imports from engine only `TenantModel` etc.; uses `src.db` async session. No `core/luana-core-*/src/` modified.
- **Live verification:** `GET /api/v1/vitalia/admin/db-state → HTTP 200` confirmed independently (with `X-Internal-Token`). The endpoint responds post-fix.

Ratified by Chris (chris-input entries 2026-05-29 19:30 + 2026-05-30): "fix-to-green dentro de la story".
This is the deployed-visible bar working as designed — the cap looked live mechanically but was broken when exercised.

## 5. Boundaries — PASS

```
git diff a6a4d86f^..HEAD --name-only | grep -E '^core/|^(nicolify|comunify|lupulo)/'  → EMPTY
```
Zero engine `core/luana-core-*/src/` edits. Zero cross-brand. T-0 touched `scripts/*.py`
(cross-cutting tooling, NOT engine) under fase solo-bootstrap (SCOPE_GATE_SKIP documented) — OK.

## 6. T-0 regression (validator path-aware) — PASS

```
.venv/bin/pytest scripts/tests/test_validate_code_cap_bidirectional.py -q  → 19 passed
```
The path-aware change to cross_check_3 (accept `def test` for `.py`, keep `test(`/`test.describe`
for `.ts`) is purely additive — `.ts` caps still validate identically (90/90 pass, drift=0, all
the `.ts`-wired G1/G2 scenarios validated correctly).

## Self-fix log
None applied (no findings requiring fix).

## Notes / non-blocking
- VERIFICATION-REPORT.md prose partial-list is slightly stale vs final cap YAMLs (sign-in / admin-streamlit). Cosmetic; gate output + cap YAMLs are SSoT and correct. Optional cleanup in a future doc pass.
- cross_check_4 drift=1 is the pre-existing RBAC advisory gap, untouched by this story.

## Handoff
APPROVED → `/pm-vitalia` merge (reviewing → done). Then Slice 2 PHI (separate story).
