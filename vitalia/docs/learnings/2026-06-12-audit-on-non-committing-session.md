---
brand: vitalia
date: 2026-06-12
slug: audit-on-non-committing-session
promotable: candidate
applies_to_other_brands_potentially: [vitalia, comunify, nicolify]
target_core_package: core/luana-core-observability (o arch-fitness guard cross-brand)
---

# Audit row sobre sesión non-committing = rollback silencioso (2ª recurrencia)

**Qué aprendimos:** un endpoint que escribe una fila de auditoría con `AsyncAuditWriter.write()`
(INSERT sin commit — by design, el unit-of-work owner commitea) montado sobre `get_async_session`
(non-committing) produce **HTTP 200 + structlog "audit_log_async_written" + CERO filas en DB**:
si los repos commitean sus propios writes antes, el INSERT del audit queda en una transacción
fresca que se descarta al cerrar la sesión. El verde unitario no lo ve (suites mockean repos/audit
y assertan "el método fue llamado"). Solo lo caza una verificación que **cuenta filas reales**.

**Origen:** story `vitalia-fase2-config-cuenta` T-2 (C9-1, auditor-backend live-confirmed:
PATCH 200 + 0 rows vs 843 audit rows de otras surfaces). **2ª recurrencia** — el mismo bug-class
se arregló antes para CRM creando `get_async_session_committing` (src/db.py docstring lo documenta).

**Why:** la durabilidad del audit es un invariante HIPAA-lite (hipaa-lite.md § Audit log: "NO
opcional · sync write antes response") — y es exactamente el tipo de invariante que el verde
mockeado enmascara. La structlog line NO es evidencia; la fila commiteada SÍ.

**How to apply:**
1. Endpoint que escribe audit → SIEMPRE `get_async_session_committing` (o commit explícito post-write)
   + repos del flujo con caller-owned commit (unit-of-work atómico).
2. Todo surface con audit obligatorio → 1 integration test real-session que asserta
   `COUNT(audit_log WHERE action=...) ≥ 1` post-request (patrón: `test_account_audit_durability.py`).
3. Candidato a **arch-fitness guard** cross-brand: detectar routers que inyectan AsyncAuditWriter
   sobre `get_async_session` non-committing (el sub-auditor ya capturó la proposal en harness-backlog).
