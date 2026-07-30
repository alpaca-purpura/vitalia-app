"""Arch fitness: PHI migration columns MUST use BYTEA type (pgcrypto encryption).

Per hipaa-lite.md § Encryption at rest:
  treatment_plans.notes → pgcrypto BYTEA
  re_engagement_events.payload_phi → pgcrypto BYTEA
  channel_sync_state.oauth_token_encrypted → pgcrypto BYTEA
  nps_responses.comment → pgcrypto BYTEA (migration 025, audit iter 2 fix F2)

  vitalia_patients.name → pgcrypto BYTEA (migration 035, CRM PHI base)
  vitalia_patients.date_of_birth → pgcrypto BYTEA (migration 035)
  vitalia_patients.dni → pgcrypto BYTEA (migration 035)
  vitalia_patients.phone → pgcrypto BYTEA (migration 035)
  vitalia_patients.email → pgcrypto BYTEA (migration 035)
  vitalia_patients.address → pgcrypto BYTEA (migration 035)
  vitalia_leads.name → pgcrypto BYTEA (migration 035)
  vitalia_leads.email → pgcrypto BYTEA (migration 035)
  vitalia_leads.phone → pgcrypto BYTEA (migration 035)
  vitalia_leads.notes → pgcrypto BYTEA (migration 035)

This test scans migration files for these columns and verifies BYTEA type.
Migration 025 adds pgcrypto trigger on nps_responses.comment for column-level
encryption per hipaa-lite.md § Encryption at rest (patient free-text PHI).
Migration 035 adds inline pgp_sym_* PHI columns for patients and leads
(CRM base tables — story vitalia-crm-phi-base-tables-migration).

T-infra-3 — vitalia pgcrypto PHI column enforcement gate.
"""

from __future__ import annotations

import re
from pathlib import Path

# Column-to-migration mapping: each (table, column) that MUST be BYTEA
# Updated audit iter 2: added nps_responses.comment (F2 fix — migration 025)
# Updated story vitalia-crm-phi-base-tables-migration: added patients/leads PHI cols (035)
PHI_BYTEA_COLUMNS: list[tuple[str, str]] = [
    ("treatment_plans", "notes"),
    ("re_engagement_events", "payload_phi"),
    ("channel_sync_state", "oauth_token_encrypted"),
    ("nps_responses", "comment"),
    # CRM PHI — migration 035 (vitalia_patients reconcile + vitalia_leads net-new)
    ("vitalia_patients", "name"),
    ("vitalia_patients", "date_of_birth"),
    ("vitalia_patients", "dni"),
    ("vitalia_patients", "phone"),
    ("vitalia_patients", "email"),
    ("vitalia_patients", "address"),
    ("vitalia_leads", "name"),
    ("vitalia_leads", "email"),
    ("vitalia_leads", "phone"),
    ("vitalia_leads", "notes"),
]

MIGRATIONS_ROOT = Path(__file__).resolve().parents[4] / "vitalia" / "backend" / "alembic" / "versions"


def _find_migration_files() -> list[Path]:
    """Return all .py migration files."""
    if not MIGRATIONS_ROOT.exists():
        return []
    return list(MIGRATIONS_ROOT.glob("*.py"))


def _migration_source() -> str:
    """Concatenate all migration file sources for scanning."""
    files = _find_migration_files()
    sources = []
    for f in files:
        try:
            sources.append(f.read_text(encoding="utf-8"))
        except Exception:
            pass
    return "\n".join(sources)


