"""API test conftest — shared test app factory for campaigns api tests.

Provides _make_campaigns_test_app() to replace `from src.main import app`
pattern from AISALESHT in luana-platform context.
"""

from __future__ import annotations

from fastapi import FastAPI


def _make_campaigns_test_app() -> FastAPI:
    """Create a minimal FastAPI test app with campaigns routers mounted at /api/v1.

    Replaces AISALESHT `from src.main import app` — luana-platform has no
    single monolith main.py. Each package tests against its own test app.

    Per backend-ddd.md: redirect_slashes=False mandatory.
    """
    from luana_core_campaigns.api.routers.campaigns_router import router as campaigns_router
    from luana_core_campaigns.api.routers.segments_router import router as segments_router
    from luana_core_campaigns.api.routers.templates_router import router as templates_router

    _app = FastAPI(redirect_slashes=False)
    _app.include_router(campaigns_router, prefix="/api/v1")
    _app.include_router(segments_router, prefix="/api/v1")
    _app.include_router(templates_router, prefix="/api/v1")
    return _app
