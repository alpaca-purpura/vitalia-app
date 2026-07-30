# T-BE-bio-docs — IMPL-LOG

> Builder: builder-backend (Fable 5, mandato checkpoint `model_mandate_2026_06_12`).
> Brand: vitalia · módulo `clinics` · cap `lisa.doctores` (checkpoint L281, `cap_change_type: new`).
> Brief: CONTEXT-BRIEF.md DELTA v3 — R24 gate OK (`Validator pass:` poblado → `CONTEXT-BRIEF-validation.md`; `Faithfulness flag: partial`, gaps §11 citados abajo).

## Brief §11 gaps consumidos (flag `partial`)

- **F-1 (MEDIUM) — download GREENFIELD:** el assets proxy es upload-only. Verifiqué la superficie real del engine (read-only): `luana_core_assets/infrastructure/storage/{base,local,r2}.py` — `StorageStrategy.get_file_bytes(storage_path)` existe en AMBOS backends; presigned-GET NO existe en ninguno. Decisión § Plan D-1.
- Validator in-process (independencia reducida) → tomé el brief como mapa, verifiqué cada superficie en disco antes de escribir (router post-13bde559, proxy L59/L70, PhiRepositoryBase vs CompoundScopeRepositoryBase, migración 039 chain).

## Plan

### D-1 · Download = stream proxy (decisión F-1, autoridad delegada por ticket/caller)

`GET /{doctor_id}/bio-files/{file_id}/download` **streamea los bytes** (200 + `media_type=content_type` almacenado + `Content-Disposition: attachment`) en vez de devolver `BioFileDownloadResponse {url}`:

1. **Ambos backends:** `get_file_bytes()` es la ÚNICA superficie simétrica local/R2 del engine (R2 presigned-GET no existe; local no tiene presigned posible). Requisito del ticket: "el download debe funcionar con AMBOS".
2. **Privacidad:** bio docs = material privado nunca publicado (03-arch-delta § 3.1). Una URL pública de bucket los haría direccionables sin auth; el stream mantiene RBAC + dual-filter + audit en el único camino de acceso.
3. **V-D3B-4 literal:** "Descarga → status 200 + content-type correcto" — el stream lo satisface directo; un JSON `{url}` lo delegaría a un segundo fetch sin headers.
4. Arch test `test_response_model_required.py` exime returns anotados `-> Response` (heurística L94-96) — sin tocar allowlist.
5. **Deviación documentada:** `BioFileDownloadResponse` NO se crea (sería DTO muerto — gate vulture/dead-code). El 03-arch-delta § 3.1 dejó el mecanismo abierto ("presigned/proxy URL via AssetsService") y el brief F-1 + prompt delegan la decisión. **T-FE-bio-docs:** `useBioFileDownload` = fetch con `useStaffActorHeaders` → blob → objectURL (igual necesitaba headers; una URL indirecta no funcionaba con anchor plano).

### D-2 · Repo base = CompoundScopeRepositoryBase (no PhiRepositoryBase literal)

El ticket dice "PhiRepositoryBase dual-filter", pero el arch test `test_compound_scope_repository_used.py` manda: repos PHI NUEVOS heredan `CompoundScopeRepositoryBase` (engine, lift 2026-05-20) con `scope_field="clinic_id"`; allowlist legacy shrink-only (PhiRepositoryBase = predecesor). Sigo el patrón vivo (`availability_block_repository.py`, `doctor_repository.py`) + método `validate_dual_filter` por consistencia. La INTENCIÓN del ticket (dual-filter incl. `get_by_id`) se cumple idéntica.

### Firmas por capa (DDD inside-out)

**Domain** — `clinics/domain/bio_file.py`:
- `BIO_DOC_ALLOWED_CONTENT_TYPES: frozenset[str]` (PDF/JPEG/PNG/DOCX) — SSoT compartida proxy + register (evita mirror del allow-list).
- `MAX_BIO_FILE_SIZE_BYTES = 10 * 1024 * 1024`.
- `@dataclass DoctorBioFile {tenant_id, clinic_id, doctor_id, storage_key, filename, size_bytes, content_type, id, uploaded_at, created_at, deleted_at}` + `__post_init__` (filename no vacío, size 1..10MB, content_type en allow-list → ValueError).