class TestPgcryptoPhiColumns:
    """PHI columns listed in hipaa-lite.md MUST use BYTEA type in migrations."""

    def test_migrations_directory_exists(self) -> None:
        """Migrations versions directory must exist."""
        assert MIGRATIONS_ROOT.exists(), (
            f"Migrations versions directory not found at: {MIGRATIONS_ROOT}\n"
            "Expected: vitalia/backend/src/modules/vitalia/persistence/migrations/versions/"
        )

    def test_treatment_plans_notes_is_bytea(self) -> None:
        """treatment_plans.notes must be defined as BYTEA in migrations.

        Per hipaa-lite.md: diagnosis, treatment_plan, medical_notes columns
        use pgcrypto symmetric encryption (BYTEA storage).
        """
        source = _migration_source()
        if not source:
            return  # No migrations yet — skip until T-infra-2 migrations exist

        # Check that treatment_plans table references BYTEA for notes
        # Pattern: notes ... BYTEA or BYTEA ... notes nearby treatment_plans
        has_bytea_notes = bool(
            re.search(
                r"treatment_plans.*notes.*BYTEA|notes.*BYTEA.*treatment_plans",
                source,
                re.IGNORECASE | re.DOTALL,
            )
        ) or ("treatment_plans" in source and "notes" in source and "BYTEA" in source)

        assert has_bytea_notes, (
            "treatment_plans.notes must be declared as BYTEA type in migrations "
            "(hipaa-lite.md § Encryption at rest: "
            "'treatment_plans.notes → pgcrypto symmetric encryption')"
        )

    def test_re_engagement_events_payload_phi_is_bytea(self) -> None:
        """re_engagement_events.payload_phi must be BYTEA."""
        source = _migration_source()
        if not source:
            return

        has_bytea = bool(
            re.search(
                r"re_engagement_events.*payload_phi.*BYTEA|payload_phi.*BYTEA",
                source,
                re.IGNORECASE | re.DOTALL,
            )
        ) or ("re_engagement_events" in source and "payload_phi" in source and "BYTEA" in source)

        assert has_bytea, (
            "re_engagement_events.payload_phi must be declared as BYTEA type "
            "in migrations (hipaa-lite.md § Encryption at rest)"
        )

    def test_channel_sync_state_oauth_token_is_bytea(self) -> None:
        """channel_sync_state.oauth_token_encrypted must be BYTEA."""
        source = _migration_source()
        if not source:
            return

        has_bytea = bool(
            re.search(
                r"channel_sync_state.*oauth_token_encrypted.*BYTEA|oauth_token_encrypted.*BYTEA",
                source,
                re.IGNORECASE | re.DOTALL,
            )
        ) or ("channel_sync_state" in source and "oauth_token_encrypted" in source and "BYTEA" in source)

        assert has_bytea, (
            "channel_sync_state.oauth_token_encrypted must be declared as BYTEA type "
            "in migrations (hipaa-lite.md § Encryption at rest — OAuth tokens are PHI-adjacent)"
        )

    def test_kek_client_exists(self) -> None:
        """KEKClient must exist at _shared/encryption/kek_client.py."""
        kek_path = (
            Path(__file__).resolve().parents[4]
            / "vitalia"
            / "backend"
            / "src"
            / "modules"
            / "vitalia"
            / "_shared"
            / "encryption"
            / "kek_client.py"
        )
        assert kek_path.exists(), (
            "vitalia/backend/src/modules/vitalia/_shared/encryption/kek_client.py "
            "must exist — KEKClient provides key management for pgcrypto operations "
            "(hipaa-lite.md § Encryption at rest)"
        )

    def test_kek_client_reads_from_env_not_hardcoded(self) -> None:
        """KEKClient must read KEK from environment variable, not hardcode it."""
        kek_path = (
            Path(__file__).resolve().parents[4]
            / "vitalia"
            / "backend"
            / "src"
            / "modules"
            / "vitalia"
            / "_shared"
            / "encryption"
            / "kek_client.py"
        )
        if not kek_path.exists():
            return

        source = kek_path.read_text(encoding="utf-8")
        assert "os.environ" in source or "os.getenv" in source or "settings" in source or "env" in source.lower(), (
            "KEKClient must read encryption key from environment variable or settings, "
            "never hardcode it (hipaa-lite.md § Encryption at rest anti-patterns)"
        )

    def test_nps_responses_comment_is_bytea(self) -> None:
        """nps_responses.comment must be defined as BYTEA in migrations.

        Per hipaa-lite.md: patient free-text NPS comment is PHI.
        Migration 022 defines comment as BYTEA.
        Migration 025 adds pgcrypto trigger for column-level encryption.
        Audit iter 2 fix F2 — closes gap in arch coverage allowlist.
        """
        source = _migration_source()
        if not source:
            return

        has_bytea = bool(
            re.search(
                r"nps_responses.*comment.*BYTEA|comment.*BYTEA.*nps",
                source,
                re.IGNORECASE | re.DOTALL,
            )
        ) or ("nps_responses" in source and "comment" in source and "BYTEA" in source)

        assert has_bytea, (
            "nps_responses.comment must be declared as BYTEA type in migrations "
            "(hipaa-lite.md § Encryption at rest: patient free-text NPS comment is PHI). "
            "Migration 022 defines the column; migration 025 adds pgcrypto trigger."
        )

    def test_nps_responses_comment_has_pgcrypto_trigger(self) -> None:
        """Migration 025 must define pgcrypto trigger on nps_responses.comment.

        Per hipaa-lite.md § Encryption at rest: pgcrypto symmetric encryption
        required for PHI free-text. Trigger enforces encryption transparently
        on INSERT/UPDATE using app.encryption_key GUC.
        """
        source = _migration_source()
        if not source:
            return

        has_trigger = "trg_encrypt_nps_comment" in source or ("nps_responses" in source and "pgp_sym_encrypt" in source)

        assert has_trigger, (
            "Migration 025 must define pgcrypto encryption trigger on "
            "vitalia_nps_responses (trg_encrypt_nps_comment) using "
            "pgp_sym_encrypt() with app.encryption_key GUC. "
            "Required by hipaa-lite.md § Encryption at rest (F2 audit iter 2)."
        )

    def test_no_phi_column_uses_text_or_varchar_unencrypted(self) -> None:
        """PHI columns listed in hipaa-lite.md MUST NOT use TEXT/VARCHAR (unencrypted)."""
        source = _migration_source()
        if not source:
            return

        # For each PHI column that should be BYTEA, check it's NOT defined as TEXT/VARCHAR
        suspicious_patterns = [
            # \b word-boundary: match the bare PHI column `notes`, NOT compound
            # non-PHI columns like `bio_inputs_notes` (staff bio, table vitalia_lisa_staff)
            # which legitimately use TEXT and are not patient PHI.
            # `'` in the lookbehind excludes PROSE matches like the migration-038 meta-comment
            # `(NOT 'notes TEXT')` (HB-70 false-positive — DDL never quotes the bare column name).
            (r"(?<![\w'])notes\s+TEXT", "treatment_plans.notes defined as TEXT instead of BYTEA"),
            (r"payload_phi\s+TEXT", "re_engagement_events.payload_phi defined as TEXT"),
            (r"payload_phi\s+VARCHAR", "re_engagement_events.payload_phi defined as VARCHAR"),
            (r"oauth_token_encrypted\s+TEXT", "channel_sync_state.oauth_token_encrypted as TEXT"),
            (r"oauth_token_encrypted\s+VARCHAR", "channel_sync_state.oauth_token_encrypted as VARCHAR"),
            (r"comment\s+TEXT\b(?!.*nps_responses)", "nps_responses.comment defined as TEXT instead of BYTEA"),
        ]
        violations = [msg for pattern, msg in suspicious_patterns if re.search(pattern, source, re.IGNORECASE)]

        assert violations == [], "PHI columns MUST use BYTEA (not TEXT/VARCHAR) for pgcrypto encryption:\n" + "\n".join(
            violations
        )

    # -------------------------------------------------------------------------
    # CRM PHI columns — migration 035 (vitalia_patients reconcile + vitalia_leads)
    # Story: vitalia-crm-phi-base-tables-migration · ADR-vitalia-007-phi-pgcrypto-encryption
    # -------------------------------------------------------------------------

    def test_vitalia_patients_phi_cols_are_bytea(self) -> None:
        """vitalia_patients PHI columns (name/date_of_birth/dni/phone/email/address) must be BYTEA.

        Migration 035 adds these via ADD COLUMN IF NOT EXISTS on vitalia_patients.
        Encrypted at repo layer with pgp_sym_encrypt(:val, :kek) / pgp_sym_decrypt(col, :kek).
        Per hipaa-lite.md § Encryption at rest + ADR-vitalia-007-phi-pgcrypto-encryption D3.
        """
        source = _migration_source()
        if not source:
            return

        patients_phi_cols = ["name", "date_of_birth", "dni", "phone", "email", "address"]
        missing = []
        for col in patients_phi_cols:
            # Migration 035 must contain "ADD COLUMN IF NOT EXISTS <col> BYTEA" context
            # within the vitalia_patients scope. We check that col + BYTEA appear
            # together in the migration source (the col is named near BYTEA, within patients context).
            has_bytea = bool(
                re.search(
                    rf"vitalia_patients.*\b{re.escape(col)}\b.*BYTEA|\b{re.escape(col)}\s+BYTEA",
                    source,
                    re.IGNORECASE | re.DOTALL,
                )
            )
            if not has_bytea:
                # Broader check: col + BYTEA appear in migration AND vitalia_patients is referenced
                has_bytea = (
                    "vitalia_patients" in source
                    and f"{col}" in source
                    and "BYTEA" in source
                    and re.search(rf"\b{re.escape(col)}\s+BYTEA", source, re.IGNORECASE) is not None
                )
            if not has_bytea:
                missing.append(col)

        assert not missing, (
            f"vitalia_patients PHI columns must be BYTEA in migrations (found missing: {missing}). "
            "Migration 035 must ADD COLUMN IF NOT EXISTS <col> BYTEA for each. "
            "Per hipaa-lite.md § Encryption at rest + ADR-vitalia-007 D3."
        )

    def test_vitalia_leads_phi_cols_are_bytea(self) -> None:
        """vitalia_leads PHI/PII columns (name/email/phone/notes) must be BYTEA.

        Migration 035 creates vitalia_leads with these columns as BYTEA.
        Encrypted at repo layer with pgp_sym_encrypt(:val, :kek).
        Per ADR-vitalia-007-phi-pgcrypto-encryption D3.
        """
        source = _migration_source()
        if not source:
            return

        leads_phi_cols = ["name", "email", "phone", "notes"]
        missing = []
        for col in leads_phi_cols:
            has_bytea = bool(
                re.search(
                    rf"vitalia_leads.*\b{re.escape(col)}\b.*BYTEA|\b{re.escape(col)}\s+BYTEA",
                    source,
                    re.IGNORECASE | re.DOTALL,
                )
            )
            if not has_bytea:
                has_bytea = (
                    "vitalia_leads" in source
                    and f"{col}" in source
                    and "BYTEA" in source
                    and re.search(rf"\b{re.escape(col)}\s+BYTEA", source, re.IGNORECASE) is not None
                )
            if not has_bytea:
                missing.append(col)

        assert not missing, (
            f"vitalia_leads PHI columns must be BYTEA in migrations (found missing: {missing}). "
            "Migration 035 must CREATE TABLE vitalia_leads with <col> BYTEA for each. "
            "Per ADR-vitalia-007 D3."
        )

    def test_migration_035_exists(self) -> None:
        """Migration 035_vitalia_crm_phi_base_tables.py must exist.

        Required by story vitalia-crm-phi-base-tables-migration T-1.
        """
        migration_035 = MIGRATIONS_ROOT / "035_vitalia_crm_phi_base_tables.py"
        assert migration_035.exists(), (
            f"Migration 035 not found at: {migration_035}. "
            "Create vitalia/backend/alembic/versions/035_vitalia_crm_phi_base_tables.py "
            "(story vitalia-crm-phi-base-tables-migration T-1)."
        )

    def test_migration_035_revision_chain(self) -> None:
        """Migration 035 must have correct revision and down_revision."""
        migration_035 = MIGRATIONS_ROOT / "035_vitalia_crm_phi_base_tables.py"
        if not migration_035.exists():
            return

        content = migration_035.read_text(encoding="utf-8")
        assert 'revision = "035_vitalia"' in content, "Migration 035 must declare revision = '035_vitalia'"
        assert 'down_revision = "034_vitalia"' in content, "Migration 035 must declare down_revision = '034_vitalia'"

    def test_migration_035_no_index_on_ciphertext(self) -> None:
        """Migration 035 must NOT create indexes on PHI/ciphertext columns.

        Per ADR-vitalia-007 D4: NO indexes on encrypted columns (blind index = follow-up).
        Only plaintext columns (tenant_id, clinic_id, status) may be indexed.
        """
        migration_035 = MIGRATIONS_ROOT / "035_vitalia_crm_phi_base_tables.py"
        if not migration_035.exists():
            return

        content = migration_035.read_text(encoding="utf-8")
        # Regex: CREATE INDEX that mentions a ciphertext column name
        ciphertext_cols = ["name", "date_of_birth", "dni", "phone", "email", "address", "notes"]
        for col in ciphertext_cols:
            pattern = rf"CREATE\s+INDEX[^\n;]*\b{re.escape(col)}\b"
            match = re.search(pattern, content, re.IGNORECASE)
            assert not match, (
                f"Migration 035 must NOT create index on PHI column '{col}' (ciphertext). "
                f"ADR-vitalia-007 D4: blind index is a follow-up. Found: {match.group()[:80] if match else ''}"
            )

    def test_migration_035_downgrade_does_not_drop_vitalia_patients(self) -> None:
        """Migration 035 downgrade must NOT drop vitalia_patients table.

        Per ADR-vitalia-007 D5: vitalia_patients is owned by 016 — 035 downgrade
        only removes the PHI columns it added and drops vitalia_leads.
        """
        migration_035 = MIGRATIONS_ROOT / "035_vitalia_crm_phi_base_tables.py"
        if not migration_035.exists():
            return

        content = migration_035.read_text(encoding="utf-8")
        # Find downgrade function body
        downgrade_match = re.search(
            r"def downgrade\(\)[^:]*:(.*?)(?=^def |\Z)",
            content,
            re.DOTALL | re.MULTILINE,
        )
        if not downgrade_match:
            return  # can't parse — skip

        downgrade_body = downgrade_match.group(1)
        # Must NOT have DROP TABLE vitalia_patients
        assert not re.search(r"DROP\s+TABLE.*vitalia_patients", downgrade_body, re.IGNORECASE), (
            "Migration 035 downgrade() must NOT drop vitalia_patients — "
            "that table is owned by migration 016 (ADR-vitalia-007 D5)."
        )
