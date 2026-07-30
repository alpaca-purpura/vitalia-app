"""Tests for ClerkJwtDecoder — Slice 2 (JWKS real + stub env-gated).

TDD: tests RED before implementation (T-infra-9 Slice 1 + T-1 Slice 2).

Slice 2 changes tested:
  - Stub path now requires VITALIA_AUTH_STUB=1 env var.
  - Real JWT path calls verify_token_payload (engine JWKS).
  - Stub token without VITALIA_AUTH_STUB=1 → JwtDecodeError (goes to JWKS).

downstream-regression-na: brand-local IAM JWT decoder tests
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
    ClerkJwtDecoder,
    ClerkJwtPayload,
    JwtDecodeError,
)


class TestClerkJwtPayload:
    """ClerkJwtPayload dataclass shape."""

    def test_payload_has_user_id(self) -> None:
        from uuid import uuid4

        p = ClerkJwtPayload(
            user_id="user_abc123",
            tenant_id=str(uuid4()),
            clinic_id=str(uuid4()),
            role="doctor",
            email="doc@clinic.com",
            name="Dr. Garcia",
        )
        assert p.user_id == "user_abc123"

    def test_payload_has_role(self) -> None:
        from uuid import uuid4

        p = ClerkJwtPayload(
            user_id="user_abc123",
            tenant_id=str(uuid4()),
            clinic_id=str(uuid4()),
            role="nurse",
            email="nurse@clinic.com",
            name="Enfermera Lopez",
        )
        assert p.role == "nurse"

    def test_payload_email_optional(self) -> None:
        from uuid import uuid4

        p = ClerkJwtPayload(
            user_id="user_xyz",
            tenant_id=str(uuid4()),
            clinic_id=str(uuid4()),
            role="receptionist",
            email=None,
            name=None,
        )
        assert p.email is None


class TestClerkJwtDecoderStubPath:
    """ClerkJwtDecoder stub path — requires VITALIA_AUTH_STUB=1 (test-only)."""

    def setup_method(self) -> None:
        self.decoder = ClerkJwtDecoder()

    def test_decode_returns_payload_for_stub_token_when_env_set(self) -> None:
        """Stub decoder accepts stub:... token ONLY when VITALIA_AUTH_STUB=1."""
        from uuid import uuid4

        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        token = f"stub:{tenant_id}:{clinic_id}:doctor:user_test123"

        with patch.dict(os.environ, {"VITALIA_AUTH_STUB": "1"}):
            payload = self.decoder.decode(token)

        assert payload.tenant_id == tenant_id
        assert payload.clinic_id == clinic_id
        assert payload.role == "doctor"
        assert payload.user_id == "user_test123"

    def test_decode_raises_on_empty_token(self) -> None:
        with pytest.raises(JwtDecodeError):
            self.decoder.decode("")

    def test_decode_raises_on_stub_token_without_env(self) -> None:
        """Stub token WITHOUT VITALIA_AUTH_STUB=1 → goes to JWKS path → JwtDecodeError."""
        from uuid import uuid4

        from fastapi import HTTPException

        token = f"stub:{uuid4()}:{uuid4()}:doctor:user_test"

        # Engine raises HTTPException(401) for stub token (not a valid JWT)
        with patch(
            "src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder.verify_token_payload",
            side_effect=HTTPException(status_code=401, detail="Invalid Token"),
        ):
            os.environ.pop("VITALIA_AUTH_STUB", None)
            with pytest.raises(JwtDecodeError):
                self.decoder.decode(token)

    def test_decode_raises_for_unknown_role_in_stub_when_env_set(self) -> None:
        from uuid import uuid4

        token = f"stub:{uuid4()}:{uuid4()}:superuser:user_999"

        with patch.dict(os.environ, {"VITALIA_AUTH_STUB": "1"}):
            with pytest.raises(JwtDecodeError, match="Unknown role"):
                self.decoder.decode(token)

    def test_stub_path_requires_4_parts_when_env_set(self) -> None:
        """Malformed stub token (wrong parts) raises JwtDecodeError."""
        with patch.dict(os.environ, {"VITALIA_AUTH_STUB": "1"}):
            with pytest.raises(JwtDecodeError):
                self.decoder.decode("stub:only-two-parts")


class TestClerkJwtDecoderRealPath:
    """ClerkJwtDecoder real JWT path — delegates to engine JWKS."""

    def setup_method(self) -> None:
        self.decoder = ClerkJwtDecoder()

    def test_real_token_calls_verify_token_payload(self) -> None:
        """Real JWT (non-stub) → calls verify_token_payload from engine."""
        fake_payload = {
            "sub": "user_real_clerk_id",
            "email": "real@clinic.com",
            "full_name": "Real Doctor",
        }

        with patch(
            "src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder.verify_token_payload",
            return_value=fake_payload,
        ) as mock_verify:
            os.environ.pop("VITALIA_AUTH_STUB", None)
            payload = self.decoder.decode("eyJhbGciOiJSUzI1NiJ9.real_token")

        mock_verify.assert_called_once_with("eyJhbGciOiJSUzI1NiJ9.real_token")
        assert payload.user_id == "user_real_clerk_id"
        assert payload.email == "real@clinic.com"
        # tenant_id / clinic_id / role are empty for real tokens (from headers+DB)
        assert payload.tenant_id == ""
        assert payload.clinic_id == ""
        assert payload.role == ""

    def test_real_token_maps_sub_to_user_id(self) -> None:
        """payload['sub'] is mapped to ClerkJwtPayload.user_id."""
        fake_payload = {"sub": "user_CLERK123", "email": None}

        with patch(
            "src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder.verify_token_payload",
            return_value=fake_payload,
        ):
            os.environ.pop("VITALIA_AUTH_STUB", None)
            payload = self.decoder.decode("any_non_stub_token")

        assert payload.user_id == "user_CLERK123"

    def test_engine_http_exception_401_raises_jwt_decode_error(self) -> None:
        """Engine HTTPException(401) → JwtDecodeError (no leak of internals)."""
        from fastapi import HTTPException

        with patch(
            "src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder.verify_token_payload",
            side_effect=HTTPException(status_code=401, detail="Invalid Token: some_details"),
        ):
            os.environ.pop("VITALIA_AUTH_STUB", None)
            with pytest.raises(JwtDecodeError) as exc_info:
                self.decoder.decode("bad_token_here")

        # The error message must NOT leak internal engine details
        assert "some_details" not in str(exc_info.value)

    def test_engine_http_exception_500_raises_jwt_decode_error(self) -> None:
        """Engine HTTPException(500) (e.g. CLERK_ISSUER missing) → JwtDecodeError."""
        from fastapi import HTTPException

        with patch(
            "src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder.verify_token_payload",
            side_effect=HTTPException(status_code=500, detail="Server misconfiguration"),
        ):
            os.environ.pop("VITALIA_AUTH_STUB", None)
            with pytest.raises(JwtDecodeError):
                self.decoder.decode("any_token")
