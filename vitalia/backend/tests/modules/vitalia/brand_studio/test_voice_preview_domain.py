"""Tests for VoicePreview domain value object.

Verifies:
  - Frozen dataclass construction
  - cache_hit default False
  - compiler_version field
  - Immutability (frozen=True)

T-3 F1 — vitalia-fase2-lisa-marca (F2-S7).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.modules.vitalia.brand_studio.domain.voice_preview import VoicePreview


class TestVoicePreviewValueObject:
    """VoicePreview dataclass contracts."""

    def test_construction_minimal(self) -> None:
        now = datetime.now(timezone.utc)
        vp = VoicePreview(
            personality_profile_id="abc123",
            sample_whatsapp="Hola, soy Lisa de Clínica Bienestar.",
            sample_email_reactivation="Estimado paciente, te escribimos...",
            compiled_at=now,
            compiler_version="v2",
        )
        assert vp.personality_profile_id == "abc123"
        assert vp.compiler_version == "v2"

    def test_cache_hit_defaults_to_false(self) -> None:
        now = datetime.now(timezone.utc)
        vp = VoicePreview(
            personality_profile_id="abc123",
            sample_whatsapp="Hola.",
            sample_email_reactivation="Estimado paciente.",
            compiled_at=now,
            compiler_version="v2",
        )
        assert vp.cache_hit is False

    def test_cache_hit_can_be_true(self) -> None:
        now = datetime.now(timezone.utc)
        vp = VoicePreview(
            personality_profile_id="abc123",
            sample_whatsapp="Hola.",
            sample_email_reactivation="Estimado paciente.",
            compiled_at=now,
            compiler_version="v2",
            cache_hit=True,
        )
        assert vp.cache_hit is True

    def test_frozen_dataclass_raises_on_assign(self) -> None:
        """VoicePreview es frozen — no permite asignación post-creación."""
        now = datetime.now(timezone.utc)
        vp = VoicePreview(
            personality_profile_id="abc123",
            sample_whatsapp="Hola.",
            sample_email_reactivation="Estimado paciente.",
            compiled_at=now,
            compiler_version="v2",
        )
        with pytest.raises((AttributeError, TypeError)):
            vp.cache_hit = True  # type: ignore[misc]

    def test_two_instances_with_same_fields_are_equal(self) -> None:
        now = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        vp1 = VoicePreview(
            personality_profile_id="x",
            sample_whatsapp="Hola.",
            sample_email_reactivation="Est.",
            compiled_at=now,
            compiler_version="v2",
        )
        vp2 = VoicePreview(
            personality_profile_id="x",
            sample_whatsapp="Hola.",
            sample_email_reactivation="Est.",
            compiled_at=now,
            compiler_version="v2",
        )
        assert vp1 == vp2

    def test_compiler_version_v2(self) -> None:
        """compiler_version debe ser v2 (sales-agent compiler cementado)."""
        now = datetime.now(timezone.utc)
        vp = VoicePreview(
            personality_profile_id="xyz",
            sample_whatsapp="Hola, soy Lisa.",
            sample_email_reactivation="Estimado paciente, queremos...",
            compiled_at=now,
            compiler_version="v2",
        )
        assert vp.compiler_version == "v2"
