<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Backend Code Review: T-4 — Admin Streamlit Vitalia + 3 integration tests

**Date:** 2026-05-19
**Brand:** vitalia
**Story:** vitalia-auth-base-functional
**Commit:** 2b056a5
**Files Reviewed:** 23 (17 NEW production + tests, 1 EDIT pyproject.toml, 1 EDIT test ratchet + 4 result/log docs)
**Domains touched:** vitalia/backend/src/modules/vitalia/admin/, vitalia/backend/src/modules/vitalia/compliance/audit.py
**Skills consulted (per IMPL-LOG):** backend-expert, tessl__fastapi, tessl__pytest-api-testing, tessl__graceful-degradation
**Verdict:** **WARN (CHANGES_REQUESTED minor)**

## /test-backend Gate Status

Caller provided gate-output.json (audit-1) — re-verified key gates locally:

| # | Gate | Result | Detail |
|---|---|---|---|
| 1 | Tools | PASS | uv venv 3.12, pytest 9.0.3, ruff |
| 2 | Postgres pre-flight | DOWN | Integration tests SKIP gracefully (5 skipped, 15 passed admin suites) |
| 3 | Lint (ruff check) | PASS | 0 errors on admin/ + tests/admin + tests/integration/admin |
| 4 | Format (ruff format) | PASS | 19 files already formatted |
| 5 | Type check (mypy) | n/a | not in T-4 validator command list (covered by global suite) |
| 6 | Arch fitness | PASS | 245 passed (re-run 2026-05-19) |
| 7 | Tests + coverage | PASS | 1085 passed in non-integration suite; T-4 admin: 8 contract + 12 integration (5 skipped) |
| 8 | Verify marker | n/a | not in scope for T-4 |
| 9 | Integration | SKIP | Postgres unavailable — pytest_collection_modifyitems auto-skip on `@pytest.mark.integration` |
| 10 | Migration idempotency | PASS-by-design | 013_vitalia_audit_log uses `IF NOT EXISTS` / `DO $$ EXCEPTION` (pre-existing Story 11) |
| 11 | jscpd | n/a | not in T-4 validator list |
| 12 | interrogate | n/a | not in T-4 validator list |
| 13 | pip-audit | n/a | not in T-4 validator list (deps added: streamlit, passlib[bcrypt], bcrypt, clerk-backend-api — recommend pip-audit on next CI run) |
| ★ | anti-duplication scan | **PASS** (corrected) | 1500 diff lines >> 50 threshold → validator script `[ "$MIRROR_COUNT" -gt 50 ]` returns exit 0. Gate-runner mislabeled this as FAIL in audit-1; manual re-run confirms PASS. |

