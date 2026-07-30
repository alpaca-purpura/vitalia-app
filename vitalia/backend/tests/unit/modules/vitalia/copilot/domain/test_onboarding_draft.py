"""RED tests — OnboardingDraft domain entity + WizardSlot value object.

TDD per .claude/rules/tdd-mandatory.md: these tests MUST fail before domain
entities exist, then GREEN after implementation.

Tests verify:
- OnboardingDraft dataclass instantiation + field contracts
- WizardSlot frozen value object (immutable)
- OnboardingDraft.update_slot() mutates slots_required
- OnboardingDraft.all_confirmed_slots() returns only confirmed slots
- OnboardingDraft is not PHI (no patient data — wizard onboarding config)
- Soft-delete field present (deleted_at)
- tenant_id cardinal field present
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


TENANT_ID = uuid4()
USER_ID = uuid4()


class TestWizardSlot:
    """WizardSlot value object tests."""

    def test_wizard_slot_is_frozen(self) -> None:
        """WizardSlot is a frozen dataclass (immutable value object)."""
        from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

        slot = WizardSlot(
            slot_id="tenant.name",
            value="Clínica Sonrisa Plena",
            confidence=0.95,
            confirmed_at=None,
            source="extracted",
        )
        with pytest.raises((AttributeError, TypeError)):
            slot.value = "changed"  # type: ignore[misc]

    def test_wizard_slot_confidence_field(self) -> None:
        """confidence field is a float 0.0-1.0."""
        from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

        slot = WizardSlot(
            slot_id="tenant.vertical",
            value="dental",
            confidence=0.92,
            confirmed_at=None,
            source="extracted",
        )
        assert 0.0 <= slot.confidence <= 1.0

    def test_wizard_slot_source_values(self) -> None:
        """source field accepts expected enum-like values."""
        from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

        for source in ("extracted", "user_text", "user_correction"):
            slot = WizardSlot(
                slot_id="test",
                value="v",
                confidence=0.5,
                confirmed_at=None,
                source=source,
            )
            assert slot.source == source

    def test_wizard_slot_value_can_be_dict(self) -> None:
        """value field accepts dict (for structured slots like location)."""
        from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

        slot = WizardSlot(
            slot_id="tenant.location",
            value={"country": "PE", "city": "Lima"},
            confidence=0.88,
            confirmed_at=None,
            source="extracted",
        )
        assert isinstance(slot.value, dict)
        assert slot.value["country"] == "PE"

    def test_wizard_slot_value_can_be_none(self) -> None:
        """value field accepts None (slot not yet filled)."""
        from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

        slot = WizardSlot(
            slot_id="brand.tone_default",
            value=None,
            confidence=0.0,
            confirmed_at=None,
            source="extracted",
        )
        assert slot.value is None


class TestOnboardingDraft:
    """OnboardingDraft domain entity tests."""

    def _make_draft(self) -> "object":
        from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft
        from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

        return OnboardingDraft(
            id=uuid4(),
            tenant_id=TENANT_ID,
            user_id=USER_ID,
            clinic_id=None,
            mode="libre",
            slots_required={
                "tenant.name": WizardSlot(
                    slot_id="tenant.name", value=None, confidence=0.0, confirmed_at=None, source="extracted"
                ),
                "tenant.vertical": WizardSlot(
                    slot_id="tenant.vertical", value=None, confidence=0.0, confirmed_at=None, source="extracted"
                ),
                "tenant.location": WizardSlot(
                    slot_id="tenant.location", value=None, confidence=0.0, confirmed_at=None, source="extracted"
                ),
            },
            slots_optional={
                "brand.tone_default": WizardSlot(
                    slot_id="brand.tone_default", value=None, confidence=0.0, confirmed_at=None, source="extracted"
                ),
            },
            bonus_extracted={},
            consent_voice_activation=False,
            created_at=_utc_now(),
            updated_at=_utc_now(),
            deleted_at=None,
            completed_at=None,
        )

    def test_onboarding_draft_has_tenant_id(self) -> None:
        """tenant_id cardinal field present on OnboardingDraft."""
        draft = self._make_draft()
        assert hasattr(draft, "tenant_id")
        assert draft.tenant_id == TENANT_ID

    def test_onboarding_draft_has_soft_delete(self) -> None:
        """deleted_at soft-delete field present and defaults to None."""
        draft = self._make_draft()
        assert hasattr(draft, "deleted_at")
        assert draft.deleted_at is None

    def test_onboarding_draft_has_completed_at(self) -> None:
        """completed_at field present and defaults to None."""
        draft = self._make_draft()
        assert hasattr(draft, "completed_at")
        assert draft.completed_at is None

    def test_onboarding_draft_mode_values(self) -> None:
        """mode field accepts 'libre' and 'guiado'."""
        from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft

        for mode in ("libre", "guiado"):
            draft = OnboardingDraft(
                id=uuid4(),
                tenant_id=TENANT_ID,
                user_id=USER_ID,
                clinic_id=None,
                mode=mode,
                slots_required={},
                slots_optional={},
                bonus_extracted={},
                consent_voice_activation=False,
                created_at=_utc_now(),
                updated_at=_utc_now(),
                deleted_at=None,
                completed_at=None,
            )
            assert draft.mode == mode

    def test_update_slot_mutates_slots_required(self) -> None:
        """update_slot() replaces slot in slots_required dict."""
        from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

        draft = self._make_draft()
        new_slot = WizardSlot(
            slot_id="tenant.name",
            value="Clínica Sonrisa Plena",
            confidence=0.95,
            confirmed_at=_utc_now(),
            source="user_text",
        )
        draft.update_slot("tenant.name", new_slot)
        assert draft.slots_required["tenant.name"].value == "Clínica Sonrisa Plena"

    def test_update_slot_mutates_slots_optional(self) -> None:
        """update_slot() also works on optional slots."""
        from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

        draft = self._make_draft()
        new_slot = WizardSlot(
            slot_id="brand.tone_default",
            value="cálido_profesional",
            confidence=0.72,
            confirmed_at=_utc_now(),
            source="extracted",
        )
        draft.update_slot("brand.tone_default", new_slot)
        assert draft.slots_optional["brand.tone_default"].value == "cálido_profesional"

    def test_all_confirmed_slots_returns_confirmed_only(self) -> None:
        """all_confirmed_slots() returns only slots with confirmed_at set."""
        from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

        draft = self._make_draft()
        confirmed = WizardSlot(
            slot_id="tenant.name",
            value="Clínica Test",
            confidence=0.99,
            confirmed_at=_utc_now(),
            source="user_text",
        )
        draft.update_slot("tenant.name", confirmed)

        result = draft.all_confirmed_slots()
        assert "tenant.name" in result
        # Unconfirmed slots should not be in result
        assert "tenant.vertical" not in result

    def test_all_confirmed_slots_empty_initially(self) -> None:
        """all_confirmed_slots() returns empty dict for fresh draft."""
        draft = self._make_draft()
        result = draft.all_confirmed_slots()
        assert result == {}

    def test_onboarding_draft_uuid_fields(self) -> None:
        """id, tenant_id, user_id are UUID instances."""
        draft = self._make_draft()
        assert isinstance(draft.id, UUID)
        assert isinstance(draft.tenant_id, UUID)
        assert isinstance(draft.user_id, UUID)
