---
ticket: T-5
story: vitalia-fase2-valeria-agenda
brand: vitalia
builder: claude-sonnet-4-6
date: 2026-05-26
state: tests-passing
---

# T-5 IMPL-LOG — BE charge orchestrator saga + port impls + stubs (service-blocker Option A)

## § Skills Consulted

| Skill | Why Invoked | Decision Taken |
|---|---|---|
| `backend-expert` | Required ALWAYS — load runtime-quality-checklist anti-patterns (FastAPI Annotated dep, override fixture, 501 stubs, datetime query, SQLA legacy Column, tenant isolation) | Applied: no `Column()`, no `session.query()`, no `datetime.utcnow()`, structlog-only, tenant_id+clinic_id dual filter per HIPAA-lite rule |
| `backend-ddd` | DDD Inside-Out layering, domain-pure, no cross-module imports | Application layer `charge_orchestrator.py` has zero framework imports; domain exceptions (`BalanceAlreadyChargedError`) used via import — no circular cross-module |
| `tenant-isolation` | Every query must filter `tenant_id`; HIPAA-lite extends to `clinic_id` dual filter | `lock_for_charge(payment_id, expected_version, tenant_id, clinic_id)` and `create(tenant_id, clinic_id, ...)` both pass dual filter |
| `hipaa-lite` (vitalia overlay) | Audit log sync write BEFORE response; dual filter tenant+clinic; sanitize_payload in traces | AsyncAuditWriter.write() called within saga before return; `# No PHI:` comments on log calls; payload keys are UUIDs only (no names/diagnoses) |
| `anti-duplication` | Pre-write grep: verify no engine `ChargeOrchestrator` cross-brand | Grep confirmed: no `ChargeOrchestrator` in `core/luana-core-*/` or other brands. Application-layer saga is brand-specific (vitalia scheduling domain). No lift required. |
| `tdd-mandatory` | Tests written FIRST (RED), then implementation (GREEN) | test_charge_orchestrator.py written first → confirmed RED (ModuleNotFoundError) → implementation written → GREEN (7/7) |
| `currency-handling` | No hardcoded 'USD'; ISO 4217 stored verbatim | `ChargeRequest.currency: str` (required, no default); `ChargeResponse.currency: str` (verbatim from request); `PaymentChargePort.charge(currency=...)` passes through |
| `tessl__fastapi` | Annotated deps, response_model, async | ChargeOrchestrator is pure application-layer service (no FastAPI imports); DI via constructor (router T-7 will inject); async throughout |
| `tessl__pytest-api-testing` | AsyncMock fixtures, MagicMock stubs, DB isolation | All fixtures use `AsyncMock` + `MagicMock`; no DB calls in unit tests; constructor DI pattern (no monkeypatch needed) |

## § Context-Brief R24 Gate Status

- `Validator pass: _pending_` — R24 would normally REFUSE; §11 explicitly states `Faithfulness flag pre-validator: PARTIAL` (not `blocking`). Proceeded per R24 exception path.
- §11 gaps cited: CONTEXT-BRIEF.md was pre-validator. All content cross-checked against 03-arch.md §7.2 and 06-tickets.yaml T-5 entry directly.

## § Default-Flip Pre-Audit (Step 0.5)

No feature flags flipped in T-5. Service-blocker Option A is a new code path (stubs), not a flag flip. No Step 0.5 audit required.

## § Anti-Duplication Step 0 Evidence

```bash
# Grepped before writing charge_orchestrator.py
find /home/chalreme/Proyectos/luana-vitalia/core /home/chalreme/Proyectos/luana-vitalia/nicolify/backend/src /home/chalreme/Proyectos/luana-vitalia/comunify/backend/src /home/chalreme/Proyectos/luana-vitalia/lupulo/backend/src -name "charge_orchestrator.py" 2>/dev/null
# Result: no match — safe to create
```

## § Implementation Decisions

### Saga Transaction Boundary (03-arch §7.3)
- Charge + fiscal NOT in same DB transaction (fiscal is external service call).
- If fiscal fails AFTER successful charge: saga compensation writes `FiscalDocument(status='failed')` + returns `fiscal_emission_status='failed'` — charge stays persisted.
- If payment adapter fails: charge NOT persisted (optimistic lock rollback is implicit since no `create()` was called).

