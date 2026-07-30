# cap: clinics.lisa.doctores
"""Tests for assets proxy upload router — T-BE-6.

Tests validate:
  - router is importable and registers POST /upload
  - response_model= AssetUploadResponse declared (PII gate)
  - 10MB file size enforcement → 422 on violation
  - content-type allow-list for kind=avatar (image/*) → 422 on violation
  - content-type allow-list for kind=credential_doc (PDF/JPG/PNG/DOCX) → 422 on violation
  - returns {key, url} on valid upload (LocalStorageStrategy — no live R2)
  - RBAC header enforced (X-User-Role: admin_clinic)

Architecture constraints (03-arch-be.md § 4 + D-3):
  - D-3: presigned upload does NOT exist in luana-core-assets.
    Consume AssetsService.upload_asset proxy — never edit engine.
  - Tests use LocalStorageStrategy swap: STORAGE_PROVIDER not set → LocalStorageStrategy.
    Live R2 = T-BE-7 Chris manual action.
  - key tenant-scoped: {tenant_id}/{kind}/{uuid}-{filename}
    (AssetsService uses path_prefix passed by router)

Mock strategy (avoiding live DB/R2):
  The route handler defers all engine imports (AssetsService, SessionLocal) inside the
  function body (per doctors_router pattern, PLC0415 accepted). Functional tests use
  monkeypatch to set minimal env vars required by luana_core_platform.core.config.Settings
  so that AssetsService can be imported, then mock AssetsService itself to avoid real DB.
"""

from __future__ import annotations

import io
import uuid
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

# ── Minimal env vars required by luana_core_platform.core.config.Settings ────
# These values are fake/test-safe — no real DB or service is contacted.
_FAKE_ENV: dict[str, str] = {
    "LOG_LEVEL": "WARNING",
    "DOMAIN_NAME": "test.local",
    "TRAEFIK_NETWORK": "test-net",
    "API_SECRET_KEY": "test-secret-key-32chars-minimum-len",
    "WHATSAPP_API_TOKEN": "fake-token",
    "WHATSAPP_PHONE_NUMBER_ID": "0000000000",
    "WHATSAPP_VERIFY_TOKEN": "fake-verify-token",
    "OPENAI_API_KEY": "sk-test-key",
    "REDIS_URL": "redis://localhost:6379",
    "QDRANT_URL": "http://localhost:6333",
    "POSTGRES_USER": "test_user",
    "POSTGRES_PASSWORD": "test_pass",
    "POSTGRES_DB": "test_db",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "API_URL": "http://localhost:8000",
    "STORAGE_PROVIDER": "local",
    "UPLOAD_DIR": "/tmp/test-uploads",
}


