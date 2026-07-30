"""Prompt Version SQLAlchemy model."""

import uuid

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func


class PromptVersion(Base):
    """Prompt Version."""

    __tablename__ = "prompt_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String, index=True, nullable=False)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)  # The actual prompt template
    is_active = Column(Boolean, default=True)
    change_reason = Column(String, nullable=True)
    author_id = Column(String, nullable=True)  # User ID or 'system'
    metadata_info = Column(JSONB, default=dict)  # target_node, target_model, etc.

    # Tenant scoping (ESC-6): NULL = system default (fallback path in PromptLoader._get_from_db).
    # No FK to tenants (engine model stays decoupled from platform tenants table — matches MessageModel).
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
