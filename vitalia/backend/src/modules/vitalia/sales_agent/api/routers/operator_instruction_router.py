# cap: sales_agent.honor-mode-bridge
# story-origin: vitalia-fase2-adrian-canal-inbound T-BE-3
"""Operator instruction router — POST /api/v1/adrian/conversations/{id}/instruction.

Thin API layer (no business logic here):
  1. Decode auth token + resolve ClinicContext (role check).
  2. Validate request DTO.
  3. Build OperatorInstructionService with injected deps.
  4. Call service.set_instruction().
  5. Map domain exceptions → HTTP errors.
  6. Return SetOperatorInstructionResponse.

V-NF-4: response_model= is MANDATORY on every endpoint.
PHI dual-filter: tenant_id AND clinic_id on every service call.
HIPAA-lite: audit log written SYNC by service layer (V-NF-3) — not here.
AC-13: service raises ConversationNotInDecideModeError if not in decide mode → 409.

redirect_slashes=False is set on the FastAPI *app* in main.py (NOT here).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_session_committing
from src.modules.vitalia._shared.auth.rbac import PHIAccessDeniedError
from src.modules.vitalia.audit.audit_writer import AsyncAuditWriter
from src.modules.vitalia.crm.infrastructure.persistence.activity_event_repository import (
    ActivityEventRepository,
)
from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
    ConversationRepository,
)
from src.modules.vitalia.iam.application.services.clinic_resolver import (
    ClinicContext,
    ClinicResolver,
    MissingAuthHeaderError,
    RoleNotFoundError,
    UserNotFoundError,
)
from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
    ClerkJwtDecoder,
    JwtDecodeError,
)
from src.modules.vitalia.sales_agent.api.dtos.operator_instruction_dtos import (
    SetOperatorInstructionRequest,
    SetOperatorInstructionResponse,
)
from src.modules.vitalia.sales_agent.application.services.operator_instruction_bridge import (
    OperatorInstructionBridge,
)
from src.modules.vitalia.sales_agent.application.services.operator_instruction_service import (
    ConversationNotInDecideModeError,
    OperatorInstructionService,
)
from src.modules.vitalia.sales_agent.infrastructure.adapters.checkpoint_instruction_adapter import (
    CheckpointInstructionAdapter,
)
from src.modules.vitalia.sales_agent.infrastructure.adapters.checkpoint_instruction_bridge_adapter import (
    CheckpointInstructionBridgeAdapter,
)

logger = structlog.get_logger()

# Roles allowed to issue operator instructions (front-desk + clinic admin + owner)
# Matches _INBOX_OPERATOR_ROLES pattern from inbox router (PHI + operator gates)
_INSTRUCTION_ROLES = frozenset({"doctor", "nurse", "admin_clinic", "owner", "receptionist"})

# Header type aliases (consistent with inbox router)
AuthorizationHeader = Annotated[str, Header(alias="Authorization")]
TenantIdHeader = Annotated[str, Header(alias="X-Tenant-ID")]
ClinicIdHeader = Annotated[str, Header(alias="X-Clinic-ID")]

router = APIRouter(tags=["adrian"])


def _get_clinic_resolver() -> ClinicResolver:
    """DI factory for ClinicResolver (stateless, construct per-request)."""
    return ClinicResolver(decoder=ClerkJwtDecoder())


async def _resolve_ctx(
    authorization: str,
    tenant_id_str: str,
    clinic_id_str: str,
    db: AsyncSession,
) -> ClinicContext:
    """Resolve and validate auth context. Raises HTTPException on failure."""
    resolver = _get_clinic_resolver()
    try:
        ctx = await resolver.async_resolve(
            token=authorization,
            session=db,
            tenant_id_str=tenant_id_str,
            clinic_id_str=clinic_id_str,
        )
    except JwtDecodeError as exc:
        raise HTTPException(status_code=401, detail="Token JWT inválido o expirado.") from exc
    except (MissingAuthHeaderError,) as exc:
        raise HTTPException(status_code=401, detail="Encabezado de autorización faltante.") from exc
    except UserNotFoundError as exc:
        raise HTTPException(status_code=403, detail="Usuario no registrado en esta clínica.") from exc
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=403, detail="Rol de usuario no encontrado.") from exc

    if ctx.role not in _INSTRUCTION_ROLES:
        raise HTTPException(
            status_code=403,
            detail=f"Rol '{ctx.role}' no tiene acceso para instruir a Adrián.",
        )
    return ctx


@router.post(
    "/conversations/{conversation_id}/instruction",
    response_model=SetOperatorInstructionResponse,
    status_code=200,
    summary="Instruir a Adrián para una conversación",
    description=(
        "Persiste una instrucción del operador (recepcionista/dueño/etc.) que "
        "Adrián leerá en todos los turnos siguientes de esa conversación. "
        "La instrucción se almacena en metadata_info JSONB del checkpoint activo. "
        "Solo disponible cuando la conversación está en modo 'decide'. "
        "Audit row escrito de forma sincrónica (HIPAA-lite V-NF-3)."
    ),
)
async def set_operator_instruction(
    conversation_id: UUID,
    request: SetOperatorInstructionRequest,
    authorization: AuthorizationHeader,
    tenant_id: TenantIdHeader,
    clinic_id: ClinicIdHeader,
    db: AsyncSession = Depends(get_async_session_committing),
) -> SetOperatorInstructionResponse:
    """POST /api/v1/adrian/conversations/{conversation_id}/instruction.

    Validates that the conversation is in 'decide' mode (AC-13), then:
    1. Persists instruction to agent_state_checkpoints.metadata_info JSONB.
    2. Writes sync audit row (HIPAA-lite V-NF-3).
    3. Writes NON-PHI activity event "La recepción instruyó a Adrián" (RN-15).

    The lead NEVER sees the instruction text (RN-15 — internal steering only).
    """
    tenant_uuid = UUID(tenant_id)
    clinic_uuid = UUID(clinic_id)

    # Resolve auth context
    ctx = await _resolve_ctx(authorization, tenant_id, clinic_id, db)

    # Build service with injected deps. T-AG-1: the OperatorInstructionBridge mirrors
    # the persisted instruction into the engine's volatile resume_objective seam so the
    # next Adrián turn injects [INSTRUCCION DEL OPERADOR] (SC-8 end-to-end wiring).
    svc = OperatorInstructionService(
        conv_repo=ConversationRepository(session=db),
        checkpoint_port=CheckpointInstructionAdapter(session=db),
        audit_writer=AsyncAuditWriter(session=db),
        activity_repo=ActivityEventRepository(session=db),
        bridge_to_turn=OperatorInstructionBridge(
            checkpoint_bridge_port=CheckpointInstructionBridgeAdapter(session=db),
        ),
    )

    try:
        persisted = await svc.set_instruction(
            tenant_id=tenant_uuid,
            clinic_id=clinic_uuid,
            conversation_id=conversation_id,
            instruction=request.instruction,
            actor_user_id=ctx.user_id,
        )
    except ConversationNotInDecideModeError as exc:
        raise HTTPException(
            status_code=409,
            detail=("La conversación no está en modo 'decide'. Cambia el modo antes de instruir a Adrián."),
        ) from exc
    except PHIAccessDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    now_iso = datetime.now(timezone.utc).isoformat()
    status = "set" if persisted else "no_active_checkpoint"

    logger.info(
        "operator_instruction_endpoint.ok",
        tenant_id=tenant_id,
        conversation_id=str(conversation_id),
        persisted=persisted,
    )

    return SetOperatorInstructionResponse(
        conversation_id=conversation_id,
        status=status,
        persisted_at=now_iso,
    )
