<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Backend Code Review: arreglar-guardado-voz-y-tono (bugfix · 4 root causes)

**Date:** 2026-05-30
**Brand:** vitalia (HIPAA-lite)
**Story / cap:** `arreglar-guardado-voz-y-tono` · cap `brand_studio.lisa-marca` · `cap_change_type: fix` · type `bugfix` (ADR-011 lite)
**Tickets reviewed (BE):** T-1 (38aa5c8b) · T-1.bis (a0060e7a) · T-2 (98a903a5) · T-2.bis (81b13787)
**Files reviewed:** 4 src + 2 new test files
**Domains touched:** audit · brand_studio · _shared/telemetry · compliance (consumed)
**Skills consulted (by me):** backend-expert, brand-expert, offer-expert(n/a), metrics-expert(n/a), tessl__fastapi, tessl__pytest-api-testing
**Verdict:** **APPROVED**

## /test-backend Gate Status (verified independently — no gate-output.json present, ran targeted gates)

| # | Gate | Result | Detail |
|---|---|---|---|
| 3 | Lint (ruff check) | PASS | 4 changed files — "All checks passed!" |
| 4 | Format (ruff format) | PASS | 4 files already formatted |
| 6 | Arch fitness | PASS | full `tests/architecture/` suite green (warnings = pre-existing unknown marks) |
| 7 | Unit tests (new) | PASS | new suites: 34 passed, 8 skipped (Postgres-gated HTTP tests) |
| 7 | Unit tests (module) | PASS | brand_studio + audit: 145 passed, 73 skipped, 0 failed |
| 8/9/10 | Postgres-bound (verify/integration/migration) | SKIP | no Postgres in env — orchestrator verified persistence LIVE (curl PATCH→GET round-trip) + E2E real-backend green. No migration in this bugfix. |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | 0 |
| 2 | Tenant Isolation | PASS | 0 |
| 3 | Soft Deletes | PASS (N/A) | 0 |
| 4 | Code Quality | PASS | 0 |
| 5 | SQLAlchemy 2.0 | PASS | 0 |
| 6 | Async Consistency | PASS | 0 |
| 7 | Pydantic v2 / PII | PASS | 0 |
| 8 | Migration Quality | PASS (N/A) | 0 — no migration |
| 9 | Security / PHI | PASS | 0 (fix RESTORES dead PHI redaction) |
| 10 | Tests / TDD | PASS | 0 |
| 11 | Cross-cutting | PASS | 0 |
| 12 | Mirror / anti-dup | PASS | 0 — consumes engine via brand-local wrapper |
| 13 | Connectivity (anti-isla) | PASS | 0 — no new public symbol; all repair sites have real consumers |

## Cross-scope flags
None. No `core/luana-core-*` edits. No cross-brand paths. No copilot/sales_agent files in diff. Fix correctly consumes engine `sanitize_payload` via the brand-local `sanitize_phi_payload` wrapper (does NOT edit engine).

## Downstream regression scope

| Surface modified | Downstream test targets | status |
|---|---|---|
| `audit/audit_writer.py` (sanitize repoint + CAST uuid) | `tests/modules/vitalia/audit/` | PASS (145 passed module-wide; Postgres HTTP paths skip — covered by orchestrator live curl + E2E) |
| `_shared/telemetry/growth_studio_emitter.py` (CAST jsonb) | charge_router · appointment_status_service (consumers — `emit_event` signature UNCHANGED) | PASS — no signature break; consumers already pass `tenant_id` |
| `brand_studio/api/dtos/marca_dtos.py` (camel alias on 2 personality DTOs) | `test_marca_router_personality.py` (Postgres-gated, skips here) · `MarcaInitialStateDTO` (embeds BrandPersonalityDTO) | PASS (no failures; nested camel serialization is the intended FE contract — other nested DTOs untouched) |
| `brand_studio/.../marca_service.py` (_emit_telemetry async+tenant_id) | private to marca_service (6 internal callers) | PASS (145 module green) |

## Findings

### Fix correctness verification

**BE-1 (sanitize repoint).** `sanitize_phi_payload(payload)` is the correct target: it calls engine `sanitize_payload(payload)` (current signature, no `compliance_level`) THEN applies the 22 canonical PHI fields (top-level + nested `patient.*`). The dead-kwarg call never redacted → the fix simultaneously kills the HTTP 500 AND restores PHI redaction (a silent HIPAA-lite hole). Verified by `test_phi_redacted_top_level_fields` / nested-patient tests using the REAL wrapper. **Import cycle: VERIFIED CLEAN** — `compliance/` does NOT import `audit/` (grep confirms zero matches), so `audit → compliance` is one-directional; additionally the imports are function-local (`noqa: PLC0415`), a second safety layer. Docstrings updated to reflect the wrapper.

