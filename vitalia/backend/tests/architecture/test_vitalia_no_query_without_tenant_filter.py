"""Architecture fitness test — A2: tenant_id column present + indexed.

Per T-be-2 acceptance criterion A2:
  All 10 tenant-scoped models must have tenant_id column NOT NULL + indexed.
  plan_tier_configs is CROSS-TENANT (exempt).

This test inspects SQLAlchemy metadata — no Postgres required.
"""

from __future__ import annotations

import pytest

TENANT_SCOPED_TABLES = [
    "vitalia_bookings",
    "vitalia_treatment_followups",
    "vitalia_consent_records",
    "vitalia_medical_audit_log",
    "vitalia_payment_intents",
    "vitalia_payment_schedules",
    "vitalia_adherence_records",
    "vitalia_doctor_extensions",
    "vitalia_patient_medical_histories",
    "vitalia_patient_dental_histories",
]

CROSS_TENANT_TABLES = [
    "vitalia_plan_tier_configs",
]

# Models with no deleted_at (financial records, audit log, consent records, adherence)
NO_DELETED_AT_TABLES = [
    "vitalia_consent_records",
    "vitalia_medical_audit_log",
    "vitalia_payment_intents",
    "vitalia_payment_schedules",
    "vitalia_adherence_records",
]

SOFT_DELETE_TABLES = [
    "vitalia_bookings",
    "vitalia_treatment_followups",
    "vitalia_doctor_extensions",
    "vitalia_patient_medical_histories",
    "vitalia_patient_dental_histories",
]


def _get_metadata():
    """Import all models and return Base.metadata."""
    from luana_core_platform.domain.base_entity import Base

    import src.modules.vitalia.infrastructure.models  # noqa: F401

    return Base.metadata


@pytest.mark.parametrize("tablename", TENANT_SCOPED_TABLES)
def test_tenant_scoped_table_has_tenant_id_column(tablename: str) -> None:
    """Each tenant-scoped table must have a tenant_id column."""
    metadata = _get_metadata()
    assert tablename in metadata.tables, f"Table '{tablename}' not found in Base.metadata"
    table = metadata.tables[tablename]
    assert "tenant_id" in table.c, f"Table '{tablename}' missing tenant_id column (R2 tenant-isolation)"


@pytest.mark.parametrize("tablename", TENANT_SCOPED_TABLES)
def test_tenant_id_is_not_nullable(tablename: str) -> None:
    """tenant_id must be NOT NULL on all tenant-scoped tables."""
    metadata = _get_metadata()
    table = metadata.tables[tablename]
    col = table.c["tenant_id"]
    assert not col.nullable, f"Table '{tablename}'.tenant_id must be NOT NULL"


@pytest.mark.parametrize("tablename", TENANT_SCOPED_TABLES)
def test_tenant_id_is_indexed(tablename: str) -> None:
    """tenant_id must have an index on all tenant-scoped tables."""
    metadata = _get_metadata()
    table = metadata.tables[tablename]

    # Check column-level index flag OR named index covering tenant_id
    col = table.c["tenant_id"]
    has_col_index = col.index  # True if index=True on mapped_column

    # Also check named indexes on the table
    index_cols = set()
    for idx in table.indexes:
        for c in idx.columns:
            index_cols.add(c.name)

    has_any_index = has_col_index or ("tenant_id" in index_cols)
    assert has_any_index, (
        f"Table '{tablename}'.tenant_id must be indexed (tenant isolation requires fast tenant-scoped queries)"
    )


@pytest.mark.parametrize("tablename", CROSS_TENANT_TABLES)
def test_cross_tenant_table_has_no_tenant_id(tablename: str) -> None:
    """Cross-tenant tables (global catalogs) must NOT have tenant_id."""
    metadata = _get_metadata()
    assert tablename in metadata.tables, f"Cross-tenant table '{tablename}' not found in Base.metadata"
    table = metadata.tables[tablename]
    assert "tenant_id" not in table.c, (
        f"Cross-tenant table '{tablename}' must NOT have tenant_id (it is a global platform catalog)"
    )


def test_medical_audit_log_has_no_deleted_at() -> None:
    """vitalia_medical_audit_log must NOT have deleted_at — IMMUTABLE (7-year retention)."""
    metadata = _get_metadata()
    table = metadata.tables["vitalia_medical_audit_log"]
    assert "deleted_at" not in table.c, "vitalia_medical_audit_log is IMMUTABLE — must not have deleted_at column"


@pytest.mark.parametrize("tablename", SOFT_DELETE_TABLES)
def test_soft_delete_tables_have_deleted_at(tablename: str) -> None:
    """Soft-delete tables must have deleted_at column."""
    metadata = _get_metadata()
    table = metadata.tables[tablename]
    assert "deleted_at" in table.c, (
        f"Table '{tablename}' must have deleted_at for soft-delete support "
        "(hard deletes are forbidden per backend-ddd.md)"
    )


@pytest.mark.parametrize("tablename", SOFT_DELETE_TABLES)
def test_deleted_at_is_nullable(tablename: str) -> None:
    """deleted_at must be nullable (NULL = not deleted)."""
    metadata = _get_metadata()
    table = metadata.tables[tablename]
    col = table.c["deleted_at"]
    assert col.nullable, f"Table '{tablename}'.deleted_at must be nullable (NULL = active record)"


@pytest.mark.parametrize("tablename", TENANT_SCOPED_TABLES + CROSS_TENANT_TABLES)
def test_all_tables_have_created_at(tablename: str) -> None:
    """All tables must have created_at for auditability."""
    metadata = _get_metadata()
    table = metadata.tables[tablename]
    assert "created_at" in table.c, f"Table '{tablename}' missing created_at column"


@pytest.mark.parametrize("tablename", TENANT_SCOPED_TABLES + CROSS_TENANT_TABLES)
def test_all_tables_have_primary_key(tablename: str) -> None:
    """All tables must have a primary key."""
    metadata = _get_metadata()
    table = metadata.tables[tablename]
    pk_cols = list(table.primary_key.columns)
    assert len(pk_cols) >= 1, f"Table '{tablename}' must have a primary key"
    assert pk_cols[0].name == "id", f"Table '{tablename}' primary key must be 'id'"
