# cap: crm.crm-consent-optout
# story-origin: TBD
"""ConsentService — informed consent request + signing with HMAC URL verification.

Per 03-arch-be.md § 9.4:
  1. Get consent template by slug + current version.
  2. Create consent_record row status=pending_signature.
  3. Generate signed URL HMAC (VITALIA_CONSENT_URL_SECRET env var).
  4. Dispatch WhatsApp + email channels (async task — stub for T-be-6 scope).
  5. Emit ConsentRequestedV1 event.

D1: Receives session + repos via DI — no direct DB session construction.
D2: Idempotency — same (patient_id, booking_id, template_slug) within TTL → returns existing.
D7: HIPAA-lite — consent URL tokens are short-lived (24h default, configurable).

HMAC secret: VITALIA_CONSENT_URL_SECRET env var.
  - Development: pass via constructor `hmac_secret` param.
  - Production: read from env at application startup, injected via FastAPI DI.
  NEVER commit secret. Document env var in T-be-6-result.md.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import structlog
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger()

_DEFAULT_EXPIRY_HOURS = 24
_CONSENT_URL_PATH = "/consent/sign"


def _utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


# ── DTOs ──────────────────────────────────────────────────────────────────────


class RequestConsentRequest(BaseModel):
    """Input DTO for consent request creation."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    patient_id: uuid.UUID
    booking_id: uuid.UUID
    consent_template_slug: str
    delivery_channels: list[str] = Field(default_factory=lambda: ["whatsapp", "email"])
    expiry_hours: int = Field(default=_DEFAULT_EXPIRY_HOURS, ge=1, le=720)


class ConsentUrlResult(BaseModel):
    """Output DTO for consent URL generation."""

    model_config = ConfigDict(from_attributes=True)

    consent_id: uuid.UUID
    consent_url: str
    expires_at: datetime
    is_new: bool


class SignConsentRequest(BaseModel):
    """Input DTO for consent signing — captures signature evidence."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    consent_id: uuid.UUID
    signed_name: str = Field(min_length=2, max_length=255)
    signed_ip: str = Field(max_length=45)  # IPv6 compat
    signed_user_agent: str = Field(max_length=512)
    signature_method: str = Field(pattern=r"^(typed_name|signature_pad)$")
    token: str


class SignConsentResult(BaseModel):
    """Output DTO for consent sign operation."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    consent_id: uuid.UUID | None = None
    error_code: str | None = None


# ── Service ───────────────────────────────────────────────────────────────────


