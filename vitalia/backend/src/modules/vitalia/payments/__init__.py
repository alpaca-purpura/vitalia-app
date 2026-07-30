# cap: payment.payment-gateways-latam-recurring
# story-origin: vitalia-fase2-s1-TBD
"""Vitalia payments brand-extension module.

Handles payment charge orchestration for clinic appointments.
Service-blocker: vitalia-payment-adapter-mvp (refined → NOT developed F2-S1).
Current phase: stub PaymentChargePort + MSW mocks (Option A per 03-arch § 8.6).

Separate from legacy vitalia/payment/ adapters (scaffold).
This module owns the charge orchestrator saga pattern.

Inside-Out DDD layers:
  domain/       — PaymentMethod + FiscalDocType enums
  application/  — PaymentChargePort interface + stub impl + ChargeOrchestrator
  api/          — charge_router (thin, delegates to orchestrator)
"""
