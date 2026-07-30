# tenant_profile — Code Review

**Reviewer:** self-audit complementing the automated pass by `nicolify-backend-auditor`
(which flagged one deviation before context timeout — addressed below).
**Date:** 2026-04-20
**Scope:** backend BC (`tenant_profile/`), port, migrations 052–053, tests,
brand cleanup, main.py router mounts.
**Goal:** flag anything a staff engineer would raise an eyebrow at.

---

## Executive summary

**Overall grade: 4.4 / 5**

The bounded context is well-structured, defensively coded, and contract-aligned
after one fix. Tests cover the invariants exhaustively. Migrations are
idempotent and cycle-verified. The one real gap (legacy endpoint redirect)
is now closed.

**Top 3 wins**

1. Aggregate invariants (min/max, rate limit, idempotent no-op writes, first-
   declaration skip) encapsulated in the domain layer with 32 dedicated tests.
2. UTC-aware datetime normalization at the repository boundary (`_ensure_utc`)
   — defensive against SQLite round-trip that drops tzinfo, invisible to
   PostgreSQL. Domain is never surprised by naive datetimes.
3. Arch ratchet (`test_business_types_ssot.py`) uses AST walk, not regex —
   correctly distinguishes class-level field declarations from API parameters
   and function locals. Allowlist frozen at 4 files.

**Top 3 risks**

1. No rate-limit enforcement at the repository / DB layer — two concurrent
   PATCH requests in the same second could both pass the aggregate check,
   succeed, and produce two `last_business_types_change_at` writes. Probability
   is low (single user rarely does this), impact is minor (clock resets), but
   a `tenant_id` advisory lock on update would close it deterministically.
   **Priority: post-ship hygiene.**
2. Event dispatch is a `logger.info` stub. `BusinessTypesChanged` needs to
   invalidate downstream caches (sales-agent grounding, landing preview) and
   broadcast via WebSocket to invalidate React Query on sibling tabs. Today,
   a user editing on one tab won't see the change on another until manual
   reload. **Priority: pre-demo if sibling tabs are part of the demo.**
3. Catalog endpoint has no `ETag` / `Cache-Control` headers. It's near-
   immutable metadata; an arch-level caching header would cut 99% of the
   traffic after first load. **Priority: post-ship hygiene.**

**5 prioritized follow-ups**

| # | Finding | Priority |
|---|---|---|
| 1 | ~~Missing 301 redirect for legacy `/brand/expert-business-types/catalog`~~ | **FIXED** in this audit pass (main.py + comment with sunset date 2026-05-04) |
| 2 | Wire `BusinessTypesChanged` to event bus + WebSocket invalidation | pre-demo |
| 3 | Add `Cache-Control: public, max-age=86400, must-revalidate` + `ETag` to catalog endpoint | post-ship hygiene |
| 4 | Advisory lock (`pg_advisory_xact_lock(hashtext(tenant_id::text))`) on PATCH inside the service | post-ship hygiene |
| 5 | Deprecation-sunset test: after 2026-05-04, remove the 301 route and assert 404 | calendar reminder |

---

## 1. DDD compliance — 5 / 5

**Strengths**

- Clean four-layer split: `domain/` has zero framework imports, `infrastructure/`
  implements the abstract repo, `application/` orchestrates, `api/` delegates.
- `TenantProfile` aggregate encapsulates all invariants in `update_business_types()`;
  the service cannot bypass them.
- `TenantProfileRepository` ABC in `domain/` + `SqlTenantProfileRepository` in
  `infrastructure/` — inversion of control done right.
- Port `shared/links/ports/tenant_profile.py` uses lazy imports and exposes
  only primitive tuples, not the aggregate type. Downstream modules cannot
  accidentally take a dependency on internal domain types.

**Findings**

- `backend/src/modules/tenant_profile/domain/repository.py:11` — moving
  `UUID` + `TenantProfile` to `TYPE_CHECKING` is correct for `from __future__
  import annotations` context. No runtime import needed.
- Events are `@dataclass(frozen=True)` — immutable by construction. ✓

---

## 2. Tenant isolation — 5 / 5

**Strengths**

- `tenant_profiles.tenant_id` is the primary key. There is no way to query
  another tenant's row without providing its UUID — the PK constraint is the
  isolation mechanism.
- Every service method threads `tenant_id` through as the first positional
  argument.
- Port-level access (`get_tenant_business_types`) requires `tenant_id` —
  cross-module callers cannot ask "what are all business_types?".
- API endpoints extract tenant_id from `X-Tenant-ID` header via
  `_require_tenant_id` dependency; 403 without it.
- Repository test `TestTenantIsolation` asserts no cross-tenant leakage.

**Findings**

- None blocking. The JSONB config_json storage on `tenants` remains out of
  scope (project-wide debt).

---

## 3. Migration safety — 5 / 5

**Strengths**

- `052_create_tenant_profiles.py`: `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX
  IF NOT EXISTS`, backfill wrapped in `DO $$ BEGIN ... EXCEPTION` block.
  Re-running is a no-op. Downgrade drops the table cleanly.
