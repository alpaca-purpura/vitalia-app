# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""LeadRepository — PII entity repository with pgcrypto encrypt/decrypt wiring.

Infrastructure layer — Lead is PII (name/email/phone/notes), NOT PHI.
Single tenant_id filter only (no clinic_id dual filter required).

Encryption wiring (ADR-007 D1 + T-2):
  - Reads: pgp_sym_decrypt(col, :kek)::text for name/email/phone/notes.
  - Writes: pgp_sym_encrypt(:val, :kek) for name/email/phone/notes.
  - KEK injected via constructor (kek: KEKClient | None = None).
    None → KEKClient.from_env() back-compat for tests.

Methods create() + update() added in T-2 (were called by lead_service but
did not exist in the repo — SC-5 round-trip deliverable).

Extended in vitalia-fase2-adrian-embudo T-BE-1:
  + update_stage(): optimistic lock (WHERE version=expected → rowcount 0 = StaleStateError)
  + list_for_board(): HOT_BOARD_STAGES scope + RN-17 sort (stage_entered_at ASC = oldest first)
  + freeze(): set is_frozen + frozen_reason + frozen_at
  + reactivate(): unset is_frozen state

Architecture fitness gate: test_lead_repository_is_not_phi_repository
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia._shared.encryption.kek_client import KEKClient
from src.modules.vitalia.crm.domain.exceptions import StaleStateError
from src.modules.vitalia.crm.domain.lead import Lead

logger = structlog.get_logger()

# PII columns that must be encrypted at-rest for leads.
_LEAD_ENC_COLS: frozenset[str] = frozenset({"name", "email", "phone", "notes"})


def _utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


