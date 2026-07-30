# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""Vitalia infrastructure repositories.

All repositories are AsyncSession-based (SQLA 2.0 select().where() style).
Constructor signature: (session: AsyncSession, tenant_id: UUID).
Every query filters tenant_id. PlanTierConfigRepository is CROSS-TENANT (no tenant_id filter).
"""

from __future__ import annotations

from src.modules.vitalia.infrastructure.repositories.booking_repository import (
    BookingRepository,
)
from src.modules.vitalia.infrastructure.repositories.consent_repository import (
    ConsentRepository,
)
from src.modules.vitalia.infrastructure.repositories.doctor_extension_repository import (
    DoctorExtensionRepository,
)
from src.modules.vitalia.infrastructure.repositories.medical_audit_log_repository import (
    MedicalAuditLogRepository,
)
from src.modules.vitalia.infrastructure.repositories.patient_medical_history_repository import (
    PatientMedicalHistoryRepository,
)
from src.modules.vitalia.infrastructure.repositories.payment_intent_repository import (
    PaymentIntentRepository,
)
from src.modules.vitalia.infrastructure.repositories.plan_tier_repository import (
    PlanTierConfigRepository,
)
from src.modules.vitalia.infrastructure.repositories.treatment_followup_repository import (
    TreatmentFollowupRepository,
)

__all__ = [
    "BookingRepository",
    "TreatmentFollowupRepository",
    "ConsentRepository",
    "PaymentIntentRepository",
    "MedicalAuditLogRepository",
    "DoctorExtensionRepository",
    "PatientMedicalHistoryRepository",
    "PlanTierConfigRepository",
]
