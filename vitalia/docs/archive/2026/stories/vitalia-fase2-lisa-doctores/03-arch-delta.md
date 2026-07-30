---
story_id: vitalia-fase2-lisa-doctores
brand: vitalia
arch_version: 1
arch_doc: 03-arch-delta.md            # DELTA over 03-arch.md (2026-05-31, Opus 4.8) — NOT a rewrite
schema_version: v5
architecture_pattern: ADR-vitalia-004
adr_004_compliance: full
ready_package_delta_by: architect-orchestrator (Fable 5)   # ★ Chris mandate 2026-06-12 — NOT Opus 4.8
ready_package_delta_at: 2026-06-12
supersedes: none                       # appends to the built ready package; story state stays `developing`
delta_source: "checkpoint.md § scope_extension_2026_06_11 (firma_1 + firma_2 TRUE) + 01-spec.md § ★ Delta v3 (D3-A..D3-F)"
---

# Contract DELTA: vitalia-fase2-lisa-doctores — scope extension v3 (D3-A..D3-F)

> **DELTA MODE.** The original ready package (03-arch.md/-be/-fe, 2026-05-31) is BUILT and live-verified (read+write green, dod_evidence in checkpoint). This document adds ONLY the v3 deltas. Do NOT re-architect the built surfaces. Builders consume this + the original arch for context.
>
> **Model disclosure:** authored by `architect-orchestrator` running as **Fable 5** (Chris mandate 2026-06-12), not Opus 4.8. Live research not required — all deltas reuse shipped patterns (EntityPicker core, assets R2 proxy, dateutil.rrule, Next public routes). No novel framework patterns introduced.

## 0. Context Summary

- **Story:** F2-S8 vitalia-fase2-lisa-doctores · state `developing` (reanudada) · cap `lisa.doctores` (`new`)
- **Delta run on:** 2026-06-12
- **Modules touched:** `clinics` (BE) + `lisa` feature (FE) + `core/@luana/ui-kit` (EXTEND via promotion proposal only)
- **6 workstreams:** D3-A switcher · D3-B bio-docs · D3-C occurrences-consume (FIX) · D3-D página pública · D3-E vista mes · D3-F recurrencia Google-clone

### Surface → builder → auditor mapping (PM uses to spawn correct agents)

