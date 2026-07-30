# T-G2F12-BE Result — lisa-servicios sales-brief 500 bugfix

**Ticket:** G2-F12-BE  
**Story:** vitalia-fase2-lisa-servicios  
**Commit:** `cc4a2ea9`  
**Branch:** wip/vitalia  
**Date:** 2026-06-18

---

## Skills consulted

| Skill | Why | Decision |
|---|---|---|
| `backend-expert` | Bugfix workflow: Outside-In trace, regression test first, fix in deepest layer | Confirmed fix scope to `_apply` in application service; import serializers from infrastructure (DDD exception: infra→app serializer use is intentional for round-trip safety, already established by the existing repo pattern) |
| `brand-expert` | N/A — not touching brand studio module | Not invoked |
| `offer-expert` | Ticket touches offer module domain VOs (FaqPair, ObjectionPair) | VOs are frozen dataclasses with `__post_init__` invariants; coercion must happen before `setattr` to preserve domain integrity |

---

## Root cause (confirmed by code read, not re-investigated)

`_apply` in `sales_brief_service.py` iterated `fields.items()` and did `setattr(brief, key, value)` unconditionally for any key in `_EDITABLE`. For `faq` and `objections`, the incoming `value` from `request.model_dump(exclude_unset=True)` is `list[dict]` (JSON deserialization). The domain `SalesBrief` declares `faq: list[FaqPair]` / `objections: list[ObjectionPair]`.

When the real `SalesBriefRepository._to_model(brief)` was called, it invoked `faq_to_list(brief.faq)` which does `f.question for f in faq` — `AttributeError: 'dict' object has no attribute 'question'` → HTTP 500.

---

## Diff (2 files changed)

### `vitalia/backend/src/modules/vitalia/offer/application/services/sales_brief_service.py`

Added import:
```python
from src.modules.vitalia.offer.infrastructure.serializers import faq_from_list, objections_from_list
```

Changed `_apply`:
```python
# BEFORE
def _apply(brief: SalesBrief, fields: dict[str, Any]) -> None:
    for key, value in fields.items():
        if key in _EDITABLE:
            setattr(brief, key, value)

# AFTER
def _apply(brief: SalesBrief, fields: dict[str, Any]) -> None:
    for key, value in fields.items():
        if key not in _EDITABLE:
            continue
        if key == "faq":
            value = faq_from_list(value)
        elif key == "objections":
            value = objections_from_list(value)
        setattr(brief, key, value)
```

### `vitalia/backend/tests/modules/vitalia/offer/test_sales_brief_service.py`

Added `_SerializingFakeBriefRepo` (subclass of `_FakeBriefRepo`) that calls `faq_to_list` / `objections_to_list` on create/update, simulating the real repo round-trip. Added 4 regression tests:

- `test_save_faq_dicts_coerced_to_vos_no_attribute_error` — create path, faq=[dict] → FaqPair
- `test_save_objections_dicts_coerced_to_vos` — create path, objections=[dict] → ObjectionPair
- `test_save_faq_empty_list_clears_faq` — clearing to []
- `test_save_faq_update_second_call_still_typed` — update path (second autosave)

---

## Gate output

```
ruff check src/modules/vitalia/offer/ tests/modules/vitalia/offer/ --no-cache
→ All checks passed! (0 errors)

pytest tests/modules/vitalia/offer/test_sales_brief_service.py -v
→ 10 passed in 0.15s (all 10 GREEN including 4 new regression tests)

pytest tests/modules/vitalia/offer/ tests/architecture/ 
→ 519 passed, 4 warnings in 6.01s (0 failed)
```

---

## TDD evidence

1. **RED** — ran tests BEFORE fix: `test_save_objections_dicts_coerced_to_vos` FAILED with `AttributeError: 'dict' object has no attribute 'objection_type'` (exact production error reproduced)
2. **GREEN** — applied 5-line fix, ran tests: 10/10 PASSED
3. **No regression** — 519 tests passed (offer module + architecture gates)

---

## Scope compliance

- Touched: `vitalia/backend/src/modules/vitalia/offer/application/services/sales_brief_service.py`
- Touched: `vitalia/backend/tests/modules/vitalia/offer/test_sales_brief_service.py`
- NOT touched: core/, frontend/, other brands, DTO/router, domain VOs