@pytest.fixture(autouse=False)
def _with_fake_env(monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: PT004
    """Set minimal env vars so luana_core_platform.core.config.Settings instantiates.

    Used by functional tests that trigger engine imports (AssetsService).
    Structural tests (import-only) don't need this.
    """
    for key, value in _FAKE_ENV.items():
        monkeypatch.setenv(key, value)


# ── Structural tests (no DB/R2 needed) ────────────────────────────────────────


def test_assets_proxy_router_importable() -> None:
    """assets_proxy_router must be importable (connectivity gate)."""
    from src.modules.vitalia.clinics.api.assets_proxy_router import router

    assert router is not None


def test_assets_proxy_router_has_post_upload() -> None:
    """Router must register POST /upload (delivery gate)."""
    from src.modules.vitalia.clinics.api.assets_proxy_router import router

    upload_routes = [r for r in router.routes if r.path == "/upload" and "POST" in getattr(r, "methods", set())]
    assert upload_routes, "POST /upload route not found on assets_proxy_router"


def test_assets_proxy_router_post_has_response_model() -> None:
    """POST /upload must declare response_model= (arch gate — PII allowlist)."""
    from src.modules.vitalia.clinics.api.assets_proxy_router import router

    upload_routes = [r for r in router.routes if r.path == "/upload" and "POST" in getattr(r, "methods", set())]
    assert upload_routes, "POST /upload not found"
    route = upload_routes[0]
    assert hasattr(route, "response_model"), "POST /upload must declare response_model="
    assert route.response_model is not None, "response_model= must not be None"


def test_asset_upload_response_dto_has_key_and_url() -> None:
    """AssetUploadResponse must have key: str and url: str fields."""
    from src.modules.vitalia.clinics.api.dtos import AssetUploadResponse

    fields = set(AssetUploadResponse.model_fields.keys())
    assert "key" in fields, "AssetUploadResponse must have 'key' field"
    assert "url" in fields, "AssetUploadResponse must have 'url' field"


# ── Functional tests using mocked AssetsService ───────────────────────────────


@pytest.fixture()
def assets_app(_with_fake_env: None) -> FastAPI:  # noqa: PT004
    """Create minimal FastAPI app with assets_proxy_router mounted.

    Requires _with_fake_env to ensure env vars are set before import of engine modules.
    """
    from src.modules.vitalia.clinics.api.assets_proxy_router import router

    app = FastAPI(redirect_slashes=False)
    app.include_router(router, prefix="/api/v1/vitalia/assets")
    return app


@pytest.fixture()
def mock_assets_service(
    _with_fake_env: None,
) -> Generator[MagicMock, None, None]:
    """Mock AssetsService.upload_asset to avoid live R2 and DB.

    Strategy (LocalStorageStrategy swap — D-3):
    - STORAGE_PROVIDER=local (set by _with_fake_env) → LocalStorageStrategy selected.
    - Patch AssetsService directly to return a fake asset (avoids real DB calls).
    - SessionLocal() is also mocked to avoid real Postgres connection.

    Tests do NOT need live R2 creds (T-BE-7 = Chris manual action).
    """
    tenant_id = uuid.uuid4()
    mock_asset = MagicMock()
    mock_asset.storage_path = f"{tenant_id}/avatar/{uuid.uuid4()!s}-test-file.jpg"
    mock_asset.public_url = f"/static/uploads/{tenant_id}/avatar/test-file.jpg"

    mock_instance = MagicMock()
    mock_instance.upload_asset.return_value = mock_asset

    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    with (
        patch(
            "luana_core_assets.application.assets_service.AssetsService",
            return_value=mock_instance,
        ),
        patch(
            "luana_core_platform.core.database.SessionLocal",
            return_value=mock_db,
        ),
    ):
        yield mock_instance


@pytest.mark.asyncio()
async def test_upload_valid_avatar_returns_key_and_url(
    assets_app: FastAPI,
    mock_assets_service: MagicMock,
) -> None:
    """POST /upload with valid image/* (avatar) returns {key, url}. V-FN-10."""
    import httpx

    tenant_id = str(uuid.uuid4())
    file_content = b"fake-image-bytes"

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=assets_app),
        base_url="http://test",
        headers={
            "X-Tenant-ID": tenant_id,
            "X-User-ID": str(uuid.uuid4()),
            "X-User-Role": "admin_clinic",
        },
    ) as ac:
        response = await ac.post(
            "/api/v1/vitalia/assets/upload",
            files={"file": ("avatar.jpg", io.BytesIO(file_content), "image/jpeg")},
            data={"kind": "avatar"},
        )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()
    assert "key" in body, "Response must contain 'key'"
    assert "url" in body, "Response must contain 'url'"
    assert body["key"] != "", "key must not be empty"
    assert body["url"] != "", "url must not be empty"


@pytest.mark.asyncio()
async def test_upload_10mb_limit_enforced(assets_app: FastAPI) -> None:
    """POST /upload with file > 10MB → 422 (enforced brand-side before forwarding). V-FN-10."""
    import httpx

    tenant_id = str(uuid.uuid4())
    # 10MB + 1 byte = over limit
    large_content = b"x" * (10 * 1024 * 1024 + 1)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=assets_app),
        base_url="http://test",
        headers={
            "X-Tenant-ID": tenant_id,
            "X-User-ID": str(uuid.uuid4()),
            "X-User-Role": "admin_clinic",
        },
    ) as ac:
        response = await ac.post(
            "/api/v1/vitalia/assets/upload",
            files={"file": ("big.jpg", io.BytesIO(large_content), "image/jpeg")},
            data={"kind": "avatar"},
        )

    assert response.status_code == 422, f"Expected 422 for >10MB file, got {response.status_code}: {response.text}"
    body = response.json()
    assert "10" in str(body).lower() or "size" in str(body).lower() or "mb" in str(body).lower(), (
        "Error message must mention size/10MB limit"
    )