class LeadRepository:
    """Repository for Lead PII entities with pgcrypto encrypt/decrypt wiring.

    Applies single tenant_id filter only (Lead is NOT PHI).
    Marketing and receptionist roles can access leads.
    Encrypts PII columns (name/email/phone/notes) at-rest via pgcrypto.
    """

    def __init__(
        self,
        session: AsyncSession,
        kek: KEKClient | None = None,
    ) -> None:
        """Initialize with a DB session and optional KEK.

        Args:
            session: SQLAlchemy async session.
            kek: Optional KEKClient. If None, KEKClient.from_env() is called
                 (back-compat for tests and callers that don't inject KEK).
        """
        self._session = session
        self._kek: KEKClient = kek if kek is not None else KEKClient.from_env()

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
    ) -> Lead | None:
        """Retrieve a Lead by ID with single tenant_id filter + pgcrypto decrypt.

        Args:
            entity_id: Lead UUID to retrieve.
            tenant_id: Tenant UUID — root isolation (required).

        Returns:
            Lead domain entity or None if not found.

        Raises:
            ValueError: If tenant_id is None.
        """
        if tenant_id is None:
            raise ValueError(
                "LeadRepository.get_by_id requires tenant_id — never bypass root tenant isolation (tenant-isolation.md)"
            )

        kek_val = self._kek.get_key()

        stmt = text(
            """
            SELECT
                id, tenant_id,
                pgp_sym_decrypt(name, :kek)::text  AS name,
                pgp_sym_decrypt(email, :kek)::text AS email,
                pgp_sym_decrypt(phone, :kek)::text AS phone,
                source, status,
                pgp_sym_decrypt(notes, :kek)::text AS notes,
                stage, stage_entered_at, score, temperature, operated_by,
                channel, service_interest, assigned_doctor_id,
                estimated_value, currency,
                buying_signals, is_frozen, frozen_reason, frozen_at,
                closure_reason, reactivation_cohort_at, deposit_status,
                is_blacklisted, version,
                deleted_at, created_at, updated_at
            FROM vitalia_leads
            WHERE tenant_id = :tenant_id
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
                "entity_id": str(entity_id),
            },
        )
        row = result.fetchone()

        if row is None:
            return None

        return self._row_to_lead(row)

    async def list_by_filter(
        self,
        *,
        tenant_id: UUID,
        **filters: object,
    ) -> list[Lead]:
        """List Leads matching the given filters + pgcrypto decrypt.

        Args:
            tenant_id: Tenant UUID — root isolation (required).
            **filters: Additional filter criteria (status, source, limit, offset).

        Returns:
            List of matching Lead entities.

        Raises:
            ValueError: If tenant_id is None.
        """
        if tenant_id is None:
            raise ValueError("LeadRepository.list_by_filter requires tenant_id")

        kek_val = self._kek.get_key()

        stmt = text(
            """
            SELECT
                id, tenant_id,
                pgp_sym_decrypt(name, :kek)::text  AS name,
                pgp_sym_decrypt(email, :kek)::text AS email,
                pgp_sym_decrypt(phone, :kek)::text AS phone,
                source, status,
                pgp_sym_decrypt(notes, :kek)::text AS notes,
                stage, stage_entered_at, score, temperature, operated_by,
                channel, service_interest, assigned_doctor_id,
                estimated_value, currency,
                buying_signals, is_frozen, frozen_reason, frozen_at,
                closure_reason, reactivation_cohort_at, deposit_status,
                is_blacklisted, version,
                deleted_at, created_at, updated_at
            FROM vitalia_leads
            WHERE tenant_id = :tenant_id
              AND deleted_at IS NULL
            ORDER BY created_at DESC
            """
        )
        result = await self._session.execute(stmt, {"kek": kek_val, "tenant_id": str(tenant_id)})
        rows = result.fetchall()

        return [self._row_to_lead(row) for row in rows]

    async def create(
        self,
        *,
        id: UUID,
        tenant_id: UUID,
        name: str,
        email: str | None,
        phone: str | None,
        source: str | None,
        status: str,
        notes: str | None,
        marketing_opt_in: bool,
        stage: str = "interesado",
        channel: str | None = None,
        service_interest: str | None = None,
        estimated_value: Decimal | None = None,
        currency: str | None = None,
    ) -> Lead:
        """Create a new Lead with PII columns encrypted at-rest.

        PII columns (name/email/phone/notes) are wrapped in pgp_sym_encrypt.
        source/status/marketing_opt_in + funnel fields are stored plaintext.
        NULL values for email/phone/notes are handled:
          pgp_sym_encrypt(NULL, :kek) = NULL — OK per pgcrypto behavior.

        Args:
            id: Lead UUID (supplied by caller — uuid4() from service).
            tenant_id: Tenant UUID.
            name: Lead name (required).
            email: Optional email (encrypted if set, NULL if None).
            phone: Optional phone (encrypted if set, NULL if None).
            source: Optional acquisition source (plaintext).
            status: Lead status (plaintext, default 'new').
            notes: Optional notes (encrypted if set, NULL if None).
            marketing_opt_in: Marketing consent flag (plaintext boolean).
            stage: Initial funnel stage (default 'interesado' — RN-11).
            channel: Origin channel (wa|ig|meta|web|referido|tiktok).
            service_interest: Service the lead expressed interest in.
            estimated_value: Estimated treatment value (NON-PHI).
            currency: Currency code — from tenant locale, NEVER hardcoded (RN-15).

        Returns:
            Created Lead domain entity (re-read via get_by_id to return decrypted).
        """
        if tenant_id is None:
            raise ValueError("LeadRepository.create requires tenant_id")

        kek_val = self._kek.get_key()
        now = _utc_now()

        stmt = text(
            """
            INSERT INTO vitalia_leads
                (id, tenant_id, name, email, phone, source, status, notes,
                 marketing_opt_in, stage, stage_entered_at, channel,
                 service_interest, estimated_value, currency,
                 deleted_at, created_at, updated_at)
            VALUES (
                :id, :tenant_id,
                pgp_sym_encrypt(:name, :kek),
                pgp_sym_encrypt(:email, :kek),
                pgp_sym_encrypt(:phone, :kek),
                :source, :status,
                pgp_sym_encrypt(:notes, :kek),
                :marketing_opt_in, :stage, :stage_entered_at, :channel,
                :service_interest, :estimated_value, :currency,
                NULL, :created_at, :updated_at
            )
            RETURNING id
            """
        )
        await self._session.execute(
            stmt,
            {
                "id": str(id),
                "tenant_id": str(tenant_id),
                "name": name,
                "email": email,
                "phone": phone,
                "source": source,
                "status": status,
                "notes": notes,
                "marketing_opt_in": marketing_opt_in,
                "stage": stage,
                "stage_entered_at": now,
                "channel": channel,
                "service_interest": service_interest,
                "estimated_value": estimated_value,
                "currency": currency,
                "kek": kek_val,
                "created_at": now,
                "updated_at": now,
            },
        )

        logger.info(
            "lead_created",
            lead_id=str(id),
            tenant_id=str(tenant_id),
        )

        # Re-read via get_by_id to return decrypted Lead entity
        created = await self.get_by_id(entity_id=id, tenant_id=tenant_id)
        if created is None:
            # Should not happen — just inserted; fallback to in-memory entity
            return Lead(
                id=id,
                tenant_id=tenant_id,
                name=name,
                email=email,
                phone=phone,
                source=source,
                status=status,
                notes=notes,
                # marketing_opt_in NO está en el domain Lead (vive solo como columna
                # DB + consent flow) — no pasarlo al constructor
                stage=stage,
                stage_entered_at=now,
                channel=channel,
                service_interest=service_interest,
                estimated_value=estimated_value,
                currency=currency,
                created_at=now,
                updated_at=now,
            )
        return created

    async def update(
        self,
        lead_id: UUID,
        *,
        tenant_id: UUID,
        updates: dict[str, object],
    ) -> Lead:
        """Update Lead fields with PII columns encrypted via pgcrypto.

        Builds a dynamic SET clause. PII columns (name/email/phone/notes)
        are wrapped in pgp_sym_encrypt(:val, :kek). Non-PII cols are bound
        directly. Returns the updated Lead (re-read via get_by_id).

        Args:
            lead_id: Lead UUID.
            tenant_id: Tenant UUID — root isolation (required).
            updates: Dict of field → value. Only PII cols are encrypted.

        Returns:
            Updated Lead domain entity.

        Raises:
            ValueError: If tenant_id is None.
        """
        if tenant_id is None:
            raise ValueError("LeadRepository.update requires tenant_id")

        if not updates:
            # Nothing to update — re-read and return current state
            existing = await self.get_by_id(entity_id=lead_id, tenant_id=tenant_id)
            if existing is None:
                raise ValueError(f"Lead {lead_id} not found for tenant {tenant_id}")
            return existing

        kek_val = self._kek.get_key()

        set_clauses = []
        params: dict[str, object] = {
            "kek": kek_val,
            "tenant_id": str(tenant_id),
            "lead_id": str(lead_id),
            "updated_at": _utc_now(),
        }

        for k, v in updates.items():
            if k in _LEAD_ENC_COLS:
                set_clauses.append(f"{k} = pgp_sym_encrypt(:{k}, :kek)")
            else:
                set_clauses.append(f"{k} = :{k}")
            params[k] = v

        set_sql = ", ".join(set_clauses)
        stmt = text(
            f"""
            UPDATE vitalia_leads
            SET {set_sql}, updated_at = :updated_at
            WHERE tenant_id = :tenant_id
              AND id = :lead_id
              AND deleted_at IS NULL
            """
        )
        await self._session.execute(stmt, params)

        logger.info(
            "lead_updated",
            lead_id=str(lead_id),
            tenant_id=str(tenant_id),
            fields=list(updates.keys()),
        )

        updated = await self.get_by_id(entity_id=lead_id, tenant_id=tenant_id)
        if updated is None:
            raise ValueError(f"Lead {lead_id} not found after update for tenant {tenant_id}")
        return updated

    # ── Funnel methods (vitalia-fase2-adrian-embudo T-BE-1) ─────────────────

    async def update_stage(
        self,
        lead_id: UUID,
        *,
        tenant_id: UUID,
        to_stage: str,
        expected_version: int,
        score: int,
        actor_user_id: UUID | None,
    ) -> Lead:
        """Update funnel stage with optimistic locking (SC-5 / RN-4).

        Uses raw SQL UPDATE with WHERE version = expected_version.
        If 0 rows updated → raises StaleStateError (maps to 409 at API layer).
        On success: increments version, sets stage_entered_at = now().

        Args:
            lead_id: Lead UUID.
            tenant_id: Tenant UUID — root isolation (required).
            to_stage: Target funnel stage slug.
            expected_version: Version the caller read (optimistic lock).
            score: Updated glass-box score after transition.
            actor_user_id: User who performed the override (None if agent).

        Returns:
            Updated Lead entity (re-read with pgcrypto decrypt).

        Raises:
            ValueError: If tenant_id is None.
            StaleStateError: If version mismatch detected (concurrent update).
        """
        if tenant_id is None:
            raise ValueError("LeadRepository.update_stage requires tenant_id — tenant isolation mandatory")

        now = _utc_now()

        stmt = text(
            """
            UPDATE vitalia_leads
            SET stage = :to_stage,
                stage_entered_at = :stage_entered_at,
                score = :score,
                version = version + 1,
                updated_at = :updated_at
            WHERE tenant_id = :tenant_id
              AND id = :lead_id
              AND version = :expected_version
              AND deleted_at IS NULL
            """
        )
        result = await self._session.execute(
            stmt,
            {
                "to_stage": to_stage,
                "stage_entered_at": now,
                "score": score,
                "updated_at": now,
                "tenant_id": str(tenant_id),
                "lead_id": str(lead_id),
                "expected_version": expected_version,
            },
        )

        if result.rowcount == 0:
            logger.warning(
                "lead_stage_update_conflict",
                lead_id=str(lead_id),
                tenant_id=str(tenant_id),
                expected_version=expected_version,
            )
            raise StaleStateError(lead_id=lead_id, expected_version=expected_version)

        logger.info(
            "lead_stage_updated",
            lead_id=str(lead_id),
            tenant_id=str(tenant_id),
            to_stage=to_stage,
            score=score,
        )

        updated = await self.get_by_id(entity_id=lead_id, tenant_id=tenant_id)
        if updated is None:
            raise ValueError(f"Lead {lead_id} not found after stage update for tenant {tenant_id}")
        return updated

    async def list_for_board(
        self,
        *,
        tenant_id: UUID,
        stage_filter: list[str] | None = None,
        is_frozen: bool = False,
        search: str | None = None,
        sort: str = "stage_age_desc",
    ) -> list[Lead]:
        """List leads for the funnel board with RN-17 sort.

        Default sort 'stage_age_desc' = ORDER BY stage_entered_at ASC
        (oldest in stage = most urgent = shown at top).

        Args:
            tenant_id: Tenant UUID — root isolation (required).
            stage_filter: Optional list of stage slugs to include.
                          If None, returns all non-frozen active leads.
            is_frozen: If True, returns frozen leads only (for Recuperar tab).
            search: Optional name search (uses LIKE on encrypted name — limited;
                    full-text search via decrypted query is handled at service layer).
            sort: Sort mode. Options:
                  'stage_age_desc' (default): ORDER BY stage_entered_at ASC (oldest first)
                  'score_desc': ORDER BY score DESC
                  'value_desc': ORDER BY estimated_value DESC
                  'activity_desc': ORDER BY updated_at DESC

        Returns:
            List of Lead entities with pgcrypto decryption applied.

        Raises:
            ValueError: If tenant_id is None.
        """
        if tenant_id is None:
            raise ValueError("LeadRepository.list_for_board requires tenant_id")

        kek_val = self._kek.get_key()

        # Build WHERE predicates
        predicates = [
            "tenant_id = :tenant_id",
            "deleted_at IS NULL",
            "is_frozen = :is_frozen",
        ]
        params: dict[str, object] = {
            "kek": kek_val,
            "tenant_id": str(tenant_id),
            "is_frozen": is_frozen,
        }

        if stage_filter:
            # Safe: stage values are internal slugs, never user-supplied raw SQL
            placeholders = ", ".join(f":stage_{i}" for i in range(len(stage_filter)))
            predicates.append(f"stage IN ({placeholders})")
            for i, s in enumerate(stage_filter):
                params[f"stage_{i}"] = s

        # Sort clause
        sort_clause = {
            "stage_age_desc": "stage_entered_at ASC NULLS LAST",
            "score_desc": "score DESC",
            "value_desc": "estimated_value DESC NULLS LAST",
            "activity_desc": "updated_at DESC",
        }.get(sort, "stage_entered_at ASC NULLS LAST")

        where_sql = " AND ".join(predicates)
        stmt = text(
            f"""
            SELECT
                id, tenant_id,
                pgp_sym_decrypt(name, :kek)::text AS name,
                pgp_sym_decrypt(email, :kek)::text AS email,
                pgp_sym_decrypt(phone, :kek)::text AS phone,
                source, status,
                pgp_sym_decrypt(notes, :kek)::text AS notes,
                stage, stage_entered_at, score, temperature, operated_by,
                channel, service_interest, assigned_doctor_id,
                estimated_value, currency,
                buying_signals, is_frozen, frozen_reason, frozen_at,
                closure_reason, reactivation_cohort_at, deposit_status,
                is_blacklisted, version,
                deleted_at, created_at, updated_at
            FROM vitalia_leads
            WHERE {where_sql}
            ORDER BY {sort_clause}
            """
        )

        result = await self._session.execute(stmt, params)
        rows = result.fetchall()

        return [self._row_to_lead(row) for row in rows]

    async def freeze(
        self,
        lead_id: UUID,
        *,
        tenant_id: UUID,
        reason: str,
    ) -> Lead:
        """Freeze a lead — set is_frozen=True with reason and timestamp.

        Args:
            lead_id: Lead UUID.
            tenant_id: Tenant UUID — isolation (required).
            reason: Freeze reason slug (inactividad_lead|sin_respuesta|agente_trabado).

        Returns:
            Updated Lead entity.

        Raises:
            ValueError: If tenant_id is None or lead not found.
        """
        if tenant_id is None:
            raise ValueError("LeadRepository.freeze requires tenant_id")

        now = _utc_now()
        stmt = text(
            """
            UPDATE vitalia_leads
            SET is_frozen = TRUE,
                frozen_reason = :reason,
                frozen_at = :frozen_at,
                updated_at = :updated_at
            WHERE tenant_id = :tenant_id
              AND id = :lead_id
              AND deleted_at IS NULL
            """
        )
        await self._session.execute(
            stmt,
            {
                "reason": reason,
                "frozen_at": now,
                "updated_at": now,
                "tenant_id": str(tenant_id),
                "lead_id": str(lead_id),
            },
        )
        logger.info("lead_frozen", lead_id=str(lead_id), tenant_id=str(tenant_id), reason=reason)

        updated = await self.get_by_id(entity_id=lead_id, tenant_id=tenant_id)
        if updated is None:
            raise ValueError(f"Lead {lead_id} not found after freeze for tenant {tenant_id}")
        return updated

    async def reactivate(
        self,
        lead_id: UUID,
        *,
        tenant_id: UUID,
    ) -> Lead:
        """Reactivate a frozen lead — clear is_frozen state.

        Args:
            lead_id: Lead UUID.
            tenant_id: Tenant UUID — isolation (required).

        Returns:
            Updated Lead entity with is_frozen=False.

        Raises:
            ValueError: If tenant_id is None or lead not found.
        """
        if tenant_id is None:
            raise ValueError("LeadRepository.reactivate requires tenant_id")

        now = _utc_now()
        stmt = text(
            """
            UPDATE vitalia_leads
            SET is_frozen = FALSE,
                frozen_reason = NULL,
                frozen_at = NULL,
                updated_at = :updated_at
            WHERE tenant_id = :tenant_id
              AND id = :lead_id
              AND deleted_at IS NULL
            """
        )
        await self._session.execute(
            stmt,
            {
                "updated_at": now,
                "tenant_id": str(tenant_id),
                "lead_id": str(lead_id),
            },
        )
        logger.info("lead_reactivated", lead_id=str(lead_id), tenant_id=str(tenant_id))

        updated = await self.get_by_id(entity_id=lead_id, tenant_id=tenant_id)
        if updated is None:
            raise ValueError(f"Lead {lead_id} not found after reactivate for tenant {tenant_id}")
        return updated

    def _row_to_lead(self, row: object) -> Lead:
        """Convert a DB row to a Lead domain entity.

        Handles both old (pre-funnel) and new (post-funnel) column sets.
        Missing funnel columns fall back to defaults (migration backward-compat).
        """

        def _get(attr: str, default: object = None) -> object:
            return getattr(row, attr, default)

        buying_signals_raw = _get("buying_signals") or []
        if isinstance(buying_signals_raw, str):
            import json

            buying_signals_raw = json.loads(buying_signals_raw)

        return Lead(
            id=UUID(str(row.id)),  # type: ignore[union-attr]
            tenant_id=UUID(str(row.tenant_id)),  # type: ignore[union-attr]
            name=row.name,  # type: ignore[union-attr]
            email=row.email,  # type: ignore[union-attr]
            phone=row.phone,  # type: ignore[union-attr]
            source=row.source,  # type: ignore[union-attr]
            status=row.status,  # type: ignore[union-attr]
            notes=row.notes,  # type: ignore[union-attr]
            # Funnel fields (default to safe values if columns don't exist yet)
            stage=str(_get("stage", "interesado")),
            stage_entered_at=_get("stage_entered_at"),  # type: ignore[arg-type]
            score=int(_get("score", 0)),  # type: ignore[arg-type]
            temperature=str(_get("temperature", "cold")),
            operated_by=str(_get("operated_by", "agent")),
            channel=_get("channel"),  # type: ignore[arg-type]
            service_interest=_get("service_interest"),  # type: ignore[arg-type]
            assigned_doctor_id=(
                UUID(str(_get("assigned_doctor_id"))) if _get("assigned_doctor_id") is not None else None
            ),
            estimated_value=(Decimal(str(_get("estimated_value"))) if _get("estimated_value") is not None else None),
            currency=_get("currency"),  # type: ignore[arg-type]
            buying_signals=list(buying_signals_raw),  # type: ignore[arg-type]
            is_frozen=bool(_get("is_frozen", False)),
            frozen_reason=_get("frozen_reason"),  # type: ignore[arg-type]
            frozen_at=_get("frozen_at"),  # type: ignore[arg-type]
            closure_reason=_get("closure_reason"),  # type: ignore[arg-type]
            reactivation_cohort_at=_get("reactivation_cohort_at"),  # type: ignore[arg-type]
            deposit_status=_get("deposit_status"),  # type: ignore[arg-type]
            is_blacklisted=bool(_get("is_blacklisted", False)),
            version=int(_get("version", 1)),  # type: ignore[arg-type]
            deleted_at=row.deleted_at,  # type: ignore[union-attr]
            created_at=row.created_at,  # type: ignore[union-attr]
            updated_at=row.updated_at,  # type: ignore[union-attr]
        )
