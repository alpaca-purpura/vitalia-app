"""Tests for BrandVoiceService — Story 7 D-T3 introduction.

Covers:
1. Protocol conformance (BrandVoicePort runtime_checkable).
2. compile_system_instruction returns cached ORM value when present.
3. compile_system_instruction recompiles from JSONB when cache empty.
4. compile_system_instruction returns "" when no active profile.
5. get_voice_metadata returns populated dict when profile exists.
6. get_voice_metadata returns empty default dict when no profile.

Per Story 7 §1.3 + §1.5 + §2.5 cardinal invariants:
- Does NOT modify PersonalityCompiler.compile() signature.
- Port surface FROZEN at 2 methods.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest
from luana_core_brand_studio.application.ports.brand_voice_port import BrandVoicePort
from luana_core_brand_studio.application.services.brand_voice_service import (
    BrandVoiceService,
)
from luana_core_brand_studio.infrastructure.repositories.personality_repository import (
    PersonalityProfileRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")

_DEFAULT_DIMENSIONS = {
    "energy": 0.65,
    "warmth": 0.85,
    "humor": 0.6,
    "expressiveness": 0.7,
    "narrative": 0.5,
    "verbosity": 0.4,
}

_DEFAULT_LINGUISTIC = {
    "emoji_style": "frequent",
    "favorite_emojis": ["😊"],
    "greeting": "¡Hola!",
    "farewell": "¡Hasta pronto!",
    "filler_phrases": ["mira"],
    "avg_message_length": "short",
    "punctuation_style": "expressive",
    "humor_type": "playful",
    "unique_vocabulary": ["genial"],
}


def _activate(repo: PersonalityProfileRepository, model, tenant_id: uuid.UUID) -> None:
    """Helper — set the profile active via repo helper."""
    repo.activate(model.id, tenant_id=tenant_id)


# ---------------------------------------------------------------------------
# Test 1 — Protocol conformance (D-T3 cardinal — port surface FROZEN)
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    """Verify BrandVoiceService satisfies BrandVoicePort runtime_checkable Protocol."""

    def test_port_is_runtime_checkable(self) -> None:
        """BrandVoicePort MUST be @runtime_checkable for isinstance check at DI wiring."""
        # runtime_checkable Protocols expose _is_runtime_protocol = True
        assert getattr(BrandVoicePort, "_is_runtime_protocol", False) is True

    def test_port_has_exactly_two_public_methods(self) -> None:
        """Per Story 7 §2.5 — port surface FROZEN at compile_system_instruction + get_voice_metadata."""
        # Discover public Protocol methods.
        public_methods = {
            name for name in dir(BrandVoicePort) if not name.startswith("_") and callable(getattr(BrandVoicePort, name))
        }
        assert public_methods == {"compile_system_instruction", "get_voice_metadata"}, (
            f"D-T3 surface drift detected — port has {public_methods}; expected exactly "
            f"{{'compile_system_instruction', 'get_voice_metadata'}}. "
            f"Adding methods requires architect ratification (Story 7 §6 halt #2)."
        )

    def test_service_satisfies_port_via_runtime_isinstance(self, db: Session) -> None:
        """BrandVoiceService instance MUST satisfy isinstance(service, BrandVoicePort)."""
        repo = PersonalityProfileRepository(db)
        service = BrandVoiceService(repo=repo)
        assert isinstance(service, BrandVoicePort)


# ---------------------------------------------------------------------------
# Test 2/3 — compile_system_instruction behavior
# ---------------------------------------------------------------------------


class TestCompileSystemInstruction:
    """compile_system_instruction returns cached ORM value, recompiles, or falls back to empty."""

    @pytest.mark.asyncio
    async def test_returns_cached_system_instruction_when_present(self, db: Session, seed_tenant) -> None:
        """When PersonalityProfileModel.system_instruction is populated, return it directly."""
        repo = PersonalityProfileRepository(db)
        cached_instruction = "## BLOQUE 1 — CACHED VOICE\nWarm energetic tone\n"
        model = repo.create(
            tenant_id=TENANT_A,
            name="Cached Voice",
            profile_type="preset",
            dimensions=_DEFAULT_DIMENSIONS,
            linguistic_patterns=_DEFAULT_LINGUISTIC,
            sample_exchanges=[],
            negative_constraints=[],
            system_instruction=cached_instruction,
        )
        _activate(repo, model, TENANT_A)

        service = BrandVoiceService(repo=repo)
        result = await service.compile_system_instruction(TENANT_A)

        assert result == cached_instruction

    @pytest.mark.asyncio
    async def test_recompiles_when_cache_empty(self, db: Session, seed_tenant) -> None:
        """When system_instruction is None/empty, recompile from JSONB pillars."""
        repo = PersonalityProfileRepository(db)
        model = repo.create(
            tenant_id=TENANT_A,
            name="No Cache Profile",
            profile_type="preset",
            dimensions=_DEFAULT_DIMENSIONS,
            linguistic_patterns=_DEFAULT_LINGUISTIC,
            sample_exchanges=[],
            negative_constraints=[],
            system_instruction=None,  # ← cache empty
        )
        _activate(repo, model, TENANT_A)

        service = BrandVoiceService(repo=repo)
        result = await service.compile_system_instruction(TENANT_A)

        # Recompiled output: must contain the 5 BLOQUE headers and the
        # linguistic surface markers.
        assert result != ""
        assert "BLOQUE 1" in result
        assert "BLOQUE 2" in result
        # Block 2 surface markers (linguistic patterns).
        assert "😊" in result or "frequent" in result

    @pytest.mark.asyncio
    async def test_returns_empty_string_when_no_active_profile(self, db: Session, seed_tenant) -> None:
        """When tenant has no active PersonalityProfile, return '' (consumer falls back to default voice)."""
        repo = PersonalityProfileRepository(db)
        # No profile created for TENANT_A.
        service = BrandVoiceService(repo=repo)

        result = await service.compile_system_instruction(TENANT_A)

        assert result == ""

    @pytest.mark.asyncio
    async def test_returns_empty_when_profile_inactive(self, db: Session, seed_tenant) -> None:
        """Inactive profile (is_active=False) should NOT be returned by get_active."""
        repo = PersonalityProfileRepository(db)
        # Create profile but do NOT activate it.
        repo.create(
            tenant_id=TENANT_A,
            name="Inactive Profile",
            profile_type="preset",
            dimensions=_DEFAULT_DIMENSIONS,
            linguistic_patterns=_DEFAULT_LINGUISTIC,
            sample_exchanges=[],
            negative_constraints=[],
            system_instruction="Should NOT be returned",
        )
        # Skip _activate call — profile stays is_active=False.

        service = BrandVoiceService(repo=repo)
        result = await service.compile_system_instruction(TENANT_A)

        assert result == ""


# ---------------------------------------------------------------------------
# Test 4 — get_voice_metadata behavior
# ---------------------------------------------------------------------------


class TestGetVoiceMetadata:
    """get_voice_metadata returns populated dict or empty default."""

    @pytest.mark.asyncio
    async def test_returns_populated_metadata_when_profile_active(self, db: Session, seed_tenant) -> None:
        """When active profile exists, return version + last_compiled_at + dimensions_summary."""
        repo = PersonalityProfileRepository(db)
        model = repo.create(
            tenant_id=TENANT_A,
            name="Voice Profile",
            profile_type="preset",
            dimensions=_DEFAULT_DIMENSIONS,
            linguistic_patterns=_DEFAULT_LINGUISTIC,
            sample_exchanges=[],
            negative_constraints=[],
            system_instruction="cached",
        )
        _activate(repo, model, TENANT_A)

        service = BrandVoiceService(repo=repo)
        meta = await service.get_voice_metadata(TENANT_A)

        # Schema cement (FROZEN per port docstring).
        assert set(meta.keys()) == {
            "personality_profile_version",
            "last_compiled_at",
            "dimensions_summary",
        }
        # Version defaults to 1 when ORM has no explicit version column.
        assert meta["personality_profile_version"] == 1
        # dimensions_summary copies JSONB dimensions verbatim.
        assert meta["dimensions_summary"]["energy"] == 0.65
        assert meta["dimensions_summary"]["warmth"] == 0.85
        # last_compiled_at falls back to created_at when no updated_at;
        # value may be None if ORM hasn't set it — but the key MUST exist.
        assert "last_compiled_at" in meta

    @pytest.mark.asyncio
    async def test_returns_empty_default_when_no_active_profile(self, db: Session, seed_tenant) -> None:
        """When tenant has no active profile, return empty default schema."""
        repo = PersonalityProfileRepository(db)
        service = BrandVoiceService(repo=repo)

        meta = await service.get_voice_metadata(TENANT_A)

        assert meta == {
            "personality_profile_version": 0,
            "last_compiled_at": None,
            "dimensions_summary": {},
        }


# ---------------------------------------------------------------------------
# Test 5 — Tenant isolation (cardinal — every method takes tenant_id)
# ---------------------------------------------------------------------------


class TestTenantIsolation:
    """Service MUST honor tenant_id boundary — no cross-tenant leaks."""

    @pytest.mark.asyncio
    async def test_compile_does_not_leak_across_tenants(self, db: Session, seed_tenant, seed_other_tenant) -> None:
        """Profile for TENANT_A MUST NOT surface for TENANT_B's compile call."""
        repo = PersonalityProfileRepository(db)
        model_a = repo.create(
            tenant_id=TENANT_A,
            name="Tenant A Voice",
            profile_type="preset",
            dimensions=_DEFAULT_DIMENSIONS,
            linguistic_patterns=_DEFAULT_LINGUISTIC,
            sample_exchanges=[],
            negative_constraints=[],
            system_instruction="TENANT_A_VOICE_SECRET",
        )
        _activate(repo, model_a, TENANT_A)

        service = BrandVoiceService(repo=repo)

        result_a = await service.compile_system_instruction(TENANT_A)
        result_b = await service.compile_system_instruction(TENANT_B)

        assert result_a == "TENANT_A_VOICE_SECRET"
        assert result_b == ""  # TENANT_B has no profile

    @pytest.mark.asyncio
    async def test_metadata_does_not_leak_across_tenants(self, db: Session, seed_tenant, seed_other_tenant) -> None:
        """Metadata for TENANT_A MUST NOT surface for TENANT_B."""
        repo = PersonalityProfileRepository(db)
        model_a = repo.create(
            tenant_id=TENANT_A,
            name="Tenant A Voice",
            profile_type="preset",
            dimensions=_DEFAULT_DIMENSIONS,
            linguistic_patterns=_DEFAULT_LINGUISTIC,
            sample_exchanges=[],
            negative_constraints=[],
            system_instruction="cached",
        )
        _activate(repo, model_a, TENANT_A)

        service = BrandVoiceService(repo=repo)

        meta_a = await service.get_voice_metadata(TENANT_A)
        meta_b = await service.get_voice_metadata(TENANT_B)

        assert meta_a["dimensions_summary"]["energy"] == 0.65
        assert meta_b["dimensions_summary"] == {}  # TENANT_B empty
        assert meta_b["personality_profile_version"] == 0