**Infrastructure**:
- `models/doctor_bio_file_model.py` — `VitaliaDoctorBioFileModel` (`Mapped[]`, `DateTime(timezone=True)`, BigInteger size) espejo tabla 040 + índices `ix_doctor_bio_files_scope` / `ix_doctor_bio_files_tenant`.
- `repositories/doctor_bio_file_repository.py` — `DoctorBioFileRepository(CompoundScopeRepositoryBase[VitaliaDoctorBioFileModel, UUID])`: `get_by_id(entity_id, *, tenant_id, clinic_id)` · `list_for_doctor(*, tenant_id, clinic_id, doctor_id)` (uploaded_at DESC) · `add(bio_file, *, tenant_id, clinic_id)` · `soft_delete(file_id, *, tenant_id, clinic_id, doctor_id) -> bool`. Todas dual-filter + `deleted_at IS NULL`.

**Application** — `application/bio_file_service.py` `BioFileService(bio_file_repo, doctor_repo, audit_repo)`:
- `register_file(...) -> DoctorBioFile | None` — doctor lookup dual-filter (None → cross_tenant_attempt audit + None→404); domain valida metadata (ValueError→422); audit SYNC `doctor.bio_file_added` pre-response.
- `list_files(...)` — read puro (sin audit, per ticket solo added/deleted/downloaded).
- `delete_file(...) -> bool` — fetch dual-filter + match doctor_id (no→cross_tenant audit+False→404); soft delete; audit `doctor.bio_file_deleted`. **RN-D3B-1**: NO toca doctor (bio_public/public_profile snapshot intacta — test asserta cero mutaciones sobre doctor_repo).
- `download_file(...) -> tuple[DoctorBioFile, bytes] | None` — fetch dual-filter; `get_storage_strategy().get_file_bytes(key)` (import diferido, patrón proxy PLC0415); fallo storage → `BioFileStorageError` (→503, graceful-degradation: except+fallback; timeout vive en config engine, no editable brand-side — documentado); audit `doctor.bio_file_downloaded` pre-response.

**API**:
- `assets_proxy_router.py`: `_VALID_KINDS += bio_doc`; `_validate_kind` msg actualizado (gotcha brief §14.3, Spanish neutro); `_validate_content_type` rama bio_doc → `BIO_DOC_ALLOWED_CONTENT_TYPES` (domain).
- `dtos.py`: `BioFileDTO {id, filename, size_bytes, content_type, uploaded_at}` camelCase out (`sizeBytes`/`contentType`/`uploadedAt`) · `BioFileRegisterRequest {storage_key, filename, size_bytes, content_type}` (`extra="forbid"`, camel in) · `BioFilesResponse {bio_files}` · `BioFileDeleteResponse {deleted}` · `DoctorDetailDTO` += `bio_files: list[BioFileDTO] = []`.
- `doctors_router.py`: POST/GET/DELETE `/{doctor_id}/bio-files(/{file_id})` + GET `.../download` — los 4 con RBAC `_STAFF_MUTATION_ROLES` (03-arch-delta § 3.1 "todos") + headers UUID X-Tenant-ID/X-Clinic-ID/X-User-ID (consistencia useStaffActorHeaders). `response_model=` en los 3 JSON; download `-> Response` (exención streaming). `get_doctor`/`patch_doctor` pueblan `bio_files[]` (POST create → lista vacía correcta por construcción).

**Migración** — `alembic/versions/040_vitalia_doctor_bio_files.py`: revision `040_vitalia` ← `039_vitalia`; raw SQL `CREATE TABLE IF NOT EXISTS` + 2 `CREATE INDEX IF NOT EXISTS`; downgrade `DROP ... IF EXISTS`. NUNCA op.create_table/sa.Enum.

### Batería de tests (naturaleza: BE endpoint + repo + migración — test-design-doctrine)

