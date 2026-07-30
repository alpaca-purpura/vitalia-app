# cap: clinics.lisa.doctores
"""Tests: Doctor bio-files API (T-BE-bio-docs, delta v3 D3-B).

TDD RED-first — battery written BEFORE the implementation (tdd-mandatory.md).

Validators: V-D3B-1 (register + detail folds bioFiles[]), V-D3B-2 (delete +
audit + RN-D3B-1 snapshot untouched), V-D3B-4 (download 200 + content-type).
Gherkin coverage: SC-D3B-1, SC-D3B-2, SC-D3B-4.

Covers:
  1. Routes exist + response_model= on POST/GET/DELETE bio-files (PII gate)
  2. Download route exists (stream proxy — Response exemption, D-1 impl-log)
  3. DTOs: BioFileDTO camelCase aliases, BioFileRegisterRequest forbid-extra,
     BioFilesResponse, BioFileDeleteResponse, DoctorDetailDTO.bio_files default
  4. Assets proxy: bio_doc kind + content-type allow-list (RN-D3B-2 reject)
  5. Domain DoctorBioFile validation (size/content_type bounds)
  6. BioFileService unit (AsyncMock repos): register/list/delete/download +
     dual-filter cross-tenant 404 + audit sync actions + RN-D3B-1
  7. Repo REAL vs Postgres (integration, auto-skip): cross-tenant get -> None,
     soft delete excluded from list (learning 2026-06-11 mocked-service-tests)
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

# ──────────────────────────────────────────────────────────────────────────────
# 1. Routes + response_model= (PII allowlist gate)
# ──────────────────────────────────────────────────────────────────────────────


def _bio_file_routes(method: str, *, with_file_id: bool = False, download: bool = False) -> list:
    from src.modules.vitalia.clinics.api.doctors_router import router

    matches = []
    for r in router.routes:
        path = getattr(r, "path", "")
        if "bio-files" not in path:
            continue
        if download != path.endswith("/download"):
            continue
        if not download and with_file_id != ("{file_id}" in path):
            continue
        if method in getattr(r, "methods", set()):
            matches.append(r)
    return matches


def test_bio_files_post_has_response_model() -> None:
    """POST /{doctor_id}/bio-files must exist and declare response_model=."""
    routes = _bio_file_routes("POST")
    assert routes, "POST /{doctor_id}/bio-files route not found"
    assert getattr(routes[0], "response_model", None) is not None, "POST bio-files must declare response_model="


def test_bio_files_get_list_has_response_model() -> None:
    """GET /{doctor_id}/bio-files must exist and declare response_model=."""
    routes = _bio_file_routes("GET")
    assert routes, "GET /{doctor_id}/bio-files route not found"
    assert getattr(routes[0], "response_model", None) is not None, "GET bio-files must declare response_model="


def test_bio_files_delete_has_response_model() -> None:
    """DELETE /{doctor_id}/bio-files/{file_id} must exist and declare response_model=."""
    routes = _bio_file_routes("DELETE", with_file_id=True)
    assert routes, "DELETE /{doctor_id}/bio-files/{file_id} route not found"
    assert getattr(routes[0], "response_model", None) is not None, "DELETE bio-files must declare response_model="


def test_bio_files_download_route_exists() -> None:
    """GET /{doctor_id}/bio-files/{file_id}/download must exist (stream proxy, D-1).

    Streams bytes (200 + stored content-type) — works with BOTH storage
    backends (local + R2) via engine StorageStrategy.get_file_bytes.
    response_model exemption: endpoint annotated -> Response.
    """
    routes = _bio_file_routes("GET", download=True)
    assert routes, "GET /{doctor_id}/bio-files/{file_id}/download route not found"


def test_bio_files_mutations_have_rbac_dependency() -> None:
    """POST/DELETE/download bio-files routes carry the staff RBAC dependency (03-arch-delta § 3.1)."""
    for method, kwargs in (
        ("POST", {}),
        ("DELETE", {"with_file_id": True}),
        ("GET", {"download": True}),
    ):
        routes = _bio_file_routes(method, **kwargs)
        assert routes, f"{method} bio-files route not found"
        dependant = getattr(routes[0], "dependant", None)
        dep_names = [d.call.__name__ for d in getattr(dependant, "dependencies", []) if d.call is not None]
        assert any("role" in n or "_dep" in n or "access" in n for n in dep_names), (
            f"{method} bio-files route must declare require_brand_owner_access dependency, got {dep_names}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# 2. DTOs — dtos.py
# ──────────────────────────────────────────────────────────────────────────────


def test_bio_file_dto_camel_aliases() -> None:
    """BioFileDTO must expose sizeBytes/contentType/uploadedAt camelCase (03-arch-delta § 3.1)."""
    from src.modules.vitalia.clinics.api.dtos import BioFileDTO

    dto = BioFileDTO(
        id=uuid4(),
        filename="cv.pdf",
        size_bytes=1024,
        content_type="application/pdf",
        uploaded_at=datetime.now(tz=timezone.utc),
    )
    dumped = dto.model_dump(by_alias=True)
    assert "sizeBytes" in dumped
    assert "contentType" in dumped
    assert "uploadedAt" in dumped
    assert "filename" in dumped


def test_bio_file_register_request_fields_and_forbid_extra() -> None:
    """BioFileRegisterRequest {storage_key, filename, size_bytes, content_type} rejects unknown keys."""
    from pydantic import ValidationError

    from src.modules.vitalia.clinics.api.dtos import BioFileRegisterRequest

    req = BioFileRegisterRequest(
        storage_key="tenant/bio_doc/abc.pdf",
        filename="cv.pdf",
        size_bytes=2048,
        content_type="application/pdf",
    )
    assert req.storage_key
    # camelCase in (FE wire contract)
    req_camel = BioFileRegisterRequest.model_validate(
        {
            "storageKey": "tenant/bio_doc/abc.pdf",
            "filename": "cv.pdf",
            "sizeBytes": 2048,
            "contentType": "application/pdf",
        }
    )
    assert req_camel.size_bytes == 2048
    with pytest.raises(ValidationError):
        BioFileRegisterRequest.model_validate(
            {
                "storage_key": "k",
                "filename": "f.pdf",
                "size_bytes": 1,
                "content_type": "application/pdf",
                "unexpected": True,
            }
        )


def test_bio_files_response_and_delete_response_exist() -> None:
    """BioFilesResponse {bio_files} + BioFileDeleteResponse {deleted} must exist."""
    from src.modules.vitalia.clinics.api.dtos import BioFileDeleteResponse, BioFilesResponse

    assert "bio_files" in BioFilesResponse.model_fields
    assert "deleted" in BioFileDeleteResponse.model_fields


def test_doctor_detail_dto_has_bio_files_default_empty() -> None:
    """DoctorDetailDTO EXTEND: bio_files list, default [] (POST create returns empty)."""
    from src.modules.vitalia.clinics.api.dtos import DoctorDetailDTO

    field = DoctorDetailDTO.model_fields.get("bio_files")
    assert field is not None, "DoctorDetailDTO must declare bio_files"
    assert field.default_factory is not None or field.default == [], "bio_files must default to empty list"


# ──────────────────────────────────────────────────────────────────────────────
# 3. Assets proxy — bio_doc kind (RN-D3B-2 backend_unit)
# ──────────────────────────────────────────────────────────────────────────────


def test_assets_proxy_valid_kinds_includes_bio_doc() -> None:
    """_VALID_KINDS must include bio_doc (shares PDF/JPG/PNG/DOCX allow-list, 10MB)."""
    from src.modules.vitalia.clinics.api.assets_proxy_router import _VALID_KINDS

    assert "bio_doc" in _VALID_KINDS


def test_assets_proxy_validate_kind_bio_doc_passes() -> None:
    """_validate_kind('bio_doc') must not raise."""
    from src.modules.vitalia.clinics.api.assets_proxy_router import _validate_kind

    _validate_kind("bio_doc")  # must not raise


def test_assets_proxy_validate_kind_unknown_still_422() -> None:
    """Unknown kind still raises 422 (error message mentions bio_doc now)."""
    from fastapi import HTTPException

    from src.modules.vitalia.clinics.api.assets_proxy_router import _validate_kind

    with pytest.raises(HTTPException) as exc_info:
        _validate_kind("malware")
    assert exc_info.value.status_code == 422
    assert "bio_doc" in str(exc_info.value.detail)


@pytest.mark.parametrize(
    "content_type",
    [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ],
)
def test_assets_proxy_bio_doc_allows_pdf_jpg_png_docx(content_type: str) -> None:
    """kind=bio_doc accepts PDF/JPG/PNG/DOCX (same allow-list as credential_doc)."""
    from src.modules.vitalia.clinics.api.assets_proxy_router import _validate_content_type

    assert _validate_content_type("bio_doc", content_type) == content_type


def test_assets_proxy_bio_doc_rejects_exe() -> None:
    """RN-D3B-2: .exe content-type for bio_doc -> 422, nothing uploaded."""
    from fastapi import HTTPException

    from src.modules.vitalia.clinics.api.assets_proxy_router import _validate_content_type

    with pytest.raises(HTTPException) as exc_info:
        _validate_content_type("bio_doc", "application/x-msdownload")
    assert exc_info.value.status_code == 422


# ──────────────────────────────────────────────────────────────────────────────
# 4. Domain — DoctorBioFile validation
# ──────────────────────────────────────────────────────────────────────────────


def _make_bio_file(**overrides: object) -> object:
    from src.modules.vitalia.clinics.domain.bio_file import DoctorBioFile

    kwargs: dict = {
        "tenant_id": uuid4(),
        "clinic_id": uuid4(),
        "doctor_id": uuid4(),
        "storage_key": "t/bio_doc/u.pdf",
        "filename": "cv.pdf",
        "size_bytes": 2048,
        "content_type": "application/pdf",
    }
    kwargs.update(overrides)
    return DoctorBioFile(**kwargs)


def test_domain_bio_file_valid() -> None:
    """A valid DoctorBioFile constructs with defaults (id, uploaded_at, deleted_at=None)."""
    f = _make_bio_file()
    assert f.deleted_at is None
    assert f.uploaded_at is not None


def test_domain_bio_file_rejects_zero_size() -> None:
    """size_bytes must be >= 1."""
    with pytest.raises(ValueError, match="size_bytes"):
        _make_bio_file(size_bytes=0)


def test_domain_bio_file_rejects_oversize() -> None:
    """size_bytes must be <= 10MB (MAX_BIO_FILE_SIZE_BYTES)."""
    with pytest.raises(ValueError, match="size_bytes"):
        _make_bio_file(size_bytes=11 * 1024 * 1024)


def test_domain_bio_file_rejects_disallowed_content_type() -> None:
    """content_type outside PDF/JPG/PNG/DOCX -> ValueError (RN-D3B-2 defense in depth)."""
    with pytest.raises(ValueError, match="content_type"):
        _make_bio_file(content_type="application/x-msdownload")


def test_domain_bio_file_rejects_empty_filename() -> None:
    """filename must be non-empty."""
    with pytest.raises(ValueError, match="filename"):
        _make_bio_file(filename="")


# ──────────────────────────────────────────────────────────────────────────────
# 5. BioFileService — unit tests (AsyncMock repos, suite precedent)
# ──────────────────────────────────────────────────────────────────────────────


def _make_doctor_stub() -> object:
    """Minimal object standing in for a Doctor entity (service only checks not-None)."""

    class _Doctor:
        id = uuid4()

    return _Doctor()


def _build_service(
    *,
    doctor: object | None,
    bio_file_repo: AsyncMock | None = None,
) -> tuple[object, AsyncMock, AsyncMock, AsyncMock]:
    from src.modules.vitalia.clinics.application.bio_file_service import BioFileService

    repo = bio_file_repo or AsyncMock()
    doctor_repo = AsyncMock()
    doctor_repo.get_by_id.return_value = doctor
    audit = AsyncMock()
    svc = BioFileService(bio_file_repo=repo, doctor_repo=doctor_repo, audit_repo=audit)
    return svc, repo, doctor_repo, audit


def _audit_actions(audit: AsyncMock) -> list[str]:
    return [call.args[0].action for call in audit.write.await_args_list]


@pytest.mark.asyncio
async def test_service_register_file_persists_and_audits() -> None:
    """register_file -> repo.add awaited + audit doctor.bio_file_added SYNC (SC-D3B-1)."""
    tid, cid, did, uid = uuid4(), uuid4(), uuid4(), uuid4()
    svc, repo, _doctor_repo, audit = _build_service(doctor=_make_doctor_stub())
    repo.add.side_effect = lambda f, **_: f

    result = await svc.register_file(
        tenant_id=tid,
        clinic_id=cid,
        doctor_id=did,
        user_id=uid,
        storage_key="t/bio_doc/u.pdf",
        filename="cv.pdf",
        size_bytes=2048,
        content_type="application/pdf",
    )

    assert result is not None
    assert result.doctor_id == did
    repo.add.assert_awaited_once()
    assert "doctor.bio_file_added" in _audit_actions(audit)


@pytest.mark.asyncio
async def test_service_register_file_cross_tenant_returns_none_and_audits() -> None:
    """Doctor not found under tenant/clinic (dual filter) -> None (router 404) + cross_tenant_attempt."""
    svc, repo, _doctor_repo, audit = _build_service(doctor=None)

    result = await svc.register_file(
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        user_id=uuid4(),
        storage_key="k",
        filename="cv.pdf",
        size_bytes=1,
        content_type="application/pdf",
    )

    assert result is None
    repo.add.assert_not_awaited()
    assert "cross_tenant_attempt" in _audit_actions(audit)


@pytest.mark.asyncio
async def test_service_register_file_invalid_content_type_raises() -> None:
    """Invalid metadata (content_type) -> ValueError (router maps 422)."""
    svc, repo, _doctor_repo, _audit = _build_service(doctor=_make_doctor_stub())

    with pytest.raises(ValueError, match="content_type"):
        await svc.register_file(
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            doctor_id=uuid4(),
            user_id=uuid4(),
            storage_key="k",
            filename="virus.exe",
            size_bytes=1,
            content_type="application/x-msdownload",
        )
    repo.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_service_list_files_delegates_dual_filter() -> None:
    """list_files delegates to repo with tenant_id + clinic_id + doctor_id."""
    tid, cid, did = uuid4(), uuid4(), uuid4()
    svc, repo, _doctor_repo, _audit = _build_service(doctor=_make_doctor_stub())
    repo.list_for_doctor.return_value = []

    result = await svc.list_files(tenant_id=tid, clinic_id=cid, doctor_id=did)

    assert result == []
    repo.list_for_doctor.assert_awaited_once_with(tenant_id=tid, clinic_id=cid, doctor_id=did)


@pytest.mark.asyncio
async def test_service_delete_file_soft_deletes_and_audits_snapshot_untouched() -> None:
    """delete_file -> soft delete + audit doctor.bio_file_deleted (SC-D3B-2).

    RN-D3B-1: bio_public/public_profile snapshot untouched — the service must
    NOT issue any doctor mutation (doctor_repo write surface untouched).
    """
    tid, cid, did, uid, fid = uuid4(), uuid4(), uuid4(), uuid4(), uuid4()
    existing = _make_bio_file()
    existing.doctor_id = did  # type: ignore[attr-defined]

    repo = AsyncMock()
    repo.get_by_id.return_value = existing
    repo.soft_delete.return_value = True
    svc, repo, doctor_repo, audit = _build_service(doctor=_make_doctor_stub(), bio_file_repo=repo)

    deleted = await svc.delete_file(tenant_id=tid, clinic_id=cid, doctor_id=did, file_id=fid, user_id=uid)

    assert deleted is True
    repo.soft_delete.assert_awaited_once()
    assert "doctor.bio_file_deleted" in _audit_actions(audit)
    # RN-D3B-1 — zero doctor mutations (snapshot intact): no update/save/patch calls
    mutation_calls = [
        name
        for name, *_ in doctor_repo.mock_calls
        if any(verb in str(name) for verb in ("update", "save", "patch", "set_"))
    ]
    assert mutation_calls == [], f"delete_file must NOT mutate doctor (RN-D3B-1), got {mutation_calls}"


@pytest.mark.asyncio
async def test_service_delete_file_not_found_returns_false_and_audits() -> None:
    """delete_file on missing/cross-tenant file -> False (router 404) + cross_tenant_attempt."""
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    svc, repo, _doctor_repo, audit = _build_service(doctor=_make_doctor_stub(), bio_file_repo=repo)

    deleted = await svc.delete_file(
        tenant_id=uuid4(), clinic_id=uuid4(), doctor_id=uuid4(), file_id=uuid4(), user_id=uuid4()
    )

    assert deleted is False
    repo.soft_delete.assert_not_awaited()
    assert "cross_tenant_attempt" in _audit_actions(audit)


@pytest.mark.asyncio
async def test_service_delete_file_doctor_mismatch_returns_false() -> None:
    """File exists but belongs to another doctor -> False (404, no leak)."""
    existing = _make_bio_file()  # random doctor_id != requested
    repo = AsyncMock()
    repo.get_by_id.return_value = existing
    svc, repo, _doctor_repo, _audit = _build_service(doctor=_make_doctor_stub(), bio_file_repo=repo)

    deleted = await svc.delete_file(
        tenant_id=uuid4(), clinic_id=uuid4(), doctor_id=uuid4(), file_id=uuid4(), user_id=uuid4()
    )

    assert deleted is False
    repo.soft_delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_service_download_returns_bytes_with_content_type_and_audits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """download_file -> (file, bytes) + audit doctor.bio_file_downloaded (SC-D3B-4 / V-D3B-4)."""
    from src.modules.vitalia.clinics.application import bio_file_service as svc_module

    did = uuid4()
    existing = _make_bio_file(content_type="application/pdf")
    existing.doctor_id = did  # type: ignore[attr-defined]

    class _FakeStrategy:
        def get_file_bytes(self, storage_path: str) -> bytes:
            assert storage_path == existing.storage_key  # type: ignore[attr-defined]
            return b"%PDF-1.4 fake"

    monkeypatch.setattr(svc_module, "_resolve_storage_strategy", lambda: _FakeStrategy())

    repo = AsyncMock()
    repo.get_by_id.return_value = existing
    svc, repo, _doctor_repo, audit = _build_service(doctor=_make_doctor_stub(), bio_file_repo=repo)

    result = await svc.download_file(
        tenant_id=uuid4(), clinic_id=uuid4(), doctor_id=did, file_id=uuid4(), user_id=uuid4()
    )

    assert result is not None
    bio_file, content = result
    assert content == b"%PDF-1.4 fake"
    assert bio_file.content_type == "application/pdf"
    assert "doctor.bio_file_downloaded" in _audit_actions(audit)


@pytest.mark.asyncio
async def test_service_download_storage_failure_raises_storage_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Storage backend failure -> BioFileStorageError (router maps 503, graceful-degradation)."""
    from src.modules.vitalia.clinics.application import bio_file_service as svc_module
    from src.modules.vitalia.clinics.application.bio_file_service import BioFileStorageError

    did = uuid4()
    existing = _make_bio_file()
    existing.doctor_id = did  # type: ignore[attr-defined]

    class _BrokenStrategy:
        def get_file_bytes(self, storage_path: str) -> bytes:
            raise FileNotFoundError(storage_path)

    monkeypatch.setattr(svc_module, "_resolve_storage_strategy", lambda: _BrokenStrategy())

    repo = AsyncMock()
    repo.get_by_id.return_value = existing
    svc, repo, _doctor_repo, _audit = _build_service(doctor=_make_doctor_stub(), bio_file_repo=repo)

    with pytest.raises(BioFileStorageError):
        await svc.download_file(tenant_id=uuid4(), clinic_id=uuid4(), doctor_id=did, file_id=uuid4(), user_id=uuid4())


