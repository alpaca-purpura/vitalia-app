# Vitalia — HIPAA-lite Compliance

**Overlay:** extiende `.claude/rules/` raíz Luana platform (refuerza `tenant-isolation.md` + `auditor-downstream-regression.md`).
**Brand:** vitalia (Salud + Bienestar — clínicas médicas, dentales, estéticas)
**Scope:** salvaguardas defensivas para datos médicos sensibles. NO somos HIPAA covered entity full (sin BAA con AWS/Postgres provider, sin certificación), pero aplicamos best-practices HIPAA + compliance LatAm sobre PHI.

## Regla cardinal

Toda lectura/escritura/transmisión de PHI (Protected Health Information) MUST cumplir las 4 obligaciones simultáneamente: (1) tenant + clinic dual filter, (2) audit log row, (3) sanitization en traces, (4) cifrado in-transit + at-rest. Sin excepción.

## PHI fields canónicos (lista SSoT para PII scanner vitalia)

Campos considerados PHI en vitalia — escaneados por `core/luana-core-observability/src/luana_core_observability/recording/sanitization.py` con perfil `compliance_level: hipaa_lite`:

- Identidad paciente: `patient.name`, `patient.dni`, `patient.cuit`, `patient.date_of_birth`, `patient.phone`, `patient.email`, `patient.address`
- Datos clínicos: `diagnosis`, `treatment_plan`, `medication`, `dosage`, `allergies`, `symptoms`, `medical_notes`, `lab_results`, `vital_signs`
- Imagenología: `imaging_url`, `xray_filename`, `ultrasound_report`
- Histórico: `previous_treatments`, `family_history`, `surgical_history`

Cualquier campo nuevo con semántica médica → agregar a esta lista mismo PR + actualizar `vitalia/backend/src/modules/vitalia/compliance/domain/phi_fields.py`.

## Constraints

### Encryption at rest
- Postgres vitalia DB DEBE tener encryption at rest (disk-level via cloud provider o `pgcrypto` extension para columnas PHI sensitive).
- Tabla `patient_medical_records` columnas `diagnosis`, `treatment_plan`, `medical_notes` → `pgcrypto` symmetric encryption con KEK rotada anualmente.
- Backups DB encrypted con key separada (no la misma KEK runtime).

### Encryption in transit
- TODAS las APIs vitalia bajo HTTPS estricto (no http fallback dev en staging+prod).
- Webhooks de integraciones (tools, payment gateway, lab providers) validados con HMAC signature + timestamp window 5min.
- Inter-service comm dentro K8s con mTLS habilitado.

### Audit log
- Tabla `audit_log` con columns `(id, tenant_id, clinic_id, user_id, action, resource_type, resource_id, from_ip, user_agent, timestamp, payload_redacted)`.
- TODA lectura/modificación de PHI registra row. NO opcional. NO async fire-forget (sync write antes response).
- Retention audit_log: 10 años mínimo (regulación LatAm health). Particionada por mes.

### Retention policy PHI
- PHI retenida 10 años post último acceso paciente (regulación Ley 25.326 Argentina, Ley 1581 Colombia, Ley 19.628 Chile, Ley 29733 Perú, LGPD Brasil).
- Cron `audit_log_retention_sweep_monthly` (en `vitalia/backend/src/modules/vitalia/_shared/workers/jobs/`, ARQ mensual 1º 02:00 UTC; stub — aún no implementado): detecta `last_access_at > 10y` → flag para anonymize.
- Anonymization: replace identifiers con hash determinístico, mantener stats agregadas. Hard delete solo bajo derecho al olvido explícito.

### Access control (RBAC strict)
- Roles permitidos PHI: `doctor`, `nurse`, `admin_clinic`. Otros (marketing, sales) NUNCA ven PHI.
- Paciente role `patient` ve SOLO su propia data (filter `patient_id == current_user.patient_id`).
- Decorator `@require_phi_access(roles=["doctor","nurse","admin_clinic"])` en TODOS endpoints PHI.

