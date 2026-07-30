"""Payment channel adapters — generic booking-deposit + recurring billing flow.

Lifted shared per Story 11 (luana-vitalia-bootstrap) D4 anti-duplication.md.
Story 12 (luana-comunify-bootstrap) T-payment-1 lifts Stripe Connect + Tokenized
Recurring base classes (Story 11 kept those vitalia-local).

Distinct concern from `luana-core-sales-agent.application.tools.payment`
(sales-agent CLOSER tool returning checkout link in chat). This package
hosts CHANNEL ADAPTERS for booking-deposit + subscription billing with:

- HMAC webhook verification
- Idempotency key = booking_id / composite (subscriber_id, entity_id, n)
- compliance_level metadata per vertical (hipaa_lite / creator_economy / etc.)
- Amount in cents (int) + currency from data (NO hardcoded 'USD')

Verticals (vitalia, comunify, lupulo) EXTEND base adapter classes —
NEVER mirror per `.claude/rules/anti-duplication.md`.
"""

from luana_core_channels.payment.mercadopago_adapter import (
    BackUrls,
    MercadoPagoAdapter,
    MpPreferenceResponse,
    PayerInfo,
    PaymentLinkOutput,
    PaymentStatusEnum,
    PreferenceItem,
)
from luana_core_channels.payment.stripe_connect_adapter import (
    StripeConnectAdapter,
    StripePaymentIntentResult,
)
from luana_core_channels.payment.tokenized_recurring_adapter import (
    Installment,
    InstallmentResult,
    RecurringPaymentSchedule,
    TokenizedRecurringAdapter,
)

__all__ = (
    # MercadoPago
    "BackUrls",
    "MercadoPagoAdapter",
    "MpPreferenceResponse",
    "PayerInfo",
    "PaymentLinkOutput",
    "PaymentStatusEnum",
    "PreferenceItem",
    # Stripe Connect
    "StripeConnectAdapter",
    "StripePaymentIntentResult",
    # Tokenized Recurring
    "Installment",
    "InstallmentResult",
    "RecurringPaymentSchedule",
    "TokenizedRecurringAdapter",
)
