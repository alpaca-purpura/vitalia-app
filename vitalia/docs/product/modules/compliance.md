---
module: compliance
brand: vitalia
last_updated: 2026-05-20
---

# compliance — HIPAA-lite LATAM posture

PII scanner pre-persistencia + PII masking en response models + audit log de operaciones sensibles + UI dashboard + export CSV + consent records. NO es hipaa_full (D7 ratificado: sin BAA, sin stripe_healthcare).

Doc completa: `vitalia/docs/domains/compliance.md`.

Post Slice 1 (2026-05-18): arquitectura defensiva architecturally enforced — PhiRepositoryBase dual filter, AuditLogRepository sync write, channel guard, RBAC decorator, encryption-at-rest pgcrypto.

## Capabilities

<!-- auto-list:start -->
- `compliance-hipaa-lite-audit` (live)
- `vitalia-hipaa-lite-defensive-stack` (live)
- `whatsapp-template-registry` (live · 2026-05-20)
<!-- auto-list:end -->
