---
story_id: vitalia-fiscal-emission-pe
state: idea
last_artifact: checkpoint.md
last_modified: '2026-05-29T13:46:24.228Z'
ratified_by_chris: false
spawned_at: 2026-05-17T00:00:00.000Z
transitioned_at: 2026-05-17T00:00:00.000Z
spawned_by: /pm-vitalia
parallel_safe: true
blocked_reason: >-
  ★ TIER reclassified 2026-05-27 (audit sweep): TIER 2 (post payment-adapter-mvp
  real). Si MVP NO launch Peru → bajar a TIER 7 DEFERRED hasta Fase 3 PE launch
  (skip Nubefact integration, otros países usan Stripe/MP invoicing). Si MVP SI
  Peru → mantener TIER 2 emparejado con payment-adapter (emit boleta inmediata
  post charge). SSoT orden:
  vitalia/docs/product/outcomes/vitalia-fase-2-tier-roadmap.md § TIER 2 + § TIER
  7. Pre-condition Chris ratify: ¿Peru en MVP launch countries?
priority: high
estimated_dev_weeks: 1-2
parent_spec: >-
  vitalia/docs/product/stories/vitalia-ux-discovery/01-spec.md §§Capa 2 fiscal
  toggle Nubefact PE
cross_phase_2_consumers:
  - vitalia-fase2-valeria-agenda
next_action: >-
  /po vitalia-fiscal-emission-pe — produce 01-spec.md service-story (sin UI
  dedicada Fase 2 más allá toggle inline subform Cobrar saldo F2-S1). UI
  configuración completa (NubefactConfigEditor) puede ir a F2-S22
  config-avanzado o story dedicada futura. Inputs cementados: scope (~80 LOC) +
  4 Gherkin + Capa 2 trigger flow + retry queue 8-step exponential backoff +
  secrets vault pgcrypto KEK rotada anualmente + CDR archive 10y retention. Open
  Chris: (1) Nubefact único PSE/OSE ó multi-provider Strategy? (2) Boleta +
  Factura ambos o solo Boleta? (3) Dead-letter alerta admin+Adrián? (4) Setup
  admin-only vía seed/script? Validate G6 batched (≤4) → refining→refined.
release: F3
cap_target: null
cap_change_type: new
parent_story: null
---

# vitalia-fiscal-emission-pe — checkpoint

## Goal

Wirear **Nubefact PE adapter** (proveedor PSE/OSE SUNAT autorizado) para que tenants Perú emitan **boletas electrónicas B/V (consumidor final)** desde el flow cobranza `/agenda` Capa 2 cementado Batch 4 — toggle `payment.fiscal_emission_pe_enabled` per clínica.

Hijo directo de `vitalia-ux-discovery` Batch 4 (Slice 1 cementado). Sin esta story, Vitalia tenants Perú no pueden operar legalmente — boleta SUNAT es requisito de toda transacción consumidor en PE.

## Scope

### In-scope MVP (Slice 1)

**Backend adapter Nubefact:**
- Adapter conforme contract Extension SDK EP-N `fiscal_provider` (cementado Batch 4 — registry `fiscal_provider` plugin-ready)
- Path: `vitalia/backend/src/modules/vitalia/connections/fiscal/nubefact_pe_adapter.py`
- Nubefact API REST integration (endpoint `/api/v1/invoice/send` + auth token per tenant)
- Signed XML emission (Nubefact firma con su certificado digital — Vitalia NO maneja firma propia)
- Document types Slice 1: **Boleta de Venta (03)** + **Factura (01)** + nota de crédito (07) opcional Slice 2

**Tabla `fiscal_receipts` schema cementado:**
- Columns: `id, tenant_id, clinic_id, appointment_id, payment_event_id, document_type, document_number, serie, status (pending|submitted|accepted|rejected), nubefact_request_id, signed_xml_url, cdr_url, error_code, error_message, retry_count, next_retry_at, sunat_deadline_at, created_at, updated_at`
- Particionada por mes (audit retention 10y per hipaa-lite.md)
- Migrations idempotentes (`IF NOT EXISTS`)

**Encrypted credentials vault per tenant:**
- Tabla `tenant_fiscal_credentials_pe` con columns `tenant_id, ruc, token_encrypted (pgcrypto KEK rotada anualmente), serie_factura, serie_boleta, environment (sandbox|production)`
- Setup UI defer Slice 2 (pantalla `/configuracion/facturacion-pe` — Owner credenciales + RUC validation + test connection button)
- Slice 1: tenants Perú early-access se configuran via seed/script BE (admin-only)

**Retry queue exponential backoff hasta 3 días calendario SUNAT deadline:**
- Cron `nubefact_emission_retry_sweep` cada 5 minutos
- Strategy: 5min → 15min → 1h → 4h → 12h → 24h → 48h → 72h (max retry)
- Cada retry registra `retry_count` + `next_retry_at` + `error_code`
- Dead-letter handling: post 72h sin éxito → status=`failed_permanent` + alerta admin clinic + audit_log row + notification Adrián a operador "Boleta {N} requiere emisión manual SUNAT — contactar a tu contador"

**CDR (Constancia de Recepción) archive:**
- Tras `accepted` por Nubefact → guarda CDR XML signed por SUNAT en S3/storage tenant (path `tenants/{tenant_id}/fiscal/cdr/{document_number}.xml`)
- Audit retention 10y (regulación SUNAT)
- Endpoint download CDR per receipt (RBAC `admin_clinic` o `doctor` con audit_log row)

