# cap: lisa.servicios
"""Offer domain enums (RN-28 · RN-31 · RN-32 · three-charge pricing).

StrEnum so values serialize as plain strings (JSONB columns + DTO mapping).
"""

from __future__ import annotations

from enum import StrEnum


class ServiceModality(StrEnum):
    """RN-28 — how the service is delivered."""

    UNICA = "unica"  # single one-off session
    SESIONES = "sesiones"  # fixed package of N sessions
    RECURRENTE = "recurrente"  # ongoing recurring care


class InitialApptType(StrEnum):
    """RN-32 — the 3 fixed (system-defined, non-configurable) kinds of first appointment."""

    VALORACION_DIAGNOSTICO = "valoracion_diagnostico"
    PRIMERA_SESION_DIRECTA = "primera_sesion_directa"
    CONSULTA_INFORMATIVA_GRATUITA = "consulta_informativa_gratuita"


class IntervalUnit(StrEnum):
    """RN-31 — typed unit for session/recurrence intervals (never free text)."""

    DIAS = "dias"
    SEMANAS = "semanas"
    MESES = "meses"
    ANIOS = "anios"


class PriceMode(StrEnum):
    """How the headline price is expressed."""

    FIJO = "fijo"  # single fixed price
    RANGO = "rango"  # a range (desde / hasta)


class ReservationKind(StrEnum):
    """Shared by reservation + advance — fixed amount or percentage of price."""

    MONTO = "monto"
    PORCENTAJE = "porcentaje"
