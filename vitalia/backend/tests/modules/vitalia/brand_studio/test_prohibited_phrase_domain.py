"""Tests for ProhibitedPhrase domain entity.

Verifies:
  - Entity creation defaults + field contracts
  - is_seed property (tenant_id IS NULL → seed)
  - ProhibitedPhraseSeverity enum values
  - datetime.now(timezone.utc) (no datetime.utcnow deprecation)

T-3 F1 — vitalia-fase2-lisa-marca (F2-S7).
"""

from __future__ import annotations

from datetime import timezone
from uuid import UUID

from src.modules.vitalia.brand_studio.domain.prohibited_phrase import (
    ProhibitedPhrase,
    ProhibitedPhraseSeverity,
)


class TestProhibitedPhraseSeverity:
    """Enum values and identity."""

    def test_severity_low_value(self) -> None:
        assert ProhibitedPhraseSeverity.LOW.value == "low"

    def test_severity_medium_value(self) -> None:
        assert ProhibitedPhraseSeverity.MEDIUM.value == "medium"

    def test_severity_high_value(self) -> None:
        assert ProhibitedPhraseSeverity.HIGH.value == "high"

    def test_severity_is_str_enum(self) -> None:
        assert str(ProhibitedPhraseSeverity.HIGH) == "high"


class TestProhibitedPhraseEntity:
    """ProhibitedPhrase dataclass contracts."""

    def test_default_creates_unique_ids(self) -> None:
        p1 = ProhibitedPhrase(phrase="curamos")
        p2 = ProhibitedPhrase(phrase="garantizado")
        assert p1.id != p2.id

    def test_is_seed_when_tenant_id_is_none(self) -> None:
        phrase = ProhibitedPhrase(phrase="curamos", tenant_id=None)
        assert phrase.is_seed is True

    def test_is_not_seed_when_tenant_id_set(self) -> None:
        tenant = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        phrase = ProhibitedPhrase(phrase="mi frase", tenant_id=tenant)
        assert phrase.is_seed is False

    def test_default_severity_is_medium(self) -> None:
        phrase = ProhibitedPhrase(phrase="cualquier frase")
        assert phrase.severity == ProhibitedPhraseSeverity.MEDIUM.value

    def test_created_at_is_timezone_aware(self) -> None:
        phrase = ProhibitedPhrase(phrase="test")
        assert phrase.created_at.tzinfo is not None
        assert phrase.created_at.tzinfo == timezone.utc

    def test_created_at_no_utcnow_deprecation(self) -> None:
        """created_at debe usar datetime.now(timezone.utc), no datetime.utcnow()."""
        phrase = ProhibitedPhrase(phrase="test frase")
        # Si usara utcnow() la creación no daría timezone aware
        assert phrase.created_at.tzinfo is not None

    def test_country_scope_none_by_default(self) -> None:
        phrase = ProhibitedPhrase(phrase="test")
        assert phrase.country_scope is None

    def test_country_scope_pe(self) -> None:
        phrase = ProhibitedPhrase(phrase="curamos", country_scope="PE")
        assert phrase.country_scope == "PE"

    def test_suggested_alternative_default_empty(self) -> None:
        phrase = ProhibitedPhrase(phrase="curamos")
        assert phrase.suggested_alternative == ""

    def test_full_construction(self) -> None:
        tenant_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        phrase = ProhibitedPhrase(
            phrase="100% efectivo",
            suggested_alternative="con alta tasa de éxito clínico",
            severity=ProhibitedPhraseSeverity.HIGH.value,
            country_scope="PE",
            tenant_id=tenant_id,
        )
        assert phrase.phrase == "100% efectivo"
        assert phrase.suggested_alternative == "con alta tasa de éxito clínico"
        assert phrase.severity == "high"
        assert phrase.country_scope == "PE"
        assert phrase.tenant_id == tenant_id
        assert phrase.is_seed is False

    def test_deleted_at_none_by_default(self) -> None:
        phrase = ProhibitedPhrase(phrase="test")
        assert phrase.deleted_at is None
