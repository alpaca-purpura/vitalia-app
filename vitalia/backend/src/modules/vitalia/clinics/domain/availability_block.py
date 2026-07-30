# cap: clinics.lisa.doctores
"""AvailabilityBlock domain entity — pure Python dataclass.

Domain validation enforces:
  - recurrent blocks MUST have exactly one end_condition_kind
  - one_off blocks MUST have specific_date
  - start_time MUST be before end_time

D3-F extension (T-BE-recurrencia-domain):
  - days_of_week: list[int] — primary multi-day field (0=Mon..6=Sun)
  - interval: int — recurrence interval in weeks (1=weekly, 2=biweekly, N custom)
  - day_of_week / freq derived for backward compat (legacy repos/mappers still populate them)

No framework imports — DDD domain layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from typing import Literal
from uuid import UUID, uuid4


def _utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(tz=timezone.utc)


@dataclass
class AvailabilityBlock:
    """A time block defining when a doctor is available for appointments.

    Two kinds:
    - recurrent: repeats weekly or biweekly, with an end condition
    - one_off: a single specific date

    Slots are projected from blocks by AvailabilityProjectionService (dateutil.rrule).

    D3-F multi-day fields (primary):
      days_of_week: list[int] — weekdays for recurrent blocks (0=Mon..6=Sun, len>=1)
      interval: int — recurrence interval in weeks (>=1; 1=weekly, 2=biweekly, N custom)

    Backward-compat derived fields (populated by __post_init__ when not explicitly set):
      day_of_week: int | None — first day from days_of_week (legacy single-day callers)
      freq: "weekly" | "biweekly" | None — derived from interval (1→weekly, 2→biweekly)
    """

    tenant_id: UUID
    clinic_id: UUID
    doctor_id: UUID
    kind: Literal["recurrent", "one_off"]
    start_time: time
    end_time: time
    id: UUID = field(default_factory=uuid4)

    # D3-F primary recurrent fields
    days_of_week: list[int] = field(default_factory=list)
    """0=Monday ... 6=Sunday (multi-day recurrent — len >= 1 for recurrent kind)."""

    interval: int = 1
    """Recurrence interval in weeks (>=1; 1=weekly, 2=biweekly, N=custom)."""

    # Legacy single-day field — derived in __post_init__ when days_of_week is set,
    # or kept as-is when populated by legacy repo mappers.
    day_of_week: int | None = None
    """Derived: days_of_week[0] for recurrent (legacy compat). None for one_off."""

    freq: Literal["weekly", "biweekly"] | None = None
    """Derived: 'weekly' if interval==1, 'biweekly' if interval==2, None otherwise."""

    end_condition_kind: Literal["end_date", "occurrences", "open_ended"] | None = None
    end_date: date | None = None
    occurrences: int | None = None

    # One-off field
    specific_date: date | None = None

    # Scoped-delete exclusions: ISO date strings ("YYYY-MM-DD") excluded occurrence by occurrence
    excluded_dates: list[str] = field(default_factory=list)
    """Dates individually excluded from projection (scope=occurrence delete). ISO format."""

    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        """Derive compat fields and validate domain invariants after construction.

        D3-F derivation logic:
          1. If days_of_week is populated → derive day_of_week + freq from it.
          2. If days_of_week is empty but day_of_week is set (legacy repo path)
             → backfill days_of_week from day_of_week + derive freq from interval
             (or from legacy freq field if interval is default 1).
          3. If neither is set (one_off) → leave both None/empty.
        """
        self._derive_compat_fields()
        self._validate_time_order()
        if self.kind == "recurrent":
            self._validate_recurrent()
        elif self.kind == "one_off":
            self._validate_one_off()

    def _derive_compat_fields(self) -> None:
        """Bidirectional derivation between legacy and D3-F fields.

        Priority: days_of_week (D3-F new) overrides day_of_week (legacy).
        If only legacy fields provided (repo mapper path), derive days_of_week from them.
        """
        if self.days_of_week:
            # D3-F path: derive legacy compat from primary fields
            self.day_of_week = self.days_of_week[0]
            if self.interval == 1:
                self.freq = "weekly"
            elif self.interval == 2:
                self.freq = "biweekly"
            else:
                # Custom interval > 2: freq stays None (no legacy shorthand)
                self.freq = None
        elif self.day_of_week is not None:
            # Legacy path: backfill days_of_week from day_of_week
            self.days_of_week = [self.day_of_week]
            # Derive interval from legacy freq field (if interval is still default)
            if self.freq == "biweekly" and self.interval == 1:
                self.interval = 2
            elif self.freq == "weekly" and self.interval == 1:
                self.interval = 1
            # If interval was already set > 1, trust it (explicit wins over legacy freq)
        # else: one_off or empty block — leave both empty/None

    def _validate_time_order(self) -> None:
        """start_time must be strictly before end_time."""
        if self.start_time >= self.end_time:
            raise ValueError(
                f"start_time ({self.start_time}) must be before end_time ({self.end_time}). "
                "Revisa los horarios del bloque de disponibilidad."
            )

    def _validate_recurrent(self) -> None:
        """Recurrent blocks require valid days_of_week, interval, and exactly one end condition."""
        # D3-F: validate days_of_week
        if not self.days_of_week:
            raise ValueError(
                "Un bloque recurrente requiere al menos un día de la semana (days_of_week). "
                "Selecciona los días en que se repite el bloque."
            )
        if any(d < 0 or d > 6 for d in self.days_of_week):
            raise ValueError(
                "Los días de la semana deben estar entre 0 (lunes) y 6 (domingo). "
                f"Valores inválidos: {[d for d in self.days_of_week if d < 0 or d > 6]}"
            )
        # D3-F: validate interval
        if self.interval < 1:
            raise ValueError(
                f"El intervalo de recurrencia debe ser al menos 1 semana, no {self.interval}. "
                "Indica cada cuántas semanas se repite el bloque."
            )

        # End condition validation (unchanged from pre-D3-F)
        valid_end_conditions = {"end_date", "occurrences", "open_ended"}
        if self.end_condition_kind not in valid_end_conditions:
            raise ValueError(
                "Un bloque recurrente requiere condicion de fin: "
                "elige 'end_date', 'occurrences', o 'open_ended'. "
                f"Valor recibido: {self.end_condition_kind!r}"
            )
        if self.end_condition_kind == "end_date" and self.end_date is None:
            raise ValueError(
                "Un bloque recurrente con condicion 'end_date' requiere el campo end_date. "
                "Indica la fecha de fin del bloque."
            )
        if self.end_condition_kind == "occurrences" and (self.occurrences is None or self.occurrences < 1):
            raise ValueError(
                "Un bloque recurrente con condicion 'occurrences' requiere al menos 1 ocurrencia. "
                "Indica cuantas veces se repite el bloque."
            )

    def _validate_one_off(self) -> None:
        """One-off blocks require specific_date."""
        if self.specific_date is None:
            raise ValueError(
                "Un bloque one_off requiere una fecha especifica (specific_date). "
                "Indica el dia exacto de disponibilidad."
            )