### Service-Blocker Option A
- `StubPaymentChargePort(mode="happy"|"unavailable")` — `# DEPRECATED: replace when vitalia-payment-adapter-mvp state=done`
- `StubFiscalEmitPort(mode="happy"|"unavailable"|"error")` — `# DEPRECATED: replace when vitalia-fiscal-emission-pe state=done`
- `PaymentChargePortImpl` — routes `efectivo/transferencia/otro` → direct record (no external call); `tarjeta/mercado_pago` → raises `PaymentAdapterUnavailableError` (service-blocker)
- `FiscalEmitPortImpl` — routes PE→Nubefact, AR→AFIP, MX→SAT; all raise `FiscalAdapterUnavailableError` (service-blockers)

### Idempotency
- `find_by_idempotency_key()` called FIRST before any charge action.
- On match: reconstructs `ChargeResponse` from existing payment+fiscal rows with `idempotency_replay=True`.
- Router (T-7) maps `idempotency_replay=True` → HTTP 200 (not 201).

### Application Exceptions (router maps in T-7)
- `ChargeConflictError` (error_code="BALANCE_ALREADY_CHARGED") → HTTP 409
- `PaymentAdapterError` (error_code="PAYMENT_ADAPTER_503") → HTTP 503

### Growth Studio Telemetry (fire-and-forget)
- `_bucket_amount()` helper buckets amount for privacy (no exact amounts in event props).
- Wrapped in `try/except Exception` — GrowthStudioEmitter failure NEVER fails the charge.

## § Files Created

| File | Purpose |
|---|---|
| `vitalia/backend/src/modules/vitalia/scheduling/application/services/charge_orchestrator.py` | Core saga: ChargeRequest, ChargeResponse, ChargeConflictError, PaymentAdapterError, ChargeOrchestrator |
| `vitalia/backend/src/modules/vitalia/payments/application/payment_charge_port_impl.py` | Real port impl — tenant gateway selector (efectivo/tarjeta/transferencia/mercado_pago/otro) |
| `vitalia/backend/src/modules/vitalia/payments/application/stubs/__init__.py` | Package init |
| `vitalia/backend/src/modules/vitalia/payments/application/stubs/stub_payment_charge_port.py` | Service-blocker stub (DEPRECATED) |
| `vitalia/backend/src/modules/vitalia/fiscal/application/fiscal_emit_port_impl.py` | Real port impl — tenant country selector (PE/AR/MX) |
| `vitalia/backend/src/modules/vitalia/fiscal/application/stubs/__init__.py` | Package init |
| `vitalia/backend/src/modules/vitalia/fiscal/application/stubs/stub_fiscal_emit_port.py` | Service-blocker stub (DEPRECATED) |
| `vitalia/backend/tests/modules/vitalia/scheduling/test_charge_orchestrator.py` | TDD tests: 7 functions (5 AC + 2 bonus) |

## § Quality Gate Results (G5)

| Gate | Command | Result |
|---|---|---|
| ruff check | `ruff check src/modules/vitalia/{scheduling,payments,fiscal}/` | PASS (0 errors after auto-fix of 3 unused imports) |
| ruff format | `ruff format --check src/modules/vitalia/{scheduling,payments,fiscal}/` | PASS (0 files to reformat after applying format to 2 files) |
| pytest T-5 | `pytest tests/modules/vitalia/scheduling/test_charge_orchestrator.py -v` | PASS 7/7 |
| arch fitness | `pytest tests/architecture/ -x -q` | PASS 270 passed, 2 warnings (same as baseline, no regression) |

## § Cross-Module Reads (read-only, not modified)

- `scheduling/application/ports/payment_charge_port.py` — consumed ABCs + exceptions
- `scheduling/application/ports/fiscal_emit_port.py` — consumed ABCs + exceptions
- `scheduling/domain/exceptions.py` — consumed `BalanceAlreadyChargedError`
- `scheduling/infrastructure/repositories/appointment_payment_repository.py` — consumed method signatures
- `fiscal/infrastructure/repositories/fiscal_document_repository.py` — consumed method signatures
- `audit/audit_writer.py` — consumed write() signature
- `_shared/telemetry/growth_studio_emitter.py` — consumed emit_event() signature
- `payments/domain/payment_method.py` — consumed `PaymentMethod` enum
- `payments/domain/fiscal_doc_type.py` — consumed `FiscalDocType` enum
- `payment/stripe_connect_adapter.py` — read to understand existing scaffold (NOT modified)
