"""ESC-6 — PromptVersion must expose tenant_id so the HYBRID/DB prompt-load path
builds its queries. Architect-verified: RED (AttributeError) before the column.
"""

import uuid

from sqlalchemy import desc, select

from luana_core_sales_agent.infrastructure.models.prompt_version_model import (
    PromptVersion,
)


def test_prompt_version_has_tenant_id_column() -> None:
    assert hasattr(PromptVersion, "tenant_id")
    assert "tenant_id" in PromptVersion.__table__.columns


def test_prompt_load_query_branches_build() -> None:
    tid = uuid.uuid4()
    # specific-override branch (base.py:84-96)
    q1 = (
        select(PromptVersion)
        .where(
            PromptVersion.key == "k",
            PromptVersion.is_active,
            PromptVersion.tenant_id == tid,
        )
        .order_by(desc(PromptVersion.version))
    )
    # system-default branch (base.py:103-115)
    q2 = (
        select(PromptVersion)
        .where(
            PromptVersion.key == "k",
            PromptVersion.is_active,
            PromptVersion.tenant_id.is_(None),
        )
        .order_by(desc(PromptVersion.version))
    )
    assert "tenant_id" in str(q1)
    assert "IS NULL" in str(q2).upper()
