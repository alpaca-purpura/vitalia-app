# T-BE-6 Result — Assets proxy upload router

**Story:** vitalia-fase2-lisa-doctores
**Ticket:** T-BE-6 — "Assets proxy upload router (consume luana-core-assets, copy nicolify wiring)"
**Builder:** builder-backend (Sonnet 4.6)
**State:** pushed
**Date:** 2026-05-31

---

## Skills Consulted

- `backend-expert` — Loaded `runtime-quality-checklist.md` before commit. Confirmed deferred-import pattern (PLC0415 noqa) for DB/engine imports inside route handler to avoid env var validation at module load time. Confirmed `response_model=` mandatory.
- `tessl__fastapi` — Confirmed Annotated dep inline pattern. Confirmed `response_model=AssetUploadResponse` on `POST /upload`. `redirect_slashes=False` at app level (confirmed in main.py).

---

## Technical Design (pre-implementation)

### Scope (D-3)
- Presigned upload does NOT exist in `luana-core-assets` (grep confirmed 0 results for `generate_presigned`).
- Consume `AssetsService.upload_asset` (proxy via boto3 put_object). Never edit engine.
- Copy nicolify wiring pattern: `from luana_core_assets.api import router as assets_gallery` (ref: nicolify/backend/src/main.py:24,1090).

### Implementation plan (Inside-Out: API thin layer only — no new domain/infra/app needed)
1. Add `AssetUploadResponse {key: str, url: str}` DTO to `clinics/api/dtos.py`
2. Create `clinics/api/assets_proxy_router.py`:
   - `POST /upload` with `file: UploadFile` + `kind: Form`
   - `_validate_kind()`: ensure kind ∈ {avatar, credential_doc} → 422 on violation
   - `_validate_content_type()`: image/* for avatar; PDF/JPG/PNG/DOCX for credential_doc → 422 on violation
   - `_read_and_validate_size()`: enforce 10MB max → 422 on violation
   - Defer engine imports (`AssetsService`, `SessionLocal`) inside handler (PLC0415 pattern)
   - Call `AssetsService(db).upload_asset(...)` sync (engine uses sync Session)
   - Return `AssetUploadResponse(key=asset.storage_path, url=asset.public_url)`
   - `response_model=AssetUploadResponse` MANDATORY
   - RBAC: `require_brand_owner_access(user_role)` → admin_clinic
3. Register in `main.py`: `include_router(assets_proxy_router, prefix="/api/v1/vitalia/assets")`
4. Tests (TDD RED-first): `test_assets_upload.py` written BEFORE implementation

### Tests battery (TDD RED → GREEN)
- Structural: importable, POST /upload registered, response_model= declared, DTO fields
- Functional (mock AssetsService + minimal env vars via `monkeypatch`):
  - Valid avatar (image/jpeg) → 200 `{key, url}`
  - >10MB file → 422
  - kind=avatar with application/pdf → 422
  - kind=credential_doc with application/pdf → 200
  - kind=credential_doc with text/plain → 422
  - invalid kind → 422

---

## Deliverables

| Artifact | Status |
|---|---|
| `vitalia/backend/src/modules/vitalia/clinics/api/assets_proxy_router.py` | NEW |
| `vitalia/backend/src/modules/vitalia/clinics/api/dtos.py` | MODIFIED (added AssetUploadResponse) |
| `vitalia/backend/src/main.py` | MODIFIED (include_router assets_proxy_router) |
| `vitalia/backend/tests/modules/vitalia/clinics/test_assets_upload.py` | NEW (10 tests) |

---

## Gate Results

| Gate | Result | Notes |
|---|---|---|
| TDD RED-first | PASS | test written first → ModuleNotFoundError; then GREEN after impl |
| ruff check clinics/ | PASS | 0 errors |
| ruff format --check clinics/ | PASS | 51 files already formatted |
| pytest test_assets_upload.py | PASS | 10/10 |
| pytest clinics/ full suite | PASS | 177/177 |
| arch fitness (334 tests) | PASS | 1 deselected = pre-existing treatment_plans.notes CRM debt (confirmed pre-existing via git stash test) |

**Pre-existing debt noted (not introduced by T-BE-6):**
- `tests/architecture/test_pgcrypto_phi_columns.py::test_no_phi_column_uses_text_or_varchar_unencrypted` → `treatment_plans.notes` defined as TEXT. Tracked in `vitalia/docs/observed-bugs/2026-05-31-pgcrypto-treatment-plans-notes.md`.

---

## Key architectural decisions

- **Deferred imports** inside handler body (PLC0415 noqa) — avoids `luana_core_platform.core.config.Settings` validation at module load time (pattern from `doctors_router._get_db`).
- **Sync `SessionLocal()`** — `AssetsService` uses sync `Session` (not `AsyncSession`); consistent with engine's own API router pattern.
- **`scope="library"`, `purpose="brand_asset"`** — prevents ephemeral 90-day expiry applied to copilot chat uploads; avatars/credentials are permanent assets.
- **kind ∈ {avatar, credential_doc}** — enforced via `_VALID_KINDS` frozenset; 422 on any other value.
- **content_type normalized** via `.lower().split(";")[0].strip()` — handles `image/jpeg; charset=utf-8` edge cases.
- **No path_prefix override needed** — `AssetsService.save()` uses `{tenant_id}/{asset_type}` automatically via `path_prefix = f"{tenant_id!s}/{asset_type.lower()}"`. The `key` returned = `asset.storage_path`.

---

## R2 provisioning note (T-BE-7)

Tests use `LocalStorageStrategy` (STORAGE_PROVIDER=local). Live R2 = T-BE-7 Chris manual action:
- Create R2 bucket `vitalia-assets`
- Generate S3 API tokens in Cloudflare R2 dashboard
- Set env vars: `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `STORAGE_PROVIDER=R2`
- CORS: allow FE origin (http://localhost:3002 in dev)

---

## Anti-orphan integration (CONN)

- **Consumed**: FE `useAvatarUpload` hook (T-FE-2) calls `POST /api/v1/vitalia/assets/upload`; returns `key` used to PATCH `doctor.avatar_key`.
- **On the map**: `# cap: clinics.lisa.doctores` header in router file.
- **Navigable**: mounted at `/api/v1/vitalia/assets/upload` in main.py.
- **Notarized**: `app.include_router(assets_proxy_router, prefix="/api/v1/vitalia/assets", tags=["assets"])` in main.py:89.