**Note on gate-runner anti-duplication mislabel:** The validator is correctly written ("MUST differ ≥50 lines"). 1500 diff lines = vitalia code is highly distinct from nicolify. Confirmed manually:
```
WS=$(git rev-parse --show-toplevel) && MIRROR_COUNT=$(diff <(find $WS/nicolify/backend/src/modules/nicolify/admin/modules -name tenants.py -o -name users.py | xargs cat) <(find $WS/vitalia/backend/src/modules/vitalia/admin/modules -name tenants.py -o -name users.py | xargs cat) | wc -l) && [ "$MIRROR_COUNT" -gt 50 ] && echo PASS
→ MIRROR_COUNT=1500 — PASS
```

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | 0 — admin is application-layer entry (per admin-panel.md), no cross-module imports |
| 2 | Tenant Isolation | WARN | 1 — admin reads `vitalia_clinics` / `vitalia_user_profiles` globally (no `tenant_id` WHERE); by-design super-admin, but undocumented intent |
| 3 | Soft Deletes | PASS | 0 — users.py respects `WHERE up.deleted_at IS NULL` in user list query |
| 4 | Code Quality | PASS | 0 — ruff check + format clean; complexity OK (PLR0912 noqa in 2 form renderers justified by Streamlit UI surface) |
| 5 | SQLAlchemy 2.0 | PASS | 0 — `text(...)` + `session.execute(...)` only; no legacy `session.query()` |
| 6 | Async Consistency | WARN | 1 — `compliance/audit.py::log_admin_action()` is `async` but admin modules call sync `INSERT INTO vitalia_audit_log` inline (Streamlit is sync, can't await); split = code duplication |
| 7 | Pydantic v2 / DTOs / PII | PASS | 0 — admin uses Streamlit (no API DTOs); webhook routes (preexisting) have `response_model=WebhookAck` |
| 8 | Migration Quality | PASS | 0 — `013_vitalia_audit_log.py` pre-existing (Story 11) is idempotent raw SQL + partitioned |
| 9 | Security | WARN | 2 — see § Findings (bcrypt error logged but generic; magic link admin action not audited) |
| 10 | Tests / TDD | PASS | 0 — 8 contract tests + 12 integration (5 skip gracefully); RED-before-GREEN cited in IMPL-LOG |
| 11 | Cross-cutting (Spanish/Native-First/Decisions) | PASS | 0 — Spanish neutro tuteo verified ("Ingresa", "Crea", "Selecciona"); no `git add .` / `--no-verify` in commit |
| 12 | Mirror detection | PASS | 0 — 1500 diff lines vs nicolify (anti-duplication scan); no cross-brand leakage; tenant_id correctly placed in audit_log writes |

## Cross-scope flags

None — all T-4 files are in vitalia/backend/src/modules/vitalia/{admin,compliance}/ + vitalia/backend/tests/. No core/luana-core-*/ touches. No other-brand touches. No copilot/sales_agent business edits.

## Findings

### WARN — Tenant isolation: admin clinic/user list queries lack tenant_id filter
**Category:** 2
**File:** `vitalia/backend/src/modules/vitalia/admin/modules/tenants.py:99-108` (clinic_list) + `users.py:88-100` (user_list)
**Issue:** Admin reads `vitalia_clinics` and `vitalia_user_profiles` with only `WHERE c.is_active = true` or `WHERE c.slug = :slug`. No `tenant_id` filter. The audit_log writes DO include `tenant_id + clinic_id` (HIPAA dual filter correctly enforced), but list/detail queries operate across all tenants.

By design: admin is super-admin → global view is intended. BUT the tenant-isolation cardinal rule (`.claude/rules/tenant-isolation.md`) says "every query must filter by `tenant_id`. Sin excepciones." There's no explicit module/file-level docstring asserting "super-admin globally-scoped — intentional bypass". Future devs copying this pattern into a per-tenant admin or non-super-admin context would silently leak cross-tenant data.

**Fix:** Add explicit module docstring + per-function docstring noting super-admin context, e.g.:
```python
# ── Super-admin scope ────────────────────────────────────────────────────
# Admin Streamlit is a super-admin tool (authenticated via single bcrypt env var).
# These queries intentionally span all tenants. Adding a tenant_id WHERE clause
# here would break the super-admin global view. DO NOT copy this pattern into
# per-tenant routes — per-tenant code MUST filter by tenant_id (see
# .claude/rules/tenant-isolation.md).
```
Optionally add an arch-fitness allowlist entry for `modules/vitalia/admin/` so the global tenant-isolation gate doesn't false-positive on these files.

**Skill ref:** `.claude/rules/tenant-isolation.md`, `vitalia/.claude/rules/hipaa-lite.md § Tenant isolation refuerzo`

### WARN — Architectural inconsistency: `log_admin_action()` async helper bypassed by sync admin modules
**Category:** 6
**File:** `vitalia/backend/src/modules/vitalia/compliance/audit.py:30-107` (async helper) vs `vitalia/backend/src/modules/vitalia/admin/modules/tenants.py:268-285` + `users.py:248-265` (inline sync `INSERT INTO vitalia_audit_log`)
**Issue:** The canonical HIPAA-lite audit log helper `log_admin_action()` is defined as `async` (uses `AsyncSession`), and the integration tests verify it via `await log_admin_action(session=db_session, ...)`. BUT the production admin modules (tenants.py, users.py) cannot use it because Streamlit is synchronous — they re-implement the same `INSERT INTO vitalia_audit_log` SQL inline with sync `session.execute()`. This means:

1. Tests pass — `log_admin_action()` works correctly when awaited.
2. Production runs different code — the inline SQL in admin modules.
3. Future PHI sanitization fixes to `log_admin_action()` won't propagate to the admin code paths.
4. Code duplication (sanitize_phi_payload + identical INSERT SQL in 3 places: audit.py, tenants.py, users.py).

The HIPAA invariants ARE enforced (sanitize_phi_payload called inline in both admin modules before INSERT), but the canonical helper is dead code w.r.t. production admin actions.

**Fix:** Either (a) add a sync sibling `log_admin_action_sync(session: Session, ...)` in `compliance/audit.py` and refactor admin modules to call it, eliminating the inline SQL; or (b) document explicitly in `audit.py` docstring that "this async helper is for FastAPI/webhook flows; admin Streamlit modules use the parallel sync implementation in `admin/modules/{tenants,users}.py` — keep both in sync if schema changes." Option (a) is preferable (DRY + single PHI sanitization choke-point).

**Skill ref:** `.claude/rules/backend-ddd.md § Schema-mirror exception` (similar pattern: schema mirror is OK with documentation); `vitalia/.claude/rules/hipaa-lite.md § Audit log` (sync write before response is satisfied either way)

### WARN — Magic link generation action not audited (HIPAA-lite gap)
**Category:** 9
**File:** `vitalia/backend/src/modules/vitalia/admin/modules/users.py:286-323` (`_render_magic_link_form`)
**Issue:** The magic link generation form calls `_send_magic_link(email, redirect_url)` which generates a Clerk sign-in token that grants access to a PHI-bearing account. Unlike "create user" and "create tenant" (both correctly write `vitalia_audit_log` rows), the magic link path does NOT write any audit row.

Per `vitalia/.claude/rules/hipaa-lite.md § Audit log`:
> "TODA lectura/modificación de PHI registra row. NO opcional."

Magic link itself isn't PHI, but it's an auth-equivalent action with downstream access implications. HIPAA general best-practice + the rule's broader "no audit log gap for admin-actor-grants" intent argue for an audit row here too (`action="user.magic_link_sent"`).

**Fix:** After successful `_send_magic_link()` (line 316), write an audit_log row mirroring the create_user pattern:
```python
# HIPAA-lite audit log — SYNC WRITE for auth grant action
safe_payload = sanitize_phi_payload({"email": _email, "redirect_url": redirect_url.strip()})
payload_bytes = _encode_payload(safe_payload)
session.execute(
    text("""INSERT INTO vitalia_audit_log ... 'user.magic_link_sent', 'user_profile', ..."""),
    {...}
)
session.commit()
```
Resolve tenant_id + clinic_id from email lookup first (already needed for any audit context).

**Skill ref:** `vitalia/.claude/rules/hipaa-lite.md § Audit log`

### WARN — Bcrypt error catch swallows specific failures (auth diagnostics + brute-force protection)
**Category:** 9
**File:** `vitalia/backend/src/modules/vitalia/admin/_shared/auth.py:62-67`
**Issue:** `verify_admin_password()` catches all bcrypt errors as `Exception` with a generic `noqa: BLE001` and returns False. While fail-secure is correct, the structlog log includes `error=str(exc)` — for unusual bcrypt failures (invalid hash format, library corruption), this could leak which env-state caused failure to logs that are widely visible. More importantly, there's no rate-limit / lockout signal: a brute-forcing actor sees identical "Contraseña incorrecta" output regardless of whether the failure was bad password vs malformed hash env vs library error.

**Fix:** (a) Categorize `bcrypt.error` (e.g., `ValueError` for malformed hash) vs unexpected errors — log differentiated severity; (b) Consider adding a per-session `failed_attempts` counter in `st.session_state` and lock out after N=5 attempts (5min window) — Streamlit best-practice; (c) Add structlog `password_truncated_len=len(plain_password)` (a length-only telemetric, no content leak) to differentiate empty/short-input mistakes from real attacks. These are defense-in-depth, not strict blockers.

**Skill ref:** general security hygiene; `vitalia/.claude/rules/hipaa-lite.md § Access control (RBAC strict)`

### info — Test env var mutation without monkeypatch cleanup
**Category:** 10
**File:** `vitalia/backend/tests/integration/admin/test_cross_tenant_isolation.py:163, 186`
**Issue:** Tests set `os.environ["VITALIA_ADMIN_PASSWORD_HASH"] = pw_hash` directly (not via `monkeypatch.setenv`). With `pytest-randomly` enabled (root pytest config), env state leaks across tests in random order can cause flaky failures (e.g., a later test that depends on `VITALIA_ADMIN_PASSWORD_HASH` unset gets it polluted).
**Fix:** Refactor to use `monkeypatch.setenv` fixture or wrap each test's env mutation in a try/finally that restores prior value. Non-blocking — current code happens to work because tests both set the same env key and both expect it set.
**Skill ref:** `tessl__pytest-api-testing § fixture scoping`

### info — Late streamlit imports inside functions (intentional for testability)
**Category:** 4
**File:** Multiple — all `_shared/`, `pages/`, `modules/` files use `import streamlit as st  # noqa: PLC0415` inside function bodies
**Issue:** This is INTENTIONAL — keeps `streamlit` an optional import so admin contract tests + arch fitness tests can import the registry without installing Streamlit in CI. Verified the pattern works (contract tests pass without Streamlit). Just flagging the pattern is unusual but justified — keep docstring note in `app.py` or `_shared/__init__.py` to prevent refactor that moves imports to module level.
**Fix:** Optional — add a single-line note in `_shared/__init__.py` documenting "Streamlit imported lazily in each function for test-time importability". Non-blocking.

## Contract Compliance (T-4 surface)

- [x] Contract test `test_admin_contract.py` (8 tests, all PASS)
- [x] PAGE_SPECS registry: `tenants` + `usuarios` slugs present, no duplicates, callable render_fn — verified
- [x] `_shared/auth.py::verify_admin_password` callable + bcrypt-based (D8 single password env-var)
- [x] `_shared/db.py::get_sync_session` context manager — verified
- [x] `compliance/audit.py::log_admin_action` async helper exists + uses sanitize_phi_payload
- [x] `compliance/domain/phi_fields.py::PHI_FIELDS_TOP_LEVEL + PHI_PATIENT_SUBFIELDS` SSoT created
- [x] Integration tests `test_clerk_webhook_integration.py` (5 tests, no Postgres required) — all PASS
- [x] Integration tests `test_audit_log_verify.py` + `test_cross_tenant_isolation.py` (Postgres-gated) — graceful SKIP confirmed
- [x] CONTRACT § 8 Agentic Surfaces — not applicable to T-4 (no agentic touch)
- [x] anti-duplication validator: 1500 diff lines vs nicolify (corrected verdict: PASS)

## Allowlist Movement

- Test ratchet `tests/unit/test_models_import.py`: 12 → 14 (vitalia_brand_studio_drafts + vitalia_onboarding_progress) — D6 in IMPL-LOG documents this came from prior tickets, T-4 adds NO new ORM models (admin uses raw SQL only). Allowlist GREW by 2; commit body justifies the growth as "from prior tickets" — acceptable (not introduced by this ticket).
- No arch fitness `KNOWN_*` allowlist growth detected.

## Native-First Audit
- [x] No `docker exec ... ruff|pytest` in commits
- [x] No `git add .` / `-A` / `-u` in commits (commit shows exact file list)
- [x] N/A for `make ci-parity` (T-4 is BE work pushed to wip/vitalia, not main)

## Downstream regression scope (per .claude/rules/auditor-downstream-regression.md)

T-4 surface modified:

| Surface modified | Downstream test targets | gate-runner status |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/admin/**` (NEW) | `vitalia/backend/tests/admin/`, `vitalia/backend/tests/integration/admin/` | PASS (15 + graceful SKIP 5) |
| `vitalia/backend/src/modules/vitalia/compliance/audit.py` (NEW) | `vitalia/backend/tests/integration/admin/test_audit_log_verify.py` (Postgres-gated SKIP) | gated |
| `vitalia/backend/src/modules/vitalia/compliance/domain/phi_fields.py` (NEW) | Consumed by `audit.py` + admin modules `sanitize_phi_payload`; tests verify via integration | gated |
| `vitalia/backend/pyproject.toml` (added: streamlit, passlib[bcrypt], bcrypt, clerk-backend-api) | None directly; pip-audit recommended on next push | n/a |
| `vitalia/backend/tests/unit/test_models_import.py` (ratchet 12→14) | Self-validating | PASS |

No engine (`core/luana-core-*/`) edits → no cross-brand fan-out. No other-brand pollution.

Cross-brand mirror scan vitalia ↔ nicolify admin modules: 1500 diff lines (>>50 threshold) — PASS, no mirror.

## Runtime-gated validators (post-merge execution)

The following validators are not executed in this audit (require post-deploy env):
- `vs-playwright-smoke-local-pre-deploy` — E2E LOCAL (auditor-frontend)
- `vs-playwright-smoke-live` — E2E LIVE post-deploy (auditor-frontend)
- `vs-playwright-trace-broader-monitor` — auditor-frontend
- `vs-playwright-a11y-axe` — auditor-frontend
- `vs-playwright-mobile-viewport` — auditor-frontend
- `vs-playwright-screenshot-baseline` — auditor-frontend
- `fn-be-webhook-clerk-integration` (the Postgres-gated portions) — execute post-deploy with vitalia_test DB available
- `fn-be-hipaa-audit-log-verify` (Postgres-gated) — execute post-deploy
- `fn-be-cross-tenant-isolation-admin` (Postgres-gated portions) — execute post-deploy

All BE-side static gates GREEN. Postgres-gated tests confirmed to skip gracefully (not fail) in absence of DB.

## Verdict Math

- Cat 1, 3, 4, 5, 7, 8, 10, 11, 12: PASS
- Cat 2 (tenant isolation): WARN — super-admin global read pattern undocumented
- Cat 6 (async consistency): WARN — async audit helper bypassed by sync admin modules
- Cat 9 (security): WARN — magic link not audited; bcrypt error handling improvable

3 WARNs + 0 FAILs in business categories. Per Verdict Math:
- ✅ No FAIL in 1/2/8/9/12 (Cat 9 WARNs are not blockers)
- ✅ No `/test-backend` gate FAIL (gate-runner mislabeled anti-dup, re-verified PASS)
- ✅ Allowlist movement explained
- ✅ Skills consulted listed in IMPL-LOG (backend-expert + tessl__fastapi + tessl__pytest-api-testing + tessl__graceful-degradation present)
- ⚠️  Three Cat WARNs → **overall WARN**

**Verdict: WARN (CHANGES_REQUESTED — minor)**

Recommended path: merge after addressing magic_link audit gap (highest-value HIPAA-lite WARN) + adding super-admin docstring to admin module (cheap clarity). The async/sync audit helper duplication can be deferred to a follow-up cleanup ticket. Bcrypt diagnostics improvement is defense-in-depth (defer).

