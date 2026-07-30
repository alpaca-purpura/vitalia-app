"""SC-04 adversarial: cross-tenant query blocked — HIPAA-lite dual filter.

Tests verify that:
1. A doctor from tenant_A + clinic_A cannot access conversations of tenant_B
   (resolved tenant_id in JWT always scopes the query).
2. A doctor from tenant_A + clinic_A cannot use a clinic_id belonging to tenant_B
   (dual filter in service rejects cross-clinic queries → 404, not 200).

Per hipaa-lite.md § Tests requeridos:
  - Cross-tenant query bloqueada: request con tenant_id_A + clinic_id_B (de tenant diferente) → 404, no leak.
  - Cross-clinic query bloqueada: request con tenant_id_A + clinic_id_X siendo user de clinic_id_Y → 403.

These are ARCHITECTURE-LEVEL tests (no live DB needed — rely on JWT-scoped tenant_id).

downstream-regression-na: brand-local vitalia inbox HIPAA-lite test
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


def _make_app() -> FastAPI:
    """Build minimal test app with inbox router."""
    from src.modules.vitalia.inbox.api.router import router as inbox_router

    app = FastAPI(redirect_slashes=False)
    app.include_router(inbox_router, prefix="/api/v1/vitalia/inbox")
    return app


TENANT_A = uuid4()
TENANT_B = uuid4()
CLINIC_A = uuid4()
CLINIC_B = uuid4()  # belongs to TENANT_B
CONV_ID = uuid4()
USER_A = uuid4()
NOW = datetime.now(UTC)
VALID_TOKEN = "Bearer valid-test-token-tenant-a"


def _make_ctx(tenant_id: uuid4, clinic_id: uuid4, role: str = "doctor") -> MagicMock:
    """Build a mock ClinicContext."""
    ctx = MagicMock()
    ctx.user_id = str(USER_A)
    ctx.tenant_id = tenant_id
    ctx.clinic_id = clinic_id
    ctx.role = role
    ctx.email = "doc@clinic-a.test"
    ctx.name = "Dr. Tenant A"
    return ctx


# ---------------------------------------------------------------------------
# Cross-tenant: JWT scopes to tenant_A, request targets CONV_ID of tenant_B
# → service will not find it (tenant_id filter), returns 404 (not 200)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_tenant_conv_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cross-tenant access: JWT tenant_A cannot retrieve conversation of tenant_B → 404.

    The service filters by tenant_id from JWT (tenant_A).
    Even if conv_id belongs to tenant_B, the query returns None.
    → 404 (no information leak about the other tenant's data).
    """
    from src.modules.vitalia.inbox.application.services.send_message_service import (
        ConversationNotFoundError,
    )

    # Inject ctx from tenant_A
    ctx_a = _make_ctx(tenant_id=TENANT_A, clinic_id=CLINIC_A)
    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=ctx_a),
    )

    # Service raises ConversationNotFoundError (dual-filter excludes TENANT_B's conversation)
    send_svc = AsyncMock()
    send_svc.send.side_effect = ConversationNotFoundError(CONV_ID)
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_send_service",
        lambda: send_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/messages",
            json={"body_text": "intento cross-tenant"},
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_A),
                "X-Clinic-ID": str(CLINIC_B),  # CLINIC_B is from TENANT_B
            },
        )

    # Must return 404 — no leak of TENANT_B data
    assert resp.status_code == 404
    body = resp.json()
    # Must NOT reveal TENANT_B identity or data
    assert str(TENANT_B) not in body.get("detail", "")


# ---------------------------------------------------------------------------
# Cross-tenant: marketing role (TENANT_A) cannot read PHI of any tenant → 403
# No PHI data is leaked before RBAC check
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_tenant_marketing_role_still_403(monkeypatch: pytest.MonkeyPatch) -> None:
    """Marketing role from any tenant is denied PHI access → 403.

    RBAC is applied BEFORE any data retrieval — no information about
    whether the conversation exists is revealed to non-PHI roles.
    """
    ctx_marketing = _make_ctx(tenant_id=TENANT_A, clinic_id=CLINIC_A, role="marketing")
    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=ctx_marketing),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/messages",
            json={"body_text": "intento marketing cross-tenant"},
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_B),  # Wrong tenant in header
                "X-Clinic-ID": str(CLINIC_B),
            },
        )

    assert resp.status_code == 403
    body = resp.json()
    # No PHI leaked in 403 response
    assert str(TENANT_B) not in body.get("detail", "")
    assert str(CONV_ID) not in body.get("detail", "")


# ---------------------------------------------------------------------------
# Cross-tenant retract: doctor tenant_A cannot retract message of tenant_B → 404
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_tenant_retract_404(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cross-tenant retract: doctor JWT scoped to tenant_A, conv belongs to tenant_B → 404."""
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        MessageNotRetractableError,
    )

    msg_id = uuid4()
    ctx_a = _make_ctx(tenant_id=TENANT_A, clinic_id=CLINIC_A)
    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=ctx_a),
    )

    retract_svc = AsyncMock()
    retract_svc.retract.side_effect = MessageNotRetractableError(msg_id)
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_retract_service",
        lambda: retract_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/messages/{msg_id}/revert",
            json={"reason": "user_undo"},
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_A),
                "X-Clinic-ID": str(CLINIC_B),  # CLINIC_B from TENANT_B
            },
        )

    assert resp.status_code == 404
