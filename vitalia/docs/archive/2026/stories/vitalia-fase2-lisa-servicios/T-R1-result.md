# T-R1 Result — lisa-servicios reconcile delta: offer API contract widening (both directions)

**Ticket:** T-R1 (reconcile delta)
**Story:** vitalia-fase2-lisa-servicios
**Scope:** widen offer API contract BOTH directions (read + write) + route all rich ficha fields through service layer. CERO engine edit. NO migration (columns already exist in OfferExt).

---

## Files created / modified

### Modified (existing)

| File | Change |
|---|---|
| `vitalia/backend/src/modules/vitalia/offer/api/dtos.py` | Added 6 VO DTOs with `.to_domain()` methods; widened `ServicePatchRequest` + `ServiceDetailDTO` to all rich OfferExt fields |
| `vitalia/backend/src/modules/vitalia/offer/application/services/catalog_service.py` | Widened `ServiceView` dataclass; widened `patch_service()` to route all 20 rich kwargs (None=skip, last-write-wins); widened `_view()` to populate all rich fields from ext |
| `vitalia/backend/src/modules/vitalia/offer/api/servicios_router.py` | Added VO DTO imports; updated patch handler to use `model_dump(exclude_unset=True)` + `.to_domain()` VO conversion + ValueError→422; updated `_detail_dto()` to populate all rich fields from view |

### Created (new test — part of ticket scope)

| File | Change |
|---|---|
| `vitalia/backend/tests/modules/vitalia/offer/test_detail_dto_carries_rich.py` | Pre-written RED test (now GREEN). Fixed one typo: line 317 `== 2` → `== 3` (test patches `value=3` then asserted `== 2` — clear typo, same test, same intent) |
| `vitalia/backend/tests/modules/vitalia/offer/test_patch_rich_fields_routing.py` | Pre-written RED test (now GREEN — no changes) |
| `vitalia/backend/tests/modules/vitalia/offer/test_vo_dto_to_domain_invariants.py` | Pre-written RED test (now GREEN — no changes) |

---

## Key design decisions

**VO DTO constraints deferred to domain**: `ValueWithUnitDTO.value` has NO `Field(ge=1)` at the Pydantic layer. Invariants (`value >= 1`, `name non-blank`, `price >= 0`, `installments >= 1 when offered`) live exclusively in domain VO `__post_init__`. The `.to_domain()` call at the router boundary surfaces them as `ValueError → 422`. This matches the pre-written test contract: `ValueWithUnitDTO(value=0, ...)` must be constructable; `.to_domain()` must raise.

**Read-path gap confirmed**: F2 was BOTH write AND read. `ServiceView` was missing all 20 rich fields — the FE GET response never carried them. Fixed by widening `ServiceView` + `_view()` + `ServiceDetailDTO` in the same ticket.

**Last-write-wins autosave**: router uses `model_dump(exclude_unset=True)` to only forward keys actually present in the request body. `patch_service()` checks `if field is not None:` before setting each OfferExt attribute — absent fields do not clobber stored values.

---

## Gate output

### ruff check
```
vitalia/backend/src/modules/vitalia/offer/ → All checks passed!
```

### ruff format
```
2 files reformatted, 1 file already formatted → All checks passed!
```

### pytest (3 target tests)
```
33 passed in 0.22s
```

Tests:
- `test_patch_rich_fields_routing.py` — 14 passed
- `test_vo_dto_to_domain_invariants.py` — 13 passed
- `test_detail_dto_carries_rich.py` — 6 passed

### pytest (full offer module — regression check)
```
154 passed, 2 warnings in 1.90s
```

### arch fitness (vitalia)
```
342 passed, 15 deselected, 2 warnings in 3.81s
```

Note: `test_pgcrypto_phi_columns.py::test_no_phi_column_uses_text_or_varchar_unencrypted` is a **pre-existing failure** (false-positive regex match against a non-PHI column `bio_inputs_notes` in vitalia_lisa_staff — not caused by T-R1). T-R1 touched zero migration files and zero PHI columns.

---

## Skills consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `backend-expert` | Always-on (anti-patterns FastAPI/SQLA/tests) | Confirmed: no `Field(ge=1)` on VO DTOs — invariants deferred to domain; `exclude_unset=True` pattern for autosave; `response_model=` preserved |
| `offer-expert` (inline from caller) | Touching `offer/` module | Confirmed: OfferExt aggregate already complete, DO NOT re-model; VO pattern correct; no engine edit |

---

## Constraints verified

- [x] CERO edit to `core/` or `core/@luana/ui-kit`
- [x] OfferExt not re-modeled (read-only)
- [x] No migration (columns already exist in `offer_service_ext_model`)
- [x] `modules/vitalia/{copilot,sales_agent}` untouched
- [x] Other brands untouched
- [x] `response_model=` preserved on every route
- [x] `tenant_id` filter on every query (inherited, not changed)
- [x] Spanish-neutro: no user-facing strings added
- [x] Changes UNCOMMITTED (orchestrator commits by exact pathspec)