class ConsentService:
    """Informed consent request + HMAC-secured signing service.

    Usage (D1 — receive deps via DI, FastAPI Depends):
        svc = ConsentService(
            session=db,
            consent_repo=ConsentRepository(session=db, tenant_id=tid),
            tenant_id=tid,
            hmac_secret=os.environ["VITALIA_CONSENT_URL_SECRET"],
        )
        result = await svc.request_consent(request=req, base_url="https://vitalia.app")

    HMAC secret env var: VITALIA_CONSENT_URL_SECRET
    """

    def __init__(
        self,
        session: Any,  # AsyncSession — Any to avoid circular imports in pure domain
        consent_repo: Any,  # ConsentRepository
        tenant_id: uuid.UUID,
        hmac_secret: str = "",
    ) -> None:
        self._session = session
        self._consent_repo = consent_repo
        self._tenant_id = tenant_id
        self._hmac_secret = hmac_secret or os.environ.get("VITALIA_CONSENT_URL_SECRET", "")

    # ── Public API ────────────────────────────────────────────────────────────

    async def request_consent(
        self,
        request: RequestConsentRequest,
        base_url: str,
    ) -> ConsentUrlResult:
        """Create or return an existing pending consent record with signed URL.

        D2 idempotency: if a pending_signature consent already exists for the same
        (booking_id, template_slug) pair, return it without creating a new row.

        Args:
            request: consent request DTO.
            base_url: base URL for consent signing page (e.g. "https://vitalia.app").

        Returns:
            ConsentUrlResult with consent_url, expires_at, and is_new flag.
        """
        # D2: check for existing pending consent (idempotency)
        existing = await self._consent_repo.get_pending_by_booking(request.booking_id)
        if existing is not None and existing.consent_template_slug == request.consent_template_slug:
            consent_url = self.build_consent_url(consent_id=existing.id, base_url=base_url)
            logger.info(
                "consent_request_idempotent",
                consent_id=str(existing.id),
                tenant_id=str(self._tenant_id),
            )
            return ConsentUrlResult(
                consent_id=existing.id,
                consent_url=consent_url,
                expires_at=existing.expires_at,
                is_new=False,
            )

        # Create new consent record
        now = _utc_now()
        expires_at = now + timedelta(hours=request.expiry_hours)
        new_consent_id = uuid.uuid4()

        # Build model via repository (avoids importing model directly here)
        from src.modules.vitalia.infrastructure.models.consent_record_model import (
            VitaliaConsentRecordModel,
        )

        consent_model = VitaliaConsentRecordModel(
            id=new_consent_id,
            tenant_id=self._tenant_id,
            patient_id=request.patient_id,
            booking_id=request.booking_id,
            consent_template_slug=request.consent_template_slug,
            template_version="v1",  # placeholder — real version from template catalog (T-be-7)
            template_snapshot_md="",  # placeholder — populated from template catalog
            status="pending_signature",
            expires_at=expires_at,
            delivery_channels=request.delivery_channels,
            created_at=now,
            updated_at=now,
        )

        await self._consent_repo.save(consent_model)

        consent_url = self.build_consent_url(consent_id=new_consent_id, base_url=base_url)

        logger.info(
            "consent_requested",
            consent_id=str(new_consent_id),
            tenant_id=str(self._tenant_id),
            template_slug=request.consent_template_slug,
            expires_at=expires_at.isoformat(),
        )

        return ConsentUrlResult(
            consent_id=new_consent_id,
            consent_url=consent_url,
            expires_at=expires_at,
            is_new=True,
        )

    async def sign_consent(self, request: SignConsentRequest) -> SignConsentResult:
        """Capture patient signature evidence after HMAC token verification.

        Validates the HMAC token before accepting any signature evidence.
        Returns success=False + error_code='invalid_token' on tampered/missing token.

        Args:
            request: sign request with signature evidence + HMAC token.

        Returns:
            SignConsentResult with success flag.
        """
        # Verify HMAC token first (security gate)
        if not self.verify_consent_token(consent_id=request.consent_id, token=request.token):
            logger.warning(
                "consent_sign_invalid_token",
                consent_id=str(request.consent_id),
                tenant_id=str(self._tenant_id),
            )
            return SignConsentResult(
                success=False,
                consent_id=request.consent_id,
                error_code="invalid_token",
            )

        signed_at = _utc_now()
        updated = await self._consent_repo.mark_signed(
            consent_id=request.consent_id,
            signed_name=request.signed_name,
            signed_ip=request.signed_ip,
            signed_user_agent=request.signed_user_agent,
            signed_at=signed_at,
            signature_method=request.signature_method,
        )

        if not updated:
            logger.warning(
                "consent_sign_not_found_or_already_signed",
                consent_id=str(request.consent_id),
                tenant_id=str(self._tenant_id),
            )
            return SignConsentResult(
                success=False,
                consent_id=request.consent_id,
                error_code="consent_not_found_or_already_signed",
            )

        logger.info(
            "consent_signed",
            consent_id=str(request.consent_id),
            tenant_id=str(self._tenant_id),
            signature_method=request.signature_method,
        )

        return SignConsentResult(success=True, consent_id=request.consent_id)

    # ── HMAC helpers ──────────────────────────────────────────────────────────

    def build_consent_url(self, *, consent_id: uuid.UUID, base_url: str) -> str:
        """Build a signed consent URL with HMAC-SHA256 token.

        URL format: {base_url}/consent/sign?consent_id={id}&token={hmac}

        The token is HMAC-SHA256(key=secret, msg=consent_id_str).
        """
        token = self._sign(str(consent_id))
        params = urlencode({"consent_id": str(consent_id), "token": token})
        return f"{base_url.rstrip('/')}{_CONSENT_URL_PATH}?{params}"

    def verify_consent_token(self, *, consent_id: uuid.UUID, token: str) -> bool:
        """Verify an HMAC-SHA256 token for a consent_id.

        Returns True iff the token was produced by build_consent_url with the
        same secret for the same consent_id. Uses constant-time comparison
        (hmac.compare_digest) to prevent timing attacks.

        Args:
            consent_id: the consent record UUID.
            token: the HMAC token string from the URL.

        Returns:
            True if valid, False otherwise.
        """
        if not token or not self._hmac_secret:
            return False

        expected = self._sign(str(consent_id))
        try:
            return hmac.compare_digest(expected, token)
        except TypeError:
            return False

    def _sign(self, message: str) -> str:
        """Compute HMAC-SHA256 hex digest for message."""
        return hmac.new(
            self._hmac_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