| Surface | Builder | Auditor |
|---|---|---|
| `core/@luana/ui-kit/{EntitySubNavBar,EntityWorkspaceLayout}.tsx` (EXTEND, additive) | `builder-frontend` (Sonnet) **+ /pm-luana promotion gate** | `auditor-frontend` (Opus) + /pm-luana lift review |
| `vitalia/backend/src/modules/vitalia/clinics/**` | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| `vitalia/frontend/src/features/lisa/**` + `app/[tenantId]/(shell-organism)/lisa/staff/**` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/app/d/[clinica-slug]/[doctor-slug]/**` (public route, no auth) | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |

- **Skills consulted (decisions only):**
  - `frontend-expert` + `vitalia-design-system` → canon §2.4 (EntityPicker reuse, no client-side full-collection load), §2.5 (Select canónico — no native `<select>` in D3-F editor), §2.6 (single FloatingAutosaveIndicator — kill inline-emoji autosave in BioRepoInputs).
  - `backend-expert` → dateutil.rrule already in-tree (D-2 original); `rrule(byweekday=list, interval=N)` is native (no engine touch); assets proxy reuse (D-3 original).
  - `brand-expert` → public structured profile supersedes BioPublic 3-blobs; voice anchor for generation only (NOT agentic — D-4 original holds; R23 N/A).
- **CONTEXT-BRIEF source:** original brief (2026-05-31) covers built surfaces; this delta self-ran the NO-NEW-LAYER scan (§ Existing systems audit below).
- **Engine boundary:** ZERO direct core edits except T-CORE-picker-slot (additive prop) gated by promotion proposal. NO `core/luana-core-*` Python touched.
- **Architecture gates that must keep passing:** `test_phi_dual_filter.py`, `test_response_model_required.py`, `test_migrations_idempotent.py`, `test_clinics_domain_no_engine_imports.py`, `test_public_doctors_allowlist.py`, `test-no-div-layout.test.ts`, `test-no-native-select.test.ts`, `test-ribbon-no-shadcn-tabs.test.ts`, `test_fsd_boundaries.test.ts`, `@luana/ui-kit` unit suite (EntitySubNavBar/EntityPicker back-compat).

---

## 1. Prior art audit (NO-NEW-LAYER · anti-duplication-refining)

### Source of evidence
- [x] Self-run greps (Path B) over `core/@luana/ui-kit`, `core/luana-core-*`, `vitalia/backend/.../clinics`, sibling FE features.

### Sistemas existentes encontrados

| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| `EntityPicker` (search server-side debounced + cursor paginated + windowed, escala 200+) | `core/@luana/ui-kit/src/EntityPicker.tsx` | **active** (core-ds-foundation T-6) | **REUSE** — D3-A wires it; ZERO new picker. Already query-lib-agnostic (`searchFn` prop). |
| `EntitySubNavBar` (N3 ribbon, static entity identity slot) | `core/@luana/ui-kit/src/EntitySubNavBar.tsx` | **active** | **EXTEND** — add optional picker slot prop (canon §6.3 already mandates EntityPicker composition; current build has static identity → gap). Additive, brand-agnostic → promotion proposal. |
| `EntityWorkspaceLayout` (wraps EntitySubNavBar) | `core/@luana/ui-kit/src/EntityWorkspaceLayout.tsx` | **active** | **EXTEND** — forward picker slot prop verbatim (same as it forwards `onAddAffordance`). |
| `AvailabilityProjectionService` (`rrule(count/until)`, weekly/biweekly) | `vitalia/.../clinics/application/availability_projection_service.py` | **active, CORRECT** | **EXTEND** — D3-C consumes it via a new range endpoint (no new projection logic); D3-F extends it to `byweekday=list + interval`. |
| Assets proxy upload → R2 (`AssetsService.upload_asset`) | `vitalia/.../clinics/api/assets_proxy_router.py` (kind ∈ {avatar, credential_doc}) | **active** | **EXTEND** — D3-B adds `bio_doc` kind to the existing allow-list (no new upload path). |
| Public doctors endpoint (allow-list serializer) | `vitalia/.../clinics/api/public_doctors_router.py` + `public_doctor_serializer.py` | **active** | **EXTEND** — D3-D adds a per-doctor structured route to the same router + extends the allow-list serializer (NOT a new public layer). |
| `useAvatarUpload`, `usePatchDoctor`, `useDoctor`, `useAvailabilityBlocks` (RQ hooks) | `vitalia/.../lisa/api/staff.ts` | **active** | **REUSE/EXTEND** — D3-B `useBioFileUpload` mirrors `useAvatarUpload`; D3-C `useAvailabilityOccurrences` is a new RQ hook over the new range endpoint. |

### Cross-brand mirror check
- D3-A picker slot is **brand-agnostic** → MUST live in core (not mirrored in vitalia). Promotion proposal redacted as deliverable of T-CORE-picker-slot. `adrian/NewLeadPage.tsx` already consumes `EntitySubNavBar` from `@luana/ui-kit` → back-compat is HARD (optional prop, default = current static identity).
- No other brand mirrors `availability_projection`/`bio_files`/`public structured profile` — these stay vitalia-local (clinics module).

### Decisión final
EXTEND everywhere. ONE NEW core prop (gated). NO new layer, NO cross-brand mirror.

---

## 2. D3-A · Entity switcher in the N3 ribbon (EntityPicker slot)

### 2.1 CORE EXTEND (T-CORE-picker-slot · promotion proposal required)

Add an **optional** picker slot to both core components. Additive, back-compat (existing consumers render unchanged).

```tsx
// EntitySubNavBar.tsx — EntitySubNavBarProps (ADD)
/**
 * Optional entity-identity selector. When provided AND entity is set (workspace mode),
 * this node renders in the entity-identity slot INSTEAD of the static avatar+name.
 * Canon §6.3: the entity identity IS a selector (EntityPicker) — "cambiar sin volver".
 * When omitted → current static identity renders (back-compat: adrian/NewLeadPage, ICPs).
 */
