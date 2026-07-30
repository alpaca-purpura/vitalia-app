# T-9 Result — BE Arch Tests NEW

**Ticket:** T-9  
**Story:** vitalia-fase2-valeria-agenda  
**Branch:** wip/vitalia  
**Status:** tests-passing

## Summary

3 new architectural fitness test files implemented for vitalia F2-S1. All 27 new tests pass. Full arch suite: 297/297 GREEN (up from 270 before T-9).

## Deliverables

### 1. `test_scheduling_module_ddd.py`
**Path:** `vitalia/backend/tests/architecture/test_scheduling_module_ddd.py`  
**Tests:** 8  
**Coverage:** DDD Inside-Out purity for scheduling/payments/fiscal modules.

Key decisions:
- `API_DOMAIN_IMPORT_ALLOWED_SUBMODULES` allows api/ to import `domain/exceptions` and `domain/enums` — these are legitimate thin-router patterns (exception mapping, DTO type annotations). Fixed via full-line scanning (not match group substring) to correctly detect `domain.exceptions` path.
- `known_cross_module` ratchet: `payments/api/charge_router.py` imports `FiscalEmitPortImpl` from fiscal — legitimate composition-root DI wiring for the charge saga (documented in 03-arch § 6.1).
- `KNOWN_DOMAIN_PYDANTIC_FILES`: empty (F2-S1 domain entities use `@dataclass(frozen=True)` exclusively).
- `KNOWN_INFRA_FORWARD_IMPORTS`: empty (no infra→api/services violations).
- `KNOWN_API_DIRECT_DOMAIN_IMPORTS`: empty (exceptions + enums allowed via submodule pattern).

### 2. `test_no_phi_in_url_params.py`
**Path:** `vitalia/backend/tests/architecture/test_no_phi_in_url_params.py`  
**Tests:** 7  
**Coverage:** HIPAA-lite PHI-free URL enforcement.

Key decisions:
- `PHI_URL_PARAM_NAMES`: 24 patterns covering identity + clinical + imaging PHI fields.
- `APPROVED_SCHEDULING_QUERY_PARAMS`: frozenset of 8 safe query params (`view`, `date`, `preset_filter`, `filters`, `page`, `page_size`, `status`, `month`).
- Dual scan: AST (`_extract_query_param_names_ast` via `ast.parse`) + grep (`_grep_phi_pattern_in_source`).
- `KNOWN_PHI_QUERY_PARAMS_VIOLATIONS`: empty (new modules start clean).
- Verifies `ALLOWED_GRID_PARAMS` whitelist defined in `agenda_router.py` and confirms it matches approved set.
- Payments/fiscal POST-only verified (no query params possible).

### 3. `test_audit_log_row_per_phi_endpoint.py`
**Path:** `vitalia/backend/tests/architecture/test_audit_log_row_per_phi_endpoint.py`  
**Tests:** 12  
**Coverage:** Audit log row presence per PHI endpoint.

Key decisions:
- `PHI_ENDPOINT_REGISTRY`: 7 known PHI endpoints with router + service paths. NamedTuple `PhiEndpointEntry`.
- `AUDIT_WRITE_PATTERNS`: 6 patterns detect `await audit_writer.write(`, `await audit.write(`, `await self._audit.write(`, sync helper, `AsyncAuditWriter().write(`.
- `KNOWN_NON_PHI_RBAC_ENDPOINTS`: frozenset containing `get_agenda_aggregates` — this endpoint checks `ALLOWED_PHI_ROLES` for access control but returns only integer aggregate counts per day (explicitly documented "PHI-free" in router docstring). No audit required per hipaa-lite.md (no PHI exposure). Added to ratchet to allow RBAC gate without audit log.
- Ratchet test `test_no_new_phi_router_without_audit` scans all `*_router.py` in scheduling/payments/fiscal for RBAC-gated functions not in registry; fails if found without audit write.

## G5 Pre-Commit Smoke Gate Results

| Gate | Result |
|---|---|
| `ruff check` (3 files) | PASS (0 errors) |
| `ruff format --check` (3 files) | PASS (0 files to reformat) |
| `pytest` (3 new files, 27 tests) | PASS (27/27) |
| `pytest tests/architecture/` (full suite) | PASS (297/297, no regression) |

## Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `backend-expert` | Runtime quality checklist — anti-patterns FastAPI/SQLA/tests | Ratchet pattern (KNOWN_* frozensets), `from __future__ import annotations`, `downstream-regression-na` magic comment |
| `tessl__pytest-api-testing` | Test structure: fixture scoping, parametrize, assertions | AST-based scanning over grep-only; `_python_files_in` helper to exclude `__pycache__` |
| `backend-ddd` | DDD boundaries for scheduling/payments/fiscal | api/ may import domain/exceptions (thin router pattern); composition-root DI is the ONLY cross-module exception |

## Fixes Applied During Gate

1. **F401 unused import** — removed `import ast` from `test_scheduling_module_ddd.py` (was added in draft, not used).
2. **E501 line-too-long** — split long line in `test_audit_log_row_per_phi_endpoint.py` (line 193: end_lineno extraction) and `test_scheduling_module_ddd.py` (is_allowed check).
3. **DDD test bug** — `API_DOMAIN_IMPORT_ALLOWED_SUBMODULES` check was incorrectly applied to `m.group(0)` (which stops at `domain` word boundary) rather than the full import line. Fixed to scan the complete source line at match position.
4. **Ratchet missing entry** — `get_agenda_aggregates` uses `ALLOWED_PHI_ROLES` check but is PHI-free. Added to `KNOWN_NON_PHI_RBAC_ENDPOINTS` with justification.
5. **Cross-module ratchet** — `payments/api/charge_router.py` legitimately imports `FiscalEmitPortImpl` (composition-root DI wiring). Added to `known_cross_module` frozenset with arch justification.

## Acceptance Criteria Status

| AC | Status |
|---|---|
| A1: `test_scheduling_module_ddd.py` exists + GREEN | PASS |
| A2: `test_no_phi_in_url_params.py` exists + GREEN | PASS |
| A3: `test_audit_log_row_per_phi_endpoint.py` exists + GREEN | PASS |
| No regression on existing arch tests (270+) | PASS (297 total, 0 failures) |

## Cross-module reads (read-only)

- `vitalia/backend/src/modules/vitalia/scheduling/api/agenda_router.py` — ALLOWED_GRID_PARAMS, ALLOWED_PHI_ROLES, audit_writer patterns
- `vitalia/backend/src/modules/vitalia/payments/api/charge_router.py` — FiscalEmitPortImpl DI wiring
- `vitalia/backend/src/modules/vitalia/fiscal/api/emit_router.py` — inline audit.write() pattern
- `vitalia/backend/src/modules/vitalia/scheduling/api/notify_router.py` — domain.exceptions import pattern
- `vitalia/backend/src/modules/vitalia/audit/audit_writer.py` — AsyncAuditWriter API surface
