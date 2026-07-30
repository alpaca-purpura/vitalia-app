# luana-core-events

**Version:** 0.0.1-alpha  
**Lift origin:** `AISALESHT/backend/src/shared/domain_events/`  
**Lift commit:** `0ba6a69` (feat(luana-core-events): lift domain-events outbox package)

## Overview

Transactional outbox pattern for reliable domain event delivery. Ensures
events are persisted atomically with business data before being dispatched
to consumers.

## Key exports

- `luana_core_events.outbox.application.event_bus_adapter.EventBusAdapter` — publishes events via outbox
- `luana_core_events.outbox.application.outbox_dispatcher.OutboxDispatcher` — background dispatcher
- `luana_core_events.outbox.infrastructure.outbox_repository_impl.OutboxRepositoryImpl` — persistence
- `luana_core_events.outbox.domain.outbox_repository.OutboxRepository` — domain interface
- `luana_core_events.outbox.infrastructure.models.DomainEventOutboxModel` — SQLAlchemy model
