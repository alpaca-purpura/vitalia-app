# Cumplimiento normativo — Vitalia Health Platform

> **Versión:** 1.0.0 · **Actualizado:** 2026-05-14
>
> Este documento describe el marco de cumplimiento de Vitalia. Está redactado
> en español neutro LatAm (tuteo) para clínicas de Argentina, Chile, México,
> Brasil, Colombia y Perú.

---

## Índice

1. [Distinción HIPAA-lite vs HIPAA completo](#1-distinción-hipaa-lite-vs-hipaa-completo)
2. [Marco legal LatAm por país](#2-marco-legal-latam-por-país)
3. [Retención del registro de auditoría (7 años)](#3-retención-del-registro-de-auditoría-7-años)
4. [Flujo de captura de consentimiento](#4-flujo-de-captura-de-consentimiento)
5. [Verificación HMAC de URLs de consentimiento](#5-verificación-hmac-de-urls-de-consentimiento)
6. [Patrones de detección de datos personales (PII)](#6-patrones-de-detección-de-datos-personales-pii)
7. [Derechos de exportación y eliminación de datos](#7-derechos-de-exportación-y-eliminación-de-datos)
8. [Aislamiento multi-tenant](#8-aislamiento-multi-tenant)

---

## 1. Distinción HIPAA-lite vs HIPAA completo

### 1.1 ¿Qué es HIPAA?

HIPAA (*Health Insurance Portability and Accountability Act*, EE.UU. 1996) exige a las
*covered entities* y sus *business associates* controles técnicos, administrativos y físicos
exhaustivos para proteger la Información de Salud Protegida Electrónica (**ePHI**).

**Vitalia NO es una plataforma HIPAA compliant** en el sentido legal estadounidense. Si tu
clínica opera en EE.UU. y está sujeta a HIPAA, necesitas controles adicionales fuera del
alcance de Story 11 (ver Story 11.bis).

### 1.2 ¿Qué significa `compliance_level=hipaa_lite`?

Vitalia implementa un nivel de cumplimiento que llamamos **HIPAA-lite**. Se inspira en los
principios de HIPAA pero está dimensionado para clínicas LatAm bajo legislación local:

| Control | HIPAA completo (EE.UU.) | Vitalia HIPAA-lite (LatAm) |
|---|---|---|
| BAA (*Business Associate Agreement*) | Obligatorio con cada proveedor | No aplica (legislación LatAm) |
| ePHI en tránsito | TLS 1.2+ + FIPS 140-2 | TLS 1.3 + cifrado en reposo (AES-256) |
| Controles de acceso | RBAC + MFA + revisión semestral | RBAC + MFA (Clerk App #2) |
| Registro de auditoría | Indefinido o 6 años mínimo | **7 años** (sobrecumple requerimiento) |
| `contains_phi=false` en metadata pagos | Requerido para Stripe Healthcare flag | Cumplido — no se envía PHI a gateways |
| Diagnóstico por IA | Prohibido sin supervisión médica | Guardrail activo (`medical_safety_no_diagnosis`) |
| Prescripción por IA | Prohibido | Guardrail activo (`medical_safety_no_prescription`) |
| Notificación de brechas | 60 días | Notificación inmediata (mejor práctica) |

### 1.3 Metadato `compliance_level` en la plataforma

Cada tenant de Vitalia tiene el campo `compliance_level=hipaa_lite` y `contains_phi=false`
persistido en su perfil de clínica. Esto garantiza:

- Los gateways de pago (MercadoPago, Stripe Connect) **nunca** reciben PHI en metadatos.
- Los logs de observabilidad redactan automáticamente campos sensibles.
- La exportación CSV del audit log enmascara emails y teléfonos.

```python
# Ejemplo: metadata limpia enviada a MercadoPago
payment_metadata = {
    "booking_id": str(booking.id),       # UUID opaco — no PHI
    "tenant_id": str(tenant_id),         # UUID opaco — no PHI
    "offer_type": "dental_implant",      # categoría — no PHI
    # ❌ NUNCA: patient_name, patient_email, diagnosis, medication
}
```

---

## 2. Marco legal LatAm por país

Vitalia se adhiere a las leyes de protección de datos personales del país de la clínica.
El campo `country` del perfil de clínica determina qué ley aplica.

### 2.1 Argentina — Ley 25.326 Protección de Datos Personales

**Vigencia:** Enero 2001 · **Autoridad:** AAIP (Agencia de Acceso a la Información Pública)

Principios clave que Vitalia implementa:

- **Consentimiento previo e informado**: capturado antes de almacenar datos del paciente.
- **Finalidad determinada**: los datos se usan solo para la gestión de la cita/tratamiento.
- **Acceso y rectificación**: el paciente puede solicitar sus datos vía `GET /api/v1/vitalia/patient/data-export`.
- **Seguridad**: TLS en tránsito + AES-256 en reposo.
- **Datos sensibles**: la Ley 25.326 Art. 7 considera *datos sensibles* la información de
  salud. Requiere consentimiento expreso. El flujo de consentimiento de Vitalia captura
  firma explícita antes de cualquier procedimiento.

**Retención de registros médicos AR:** el Código Civil exige conservar historiales clínicos
10 años. Vitalia retiene el audit log **7 años** mínimo, alineado con esta práctica.

### 2.2 Brasil — LGPD (Lei Geral de Proteção de Dados, Lei 13.709/2018)

**Vigencia:** Agosto 2020 · **Autoridad:** ANPD

Bases legales que Vitalia utiliza:

- **Art. 7, III — Cumplimiento de obligación legal**: retención de registros médicos.
- **Art. 7, V — Ejecución de contrato**: prestación del servicio de agenda/tratamiento.
- **Art. 11, II, a — Datos de saúde**: consentimiento específico y destacado requerido.

Derechos del titular (paciente) que Vitalia soporta:

| Derecho (Art. 18) | Endpoint Vitalia |
|---|---|
| Confirmação de tratamento | `GET /api/v1/vitalia/patient/data-summary` |
| Acesso | `GET /api/v1/vitalia/patient/data-export` |
| Correção | `PATCH /api/v1/vitalia/patient/profile` |
| Anonimização / eliminação | `DELETE /api/v1/vitalia/patient/data` (soft delete + anonimización) |
| Portabilidade | `GET /api/v1/vitalia/patient/data-export?format=json` |
| Revogação do consentimento | `POST /api/v1/vitalia/patient/consent/revoke` |

### 2.3 México — LFPDPPP (Ley Federal de Protección de Datos Personales en Posesión de los Particulares, 2010)

**Autoridad:** INAI

Principios implementados:

- **Aviso de privacidad**: el wizard de onboarding presenta el aviso antes del registro.
- **Datos sensibles** (Art. 3 XII): datos sobre salud requieren consentimiento expreso.
- **Derechos ARCO** (Acceso, Rectificación, Cancelación, Oposición): disponibles vía
  endpoints de gestión de datos del paciente.
- **Medidas de seguridad** (Art. 19): TLS + cifrado + control de acceso RBAC.

### 2.4 Chile — Ley 19.628 Protección de la Vida Privada

**Estado:** Actualización en curso (Proyecto de Ley alineado con RGPD pendiente). Vitalia
implementa controles de la ley vigente + mejores prácticas del proyecto de reforma.

- **Datos sensibles** (Art. 10): información de salud solo puede tratarse con consentimiento
  del titular o en ejercicio de funciones propias de los establecimientos de salud.
- **Centros de salud** (Art. 10 b): Vitalia opera como plataforma de gestión de centros de
  salud; el consentimiento se captura en el flujo de booking.
- **Corrección y cancelación**: disponibles vía endpoints de gestión de datos.

### 2.5 Perú — Ley 29.733 Protección de Datos Personales

**Vigencia:** 2011 · **Autoridad:** ANPD Perú

- Datos de salud clasificados como **datos sensibles**.
- Consentimiento libre, previo, expreso, informado e inequívoco requerido.
- Derechos de acceso, rectificación, cancelación y oposición disponibles.
- Periodo de retención alineado con normativa sectorial de salud.

### 2.6 Colombia — Ley 1.581 Habeas Data

**Vigencia:** 2012 · **Autoridad:** SIC (Superintendencia de Industria y Comercio)

- Datos de salud = **datos sensibles** (Art. 5).
- Tratamiento solo con autorización explícita.
- Aviso de privacidad presentado en onboarding.
- Derechos de acceso, corrección, supresión, revocación y queja disponibles.
- Registro Nacional de Bases de Datos (RNBD): responsabilidad de la clínica (no de Vitalia
  como proveedor de software).

---

## 3. Retención del registro de auditoría (7 años)

### 3.1 Política

Vitalia retiene todos los eventos del audit log durante **7 años** desde la fecha del evento.
Este periodo:

- Supera el mínimo de la Ley 25.326 AR (5 años practicados).
- Se alinea con el estándar clínico de Argentina (historiales 10 años, audit log 7 años).
- Cubre los requisitos de Brasil LGPD para evidencia de cumplimiento.

### 3.2 Eventos auditados

| Evento | Metadata capturada |
|---|---|
| `booking_created` | tenant_id, booking_id, doctor_id (opaco), timestamp |
| `booking_confirmed` | tenant_id, booking_id, payment_status, amount |
| `consent_signed` | tenant_id, consent_id, consent_version, ip_hash, user_agent_hash, timestamp |
| `consent_revoked` | tenant_id, consent_id, revoked_at |
| `pii_detected_offer_description` | tenant_id, field, pattern_matched (sin valor real) |
| `pii_detected_testimonial` | idem |
| `medical_pii_allowed` | tenant_id, context (chat — consentimiento activo) |
| `medication_mentioned` | tenant_id, conversation_id (anonimizado) |
| `cross_tenant_attempt` | tenant_id_requested, tenant_id_actual, endpoint |
| `prompt_injection_blocked` | tenant_id, conversation_id, pattern_type |
| `data_export_requested` | tenant_id, patient_id (opaco), requested_by |
| `data_deletion_requested` | tenant_id, patient_id (opaco), requested_by |
| `audit_log_csv_exported` | tenant_id, filter_set, row_count, exported_by |

### 3.3 Eliminación controlada

Al cumplirse los 7 años, los registros se marcan `archived=true` y se mueven a cold storage.
No se eliminan automáticamente sin aprobación manual del administrador de la clínica.

### 3.4 Exportación CSV

Disponible en `/medical-compliance` → "Exportar CSV". Campos sensibles son enmascarados:

- Email: `p***@dominio.com`
- Teléfono: `+54-9-11-****-1234`
- Nombre paciente: `J. P.` (iniciales)

---

## 4. Flujo de captura de consentimiento

### 4.1 Cuándo se requiere consentimiento informado

Consentimiento informado requerido cuando `requires_informed_consent=true` en la oferta
(configurado por la clínica). Casos típicos:

- Procedimientos invasivos (implantes, cirugía oral)
- Psicoterapia (primera sesión formal)
- Tratamientos con medicación (psiquiatría — firmado por profesional)
- Procedimientos con anestesia

### 4.2 Pasos del flujo

```
1. Paciente selecciona turno en el widget de booking
   ↓
2. Sistema detecta requires_informed_consent=true en oferta
   ↓
3. Se presenta plantilla de consentimiento (versión versionada)
   Contiene: descripción del procedimiento + riesgos + alternativas + derechos
   ↓
4. Paciente firma (nombre tipado O pad de firma digital)
   ↓
5. Sistema captura: ip_hash, user_agent_hash, timestamp UTC, consent_template_version
   ↓
6. Registro consent_record creado: consent_id, signed=true, signed_at
   ↓
7. audit_log event "consent_signed" emitido
   ↓
8. Booking avanza a estado "awaiting_payment" (o "confirmed" si pago previo)
   ↓
9. Documento descargable generado para registro legal de la clínica
```

### 4.3 Revocación de consentimiento

El paciente puede revocar su consentimiento en cualquier momento antes del procedimiento:

- **Endpoint:** `POST /api/v1/vitalia/patient/consent/revoke`
- **Efecto:** `consent_record.revoked_at` se registra, booking pasa a `awaiting_consent`
- **Audit log:** evento `consent_revoked`
- **Nota:** La revocación no elimina el historial del audit log (obligación legal).

### 4.4 Versionado de plantillas de consentimiento

Cada plantilla tiene una versión semántica (`consent_template_version`). Cuando la clínica
actualiza la plantilla:

- Los consentimientos previos permanecen válidos (conservan su versión).
- Nuevas reservas requieren firma de la versión actualizada.
- El historial de versiones se mantiene inmutable.

---

## 5. Verificación HMAC de URLs de consentimiento

Las URLs de consentimiento contienen un token HMAC para prevenir acceso no autorizado a
formularios de consentimiento de otros pacientes.

### 5.1 Estructura de la URL

```
https://app.vitalia.health/consent/{consent_id}?token={hmac_token}&exp={expiry_unix}
```

### 5.2 Generación del HMAC

```python
import hashlib
import hmac
import time

def generate_consent_url_token(
    consent_id: str,
    patient_id: str,
    tenant_id: str,
    secret_key: bytes,
    expiry_seconds: int = 86400,  # 24 horas
) -> tuple[str, int]:
    """Genera token HMAC para URL de consentimiento.

    Returns: (token_hex, expiry_unix_timestamp)
    """
    expiry = int(time.time()) + expiry_seconds
    message = f"{consent_id}:{patient_id}:{tenant_id}:{expiry}".encode("utf-8")
    token = hmac.new(secret_key, message, hashlib.sha256).hexdigest()
    return token, expiry
```

### 5.3 Verificación en el servidor

Al acceder a la URL de consentimiento:

1. Se extrae `consent_id`, `token` y `exp` de la URL.
2. Se reconstruye el mensaje y se calcula el HMAC esperado.
3. Se compara con tiempo constante (`hmac.compare_digest`) para evitar timing attacks.
4. Si `exp < now()` → URL expirada → error 410 Gone.
5. Si HMAC no coincide → error 403 Forbidden.

### 5.4 Seguridad adicional

- La clave secreta se almacena en variables de entorno (nunca en código fuente).
- Los tokens son de un solo uso (se marcan como usados al acceder al formulario).
- Los formularios de consentimiento solo son accesibles mediante estas URLs firmadas.

---

## 6. Patrones de detección de datos personales (PII)

La detección de PII se ejecuta en los siguientes contextos (ver § 14.2 del spec):

### 6.1 Qué se detecta

| Categoría | Patrones | Acción |
|---|---|---|
| Nombre completo | 2+ tokens en mayúsculas (formato nombre propio) | Bloquear antes de guardar o enmascarar |
| DNI Argentina | 8 dígitos con/sin puntos (ej. 12.345.678) | Bloquear + advertencia |
| RUT Chile | 7-9 dígitos + dígito verificador (ej. 12.345.678-9) | Bloquear + advertencia |
| RFC México | Patrón alfanumérico 12-13 caracteres | Bloquear + advertencia |
| CURP México | 18 caracteres alfanuméricos específicos | Bloquear + advertencia |
| Cédula Colombia | 6-10 dígitos | Bloquear + advertencia |
| Teléfono | Formatos internacionales y locales (+54, +56, +52, +55) | Bloquear o enmascarar |
| Email | Formato estándar | Bloquear o enmascarar |
| Dirección | Patrones calle + número | Bloquear o enmascarar |
| Fecha de nacimiento | Formatos de fecha (DD/MM/YYYY, YYYY-MM-DD) | Bloquear o enmascarar |
| Condición médica | Lista vocabulario (cáncer, diabetes, VIH, etc.) | Permitir pero registrar evento `medical_pii` |
| Medicamentos | Catálogo INN 200+ entradas | Permitir pero registrar evento `medication_mentioned` |

### 6.2 Dónde se ejecuta la detección

- **Descripción de oferta**: bloquear antes de guardar — ninguna oferta debe contener datos del paciente.
- **Testimonios en Brand Studio**: bloquear al guardar + protección XSS.
- **Mensajes de chat del paciente**: registrar pero permitir (contexto de consentimiento activo).
- **Notas de seguimiento de tratamiento**: permitir pero registrar evento.
- **Exportación CSV del audit log**: enmascarar emails/teléfonos antes de descarga.

### 6.3 Respuesta al usuario ante detección

Cuando PII se detecta en un campo bloqueante, el formulario muestra:

> "El campo contiene datos personales. Elimina nombres, números de documento, condiciones
> médicas específicas o información de contacto antes de guardar."

El botón de envío permanece deshabilitado hasta que el campo sea corregido.

---

## 7. Derechos de exportación y eliminación de datos

Vitalia implementa derechos equivalentes al RGPD (en línea con LGPD, LFPDPPP, Ley 25.326 y
Ley 1.581) para los datos de los pacientes.

### 7.1 Derecho de acceso y exportación

El paciente puede solicitar todos sus datos almacenados:

```http
GET /api/v1/vitalia/patient/data-export
Authorization: Bearer {clerk_token}
Accept: application/json

# Responde con ZIP que contiene:
# - profile.json (datos del perfil)
# - bookings.json (historial de citas)
# - consents.json (registro de consentimientos)
# - medical_history.json (historial médico — con campos sensibles)
# - audit_log.json (actividad de la cuenta)
```

### 7.2 Derecho de rectificación

El paciente puede corregir sus datos de perfil:

```http
PATCH /api/v1/vitalia/patient/profile
Content-Type: application/json

{
  "name": "Nombre Corregido",
  "phone": "+54911234567"
}
```

### 7.3 Derecho de eliminación (derecho al olvido)

La eliminación es **lógica** (soft delete + anonimización), no física, para cumplir con
obligaciones de retención del registro médico y audit log:

```http
DELETE /api/v1/vitalia/patient/data
Authorization: Bearer {clerk_token}
```

**Efecto:**
- El perfil del paciente se anonimiza: nombre → `Paciente Eliminado`, email → hash, teléfono → null.
- Las citas históricas permanecen para el registro médico de la clínica (sin datos identificables del paciente).
- El audit log retiene los eventos (obligación legal), pero con `patient_id` anonimizado.
- El registro de consentimientos permanece (evidencia legal), con datos del firmante anonimizados.

### 7.4 Derecho a la portabilidad

Disponible a través del endpoint de exportación (`format=json` o `format=csv`).

### 7.5 Revocación del consentimiento

Ver sección 4.3 de este documento.

---

## 8. Aislamiento multi-tenant

Cada clínica es un tenant independiente. El aislamiento se garantiza a nivel de:

- **Base de datos**: todas las consultas filtran `tenant_id`. No hay JOINs cross-tenant.
- **API**: el header `X-Tenant-ID` se valida en cada request. Requests sin tenant válido
  devuelven 401.
- **Audit log**: intentos de acceso cross-tenant generan evento `cross_tenant_attempt` y
  retornan 403 Forbidden.
- **Exports**: los CSV del audit log solo contienen datos del tenant del usuario autenticado.
- **KB médica**: el contenido genérico (sin `tenant_id`) es compartido entre tenants del
  mismo `brand_slug=vitalia`. El contenido específico de clínica (`tenant_id != null`) es
  accesible solo por ese tenant.

---

*Para consultas sobre cumplimiento, contacta: compliance@vitalia.health*

*Este documento se actualiza con cada versión de la plataforma. Versión actual: 1.0.0*