entityIdentitySlot?: React.ReactNode;
```
- Render rule: in workspace mode (`entity !== null`), if `entityIdentitySlot` provided → render it where the static `<div aria-label="Editando: {name}">` block currently sits; else keep the static block verbatim.
- `EntityWorkspaceLayoutProps` adds the same `entityIdentitySlot?: React.ReactNode` and forwards it verbatim to `<EntitySubNavBar entityIdentitySlot={...} />` (mirror of how `onAddAffordance` is forwarded).
- a11y: the slot owns its own combobox (EntityPicker already provides `aria-haspopup=listbox` + listbox/option roles + ↑↓/Enter/Esc + focus-on-open). The ribbon `role=tablist` is unaffected (the identity slot is NOT a tab).
- **Promotion proposal:** `docs/promotion-protocol/proposals/2026-06-12-lift-entitysubnavbar-picker-slot.md` (aditiva, brand-agnostic, back-compat). Redacted as a deliverable of T-CORE-picker-slot. **Merge gated by /pm-luana lift acceptance.**
- Tests (core, back-compat ratchet): `EntitySubNavBar.test.tsx` + `EntityWorkspaceLayout.test.tsx` — (a) absent slot → static identity renders (existing assertions unchanged); (b) present slot → custom node renders, static identity absent; (c) master mode (entity=null) → slot NOT rendered.

### 2.2 Vitalia cabling (T-FE-switcher-wire)

Doctors list is **page-based** (`GET /api/v1/vitalia/clinics/doctors?q=&page=&page_size=&active=`). EntityPicker wants a cursor `searchFn`. Adapter maps page↔cursor:

```ts
// features/lisa/api/staff.ts — NEW
const doctorPickerSearchFn: EntitySearchFn<DoctorPickerItem> = async ({ q, cursor, limit }) => {
  const page = cursor ? Number(cursor) : 1;                 // cursor = stringified next page
  const params = new URLSearchParams({ page: String(page), page_size: String(limit), active: "true" });
  if (q) params.set("q", q);
  const res = await fetchJson(`${API_BASE}/api/v1/vitalia/clinics/doctors?${params}`, { headers: staffActorHeaders });
  const lastPage = Math.max(1, Math.ceil(res.total / res.pageSize));
  return {
    items: res.items.map(d => ({ id: d.id, name: d.displayName ?? `${d.firstName} ${d.lastName}` })),
    nextCursor: page < lastPage ? String(page + 1) : null,
    total: res.total,
  };
};
```
- **RN-D3A-1:** server filter `q` (never client-side full-collection — canon §2.4). **RN-D3A-2:** `active=true` excludes inactive.
- Consumer (`StaffWorkspaceShell`): build `<EntityPicker value={{id, name}} searchFn={doctorPickerSearchFn} onChange={onPickDoctor} />` and pass as `entityIdentitySlot` to `EntityWorkspaceLayout`.
- **Navigate preserving leaf:** `onPickDoctor(d)` → derive current leaf from `usePathname()` (last segment ∈ {perfil, horarios, servicios, pagina}) → `router.push('/${tenantId}/lisa/staff/${d.id}/${currentLeaf}')`. SC-D3A-1: Horarios of Ana → Horarios of Carlos.
- Master mode (directorio, no entity): no picker (existing root-pill behavior).
- Reachability (CONN): consumer = `StaffWorkspaceShell` (already mounted on every `[doctor-id]` route). Notarized = the picker is wired into the existing layout; no new route.

### 2.3 No new endpoint — `GET /clinics/doctors` already supports `q`, `page`, `page_size`, `active`. ZERO BE change for D3-A.

---

## 3. D3-B · Bio material upload (funcional) — BE + FE

### 3.1 BE (T-BE-bio-docs)

**Kind decision:** add **`bio_doc`** (new) to the assets proxy allow-list — distinct from `credential_doc` (credential verification) because bio material is private input never published. Content-type allow-list = same as credential_doc (PDF/JPG/PNG/DOCX, ≤10MB).

```python
# assets_proxy_router.py — EXTEND _VALID_KINDS + per-kind allow-list
_VALID_KINDS = frozenset({"avatar", "credential_doc", "bio_doc"})
# bio_doc shares _CREDENTIAL_DOC_ALLOWED_CONTENT_TYPES (PDF/JPG/PNG/DOCX)
```

**NEW table `vitalia_doctor_bio_files`** (migration 040, idempotent raw SQL):

| col | type | notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | dual-filter |
| `clinic_id` | UUID NOT NULL | dual-filter (hipaa-lite) |
| `doctor_id` | UUID NOT NULL | FK logical → vitalia_doctors |
| `storage_key` | TEXT NOT NULL | R2 object key (from assets proxy) |
| `filename` | TEXT NOT NULL | original name (truncated in UI) |
| `size_bytes` | BIGINT NOT NULL | |
| `content_type` | TEXT NOT NULL | |
| `uploaded_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | drives RN-D3D-4 material-new detection |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| `deleted_at` | TIMESTAMPTZ NULL | soft delete |

Indexes: `ix_doctor_bio_files_scope (tenant_id, clinic_id, doctor_id)` + `ix_doctor_bio_files_tenant (tenant_id)`. Repo inherits `PhiRepositoryBase` (dual filter incl `get_by_id`).

**Endpoints (under existing `doctors_router`, all `response_model=` + RBAC `_STAFF_MUTATION_ROLES` {owner, admin_clinic}):**

| Method | Path | Request | response_model | Notes |
|---|---|---|---|---|
| POST | `/{doctor_id}/bio-files` | `BioFileRegisterRequest {storage_key, filename, size_bytes, content_type}` | `BioFileDTO` | called after `/assets/upload` (kind=bio_doc) returns key. Audit `doctor.bio_file_added`. |
| GET | `/{doctor_id}/bio-files` | — | `BioFilesResponse {bio_files: list[BioFileDTO]}` | also folded into `DoctorDetailDTO.bio_files[]` |
| DELETE | `/{doctor_id}/bio-files/{file_id}` | — | `BioFileDeleteResponse {deleted: bool}` | soft delete + audit `doctor.bio_file_deleted`. Tenant+doctor scoped → cross-tenant 404. **RN-D3B-1: bio_public/public_profile snapshot untouched.** |
| GET | `/{doctor_id}/bio-files/{file_id}/download` | — | `BioFileDownloadResponse {url}` | resolves presigned/proxy URL via AssetsService; audit `doctor.bio_file_downloaded`. SC-D3B-4 content-type correct. |

`DoctorDetailDTO` (EXTEND): add `bio_files: list[BioFileDTO]` where `BioFileDTO {id, filename, size_bytes, content_type, uploaded_at}` (camelCase out: `sizeBytes`, `uploadedAt`).

### 3.2 FE (T-FE-bio-docs)

