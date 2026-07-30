# cap: crm.crm-consent-optout
# story-origin: TBD
"""Vitalia CRM domain events — 6 events per 03-arch-be.md § 3.5.

Domain layer — pure Python dataclasses, no ORM imports.

Per hipaa-lite.md: PHI dual-filter (tenant_id + clinic_id) mandatory in events.
Per anti-duplication.md: extends DomainEvent from core engine — NEVER reimplementing.

SC-01 coverage: ConversationStarted, MessageSent, MessageRetracted, ModeChanged,
                AdrianPaused, ProactiveOutboundSent
SC-03 coverage: ModeChanged carries OCC context (previous_updated_at).

All events carry tenant_id + clinic_id for PHI dual-filter integrity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from luana_core_platform.domain.events import DomainEvent

# downstream-regression-na: brand-local vitalia CRM domain events (no cross-brand consumers)


@dataclass
class ConversationStarted(DomainEvent):
    """Fired when a new conversation is created.

    SC-01: Adrián receives new WA message → conversation started.
    PHI: carries clinic_id in payload for audit trail.

    event_name = 'conversation_started'
    """

    conversation_id: UUID = field(default_factory=UUID)
    clinic_id: UUID = field(default_factory=UUID)
    lead_id: UUID = field(default_factory=UUID)
    channel: str = ""

    def __post_init__(self) -> None:
        """Set event_name after dataclass initialization."""
        self.event_name = "conversation_started"


@dataclass
class MessageSent(DomainEvent):
    """Fired when any message is sent (patient, agent_ai, agent_human, system).

    SC-01: Adrián sends reply → MessageSent + ActionReceipt created for 5min undo.
    PHI: sender_type + channel in payload (non-identifiable but useful for audit).

    event_name = 'message_sent'
    """

    message_id: UUID = field(default_factory=UUID)
    conversation_id: UUID = field(default_factory=UUID)
    clinic_id: UUID = field(default_factory=UUID)
    sender_type: str = ""
    channel: str = ""

    def __post_init__(self) -> None:
        """Set event_name after dataclass initialization."""
        self.event_name = "message_sent"


@dataclass
class MessageRetracted(DomainEvent):
    """Fired when a message retraction is attempted (success or fallback).

    SC-01: User clicks ↩ Revertir within 5min window.
    retract_succeeded=True → message deleted via WA/IG API.
    retract_succeeded=False → email channel or API failure → 'marcar erróneo'.

    event_name = 'message_retracted'
    """

    message_id: UUID = field(default_factory=UUID)
    conversation_id: UUID = field(default_factory=UUID)
    clinic_id: UUID = field(default_factory=UUID)
    retract_succeeded: bool = False
    retract_reason: str = ""  # 'user_undo' | 'expired' | 'patient_replied'

    def __post_init__(self) -> None:
        """Set event_name after dataclass initialization."""
        self.event_name = "message_retracted"


@dataclass
class ModeChanged(DomainEvent):
    """Fired when conversation handler_mode changes.

    SC-03: Concurrent mode change → OCC check via previous_updated_at.
    Transitions: ai ↔ human, proposal_required True ↔ False.

    previous_updated_at: OCC token from If-Match header (SC-03 validation).

    event_name = 'mode_changed'
    """

    conversation_id: UUID = field(default_factory=UUID)
    clinic_id: UUID = field(default_factory=UUID)
    previous_handler_mode: str = ""
    new_handler_mode: str = ""
    previous_updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Set event_name after dataclass initialization."""
        self.event_name = "mode_changed"


@dataclass
class AdrianPaused(DomainEvent):
    """Fired when Adrián (AI agent) is paused for 60 minutes.

    SC-01: 'Adrián consulta' HITL mode — human operator handles session.
    pause_until: datetime when Adrián auto-resumes (60min from now).

    event_name = 'adrian_paused'
    """

    conversation_id: UUID = field(default_factory=UUID)
    clinic_id: UUID = field(default_factory=UUID)
    pause_until: datetime = field(default_factory=lambda: datetime.now(UTC))
    paused_by_user_id: UUID | None = None

    def __post_init__(self) -> None:
        """Set event_name after dataclass initialization."""
        self.event_name = "adrian_paused"


@dataclass
class PatientOptedOut(DomainEvent):
    """Fired when a patient is recorded as opted out from marketing.

    T-2: emitted by PatientConsentService.opt_out() via outbox adapter_bus.
    Downstream fidelizacion consumers MUST cancel pending fidelization events
    for this patient (SC-04 Slice 1).

    PHI: carries only UUIDs — no PHI fields (name, diagnosis, etc.).
    clinic_id mandatory per hipaa-lite.md dual-filter invariant.

    event_name = 'patient_opted_out'
    """

    patient_id: UUID = field(default_factory=UUID)
    clinic_id: UUID = field(default_factory=UUID)
    reason: str | None = None
    triggered_by_user_id: UUID = field(default_factory=UUID)

    def __post_init__(self) -> None:
        """Set event_name after dataclass initialization."""
        self.event_name = "patient_opted_out"


@dataclass
class ProactiveOutboundSent(DomainEvent):
    """Fired when Adrián sends a proactive outbound message.

    Proactive outbound = bot initiates contact (follow-up, appointment reminder).
    Distinct from MessageSent: always agent_ai sender_type, scheduled context.

    event_name = 'proactive_outbound_sent'
    """

    message_id: UUID = field(default_factory=UUID)
    conversation_id: UUID = field(default_factory=UUID)
    clinic_id: UUID = field(default_factory=UUID)
    channel: str = ""
    outbound_kind: str = ""  # 'follow_up' | 'appointment_reminder' | 'reactivation'

    def __post_init__(self) -> None:
        """Set event_name after dataclass initialization."""
        self.event_name = "proactive_outbound_sent"
