---
module: patients
brand: vitalia
last_updated: 2026-05-20
---

# patients — Pacientes + historial médico

CRUD de pacientes con tenant_id enforcement obligatorio. Upload de PDF historial médico → extracción 4-wave vision-based via `MedicalKBExtractor` → estructura en `medical_history_model`. PII masking obligatorio (phone, email, name_last_initial).

## Capabilities

<!-- auto-list:start -->
- `patient-records-medical-history` (live)
- `nps-tracking` (live · 2026-05-20)
<!-- auto-list:end -->
