# cap: sales_agent.honor-mode-bridge
# story-origin: vitalia-fase2-adrian-canal-inbound T-BE-3
"""DTOs for the set-operator-instruction endpoint.

V-NF-4: response_model= is mandatory on every endpoint — these DTOs are the
response model and request body for:
  POST /api/v1/adrian/conversations/{conversation_id}/instruction

PII: SetOperatorInstructionResponse MUST NOT expose PHI. Instruction text is
operator-authored (non-PHI commercial context) but is stored in the checkpoint,
not returned in the response body (RN-15: lead never sees it).
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SetOperatorInstructionRequest(BaseModel):
    """Request body for POST .../instruction.

    instruction: operator-authored commercial text telling Adrián how to behave
    in subsequent turns. Spanish neutro (no PHI, no clinical data).

    Pydantic v2 with validation: empty / whitespace-only strings rejected.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    instruction: str = Field(
        ...,
        min_length=1,
        description="Texto de instrucción para Adrián (no PHI, texto comercial).",
    )

    @field_validator("instruction")
    @classmethod
    def instruction_not_blank(cls, v: str) -> str:
        """Reject whitespace-only strings after strip."""
        if not v.strip():
            raise ValueError("La instrucción no puede estar vacía o solo contener espacios.")
        return v


class SetOperatorInstructionResponse(BaseModel):
    """Response model for POST .../instruction (V-NF-4: response_model= mandatory).

    Returns minimal acknowledgment — the instruction text is NOT echoed back
    (RN-15: the lead must never see the operator's steering instruction).
    """

    model_config = ConfigDict(from_attributes=True)

    conversation_id: UUID
    status: str  # 'set' | 'no_active_checkpoint'
    persisted_at: str  # ISO-8601 UTC timestamp of the write
