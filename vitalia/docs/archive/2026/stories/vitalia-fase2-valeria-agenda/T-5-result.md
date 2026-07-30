---
ticket: T-5
story: vitalia-fase2-valeria-agenda
brand: vitalia
builder: claude-sonnet-4-6
date: 2026-05-26
state: tests-passing
---

# T-5 Result — BE charge orchestrator saga + port impls + stubs (service-blocker Option A)

## Skills Consulted

| Skill | Decision |
|---|---|
| `backend-expert` | No legacy patterns; structlog-only; tenant+clinic dual filter applied |
| `backend-ddd` | Application-layer service, zero framework imports, domain exceptions via import |
| `tenant-isolation` | Dual filter `tenant_id + clinic_id` per HIPAA-lite rule on all repo calls |
| `hipaa-lite` (vitalia) | Audit write sync before response; no PHI in log payloads (UUIDs only) |
| `anti-duplication` | Grep confirmed no `ChargeOrchestrator` in core or other brands |
| `tdd-mandatory` | RED (ModuleNotFoundError) confirmed before implementation; GREEN 7/7 post |
| `currency-handling` | `ChargeRequest.currency: str` required, no default; verbatim ISO 4217 passthrough |
| `tessl__fastapi` | Pure application service; DI via constructor; router T-7 will inject |
| `tessl__pytest-api-testing` | AsyncMock fixtures; no DB calls; constructor DI pattern |

## Deliverables

| File | Status |
|---|---|
| `scheduling/application/services/charge_orchestrator.py` | Created |
| `payments/application/payment_charge_port_impl.py` | Created |
| `payments/application/stubs/__init__.py` | Created |
| `payments/application/stubs/stub_payment_charge_port.py` | Created (DEPRECATED) |
| `fiscal/application/fiscal_emit_port_impl.py` | Created |
| `fiscal/application/stubs/__init__.py` | Created |
| `fiscal/application/stubs/stub_fiscal_emit_port.py` | Created (DEPRECATED) |
| `tests/modules/vitalia/scheduling/test_charge_orchestrator.py` | Created (7 tests) |

## Acceptance Criteria Coverage

| AC | Description | Test | Result |
|---|---|---|---|
| A1 | Saga happy path (charge + fiscal emit + 2 audit rows) | `test_happy_path_pe_boleta` | PASS |
| A2 | Payment 503 → charge_failed audit + no fiscal + no payment row | `test_payment_adapter_503` | PASS |
| A3 | Fiscal 503 post-charge → charge persisted + compensation | `test_fiscal_503_post_charge` | PASS |
| A4 | Concurrent charge → BalanceAlreadyChargedError → 409 | `test_concurrent_charge_optimistic_lock` | PASS |
| A5 | Idempotency key → return prior response | `test_idempotency_key_returns_prior_response` | PASS |
| Bonus | FiscalEmitError compensation (distinct from 503) | `test_fiscal_emit_error_post_charge_uses_compensation` | PASS |
| Bonus | emit_invoice=False skips fiscal emit entirely | `test_no_invoice_requested_skips_fiscal_emit` | PASS |

## G5 Pre-Commit Smoke Gate

| Gate | Result |
|---|---|
| `ruff check` | PASS (0 errors) |
| `ruff format --check` | PASS (0 files to reformat) |
| `pytest test_charge_orchestrator.py -v` | PASS 7/7 |
| `pytest tests/architecture/ -x -q` | PASS 270 passed (no regression) |

## Commit SHA

<!-- populated after commit -->

## R24 / CONTEXT-BRIEF.md Note

`Validator pass: _pending_` (CONTEXT-BRIEF.md pre-validator). §11 states `Faithfulness flag pre-validator: PARTIAL` (not `blocking`). Proceeded per R24 exception path. All content cross-verified against 03-arch.md §7.2 and 06-tickets.yaml T-5 directly.

## Option A Service-Blocker Note

Both stubs are annotated `# DEPRECATED: replace when vitalia-{X} state=done`:
- `StubPaymentChargePort` → replace when `vitalia-payment-adapter-mvp` state=done
- `StubFiscalEmitPort` → replace when `vitalia-fiscal-emission-pe` state=done

The `PaymentChargePortImpl` and `FiscalEmitPortImpl` are the real selectors (already route by gateway/country) but raise `*AdapterUnavailableError` until the service-blocker stories ship their adapters.