`BioRepoInputs.tsx` rewrite (canon homologation):
- Real upload via NEW `useBioFileUpload(doctorId)` (mirror `useAvatarUpload`: POST `/assets/upload` kind=bio_doc → POST `/{doctor_id}/bio-files`). Optimistic row + RQ invalidate.
- List rows: icon by content-type (PDF/IMG/DOCX) + filename (truncate) + size + date + **descargar** (useBioFileDownload) + **eliminar** (confirm dialog → useDeleteBioFile). States: subiendo (per-file progress), error (reintentar/quitar), empty (soft text). **RN-D3B-2:** rejected file (type/size) → inline feedback, never silent.
- Canon: kill raw `<textarea>`/`<button>` → `Textarea`/`Button` atoms; links Zod-validated (URL) chips; **kill inline-emoji autosave** → rely on the single page `FloatingAutosaveIndicator` (canon §2.6). Card homologated (border + `agent-lisa` header).
- `staff.types.ts` (EXTEND): `DoctorDetail.bioFiles?: BioFile[]` where `BioFile {id, filename, sizeBytes, contentType, uploadedAt}`.

---

## 4. D3-C · Occurrences projection consume (FIX) — root cause anchored

### 4.1 Root cause (CONFIRMED, repro_evidence in checkpoint)
`AvailabilityCalendar.tsx::recurrentBlockVisibleInWeek` (L99-115) only handles `end_date`; for `end_condition_kind ∈ {occurrences, open_ended}` it `return true` always → block painted in EVERY week. BE `AvailabilityProjectionService` (`rrule(count=occurrences)`) is **correct**. Drift = FE duplicates expansion client-side instead of consuming the BE projection (SSoT) — 4th instance of the imagined-contract pattern in this story.

### 4.2 Direction (ratified): both views consume BE projection of the visible range. `recurrentBlockVisibleInWeek` + `oneOffBlockVisibleInWeek` + client `blocksByDay` expansion **DIE**.

### 4.3 BE (T-BE-occurrences-endpoint)
NEW range endpoint — reuses `AvailabilityProjectionService` (no new projection logic):

```
GET /api/v1/vitalia/clinics/doctors/{doctor_id}/availability-occurrences?from=YYYY-MM-DD&to=YYYY-MM-DD
response_model = AvailabilityOccurrencesResponse { occurrences: list[AvailabilityOccurrenceDTO] }
AvailabilityOccurrenceDTO { block_id, occurrence_date, start_time, end_time, kind, freq | null, pattern_summary }
```
- Impl: load active blocks (dual-filter) → for each, `project_block(block, reference_date=from)` → collapse slots to one occurrence per (block, date) within `[from, to]` → return block-level occurrences (calendar paints blocks, not 30-min slots).
- `pattern_summary` = human pattern string (post D3-F it reflects days_of_week+interval; pre D3-F = "Semanal"/"Quincenal"/"Único"). **RN-D3F-1: same source as the editor summary (shared formatter `format_recurrence_summary`).**
- `from/to` bounded (max 62 days) to avoid unbounded projection.
- **8-case battery (SC-D3C-1..8) backend_integration, RED first:** SC-D3C-1 weekly occurrences=2 → exactly 2 dates (off-by-one guard); SC-D3C-2 biweekly occurrences=3 → 3 dates spaced 14d (span 6 weeks); SC-D3C-3 end_date inclusive (TZ tenant); SC-D3C-4 open_ended horizon (90d, not infinite, not short); SC-D3C-5 edit recurrent → count not reset/duplicated; SC-D3C-6 one_off + recurrent overlap same day → both; SC-D3C-7 delete recurrent → all occurrences gone; SC-D3C-8 TZ midnight border → correct day.

### 4.4 FE (T-FE-occurrences-consume)
- NEW `useAvailabilityOccurrences(doctorId, fromIso, toIso)` RQ hook.
- Week view: compute visible `[monday, sunday]` → consume occurrences → render directly (each occurrence = a `CalendarBlock` at its date/time). DELETE `recurrentBlockVisibleInWeek`, `oneOffBlockVisibleInWeek`, `blockDayOfWeek`, client `blocksByDay` expansion.
- `useAvailabilityBlocks` still used for **edit** (BloquePopover opens a block to edit), NOT for paint. Paint = occurrences SSoT.
- Regression e2e (SC-D3C-1 paint): weekly occurrences=2 → calendar paints EXACTLY 2 weeks (not indefinite). + SC-D3C-5/6/7 e2e (edit/overlap/delete).

---

## 5. D3-E · Month view (NEW) — FE only (T-FE-vista-mes)

- Toggle **Semana | Mes** in Horarios header (canon `Select`/pills, default Semana; drag-create only in Semana).
- Month grid 6×7. Each day cell: compact chips (start–end, `agent-lisa` tint) + overflow `+N más`.
- **Data: consume the SAME occurrences endpoint** over the visible month range `[firstVisibleDay, lastVisibleDay]` (coherent with D3-C — no client-side expansion). **RN-D3E-1:** occurrences=2 block → chips in exactly 2 dates.
- Click day → switch to Semana of that week (focused day). **RN-D3E-2: read+nav only (no writes from month).**
- States: skeleton grid (loading) / soft empty / error + retry. Nav: ‹ prev · hoy · next ›. a11y: grid navigable, aria-labels per day.
- Depends on T-FE-occurrences-consume (the endpoint + hook).

