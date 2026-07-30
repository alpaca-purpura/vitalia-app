# downstream-regression-na: engine abstract base; brand subclasses own their dual-filter tests
"""CompoundScopeRepositoryBase — dual-scope async repository base class.

Provides the multi-tenant compound isolation pattern where every query MUST
filter by two axes simultaneously:

  1. ``tenant_id``: root multitenant isolation (per .claude/rules/tenant-isolation.md)
  2. ``scope_id``: brand-specific secondary isolation axis

The scope axis is named generically ``scope_id`` at the engine level. Each brand
consumer assigns semantic meaning via the ``scope_field`` constructor argument:

  - vitalia  → ``scope_field="clinic_id"``   (HIPAA-lite clinic isolation)
  - fitflow  → ``scope_field="studio_id"``   (multi-studio gym chain)
  - retailly → ``scope_field="store_id"``    (multi-store D2C)
  - comunify → ``scope_field="cohort_id"``   (multi-cohort creator economy)
  - fixia    → ``scope_field="technician_zone_id"`` (geo-zone isolation)
  - saasora  → ``scope_field="workspace_id"``  (multi-workspace SaaS)

Usage::

    from luana_core_platform.repositories.compound_scope_repository import (
        CompoundScopeRepositoryBase,
    )

    class PatientRepository(CompoundScopeRepositoryBase[PatientModel, UUID]):
        MODEL = PatientModel

        def __init__(self, *, session: AsyncSession) -> None:
            super().__init__(session=session, scope_field="clinic_id")

Promotion origin:
  vitalia/_shared/repositories/phi_repository.py (brand-local PhiRepositoryBase).
  Reframed brand-agnostically: "clinic" → "scope" (engine is brand-neutral).
  Lifted to engine Slice 1 per proposal 2026-05-20-core-platform-extensions-slice-1.md.
"""

from __future__ import annotations

from typing import Any, ClassVar, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")
IdT = TypeVar("IdT")


class MissingScopeFieldError(AttributeError):
    """Raised when MODEL class attribute or scope field is not properly configured.

    Subclasses MUST define a ``MODEL`` class attribute pointing to the
    SQLAlchemy mapped class. The ``scope_field`` string MUST match an attribute
    name on that model.
    """

    def __init__(self, message: str | None = None) -> None:
        default = (
            "CompoundScopeRepositoryBase subclass is missing required configuration. "
            "Subclass MUST define ``MODEL`` as a class attribute pointing to the "
            "SQLAlchemy mapped model class. "
            "Example: class MyRepo(CompoundScopeRepositoryBase[MyModel, UUID]): "
            "    MODEL = MyModel"
        )
        super().__init__(message or default)


