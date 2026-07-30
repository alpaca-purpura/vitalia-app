# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Vitalia appointment origin registry (4 origins Slice 1)."""

from .registry import (
    APPOINTMENT_ORIGIN_REGISTRY,
    AppointmentOriginDef,
    get_appointment_origin,
    list_appointment_origins,
)

__all__ = (
    "APPOINTMENT_ORIGIN_REGISTRY",
    "AppointmentOriginDef",
    "get_appointment_origin",
    "list_appointment_origins",
)
