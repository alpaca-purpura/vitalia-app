"""SQLAlchemy model for appointment model."""

import uuid

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func


class AppointmentModel(Base):
    """SQLAlchemy model for appointment."""

    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    lead_id = Column(
        UUID(as_uuid=True),
        ForeignKey("leads.id"),
        nullable=True,
        index=True,
    )

    summary = Column(String, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    status = Column(
        String,
        default="SCHEDULED",
    )  # SCHEDULED, CANCELLED, COMPLETED, NO_SHOW
    meeting_link = Column(String, nullable=True)

    external_event_id = Column(String, nullable=True)  # Google Calendar ID
    metadata_info = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ESC-18 (2026-06-22 · multibrand-graph-runtime): the `lead = relationship("LeadModel")`
    # forward nav was REMOVED. It is the mirror of ESC-7's already-removed
    # LeadModel.appointments and was DEAD (no `appointment.lead` access anywhere — the
    # `link.lead` usages are BookingLinkModel, a different model). As a bare-string
    # cross-registry target (scheduling→platform on a different mapper registry) it only
    # resolved on a clean global configure_mappers(); any later lazy import re-triggered a
    # per-registry configure that could NOT locate `LeadModel` → crashed the FIRST ORM query
    # on `appointments`. The FK `lead_id` (ForeignKey "leads.id") stays; only the ORM
    # relationship object is dropped. Read the lead via an explicit query when needed.
    # (arch-green != runtime — found by book_appointment live-verify; engine fix promoted
    # shared-only to main since the original change was entangled in a brand commit.)