---

## 6. D3-D · Public doctor page (structured + state-driven) — BE + FE

### 6.1 BE (T-BE-pagina-publica)
**Supersede `BioPublic` (3 blobs) → `DoctorPublicProfile` (structured).** Domain VO + JSONB column `vitalia_doctors.public_profile` (migration 041, additive, compat).

```python
@dataclass(frozen=True)
class DoctorPublicProfile:
    sobre_mi: str | None = None
    formacion: list[FormacionItem] = field(default_factory=list)      # {titulo, institucion, anio}
    experiencia: list[ExperienciaItem] = field(default_factory=list)  # {puesto, lugar, anios}
    tratamientos: list[str] = field(default_factory=list)             # chips
    certificaciones: list[str] = field(default_factory=list)          # ✓ list
    idiomas: list[str] = field(default_factory=list)                  # RN-D3D-5: rendered public only if len>1
```
- **Migration 041 (idempotent):** `ADD COLUMN IF NOT EXISTS public_profile JSONB`, `bio_generated_at TIMESTAMPTZ`, `public_slug TEXT`. Backfill compat: `public_profile.sobre_mi ← bio_public.resumen`; `formacion ← [{titulo: bio_public.formacion, institucion:null, anio:null}]` when present; `bio_public` retained read-only for legacy. `public_slug` backfilled from `slugify(first_name-last_name)` unique per (tenant_id, clinic_id) with numeric suffix on collision. Unique index `ux_doctors_public_slug (tenant_id, clinic_id, public_slug)`.
- **`bio_generated_at`** set ONLY on generation (RN-D3B-4). **Material-new detection (RN-D3D-4, server):** `material_new = max(bio_files.uploaded_at, doctor.updated_at_inputs, bio_links change) > bio_generated_at`. Exposed via `DoctorDetailDTO.profile_state { generated_at, material_new, material_new_count }`.
- **Public route extension** on `public_doctors_router`:
  ```
  GET /api/public/clinic/{tenant_slug}/doctors/{doctor_slug}   (NO auth)
  response_model = PublicDoctorProfileDTO   (allow-list, structured)
  ```
  - Allow-list serializer EXTEND (`public_doctor_serializer.to_public_profile_dto`): emits `{display_name, specialty, clinic_name, credential_label (✓ verified), public_profile.*}`. **NO stats** (D3-D.1), **NO CTA** (D3-D.1). `idiomas` only if `len>1` (RN-D3D-5). Filter: `visible_en_landing AND active`. Toggle OFF / unknown slug / cross-tenant slug-fuzzing → **generic 404 "perfil no disponible"** (RN-D3D-2, SC-D3D-6). PHI NEVER serialized (allow-list is the security boundary; new arch test asserts `PublicDoctorProfileDTO` has zero PHI fields).
- Generation service (T-BE-pagina-publica, reuses BioGenerationService deterministic, NOT agentic — D-4 holds): produces structured sections from material; overwrite requires confirm (RN-D3B-3) handled FE-side.

### 6.2 FE (T-FE-pagina-publica)
- **NEW 4th leaf "Página"** → route `app/[tenantId]/(shell-organism)/lisa/staff/[doctor-id]/pagina/page.tsx` (Server → client view). Add to `LEAF_DEFS` in `StaffWorkspaceShell`. Bio/material block MOVES from Perfil leaf to Página (cross-link card on Perfil).
- Pipeline in one place: estado pill (Publicada/Borrador) · URL estable `{APP_BASE_URL}/d/{clinica-slug}/{doctor-slug}` · Copiar link · Ver página · toggle "Visible públicamente" · material privado (notas + dropzone D3-B + links) · structured editor (Sobre mí · Formación[] · Experiencia[] · Tratamientos · Certificaciones[] · Idiomas[], inline + autosave) · phone-frame preview.
- **State-driven generation (kills "regenerar porque sí"):** never-generated → single CTA "✨ Generar perfil"; generated+quiet → "Última generación {fecha}" + ⋮(Regenerar todo, secondary), NO primary CTA; material-new (server `profile_state.material_new`) → banner "⚡ {N} nuevos" + CTA "✨ Actualizar perfil". Overwrite with manual edits → confirm modal (RN-D3B-3, SC-D3D-5).
- **Public Next route** `app/d/[clinica-slug]/[doctor-slug]/page.tsx` — **Server Component, NO auth, NO `(shell-organism)` group**. Fetches `GET /api/public/clinic/{clinica-slug}/doctors/{doctor-slug}`. Mobile-first Doctoralia structure (D3-D.1): header (foto·nombre·especialidad·badge "✓ Nro. colegiatura CMP verificado") → Sobre mí → Formación → Experiencia profesional → Tratamientos (chips) → Certificaciones (✓) → Idiomas (conditional) → Consultorio (nombre+dirección, informativo). **SIN CTA contacto, SIN stats.** Toggle OFF / bad slug → "perfil no disponible" page (not broken 404, no leak).
- **`APP_BASE_URL` = env var, NEVER hardcoded:** `NEXT_PUBLIC_APP_BASE_URL` (dev `dev-app.vitalialat.com` · test `test-app.vitalialat.com` · prod `app.vitalialat.com`). Surfaced to BE for link generation via `APP_BASE_URL` settings var too.
- Depends on T-BE-pagina-publica + T-FE-bio-docs (dropzone/material reused).

