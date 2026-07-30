# cap: copilot.valeria-wizard-onboarding-agentic
"""Integration — wizard durable resume across a simulated process restart.

``v_replay_safety`` (04-validators.yaml, story empleados-ia-auto-extension): compile
the vitalia wizard graph with the DURABLE checkpointer
(``luana_core_flows.make_durable_checkpointer`` → ``AsyncPostgresSaver``), advance
>=1 checkpoint, then build a FRESH checkpointer (new connection pool, same Postgres
DB) and re-read the thread → state resumes from the PERSISTED checkpoint, not a
restart. This proves the lift produces real durable persistence: an in-memory
``MemorySaver`` could never survive a new pool / process restart.

Requires real Postgres (marker ``integration`` → auto-skipped by tests/conftest.py
when the DB is down) + a working psycopg/libpq. Native runs without
``psycopg[binary]`` skip gracefully (the dev container has libpq).
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from luana_core_flows.checkpointer import build_flow_thread_id

pytestmark = pytest.mark.integration

_SQLALCHEMY_DRIVER_TAGS = (
    "postgresql+asyncpg://",
    "postgresql+psycopg://",
    "postgresql+psycopg2://",
)


def _psycopg_dsn() -> str:
    """Resolve the test Postgres DSN in psycopg (libpq) form."""
    dsn = os.getenv(
        "POSTGRES_DSN",
        "postgresql://postgres:postgres@localhost:5432/vitalia_test",
    )
    for tag in _SQLALCHEMY_DRIVER_TAGS:
        if dsn.startswith(tag):
            return "postgresql://" + dsn.split("://", 1)[1]
    return dsn


async def _make_durable_or_skip():
    """Build a durable checkpointer; skip gracefully if psycopg/libpq is missing."""
    from luana_core_flows.checkpointer import make_durable_checkpointer

    try:
        return await make_durable_checkpointer(postgres_dsn=_psycopg_dsn(), encryption_key=None)
    except RuntimeError as exc:  # psycopg/libpq wrapper unavailable (native run)
        pytest.skip(f"durable checkpointer unavailable (install psycopg[binary]): {exc}")


async def test_wizard_durable_resume_survives_new_pool() -> None:
    """A persisted checkpoint resumes from a FRESH pool — durable, not in-memory."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_graph import (
        build_wizard_onboarding_graph,
    )
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_state import (
        build_initial_state,
    )

    tenant_id = str(uuid4())
    draft_id = str(uuid4())
    thread_id = build_flow_thread_id(
        flow_id="vitalia.wizard",
        tenant_id=tenant_id,
        instance_id=draft_id,
    )
    config = {"configurable": {"thread_id": thread_id}}
    initial = build_initial_state(tenant_id=tenant_id, user_id=str(uuid4()), clinic_id=None)

    # 1) Advance >=1 checkpoint on a durable AsyncPostgresSaver.
    cp1 = await _make_durable_or_skip()
    graph1 = build_wizard_onboarding_graph(checkpointer=cp1)
    await graph1.ainvoke({**initial, "task_complete": True}, config=config)
    snap1 = await graph1.aget_state(config)
    assert snap1.values.get("tenant_id") == tenant_id

    # 2) Simulate a process restart — a BRAND-NEW checkpointer (fresh pool, same DB).
    cp2 = await _make_durable_or_skip()
    graph2 = build_wizard_onboarding_graph(checkpointer=cp2)
    snap2 = await graph2.aget_state(config)

    # 3) State resumed from the persisted Postgres checkpoint (impossible w/ MemorySaver).
    assert snap2.values, "no persisted checkpoint found — durable persistence failed"
    assert snap2.values.get("tenant_id") == tenant_id, "resumed state lost tenant isolation"
    assert snap2.config["configurable"]["thread_id"] == thread_id
