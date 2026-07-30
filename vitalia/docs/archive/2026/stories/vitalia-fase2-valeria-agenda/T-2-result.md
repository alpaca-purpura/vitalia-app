# T-2 Result — BE scheduling domain (enums + dataclasses)

**Ticket:** T-2  
**Story:** vitalia-fase2-valeria-agenda  
**Brand:** vitalia  
**Surface:** BE domain layer (pure Python, no framework)  
**Estimate:** 2h  
**State:** developed  
**Dependencies:** T-1 DONE (migration committed 635a96d7)  
**Blocks:** T-3, T-4, T-5  

---

## Skills Consulted (must_load enforcement v4.1)

| Skill / Rule | Loaded | Decision taken |
|---|---|---|
| `backend-expert` (SKILL.md + runtime-quality-checklist.md) | YES | DDD Inside-Out domain pure Python. `datetime.utcnow()` forbidden → used `datetime.now(timezone.utc)`. No Pydantic in domain — pure `@dataclass(frozen=True)`. |
| `.claude/rules/backend-ddd.md` | YES | Domain layer zero framework imports. DDD boundary: scheduling domain does NOT import from crm or clinics. |
| `.claude/rules/anti-duplication.md` | YES | Cross-brand grep: zero matches (nicolify/comunify/lupulo have no scheduling/payments/fiscal modules). Engine check: no `agenda_slot.py` or `appointment_origin.py` in `core/luana-core-*/`. |
| `.claude/rules/tdd-mandatory.md` | YES | TDD RED→GREEN: test file written FIRST, ran RED (import errors), then implemented (50 tests GREEN). |
| `.claude/rules/master-data.md` | YES | UTC tz-aware `created_at` default. No `datetime.utcnow()` (forbidden). |
| `.claude/rules/currency-handling.md` | YES | `currency: str` no default. `amount_cents: int` (money as integer cents). Test `test_currency_no_hardcoded_usd_default` verifies no `'USD'` default. |
| `tessl__pytest-api-testing` | YES | Test structure: class-based TDD, `_make_*` factory helpers, import inside test (lazy load pattern), domain purity assertions. |
| `vitalia/.claude/rules/hipaa-lite.md` | YES | `tenant_id + clinic_id` BOTH present in `AgendaSlot`, `AppointmentPayment`, `FiscalDocument`. Domain entities carry dual filter anchors. |
| `.claude/rules/tenant-isolation.md` | YES | Every domain entity includes `tenant_id`. No entity without `tenant_id` field. |

**CONTEXT-BRIEF.md note:** `Validator pass: _pending_` and `Faithfulness flag: _pending_` found. Proceeding per ticket authoritative spec (fully explicit deliverables) and citing R24 gap here. Ticket prompt from orchestrator serves as override (explicit caller instruction). Faithfulness § 11 shows PARTIAL (not blocking).

---

## Deliverables

### Files created

**Scheduling domain (6 files):**

1. `vitalia/backend/src/modules/vitalia/scheduling/__init__.py` — module docstring
2. `vitalia/backend/src/modules/vitalia/scheduling/domain/__init__.py` — domain package
3. `vitalia/backend/src/modules/vitalia/scheduling/domain/agenda_filter.py` — `AgendaPresetFilter` StrEnum (5 values: hoy/por_confirmar_manana/reagendar_pendientes/no_shows_dia/saldos_pendientes)
4. `vitalia/backend/src/modules/vitalia/scheduling/domain/appointment_origin.py` — `AppointmentOrigin` StrEnum (4 values: walk_in/telefono/proactivo_adrian/portal)
5. `vitalia/backend/src/modules/vitalia/scheduling/domain/agenda_view.py` — `AgendaView` StrEnum (3 values: dia/semana/mes, default=semana)
6. `vitalia/backend/src/modules/vitalia/scheduling/domain/slot_payment_status.py` — `SlotPaymentStatus` StrEnum (4 values: pagado/deposito/sin_pago/no_show)
7. `vitalia/backend/src/modules/vitalia/scheduling/domain/agenda_slot.py` — `AgendaSlot` @dataclass(frozen=True) (14 fields)
8. `vitalia/backend/src/modules/vitalia/scheduling/domain/appointment_payment.py` — `AppointmentPayment` @dataclass(frozen=True) (11 fields + created_at default)

