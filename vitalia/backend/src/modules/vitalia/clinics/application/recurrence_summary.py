# cap: clinics.lisa.doctores
"""format_recurrence_summary — SSoT of the human recurrence pattern (RN-D3F-1).

Shared by:
  - AvailabilityOccurrenceDTO.pattern_summary (D3-C occurrences endpoint)
  - any BE display of the block pattern (the D3-F editor summary — single source)

Pre-D3-F wording (backward compat — preserved for single-day legacy blocks):
  interval=1 + 1 day → "Semanal"
  interval=2 + 1 day → "Quincenal"

Post-D3-F (T-BE-recurrencia-domain) — multi-day or custom interval:
  "Se repite cada N semanas los lunes y jueves, 8 veces"
  "Se repite cada semana los lunes y miércoles, hasta el 31/08/2026"
  "Se repite cada 3 semanas los martes, 4 veces"
  "Se repite cada semana los lunes, sin fecha de fin"

Decision tree (RN-D3F-1: single source, never fork):
  1. one_off → "Único"
  2. len(days_of_week) == 1 AND interval == 1 → "Semanal" (legacy compat)
  3. len(days_of_week) == 1 AND interval == 2 → "Quincenal" (legacy compat)
  4. any other combination → full Google-style summary

Spanish neutro LatAm (user-facing strings, .claude/rules/spanish-text.md).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

# Day names in Spanish neutro (0=Monday..6=Sunday — dateutil/Python weekday order)
_DAY_NAMES_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def _days_label(days_of_week: list[int]) -> str:
    """Human-readable day list: 'el lunes' / 'los lunes y jueves' / 'los lunes, martes y miércoles'."""
    names = [_DAY_NAMES_ES[d] for d in sorted(days_of_week)]
    if len(names) == 1:
        return f"el {names[0]}"
    if len(names) == 2:
        return f"los {names[0]} y {names[1]}"
    return f"los {', '.join(names[:-1])} y {names[-1]}"


def _interval_label(interval: int) -> str:
    """'cada semana' (1) / 'cada 2 semanas' (2) / 'cada N semanas' (N>2)."""
    if interval == 1:
        return "cada semana"
    return f"cada {interval} semanas"


def _end_condition_label(block: "AvailabilityBlock") -> str:
    """Human suffix for the end condition."""
    if block.end_condition_kind == "occurrences" and block.occurrences:
        count = block.occurrences
        return f", {count} {'vez' if count == 1 else 'veces'}"
    if block.end_condition_kind == "end_date" and block.end_date:
        d = block.end_date
        return f", hasta el {d.day:02d}/{d.month:02d}/{d.year}"
    return ", sin fecha de fin"  # open_ended


def format_recurrence_summary(block: "AvailabilityBlock") -> str:
    """Human-readable summary of a block's recurrence pattern (RN-D3F-1 SSoT).

    Backward compat (single-day, standard intervals):
      - weekly  + 1 day → "Semanal"
      - biweekly + 1 day → "Quincenal"

    D3-F (multi-day or custom interval) → Google Calendar-style:
      "Se repite cada 2 semanas los lunes y jueves, 8 veces"

    Args:
        block: The AvailabilityBlock domain entity (recurrent or one_off).

    Returns:
        Human-readable recurrence pattern string in Spanish neutro LatAm.
    """
    if block.kind == "one_off":
        return "Único"

    # Use D3-F primary fields when available; fall back to legacy freq
    days = block.days_of_week or ([block.day_of_week] if block.day_of_week is not None else [])
    interval = block.interval if block.interval >= 1 else 1

    # Legacy backward-compat shortcuts: single-day + standard interval
    if len(days) == 1 and interval == 1:
        return "Semanal"
    if len(days) == 1 and interval == 2:
        return "Quincenal"

    # D3-F full summary: multi-day or custom interval
    if not days:
        # Defensive: unknown pattern (should not happen post-migration)
        return "Recurrente"

    interval_str = _interval_label(interval)
    days_str = _days_label(days)
    end_str = _end_condition_label(block)
    return f"Se repite {interval_str} {days_str}{end_str}"