**UI minimal Slice 1:**
- Toggle inline en `/agenda` sheet cobro saldo (cementado Batch 4): si tenant `fiscal_emission_pe_enabled=true` Y país=PE → checkbox "Emitir boleta SUNAT" (default checked) + serie auto-display + document_number preview
- Estado emission en sheet post-cobro: `pending` (spinner) / `submitted` / `accepted ✓` (verde + link CDR download) / `rejected ✗` (rojo + error + retry button manual)
- Cross-link `/configuracion/facturacion-pe` defer Slice 2 (CTA "Configurar facturación" si tenant aún no setup)
- Microcopy en `vitalia/frontend/src/features/agenda/copy.ts` § fiscal_pe section + arch fitness `no-hardcoded-strings.test.ts` enforced

**Audit log obligatorio (hipaa-lite cardinal):**
- Toda emisión registra row `audit_log` con `(tenant_id, clinic_id, user_id, action='fiscal_emit', resource_type='fiscal_receipt', resource_id, payload_redacted)` — payload sin PII paciente

**4 Gherkin scenarios cementados:**
1. **Happy** — boleta B/V emitida + CDR archivado (operador cobra saldo /agenda → toggle on → Nubefact responde 200 + CDR XML → tabla fiscal_receipts status=accepted + audit row + UI muestra ✓ + CDR downloadable)
2. **Negative** — Nubefact API down → retry queue exponential (operador cobra → Nubefact 503 → status=pending + retry_count=0 → cron retry 5min después → eventual success / dead-letter post 72h con alert admin)
3. **Edge** — tenant sin RUC válido / serie agotada → Nubefact rejection (operador cobra → Nubefact 400 con error_code=`INVALID_RUC` o `SERIE_EXHAUSTED` → status=rejected + alerta admin clinic + UI muestra error humano "Tu RUC no está activo en SUNAT — contactar a tu contador" + payment_event registra sin boleta)
4. **Adversarial** — CDR replay attack + signature tampering (atacante intercepta CDR signed XML + modifica document_number → backend valida signature SUNAT con cert público + rechaza tampered CDR + audit row con `action='fiscal_cdr_tampering_detected'` + alerta security)

### Out-of-scope MVP (defer Slice 2/3)

- UI completa `/configuracion/facturacion-pe` Owner setup (RUC validation + test connection + serie management + branding boleta)
- Otros tipos documento (notas de crédito 07 / notas de débito 08 / guías remisión 09 — solo boleta + factura Slice 1)
- Nota de crédito automática on refund (defer Slice 2 — política reembolso 24h cementada Batch 4 hardcoded Slice 1 sin nota crédito)
- Otros proveedores PSE/OSE PE (tefacturo, facturak — Extension SDK plugin-ready Slice 2)
- Multi-país fiscal emission (Facturama MX · DIAN CO · AFIP AR · SII CL · NFe BR — Extension SDK plugin-ready Slice 3)
- Branding boleta tenant (logo + colores + footer custom — Slice 2)
- Reportes contables agregados (defer Slice 3 dashboard `/configuracion/facturacion-pe/reports`)
- WebUSB ESC/POS impresión térmica boleta (Slice 2 cementado Batch 4 capa 3 impresión)

## Dependencies

- **vitalia-ux-discovery v1** — Batch 4 cementó Capa 2 trigger flow + toggle + 5 Extension SDK registries plugin-ready (`fiscal_provider` registry)
- **vitalia-payment-adapter-mvp** — `payment_events` table existe Slice 1 (depósito 30% + saldo final captured) → trigger fiscal emission post-payment
- **Backend Vitalia Story 11** — scaffold `vitalia/backend/src/modules/vitalia/connections/` existe (post extensions.py register_all montó EP-N)
- **engine `core/luana-core-extension-sdk/`** — registries pattern reusable

## Analysis backend pre-refining

Pre-architect spawn `/po` debe leer:
- `vitalia/docs/product/stories/vitalia-ux-discovery/01-spec.md` §§Ruta /agenda Batch 4 (Capa 2 fiscal section completa)
- `vitalia/.claude/rules/hipaa-lite.md` (audit log obligatorio + retention 10y aplicable a fiscal_receipts + CDR archive)
- `vitalia/config/brand.yaml` (`payment_gateways: [mercadopago, stripe_connect, tokenized_recurring]` + `default_currency_per_country.PE: PEN`)
- Nubefact API docs (público — https://www.nubefact.com/apis) — endpoints REST + auth + document types codes SUNAT
- SUNAT Resolución 097-2012 (boletas electrónicas obligatoriedad) + plazo emisión legal

## Bitácora

- 2026-05-17 spawned: `/pm-vitalia` crea story idea formal para tracking explícito. Hijo directo de `vitalia-ux-discovery` Batch 4 cementado Capa 2 fiscal toggle Nubefact PE. Story side paralela Slice 1 listada en §Slice 1 cut + §Components mapping consolidado + §Handoff /architect del spec principal. Sin esta story Vitalia tenants Perú no operan legalmente (boleta electrónica obligatoria SUNAT Resolución 097-2012). Next: handoff `/po vitalia-fiscal-emission-pe` para refining iterativo con Chris → 01-spec.md service-story con 4 Gherkin scenarios + Capa 2 trigger flow + retry queue policy + secrets vault design + CDR archive policy → ratify Chris → state refining→refined → handoff `/architect`.
- **2026-05-22 cross-story deps update:** post paradigma shell-organism cementado, consumer único Fase 2 = `vitalia-fase2-valeria-agenda` (F2-S1 subform Cobrar saldo emite boleta inline). UI configuración Nubefact full puede ir a F2-S22 config-avanzado o story dedicada futura. Story sigue refining. Priority bump recomendado cuando Fase 1 (F1-S0..F1-S10) entra developing — para que developed esté ANTES de F2-S1 arrancar. Outcome refactor v2.0 cementado: `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md`.