**Fiscal domain (3 files):**

9. `vitalia/backend/src/modules/vitalia/fiscal/__init__.py` — module docstring
10. `vitalia/backend/src/modules/vitalia/fiscal/domain/__init__.py` — domain package
11. `vitalia/backend/src/modules/vitalia/fiscal/domain/fiscal_document.py` — `FiscalDocument` @dataclass(frozen=True) (9 fields)

**Payments domain (4 files):**

12. `vitalia/backend/src/modules/vitalia/payments/__init__.py` — module docstring
13. `vitalia/backend/src/modules/vitalia/payments/domain/__init__.py` — domain package
14. `vitalia/backend/src/modules/vitalia/payments/domain/payment_method.py` — `PaymentMethod` StrEnum (5 values: efectivo/tarjeta/transferencia/mercado_pago/otro)
15. `vitalia/backend/src/modules/vitalia/payments/domain/fiscal_doc_type.py` — `FiscalDocType` StrEnum (7 values: boleta/factura/factura_a/factura_b/recibo/cfdi/ticket)

**Infrastructure stubs (empty `__init__.py` for module structure):**

- scheduling/{infrastructure,application,api}/__init__.py
- fiscal/{infrastructure,application,api}/__init__.py
- payments/{application,api}/__init__.py

**Test:**

- `vitalia/backend/tests/modules/vitalia/scheduling/__init__.py`
- `vitalia/backend/tests/modules/vitalia/scheduling/test_agenda_slot_domain.py` — 50 tests

---

## Validator gates output (A1 + A2 + G5)

### A1 — Pytest GREEN

```
cmd: cd vitalia/backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/scheduling/test_agenda_slot_domain.py -v
result: 50 passed in 0.16s
```

### A2 — No cross-module imports (DDD purity)

```
cmd: ! grep -rn 'from src.modules.vitalia.crm\|from src.modules.vitalia.clinics' vitalia/backend/src/modules/vitalia/scheduling/domain/
result: exit 0 (no matches found)
```

### G5 Pre-commit smoke gate

| Gate | Command | Result |
|---|---|---|
| G5-1 ruff check | `ruff check src/…scheduling/domain/ …fiscal/domain/ …payments/domain/ tests/…scheduling/` | ALL PASSED |
| G5-2 ruff format | `ruff format --check …` | 14 files already formatted |
| G5-3 pytest domain | `pytest tests/…/test_agenda_slot_domain.py -v` | 50 passed |
| G5-4 arch tests | `pytest tests/architecture/ -x -q` | 270 passed, 2 warnings (pre-existing) |

---

## Domain design notes

### FiscalDocType — PE/AR/MX coverage confirmed

CONTEXT-BRIEF § 11 flagged: "Verify FiscalDocType enum covers PE/AR/MX territories". Confirmed:
- PE: `boleta`, `factura`
- AR: `factura_a`, `factura_b`, `recibo`
- MX: `cfdi`
- Generic: `ticket`

### AppointmentPayment — `created_at` UTC fix

03-arch § 2.3 showed `datetime.utcnow()` in the domain snippet — this is **forbidden** per `.claude/rules/master-data.md` (no `datetime.utcnow()`). Fixed to `datetime.now(timezone.utc)`.

### AgendaSlot fields — ticket vs 03-arch reconciliation

Ticket prompt specifies `slot_id, appointment_id, tenant_id, clinic_id, patient_name_masked, dni_masked, service, doctor, start_at, end_at, payment_status, origin, balance_amount_cents, currency` — used these exact field names as the ticket is the implementation-spec authority for T-2.

### FiscalDocument — typed UUID fields

Initially implemented with `object` type to avoid UUID imports — corrected to proper `from uuid import UUID` (stdlib only, not SQLAlchemy). Domain purity test confirms no framework imports.

---

## Commit SHA

`4253e076` — pushed to `wip/vitalia`
