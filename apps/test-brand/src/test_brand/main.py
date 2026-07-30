"""FastAPI app for test-brand SDK smoke validation.

Per 05-guidelines.md §1.10 verbatim — Story 8 §7.5.2 D2=B explicit register pattern.

Lifespan:
1. Construct ExtensionPointRegistry (adapter wiring None for Story 8 — Stories 11-13 wire real)
2. register_all(registry) — 18 registrations (5 executable + 13 stubs)
3. registry.close() — CC-3 lock; subsequent register raises RegistrationClosedError
4. app.state.registry — make available for request handlers
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from luana_core_extension_sdk import ExtensionPointRegistry

from test_brand.extensions import register_all


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:  # type: ignore[misc]
    """FastAPI lifespan event — Story 8 §7.5.2 D2=B explicit register pattern.

    1. Construct ExtensionPointRegistry (adapter wiring None for Story 8)
    2. register_all(registry) — 18 registrations (5 executable + 13 stubs)
    3. registry.close() — CC-3 lock
    4. app.state.registry — available for request handlers (Stories 11-13 retrieve via dep)
    """
    registry = ExtensionPointRegistry(
        sales_agent_tool_registry_adapter=None,  # Story 8 — Stories 11-13 wire real
        copilot_workflow_registry_adapter=None,
    )
    register_all(registry)
    registry.close()
    app.state.registry = registry
    yield
    # No teardown — registry held until process exit


app = FastAPI(lifespan=lifespan, redirect_slashes=False)


@app.get("/health")
async def health() -> dict[str, Any]:
    """Health check endpoint — verifies registry is closed (CC-3 lock confirmed)."""
    return {"status": "ok", "registry_closed": True}