`tests/modules/vitalia/clinics/test_bio_files_api.py` (RED first):
1. Rutas + `response_model=` (POST/GET/DELETE) + download existe con exención Response — introspección router (patrón test_availability_blocks_api).
2. DTOs: campos + aliases camelCase (`sizeBytes`, `contentType`, `uploadedAt`) + `DoctorDetailDTO.bio_files` default [].
3. Proxy: `bio_doc ∈ _VALID_KINDS`; content-type allow (PDF/JPG/PNG/DOCX pasan; `.exe` 422 — RN-D3B-2 backend_unit); kind inválido 422 con mensaje actualizado.
4. Domain: DoctorBioFile valida size 0 / >10MB / content_type fuera de lista → ValueError.
5. Service (AsyncMock repos — patrón suite existente): register→add+audit `doctor.bio_file_added` · register cross-tenant (doctor None)→None+cross_tenant_attempt (V-D3B-1 dual-filter 404) · list delegación dual-filter · delete→soft_delete+audit `doctor.bio_file_deleted` + **RN-D3B-1** (cero calls de mutación sobre doctor_repo) (V-D3B-2) · delete not-found→False+audit · download→bytes+content_type correcto+audit `doctor.bio_file_downloaded` (V-D3B-4) · download storage error→BioFileStorageError (graceful).
6. Repo REAL contra Postgres (`db_session` + `@pytest.mark.integration`, skip si PG down — learning 2026-06-11 mocked-service-tests): insert tenant A → `get_by_id` tenant B = None (cross-tenant 404 source) + soft_delete excluye de list.

`tests/migrations/test_040_doctor_bio_files_idempotency.py` (patrón test_035):
- Estructurales: existe, chain 040→039, IF NOT EXISTS everywhere, sin op.create_table/add_column/sa.Enum, TIMESTAMPTZ, 2 índices, downgrade IF EXISTS.
- Integración doble-upgrade (skip sin PG): `alembic upgrade head` ×2 = no-op.

### Integración (CONN — anti-orphan)

- **Registro:** rutas montadas en `doctors_router` existente (ya `include_router` en `main.py:72`) — cero wiring nuevo.
- **Consumer:** T-FE-bio-docs (`depends_on: [T-BE-bio-docs]`) — `useBioFileUpload`/`useBioFiles`/`useDeleteBioFile`/`useBioFileDownload`.
- **On-map:** cap `lisa.doctores` (zona Agentes → Lisa) · reachability: workspace doctor → hoja Perfil/Página → BioRepoInputs.
- **Notarized:** header `# cap: clinics.lisa.doctores` en todo archivo nuevo.

### Prior-art (Step 0 grep — brief §6/§7 confirmado en disco)

`bio_doc`/`vitalia_doctor_bio_files`/`BioFileService` = 0 hits en código (greenfield). EXTEND: assets proxy (kind), doctors_router (sub-rutas), CompoundScopeRepositoryBase (engine import). Cero mirror cross-brand; cero edit engine.

## Skills Consulted

- `backend-expert` — invocada por command (Step 0 GATE). SOP "Nuevos features (Inside-Out)" aplicado; **`references/runtime-quality-checklist.md` LEÍDO COMPLETO antes de codear** — decisiones: sin type-alias Annotated para deps (patrón `_get_db` existente), request DTO `extra="forbid"`, `Mapped[]`+`DateTime(timezone=True)`, 404-no-403 en cross-tenant, `response_model=` en todo JSON endpoint + exención `-> Response` para stream (checklist § response_model + arch test L94).
- FastAPI canonical patterns — `Header(alias=...)` UUID tipado (422 nativo), `Depends` route-level RBAC, deferred imports patrón codebase (PLC0415), `Response` con media_type/Content-Disposition para binario.
- pytest async testing patterns — `asyncio_mode=auto`, AsyncMock para servicio (patrón suite clinics), `db_session` fixture + `@pytest.mark.integration` auto-skip sin PG (conftest L95-130), introspección de rutas en vez de TestClient (precedente test_availability_blocks_api).
- graceful-degradation — llamada externa storage (R2/local): try/except → `BioFileStorageError` → 503 con mensaje Spanish neutro + `logger.exception`. Limitación: timeout boto3 vive en config del engine (read-only, no editable brand-side) — fallback + error-mapping cubiertos; circuit breaker N/A (operación user-triggered de bajo volumen, igual que upload proxy shipped).
- `brand-expert` / `offer-expert` / `offer-type-preset-expert` / `metrics-expert` — cargadas por el wrapper del command; **decisión: N/A scope** — el ticket toca SOLO `clinics` (ni brand_studio, ni offer, ni analytics, ni manychat). Sin extracción de reglas aplicables.

## Cross-module reads (read-only)

