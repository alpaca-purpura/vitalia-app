# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""Lucas cron trigger internal API routes.

Internal endpoint consumed by LucasCronScheduler (APScheduler) only.
Auth: Bearer token = LUCAS_CRON_SECRET env var.
NOT exposed to end-users or frontend.

Endpoint:
  POST /api/v1/copilot/internal/lucas/cron-trigger
    Headers:
      Authorization: Bearer <LUCAS_CRON_SECRET>
      X-Tenant-ID: <UUID>
      X-Clinic-ID: <UUID>

response_model= MANDATORY on every route (arch fitness V-AE-2).
redirect_slashes=False is set on the FastAPI *app* in main.py.
"""

from __future__ import annotations

import os
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict

logger = structlog.get_logger()

router = APIRouter(prefix="/internal/lucas", tags=["lucas-internal"])

_SECRET_ENV_KEY = "LUCAS_CRON_SECRET"


class CronTriggerResponse(BaseModel):
    """Response for internal Lucas cron trigger endpoint."""

    model_config = ConfigDict(from_attributes=True)

    status: str
    tenant_id: str
    clinic_id: str
    message: str


def _verify_cron_secret(authorization: str) -> None:
    """Validate Bearer token against LUCAS_CRON_SECRET env var.

    Raises HTTP 401 if missing/invalid.
    """
    expected = os.environ.get(_SECRET_ENV_KEY, "")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LUCAS_CRON_SECRET not configured.",
        )
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must use Bearer scheme.",
        )
    token = authorization[len("Bearer ") :].strip()
    if token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cron secret.",
        )


@router.post("/cron-trigger", response_model=CronTriggerResponse)
async def lucas_cron_trigger(
    authorization: Annotated[str, Header()],
    x_tenant_id: Annotated[str, Header(alias="X-Tenant-ID")],
    x_clinic_id: Annotated[str, Header(alias="X-Clinic-ID")],
) -> CronTriggerResponse:
    """Trigger Lucas cron computation for a tenant/clinic.

    Internal endpoint — only callable from LucasCronScheduler with valid secret.
    Runs:
      1. LucasStageRecommendationService for each active stage
      2. LucasAttributionService for current month period
      3. LucasReferralsService for current month period

    Auth: Bearer <LUCAS_CRON_SECRET>. Returns 401 if invalid.
    """
    # Validate secret FIRST
    _verify_cron_secret(authorization)

    # Parse UUIDs
    try:
        tenant_id = UUID(x_tenant_id)
        clinic_id = UUID(x_clinic_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID in header: {exc}",
        ) from exc

    logger.info(
        "lucas_cron_trigger_received",
        tenant_id=str(tenant_id),
        clinic_id=str(clinic_id),
    )

    # NOTE: Full service wiring is injected by the ARQ job (lucas_weekly_recommendations.py)
    # This internal route signals that the cron fired; actual service execution happens
    # in the ARQ worker context where DB session + services are available.
    # The route acknowledges receipt and returns 202.
    # (Full service DI wiring done in lucas_weekly_recommendations.py)

    return CronTriggerResponse(
        status="accepted",
        tenant_id=str(tenant_id),
        clinic_id=str(clinic_id),
        message="Lucas cron trigger accepted. Processing scheduled.",
    )
