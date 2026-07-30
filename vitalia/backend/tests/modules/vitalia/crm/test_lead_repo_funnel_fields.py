# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""Regression — LeadRepository.create MUST persist funnel fields (bug 2026-06-11).

Origen: fix demo-bug-2 (channel no persistía). El service pasaba
stage/channel/service_interest/estimated_value/currency al repo, pero
repo.create() no aceptaba esos kwargs → TypeError → 500 en POST /crm/leads.
Los tests de funnel_api mockean el SERVICE entero, así que el contrato
service→repo nunca se ejercitó (falso verde — verification-real-not-200).

Este test ejercita el contrato real service→repo con session mockeada:
  - repo.create acepta los kwargs funnel (RED: TypeError pre-fix)
  - el INSERT incluye las columnas funnel + marketing_opt_in + stage_entered_at
  - los params del INSERT llevan los valores

downstream-regression-na: brand-local vitalia CRM
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.vitalia.crm.infrastructure.persistence.lead_repository import (
    LeadRepository,
)

pytestmark = pytest.mark.asyncio


def _make_repo() -> tuple[LeadRepository, AsyncMock]:
    """LeadRepository con session + KEK mockeados."""
    session = AsyncMock()
    kek = MagicMock()
    kek.get_key.return_value = "test-kek-32-bytes-hex-aaaaaaaaaaaaaaaa"
    repo = LeadRepository(session=session, kek=kek)
    return repo, session


async def test_create_accepts_and_persists_funnel_fields() -> None:
    """repo.create con stage/channel/service_interest/estimated_value/currency.

    RED pre-fix: TypeError unexpected keyword argument 'stage'.
    """
    repo, session = _make_repo()
    tenant_id = uuid4()
    lead_id = uuid4()

    # get_by_id re-read post-INSERT → devolvemos sentinel para no tocar DB
    sentinel = object()
    repo.get_by_id = AsyncMock(return_value=sentinel)  # type: ignore[method-assign]

    result = await repo.create(
        id=lead_id,
        tenant_id=tenant_id,
        name="María Torres",
        email="maria@example.com",
        phone="+99 0 1234 5678",
        source="instagram",
        status="new",
        notes=None,
        marketing_opt_in=True,
        stage="calificando",
        channel="ig",
        service_interest="Ortodoncia",
        estimated_value=Decimal("1500.00"),
        currency="PEN",
    )

    assert result is sentinel

    # INSERT ejecutado con columnas + params funnel
    assert session.execute.await_count == 1
    stmt, params = session.execute.await_args.args
    sql = str(stmt)
    for col in (
        "stage",
        "stage_entered_at",
        "channel",
        "service_interest",
        "estimated_value",
        "currency",
        "marketing_opt_in",
    ):
        assert col in sql, f"columna '{col}' ausente del INSERT"

    assert params["stage"] == "calificando"
    assert params["channel"] == "ig"
    assert params["service_interest"] == "Ortodoncia"
    assert params["estimated_value"] == Decimal("1500.00")
    assert params["currency"] == "PEN"
    assert params["marketing_opt_in"] is True
    assert params["stage_entered_at"] is not None


async def test_create_funnel_fields_default_when_omitted() -> None:
    """Back-compat: llamada vieja (sin kwargs funnel) sigue funcionando."""
    repo, session = _make_repo()
    repo.get_by_id = AsyncMock(return_value=object())  # type: ignore[method-assign]

    await repo.create(
        id=uuid4(),
        tenant_id=uuid4(),
        name="Carlos Ruiz",
        email=None,
        phone="+99 0 8765 4321",
        source=None,
        status="new",
        notes=None,
        marketing_opt_in=False,
    )

    _, params = session.execute.await_args.args
    assert params["stage"] == "interesado"
    assert params["channel"] is None
    assert params["service_interest"] is None
    assert params["estimated_value"] is None
    assert params["currency"] is None