@pytest.mark.asyncio
async def test_service_download_not_found_returns_none() -> None:
    """download_file on missing/cross-tenant file -> None (router 404 generic)."""
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    svc, repo, _doctor_repo, _audit = _build_service(doctor=_make_doctor_stub(), bio_file_repo=repo)

    result = await svc.download_file(
        tenant_id=uuid4(), clinic_id=uuid4(), doctor_id=uuid4(), file_id=uuid4(), user_id=uuid4()
    )

    assert result is None


# ──────────────────────────────────────────────────────────────────────────────
# 6. Repository REAL vs Postgres (integration — auto-skip when PG down)
#    Learning 2026-06-11: mocked-service tests hide the service->repo contract.
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.asyncio
async def test_repo_cross_tenant_get_by_id_returns_none(db_session) -> None:  # noqa: ANN001
    """Dual filter source of cross-tenant 404: row of tenant A invisible to tenant B."""
    from src.modules.vitalia.clinics.domain.bio_file import DoctorBioFile
    from src.modules.vitalia.clinics.infrastructure.repositories.doctor_bio_file_repository import (
        DoctorBioFileRepository,
    )

    tid_a, cid_a, did = uuid4(), uuid4(), uuid4()
    repo = DoctorBioFileRepository(session=db_session)
    bio_file = DoctorBioFile(
        tenant_id=tid_a,
        clinic_id=cid_a,
        doctor_id=did,
        storage_key="t/bio_doc/x.pdf",
        filename="cv.pdf",
        size_bytes=100,
        content_type="application/pdf",
    )
    await repo.add(bio_file, tenant_id=tid_a, clinic_id=cid_a)

    # Same tenant + clinic -> found
    found = await repo.get_by_id(bio_file.id, tenant_id=tid_a, clinic_id=cid_a)
    assert found is not None

    # Cross-tenant -> None (404 at API layer, no leak)
    other = await repo.get_by_id(bio_file.id, tenant_id=uuid4(), clinic_id=cid_a)
    assert other is None

    # Cross-clinic same tenant -> None (HIPAA-lite dual filter)
    other_clinic = await repo.get_by_id(bio_file.id, tenant_id=tid_a, clinic_id=uuid4())
    assert other_clinic is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_repo_soft_delete_excludes_from_list(db_session) -> None:  # noqa: ANN001
    """soft_delete sets deleted_at; list_for_doctor no longer returns the row."""
    from src.modules.vitalia.clinics.domain.bio_file import DoctorBioFile
    from src.modules.vitalia.clinics.infrastructure.repositories.doctor_bio_file_repository import (
        DoctorBioFileRepository,
    )

    tid, cid, did = uuid4(), uuid4(), uuid4()
    repo = DoctorBioFileRepository(session=db_session)
    bio_file = DoctorBioFile(
        tenant_id=tid,
        clinic_id=cid,
        doctor_id=did,
        storage_key="t/bio_doc/y.pdf",
        filename="diploma.pdf",
        size_bytes=200,
        content_type="application/pdf",
    )
    await repo.add(bio_file, tenant_id=tid, clinic_id=cid)

    listed = await repo.list_for_doctor(tenant_id=tid, clinic_id=cid, doctor_id=did)
    assert [f.id for f in listed] == [bio_file.id]

    deleted = await repo.soft_delete(bio_file.id, tenant_id=tid, clinic_id=cid, doctor_id=did)
    assert deleted is True

    listed_after = await repo.list_for_doctor(tenant_id=tid, clinic_id=cid, doctor_id=did)
    assert listed_after == []

    # Idempotent-safe: second soft delete returns False (already gone)
    deleted_again = await repo.soft_delete(bio_file.id, tenant_id=tid, clinic_id=cid, doctor_id=did)
    assert deleted_again is False
