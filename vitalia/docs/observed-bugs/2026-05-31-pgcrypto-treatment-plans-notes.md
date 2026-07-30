# Observed bug — treatment_plans.notes not pgcrypto BYTEA

**Observed during:** vitalia-fase2-lisa-doctores autonomous build (T-BE-2 gate run).
**Origin:** CRM story (migration 035 `vitalia_crm_phi_base_tables`, commit 540249cb) — NOT the doctor story.
**Symptom:** arch fitness `tests/architecture/test_pgcrypto_phi_columns.py::test_treatment_plans_notes_is_bytea` FAILS — `treatment_plans.notes` declared as plain column, test expects pgcrypto BYTEA (HIPAA-lite at-rest encryption).
**Scope discipline:** out-of-scope for lisa-doctores (different module/table). NOT fixed inline (non-egoísmo clause). Doctor-story pgcrypto columns (vitalia_doctors dni/email/phone/credential) DO pass.
**Suggested follow-up:** bugfix story on CRM module to encrypt treatment_plans.notes (HIPAA-lite gap).
