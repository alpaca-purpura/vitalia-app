# luana-core-commercial-calendar

Brand-agnostic commercial calendar events package for the Luana Platform.

## Lift origin

Lifted verbatim from `AISALESHT/backend/src/modules/commercial_calendar/` (Story 3 — 2026-05-11).
Tests lifted from `AISALESHT/backend/tests/modules/commercial_calendar/`.

## Key exports

- `luana_core_commercial_calendar.domain.calendar_event.CalendarEvent` — aggregate root
- `luana_core_commercial_calendar.infrastructure.repositories.calendar_event_repository.CalendarEventRepository`
- `luana_core_commercial_calendar.api.events` — FastAPI router

## Deferred

- `copilot_provider/` — deferred to Story 6 (copilot lift). Imports `copilot.domain.ports`.

## Version

0.0.1-alpha (Story 3 lift)
