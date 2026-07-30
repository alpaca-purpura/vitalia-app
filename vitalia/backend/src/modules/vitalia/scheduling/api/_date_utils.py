# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""Date range utilities for the Agenda API.

Translates view+date parameters into (date_from, date_to) UTC datetime tuples.

Views:
  dia    — single day: [date 00:00:00, date 23:59:59.999999] UTC
  semana — ISO week containing date: [Monday 00:00, Sunday 23:59] UTC
  mes    — calendar month: [1st 00:00, last-day 23:59] UTC

All datetimes are timezone-aware UTC (DateTime(timezone=True) contract).
"""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta, timezone


def compute_date_range(*, view: str, date_str: str) -> tuple[datetime, datetime]:
    """Return (date_from, date_to) UTC datetimes for the given view and anchor date.

    Args:
        view: One of 'dia', 'semana', 'mes'. Unknown views fall back to 'dia'.
        date_str: ISO date string in YYYY-MM-DD format (anchor date).

    Returns:
        Tuple of (date_from, date_to) — both timezone-aware UTC datetimes.
        date_from is 00:00:00 UTC of the range start.
        date_to   is 23:59:59.999999 UTC of the range end.

    Raises:
        ValueError: If date_str is not a valid ISO date.
    """
    anchor: date = date.fromisoformat(date_str)

    if view == "semana":
        # ISO week: Monday=0 … Sunday=6
        monday = anchor - timedelta(days=anchor.weekday())
        sunday = monday + timedelta(days=6)
        range_start = monday
        range_end = sunday
    elif view == "mes":
        first_day = anchor.replace(day=1)
        last_day_num = calendar.monthrange(anchor.year, anchor.month)[1]
        last_day = anchor.replace(day=last_day_num)
        range_start = first_day
        range_end = last_day
    else:
        # Default: "dia" — single day
        range_start = anchor
        range_end = anchor

    date_from = datetime(
        range_start.year,
        range_start.month,
        range_start.day,
        0,
        0,
        0,
        tzinfo=timezone.utc,
    )
    date_to = datetime(
        range_end.year,
        range_end.month,
        range_end.day,
        23,
        59,
        59,
        999999,
        tzinfo=timezone.utc,
    )
    return date_from, date_to
