# luana-core-crm

Version: 0.0.1-alpha

Lift of `backend/src/modules/crm/` from AISALESHT (Nicolify monorepo).

This package provides the CRM engine for Luana Platform: customer data platform,
lead management, lifecycle tracking, NPS surveys, referrals, and sales records.
Multi-tenant by design — all queries filter by `tenant_id`.

## Lift origin

Source: `/home/chris/AISALESHT/backend/src/modules/crm/`
Tests: `/home/chris/AISALESHT/backend/tests/modules/crm/`

## Key exports

- `luana_core_crm.domain` — Customer, Lead, Sale, NPS, Referral, Scoring entities
- `luana_core_crm.application.services` — CustomerService, LeadService, SaleService, NpsService, ReferralService, LifecycleService
- `luana_core_crm.infrastructure` — SQLAlchemy models + repositories
- `luana_core_crm.api` — FastAPI routers for CRM endpoints

## Deferrals

- `copilot_provider/` → Story 6 (imports `luana_core_copilot.domain.ports`)
- `api/contacts.py` + `application/services/contact_query_service.py` → Story 8 (imports `luana_core_campaigns`)
- `tests/test_contacts_api.py` → Story 8 (tests deferred contacts.py)