@pytest.mark.asyncio()
async def test_upload_avatar_wrong_content_type_rejected(assets_app: FastAPI) -> None:
    """POST /upload kind=avatar with non-image content-type → 422. V-FN-10."""
    import httpx

    tenant_id = str(uuid.uuid4())
    file_content = b"%PDF-1.4 fake-pdf"

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=assets_app),
        base_url="http://test",
        headers={
            "X-Tenant-ID": tenant_id,
            "X-User-ID": str(uuid.uuid4()),
            "X-User-Role": "admin_clinic",
        },
    ) as ac:
        response = await ac.post(
            "/api/v1/vitalia/assets/upload",
            files={"file": ("doc.pdf", io.BytesIO(file_content), "application/pdf")},
            data={"kind": "avatar"},
        )

    assert response.status_code == 422, (
        f"Expected 422 for PDF avatar upload, got {response.status_code}: {response.text}"
    )


@pytest.mark.asyncio()
async def test_upload_credential_doc_valid_pdf_accepted(
    assets_app: FastAPI,
    mock_assets_service: MagicMock,
) -> None:
    """POST /upload kind=credential_doc with application/pdf → 200. V-FN-10."""
    import httpx

    tenant_id = str(uuid.uuid4())
    file_content = b"%PDF-1.4 fake-pdf-content"

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=assets_app),
        base_url="http://test",
        headers={
            "X-Tenant-ID": tenant_id,
            "X-User-ID": str(uuid.uuid4()),
            "X-User-Role": "admin_clinic",
        },
    ) as ac:
        response = await ac.post(
            "/api/v1/vitalia/assets/upload",
            files={"file": ("credencial.pdf", io.BytesIO(file_content), "application/pdf")},
            data={"kind": "credential_doc"},
        )

    assert response.status_code == 200, (
        f"Expected 200 for PDF credential_doc, got {response.status_code}: {response.text}"
    )
    body = response.json()
    assert "key" in body
    assert "url" in body


@pytest.mark.asyncio()
async def test_upload_credential_doc_invalid_type_rejected(assets_app: FastAPI) -> None:
    """POST /upload kind=credential_doc with text/plain → 422. V-FN-10."""
    import httpx

    tenant_id = str(uuid.uuid4())
    file_content = b"plain text document"

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=assets_app),
        base_url="http://test",
        headers={
            "X-Tenant-ID": tenant_id,
            "X-User-ID": str(uuid.uuid4()),
            "X-User-Role": "admin_clinic",
        },
    ) as ac:
        response = await ac.post(
            "/api/v1/vitalia/assets/upload",
            files={"file": ("notes.txt", io.BytesIO(file_content), "text/plain")},
            data={"kind": "credential_doc"},
        )

    assert response.status_code == 422, (
        f"Expected 422 for text/plain credential_doc, got {response.status_code}: {response.text}"
    )


@pytest.mark.asyncio()
async def test_upload_invalid_kind_rejected(assets_app: FastAPI) -> None:
    """POST /upload with kind not in {avatar, credential_doc} → 422."""
    import httpx

    tenant_id = str(uuid.uuid4())
    file_content = b"fake-image-bytes"

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=assets_app),
        base_url="http://test",
        headers={
            "X-Tenant-ID": tenant_id,
            "X-User-ID": str(uuid.uuid4()),
            "X-User-Role": "admin_clinic",
        },
    ) as ac:
        response = await ac.post(
            "/api/v1/vitalia/assets/upload",
            files={"file": ("x.jpg", io.BytesIO(file_content), "image/jpeg")},
            data={"kind": "invalid_kind"},
        )

    assert response.status_code == 422, f"Expected 422 for invalid kind, got {response.status_code}: {response.text}"


