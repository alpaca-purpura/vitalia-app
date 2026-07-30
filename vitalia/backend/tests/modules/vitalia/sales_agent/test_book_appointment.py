# cap: sales_agent.honor-mode-bridge
"""OLA-2 ``book_appointment`` — engine-ABI + fast-path shape tests (DB-free).

The real booking (DB write via the main-loop bridge) is live-verified separately
(in-container single-call → real appointment row). Here we assert the engine ABI
(callable as ``fn(state, db)``) + the structured guards that never touch the DB.
"""

from __future__ import annotations

import json

from src.modules.vitalia.sales_agent.tools.book_appointment import _parse_dt, book_appointment

_DEV_TENANT = "e69a691d-070e-5caf-a053-6e74642ec100"
_LEAD = "11111111-1111-1111-1111-111111111111"
_DOCTOR = "22222222-2222-2222-2222-222222222222"


def test_missing_tenant_is_structured() -> None:
    out = book_appointment({"_pending_tool": {"args": {}}}, db=None)
    assert out["status"] == "error"
    json.dumps(out, ensure_ascii=False)


def test_missing_doctor_asks_for_info() -> None:
    out = book_appointment(
        {"tenant_id": _DEV_TENANT, "user_id": _LEAD, "_pending_tool": {"args": {"start_time": "2026-06-26T15:00"}}},
        db=None,
    )
    assert out["status"] == "need_info"


def test_missing_start_time_asks_for_info() -> None:
    out = book_appointment(
        {"tenant_id": _DEV_TENANT, "user_id": _LEAD, "_pending_tool": {"args": {"doctor_id": _DOCTOR}}},
        db=None,
    )
    assert out["status"] == "need_info"


def test_bad_datetime_is_structured() -> None:
    out = book_appointment(
        {
            "tenant_id": _DEV_TENANT,
            "user_id": _LEAD,
            "_pending_tool": {"args": {"doctor_id": _DOCTOR, "start_time": "mañana a la tarde"}},
        },
        db=None,
    )
    assert out["status"] == "error"


def test_parse_dt() -> None:
    assert _parse_dt("2026-06-26T15:00") is not None
    assert _parse_dt("2026-06-26 15:00:00") is not None
    assert _parse_dt("2026-06-26T15:00:00Z") is not None
    assert _parse_dt("not a date") is None
    assert _parse_dt(None) is None
    # naive → UTC tz attached
    dt = _parse_dt("2026-06-26T15:00")
    assert dt is not None and dt.tzinfo is not None