class CompoundScopeRepositoryBase(Generic[ModelT, IdT]):
    """Abstract async repository base with dual-scope isolation.

    Enforces two mandatory query filters on every database operation:
      - ``tenant_id``: root multitenant isolation
      - ``scope_id``: brand-specific secondary axis (e.g. clinic_id, studio_id)

    All queries automatically exclude soft-deleted rows (``deleted_at IS NULL``).

    Subclass contract:
      1. Define ``MODEL: type[ModelT]`` as a class attribute.
      2. Pass ``scope_field`` to ``super().__init__()`` with the attribute name
         that matches the secondary scope column on your model.
      3. Every custom query method MUST apply both filters — use ``get_by_id``
         and ``list_for_scope`` as reference implementations.

    Type parameters:
      ``ModelT``: SQLAlchemy mapped class (must have ``id``, ``tenant_id``,
                  ``deleted_at`` columns, and the column named by ``scope_field``).
      ``IdT``:    Type of the primary key (typically ``UUID``).

    Args:
        session: Async SQLAlchemy session.
        scope_field: Name of the secondary scope attribute on MODEL.
                     Default ``"scope_id"`` for generic axes.
                     Brand consumers set brand-specific names:
                     ``"clinic_id"``, ``"studio_id"``, ``"store_id"``, etc.

    Raises:
        MissingScopeFieldError: If ``MODEL`` class attribute is not defined
                                when a method is called.
        AttributeError: If ``scope_field`` does not match any attribute on MODEL.

    Example::

        class VisitRepository(CompoundScopeRepositoryBase[VisitModel, UUID]):
            MODEL = VisitModel

            def __init__(self, *, session: AsyncSession) -> None:
                super().__init__(session=session, scope_field="clinic_id")

            async def get_todays_visits(
                self, *, tenant_id: UUID, clinic_id: UUID
            ) -> list[VisitModel]:
                scope_attr = getattr(self.MODEL, self._scope_field)
                stmt = (
                    select(self.MODEL)
                    .where(self.MODEL.tenant_id == tenant_id)
                    .where(scope_attr == clinic_id)
                    .where(self.MODEL.deleted_at.is_(None))
                    .where(...)  # domain-specific filters
                )
                result = await self._session.execute(stmt)
                return list(result.scalars().all())
    """

    MODEL: ClassVar[Any]  # subclass MUST define

    def __init__(
        self,
        *,
        session: AsyncSession,
        scope_field: str = "scope_id",
    ) -> None:
        """Initialize the repository.

        Args:
            session: Async SQLAlchemy session (injected by DI container).
            scope_field: Attribute name on MODEL for the secondary scope axis.
                         Default ``"scope_id"``. Brand consumers override with
                         their semantic name (``"clinic_id"``, ``"studio_id"``, etc.).
        """
        self._session = session
        self._scope_field = scope_field

    def _get_model(self) -> Any:  # noqa: ANN401
        """Retrieve MODEL class attribute, raising a clear error if missing.

        Returns:
            The SQLAlchemy mapped model class.

        Raises:
            MissingScopeFieldError: If MODEL is not defined on the subclass.
        """
        model = getattr(type(self), "MODEL", None)
        if model is None:
            raise MissingScopeFieldError(
                f"{type(self).__name__} does not define required class attribute 'MODEL'. "
                "Add 'MODEL = YourSQLAlchemyModel' to the subclass body."
            )
        return model

    def _scope_attr(self) -> Any:  # noqa: ANN401
        """Return the SQLAlchemy mapped column for the scope field.

        Returns:
            Column attribute descriptor for self._scope_field on MODEL.

        Raises:
            AttributeError: If scope_field does not exist on MODEL.
        """
        model = self._get_model()
        attr = getattr(model, self._scope_field, None)
        if attr is None:
            msg = (
                f"{type(self).__name__}: scope_field={self._scope_field!r} "
                f"does not exist on MODEL={model.__name__!r}. "
                "Verify the column name matches exactly."
            )
            raise AttributeError(msg)
        return attr

    async def get_by_id(
        self,
        *,
        id: IdT,
        tenant_id: UUID,
        scope_id: UUID,
    ) -> ModelT | None:
        """Retrieve a single row by primary key with dual-scope filter.

        Applies three mandatory WHERE clauses:
          - ``id == id``
          - ``tenant_id == tenant_id``
          - ``{scope_field} == scope_id``

        Soft-deleted rows (``deleted_at IS NOT NULL``) are excluded.

        Args:
            id: Primary key of the entity.
            tenant_id: Tenant UUID for root isolation.
            scope_id: Scope UUID for secondary isolation (e.g. clinic_id value).

        Returns:
            The model instance, or None if not found or not accessible under
            this (tenant_id, scope_id) combination.
        """
        model = self._get_model()
        scope_attr = self._scope_attr()
        stmt = (
            select(model)
            .where(model.id == id)
            .where(model.tenant_id == tenant_id)
            .where(scope_attr == scope_id)
            .where(model.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()  # type: ignore[return-value]

    async def list_for_scope(
        self,
        *,
        tenant_id: UUID,
        scope_id: UUID,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[ModelT]:
        """List all non-deleted rows for the given (tenant_id, scope_id) pair.

        Applies two mandatory WHERE clauses:
          - ``tenant_id == tenant_id``
          - ``{scope_field} == scope_id``

        Soft-deleted rows are excluded. Results are ordered by insertion order
        (no explicit ORDER BY — subclass may override for deterministic ordering).

        Args:
            tenant_id: Tenant UUID for root isolation.
            scope_id: Scope UUID for secondary isolation.
            limit: Maximum number of rows to return. None returns all matching rows.
            offset: Number of rows to skip (for pagination). Default 0.

        Returns:
            List of model instances (empty list if none found).
        """
        model = self._get_model()
        scope_attr = self._scope_attr()
        stmt = (
            select(model)
            .where(model.tenant_id == tenant_id)
            .where(scope_attr == scope_id)
            .where(model.deleted_at.is_(None))
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())  # type: ignore[return-value]