# ── RBAC negative tests (audit fix: BLOCKING — T-BE audit iteration 2) ──────


@pytest.mark.asyncio()
async def test_upload_non_admin_role_denied_403(assets_app: FastAPI) -> None:
    """POST /upload with X-User-Role: marketing → 403 RBAC denied.

    RED test for RBAC fix: the imperative require_brand_owner_access(user_role) call
    was a no-op — ANY role could upload. This test asserts the corrected Depends()
    wiring enforces role restriction.

    hipaa-lite.md § Access control: roles other than admin_clinic MUST be denied.
    """
    import httpx

    tenant_id = str(uuid.uuid4())
    file_content = b"fake-image-bytes"

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=assets_app),
        base_url="http://test",
        headers={
            "X-Tenant-ID": tenant_id,
            "X-User-ID": str(uuid.uuid4()),
            "X-User-Role": "marketing",  # non-admin role — must be denied
        },
    ) as ac:
        response = await ac.post(
            "/api/v1/vitalia/assets/upload",
            files={"file": ("avatar.jpg", io.BytesIO(file_content), "image/jpeg")},
            data={"kind": "avatar"},
        )

    assert response.status_code == 403, (
        f"Expected 403 for X-User-Role: marketing, got {response.status_code}: {response.text}. "
        "RBAC must deny non-admin roles on assets upload endpoint."
    )


@pytest.mark.asyncio()
async def test_upload_sales_role_denied_403(assets_app: FastAPI) -> None:
    """POST /upload with X-User-Role: sales → 403 RBAC denied."""
    import httpx

    tenant_id = str(uuid.uuid4())
    file_content = b"fake-image-bytes"

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=assets_app),
        base_url="http://test",
        headers={
            "X-Tenant-ID": tenant_id,
            "X-User-ID": str(uuid.uuid4()),
            "X-User-Role": "sales",
        },
    ) as ac:
        response = await ac.post(
            "/api/v1/vitalia/assets/upload",
            files={"file": ("avatar.jpg", io.BytesIO(file_content), "image/jpeg")},
            data={"kind": "avatar"},
        )

    assert response.status_code == 403, (
        f"Expected 403 for X-User-Role: sales, got {response.status_code}: {response.text}."
    )


@pytest.mark.asyncio()
async def test_upload_empty_role_denied_403(assets_app: FastAPI) -> None:
    """POST /upload with empty X-User-Role header → 403 RBAC denied."""
    import httpx

    tenant_id = str(uuid.uuid4())
    file_content = b"fake-image-bytes"

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=assets_app),
        base_url="http://test",
        headers={
            "X-Tenant-ID": tenant_id,
            "X-User-ID": str(uuid.uuid4()),
            "X-User-Role": "",
        },
    ) as ac:
        response = await ac.post(
            "/api/v1/vitalia/assets/upload",
            files={"file": ("avatar.jpg", io.BytesIO(file_content), "image/jpeg")},
            data={"kind": "avatar"},
        )

    assert response.status_code == 403, (
        f"Expected 403 for empty X-User-Role, got {response.status_code}: {response.text}."
    )


@pytest.mark.asyncio()
async def test_upload_admin_clinic_role_allowed(
    assets_app: FastAPI,
    mock_assets_service: MagicMock,
) -> None:
    """POST /upload with X-User-Role: admin_clinic → 200 (keeps existing admin tests green).

    Regression guard: fixing RBAC must NOT break the happy path.
    """
    import httpx

    tenant_id = str(uuid.uuid4())
    file_content = b"fake-image-bytes"

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=assets_app),
        base_url="http://test",
        headers={
            "X-Tenant-ID": tenant_id,
            "X-User-ID": str(uuid.uuid4()),
            "X-User-Role": "admin_clinic",
        },
    ) as ac:
        response = await ac.post(
            "/api/v1/vitalia/assets/upload",
            files={"file": ("avatar.jpg", io.BytesIO(file_content), "image/jpeg")},
            data={"kind": "avatar"},
        )

    assert response.status_code == 200, (
        f"Expected 200 for admin_clinic role, got {response.status_code}: {response.text}."
    )