### 6.3 Page-construction completeness (spec § D3-D.2 — close the artifact gaps)
- **RN-D3D-6 (partial profile minimum):** the public page renders with WHATEVER sections exist — guaranteed minimum = identity (nombre+especialidad+colegiatura+clínica). A section with no content is OMITTED (never an empty box). Doctor visible ON but never-generated → valid page with the minimum (SC-D3D-9). The BE serializer returns the structured profile as-is (nullable sections); FE renders only non-empty sections.
- **RN-D3D-7 (WhatsApp preview / Open Graph):** the public route emits OG metadata via Next `generateMetadata()` — `og:title` = nombre + especialidad · `og:description` = start of Sobre mí (or specialty fallback) · `og:image` = doctor photo (or brand fallback). So the link Adrián sends shows a decent preview card in WhatsApp (SC-D3D-10 state_check the HTML head). NO PHI in OG tags (allow-list applies).
- **RN-D3D-8 (missing photo):** no avatar → initials avatar with tint (same as workspace); `og:image` → brand fallback. Never a broken image (SC-D3D-11).
- **RN-D3D-9 (nonexistent slug = anti-enumeration):** `/d/{x}/{y}` unknown → the SAME generic "perfil no disponible" view as toggle-OFF (no distinction between not-exists vs disabled — prevents slug enumeration). BE returns the same 404 shape for unknown-slug, disabled, and cross-tenant (SC-D3D-12). This subsumes the cross-tenant slug-fuzz (SC-D3D-6) into one indistinguishable response.
- **Responsive:** mobile-first 390×844 primary (no horizontal overflow, legible — SC-D3D-7); desktop degrades to centered max-width content (SC-D3D-8).
- **a11y + i18n:** public page axe wcag2aa 0 violations + keyboard-navigable (SC-D3D-13); all copy Spanish neutro, no voseo (SC-D3D-14).
- **Workspace link actions:** "📋 Copiar link" → clipboard has the env-correct URL; "👁 Ver página" → opens the public page (SC-D3D-15).

---

## 7. D3-F · Recurrence editor (Google Calendar clone) — BE + FE

### 7.1 BE (T-BE-recurrencia-domain)
Domain extension: `day_of_week: int|None` → **`days_of_week: list[int]`** (multi-day) + **`interval: int`** (1=weekly, 2=biweekly, N custom). `freq` retained read for legacy compat.
- **Migration 042 (idempotent, compat):** `ADD COLUMN IF NOT EXISTS days_of_week JSONB`, `interval INTEGER`. Backfill: `days_of_week = [day_of_week]`, `interval = (freq='biweekly' ? 2 : 1)`. **RN-D3F-3: legacy single-day blocks project identically post-migration** (SC-D3F-4 regression).
- Domain validation (`availability_block.py`): recurrent requires `len(days_of_week) >= 1` AND `interval >= 1` AND exactly one end_condition. Keep `day_of_week`/`freq` as derived back-compat (or map at repo boundary).
- Projection (`availability_projection_service.py`): `rrule(WEEKLY, interval=interval, byweekday=days_of_week, count=occurrences | until=...)`. **RN-D3F-2: `count` = TOTAL occurrences across all weekdays (Google semantics)** — rrule's `count` already counts every occurrence date, so a 2-day × 4 weeks = count of occurrences, not weeks. SC-D3F-1: custom L+J every 2 weeks ×8 → 8 occurrence dates.
- Shared `format_recurrence_summary(block) -> str` (BE) consumed by both `pattern_summary` (occurrences endpoint) and any BE display. **RN-D3F-1: single source.**
- DTOs (EXTEND `AvailabilityBlockDTO`): `days_of_week: list[int]`, `interval: int` (camelCase `daysOfWeek`, `interval`). Create/PATCH accept the new shape; legacy single-day payloads still accepted (coerced to list).
- Depends on T-BE-occurrences-endpoint (serialize edits on `availability_projection_service.py`).

