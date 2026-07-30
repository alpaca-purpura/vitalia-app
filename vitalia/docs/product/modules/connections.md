---
module: connections
brand: vitalia
last_updated: 2026-05-21
---

# connections — Brand-internal dispatch registries

5 dispatch tables medical-vertical specific brand-internal, wireados via Extension SDK EP-3 (tools) + EP-13 (guardrails) en `extensions.py::register_all(registry)`:

- **PAYMENT_PROVIDER_REGISTRY** (6 slots: cash, card, transfer, manual_mp, other, mercadopago placeholder)
- **FISCAL_PROVIDER_REGISTRY** (1 slot: nubefact_pe placeholder)
- **APPOINTMENT_ORIGIN_REGISTRY** (4 origins: sales_agent, walk_in, phone_manual, proactive_outbound)
- **CONVERSATION_INITIATION_REGISTRY** (1 slot: whatsapp_template_meta con requires_opt_in_if_marketing=True)
- **PRINT_METHOD_REGISTRY** (1 slot: browser_pdf FE-only)

## Capabilities

<!-- auto-list:start -->
- `vitalia-registries-medical-vertical` (live)
- `vitalia-connections-oauth-meta-google-ads` (live)
<!-- auto-list:end -->
