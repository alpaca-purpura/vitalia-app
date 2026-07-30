# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""OnboardingDraft — mutable domain entity for Valeria wizard onboarding state.

Tracks the complete state of a tenant's wizard onboarding session, including
required and optional wizard slots, consent, and completion state.

Not PHI: wizard onboarding config data only (clinic identity, vertical, tone).
Tenant + clinic isolation is enforced at the repository layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from src.modules.vitalia.copilot.domain.entities.wizard_slot import (
    WizardSlot,
)


@dataclass
class OnboardingDraft:
    """Mutable entity representing an in-progress Valeria wizard onboarding session.

    Attributes:
        id: Unique draft identifier.
        tenant_id: Cardinal tenant isolation field. Every query MUST filter by this.
        user_id: Initiating user ID (admin starting onboarding).
        clinic_id: Clinic identifier for HIPAA-lite dual filter. May be None pre-creation.
        mode: Wizard mode — "libre" (free-form conversation) | "guiado" (step-by-step).
        slots_required: Dict of slot_id → WizardSlot for mandatory onboarding data.
        slots_optional: Dict of slot_id → WizardSlot for optional enhancement data.
        bonus_extracted: Free-form extras extracted but not in required/optional lists.
        consent_voice_activation: Whether tenant consented to voice onboarding mode.
        created_at: UTC timestamp of draft creation.
        updated_at: UTC timestamp of last modification.
        deleted_at: Soft-delete timestamp. None = active.
        completed_at: Completion timestamp. None = in-progress.
    """

    id: UUID
    tenant_id: UUID
    user_id: UUID
    clinic_id: Optional[UUID]
    mode: str
    slots_required: dict[str, WizardSlot]
    slots_optional: dict[str, WizardSlot]
    bonus_extracted: dict
    consent_voice_activation: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    completed_at: Optional[datetime]

    def update_slot(self, slot_id: str, new_slot: WizardSlot) -> None:
        """Replace a slot value in either slots_required or slots_optional.

        Updates whichever dict contains the slot_id. If the slot_id exists in
        slots_required, it is updated there. If in slots_optional, updated there.
        If neither contains the slot_id, it is stored in bonus_extracted.

        Args:
            slot_id: The dot-notation slot identifier to update.
            new_slot: New WizardSlot value object (frozen) to store.
        """
        if slot_id in self.slots_required:
            self.slots_required[slot_id] = new_slot
        elif slot_id in self.slots_optional:
            self.slots_optional[slot_id] = new_slot
        else:
            self.bonus_extracted[slot_id] = new_slot

    def all_confirmed_slots(self) -> dict[str, WizardSlot]:
        """Return all confirmed slots from both required and optional dicts.

        A slot is confirmed if its confirmed_at field is not None.

        Returns:
            Dict of slot_id → WizardSlot for all confirmed slots.
        """
        confirmed: dict[str, WizardSlot] = {}
        for slot_id, slot in self.slots_required.items():
            if slot.confirmed_at is not None:
                confirmed[slot_id] = slot
        for slot_id, slot in self.slots_optional.items():
            if slot.confirmed_at is not None:
                confirmed[slot_id] = slot
        return confirmed
