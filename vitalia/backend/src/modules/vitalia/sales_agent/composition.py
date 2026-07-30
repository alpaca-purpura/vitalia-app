# cap: sales_agent.honor-mode-bridge
"""T-AG-GAP1 — DI composition root for the 5 async-wrapped EP-3 sales_agent tools.

GAP-1 (RECONCILE-2026-06-22 §1 + §6 item 1): the 5 async ``StructuredTool`` tools
(``screening_questions``, ``send_payment_link``, ``reschedule_appointment``,
``send_proactive_reengagement``, ``retract_last_message``) dispatch live via the
``structured_tool_adapter`` bridge, but their ``set_*_service_resolver(...)`` DI
hooks were never called at startup → ``_get_service()`` raised ``RuntimeError`` →
the tool returned a resolver-not-configured error and never executed real logic.

``wire_sales_agent_tool_resolvers()`` registers a ``() -> Service`` resolver for
each tool. ``register_all`` (the brand EP-3 composition root, called from
``main.py`` lifespan AFTER ``set_main_loop``) calls it once.

### Event-loop + session lifecycle (the crux)

Each resolver is a SYNC ``() -> Service`` but is invoked at tool-invocation time
**on the app main loop**: the engine ``node_tool_executor`` calls the sync handler,
the ``structured_tool_adapter`` runs ``tool.ainvoke(args)`` via
``tool_bridge.run_async`` which submits the coroutine to the main loop
(``run_coroutine_threadsafe(coro, _main_loop)``). The ``@tool`` body then calls
``_get_service()`` → our resolver, already inside that main-loop coroutine. So the
resolver may safely open an ``AsyncSession`` from the brand ``_AsyncSessionLocal``
(bound to the main-loop async engine) — no cross-loop asyncpg trap.

The brand repos only ``flush()`` (never ``commit()``); the tools have no
unit-of-work (unlike ``book_appointment`` which uses
``get_async_session_committing``). So each resolver wraps the service's primary
write coroutine in a **commit-on-success / rollback-on-error / close** UoW
(``_committing_session_service``), mirroring ``get_async_session_committing``.
Read-only paths (screening first-turn question load) never trigger a write, so the
commit is a harmless no-op.

Tenant/clinic dual-filter is NOT scoped here — the ``structured_tool_adapter``
overrides ``tenant_id``/``clinic_id`` from authoritative ``state`` and each service
enforces the dual filter per query (hipaa-lite.md). Resolvers only build deps.

Graceful degradation: a resolver never raises into the bridge — if a dep cannot be
built the tool's own ``try/except`` returns a Spanish-neutro fallback (the turn
never crashes). Adapter credentials (MercadoPago / WhatsApp) come from settings;
empty creds degrade at send-time inside the adapter, not here.

SSoT: RECONCILE-2026-06-22-doc-vs-reality.md §6 item 1 ·
docs/learnings/2026-06-22-ep3-tool-handler-abi-mismatch.md
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# ── Committing-session UoW wrapper ───────────────────────────────────────────


def _wrap_committing(service: object, session: Any, method_names: tuple[str, ...]) -> object:
    """Wrap ``service.<method>`` coroutines so the session commits on success,
    rolls back on error, and ALWAYS closes — the UoW the tools otherwise lack.

    Only the named write coroutines are wrapped; other attributes pass through.
    """

    class _CommittingProxy:
        __slots__ = ("_svc", "_session", "_methods")

        def __init__(self) -> None:
            self._svc = service
            self._session = session
            self._methods = method_names

        def __getattr__(self, item: str) -> Any:  # noqa: ANN401
            attr = getattr(self._svc, item)
            if item not in self._methods or not callable(attr):
                return attr

            async def _committing(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
                try:
                    result = await attr(*args, **kwargs)
                    await self._session.commit()
                    return result
                except Exception:
                    await self._session.rollback()
                    raise
                finally:
                    await self._session.close()

            return _committing

    return _CommittingProxy()


def _new_async_session() -> Any:
    """Open a fresh brand ``AsyncSession`` (main-loop bound at invocation time)."""
    from src.db import _AsyncSessionLocal  # noqa: PLC0415 — runtime DI, avoid import cycle

    return _AsyncSessionLocal()


# ── Nano LLM adapter (screening expects ``.generate(prompt) -> obj.content``) ──


class _NanoLLMAdapter:
    """Adapt the engine NANO chat client (``.ainvoke``) to the
    ``.generate(prompt) -> object`` coroutine ``ScreeningQuestionsService`` expects.

    Uses ``LLMFactory.get_service().get_client(ModelRole.NANO)`` (engine SSoT —
    NEVER a hardcoded model name). Returns the LangChain message (has ``.content``);
    the service reads ``getattr(resp, "content", str(resp))``.
    """

    __slots__ = ("_client",)

    def __init__(self) -> None:
        from luana_core_llm.factory import LLMFactory  # noqa: PLC0415
        from luana_core_platform.core.enums import ModelRole  # noqa: PLC0415

        self._client = LLMFactory.get_service().get_client(ModelRole.NANO)

    async def generate(self, prompt: str) -> Any:  # noqa: ANN401 — LLM message
        return await self._client.ainvoke(prompt)


# ── Per-tool resolvers ───────────────────────────────────────────────────────


def _resolve_screening_service() -> object:
    from src.modules.vitalia._shared.repositories.audit_log_repository import (  # noqa: PLC0415
        AuditLogRepository,
    )
    from src.modules.vitalia.sales_agent.application.services.screening_questions_service import (  # noqa: PLC0415
        ScreeningQuestionsService,
    )
    from src.modules.vitalia.sales_agent.infrastructure.repositories.lead_screening_event_repository import (  # noqa: PLC0415,E501
        LeadScreeningEventRepository,
    )

    session = _new_async_session()
    service = ScreeningQuestionsService(
        screening_repo=LeadScreeningEventRepository(session=session),
        audit_log_repo=AuditLogRepository(session=session),
        llm_service=_NanoLLMAdapter(),
    )
    # `.screen()` persists the screening event + audit row → committing UoW.
    return _wrap_committing(service, session, ("screen",))


def _resolve_payment_link_service() -> object:
    from luana_core_platform.core.config import get_settings  # noqa: PLC0415

    from src.modules.vitalia._shared.repositories.audit_log_repository import (  # noqa: PLC0415
        AuditLogRepository,
    )
    from src.modules.vitalia.compliance.guardrails.medical_results_guard import (  # noqa: PLC0415
        MedicalResultsChannelGuard,
    )
    from src.modules.vitalia.sales_agent.application.services.payment_link_service import (  # noqa: PLC0415
        PaymentLinkService,
    )
    from src.modules.vitalia.sales_agent.infrastructure.adapters.mercadopago_adapter import (  # noqa: PLC0415
        MercadoPagoAdapter,
    )
    from src.modules.vitalia.sales_agent.infrastructure.adapters.whatsapp_business_adapter import (  # noqa: PLC0415,E501
        WhatsAppBusinessAdapter,
    )

    settings = get_settings()
    # Credentials from settings env; empty → adapter degrades at send-time (the
    # tool's own try/except returns a Spanish fallback). The resolver must not raise.
    mp = MercadoPagoAdapter(
        access_token=getattr(settings, "MERCADOPAGO_ACCESS_TOKEN", "") or "",
        webhook_secret=getattr(settings, "MERCADOPAGO_WEBHOOK_SECRET", "") or "",
    )
    wa = WhatsAppBusinessAdapter(
        phone_number_id=getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "") or "",
        access_token=getattr(settings, "WHATSAPP_API_TOKEN", "") or "",
    )
    session = _new_async_session()
    service = PaymentLinkService(
        channel_guard=MedicalResultsChannelGuard(),
        mercadopago_adapter=mp,
        whatsapp_adapter=wa,
        audit_log_repo=AuditLogRepository(session=session),
        session=session,
    )
    return _wrap_committing(service, session, ("send_payment_link",))


def _resolve_reschedule_service() -> object:
    from src.modules.vitalia._shared.repositories.audit_log_repository import (  # noqa: PLC0415
        AuditLogRepository,
    )
    from src.modules.vitalia.sales_agent.application.services.reschedule_appointment_service import (  # noqa: PLC0415,E501
        RescheduleAppointmentService,
    )

    session = _new_async_session()
    # NOTE (GAP-1 sub-limitation): no production AppointmentService implements
    # `async update_slot(...)` yet (parallels the book/ESC-19 scheduling-domain gap).
    # The resolver fires and the service is built (so the tool reaches PAST the
    # resolver — the GAP-1 bar), but a real reschedule write will fail inside
    # `update_slot` → the tool's own except returns the Spanish "No pude reprogramar"
    # fallback. Wiring the real scheduling AppointmentService is a scheduling-domain
    # follow-up, not GAP-1. We pass a fail-fast stub that raises a clear error so
    # the tool degrades cleanly (never the resolver-not-configured signal).
    service = RescheduleAppointmentService(
        appointment_service=_RescheduleAppointmentNotWiredStub(),
        audit_log_repo=AuditLogRepository(session=session),
    )
    return _wrap_committing(service, session, ("reschedule",))


class _RescheduleAppointmentNotWiredStub:
    """Fail-fast stand-in for the scheduling AppointmentService.

    `reschedule()` delegates to `appointment_service.update_slot(...)`, which has no
    production implementation (scheduling-domain gap, like book/ESC-19). Raising a
    clear error here makes the tool degrade to its Spanish fallback ("No pude
    reprogramar...") — a service-level error PAST the resolver, never the
    resolver-not-configured signal. Replace with the real AppointmentService once
    the scheduling create/reschedule lane lands.
    """

    async def update_slot(self, **_kwargs: Any) -> Any:  # noqa: ANN401
        raise NotImplementedError(
            "scheduling AppointmentService.update_slot not yet wired "
            "(scheduling-domain reschedule lane pending — see GAP-1 sub-limitation / ESC-19)."
        )


def _resolve_proactive_outbound_service() -> object:
    from src.modules.vitalia._shared.repositories.audit_log_repository import (  # noqa: PLC0415
        AuditLogRepository,
    )
    from src.modules.vitalia.fidelizacion.application.services.proactive_outbound_service import (  # noqa: PLC0415,E501
        ProactiveOutboundService,
    )
    from src.modules.vitalia.fidelizacion.infrastructure.repositories.re_engagement_event_repository import (  # noqa: PLC0415,E501
        ReEngagementEventRepository,
    )

    session = _new_async_session()
    # Mirror the production DI in fidelizacion/api/re_engagement_endpoints.py:337.
    service = ProactiveOutboundService(
        session=session,
        re_engagement_repo=ReEngagementEventRepository(session=session),
        audit_repo=AuditLogRepository(session=session),
        compliance_service=_build_compliance_service(),
    )
    return _wrap_committing(service, session, ("send_proactive_reminder",))


def _resolve_retract_message_service() -> object:
    from src.modules.vitalia.audit.audit_writer import AsyncAuditWriter  # noqa: PLC0415
    from src.modules.vitalia.crm.infrastructure.persistence.action_receipt_repository import (  # noqa: PLC0415,E501
        ActionReceiptRepository,
    )
    from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (  # noqa: PLC0415,E501
        ConversationRepository,
    )
    from src.modules.vitalia.crm.infrastructure.persistence.message_repository import (  # noqa: PLC0415
        MessageRepository,
    )
    from src.modules.vitalia.inbox.application.services.retract_message_service import (  # noqa: PLC0415
        RetractMessageService,
    )

    session = _new_async_session()
    # Mirror the production DI in inbox/api/router.py:256.
    service = RetractMessageService(
        msg_repo=MessageRepository(session=session),
        receipt_repo=ActionReceiptRepository(session=session),
        conv_repo=ConversationRepository(session=session),
        audit_writer=AsyncAuditWriter(session=session),
        event_bus=_adapter_bus(),
        channel_adapters={},
        session=session,
    )
    return _wrap_committing(service, session, ("retract",))


# ── Shared deps (mirror inbox/fidelizacion composition; NO mirror of engine) ──


def _build_compliance_service() -> object:
    """Real ComplianceService running the brand PhiChannelPolicy (mirrors
    inbox/api/router.py::_build_compliance_service). Extends the engine
    CompliancePolicy Protocol — NOT a mirror (anti-duplication.md)."""
    from luana_core_compliance.application.compliance_service import ComplianceService  # noqa: PLC0415

    from src.modules.vitalia.inbox.application.policies.phi_channel_policy import (  # noqa: PLC0415
        PhiChannelPolicy,
    )

    return ComplianceService(policies=[PhiChannelPolicy()])


def _adapter_bus() -> object:
    """The outbox adapter bus (same import the inbox/fidelizacion services use)."""
    try:
        from luana_core_events.outbox import adapter_bus  # noqa: PLC0415

        return adapter_bus
    except Exception:  # noqa: BLE001 — tests / no outbox configured
        from unittest.mock import AsyncMock  # noqa: PLC0415

        bus = AsyncMock()
        return bus


# ── Public composition entrypoint (called from register_all) ──────────────────


# ── Inbound mode seam (GAP-2/GAP-3) ───────────────────────────────────────────


async def _load_open_conversation(*, tenant_id: Any, lead_id: Any) -> Any:
    """Load the most-recent open Conversation for a lead (tenant-scoped, own session).

    Tenant-scoped read (clinic_id is READ from the row, it is the authoritative
    dual-filter axis the brand then uses to write). Returns the Conversation row
    or None. Best-effort: any failure → None (the seam degrades to DECIDE / no-op).
    Runs on the app main loop (deliver_response awaits it) → the brand AsyncSession
    binds to the loop that owns the shared async engine pool (no cross-loop trap).
    """
    if lead_id is None:
        return None
    from sqlalchemy import select  # noqa: PLC0415

    from src.modules.vitalia.crm.infrastructure.persistence.models.conversation_model import (  # noqa: PLC0415
        ConversationModel,
    )

    session = _new_async_session()
    try:
        stmt = (
            select(ConversationModel)
            .where(ConversationModel.tenant_id == tenant_id)
            .where(ConversationModel.lead_id == lead_id)
            .where(ConversationModel.status == "open")
            .where(ConversationModel.deleted_at.is_(None))
            .order_by(ConversationModel.last_message_at.desc().nullslast())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    except Exception as exc:  # noqa: BLE001 — seam read is best-effort
        logger.warning("inbound_seam_conv_load_failed", error=str(exc))
        return None
    finally:
        await session.close()


async def _write_activity_event(**kwargs: Any) -> Any:  # noqa: ANN401
    """Write one vitalia_activity_events row in its own committing session.

    Mirrors the inbox/fidelización per-call session pattern (composition.py GAP-1):
    open → ActivityEventRepository.create (flush) → commit → close. Best-effort.
    """
    from src.modules.vitalia.crm.infrastructure.persistence.activity_event_repository import (  # noqa: PLC0415,E501
        ActivityEventRepository,
    )

    session = _new_async_session()
    try:
        repo = ActivityEventRepository(session=session)
        row = await repo.create(**kwargs)
        await session.commit()
        return row
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def _build_inbound_seam_adapter() -> Any:  # noqa: ANN401
    """Construct the VitaliaInboundSeamAdapter with brand loader + writer ports."""
    from src.modules.vitalia.sales_agent.application.services.inbound_seam_adapter import (  # noqa: PLC0415,E501
        VitaliaInboundSeamAdapter,
    )

    return VitaliaInboundSeamAdapter(
        conv_loader=_load_open_conversation,
        activity_writer=_write_activity_event,
    )


def wire_inbound_mode_seam() -> None:
    """Wire vitalia's mode resolver + draft sink + activity subscriber (GAP-2/3).

    - ``set_mode_resolver`` → HonorModeBridge over the lead's open conversation.
    - ``set_draft_sink`` → on CONSULTA, write an ``adrian_draft_pending`` activity row.
    - ``EventBus.subscribe('agent_turn_completed', ...)`` → write an ``adrian_turn``
      activity row from the engine AgentTurnCompletedEvent (outbox-delivered).

    Idempotent (module-level rebind + subscribe is additive). Called once from
    ``register_all`` at FastAPI lifespan startup. Each adapter builds its own
    committing session per call (main-loop bound).
    """
    from luana_core_sales_agent.application.orchestrator.inbound_mode_seam import (  # noqa: PLC0415
        set_draft_sink,
        set_mode_resolver,
    )

    from src.modules.vitalia.sales_agent.application.services.inbound_seam_adapter import (  # noqa: PLC0415,E501
        build_agent_turn_completed_handler,
    )

    adapter = _build_inbound_seam_adapter()

    async def _resolver(*, tenant_id: Any, lead_id: Any, checkpoint: Any) -> Any:  # noqa: ANN401, ARG001
        # checkpoint is the ENGINE checkpoint (no vitalia mode fields) — the
        # adapter loads vitalia's own Conversation by (tenant_id, lead_id).
        return await adapter.resolve_mode_async(tenant_id=tenant_id, lead_id=lead_id)

    set_mode_resolver(_resolver)
    set_draft_sink(adapter.draft_sink_async)

    # Subscribe the activity-event handler on the legacy in-memory bus — the outbox
    # dispatcher re-emits via LegacyEventBus._dispatch(event_name), so this fires
    # for both the in-memory (flag-off) and the outbox (flag-on) delivery paths.
    from luana_core_platform.domain.events import EventBus as _LegacyEventBus  # noqa: PLC0415

    _LegacyEventBus.subscribe("agent_turn_completed", build_agent_turn_completed_handler(adapter))

    logger.info("vitalia.sales_agent.inbound_mode_seam_wired")


def wire_sales_agent_tool_resolvers() -> None:
    """Wire every ``set_*_service_resolver`` for the 5 async-wrapped EP-3 tools.

    Idempotent (resolvers are module-level globals; re-wiring is a no-op rebind).
    Called once from ``register_all`` at FastAPI lifespan startup.
    """
    from src.modules.vitalia.sales_agent.tools.payment_link import (  # noqa: PLC0415
        set_payment_link_service_resolver,
    )
    from src.modules.vitalia.sales_agent.tools.reschedule_appointment import (  # noqa: PLC0415
        set_reschedule_service_resolver,
    )
    from src.modules.vitalia.sales_agent.tools.retract_last_message import (  # noqa: PLC0415
        set_retract_message_service_resolver,
    )
    from src.modules.vitalia.sales_agent.tools.screening_questions import (  # noqa: PLC0415
        set_screening_service_resolver,
    )
    from src.modules.vitalia.sales_agent.tools.send_proactive_reengagement import (  # noqa: PLC0415
        set_proactive_outbound_service_resolver,
    )

    set_screening_service_resolver(_resolve_screening_service)
    set_payment_link_service_resolver(_resolve_payment_link_service)
    set_reschedule_service_resolver(_resolve_reschedule_service)
    set_proactive_outbound_service_resolver(_resolve_proactive_outbound_service)
    set_retract_message_service_resolver(_resolve_retract_message_service)

    logger.info(
        "vitalia.sales_agent.tool_resolvers_wired",
        tools=[
            "screening_questions",
            "send_payment_link",
            "reschedule_appointment",
            "send_proactive_reengagement",
            "retract_last_message",
        ],
    )


__all__ = ["wire_inbound_mode_seam", "wire_sales_agent_tool_resolvers"]
