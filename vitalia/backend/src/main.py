# cap: observability.api-health-endpoint
# story-origin: TBD
"""Vitalia FastAPI application entry point.

Per 03-arch-be.md § 3 + 05-guidelines § 1.1:
  - FastAPI(redirect_slashes=False) MANDATORY (arch test enforces).
    Default True → 307 POST → Next.js drops body.
  - Vitalia router mounted at /api/v1/vitalia prefix.
  - No business logic here — thin mount only.

Arch tests verify:
  - redirect_slashes=False present in main.py app instantiation.
  - All endpoints have response_model= (V-AE-2 PII gate).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from luana_core_iam.api.routers import auth_router as iam_users
from pydantic import BaseModel

from src.modules.vitalia._shared.telemetry.api.telemetry_router import router as telemetry_router
from src.modules.vitalia.admin.api.admin_helpers_router import router as admin_helpers_router
from src.modules.vitalia.api.routes import router as vitalia_router
from src.modules.vitalia.api.webhook_routes import webhook_router
from src.modules.vitalia.audit.api.audit_log_router import router as audit_log_router
from src.modules.vitalia.brand_studio.api.routers.marca_router import router as marca_router
from src.modules.vitalia.clinics.api.account_router import router as account_router
from src.modules.vitalia.clinics.api.assets_proxy_router import router as assets_proxy_router
from src.modules.vitalia.clinics.api.doctors_router import router as doctors_router
from src.modules.vitalia.clinics.api.public_doctors_router import router as public_doctors_router
from src.modules.vitalia.clinics.api.router import router as clinics_router
from src.modules.vitalia.connections.telegram.api.router import router as telegram_router
from src.modules.vitalia.copilot.api.routes.wizard_onboarding_routes import (
    router as wizard_onboarding_router,
)
from src.modules.vitalia.crm.api.router import router as crm_router
from src.modules.vitalia.fidelizacion.api.router import fidelizacion_router
from src.modules.vitalia.fiscal.api.emit_router import router as emit_router
from src.modules.vitalia.inbox.api.router import router as inbox_router
from src.modules.vitalia.marketing.api.routes import router as marketing_router
from src.modules.vitalia.offer.api.servicios_router import router as servicios_router
from src.modules.vitalia.payments.api.charge_router import router as charge_router
from src.modules.vitalia.sales_agent.api.routers.operator_instruction_router import (
    router as operator_instruction_router,
)
from src.modules.vitalia.scheduling.api.agenda_router import router as agenda_router
from src.modules.vitalia.scheduling.api.availability_router import router as availability_router
from src.modules.vitalia.scheduling.api.notify_router import router as notify_router


@asynccontextmanager
async def _brand_lifespan(_app: FastAPI):
    """Tier-2 (multibrand-graph-runtime 2026-06-22): brand composition root.

    Registers Vitalia's Extension SDK surface at startup so its EP-3 sales_agent tools
    merge into the engine ToolRegistry singleton — the sales_agent graph then dispatches
    Vitalia's own tools (each brand owns its tools). Fail-open: a registration error must
    never block app boot (the engine graph still runs with its base tool set).
    """
    try:
        import asyncio

        from luana_core_extension_sdk._adapters import _SalesAgentToolRegistryAdapter
        from luana_core_extension_sdk.extension_points import ExtensionPointRegistry
        from luana_core_sales_agent.application.tools.registry import get_tool_registry

        from src.modules.vitalia.extensions import register_all
        from src.modules.vitalia.sales_agent.tool_bridge import set_main_loop

        # ESC-17 / Tier 2.4b: capture the main loop so EP-3 sync tool adapters can
        # submit async-DB coroutines back to the loop that owns the shared engine pool
        # (run_coroutine_threadsafe) — eliminates the cross-loop asyncpg trap.
        set_main_loop(asyncio.get_running_loop())

        _ext_registry = ExtensionPointRegistry(
            sales_agent_tool_registry_adapter=_SalesAgentToolRegistryAdapter(get_tool_registry()),
        )
        register_all(_ext_registry)
        _ext_registry.close()  # CC-3 lock after startup
    except Exception:  # noqa: BLE001 — brand-extension wiring must never block app boot
        import structlog

        structlog.get_logger(__name__).exception("brand_extension_registration_failed")
    yield


# redirect_slashes=False is MANDATORY — arch test test_vitalia_response_models_required.py
# also verifies this flag. Default True → 307 POST → Next.js drops body (DDD rule).
app = FastAPI(
    title="Vitalia API",
    description=(
        "Vitalia medical/dental/wellness clinic vertical — Luana Platform brand bootstrap. "
        "Story 11 luana-vitalia-bootstrap."
    ),
    version="0.1.0",
    redirect_slashes=False,
    lifespan=_brand_lifespan,
)

app.include_router(vitalia_router)
# T-be-8: 5 webhook receivers (Stripe + MercadoPago + Clerk + WhatsApp + ManyChat)
app.include_router(webhook_router)
# F1-S9: REUSE core IAM auth router (anti-duplication — deleted vitalia local /me stub).
app.include_router(
    iam_users.router,
    prefix="/api/v1/iam/users",
    tags=["IAM - Users"],
)
app.include_router(crm_router, prefix="/api/v1/crm")
# T-be-services-1: Valeria wizard onboarding (copilot)
app.include_router(wizard_onboarding_router, prefix="/api/v1/vitalia/onboarding")
# T-BE-1 F2-S8: Lisa Staff doctors router — registered BEFORE clinics_router to prevent
# route shadowing: clinics_router has GET /{clinic_id} which would capture /clinics/doctors
# as clinic_id="doctors" if registered first. FastAPI matches in registration order.
app.include_router(doctors_router, prefix="/api/v1/vitalia/clinics/doctors", tags=["staff"])
# T-be-clinics-extension: Clinic branches CRUD (brand extension)
app.include_router(clinics_router, prefix="/api/v1/vitalia/clinics")
# T-be-clinics-extension: Admin helper API (internal, not in OpenAPI schema)
app.include_router(admin_helpers_router, prefix="/api/v1/vitalia/admin")
# T-inbox-be-5: Inbox module — 8 endpoints (send, retract, mode, pause, tools, activity, transcribe, proactive)
app.include_router(inbox_router, prefix="/api/v1/vitalia/inbox")
# T-7 fidelizacion: 9 API endpoints (re_engagement + nps + summary + activity_stream)
app.include_router(fidelizacion_router, prefix="/api/v1/vitalia/fidelizacion")
# T-mk-be-5: Marketing module — 11 endpoints (bowtie + channel + recommendations + attribution + referrals)
app.include_router(marketing_router, prefix="/api/v1/vitalia/marketing")
# T-6 F2-S1: Scheduling agenda router — 5 endpoints (grid, aggregates, detail, create, patch_status)
app.include_router(agenda_router, prefix="/api/v1/scheduling")
# T-BE-3 vitalia-fase2-mateo-nueva-cita: Availability endpoints (check + free-doctors + day-strip)
app.include_router(availability_router, prefix="/api/v1/scheduling")
# T-8 F2-S1: Scheduling notify — template-only WhatsApp + ComplianceService guard + audit log
app.include_router(notify_router, prefix="/api/v1/scheduling")
# T-7 F2-S1: Payments charge router — CobrarSaldo saga (payment + fiscal + audit + idempotency)
app.include_router(charge_router, prefix="/api/v1/payments")
# T-7 F2-S1: Fiscal emit router — standalone fiscal emission retry (saga compensation A6)
app.include_router(emit_router, prefix="/api/v1/fiscal")
# T-2 F2-S7: Brand Studio marca router — 21 endpoints Lisa > Marca sub-tab
app.include_router(marca_router, prefix="/api/v1/lisa/marca", tags=["brand_studio"])
# T-2 vitalia-fase2-lisa-servicios: Offer service catalog router — 16 endpoints Lisa > Servicios
app.include_router(servicios_router, prefix="/api/v1/offer", tags=["offer"])
# T-BE-5 F2-S8: Public doctors router — unauthenticated, allow-list channel guard
app.include_router(public_doctors_router, prefix="/api/public/clinic", tags=["public"])
# T-BE-6 F2-S8: Assets proxy upload router — consume luana-core-assets AssetsService (D-3)
app.include_router(assets_proxy_router, prefix="/api/v1/vitalia/assets", tags=["assets"])
# vitalia-fase2-adrian-inbox (telemetry-404 side-fix): FE growth-studio telemetry ingestion.
# Path is /api/telemetry/* (NOT /api/v1/*) — matches mateo/lib/telemetry.ts + dev-app tunnel ^/api/.* → BE.
app.include_router(telemetry_router, prefix="/api/telemetry", tags=["telemetry"])
# vitalia-fase2-adrian-inbox (audit-log-404 twin-fix): FE PHI-read audit ingestion (AuditedSection).
# Serves /api/v1/vitalia/audit-log — wires the FE beacon to AsyncAuditWriter (hipaa-lite dual filter).
app.include_router(audit_log_router, prefix="/api/v1/vitalia", tags=["audit"])

app.include_router(account_router, prefix="/api/v1/clinics/account", tags=["account"])
# T-BE-1 vitalia-fase2-adrian-canal-inbound: Telegram inbound webhook receiver.
# Route: POST /api/v1/connections/telegram/webhook
# Secret validation + update_id dedup + tenant resolve + engine dispatch.
app.include_router(telegram_router, prefix="/api/v1/connections/telegram", tags=["connections"])
# T-BE-3 vitalia-fase2-adrian-canal-inbound: Operator instruction endpoint for Adrián.
# Route: POST /api/v1/adrian/conversations/{conversation_id}/instruction
# Sets per-conversation steering instruction persisted to metadata_info JSONB.
app.include_router(operator_instruction_router, prefix="/api/v1/adrian", tags=["adrian"])


class HealthResponse(BaseModel):
    """Liveness probe response DTO."""

    status: str
    brand: str
    version: str


@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health() -> HealthResponse:
    """Liveness probe — used by Docker HEALTHCHECK + smoke checks."""
    return HealthResponse(status="ok", brand="vitalia", version=app.version)


@app.get("/api/health", response_model=HealthResponse, tags=["meta"])
async def api_health() -> HealthResponse:
    """API-prefixed health endpoint — used by post_deploy_smoke.sh + Clerk middleware public routes.

    Clerk middleware whitelist includes /api/health (no redirect).
    Idempotent: returns same payload as /health for compatibility.
    T-5 vitalia-auth-base-functional — SC-17 post-deploy smoke verify.
    """
    return HealthResponse(status="ok", brand="vitalia", version=app.version)
