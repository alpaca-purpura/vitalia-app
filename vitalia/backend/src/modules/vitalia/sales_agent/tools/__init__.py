# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""Vitalia Adrián sales_agent tools (3 MVP per Q1 Slice 1 default).

Story T-ag-tools-2 (R23 production_code=true).

Tools:
- ``screening_questions`` — wraps ``ScreeningQuestionsService.screen``
- ``send_payment_link`` — wraps ``PaymentLinkService.send_payment_link``
- ``reschedule_appointment`` — wraps ``RescheduleAppointmentService.reschedule``

All tools:
- ``@tool`` LangChain decorator + Pydantic v2 ``args_schema``
- Async (``async def``)
- ``tenant_id`` + ``clinic_id`` MANDATORY in input schema (HIPAA-lite dual filter)
- Call SERVICES (NEVER raw repos) — services wrap adapter timeouts + retries
- Best-effort observability (services handle audit log writes synchronously)

Deferred Slice 2 (per Q1 default):
- ``send_template_confirmation`` — engine defaults cover (T-24h/T-2h reminders)
- ``retract_last_message`` — UI undo 5min (Inbox UndoToast) covers
"""

from __future__ import annotations

from src.modules.vitalia.sales_agent.tools.payment_link import send_payment_link
from src.modules.vitalia.sales_agent.tools.reschedule_appointment import (
    reschedule_appointment,
)
from src.modules.vitalia.sales_agent.tools.screening_questions import screening_questions

__all__ = [
    "reschedule_appointment",
    "screening_questions",
    "send_payment_link",
]
