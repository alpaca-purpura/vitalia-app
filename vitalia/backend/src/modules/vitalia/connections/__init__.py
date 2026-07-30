# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Vitalia connections — brand-extension surface for adapter registries.

Per `03-arch-be.md` § 6 (Slice 1 cement) — 5 NEW brand-internal registries
mounted via existing Extension SDK EP-1..EP-18 (NOT new EPs):

- payment/      → payment_provider_registry  (referenced by EP-3 vitalia.capture_payment tool)
- fiscal/       → fiscal_provider_registry   (referenced by EP-3 vitalia.emit_fiscal_receipt tool — future ticket)
- appointment_origin/  → appointment_origin_registry (referenced by EP-3 reschedule + agenda dispatch)
- conversation_initiation/ → conversation_initiation_registry (referenced by EP-8 channel adapters)
- print_method/ → print_method_registry      (referenced by EP-12 asset_template render dispatch)

NOTE — the registries are brand-specific dict structures internal to Vitalia
(NOT engine EPs). Slice 2 lift candidates (NEW core EP-19..EP-23) documented in
`vitalia/docs/product/stories/vitalia-ux-discovery/delta-arch-notes.md`.

T-infra-2 scope (per 06-tickets.yaml Slice 1):
  Slice 1 ships ONLY definition shells + selected real entries:
  - payment: 5 manual providers (cash/card/transfer/manual_mp/other) + 1 placeholder
    (mercadopago) handler that raises NotImplementedError until side story
    `vitalia-payment-adapter-mvp` lands. Handler refs use `vitalia.connections.X.adapter:Y` style.
  - fiscal: 1 entry `nubefact_pe` with placeholder handler (raises until
    side story `vitalia-fiscal-emission-pe` lands).
  - appointment_origin: 4 entries (sales_agent / walk_in / phone_manual /
    proactive_outbound) — pure metadata, no callables.
  - conversation_initiation: 1 entry whatsapp_template_meta with placeholder
    handler (real adapter in future ticket).
  - print_method: 1 entry browser_pdf — FE-only Slice 1 (no callable).
"""
