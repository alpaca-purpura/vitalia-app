# cap: iam.iam-scaffold-slice-1
"""Arch fitness: VITALIA_AUTH_STUB must NOT be set in runtime config files.

Per Q2 (spec v2) + AD-4 (03-arch): the stub decoder path is test-only.
Runtime and dev-app MUST always use JWKS real verification.

Asserts:
  1. vitalia/.env.dev.template does NOT contain VITALIA_AUTH_STUB
  2. vitalia/docker-compose.dev.yml does NOT contain VITALIA_AUTH_STUB
  3. ClerkJwtDecoder.decode() raises JwtDecodeError (not parse stub) when
     VITALIA_AUTH_STUB is absent and token starts with "stub:"

Story: vitalia-iam-slice2-phi-real-auth · T-1 (arch gate)
Cement-date: 2026-05-29

downstream-regression-na: brand-local arch fitness for auth stub env gate
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch


def _ws_root() -> Path:
    """Return workspace root (4 levels up from this file)."""
    return Path(__file__).resolve().parents[4]


class TestAuthStubEnvGate:
    """VITALIA_AUTH_STUB must never appear in runtime configuration."""

    def test_env_dev_template_does_not_contain_auth_stub(self) -> None:
        """vitalia/.env.dev.template must NOT set VITALIA_AUTH_STUB."""
        env_template = _ws_root() / "vitalia" / ".env.dev.template"
        if not env_template.exists():
            return  # Template not present — no violation possible

        content = env_template.read_text(encoding="utf-8")
        assert "VITALIA_AUTH_STUB" not in content, (
            "vitalia/.env.dev.template MUST NOT contain VITALIA_AUTH_STUB.\n"
            "This env var is test-only (VITALIA_AUTH_STUB=1 activates stub decoder).\n"
            "Runtime ALWAYS uses JWKS real verification (AD-4, spec v2 Q2)."
        )

    def test_docker_compose_dev_does_not_contain_auth_stub(self) -> None:
        """vitalia/docker-compose.dev.yml must NOT set VITALIA_AUTH_STUB."""
        compose_file = _ws_root() / "vitalia" / "docker-compose.dev.yml"
        if not compose_file.exists():
            return  # File not present — no violation possible

        content = compose_file.read_text(encoding="utf-8")
        assert "VITALIA_AUTH_STUB" not in content, (
            "vitalia/docker-compose.dev.yml MUST NOT contain VITALIA_AUTH_STUB.\n"
            "This env var is test-only. Runtime always uses JWKS real verification (AD-4)."
        )

    def test_decoder_rejects_stub_token_when_stub_env_absent(self) -> None:
        """ClerkJwtDecoder must NOT accept stub:... tokens in runtime (no env).

        When VITALIA_AUTH_STUB is absent (default runtime mode), the decoder
        MUST attempt JWKS verification on any token — including stub: prefixed ones.
        It should raise JwtDecodeError, NOT silently parse the stub format.
        """
        from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
            ClerkJwtDecoder,
            JwtDecodeError,
        )

        decoder = ClerkJwtDecoder()

        # Ensure VITALIA_AUTH_STUB is not set (simulate runtime env)
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("VITALIA_AUTH_STUB", None)

            # A stub-format token MUST be rejected (goes to JWKS path → fails)
            import pytest

            with pytest.raises(JwtDecodeError):
                decoder.decode("stub:tenant-id:clinic-id:doctor:user-123")

    def test_decoder_accepts_stub_token_only_when_stub_env_set(self) -> None:
        """ClerkJwtDecoder accepts stub:... tokens ONLY when VITALIA_AUTH_STUB=1.

        This validates the correct conditional: stub path is opt-in for tests,
        never the default runtime behavior.
        """
        from uuid import uuid4

        from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
            ClerkJwtDecoder,
        )

        decoder = ClerkJwtDecoder()
        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        stub_token = f"stub:{tenant_id}:{clinic_id}:doctor:user_test123"

        with patch.dict(os.environ, {"VITALIA_AUTH_STUB": "1"}):
            payload = decoder.decode(stub_token)
            assert payload.user_id == "user_test123"
            assert payload.role == "doctor"
