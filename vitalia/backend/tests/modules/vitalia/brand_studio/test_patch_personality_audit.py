"""T-2 / T-2.bis — camelCase alias + telemetry tenant_id regression tests.

Verifies that:
  1. camelCase voice-block fields (soISpeak, identityAnchor, etc.) are accepted in PATCH.
  2. snake_case fields still accepted (populate_by_name=True).
  3. Genuinely-extra fields are still rejected (extra="forbid").
  4. Invalid archetype value triggers ValidationError / 422.
  5. Valid archetype ("sage") is accepted.
  6. Response serializes with camelCase keys (by_alias=True in router).
  7. Cross-tenant: PATCH service receives only the requesting tenant_id.

§ 1 — DTO-level unit tests: no integration mark (run without Postgres).
§ 2 — HTTP route-level tests: @pytest.mark.integration (skipped without Postgres).
§ 3 — Cross-tenant isolation: @pytest.mark.integration.
§ 4 — T-2.bis: _emit_telemetry forwards tenant_id to emit_event (unit, no DB).
      RED before fix: GrowthStudioEmitter.emit_event() missing 1 required keyword-only
      argument: 'tenant_id' (swallowed, event silently lost).
      GREEN after: emit_event called with tenant_id= kwarg present.

Story: arreglar-guardado-voz-y-tono / T-2 + T-2.bis
cap: brand_studio.lisa-marca
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from pydantic import ValidationError

from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import (
    BrandPersonalityDTO,
    BrandPersonalityPatchDTO,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_TENANT_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
_USER_A = "11111111-1111-1111-1111-111111111111"
_PROFILE_ID = "22222222-2222-2222-2222-222222222222"

_PERSONALITY_URL = "/api/v1/lisa/marca/personality"


def _make_full_personality(tenant_id: str = _TENANT_A) -> BrandPersonalityDTO:
    return BrandPersonalityDTO(
        tenant_id=UUID(tenant_id),
        personality_profile_id=UUID(_PROFILE_ID),
        archetype="caregiver",
        so_i_speak="Hablo con claridad y empatía.",
        so_i_dont_speak="No uso tecnicismos sin contexto.",
        technical_context="Contexto médico-dental.",
        format_instructions="Frases cortas, lenguaje neutro.",
        identity_anchor="Clínica Bienestar — tu salud primero.",
        domain_context="Salud preventiva LatAm.",
        compiled_at=datetime.now(timezone.utc),
        compiler_version="v2",
    )


# ---------------------------------------------------------------------------
# § 1  DTO-level (pure Pydantic) — NO integration mark, runs without Postgres
# ---------------------------------------------------------------------------


class TestBrandPersonalityPatchDTOAlias:
    """Unit tests on the Pydantic DTO directly (no app / no DB required)."""

    def test_camel_case_so_i_speak_accepted(self) -> None:
        """camelCase field soISpeak must not raise ValidationError.

        RED before alias fix: ValidationError extra_forbidden.
        GREEN after: model accepts camelCase via alias_generator=to_camel.
        """
        dto = BrandPersonalityPatchDTO.model_validate({"soISpeak": "hola"})
        assert dto.so_i_speak == "hola"

    def test_camel_case_so_i_dont_speak_accepted(self) -> None:
        dto = BrandPersonalityPatchDTO.model_validate({"soIDontSpeak": "nunca"})
        assert dto.so_i_dont_speak == "nunca"

    def test_camel_case_identity_anchor_accepted(self) -> None:
        dto = BrandPersonalityPatchDTO.model_validate({"identityAnchor": "Clínica XYZ"})
        assert dto.identity_anchor == "Clínica XYZ"

    def test_camel_case_domain_context_accepted(self) -> None:
        dto = BrandPersonalityPatchDTO.model_validate({"domainContext": "Salud LatAm"})
        assert dto.domain_context == "Salud LatAm"

    def test_camel_case_technical_context_accepted(self) -> None:
        dto = BrandPersonalityPatchDTO.model_validate({"technicalContext": "Contexto técnico"})
        assert dto.technical_context == "Contexto técnico"

    def test_camel_case_format_instructions_accepted(self) -> None:
        dto = BrandPersonalityPatchDTO.model_validate({"formatInstructions": "Frases cortas"})
        assert dto.format_instructions == "Frases cortas"

    def test_snake_case_still_accepted_populate_by_name(self) -> None:
        """snake_case must still work (populate_by_name=True)."""
        dto = BrandPersonalityPatchDTO.model_validate({"so_i_speak": "serpiente"})
        assert dto.so_i_speak == "serpiente"

    def test_genuinely_extra_field_rejected(self) -> None:
        """A field not in the model schema must still be rejected (extra='forbid').

        'bogusField' maps to no snake_case field → still extra_forbidden.
        """
        with pytest.raises(ValidationError, match="extra"):
            BrandPersonalityPatchDTO.model_validate({"bogusField": "x"})

    def test_archetype_valid_sage_accepted(self) -> None:
        """Valid archetype value 'sage' must be accepted."""
        dto = BrandPersonalityPatchDTO.model_validate({"archetype": "sage"})
        assert dto.archetype == "sage"

    def test_archetype_invalid_value_rejected(self) -> None:
        """Invalid archetype like 'sabio' must trigger ValidationError."""
        with pytest.raises(ValidationError):
            BrandPersonalityPatchDTO.model_validate({"archetype": "sabio"})

    def test_all_none_patch_accepted(self) -> None:
        """Empty patch (all fields None) is valid — partial update."""
        dto = BrandPersonalityPatchDTO.model_validate({})
        assert dto.archetype is None
        assert dto.so_i_speak is None


class TestBrandPersonalityDTOResponseCamelCase:
    """Response DTO serializes with camelCase aliases (by_alias=True)."""

    def test_response_serializes_so_i_speak_as_camel(self) -> None:
        """Serialized response must use 'soISpeak', NOT 'so_i_speak'.

        RED before fix: key is 'so_i_speak'.
        GREEN after alias_generator=to_camel: key is 'soISpeak'.
        """
        dto = BrandPersonalityDTO(
            tenant_id=UUID(_TENANT_A),
            personality_profile_id=UUID(_PROFILE_ID),
            archetype="sage",
            so_i_speak="Hablo con claridad.",
            so_i_dont_speak="No uso jerga.",
            technical_context="Contexto.",
            format_instructions="Frases cortas.",
            identity_anchor="Clínica XYZ.",
            domain_context="Salud preventiva.",
            compiled_at=None,
            compiler_version="v2",
        )
        data = dto.model_dump(by_alias=True)
        assert "soISpeak" in data, f"Expected 'soISpeak' key; got keys: {list(data.keys())}"
        assert "so_i_speak" not in data

    def test_response_serializes_identity_anchor_as_camel(self) -> None:
        dto = _make_full_personality()
        data = dto.model_dump(by_alias=True)
        assert "identityAnchor" in data
        assert "identity_anchor" not in data

    def test_response_serializes_tenant_id_as_camel(self) -> None:
        dto = _make_full_personality()
        data = dto.model_dump(by_alias=True)
        assert "tenantId" in data
        assert "tenant_id" not in data

    def test_response_serializes_personality_profile_id_as_camel(self) -> None:
        dto = _make_full_personality()
        data = dto.model_dump(by_alias=True)
        assert "personalityProfileId" in data
        assert "personality_profile_id" not in data

    def test_snake_case_construction_still_works(self) -> None:
        """BrandPersonalityDTO can be constructed with snake_case kwargs (populate_by_name)."""
        dto = BrandPersonalityDTO(
            tenant_id=UUID(_TENANT_A),
            personality_profile_id=UUID(_PROFILE_ID),
            archetype="caregiver",
            so_i_speak="test",
            so_i_dont_speak="test",
            technical_context="test",
            format_instructions="test",
            identity_anchor="test",
            domain_context="test",
            compiled_at=None,
            compiler_version="v2",
        )
        assert dto.so_i_speak == "test"


# ---------------------------------------------------------------------------
# § 2  HTTP route-level — @pytest.mark.integration (skipped without Postgres)
# ---------------------------------------------------------------------------

# NOTE: these tests import src.main (needs env vars) — they use @pytest.mark.integration
# so they auto-skip when Postgres is unavailable, consistent with existing router tests.


@pytest.fixture
def app():
    """Vitalia FastAPI app instance."""
    from src.main import app as vitalia_app

    return vitalia_app


@pytest.mark.integration
@pytest.mark.asyncio
class TestPatchPersonalityRouteAlias:
    """HTTP PATCH /personality — camelCase body must NOT return 422."""

    async def test_camel_case_voice_block_not_rejected_as_extra(self, app) -> None:
        """PATCH with camelCase soISpeak body must reach service (not 422).

        Repro from bug: 422 extra_forbidden on soISpeak.
        """
        from httpx import AsyncClient

        with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
            mock_bundle = AsyncMock()
            mock_bundle.marca.patch_personality.return_value = _make_full_personality()
            mock_build.return_value = mock_bundle

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.patch(
                    _PERSONALITY_URL,
                    json={"soISpeak": "hola"},
                    headers={
                        "X-Tenant-ID": _TENANT_A,
                        "X-User-ID": _USER_A,
                        "X-User-Role": "owner",
                    },
                )

        assert response.status_code != 422, (
            f"camelCase soISpeak triggered 422 — alias_generator not applied. Response: {response.text}"
        )

    async def test_patch_snake_case_still_accepted(self, app) -> None:
        """PATCH with snake_case body also accepted (populate_by_name=True)."""
        from httpx import AsyncClient

        with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
            mock_bundle = AsyncMock()
            mock_bundle.marca.patch_personality.return_value = _make_full_personality()
            mock_build.return_value = mock_bundle

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.patch(
                    _PERSONALITY_URL,
                    json={"so_i_speak": "serpiente"},
                    headers={
                        "X-Tenant-ID": _TENANT_A,
                        "X-User-ID": _USER_A,
                        "X-User-Role": "owner",
                    },
                )

        assert response.status_code != 422

    async def test_patch_bogus_field_still_rejected(self, app) -> None:
        """extra='forbid' still blocks genuinely-extra fields after alias fix."""
        from httpx import AsyncClient

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.patch(
                _PERSONALITY_URL,
                json={"bogusField": "x"},
                headers={
                    "X-Tenant-ID": _TENANT_A,
                    "X-User-ID": _USER_A,
                    "X-User-Role": "owner",
                },
            )
        assert response.status_code == 422

    async def test_patch_invalid_archetype_returns_422(self, app) -> None:
        """Archetype value not in Literal returns 422."""
        from httpx import AsyncClient

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.patch(
                _PERSONALITY_URL,
                json={"archetype": "sabio"},
                headers={
                    "X-Tenant-ID": _TENANT_A,
                    "X-User-ID": _USER_A,
                    "X-User-Role": "owner",
                },
            )
        assert response.status_code == 422

    async def test_patch_valid_archetype_sage_accepted(self, app) -> None:
        """Archetype 'sage' must pass validation and reach service."""
        from httpx import AsyncClient

        with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
            mock_bundle = AsyncMock()
            mock_bundle.marca.patch_personality.return_value = _make_full_personality()
            mock_build.return_value = mock_bundle

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.patch(
                    _PERSONALITY_URL,
                    json={"archetype": "sage"},
                    headers={
                        "X-Tenant-ID": _TENANT_A,
                        "X-User-ID": _USER_A,
                        "X-User-Role": "owner",
                    },
                )

        assert response.status_code == 200

    async def test_response_contains_camel_case_keys(self, app) -> None:
        """GET /personality response keys must be camelCase (by_alias serialization)."""
        from httpx import AsyncClient

        with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
            mock_bundle = AsyncMock()
            mock_bundle.marca.get_personality.return_value = _make_full_personality()
            mock_build.return_value = mock_bundle

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    _PERSONALITY_URL,
                    headers={"X-Tenant-ID": _TENANT_A},
                )

        assert response.status_code == 200
        data = response.json()
        assert "soISpeak" in data, f"Expected camelCase 'soISpeak'; got: {list(data.keys())}"
        assert "so_i_speak" not in data


# ---------------------------------------------------------------------------
# § 3  Cross-tenant isolation — @pytest.mark.integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
class TestPatchPersonalityCrossTenantIsolation:
    """Cross-tenant: tenant_A request must never leak tenant_B to the service."""

    async def test_patch_personality_service_receives_correct_tenant(self, app) -> None:
        """Service is called with tenant_A UUID, not tenant_B."""
        from httpx import AsyncClient

        with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
            mock_bundle = AsyncMock()
            mock_bundle.marca.patch_personality.return_value = _make_full_personality()
            mock_build.return_value = mock_bundle

            async with AsyncClient(app=app, base_url="http://test") as client:
                await client.patch(
                    _PERSONALITY_URL,
                    json={"archetype": "sage"},
                    headers={
                        "X-Tenant-ID": _TENANT_A,
                        "X-User-ID": _USER_A,
                        "X-User-Role": "owner",
                    },
                )

            call_kwargs = mock_bundle.marca.patch_personality.call_args.kwargs
            assert str(call_kwargs["tenant_id"]) == _TENANT_A
            assert str(call_kwargs["tenant_id"]) != _TENANT_B

    async def test_patch_personality_tenant_b_header_sends_only_tenant_b(self, app) -> None:
        """When X-Tenant-ID is tenant_B, service ONLY receives tenant_B."""
        from httpx import AsyncClient

        with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
            mock_bundle = AsyncMock()
            mock_bundle.marca.patch_personality.return_value = _make_full_personality(_TENANT_B)
            mock_build.return_value = mock_bundle

            async with AsyncClient(app=app, base_url="http://test") as client:
                await client.patch(
                    _PERSONALITY_URL,
                    json={"archetype": "sage"},
                    headers={
                        "X-Tenant-ID": _TENANT_B,
                        "X-User-ID": _USER_A,
                        "X-User-Role": "owner",
                    },
                )

            call_kwargs = mock_bundle.marca.patch_personality.call_args.kwargs
            assert str(call_kwargs["tenant_id"]) == _TENANT_B
            assert str(call_kwargs["tenant_id"]) != _TENANT_A


# ---------------------------------------------------------------------------
# § 4  T-2.bis — _emit_telemetry forwards tenant_id to emit_event (unit, no DB)
#
# Root cause: _emit_telemetry(event_type, **props) silently swallowed every
# GrowthStudioEmitter.emit_event() call because it never forwarded `tenant_id`
# (keyword-only required arg). TypeError was caught by bare `except Exception`
# → every brand_studio save lost its telemetry event silently.
#
# RED before fix: emit_event is called WITHOUT tenant_id kwarg → TypeError.
# GREEN after fix: emit_event awaited with tenant_id= present.
# ---------------------------------------------------------------------------


class TestEmitTelemetryForwardsTenantId:
    """Unit: MarcaService._emit_telemetry passes tenant_id to GrowthStudioEmitter.emit_event.

    No DB required — GrowthStudioEmitter mocked via AsyncMock.
    """

    def _make_service(self, mock_emitter: AsyncMock) -> object:  # MarcaService (imported lazily)
        """Build a MarcaService with all dependencies mocked except the emitter."""
        from unittest.mock import AsyncMock as _AsyncMock

        from src.modules.vitalia.brand_studio.application.services.marca_service import MarcaService

        return MarcaService(
            session=_AsyncMock(),
            audit=_AsyncMock(),
            telemetry=mock_emitter,
            voice_preview_service=_AsyncMock(),
            voice_blocklist_service=_AsyncMock(),
            trust_signal_repo=_AsyncMock(),
            trust_catalog_service=_AsyncMock(),
        )

    @pytest.mark.asyncio
    async def test_emit_telemetry_passes_tenant_id_as_kwarg(self) -> None:
        """After fix, emit_event must be awaited with tenant_id= as explicit kwarg.

        RED: emit_event called WITHOUT tenant_id → TypeError swallowed → silent loss.
        GREEN: emit_event awaited with keyword argument tenant_id=<UUID>.
        """
        mock_emitter = AsyncMock()
        mock_emitter.emit_event = AsyncMock()

        service = self._make_service(mock_emitter)
        tenant_id = UUID(_TENANT_A)

        # Exercise: call the helper directly — no DB interactions needed.
        await service._emit_telemetry(
            "lisa_marca_personality_saved",
            tenant_id=tenant_id,
            archetype="caregiver",
            voice_warning_triggered=False,
        )

        # Verify emit_event was awaited exactly once with tenant_id as kwarg.
        mock_emitter.emit_event.assert_awaited_once()
        call_kwargs = mock_emitter.emit_event.call_args.kwargs
        assert "tenant_id" in call_kwargs, (
            f"emit_event NOT called with tenant_id kwarg — it would have raised TypeError. Actual kwargs: {call_kwargs}"
        )
        assert call_kwargs["tenant_id"] == tenant_id
        assert call_kwargs["event_type"] == "lisa_marca_personality_saved"

    @pytest.mark.asyncio
    async def test_emit_telemetry_extra_props_not_in_tenant_id_position(self) -> None:
        """Extra props (archetype, voice_warning_triggered) must NOT be passed as tenant_id.

        Guards against regression where tenant_id is buried in props dict.
        """
        mock_emitter = AsyncMock()
        mock_emitter.emit_event = AsyncMock()

        service = self._make_service(mock_emitter)
        tenant_id = UUID(_TENANT_A)

        await service._emit_telemetry(
            "lisa_marca_personality_saved",
            tenant_id=tenant_id,
            archetype="sage",
        )

        call_kwargs = mock_emitter.emit_event.call_args.kwargs
        # tenant_id must NOT be in props dict — it must be a direct kwarg.
        props = call_kwargs.get("props", {})
        assert "tenant_id" not in props, "tenant_id must be a direct emit_event kwarg, not buried in props dict."

    @pytest.mark.asyncio
    async def test_emit_telemetry_user_id_forwarded_when_present(self) -> None:
        """user_id, when provided, must be forwarded as a direct kwarg to emit_event."""
        mock_emitter = AsyncMock()
        mock_emitter.emit_event = AsyncMock()

        service = self._make_service(mock_emitter)
        tenant_id = UUID(_TENANT_A)
        user_id = UUID(_USER_A)

        await service._emit_telemetry(
            "lisa_marca_trust_signal_added",
            tenant_id=tenant_id,
            user_id=user_id,
        )

        call_kwargs = mock_emitter.emit_event.call_args.kwargs
        assert call_kwargs.get("user_id") == user_id

    @pytest.mark.asyncio
    async def test_emit_telemetry_swallows_exception_gracefully(self) -> None:
        """Exception from emit_event must be caught — never propagated to caller.

        Contract: fire-forget. An exception in telemetry must NOT break the save.
        """
        mock_emitter = AsyncMock()
        mock_emitter.emit_event = AsyncMock(side_effect=Exception("DB down"))

        service = self._make_service(mock_emitter)

        # Must NOT raise — exception is swallowed + logged at WARNING.
        await service._emit_telemetry(
            "lisa_marca_personality_saved",
            tenant_id=UUID(_TENANT_A),
            archetype="caregiver",
        )