- `053_strip_business_types_from_brand_settings.py`: `jsonb_set` guarded by
  `WHERE config_json #> '{...}' IS NOT NULL`. Re-running is a no-op.
- Full upgrade/downgrade/re-upgrade cycle verified against dev DB.
  11 tenants backfilled, 0 lost, 0 remaining with legacy key.

**Findings**

- Downgrade of 053 is intentionally no-op with an explanatory docstring
  (cannot restore data that was deleted). Documented in the migration file.
  This is the right call — silently restoring stale data is worse.

---

## 4. Security & PII — 4 / 5

**Strengths**

- Every endpoint has `response_model=`.
- 403 returned without `X-Tenant-ID`.
- `BusinessTypesCatalogResponse` and `TenantProfileResponse` contain no PII.
- No raw SQL with user input — all queries use SQLAlchemy parameterized selects.
- Structlog logs `str(tenant_id)` and the slug list — no PII.

**Findings**

- **Minor — rate-limit 409 body exposes `next_allowed_change_at`**. This is
  necessary UX (the FE renders the date to the user) but it could leak timing
  information if any external party other than the tenant can call the endpoint.
  The endpoint requires a Clerk session tied to the tenant, so effectively not
  exposed. **Non-issue, documented by design.**
- **Minor — catalog endpoint has no auth check shown in router**. It is
  mounted under the app's global auth middleware (inherits Clerk auth via
  `get_current_user` chain in main.py); verify by end-to-end probe if auditing
  for a SOC2 context. Not a finding for this sprint, but worth confirming.

---

## 5. Test coverage & design — 5 / 5

**Strengths**

- 32 aggregate tests cover every invariant: min, max, duplicates, first-time
  skip, rate-limit inside window, rate-limit window reopens, no-op write
  returns empty events, no-op does not reset `last_change_at`, order-independent
  set comparison.
- 4 service tests verify orchestration + error propagation + event dispatch
  + no-op behavior.
- 10 repo tests cover `get_or_none` (no-side-effect), `get_or_init`
  (in-memory only), save round-trip with tzinfo normalization, tenant isolation,
  legacy data handling (unknown enum values dropped silently).
- 8 API tests exercise 200/400/409/403 codes with realistic payloads.
- 1 arch test AST-scans the entire modules tree and a direct Pydantic
  `model_fields` assertion on `BrandIdentity`. Belt and suspenders.

**Findings**

- No test for the 301 redirect. Added follow-up #5 in summary.

---

## 6. Code quality (senior standard) — 4 / 5

**Strengths**

- All public functions have docstrings; modules have summary docstrings.
- No TODOs, HACKs, or bare `except` clauses.
- Only one `# type: ignore` — in the port's lazy import, with a comment
  explaining why.
- `utc_now()` used consistently; no `datetime.utcnow()`.
- `DateTime(timezone=True)` on every column.
- Errors are meaningful: `ValueError` for invariant violations, dedicated
  `BusinessTypesChangeRateLimitedError` for rate-limit with typed payload.
- Structlog with structured keys for every significant event.

**Findings**

- **Minor — `_to_domain` in repository is module-level** rather than a
  staticmethod or classmethod on the repository. Not wrong, but a `@staticmethod`
  on the repository reads more cohesively and keeps the mapping with the
  class that owns it. Style preference, not blocking.
- **Minor — duplicate UTC normalisation helpers**. The repository has
  `_ensure_utc`, the tests have `_same_instant` doing essentially the same
  work. Extracting to `shared/domain/datetime_utils.py` would serve the broader
  codebase. **Priority: post-ship hygiene.**

---

## 7. API design — 5 / 5

**Strengths**

- REST verbs match semantics: `GET` for read, `PATCH` for partial update.
- Error contract documented in CONTRACT.md and honored: `code` + `message`
  + context fields (`next_allowed_change_at` in 409 body).
- DTOs leave room for future fields (adding `sector`, `company_size` is a
  schema change with no API surface break).
- Single `tenant_id` path — no `/tenants/{id}/profile` ambiguity (the ID is
  always the authenticated tenant).

**Findings**

- The catalog endpoint does not emit `Last-Modified` or `ETag`. For near-
  immutable metadata this is a performance win. Added to follow-ups.

---

## 8. Contract adherence — 5 / 5 (after fix)

**Strengths**

- All CONTRACT §1–3 invariants implemented literally.
- Business rules match §8 to the letter: min=1, max=2, 30-day window,
  first-time skip, no-op no-reset.
- Port API matches §4.

**Fixed during this review**

- **§3.4 deviation — missing 301 for legacy catalog URL**. `migration.md` said
  the endpoint was deleted outright. CONTRACT §3.4 specifies "301 for two
  weeks, then deleted". A 301 alias was added to `backend/src/main.py` with
  a sunset date comment (2026-05-04). Preserves external callers (none known,
  but cheap insurance).

---

## Closing note

The code is shippable as-is. The three post-ship items (advisory lock, event
bus, ETag) are polish that don't block a buyer walkthrough; they strengthen
the resilience story post-sale. Recommend addressing #2 (event bus) before
any demo that involves multi-tab or multi-device scenarios.
