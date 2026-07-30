# cap: clinics.lisa.doctores
"""Assets proxy upload router — T-BE-6.

Route:
  POST /upload  — multipart (file + kind); proxies to AssetsService.upload_asset → R2.

Architecture decisions (03-arch-be.md § 4 + D-3):
  - D-3: presigned upload does NOT exist in luana-core-assets.
    Consume AssetsService.upload_asset (proxy via boto3 put_object). Never edit engine.
  - Wiring copied from nicolify/backend/src/main.py assets_gallery pattern.
  - Content-type allow-list enforced brand-side BEFORE forwarding to engine.
  - 10MB max enforced brand-side BEFORE forwarding.
  - Key is tenant-scoped: path_prefix = {tenant_id}/{kind} → AssetsService appends uuid-filename.
  - Tests use LocalStorageStrategy (STORAGE_PROVIDER env not R2) — no live R2 needed.
    Live R2 = T-BE-7 Chris manual action.
  - RBAC: admin_clinic role required (hipaa-lite.md + 03-arch-be § 4).
  - response_model= MANDATORY (PII gate + arch test).
  - redirect_slashes=False enforced at app level in main.py.

Content-type allow-list (spec 01-spec.md § Business rules avatar-presigned-direct-r2 corrected D-3):
  - kind=avatar: image/* (any image MIME type)
  - kind=credential_doc: application/pdf, image/jpeg, image/png,
    application/vnd.openxmlformats-officedocument.wordprocessingml.document (DOCX)
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status

from src.modules.vitalia._shared.auth.rbac import require_brand_owner_access
from src.modules.vitalia.clinics.api.dtos import AssetUploadResponse
from src.modules.vitalia.clinics.domain.bio_file import BIO_DOC_ALLOWED_CONTENT_TYPES

logger = structlog.get_logger()

router = APIRouter()

# Allowed roles for upload mutations — admin_clinic only (hipaa-lite.md § RBAC)
# RBAC ratificado Chris 2026-06-07 (rescate): {owner, admin_clinic} — alineado a bio-files/staff
_ADMIN_CLINIC_ROLES: frozenset[str] = frozenset(["owner", "admin_clinic"])

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB — spec § Business rules

# Content-type allow-lists per kind
_AVATAR_ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset()
# image/* is a prefix check, not a literal set — see _validate_content_type()

_CREDENTIAL_DOC_ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
)

# Valid kinds (spec § Business rules + 03-arch-be § 4 + delta v3 D3-B bio_doc)
_VALID_KINDS: frozenset[str] = frozenset({"avatar", "credential_doc", "bio_doc"})


# ── Validation helpers ────────────────────────────────────────────────────────


def _validate_kind(kind: str) -> None:
    """Raise 422 if kind is not in the allow-list."""
    if kind not in _VALID_KINDS:
        raise HTTPException(
            status_code=422,
            detail=f"kind debe ser 'avatar', 'credential_doc' o 'bio_doc'. Recibido: '{kind}'",
        )


def _validate_content_type(kind: str, content_type: str | None) -> str:
    """Validate content-type against the allow-list for the given kind.

    Returns the validated content_type (normalized to lowercase).
    Raises 422 if not allowed.
    """
    ct = (content_type or "").lower().split(";")[0].strip()

    if kind == "avatar":
        # avatar: only image/* (any image MIME type)
        if not ct.startswith("image/"):
            raise HTTPException(
                status_code=422,
                detail=(f"Para kind='avatar' solo se aceptan archivos de imagen (image/*). Tipo recibido: '{ct}'"),
            )
    elif kind == "credential_doc":
        # credential_doc: PDF, JPG, PNG, DOCX
        if ct not in _CREDENTIAL_DOC_ALLOWED_CONTENT_TYPES:
            allowed = ", ".join(sorted(_CREDENTIAL_DOC_ALLOWED_CONTENT_TYPES))
            raise HTTPException(
                status_code=422,
                detail=(f"Para kind='credential_doc' se aceptan: {allowed}. Tipo recibido: '{ct}'"),
            )
    elif kind == "bio_doc":
        # bio_doc: same allow-list as credential_doc (PDF/JPG/PNG/DOCX, RN-D3B-2)
        if ct not in BIO_DOC_ALLOWED_CONTENT_TYPES:
            allowed = ", ".join(sorted(BIO_DOC_ALLOWED_CONTENT_TYPES))
            raise HTTPException(
                status_code=422,
                detail=(f"Para kind='bio_doc' se aceptan: {allowed}. Tipo recibido: '{ct}'"),
            )
    return ct


async def _read_and_validate_size(file: UploadFile) -> bytes:
    """Read the entire file and enforce the 10MB max size limit.

    Raises 422 if file exceeds MAX_FILE_SIZE_BYTES.
    Returns file bytes.
    """
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        size_mb = len(content) / (1024 * 1024)
        raise HTTPException(
            status_code=422,
            detail=(f"El archivo supera el limite de 10 MB. Tamano recibido: {size_mb:.1f} MB."),
        )
    return content


# ── Route ─────────────────────────────────────────────────────────────────────


@router.post(
    "/upload",
    response_model=AssetUploadResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_brand_owner_access(roles=_ADMIN_CLINIC_ROLES))],
)
async def upload_asset_proxy(
    file: UploadFile = File(..., description="Archivo a subir (avatar o documento de credencial)"),
    kind: str = Form(..., description="Tipo de asset: 'avatar' | 'credential_doc'"),
    tenant_id: str = Header(alias="X-Tenant-ID"),
    user_id: str = Header(alias="X-User-ID"),
) -> AssetUploadResponse:
    """Proxy asset upload to AssetsService.upload_asset → R2.

    Business rules (01-spec.md § Business rules corrected D-3):
    - kind=avatar: image/* only, 10MB max.
    - kind=credential_doc: PDF/JPG/PNG/DOCX, 10MB max.
    - key tenant-scoped: {tenant_id}/{kind}/{uuid}-{filename}.
    - Returns {key, url} — FE PATCHes doctor.avatar_key with key.

    D-3: presigned upload does NOT exist in luana-core-assets.
    Consume AssetsService.upload_asset (proxy) — never edit engine.
    Live R2 = T-BE-7 Chris manual action. Tests use LocalStorageStrategy.

    RBAC: admin_clinic required — wired as route dependency via Depends().
    response_model=AssetUploadResponse (PII gate — no PHI fields).
    """

    # ── Validate kind ─────────────────────────────────────────────────────────
    _validate_kind(kind)

    # ── Validate content-type ─────────────────────────────────────────────────
    _validate_content_type(kind, file.content_type)

    # ── Read file + enforce 10MB limit ────────────────────────────────────────
    file_bytes = await _read_and_validate_size(file)

    filename = file.filename or f"upload.{kind}"

    logger.info(
        "assets_proxy_upload_start",
        tenant_id=tenant_id,
        kind=kind,
        filename=filename,
        size_bytes=len(file_bytes),
    )

    # ── Proxy to AssetsService (engine consume — D-3) ─────────────────────────
    # AssetsService uses a synchronous Session (luana_core_platform.core.database.SessionLocal).
    # We use SessionLocal() directly to match the engine's sync pattern.
    # path_prefix = "{tenant_id}/{kind}" → AssetsService appends uuid-filename → tenant-scoped key.
    # Imports deferred to function body to avoid env var validation at module load time
    # (pattern from doctors_router._get_db — PLC0415 noqa accepted per codebase convention).
    import io as _io  # noqa: PLC0415
    from uuid import UUID  # noqa: PLC0415

    from luana_core_assets.application.assets_service import AssetsService  # noqa: PLC0415
    from luana_core_platform.core.database import SessionLocal  # noqa: PLC0415

    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"X-Tenant-ID debe ser un UUID valido. Recibido: '{tenant_id}'",
        ) from exc

    db = SessionLocal()
    try:
        service = AssetsService(db)
        asset = service.upload_asset(
            tenant_id=tenant_uuid,
            file_obj=_io.BytesIO(file_bytes),
            filename=filename,
            mime_type=file.content_type,
            scope="library",
            purpose="brand_asset",
        )
    except Exception as exc:
        logger.exception(
            "assets_proxy_upload_failed",
            tenant_id=tenant_id,
            kind=kind,
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al subir el archivo. Intenta de nuevo.",
        ) from exc
    finally:
        db.close()

    logger.info(
        "assets_proxy_upload_done",
        tenant_id=tenant_id,
        kind=kind,
        storage_path=asset.storage_path,
    )

    return AssetUploadResponse(
        key=asset.storage_path,
        url=asset.public_url,
    )