### Tenant isolation refuerzo
- Además de `tenant_id` (raíz rule), vitalia agrega `clinic_id` como **segundo filter obligatorio** en queries PHI: `.where(Model.tenant_id == tenant_id, Model.clinic_id == clinic_id)`.
- Arch fitness test `vitalia/backend/tests/architecture/test_phi_dual_filter.py` enforces.

### Voice patterns en sales_agent vitalia
- NUNCA discutir diagnósticos/resultados por canales no-encriptados (WhatsApp tier free, SMS).
- Si paciente pregunta resultados → bot deriva a portal seguro autenticado: "Por seguridad, los resultados los podés ver en tu portal: {link}".
- Persona vitalia carga rule `medical_results_only_in_portal: true` que bloquea tool `send_medical_summary` por chat.

### PII sanitization en traces
- `sanitize_payload(payload, compliance_level="hipaa_lite")` DEBE omitir TODOS PHI fields antes logging/observability/cost recording.
- NUNCA loguear nombre+diagnóstico mismo trace event (re-identifiable aún si individuales OK).
- Trace events que necesitan referencia paciente usan `patient_id` hash (UUID), no nombre.

### Compliance gates
- `core/luana-core-compliance/` (engine core) activado en vitalia con perfil `compliance_level: hipaa_lite` en `vitalia/config/brand.yaml`.
- `ComplianceService.validate_outbound_message(message, channel)` bloquea mensajes con PHI por canales no-encriptados.

## Tests requeridos

Todo PR vitalia tocando tablas/módulos `patient_*`, `medical_*`, `treatment_*`, `prescription_*`, `appointment_*` MUST incluir tests que verifiquen:

1. **PHI no leaked en API response:** assertion explícita response body NO contiene fields PHI cuando role no autorizado.
2. **Audit log row creado:** después request PHI, query `audit_log` retorna row con action+user+timestamp esperados.
3. **Cross-tenant query bloqueada:** request con `tenant_id_A` + `clinic_id_B` (de tenant diferente) retorna 404, no leak.
4. **Cross-clinic query bloqueada:** request con `tenant_id_A` + `clinic_id_X` siendo user de `clinic_id_Y` mismo tenant → 403.
5. **Sanitize en traces:** trace event capturado no contiene PHI fields.
6. **Channel guard:** `send_medical_summary` por WhatsApp free → ComplianceService raise BlockedChannelError.

## Anti-patterns prohibidos

- PHI en URLs (GET query params) — usa POST body siempre. Ej: `GET /patients?dni=12345678` PROHIBIDO.
- PHI en logs sin `sanitize_payload`. Ej: `logger.info(f"Patient {patient.name}...")` PROHIBIDO.
- PHI en email plaintext (notification debe linkear portal, no incluir diagnóstico body).
- PHI en `localStorage` / `sessionStorage` frontend — solo IDs hash, fetch on-demand server-side.
- Cifrado simétrico app-level "rolled-our-own" — usar `pgcrypto` o cloud KMS.
- Audit log async sin confirmation antes response — write sync mandatorio.
- Skip dual filter (`clinic_id`) "porque single-tenant clinic" — siempre, sin excepción.
- Reusar audit_log de raíz Luana — vitalia tiene su propio audit_log con campos extra (clinic_id, payload_redacted).

## Referencias

- Raíz: `.claude/rules/tenant-isolation.md`, `.claude/rules/auditor-downstream-regression.md`, `.claude/rules/anti-duplication.md`
- Brand config: `vitalia/config/brand.yaml` (compliance_level: hipaa_lite)
- Brand module home: `vitalia/backend/src/modules/vitalia/`
- PHI fields SSoT: `vitalia/backend/src/modules/vitalia/compliance/domain/phi_fields.py`
- Compliance engine: `core/luana-core-compliance/`
- Sanitization: `core/luana-core-observability/src/luana_core_observability/recording/sanitization.py`
- Regulaciones: Ley 25.326 (AR), LGPD (BR), Ley 1581 (CO), Ley 19.628 (CL), Ley 29733 (PE), HIPAA §164.312 (US reference best-practice)
