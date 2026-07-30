# cap: fidelizacion.re-engagement
# story-origin: TBD
"""Router de fidelización vitalia — monta los 3 sub-routers de la capa API.

Mounts:
  re_engagement_endpoints — /re-engagement/* (6 rutas)
  nps_endpoints           — /nps/* (2 rutas)
  fidelizacion_summary_endpoints — /summary + /activity-stream (2 rutas)

Registrar en main.py:
    from src.modules.vitalia.fidelizacion.api.router import fidelizacion_router
    app.include_router(fidelizacion_router, prefix="/api/v1/vitalia/fidelizacion")

HIPAA-lite: todos los routers hijos aplican dual filter tenant_id + clinic_id,
RBAC vía roles PHI, y response_model= mandatorio (arch test enforces).

downstream-regression-na: brand-local fidelizacion router vitalia
"""

from __future__ import annotations

from fastapi import APIRouter

from src.modules.vitalia.fidelizacion.api.fidelizacion_summary_endpoints import (
    router as summary_router,
)
from src.modules.vitalia.fidelizacion.api.nps_endpoints import router as nps_router
from src.modules.vitalia.fidelizacion.api.re_engagement_endpoints import (
    router as re_engagement_router,
)

# Router raíz — agrupa todos los endpoints de fidelización
fidelizacion_router = APIRouter(prefix="", tags=["fidelizacion"])

fidelizacion_router.include_router(re_engagement_router)
fidelizacion_router.include_router(nps_router)
fidelizacion_router.include_router(summary_router)
