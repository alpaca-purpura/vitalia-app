# cap: sales_agent.honor-mode-bridge
"""T-AG-GAP1 EXECUTION gate — every async-wrapped EP-3 tool must REACH its service
when dispatched the way the engine does it, NOT short-circuit on
``resolver not configured``.

GAP-1 (RECONCILE-2026-06-22 §1): the 5 async StructuredTools dispatch live but
their ``set_*_service_resolver(...)`` DI hooks were never called at startup, so
``_get_service()`` raised ``RuntimeError`` → the adapter returned
``{"status": "error", ... resolver not configured}`` (or, for proactive, a
"dispatcher" fallback string) → the tool never executed real logic.

This test invokes each handler EXACTLY as ``node_tool_executor`` does
(``tool_fn(state, db=state.get("_db"))`` with realistic
``state["_pending_tool"]["args"]``) and asserts the result is NOT the
resolver-unwired signal. RED before ``register_all`` wires the resolvers; GREEN
after.

The bar is "reaches the service" (the resolver fired + the service was built),
NOT a successful business outcome — DB/LLM/scheduling effects are the live-verify
step. Reaching the service may surface a service-level error (no DB in CI, a
missing scheduling ``update_slot`` impl, etc.); that is still PAST the resolver
and therefore GREEN for GAP-1.

SSoT: RECONCILE-2026-06-22-doc-vs-reality.md §1 + §6 item 1.
"""

from __future__ import annotations

import json
from uuid import uuid4

from luana_core_extension_sdk._adapters import _SalesAgentToolRegistryAdapter
from luana_core_extension_sdk.extension_points import ExtensionPointRegistry
from luana_core_sales_agent.application.tools.registry import ToolRegistry

from src.modules.vitalia.extensions import register_all

# A real-looking tenant/clinic (state-authoritative; the adapter overrides these
# from state, never from the LLM args).
_TENANT = str(uuid4())
_CLINIC = str(uuid4())


def _merged_handlers() -> dict:
    tr = ToolRegistry()
    reg = ExtensionPointRegistry(
        sales_agent_tool_registry_adapter=_SalesAgentToolRegistryAdapter(tr),
    )
    register_all(reg)
    return {name: tool.handler for name, tool in tr.extension_tools().items()}


def _dispatch(handler, args: dict) -> dict | str:
    """Mirror ``node_tool_executor``: build state with a [TOOL_REQUEST], call
    ``handler(state, db=state.get("_db"))``, and round-trip through json.dumps
    (the engine does this next)."""
    state = {
        "tenant_id": _TENANT,  # authoritative — adapter overrides args
        "clinic_id": _CLINIC,
        "_db": None,  # engine never seeds _db at inbound (RECONCILE §2)
        "_pending_tool": {"tool": "", "args": args},
    }
    result = handler(state, db=state.get("_db"))
    json.dumps(result, ensure_ascii=False)  # must be serialisable
    return result


def _is_resolver_unwired(result: dict | str) -> bool:
    """True iff the result is the GAP-1 resolver-not-configured signal.

    Two shapes per tool:
      * screening / payment_link / reschedule: ``_get_service()`` raises
        RuntimeError → adapter ``{"status":"error", "message": "...resolver not
        configured..."}``.
      * send_proactive_reengagement / retract_last_message: the tool catches the
        RuntimeError itself and returns a Spanish "dispatcher" fallback string.
    """
    text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
    low = text.lower()
    return (
        "resolver not configured" in low
        or "set_" in low  # the RuntimeError message points at set_*_service_resolver
        or "dispatcher de mensajes proactivos" in low  # proactive resolver-unwired fallback
        # retract resolver-unwired fallback (distinct from its WIRED error strings,
        # which say "marcado como erróneo" / "el paciente ya respondió" / "excedió 5 minutos"):
        or "no pude revertir el mensaje. quedó registrado para revisión." in low
    )


# ── Per-tool execution probes ────────────────────────────────────────────────


def test_screening_questions_reaches_service() -> None:
    handlers = _merged_handlers()
    handler = handlers["vitalia.screening_questions"]
    # No lead_response → first-turn path loads questions from YAML (no DB, no LLM).
    out = _dispatch(handler, {"lead_id": str(uuid4()), "vertical": "dental"})
    assert not _is_resolver_unwired(out), f"screening_questions resolver not wired: {out}"


def test_send_payment_link_reaches_service() -> None:
    handlers = _merged_handlers()
    handler = handlers["vitalia.send_payment_link"]
    out = _dispatch(
        handler,
        {
            "lead_id": str(uuid4()),
            "appointment_id": str(uuid4()),
            "deposit_percent": 30,
            "channel": "whatsapp_free",
        },
    )
    assert not _is_resolver_unwired(out), f"send_payment_link resolver not wired: {out}"


def test_reschedule_appointment_reaches_service() -> None:
    handlers = _merged_handlers()
    handler = handlers["vitalia.reschedule_appointment"]
    out = _dispatch(
        handler,
        {
            "appointment_id": str(uuid4()),
            "new_starts_at": "2026-07-01T15:00:00+00:00",
            "reason": "Paciente pidió cambio",
        },
    )
    assert not _is_resolver_unwired(out), f"reschedule_appointment resolver not wired: {out}"


def test_send_proactive_reengagement_reaches_service() -> None:
    handlers = _merged_handlers()
    handler = handlers["vitalia.send_proactive_reengagement"]
    out = _dispatch(
        handler,
        {
            "patient_id": str(uuid4()),
            "patient_phone": "+99 0 1234 5678",
            "patient_name": "Paciente Sintético",
            "pattern": "absence",  # valid ReEngagementPattern literal
            "template_id": "vitalia_reengagement",
            "marketing_opt_in": True,
            "opt_out": False,
            "re_engagement_event_id": str(uuid4()),
            "trigger_source": "cron",
            "triggered_by_user_id": str(uuid4()),
        },
    )
    assert not _is_resolver_unwired(out), f"send_proactive_reengagement resolver not wired: {out}"


def test_retract_last_message_reaches_service() -> None:
    handlers = _merged_handlers()
    handler = handlers["vitalia.retract_last_message"]
    out = _dispatch(
        handler,
        {
            "conversation_id": str(uuid4()),
            "message_id": str(uuid4()),
            "reason": "Promesa clínica fuera de scope detectada por ComplianceService",
        },
    )
    assert not _is_resolver_unwired(out), f"retract_last_message resolver not wired: {out}"


def test_all_five_wrapped_tools_present() -> None:
    """Guard: the 5 async-wrapped tools are still registered (so the probes above
    don't silently pass on a missing key)."""
    handlers = _merged_handlers()
    for name in (
        "vitalia.screening_questions",
        "vitalia.send_payment_link",
        "vitalia.reschedule_appointment",
        "vitalia.send_proactive_reengagement",
        "vitalia.retract_last_message",
    ):
        assert name in handlers, f"{name} missing from register_all EP-3 tools"
