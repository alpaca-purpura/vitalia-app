# T-7 Result — charge_router + emit_router

**Story:** vitalia-fase2-valeria-agenda
**Ticket:** T-7
**Date:** 2026-05-26
**Branch:** wip/vitalia
**Status:** tests-passing

## Deliverables

### Production Code

| Path | Description |
|---|---|
| `vitalia/backend/src/modules/vitalia/payments/api/charge_router.py` | POST /api/v1/payments/charge — CobrarSaldo saga endpoint |
| `vitalia/backend/src/modules/vitalia/payments/api/dtos/charge_dtos.py` | ChargeRequestDTO + ChargeResponseDTO + ChargeConflict409DTO + PaymentAdapter503DTO |
| `vitalia/backend/src/modules/vitalia/fiscal/api/emit_router.py` | POST /api/v1/fiscal/emit — standalone fiscal retry (saga compensation A6) |
| `vitalia/backend/src/modules/vitalia/fiscal/api/dtos/emit_dtos.py` | FiscalEmitRequestDTO + FiscalDocResponseDTO + FiscalEmit503DTO |
| `vitalia/backend/src/main.py` | Registered charge_router at /api/v1/payments + emit_router at /api/v1/fiscal |

### Test Code

| Path | Tests | Coverage |
|---|---|---|
| `vitalia/backend/tests/modules/vitalia/payments/test_charge_router.py` | 16 tests | A1-A5 acceptance criteria, RBAC, 409, 503, idempotency, currency override |
| `vitalia/backend/tests/modules/vitalia/fiscal/test_emit_router.py` | 7 tests | happy path, audit log, 503, 404, 403, idempotency replay, header validation |

## Acceptance Criteria Mapping

| AC | Test | Status |
|---|---|---|
| A1: POST /charge → 200 + ChargeResponseDTO | `test_happy_path_pe_boleta` | PASS |
| A2: Payment 503 → HTTP 503 (no fiscal) | `test_payment_503_returns_503_no_fiscal` | PASS |
| A3: Fiscal fail post-charge → 200 + status='failed' | `test_fiscal_503_post_charge_returns_200_retry` | PASS |
| A4: Concurrent charge → 409 + error_code | `test_concurrent_charge_optimistic_lock_returns_409` | PASS |
| A5: Same idempotency key → prior response | `test_idempotency_returns_prior_response` | PASS |
| Q14: Currency override per-transaction | `test_happy_path_currency_override` | PASS |
| HIPAA: PHI roles enforced (403 for marketing) | `test_require_phi_access_enforced` | PASS |
| HIPAA: Dual filter tenant+clinic passed through | `test_audit_log_per_branch` | PASS |
| Saga retry: standalone emit → 200 emitted | `test_standalone_emit_after_charge_succeeded` | PASS |
| Audit: invoice_emitted written sync | `test_audit_log_invoice_emitted` | PASS |

## Gate Summary

| Gate | Result |
|---|---|
| ruff check | PASS (0 errors) |
| ruff format --check | PASS |
| pytest T-7 (23 tests) | 23/23 PASS |
| Architecture fitness (270 tests) | 270/270 PASS |
| Pre-existing failures | CRM/copilot/e2e/unit — confirmed pre-existing (verified via git stash) |

## Key Design Decisions

1. **JSONResponse for 409/503**: Avoids FastAPI wrapping error body in `{"detail": {...}}` — body is flat and matches DTO fields.
2. **Minimal test app pattern**: No `from src.main import app` at module level — creates isolated FastAPI app with router only, avoiding Settings env var validation.
3. **_get_emit_deps exports tuple**: `(FiscalDocumentRepository, FiscalEmitPort)` tuple dependency — tests override entire factory.
4. **Service-blocker unblocked**: Both `PaymentChargePortImpl` and `FiscalEmitPortImpl` route direct charges or raise unavailable errors respectively. Tests mock the orchestrator/port directly.

## Dependencies

- T-4 (PaymentChargePort, FiscalEmitPort, stubs): DONE ✓
- T-5 (ChargeOrchestrator saga): DONE ✓
