---
module: offer
brand: vitalia
last_updated: 2026-06-19
---

# offer — Catálogo de servicios + escalera de valor

Módulo `offer` de Vitalia: el catálogo de servicios de la clínica construido sobre **Offer Studio engine** (`core/luana-core-offer-studio`) vía Extension SDK **EP-2** — cada servicio es un `Offer` y el peldaño es `OfferValueLevel`; **cero edit del engine** (consume vía port `luana_core_platform.links.ports.offer`).

`lisa-servicios` (2026-06-19) introduce el catálogo + la escalera de valor + el workspace de servicio de 5 leaves (Resumen · Para Adrián · Especialistas · Plan de pago · Prueba social), todo con autoguardado. Es la **keystone del conocimiento de Adrián**: un servicio activo entra a `TenantKnowledgeBuilder.build_identity` (consume-only) y el agente lo ofrece/cita/matchea al especialista. Plan de pago = 3 cobros distintos (reserva · anticipo · financiamiento, RN-6). RAG runtime de las fuentes documentales = Sub-phase B (engine-lift `/pm-luana`).

## Capabilities

<!-- auto-list:start -->
- `lisa-servicios` (live · 2026-06-19) — catálogo + escalera + workspace 5 leaves · keystone Adrián · auditor APPROVED + Chris live-verify
<!-- auto-list:end -->
