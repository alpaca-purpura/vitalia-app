# cap: iam.iam-scaffold-slice-1
# story-origin: vitalia-iam-slice2-phi-real-auth
"""Clerk JWT decoder — Slice 2: JWKS real verification via engine import.

Infrastructure layer — validates Clerk JWTs using the shared engine JWKS client.

Slice 2 changes (per AD-4):
  - decode() uses verify_token_payload from luana_core_iam (engine JWKS).
  - Stub path is ONLY active when VITALIA_AUTH_STUB=1 env var is set AND
    token starts with "stub:". This is test-only; runtime NEVER sets this env.
  - ClerkJwtPayload shape is preserved (consumers unchanged).
  - For real JWTs: user_id = payload["sub"]; tenant_id/clinic_id/role
    are set to "" (resolved from headers + DB by ClinicResolver, not from token).

Anti-duplication: NEVER recreate PyJWKClient or JWKS logic brand-local.
Consume via import: from luana_core_iam.application.auth import verify_token_payload
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import structlog
from fastapi import HTTPException
from luana_core_iam.application.auth import verify_token_payload

from src.modules.vitalia.iam.domain.role import VitaliaRole

logger = structlog.get_logger()

_STUB_PREFIX = "stub:"


class JwtDecodeError(Exception):
    """Raised when a JWT token cannot be decoded or validated."""


@dataclass(frozen=True)
class ClerkJwtPayload:
    """Parsed payload from a Clerk JWT token.

    Value object — immutable after construction.

    For real JWTs:
      - user_id = payload["sub"] (Clerk user ID string)
      - tenant_id / clinic_id = "" (resolved from X-Tenant-ID / X-Clinic-ID headers)
      - role = "" (resolved from user_tenants DB by ClinicResolver)
      - email / name = from token claims if present

    For stub tokens (test-only, VITALIA_AUTH_STUB=1):
      - All fields parsed from "stub:{tenant_id}:{clinic_id}:{role}:{user_id}"
    """

    user_id: str
    tenant_id: str
    clinic_id: str
    role: str
    email: str | None
    name: str | None


class ClerkJwtDecoder:
    """Decodes Clerk JWT tokens.

    Slice 2: uses JWKS real verification via luana_core_iam engine (AD-4).
    Stub path active ONLY when VITALIA_AUTH_STUB=1 (test env).
    """

    def decode(self, token: str) -> ClerkJwtPayload:
        """Decode a token and return its payload.

        For real tokens: calls verify_token_payload (engine JWKS).
        For stub tokens: only if VITALIA_AUTH_STUB=1 (test-only).

        Args:
            token: Bearer token string.

        Returns:
            ClerkJwtPayload with extracted claims.

        Raises:
            JwtDecodeError: If the token is empty, invalid, expired, or forged.
                            Also raised if stub token used without VITALIA_AUTH_STUB=1.
        """
        if not token:
            raise JwtDecodeError("Token vacío.")

        # Stub path: ONLY active in test mode (VITALIA_AUTH_STUB=1)
        # Runtime NEVER sets this env → this branch never runs in production
        if os.environ.get("VITALIA_AUTH_STUB") == "1" and token.startswith(_STUB_PREFIX):
            return self._decode_stub(token)

        # Real path: delegate to engine JWKS verification
        return self._decode_real(token)

    def _decode_real(self, token: str) -> ClerkJwtPayload:
        """Decode a real Clerk JWT using the engine JWKS client.

        Converts HTTPException(401) from engine into JwtDecodeError
        to keep the caller interface consistent.

        Args:
            token: Clerk JWT string (RS256, signed by Clerk).

        Returns:
            ClerkJwtPayload with user_id from "sub" claim.

        Raises:
            JwtDecodeError: If token is invalid, expired, or cannot be verified.
        """
        try:
            payload = verify_token_payload(token)
        except HTTPException as exc:
            # Engine raises HTTPException(401) on invalid JWT.
            # Map to JwtDecodeError to keep our interface — caller maps to HTTP 401.
            # Do NOT include internal details in the error message (security + PHI safety).
            logger.warning(
                "iam.clerk_jwt_decoder.invalid_token",
                status_code=exc.status_code,
            )
            raise JwtDecodeError("Token inválido o expirado.") from exc
        except Exception as exc:
            logger.exception("iam.clerk_jwt_decoder.unexpected_error")
            raise JwtDecodeError("No se pudieron verificar las credenciales.") from exc

        return ClerkJwtPayload(
            user_id=payload.get("sub", ""),
            tenant_id="",  # Not in JWT — resolved from X-Tenant-ID header by ClinicResolver
            clinic_id="",  # Not in JWT — resolved from X-Clinic-ID header by ClinicResolver
            role="",  # Not in JWT — resolved from user_tenants DB by ClinicResolver
            email=payload.get("email") or payload.get("primary_email_address"),
            name=payload.get("name") or payload.get("full_name"),
        )

    def _decode_stub(self, token: str) -> ClerkJwtPayload:
        """Parse stub token: stub:{tenant_id}:{clinic_id}:{role}:{user_id}.

        TEST-ONLY: only reachable when VITALIA_AUTH_STUB=1.
        """
        parts = token[len(_STUB_PREFIX) :].split(":")
        if len(parts) != 4:
            raise JwtDecodeError(f"Stub token must have 4 parts after 'stub:' prefix, got {len(parts)}: '{token}'")

        tenant_id, clinic_id, role_str, user_id = parts

        # Validate role
        try:
            VitaliaRole(role_str)
        except ValueError:
            raise JwtDecodeError(
                f"Unknown role '{role_str}' in stub token. Valid roles: {[r.value for r in VitaliaRole]}"
            )

        return ClerkJwtPayload(
            user_id=user_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            role=role_str,
            email=f"{user_id}@stub.vitalia.test",
            name=f"Stub User ({role_str})",
        )
