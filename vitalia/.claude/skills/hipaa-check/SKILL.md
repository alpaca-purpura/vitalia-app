---
name: hipaa-check
description: Checklist corta para auditar que un cambio de código Vitalia cumple las salvaguardas PHI de la rule hipaa-lite (dual filter tenant+clinic, audit log, encryption, sanitization en traces). Usá cuando toques tablas/módulos patient_*, medical_*, treatment_*, prescription_*, appointment_* o cualquier lectura/escritura/transmisión de PHI. Triggers 'chequeá PHI', 'hipaa check', 'auditá compliance', 'esto cumple hipaa-lite'.
version: 0.1.0
model: opus
clase: skill
contract:
  caja: true
  clase: skill
  arquetipo: pipeline
  perfil_harness: T1
  fase: verificacion-de-marca
  estado: "cambio-propuesto -> cambio-verificado"
  why: "Que ningún cambio de Vitalia que toque PHI llegue a merge sin que las 4 salvaguardas cardinales de hipaa-lite estén verificadas una por una, con veredicto escrito y auditable."
  capabilities:
    - id: alcance-phi
      what: "decide si el diff toca PHI (campos de phi_fields.py o tablas patient_/medical_/treatment_/prescription_/appointment_)"
      success: "el veredicto declara APLICA o NO-APLICA nombrando el campo/tabla concreto que lo dispara"
    - id: cuatro-salvaguardas
      what: "recorre las 4 salvaguardas cardinales (dual filter · audit log · encryption · sanitization) ítem por ítem"
      success: "cada ítem queda marcado PASS / FAIL / N-A — ninguno sin marcar"
    - id: veredicto-accionable
      what: "emite el veredicto con lo que falta por ítem en FAIL"
      success: "todo FAIL nombra archivo + qué salvaguarda incumple; un solo FAIL HARD ⇒ veredicto NO-CONFORME"
  constraints:
    - "un FAIL en cualquier ítem HARD ⇒ NO-CONFORME (las 4 salvaguardas se exigen simultáneamente, no por mayoría)"
    - "no marca PASS por inspección de nombres: cita la línea/archivo que lo sostiene"
    - "no evalúa PHI a partir del texto del PR — lee el diff"
  non_goals:
    - "no arregla el código (reporta; el fix es de quien construyó)"
    - "no reemplaza los arch fitness tests — los complementa donde no llegan"
    - "no cubre gates de marca no-PHI (shell-feature, mockup) — ésos son otras rules"
  necesita:
    - art: "diff del cambio Vitalia a verificar"
      de: "usuario"
      requerido: true
    - art: "hipaa-lite — doctrina PHI (regla cardinal + constraints + anti-patterns)"
      de: "base:hipaa-lite"
      requerido: true
    - art: "vitalia/backend/src/modules/vitalia/compliance/domain/phi_fields.py — lista canónica de campos PHI"
      de: "terceros:codigo-vitalia"
      requerido: true
    - art: "vitalia/backend/tests/architecture/ — arch fitness tests PHI"
      de: "terceros:codigo-vitalia"
      requerido: false
  entrega:
    - art: "veredicto PHI del cambio (un archivo por verificación, {YYYY-MM-DD}-{slug}.md)"
      path: "docs/compliance/phi-checks/"
      escritor_unico: true
  ruta:
    - a: "humano"
  gate:
    tipo: parcial
    detalle: "Parte del checklist tiene enforcement mecánico real (6 arch fitness tests en vitalia/backend/tests/architecture/: test_phi_dual_filter · test_no_phi_in_url_params · test_audit_log_sync_write · test_audit_log_row_per_phi_endpoint · test_pgcrypto_phi_columns · test_growth_studio_event_no_phi). El resto de los ítems (RBAC, channel guard, no-PII-en-logs, tests incluidos) queda a juicio del que ejerce la caja — sin enforcer determinista."
    aceptacion:
      - given: "un diff de Vitalia que toca una tabla patient_* o un campo de phi_fields.py"
        when: "se ejerce el checklist completo"
        then: "los 6 arch tests PHI corren en verde Y cada ítem del checklist queda marcado PASS/FAIL/N-A en el veredicto escrito"
      - given: "un diff con una query PHI sin clinic_id"
        when: "se ejerce el checklist"
        then: "el veredicto es NO-CONFORME y nombra el archivo + la salvaguarda 1"
    evidencia: "SIN MEDIR — la mitad mecánica corre (`cd vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/ -k phi -q`); la efectividad de la caja no tiene corridas medidas ni evals. No promover sin medición."
  handoff:
    cuando: "veredicto escrito — siempre, y de inmediato si cualquier ítem HARD dio FAIL"
    a: "humano"
---

# hipaa-check — auditoría PHI de un cambio (rule hipaa-lite operacionalizada)

