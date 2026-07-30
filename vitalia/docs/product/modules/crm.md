---
module: crm
brand: vitalia
last_updated: 2026-06-11
---

# crm — Patient + Lead management

Módulo CRM Vitalia: Patient (PHI entity con dual filter tenant_id + clinic_id, extiende PhiRepositoryBase) + Lead (non-PHI entity con single tenant filter) + services con `@require_phi_access` RBAC + 4 endpoints REST.

Slice 1 (2026-05-18) introdujo scaffold con raw SQL `text()` (ORM models pending Slice 2). PatientService restricts `opt_out` a admin_clinic role only.

Adrián-embudo (2026-06-11) EXTIENDE el módulo con el funnel clínico de 6 etapas sobre Lead: FunnelService/ScoreService/DiagnoseService + transición con optimistic lock (`version`→409) + auto-freeze/Recuperar + funnel fields persistidos en create (stage/channel/service_interest/estimated_value/currency).

## Capabilities

<!-- auto-list:start -->
- `vitalia-crm-scaffold-slice-1` (live · extended 2026-05-20)
- `crm-consent-optout` (live · 2026-05-20)
- `adrian-embudo` (live · 2026-06-11)
<!-- auto-list:end -->