### 7.2 FE (T-FE-recurrencia-editor)
`BloquePopover.tsx` rewrite (canon §2.5 — **`Select` canónico, NO native `<select>`**, gated by `test-no-native-select.test.ts`):
- **Select "Repetir":** `No se repite` · `Todos los días` · `Cada semana el {día}` · `Cada 2 semanas el {día}` · `Personalizado…`.
- **`Personalizado…` sub-editor:** "Repetir cada [N] semana(s)" (number) + **day chips L M X J V S D (multi-select, a11y keyboard SC-D3F-5)** + "Termina": `Nunca` (open_ended) · `El [fecha]` (end_date) · `Después de [N] repeticiones` (occurrences).
- **Human summary always visible** (RN-D3F-1, shares formatter semantics with BE `format_recurrence_summary` — FE `formatRecurrenceSummary(rule)`): "Se repite cada 2 semanas los lunes y jueves, 8 veces" / "...hasta el 30 jul 2026".
- Maps editor state → `{days_of_week, interval, end_condition_kind, occurrences|end_date}` payload.
- Display (D3-F): `CalendarBlock` shows the short pattern summary (not just "Semanal/Quincenal"). Paint = occurrences from BE (D3-C fix), week + month.
- `staff.types.ts` (EXTEND): `RecurrentBlock` → `daysOfWeek: number[]`, `interval: number` (keep `dayOfWeek`/`freq` optional for legacy reads).
- Depends on T-BE-recurrencia-domain + T-FE-occurrences-consume.

---

## 8. Reconcile — EntitySubNavBar location (drift correction)

The original `03-arch-fe.md` (2026-05-31) declared `EntitySubNavBar` as a brand-local `vitalia/frontend/src/components/shared/shell-organism/EntitySubNavBar.tsx` (D-1). **That is now stale.** Since `vitalia-shell-core-hardening` (lift 3cb9d5a0), `EntitySubNavBar` + `EntityWorkspaceLayout` + `EntityPicker` live in `core/@luana/ui-kit/` and vitalia consumes them via `import { EntityWorkspaceLayout } from "@luana/ui-kit"` (verified: `StaffWorkspaceShell.tsx` L25). The 04-validators `playwright_visual_scope.story_scope_components` reference to `components/shared/shell-organism/EntitySubNavBar.tsx` is corrected in the validators backfill (§ below) to `core/@luana/ui-kit/EntitySubNavBar.tsx (T-CORE only)`.

---

## 9. Integration design (CONN) — delta surfaces

| Surface | Consumed | On-map | Navigable | Notarized |
|---|---|---|---|---|
| Entity picker slot (D3-A) | StaffWorkspaceShell renders it on every `[doctor-id]` route | cap `lisa.doctores` (extend) | already-reachable workspace; picker = identity affordance | wired into `EntityWorkspaceLayout` consumer; core prop registered |
| bio-files endpoints (D3-B) | BioRepoInputs (Página/Perfil) | cap `lisa.doctores` | reachable from doctor workspace | `include_router` already mounted (doctors_router) |
| occurrences endpoint (D3-C) | week + month calendar | cap `lisa.doctores` | Horarios leaf | doctors_router sub-route |
| Página leaf + editor (D3-D) | new 4th leaf in `LEAF_DEFS` | cap `lisa.doctores` | `/lisa/staff/[doctor-id]/pagina` | leaf added to StaffWorkspaceShell `LEAF_DEFS` |
| **Public route `/d/[clinica]/[doctor]`** (D3-D) | **link shared by Adrián / copied by owner** (external lead path) | cap `lisa.doctores` (provides), consumed by `adrian-canal-inbound` (sends) | direct URL (no in-app nav — public) | `app/d/[clinica-slug]/[doctor-slug]/page.tsx` Next route + `include_router(public_doctors_router)` already mounted |
| Month view (D3-E) | Horarios header toggle | cap `lisa.doctores` | Horarios leaf | toggle in DoctorHorariosView |
| Recurrence editor (D3-F) | BloquePopover | cap `lisa.doctores` | Horarios drag-create/edit | BloquePopover already mounted |

No islands: every delta surface has ≥1 real consumer + a reachability path. The public page's reachability is the shared link (Adrián sends per `adrian-canal-inbound`; owner copies) — explicitly NOT in-app nav (it is the public face).

---

## 10. Migrations (idempotent raw SQL, IF NOT EXISTS)

| # | Ticket | DDL |
|---|---|---|
| 040 | T-BE-bio-docs | `CREATE TABLE IF NOT EXISTS vitalia_doctor_bio_files (...)` + 2 indexes |
| 041 | T-BE-pagina-publica | `ALTER TABLE vitalia_doctors ADD COLUMN IF NOT EXISTS public_profile JSONB`, `bio_generated_at TIMESTAMPTZ`, `public_slug TEXT` + unique index + backfill from bio_public |
| 042 | T-BE-recurrencia-domain | `ALTER TABLE vitalia_availability_blocks ADD COLUMN IF NOT EXISTS days_of_week JSONB`, `interval INTEGER` + backfill `days_of_week=[day_of_week]`, `interval = freq='biweekly'?2:1` |

down_revision chain: 039 → 040 → 041 → 042. All `op.execute("...IF NOT EXISTS...")`. NO `op.create_table`/`sa.Enum`. Prod-clone test per `backend-migrations.md`. **041 + 042 are additive (nullable cols + backfill); legacy rows keep working (compat RN-D3F-3, RN-D3D backfill).**

## 10.5 Default-flip audit
- [x] **No aplica** — this delta flips NO feature flag side-effect path. All changes are additive endpoints/columns/components. (No `USE_*_PATTERN_*` / `ENABLE_*` toggled.)

---