- `core/luana-core-assets/src/luana_core_assets/{application/assets_service.py, infrastructure/storage/{base,local,r2}.py}` — superficie download (F-1). NO editado.
- `core/luana-core-platform/src/luana_core_platform/repositories/compound_scope_repository.py` — contrato base repo. NO editado.

## Bitácora RED→GREEN

### Continuation (sesión 2 — contexto límite sesión 1)

**Sesión 1** murió tras completar el diseño y escribir domain+infra+application+migración. API layer (DTOs + proxy kind + router endpoints) faltaba.

**RED baseline (heredado de sesión 1):** `pytest tests/modules/vitalia/clinics/test_bio_files_api.py -m "not integration"` fallaba con ImportError — `BioFileDTO`, `BioFileRegisterRequest`, `BioFilesResponse`, `BioFileDeleteResponse` no existían en `dtos.py`; rutas bio-files no registradas en `doctors_router.py`; `bio_doc` ausente de `_VALID_KINDS`.

**Implementación (sesión 2, orden inside-out):**

1. **`dtos.py`** — añadidas 4 clases: `BioFileDTO` (camel out: `sizeBytes`/`contentType`/`uploadedAt`), `BioFileRegisterRequest` (camel in, `extra="forbid"`), `BioFilesResponse` (`bio_files: list[BioFileDTO]`), `BioFileDeleteResponse` (`deleted: bool`). `DoctorDetailDTO.bio_files` ya existía (sesión 1).

2. **`assets_proxy_router.py`** — `_VALID_KINDS += "bio_doc"`; `_validate_kind` msg actualizado (menciona `bio_doc`); `_validate_content_type` rama `bio_doc` → `BIO_DOC_ALLOWED_CONTENT_TYPES` (domain SSoT, no mirror). Import: `from src.modules.vitalia.clinics.domain.bio_file import BIO_DOC_ALLOWED_CONTENT_TYPES`.

3. **`doctors_router.py`** — importados: `BioFileDeleteResponse`, `BioFileDTO`, `BioFileRegisterRequest`, `BioFilesResponse`, `DoctorBioFile`, `DoctorBioFileRepository`, `BioFileService`, `BioFileStorageError`, `Response`. Agregado `_build_bio_file_service()` helper. Agregados 4 endpoints + mapper `_to_bio_file_dto`:
   - `POST /{doctor_id}/bio-files` → `BioFilesResponse` (201) · RBAC `_STAFF_MUTATION_ROLES` · re-fetch lista post-commit.
   - `GET /{doctor_id}/bio-files` → `BioFilesResponse` · RBAC.
   - `DELETE /{doctor_id}/bio-files/{file_id}` → `BioFileDeleteResponse` · RBAC.
   - `GET /{doctor_id}/bio-files/{file_id}/download` → `Response` (stream exemption D-1) · RBAC · `BioFileStorageError → 503` graceful.

4. **Ruff format** — 4 archivos escritos por sesión 1 reformateados (sesión 1 no corrió ruff format).

**GREEN results:**
- `test_bio_files_api.py -m "not integration"`: **32/32 PASS**
- `test_040_doctor_bio_files_idempotency.py -k "not double_upgrade"`: **10/10 PASS** (static structural)
- `test_040 :: test_double_upgrade_is_noop`: SKIP/FAIL — DB no en head (migration 015 falla en tabla `offers` inexistente — pre-existing, ajeno a T-BE-bio-docs)
- `tests/modules/vitalia/clinics/ -m "not integration"`: **353/353 PASS** (sin regresiones)
- `tests/architecture/ (excl. pgcrypto pre-existing)`: **326/326 PASS**
- `ruff check`: PASS
- `ruff format --check`: PASS

**Pre-existing failures (documentados, no introducidos):**
- `test_pgcrypto_phi_columns::test_no_phi_column_uses_text_or_varchar_unencrypted` — `treatment_plans.notes TEXT` (pre-existing, confirmado con `git stash`)
- `test_double_upgrade_is_noop` — DB no en head (migration 015 `offers` table missing)
- `test_bio_files_api.py @integration tests` — `vitalia_doctor_bio_files` table no existe (migration no aplicada; skip automático per `@pytest.mark.integration` con PG disponible pero tabla ausente — requiere `alembic upgrade head` en el container)
