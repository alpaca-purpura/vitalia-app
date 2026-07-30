"""Tests for ClinicResolver — resolve_current_clinic flow.

TDD: RED tests defined before implementation (T-infra-9).

downstream-regression-na: brand-local IAM clinic resolver tests
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from src.modules.vitalia.iam.application.services.clinic_resolver import (
    ClinicContext,
    ClinicResolver,
    MissingAuthHeaderError,
)
from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
    ClerkJwtDecoder,
    ClerkJwtPayload,
)


def _make_payload(
    role: str = "doctor",
    tenant_id: str | None = None,
    clinic_id: str | None = None,
) -> ClerkJwtPayload:
    return ClerkJwtPayload(
        user_id="user_test",
        tenant_id=tenant_id or str(uuid4()),
        clinic_id=clinic_id or str(uuid4()),
        role=role,
        email="test@clinic.com",
        name="Test User",
    )


class TestClinicContext:
    """ClinicContext dataclass shape."""

    def test_context_has_required_fields(self) -> None:
        tid = uuid4()
        cid = uuid4()
        ctx = ClinicContext(
            user_id="user_abc",
            tenant_id=tid,
            clinic_id=cid,
            role="doctor",
            email="doc@clinic.com",
            name="Dr. Garcia",
        )
        assert ctx.tenant_id == tid
        assert ctx.clinic_id == cid
        assert ctx.role == "doctor"


class TestClinicResolver:
    """ClinicResolver extracts ClinicContext from JWT claims."""

    def _make_resolver(self, payload: ClerkJwtPayload) -> ClinicResolver:
        mock_decoder = MagicMock(spec=ClerkJwtDecoder)
        mock_decoder.decode.return_value = payload
        return ClinicResolver(decoder=mock_decoder)

    def test_resolve_returns_clinic_context(self) -> None:
        payload = _make_payload(role="nurse")
        resolver = self._make_resolver(payload)
        ctx = resolver.resolve("stub:token")
        assert ctx.role == "nurse"
        assert isinstance(ctx.tenant_id, UUID)
        assert isinstance(ctx.clinic_id, UUID)

    def test_resolve_raises_on_empty_token(self) -> None:
        mock_decoder = MagicMock(spec=ClerkJwtDecoder)
        resolver = ClinicResolver(decoder=mock_decoder)
        with pytest.raises(MissingAuthHeaderError):
            resolver.resolve("")

    def test_resolve_raises_on_none_token(self) -> None:
        mock_decoder = MagicMock(spec=ClerkJwtDecoder)
        resolver = ClinicResolver(decoder=mock_decoder)
        with pytest.raises(MissingAuthHeaderError):
            resolver.resolve(None)  # type: ignore[arg-type]

    def test_resolve_propagates_decoder_error(self) -> None:
        from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import JwtDecodeError

        mock_decoder = MagicMock(spec=ClerkJwtDecoder)
        mock_decoder.decode.side_effect = JwtDecodeError("bad token")
        resolver = ClinicResolver(decoder=mock_decoder)
        with pytest.raises(JwtDecodeError):
            resolver.resolve("bad_token")

    def test_resolve_converts_string_ids_to_uuid(self) -> None:
        tid = str(uuid4())
        cid = str(uuid4())
        payload = _make_payload(tenant_id=tid, clinic_id=cid)
        resolver = self._make_resolver(payload)
        ctx = resolver.resolve("stub:any_token")
        assert ctx.tenant_id == UUID(tid)
        assert ctx.clinic_id == UUID(cid)