Checklist bloqueante para todo cambio Vitalia que lea/escriba/transmita PHI. Ejercela ANTES de dar por bueno el diff. SSoT: `vitalia/.claude/rules/hipaa-lite.md`. La regla cardinal exige las 4 salvaguardas **simultáneamente** — una falla ⇒ el cambio NO cumple.

## Cuándo

Precondición de entrada (`cambio-propuesto`): hay un diff de Vitalia listo para verificar y toca — o podría tocar — PHI: campos de `phi_fields.py` o tablas `patient_* / medical_* / treatment_* / prescription_* / appointment_*`. Si el diff no toca PHI, la caja cierra en NO-APLICA (eso también es un veredicto: se escribe).

## Pasos

1. **Determinar alcance.** Identificá si el diff toca PHI. Si no toca → veredicto NO-APLICA, nombrando qué revisaste.
2. **Recorrer las 4 salvaguardas** de abajo. Cada ítem es PASS / FAIL / N-A, citando archivo + línea que lo sostiene.
3. **Correr la mitad mecánica:** `cd vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/ -k phi -q`.
4. **Escribir el veredicto** en `vitalia/docs/compliance/phi-checks/{YYYY-MM-DD}-{slug}.md` (la entrega de esta caja): alcance, tabla ítem→PASS/FAIL/N-A, salida de los arch tests, y para cada FAIL qué falta. Cualquier FAIL en un ítem HARD ⇒ **NO-CONFORME**.
5. **Handoff a humano** con el veredicto (`cambio-verificado`).

## Checklist (4 salvaguardas cardinales)

### 1 · Dual filter tenant + clinic (HARD)
- [ ] Toda query PHI filtra `tenant_id` **y** `clinic_id`: `.where(Model.tenant_id == tenant_id, Model.clinic_id == clinic_id)` — incluido `get_by_id`.
- [ ] Repo PHI hereda `PhiRepositoryBase` (no query suelta "porque single-clinic tenant").
- [ ] Sin PHI en URL / query params (`GET ?dni=...` prohibido) — siempre POST body.

### 2 · Audit log (HARD)
- [ ] Toda lectura/modificación de PHI escribe una fila en `audit_log` (`tenant_id, clinic_id, user_id, action, resource_type, resource_id, from_ip, user_agent, timestamp, payload_redacted`).
- [ ] Write **sync antes de la response** — nunca `async` fire-and-forget.

### 3 · Encryption at-rest + in-transit (HARD)
- [ ] Columnas PHI sensibles (`diagnosis`, `treatment_plan`, `medical_notes`) bajo `pgcrypto` — nunca cifrado app-level "rolled-our-own".
- [ ] Endpoint bajo HTTPS estricto; webhooks con HMAC + ventana de timestamp.

### 4 · Sanitization en traces / observabilidad (HARD)
- [ ] Payloads de traza/LLM pasan por `sanitize_payload(payload, compliance_level="hipaa_lite")` ANTES de persistir.
- [ ] Nunca nombre + diagnóstico en el mismo trace event (re-identificable); referencias por `patient_id` hash, no por nombre.
- [ ] Sin PII/PHI en logs (`logger.info(f"Patient {name}...")` prohibido) ni en `localStorage`/`sessionStorage` del FE.

## Extras que la rule exige (verificar si el cambio los toca)
- [ ] RBAC: endpoints PHI decorados `@require_phi_access(roles=["doctor","nurse","admin_clinic"])`; rol `patient` ve solo su propia data.
- [ ] `send_medical_summary` bloqueado por canales no-encriptados (WhatsApp free / SMS) vía `ComplianceService`.
- [ ] Campo PHI nuevo ⇒ agregado a `phi_fields.py` **y** a la lista SSoT de la rule en el mismo PR.
- [ ] Tests incluidos: PHI no leaked en response, audit row creado, cross-tenant 404, cross-clinic 403, sanitize en trace, channel guard.

## Guardarraíles

- **Las 4 salvaguardas son simultáneas.** No hay veredicto CONFORME con un HARD en FAIL, por chico que parezca el diff.
- **Verde mecánico ≠ conforme.** Los 6 arch tests cubren parte del checklist; los ítems sin enforcer (RBAC, channel guard, logs, tests incluidos) se verifican a mano o quedan explícitamente N-A con razón.
- **No marcar PASS sin evidencia.** Un ítem sin archivo/línea que lo sostenga se marca FAIL, no PASS optimista.
- **La caja no arregla.** Reporta y hace handoff; el fix vuelve a quien construyó el cambio.

## Referencias
- `vitalia/.claude/rules/hipaa-lite.md` — SSoT de la doctrina (regla cardinal + constraints + anti-patterns)
- `vitalia/backend/src/modules/vitalia/compliance/domain/phi_fields.py` — lista canónica de campos PHI
- `core/luana-core-observability/.../recording/sanitization.py` — `sanitize_payload`
- `.claude/rules/tenant-isolation.md` — filtro tenant raíz (esta lo refuerza con `clinic_id`)
