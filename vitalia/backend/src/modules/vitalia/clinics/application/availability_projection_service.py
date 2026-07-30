# cap: clinics.lisa.doctores
"""AvailabilityProjectionService — expands AvailabilityBlock into slots via dateutil.rrule.

Architecture decision D-2 (03-arch.md): recurrence engine is brand-local dateutil.rrule
(NOT luana-core-commercial-calendar which is a marketing-event calendar with zero RRULE
support). python-dateutil v2.9.0 is already in uv.lock.

RFC 5545 RRULE mapping:
  - weekly  → rrule(WEEKLY, interval=1, byweekday=day_of_week, ...)
  - biweekly → rrule(WEEKLY, interval=2, byweekday=day_of_week, ...)
  - end_date   → until=end_date (datetime)
  - occurrences → count=occurrences
  - open_ended → until=today+90d (rolling horizon, materialized on create/update)
  - one_off → single date, no rrule needed

Slot granularity: default 30min (tenant appointment duration config — passed by caller).
UTC: all start_ts/end_ts are timezone-aware UTC datetimes.
Tenant timezone conversion: caller passes slot_duration_minutes only; full tz conversion
is deferred to scheduling service (brand-local pattern — scheduler owns tz display).

Mutability:
  - project_block(block, reference_date): expand from reference_date onward (create/reproject)
  - classify_future_slots_for_deletion(existing_slots, reference_date): split into
    to_delete (free) vs preserved (confirmed) — used by repo delete_block / update_block
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import structlog
from dateutil.rrule import WEEKLY, rrule

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()

# Default slot granularity in minutes (tenant config can override)
_DEFAULT_SLOT_DURATION_MINUTES = 30

# Rolling horizon for open_ended blocks
_OPEN_ENDED_HORIZON_DAYS = 90


def _is_excluded(occurrence_date: date, block: "AvailabilityBlock") -> bool:  # noqa: F821
    """Return True if occurrence_date is in block.excluded_dates.

    Single source for exclusion check — used by both project_block and
    occurrence_dates_in_range so the logic is never duplicated.
    """
    excluded = getattr(block, "excluded_dates", None) or []
    return occurrence_date.isoformat() in excluded


# ── Value object returned by projection ──────────────────────────────────────


@dataclass
class ProjectedSlot:
    """A single materialized availability slot.

    Returned by AvailabilityProjectionService.project_block().
    Caller maps this to VitaliaAvailabilitySlotModel for persistence.
    """

    tenant_id: UUID
    clinic_id: UUID
    doctor_id: UUID
    block_id: UUID
    slot_date: date
    start_ts: datetime
    end_ts: datetime
    has_confirmed_appointment: bool = field(default=False)
    id: UUID = field(default_factory=uuid4)


# ── Service ───────────────────────────────────────────────────────────────────


class AvailabilityProjectionService:
    """Expand AvailabilityBlock into materialized ProjectedSlot list.

    Usage::

        service = AvailabilityProjectionService(slot_duration_minutes=30)
        slots = service.project_block(block, reference_date=date.today())
        # slots is list[ProjectedSlot] ready for persistence

    reference_date filters out past dates — only slot_date >= reference_date
    are materialized. This implements the "reproject future only" invariant.
    """

    def __init__(self, slot_duration_minutes: int = _DEFAULT_SLOT_DURATION_MINUTES) -> None:
        """Initialize with slot granularity.

        Args:
            slot_duration_minutes: Duration per slot in minutes (default: 30).
        """
        if slot_duration_minutes < 1:
            raise ValueError(f"slot_duration_minutes must be >= 1, got {slot_duration_minutes}")
        self._duration = timedelta(minutes=slot_duration_minutes)

    def project_block(
        self,
        block: "AvailabilityBlock",  # noqa: F821 — forward ref avoided via string
        *,
        reference_date: date | None = None,
    ) -> list[ProjectedSlot]:
        """Expand a block into materialized slots.

        Args:
            block: The AvailabilityBlock domain entity.
            reference_date: Only project slots on or after this date.
                            Defaults to today (UTC). Use a specific date for
                            historical projection in tests.

        Returns:
            List of ProjectedSlot ready to be persisted as VitaliaAvailabilitySlotModel.
        """

        if reference_date is None:
            reference_date = datetime.now(tz=timezone.utc).date()

        if block.kind == "one_off":
            return self._project_one_off(block, reference_date=reference_date)
        elif block.kind == "recurrent":
            return self._project_recurrent(block, reference_date=reference_date)
        else:
            logger.warning("unknown_block_kind", kind=block.kind, block_id=str(block.id))
            return []

    def occurrence_dates_in_range(
        self,
        block: "AvailabilityBlock",  # noqa: F821
        *,
        range_start: date,
        range_end: date,
        series_anchor: date | None = None,
    ) -> list[date]:
        """Block-level occurrence dates within [range_start, range_end] (inclusive).

        D3-C contract (03-arch-delta § 4.3 + V-D3C-1..8) — the occurrences
        endpoint collapses slots to one occurrence per (block, date); this is
        the date-level projection it reuses (NO new expansion logic: same rrule
        builder as project_block).

        Anchor invariant (regression SC-D3C-1/SC-D3C-2):
          - The recurrence series anchors at ``series_anchor`` (default: the
            block's created_at date — the same reference_date used when slots
            materialized on create). Re-anchoring at the query window start
            would RESTART count-based series in every window (the indefinite-
            paint bug, server-side) and flip biweekly parity.
          - ``open_ended`` uses a rolling today+90d horizon (mirrors slot
            re-materialization): old open-ended blocks keep painting current
            windows; nothing projects beyond the horizon (SC-D3C-4).

        Args:
            block: The AvailabilityBlock domain entity.
            range_start: First date of the window (inclusive).
            range_end: Last date of the window (inclusive).
            series_anchor: Override the series anchor (tests / re-anchored series).

        Returns:
            Sorted occurrence dates within the window.
        """
        if block.kind == "one_off":
            assert block.specific_date is not None, "one_off block must have specific_date"
            if range_start <= block.specific_date <= range_end and not _is_excluded(block.specific_date, block):
                return [block.specific_date]
            return []

        if block.kind != "recurrent":
            logger.warning("unknown_block_kind", kind=block.kind, block_id=str(block.id))
            return []

        anchor = series_anchor if series_anchor is not None else block.created_at.date()
        today = datetime.now(tz=timezone.utc).date()
        dates = self._recurrent_occurrence_dates(
            block,
            series_anchor=anchor,
            open_ended_until=today + timedelta(days=_OPEN_ENDED_HORIZON_DAYS),
        )
        return [d for d in dates if range_start <= d <= range_end and not _is_excluded(d, block)]

    def classify_future_slots_for_deletion(
        self,
        existing_slots: list[ProjectedSlot],
        *,
        reference_date: date | None = None,
    ) -> tuple[list[ProjectedSlot], int]:
        """Split future slots into deletable (free) and preserved (confirmed).

        Used by repository delete_block / update_block to determine which
        slots to soft-delete without touching confirmed appointments.

        Args:
            existing_slots: All current slots for the block (any date).
            reference_date: Cutoff date — only classify slots >= this date.
                            Defaults to today (UTC).

        Returns:
            Tuple of (to_delete: list[ProjectedSlot], preserved_count: int).
            to_delete: free future slots (has_confirmed_appointment=False)
            preserved_count: count of confirmed future slots (untouched)
        """
        if reference_date is None:
            reference_date = datetime.now(tz=timezone.utc).date()

        to_delete: list[ProjectedSlot] = []
        preserved_count = 0

        for slot in existing_slots:
            if slot.slot_date < reference_date:
                # Past slots — never touch regardless of confirmation status
                continue
            if slot.has_confirmed_appointment:
                preserved_count += 1
            else:
                to_delete.append(slot)

        return to_delete, preserved_count

    # ── Private expansion helpers ─────────────────────────────────────────────

    def _project_one_off(
        self,
        block: "AvailabilityBlock",  # noqa: F821
        *,
        reference_date: date,
    ) -> list[ProjectedSlot]:
        """Project a one_off block: single date only."""
        assert block.specific_date is not None, "one_off block must have specific_date"

        # Skip if specific_date is before the reference (past slot)
        if block.specific_date < reference_date:
            return []

        # Skip if specific_date is individually excluded
        if _is_excluded(block.specific_date, block):
            return []

        return self._slots_for_date(block.specific_date, block=block)

    def _project_recurrent(
        self,
        block: "AvailabilityBlock",  # noqa: F821
        *,
        reference_date: date,
    ) -> list[ProjectedSlot]:
        """Project a recurrent block using dateutil.rrule.

        Maps freq to interval:
          - weekly  → WEEKLY interval=1
          - biweekly → WEEKLY interval=2

        Maps end_condition_kind:
          - end_date   → until=datetime(end_date, tzinfo=UTC)
          - occurrences → count=occurrences
          - open_ended → until=reference_date + 90d
        """
        if block.end_condition_kind == "end_date":
            assert block.end_date is not None, "end_date condition requires end_date field"
            if block.end_date < reference_date:
                return []  # entire range is in the past

        occurrence_dates = self._recurrent_occurrence_dates(
            block,
            series_anchor=reference_date,
            open_ended_until=reference_date + timedelta(days=_OPEN_ENDED_HORIZON_DAYS),
        )

        # Filter occurrences < reference_date (can happen with count-based)
        # Also filter individually excluded occurrences
        occurrence_dates = [d for d in occurrence_dates if d >= reference_date and not _is_excluded(d, block)]

        slots: list[ProjectedSlot] = []
        for occ_date in occurrence_dates:
            slots.extend(self._slots_for_date(occ_date, block=block))

        return slots

    def _recurrent_occurrence_dates(
        self,
        block: "AvailabilityBlock",  # noqa: F821
        *,
        series_anchor: date,
        open_ended_until: date,
    ) -> list[date]:
        """Raw rrule occurrence dates for a recurrent block (single rrule builder).

        Shared by _project_recurrent (slot materialization) and
        occurrence_dates_in_range (D3-C paint projection) — the ONLY place the
        recurrence rrule is built.

        D3-F extension: uses block.days_of_week (list[int]) and block.interval (int).
        Legacy blocks (migrated): days_of_week=[day_of_week], interval=1|2 — identical
        projection to pre-D3-F (RN-D3F-3 invariant).

        Maps via block.interval (weeks):
          - interval=1 → WEEKLY interval=1
          - interval=2 → WEEKLY interval=2 (biweekly)
          - interval=N → WEEKLY interval=N (custom)

        byweekday: block.days_of_week (list[int], 0=Mon..6=Sun).

        Maps end_condition_kind:
          - end_date   → until=datetime(end_date 23:59:59, UTC) — inclusive (SC-D3C-3)
          - occurrences → count = occurrences × len(days_of_week): N COMPLETE cycles
            of the pattern (each repetition includes ALL selected weekdays — Chris
            ratified 2026-06-15). Single-day → N. Multi-day → N weeks complete.
          - open_ended → until=open_ended_until 23:59:59 UTC

        Args:
            block: The recurrent AvailabilityBlock (D3-F: days_of_week + interval).
            series_anchor: Date the series anchors at — dtstart is the earliest
                first-occurrence date across all days_of_week on or after this
                date (count consumption and biweekly parity derive from dtstart).
            open_ended_until: Horizon date for open_ended blocks.

        Returns:
            Sorted occurrence dates from the anchor onward (callers filter further).
        """
        days_of_week = block.days_of_week
        if not days_of_week:
            # Fallback to legacy single-day field (safety net for unconverted legacy data)
            assert block.day_of_week is not None, "recurrent block must have days_of_week or day_of_week"
            days_of_week = [block.day_of_week]

        interval = block.interval if block.interval >= 1 else 1

        # dtstart: earliest first-occurrence across all weekdays on or after series_anchor.
        # For multi-day rrule, dtstart controls count consumption and biweekly parity
        # for the entire series. We anchor at the earliest weekday >= series_anchor.
        dtstart_date = min(_next_weekday_from(series_anchor, weekday=d) for d in days_of_week)

        rrule_kwargs: dict[str, object] = {
            "freq": WEEKLY,
            "interval": interval,
            "byweekday": days_of_week,
            "dtstart": datetime.combine(dtstart_date, time(0, 0), tzinfo=timezone.utc),
        }

        if block.end_condition_kind == "end_date":
            assert block.end_date is not None, "end_date condition requires end_date field"
            rrule_kwargs["until"] = datetime.combine(block.end_date, time(23, 59, 59), tzinfo=timezone.utc)

        elif block.end_condition_kind == "occurrences":
            assert block.occurrences and block.occurrences >= 1, "occurrences must be >= 1"
            # bug7 round-6 (Chris ratified 2026-06-15): "Después de N repeticiones" =
            # N COMPLETE cycles of the weekly pattern — each repetition includes ALL
            # selected weekdays. rrule count is per-individual-occurrence, so
            # N cycles = N × len(days_of_week). Single-day → N×1 = N (unchanged);
            # multi-day → every week complete (no half-week tail). Previously count=N
            # gave N TOTAL occurrences → Mar+Jue ×"3" left week 2 with only Mar.
            rrule_kwargs["count"] = block.occurrences * len(days_of_week)

        elif block.end_condition_kind == "open_ended":
            rrule_kwargs["until"] = datetime.combine(open_ended_until, time(23, 59, 59), tzinfo=timezone.utc)

        else:
            logger.warning(
                "unknown_end_condition_kind",
                end_condition_kind=block.end_condition_kind,
                block_id=str(block.id),
            )
            return []

        occurrence_rule = rrule(**rrule_kwargs)  # type: ignore[arg-type]
        return sorted({dt.date() for dt in occurrence_rule})

    def _slots_for_date(
        self,
        slot_date: date,
        *,
        block: "AvailabilityBlock",  # noqa: F821
    ) -> list[ProjectedSlot]:
        """Generate slots for a single date from start_time to end_time.

        Uses UTC timezone. Each slot is self._duration long.
        Block's start_time and end_time are treated as UTC (tenant tz conversion
        is handled by the scheduling display layer, not the projection layer).
        """
        slots: list[ProjectedSlot] = []
        cursor = datetime.combine(slot_date, block.start_time, tzinfo=timezone.utc)
        end_dt = datetime.combine(slot_date, block.end_time, tzinfo=timezone.utc)

        while cursor + self._duration <= end_dt:
            slot_end = cursor + self._duration
            slots.append(
                ProjectedSlot(
                    id=uuid4(),
                    tenant_id=block.tenant_id,
                    clinic_id=block.clinic_id,
                    doctor_id=block.doctor_id,
                    block_id=block.id,
                    slot_date=slot_date,
                    start_ts=cursor,
                    end_ts=slot_end,
                    has_confirmed_appointment=False,
                )
            )
            cursor = slot_end

        return slots


# ── Utility ───────────────────────────────────────────────────────────────────


def _next_weekday_from(from_date: date, *, weekday: int) -> date:
    """Return the first date >= from_date that falls on weekday (0=Monday..6=Sunday)."""
    days_ahead = weekday - from_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return from_date + timedelta(days=days_ahead)
