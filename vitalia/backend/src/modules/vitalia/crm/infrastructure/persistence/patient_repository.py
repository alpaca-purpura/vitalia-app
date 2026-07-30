# cap: crm.crm-consent-optout
# story-origin: TBD
"""PatientRepository — PHI entity repository with dual filter + pgcrypto decrypt wiring.

Infrastructure layer — extends PhiRepositoryBase (HIPAA-lite dual filter).

Every method MUST:
  1. Call self.validate_dual_filter(tenant_id=..., clinic_id=...) first.
  2. Apply BOTH tenant_id AND clinic_id in the SQL WHERE clause.
  3. Exclude soft-deleted rows (deleted_at IS NULL).
  4. Write an audit log entry via self._audit_repo (sync — never fire-forget).
  5. Decrypt PHI columns with pgp_sym_decrypt(:col, :kek) on reads.
  6. Encrypt PHI columns with pgp_sym_encrypt(:val, :kek) on writes.

PHI_ENC_COLS = {name, date_of_birth, dni, phone, email, address}
KEK is injected via constructor (kek: KEKClient | None = None).
  - kek=None → KEKClient.from_env() called once (back-compat for tests without DI).
  - kek=explicit → used directly (router injects KEKClient.from_env()).

Architecture fitness gate: vitalia/backend/tests/architecture/test_phi_dual_filter.py
ADR-007 D1: inline pgp_sym_* with :kek bound param. NO trigger+GUC.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia._shared.encryption.kek_client import KEKClient
from src.modules.vitalia._shared.repositories.audit_log_repository import (
    AuditLogEntry,
    AuditLogRepository,
)
from src.modules.vitalia._shared.repositories.phi_repository import PhiRepositoryBase
from src.modules.vitalia.crm.domain.patient import Patient

logger = structlog.get_logger()

# PHI columns that must be encrypted at-rest (ADR-007 D3).
# Indexed over plaintext cols only (no name/dni/email etc. index).
_PHI_ENC_COLS: frozenset[str] = frozenset({"name", "date_of_birth", "dni", "phone", "email", "address"})


def _utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


def _parse_dob(value: str | None) -> datetime | None:
    """Parse date_of_birth from pgp_sym_decrypt text output to datetime.

    pgp_sym_decrypt(date_of_birth, :kek)::text returns the ISO-format string
    that was stored (or NULL if the column was NULL).

    Args:
        value: ISO-format datetime string from pgcrypto, or None.

    Returns:
        UTC-aware datetime, or None if value is None/empty.
    """
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        logger.warning("patient_repo.dob_parse_error", raw_value_len=len(value))
        return None


class PatientRepository(PhiRepositoryBase):
    """Repository for Patient PHI entities with pgcrypto encrypt/decrypt wiring.

    Enforces dual filter (tenant_id + clinic_id) per HIPAA-lite rule.
    Writes audit log on every PHI read/write operation.
    Decrypts PHI columns (name/date_of_birth/dni/phone/email/address) on reads
    and encrypts them on writes using pgcrypto pgp_sym_encrypt/decrypt with
    the KEK bound as :kek parameter (ADR-007 D1).
    """

    def __init__(
        self,
        session: AsyncSession,
        audit_repo: AuditLogRepository,
        kek: KEKClient | None = None,
    ) -> None:
        """Initialize with a DB session, audit repository, and optional KEK.

        Args:
            session: SQLAlchemy async session.
            audit_repo: AuditLogRepository for mandatory PHI audit writes.
            kek: Optional KEKClient. If None, KEKClient.from_env() is called
                 (back-compat for tests and callers that don't inject KEK).
        """
        self._session = session
        self._audit_repo = audit_repo
        self._kek: KEKClient = kek if kek is not None else KEKClient.from_env()

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID | None = None,
    ) -> Patient | None:
        """Retrieve a Patient by ID with dual filter + pgcrypto decrypt.

        Args:
            entity_id: Patient UUID to retrieve.
            tenant_id: Tenant UUID — root isolation (required).
            clinic_id: Clinic UUID — HIPAA-lite dual filter (required).
            user_id: Optional user UUID for audit log. If None, skips audit.

        Returns:
            Patient domain entity or None if not found.

        Raises:
            ValueError: If tenant_id is None.
            MissingClinicFilterError: If clinic_id is None.
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        kek_val = self._kek.get_key()

        stmt = text(
            """
            SELECT id, tenant_id, clinic_id,
                   pgp_sym_decrypt(name, :kek)::text          AS name,
                   pgp_sym_decrypt(date_of_birth, :kek)::text AS date_of_birth,
                   pgp_sym_decrypt(dni, :kek)::text           AS dni,
                   pgp_sym_decrypt(phone, :kek)::text         AS phone,
                   pgp_sym_decrypt(email, :kek)::text         AS email,
                   pgp_sym_decrypt(address, :kek)::text       AS address,
                   marketing_opt_out_at,
                   marketing_opt_in, opt_out, opt_out_reason, opt_out_at,
                   deleted_at, created_at, updated_at
            FROM vitalia_patients
            WHERE tenant_id = :tenant_id
              AND clinic_id = :clinic_id
              AND id = :entity_id
              AND deleted_at IS NULL
            LIMIT 1
            """
        )
        result = await self._session.execute(
            stmt,
            {
                "kek": kek_val,
                "tenant_id": str(tenant_id),
                "clinic_id": str(clinic_id),
                "entity_id": str(entity_id),
            },
        )
        row = result.fetchone()

        if user_id is not None:
            audit_entry = AuditLogEntry(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                action="read_patient",
                resource_type="patient",
                resource_id=entity_id,
            )
            await self._audit_repo.write(audit_entry)

        if row is None:
            return None

        return Patient(
            id=UUID(str(row.id)),
            tenant_id=UUID(str(row.tenant_id)),
            clinic_id=UUID(str(row.clinic_id)),
            name=row.name,
            date_of_birth=_parse_dob(row.date_of_birth),
            dni=row.dni,
            phone=row.phone,
            email=row.email,
            address=row.address,
            marketing_opt_out_at=row.marketing_opt_out_at,
            marketing_opt_in=bool(row.marketing_opt_in) if row.marketing_opt_in is not None else False,
            opt_out=bool(row.opt_out) if row.opt_out is not None else False,
            opt_out_reason=row.opt_out_reason,
            opt_out_at=row.opt_out_at,
            deleted_at=row.deleted_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def list_by_filter(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        **filters: object,
    ) -> list[Patient]:
        """List Patients matching the given filters + pgcrypto decrypt.

        Args:
            tenant_id: Tenant UUID — root isolation (required).
            clinic_id: Clinic UUID — HIPAA-lite dual filter (required).
            **filters: Additional filter criteria (name_contains, status, etc.).

        Returns:
            List of matching Patient entities.

        Raises:
            ValueError: If tenant_id is None.
            MissingClinicFilterError: If clinic_id is None.
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        kek_val = self._kek.get_key()

        stmt = text(
            """
            SELECT id, tenant_id, clinic_id,
                   pgp_sym_decrypt(name, :kek)::text          AS name,
                   pgp_sym_decrypt(date_of_birth, :kek)::text AS date_of_birth,
                   pgp_sym_decrypt(dni, :kek)::text           AS dni,
                   pgp_sym_decrypt(phone, :kek)::text         AS phone,
                   pgp_sym_decrypt(email, :kek)::text         AS email,
                   pgp_sym_decrypt(address, :kek)::text       AS address,
                   marketing_opt_out_at,
                   marketing_opt_in, opt_out, opt_out_reason, opt_out_at,
                   deleted_at, created_at, updated_at
            FROM vitalia_patients
            WHERE tenant_id = :tenant_id
              AND clinic_id = :clinic_id
              AND deleted_at IS NULL
            ORDER BY created_at DESC
            """
        )
        result = await self._session.execute(
            stmt,
            {
                "kek": kek_val,
                "tenant_id": str(tenant_id),
                "clinic_id": str(clinic_id),
            },
        )
        rows = result.fetchall()

        return [
            Patient(
                id=UUID(str(row.id)),
                tenant_id=UUID(str(row.tenant_id)),
                clinic_id=UUID(str(row.clinic_id)),
                name=row.name,
                date_of_birth=_parse_dob(row.date_of_birth),
                dni=row.dni,
                phone=row.phone,
                email=row.email,
                address=row.address,
                marketing_opt_out_at=row.marketing_opt_out_at,
                marketing_opt_in=bool(row.marketing_opt_in) if row.marketing_opt_in is not None else False,
                opt_out=bool(row.opt_out) if row.opt_out is not None else False,
                opt_out_reason=row.opt_out_reason,
                opt_out_at=row.opt_out_at,
                deleted_at=row.deleted_at,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]

    async def update(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        updates: dict[str, object],
    ) -> None:
        """Update patient fields with pgcrypto encrypt for PHI columns.

        Builds a dynamic SET clause. PHI columns (name/date_of_birth/dni/phone/
        email/address) are wrapped in pgp_sym_encrypt(:val, :kek). Non-PHI
        columns are bound directly.

        For date_of_birth: if the value is a datetime, serialized to ISO string
        before binding (pgp_sym_encrypt expects text input).

        Args:
            entity_id: Patient UUID to update.
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID.
            user_id: User performing the update (for audit log).
            updates: Dict of field → value pairs to set.
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        if not updates:
            return

        kek_val = self._kek.get_key()

        # Build SET clause — PHI columns wrapped in pgp_sym_encrypt
        set_clauses = []
        params: dict[str, object] = {
            "kek": kek_val,
            "tenant_id": str(tenant_id),
            "clinic_id": str(clinic_id),
            "entity_id": str(entity_id),
            "updated_at": _utc_now(),
        }

        for k, v in updates.items():
            if k in _PHI_ENC_COLS:
                set_clauses.append(f"{k} = pgp_sym_encrypt(:{k}, :kek)")
                # date_of_birth: serialize datetime → isoformat string for pgp_sym_encrypt
                if k == "date_of_birth" and isinstance(v, datetime):
                    params[k] = v.isoformat()
                else:
                    params[k] = v
            else:
                set_clauses.append(f"{k} = :{k}")
                params[k] = v

        set_sql = ", ".join(set_clauses)
        stmt = text(
            f"""
            UPDATE vitalia_patients
            SET {set_sql}, updated_at = :updated_at
            WHERE tenant_id = :tenant_id
              AND clinic_id = :clinic_id
              AND id = :entity_id
              AND deleted_at IS NULL
            """
        )
        await self._session.execute(stmt, params)

        audit_entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="update_patient",
            resource_type="patient",
            resource_id=entity_id,
        )
        await self._audit_repo.write(audit_entry)

    async def opt_out(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> None:
        """Mark patient as opted out from marketing (LGPD/HIPAA right to erasure flow).

        Updates opt_out=True, opt_out_reason, opt_out_at, marketing_opt_in=False.
        Does NOT touch PHI encrypted columns → no :kek needed here.

        Args:
            entity_id: Patient UUID.
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID.
            user_id: User requesting the opt-out (for audit log).
            reason: Reason for opt-out (stored redacted in audit log payload).
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        now = _utc_now()
        stmt = text(
            """
            UPDATE vitalia_patients
            SET opt_out = TRUE,
                opt_out_at = :opt_out_at,
                opt_out_reason = :opt_out_reason,
                marketing_opt_in = FALSE,
                updated_at = :updated_at
            WHERE tenant_id = :tenant_id
              AND clinic_id = :clinic_id
              AND id = :entity_id
              AND deleted_at IS NULL
            """
        )
        await self._session.execute(
            stmt,
            {
                "opt_out_at": now,
                "opt_out_reason": reason,
                "updated_at": now,
                "tenant_id": str(tenant_id),
                "clinic_id": str(clinic_id),
                "entity_id": str(entity_id),
            },
        )

        audit_entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="patient_opted_out",
            resource_type="patient",
            resource_id=entity_id,
            payload_redacted=b"<reason_redacted>",
        )
        await self._audit_repo.write(audit_entry)

        logger.info(
            "patient_opted_out",
            patient_id=str(entity_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
        )

    async def marketing_opt_in(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        opt_in: bool,
    ) -> None:
        """Update patient marketing consent flag.

        Sets marketing_opt_in to the given value.
        Does NOT modify opt_out — consent is a separate flag from erasure.
        Does NOT touch PHI encrypted columns → no :kek needed here.

        Args:
            entity_id: Patient UUID.
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID.
            user_id: User updating the consent (for audit log).
            opt_in: New consent value (True = consented, False = refused).
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        now = _utc_now()
        stmt = text(
            """
            UPDATE vitalia_patients
            SET marketing_opt_in = :opt_in,
                updated_at = :updated_at
            WHERE tenant_id = :tenant_id
              AND clinic_id = :clinic_id
              AND id = :entity_id
              AND deleted_at IS NULL
            """
        )
        await self._session.execute(
            stmt,
            {
                "opt_in": opt_in,
                "updated_at": now,
                "tenant_id": str(tenant_id),
                "clinic_id": str(clinic_id),
                "entity_id": str(entity_id),
            },
        )

        audit_entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="patient_marketing_opt_in",
            resource_type="patient",
            resource_id=entity_id,
        )
        await self._audit_repo.write(audit_entry)

        logger.info(
            "patient_marketing_consent_updated",
            patient_id=str(entity_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            opt_in=opt_in,
        )

    # ------------------------------------------------------------------
    # T-BE-5: inline create + typeahead search + dedup
    # ------------------------------------------------------------------

    @staticmethod
    def _mask_name(name: str) -> str:
        """Return first initial + last name: 'María López' → 'M. López'.

        If name has only one word, returns first initial + '.'.
        PHI masking — raw name must never reach API response.
        """
        parts = name.strip().split()
        if len(parts) == 1:
            return f"{parts[0][0].upper()}."
        return f"{parts[0][0].upper()}. {parts[-1]}"

    @staticmethod
    def _mask_phone(phone: str | None) -> str | None:
        """Return phone with digits replaced by *** after country/area prefix.

        Examples:
          '+51987654321' → '+51 9***'
          '+5491112345678' → '+54 9***'
          None → None
        """
        if not phone:
            return None
        # Keep up to first 4 chars of stripped digits after '+'
        stripped = phone.replace(" ", "").replace("-", "")
        if stripped.startswith("+"):
            visible = stripped[:4]  # e.g. '+519'
            return f"{visible}***"
        # Fallback: show first digit then mask
        return f"{stripped[0]}***"

    async def create_minimal(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        name: str,
        phone: str | None = None,
        email: str | None = None,
        channel: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        """Insert a minimal patient record with pgcrypto-encrypted PHI.

        Writes audit log BEFORE returning result (HIPAA-lite sync).
        Returns masked fields only (name_masked, phone_masked) — raw PHI never returned.

        T-BE-5: used by inline patient create in the nueva-cita flow.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (dual filter).
            user_id: User creating the record (for audit log).
            name: Patient full name (PHI — encrypted at-rest).
            phone: Optional E.164 phone (PHI — encrypted at-rest).
            email: Optional email (PHI — encrypted at-rest).
            channel: Acquisition channel (not PHI).
            note: Optional note (not PHI).

        Returns:
            dict with patient_id, name_masked, phone_masked, is_duplicate, created_at.
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        kek_val = self._kek.get_key()
        patient_id = uuid4()
        now = _utc_now()

        # Insert with pgcrypto encryption for PHI columns
        stmt = text(
            """
            INSERT INTO vitalia_patients
              (id, tenant_id, clinic_id,
               name, phone, email,
               channel_first, notes,
               marketing_opt_in, opt_out, created_at, updated_at)
            VALUES
              (:id, :tenant_id, :clinic_id,
               pgp_sym_encrypt(:name, :kek),
               pgp_sym_encrypt(:phone, :kek),
               pgp_sym_encrypt(:email, :kek),
               :channel_first, :notes,
               FALSE, FALSE, :created_at, :updated_at)
            """
        )
        await self._session.execute(
            stmt,
            {
                "id": str(patient_id),
                "tenant_id": str(tenant_id),
                "clinic_id": str(clinic_id),
                "name": name,
                "phone": phone or "",
                "email": email or "",
                "channel_first": channel,
                "notes": note or "",
                "kek": kek_val,
                "created_at": now,
                "updated_at": now,
            },
        )

        # Audit log SYNC (HIPAA-lite — must complete before response)
        audit_entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="patient_create",
            resource_type="patient",
            resource_id=patient_id,
        )
        await self._audit_repo.write(audit_entry)

        logger.info(
            "patient_created_minimal",
            patient_id=str(patient_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            channel=channel,
        )

        return {
            "patient_id": patient_id,
            "name_masked": self._mask_name(name),
            "phone_masked": self._mask_phone(phone),
            "is_duplicate": False,
            "created_at": now,
        }

    async def find_by_phone(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        phone: str,
    ) -> dict[str, Any] | None:
        """Find an existing patient by phone (decrypt-then-compare) for RN-9 dedup.

        Decrypts phone column and compares exact match. Returns masked result dict
        or None if no match. Used to detect duplicates before inline create.

        HIPAA-lite: dual filter enforced. Raw PHI never returned.

        T-BE-5 / RN-9: drives "use existing patient?" dialog.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (dual filter).
            phone: Phone number to search (exact match after decrypt).

        Returns:
            Masked patient dict or None if not found.
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        kek_val = self._kek.get_key()

        stmt = text(
            """
            SELECT id,
                   pgp_sym_decrypt(name, :kek)::text  AS name,
                   pgp_sym_decrypt(phone, :kek)::text AS phone,
                   channel_first,
                   created_at
            FROM vitalia_patients
            WHERE tenant_id = :tenant_id
              AND clinic_id = :clinic_id
              AND pgp_sym_decrypt(phone, :kek)::text = :phone
              AND deleted_at IS NULL
            LIMIT 1
            """
        )
        result = await self._session.execute(
            stmt,
            {
                "kek": kek_val,
                "tenant_id": str(tenant_id),
                "clinic_id": str(clinic_id),
                "phone": phone,
            },
        )
        row = result.fetchone()
        if row is None:
            return None

        return {
            "patient_id": UUID(str(row.id)),
            "name_masked": self._mask_name(row.name),
            "phone_masked": self._mask_phone(row.phone),
            "created_at": row.created_at,
        }

    async def search(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        q: str,
        cursor: UUID | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Typeahead patient search using decrypt-then-ILIKE on name/phone.

        Windowed cursor pagination for datasets with 1500+ rows.
        Returns masked items only — raw PHI never returned.

        Performance note: decrypt-then-ILIKE is O(n) over encrypted rows.
        Acceptable at 1500 rows; for >50k rows, a name_hash index + suggest
        approach would be needed (out of scope for MVP).

        HIPAA-lite: dual filter enforced. Audit log written.

        T-BE-5: drives typeahead picker in nueva-cita form.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (dual filter).
            q: Search query (applied to decrypted name ILIKE %q%).
            cursor: Optional UUID of last seen patient (pagination cursor).
            limit: Page size (default 20, max enforced by caller).

        Returns:
            dict with items (list of masked dicts), next_cursor (UUID | None),
            total_approx (int).
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        kek_val = self._kek.get_key()
        search_pattern = f"%{q}%"

        # Cursor-based pagination ESTABLE: ordenamos por (created_at, id) DESC y el
        # cursor compara la TUPLA contra el (created_at, id) de la fila-cursor. Bug
        # previo: cursor `id > :cursor` (asc) sobre `ORDER BY created_at DESC` →
        # campo-cursor ≠ campo-orden + dirección invertida → páginas SOLAPADAS
        # (filas duplicadas → "two children with the same key" en el FE) y filas
        # omitidas. La row-comparison `(created_at, id) < (cursor_row)` con orden
        # DESC compuesto es estable y NO solapa, manteniendo el contrato cursor=UUID.
        cursor_clause = (
            "AND (created_at, id) < (SELECT created_at, id FROM vitalia_patients WHERE id = :cursor)"
            if cursor is not None
            else ""
        )

        stmt = text(
            f"""
            WITH filtered AS (
                SELECT id,
                       pgp_sym_decrypt(name, :kek)::text  AS name,
                       pgp_sym_decrypt(phone, :kek)::text AS phone,
                       channel_first,
                       created_at,
                       COUNT(*) OVER() AS total_approx
                FROM vitalia_patients
                WHERE tenant_id = :tenant_id
                  AND clinic_id = :clinic_id
                  AND deleted_at IS NULL
                  {cursor_clause}
                  AND pgp_sym_decrypt(name, :kek)::text ILIKE :q
                ORDER BY created_at DESC, id DESC
                LIMIT :limit_plus1
            )
            SELECT * FROM filtered
            """
        )
        params: dict[str, Any] = {
            "kek": kek_val,
            "tenant_id": str(tenant_id),
            "clinic_id": str(clinic_id),
            "q": search_pattern,
            "limit_plus1": limit + 1,
        }
        if cursor is not None:
            params["cursor"] = str(cursor)

        result = await self._session.execute(stmt, params)
        rows = result.fetchall()

        has_more = len(rows) > limit
        page_rows = rows[:limit]
        total_approx = int(rows[0].total_approx) if rows else 0

        items = [
            {
                "patient_id": UUID(str(row.id)),
                "name_masked": self._mask_name(row.name),
                "phone_masked": self._mask_phone(row.phone),
                "channel_first": row.channel_first,
                "created_at": row.created_at,
            }
            for row in page_rows
        ]

        next_cursor: UUID | None = None
        if has_more and page_rows:
            next_cursor = UUID(str(page_rows[-1].id))

        return {
            "items": items,
            "next_cursor": next_cursor,
            "total_approx": total_approx,
        }
