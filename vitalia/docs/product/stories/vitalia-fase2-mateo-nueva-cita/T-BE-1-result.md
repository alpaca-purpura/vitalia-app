# T-BE-1 — Result

**Ticket:** T-BE-1 · BE-1 · exponer `initial_appt_duration_minutes` en `ServiceListItemDTO`
**Story:** vitalia-fase2-mateo-nueva-cita
**Builder:** builder-backend (sonnet-4.6 workhorse)
**Completed:** 2026-06-22

---

## Skills Consulted (must_load enforcement v4.1)

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | ALWAYS mandatory; FastAPI/SQLA/Pydantic v2 patterns + anti-patterns runtime checklist | Used `ConfigDict(from_attributes=True)` pattern; field added as `int \| None = None` (optional, not required); no `Any`, no `dict`, no inner `class Config` |
| `offer-expert` | T-BE-1 touches `offer` module ServiceListItemDTO | Confirmed: `_CATALOG_VERSION` bump NOT needed (not an offer-studio catalog change — this is a brand `dtos.py` Pydantic DTO, not the engine catalog). No `OFFER_SECTION_MAP` or `OFFER_FIELD_OVERRIDES` changes needed. Field already exists in `ServiceDetailDTO` + `ServiceView` + `_view()` + `offer_ext.py` — pure list DTO exposure. |

---

## Diff Summary

### Files modified

**1. `vitalia/backend/src/modules/vitalia/offer/api/dtos.py`**

Added `initial_appt_duration_minutes: int | None = None` to `ServiceListItemDTO` (line ~178 in modified file). The field was already present in `ServiceDetailDTO` (line 313) and `ServiceView` (line 93) and populated by `_view()` from `OfferExt`. The projection was already complete — only the list DTO was missing the field.

```python
# Before (ServiceListItemDTO — missing field):
price: Decimal | None = None
currency: str | None = None

# After (ServiceListItemDTO — T-BE-1):
price: Decimal | None = None
currency: str | None = None
initial_appt_duration_minutes: int | None = None  # T-BE-1: prefill duración cita (RN-5)
```

### Files created

**2. `vitalia/backend/tests/modules/vitalia/offer/test_service_list_duration.py`**

3 RED-first TDD tests for SC-dur-default:
- `test_list_returns_duration_when_set` — non-null value (45) round-trips through list endpoint
- `test_list_returns_null_duration_when_not_set` — null preserved (FE defaults 30, RN-5)
- `test_service_list_item_dto_has_duration_field` — schema contract test (field present + optional)

---

## Validator Output (V-FE-duration backend portion)

**Checks verified:**
- [x] `GET /servicios` returns `initial_appt_duration_minutes` per item → **PASS** (test_list_returns_duration_when_set)
- [x] null → FE uses 30 (RN-5) — FE concern, backend exposes null → **PASS** (test_list_returns_null_duration_when_not_set)

**Test run output (literal):**
```
============================= test session starts ==============================
collected 3 items

tests/modules/vitalia/offer/test_service_list_duration.py ...            [100%]

========================= 3 passed, 1 warning in 1.16s =========================
```

**Full offer module suite (no regressions):**
```
167 passed, 2 warnings in 1.83s
```

**Architecture fitness (no regressions):**
```
363 passed, 3 warnings in 5.53s
```

**Ruff + format:**
```
All checks passed!
2 files already formatted
```

---

## Technical Decisions

1. **No `_CATALOG_VERSION` bump required.** The offer-expert skill confirmed this is a brand-level Pydantic DTO change in `vitalia/backend/src/modules/vitalia/offer/api/dtos.py`, NOT an offer-studio engine catalog change. The `_CATALOG_VERSION` in `core/luana-core-offer-studio/` + brand `api/offer_type_presets.py` is for the preset/section catalogs — unrelated.

2. **No `catalog_service.py` or `_view()` changes needed.** The `_view()` helper already reads `ext.initial_appt_duration_minutes` from `OfferExt` and populates `ServiceView.initial_appt_duration_minutes`. The `ServiceListItemDTO` is built with `from_attributes=True` from the `ServiceView` dataclass — adding the field to the DTO was sufficient.

3. **No migration required.** Field `initial_appt_duration_minutes` already exists in `vitalia_offer_service_ext` DB table (shipped in earlier vitalia story). This ticket only exposes it in the LIST DTO response.

4. **TDD order maintained.** Test file written first → RED confirmed (assertion fail: field missing from response) → implementation (1-line DTO addition) → GREEN.

5. **Cap header correct.** Test file uses `# cap: scheduling.mateo-agenda` (the consuming capability that this field enables). DTO file already had `# cap: lisa.servicios` (the producer). Bidirectional mapping preserved.

---

## Commit SHA

`4969a6d0` — `wip/vitalia` — pushed to origin

---

## Notes

- `_CATALOG_VERSION` **NOT bumped** — this is a brand-local DTO addition, not an engine catalog change. Confirmed by `offer-expert` skill.
- The fidelizacion test failure (`test_list_for_patient`) is PRE-EXISTING (requires running Postgres with migration applied; column `last_session_at` absent in dev DB). Unrelated to T-BE-1.
- Gates 8/9/10 (integration/verify markers, migration idempotency) legitimately SKIP without Postgres — documented.