## 11. Cross-cutting

- **Tenant isolation:** every clinics query dual-filter `tenant_id + clinic_id` (incl bio_files `get_by_id`). Public route resolves tenant from slug (no header) — allow-list serializer is the leak boundary.
- **PHI / public page:** `PublicDoctorProfileDTO` is allow-list (new arch test asserts zero PHI fields). Slug-fuzzing cross-tenant → generic 404 (SC-D3D-6). Doctor profile is staff data (not patient PHI), but audit on staff surface per ADR-004 (bio-file add/delete/download audited).
- **Master data:** all timestamps `DateTime(timezone=True)` UTC; calendar display via existing `Intl es-419` helper (master-data.md). Occurrence dates computed UTC then displayed tenant-tz (existing pattern).
- **Spanish neutro LatAm:** all new UI strings + Select labels + summaries (tuteo, no voseo). `test_no_voseo_in_copy.test.ts` covers.
- **Native-first:** lint/tests native host (`${WS}/.venv/bin/pytest`, `npx vitest`). NO docker exec.
- **APP_BASE_URL:** env var both FE (`NEXT_PUBLIC_APP_BASE_URL`) + BE (`APP_BASE_URL`); NEVER hardcoded.

---

## 12. Architecture fitness impact
- Keep green: phi_dual_filter, response_model_required, migrations_idempotent, clinics_domain_no_engine_imports, public_doctors_allowlist (EXTEND for profile DTO), no-div-layout, no-native-select (D3-F Select), ribbon-no-shadcn-tabs, fsd_boundaries.
- NEW arch test: `test_public_doctor_profile_allowlist.py` (V-ARCH-D-1) — structured public profile DTO has zero PHI fields.
- `@luana/ui-kit` back-compat ratchet: EntitySubNavBar/EntityWorkspaceLayout existing tests must stay green (optional prop = no regression for adrian/ICPs consumers).

## 13. capability YAML + modules updates (post-merge, Fase F.3)
- `vitalia/docs/product/capabilities/clinics/lisa-doctores.yaml` (cap `lisa.doctores`, `extend`): add scenarios SC-D3A/B/C/D/E/F + `dev_preview.main_component` pointers (Página leaf, public route) + business_rules RN-D3A..F + access (public route = unauthenticated read).
- `vitalia/docs/product/modules/clinics.md` if narrative changes (public doctor page is a new user-facing surface).
- `core/@luana/ui-kit` proposal `2026-06-12-lift-entitysubnavbar-picker-slot.md` accepted → note in change_log.

## 14. Open questions for PM
- **OQ-1 (lift):** T-CORE-picker-slot edits `core/@luana/ui-kit` (additive prop). Promotion proposal redacted as deliverable — **merge requires /pm-luana lift acceptance**. Confirm /pm-luana reviews before the brand wire (T-FE-switcher-wire) merges.
- **OQ-2 (public route auth):** `/d/[clinica]/[doctor]` is unauthenticated. Confirm the Clerk middleware matcher EXCLUDES `/d/**` (public path) — else login wall blocks the public page. (Builder must update `middleware.ts` matcher.)
- **OQ-3 (clinica-slug source):** public URL uses `{clinica-slug}`. Confirm the tenant/clinic slug already exists (the existing public endpoint uses `{tenant_slug}`). If clinic-level slug differs from tenant_slug, the route key must match BE resolution.

## 15. Research notes
- No novel patterns. All deltas reuse shipped, in-tree mechanisms (EntityPicker core component, `dateutil.rrule` byweekday+interval native, assets R2 proxy, Next public routes, allow-list serializer). Model = Fable 5; knowledge of these is in-repo (verified by reading the real files), not knowledge-cutoff-dependent. No WebSearch required.

## 16. OQ resolutions (/pm-vitalia + /pm-luana hats · 2026-06-12 · mandato autónomo Chris)

- **OQ-1 RESUELTA:** promotion proposal escrita y **accepted** → `docs/promotion-protocol/proposals/2026-06-12-ui-kit-entity-subnavbar-picker-slot.md` (base: ratificación verbal Chris 2026-06-11 "Genérico en @luana/ui-kit"). T-CORE-picker-slot desbloqueado — aditivo opt-in, chip estático = fallback, consumers existentes intactos.
- **OQ-2 RESUELTA:** SÍ — el matcher del middleware Clerk EXCLUYE `/d/**` (ruta pública). Deliverable de T-FE-pagina-publica: actualizar matcher + e2e SC-D3D-1 verifica acceso sin auth.
- **OQ-3 RESUELTA:** `clinics.slug` EXISTE (`clinic_model.py:39`, unique per tenant — ej. "aurora-dental-ar"). Resolución pública por clinic-slug SIN tenant header. ⚠️ Colisión cross-tenant teóricamente posible (unique es per-tenant): guard → si lookup matchea >1 clínica, responder "perfil no disponible" genérico (RN-D3D-9 anti-enumeración) + structlog warning; y la creación de clínicas NUEVAS valida unicidad global del slug en adelante (validación service-level, sin migración de constraint — no romper data existente).
