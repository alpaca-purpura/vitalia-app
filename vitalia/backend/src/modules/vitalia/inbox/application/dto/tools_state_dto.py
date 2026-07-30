# cap: agentic.medical-agentic-tools
# story-origin: TBD
"""ToolsState DTOs — vitalia inbox application layer.

downstream-regression-na: brand-local vitalia inbox DTO
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ToolState(BaseModel):
    """Single tool availability record."""

    model_config = ConfigDict(from_attributes=True)

    tool_name: str
    enabled: bool
    last_used_at: datetime | None = None
    display_name_es: str


class ToolsStateResponse(BaseModel):
    """Response for GET /inbox/conversations/{conv_id}/tools."""

    model_config = ConfigDict(from_attributes=True)

    tools: list[ToolState]
    read_only: bool = True  # Slice 1: read-only