**BE-1.bis (`:x::uuid` → `CAST(:x AS uuid)` and `:props::jsonb` → `CAST(:props AS jsonb)`).** Semantically EXACT: same Postgres cast, function-call form avoids collision with SQLAlchemy `text()` `:param` bindparam tokenizer (`::` after a bindparam name was mis-parsed → asyncpg syntax error). Note: in `growth_studio_emitter` the `tenant_id/clinic_id/user_id` are passed as plain strings WITHOUT `CAST(... AS uuid)` — this is **pre-existing** behavior (the only `::` there was `:props::jsonb`), not a regression introduced by this fix; Postgres infers the column cast positionally and the LIVE E2E confirms inserts succeed.

**BE-2 (camelCase alias on `BrandPersonalityDTO` + `BrandPersonalityPatchDTO`).** `populate_by_name=True` + `alias_generator=to_camel` accepts both camel (FE) and snake (internal/tests); `extra="forbid"` STILL blocks genuinely-unknown fields — verified by `test_genuinely_extra_field_rejected` (`bogusField` → still rejected). Response emits camelCase (`by_alias=True` default). **GET response shape for other consumers preserved**: scope is surgically the 2 personality DTOs only; `BrandIdentityDTO`/`BrandVisualsDTO`/`BrandContactDTO` keep snake_case. `MarcaInitialStateDTO` embeds `BrandPersonalityDTO` → its nested `personality` block now serializes camelCase (the intended FE SSR-hydration contract), outer fields stay snake_case. No regression.

**BE-2.bis (`_emit_telemetry` async + tenant_id).** Root cause real: old `def _emit_telemetry(self, event_type, **props)` called an async `emit_event` without `await` (coroutine never executed = telemetry silently lost) AND omitted the required `tenant_id` kwarg. Fix makes it `async`, forwards `tenant_id` (required) + `user_id`, and the diff confirms all 6 internal call sites converted to `await`. Verified RED→GREEN by `TestEmitTelemetryTenantId`.

### Stake-asymmetric categories (HIPAA-lite — escalation-eligible, all PASS)
- **Tenant isolation:** every audit write passes `tenant_id` + `clinic_id` (dual filter); `_NULL_CLINIC_ID = UUID(int=0)` is the documented owner-config sentinel (brand config is not patient-PHI scoped). `patch_personality` UPDATE filters `tenant_id`. PASS.
- **PHI sanitization:** RESTORED (was dead). No PHI in audit payloads (only `fields_updated`/`archetype` metadata — verbatim voice text NOT logged). PASS.
- **Audit-log sync write:** preserved — `await self._audit.write(...)` BEFORE return in `patch_personality`. PASS.
No escalation required: these are repairs that strengthen the HIPAA-lite posture, not new stake-asymmetric surface.

## Contract Compliance
- [x] DTOs match arch (2 personality DTOs aliased, others untouched — as specified in 03-arch § BE-2)
- [x] Routes keep `response_model=` (`MarcaInitialStateDTO`, `BrandPersonalityDTO` ×2)
- [x] TDD RED-first: T-1/T-1.bis/T-2/T-2.bis each cite RED reproducing the bug before GREEN (IMPL-LOG + test docstrings)
- [x] Integration design (CONN): no new symbol; 3 repaired call sites have real consumers (all brand_studio PATCH + trust-signals + CRM + telemetry). No isla.
- [x] Skills Consulted populated (backend-expert + tessl__pytest-api-testing + tessl__fastapi + tdd-mandatory + brand-expert)

## Allowlist Movement
No arch-fitness allowlist grew (full suite green, no ratchet change). No new CVE surface (no deps changed).

## Native-First Audit
- [x] No `docker exec ... ruff|pytest` in commits (I ran native `.venv/bin`)
- [x] No `git add .`/`-A`/`-u` evidence; scoped commits by pathspec
- [x] Conventional Commits (`fix(vitalia/...): ...`)

## Self-fix log
None. No findings required a fix — all 4 fixes correct as-shipped.

## Deferred finding (agree with deferral)
`GET /prohibited-phrases` requires `X-User-ID` the FE doesn't send → 422. OUT OF SCOPE here; correctly tracked in follow-up story `estabilizar-harness-e2e-lisa-marca`. **I agree it is correctly deferred** — it is a separate FE↔BE header contract issue, not part of the voz-y-tono save path, and does not block this bugfix.

## Verdict Math
- 0 FAIL in categories 1/2/8/9/12 · 0 gate FAIL (3-7,11-13 all PASS/N-A) · 0 allowlist growth · downstream scope PASS · Skills Consulted populated · 0 WARN.
- **→ APPROVED.**

> Note: the only verification not runnable in this env is the Postgres-bound HTTP/persistence path (8+73 skips). The orchestrator verified it LIVE (curl PATCH→GET round-trip → 200 + audit row + telemetry) and the E2E real-backend suite is green — consistent with `test-design-doctrine § Verificación REAL ≠ HTTP 200`. I confirm the code-path correctness independently above.
