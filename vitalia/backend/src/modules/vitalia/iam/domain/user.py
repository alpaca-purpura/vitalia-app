# cap: iam.iam-scaffold-slice-1
# story-origin: TBD
"""Vitalia User domain entity.

Domain layer — pure Python dataclass, no ORM imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.modules.vitalia.iam.domain.role import VitaliaRole


@dataclass(frozen=True)
class User:
    """Authenticated user context in Vitalia.

    Represents the resolved identity from a JWT token.
    Immutable value object — created fresh per request.
    """

    user_id: str
    tenant_id: UUID
    clinic_id: UUID
    role: VitaliaRole
    email: str
    name: str
