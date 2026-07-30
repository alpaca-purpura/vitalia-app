"""Unit tests for ClinicService — business logic + slug uniqueness.

TDD: RED tests defined per vitalia-adopt-luana-core-iam story.

downstream-regression-na: brand-local clinics service tests
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from src.modules.vitalia.clinics.domain.clinic import Clinic


def _make_domain_clinic(
    tenant_id: UUID | None = None,
    slug: str = "aurora-norte",
    is_active: bool = True,
) -> Clinic:
    return Clinic(
        id=uuid4(),
        tenant_id=tenant_id or uuid4(),
        name="Clínica Aurora",
        slug=slug,
        country="AR",
        timezone="America/Argentina/Buenos_Aires",
        plan_tier="starter",
        is_active=is_active,
        onboarding_completed=False,
        created_at=datetime.now(tz=timezone.utc),
    )


class TestClinicServiceGetClinic:
    """get_clinic — tenant-scoped retrieval."""

    @pytest.mark.anyio
    async def test_get_clinic_returns_clinic(self) -> None:
        """Returns Clinic when found for tenant."""
        from src.modules.vitalia.clinics.application.clinic_service import ClinicService
        from src.modules.vitalia.clinics.infrastructure.repositories.clinic_repository import (
            ClinicRepository,
        )

        tenant_id = uuid4()
        clinic = _make_domain_clinic(tenant_id=tenant_id)

        mock_repo = AsyncMock(spec=ClinicRepository)
        mock_repo.get_by_id = AsyncMock(return_value=clinic)

        mock_session = AsyncMock()
        service = ClinicService(mock_session)
        service._repo = mock_repo  # type: ignore[attr-defined]

        with MagicMock():
            # Patch repo instantiation
            pass

        # Create service with patched repo
        from unittest.mock import patch

        with patch(
            "src.modules.vitalia.clinics.application.clinic_service.ClinicRepository",
            return_value=mock_repo,
        ):
            svc = ClinicService(mock_session)
            result = await svc.get_clinic(str(tenant_id), clinic.id)

        assert result is not None
        assert result.id == clinic.id

    @pytest.mark.anyio
    async def test_get_clinic_returns_none_when_not_found(self) -> None:
        """Returns None when clinic not found for tenant."""
        from unittest.mock import patch

        from src.modules.vitalia.clinics.application.clinic_service import ClinicService
        from src.modules.vitalia.clinics.infrastructure.repositories.clinic_repository import (
            ClinicRepository,
        )

        mock_repo = AsyncMock(spec=ClinicRepository)
        mock_repo.get_by_id = AsyncMock(return_value=None)

        mock_session = AsyncMock()

        with patch(
            "src.modules.vitalia.clinics.application.clinic_service.ClinicRepository",
            return_value=mock_repo,
        ):
            svc = ClinicService(mock_session)
            result = await svc.get_clinic(str(uuid4()), uuid4())

        assert result is None


class TestClinicServiceListClinics:
    """list_clinics — returns tenant-scoped list."""

    @pytest.mark.anyio
    async def test_list_clinics_returns_all_for_tenant(self) -> None:
        """Returns all clinics for tenant."""
        from unittest.mock import patch

        from src.modules.vitalia.clinics.application.clinic_service import ClinicService
        from src.modules.vitalia.clinics.infrastructure.repositories.clinic_repository import (
            ClinicRepository,
        )

        tenant_id = uuid4()
        clinics = [
            _make_domain_clinic(tenant_id=tenant_id, slug="aurora-norte"),
            _make_domain_clinic(tenant_id=tenant_id, slug="aurora-sur"),
        ]

        mock_repo = AsyncMock(spec=ClinicRepository)
        mock_repo.list_by_tenant = AsyncMock(return_value=clinics)

        mock_session = AsyncMock()

        with patch(
            "src.modules.vitalia.clinics.application.clinic_service.ClinicRepository",
            return_value=mock_repo,
        ):
            svc = ClinicService(mock_session)
            result = await svc.list_clinics(str(tenant_id))

        assert len(result) == 2
        assert {c.slug for c in result} == {"aurora-norte", "aurora-sur"}


class TestClinicServiceCreateClinic:
    """create_clinic — slug uniqueness enforcement."""

    @pytest.mark.anyio
    async def test_create_clinic_succeeds_when_slug_unique(self) -> None:
        """Creates clinic when slug is not taken for tenant."""
        from unittest.mock import patch

        from src.modules.vitalia.clinics.application.clinic_service import ClinicService
        from src.modules.vitalia.clinics.infrastructure.repositories.clinic_repository import (
            ClinicRepository,
        )

        tenant_id = uuid4()
        created = _make_domain_clinic(tenant_id=tenant_id, slug="aurora-norte")

        mock_repo = AsyncMock(spec=ClinicRepository)
        mock_repo.get_by_slug = AsyncMock(return_value=None)  # slug free
        mock_repo.create = AsyncMock(return_value=created)

        mock_session = AsyncMock()

        with patch(
            "src.modules.vitalia.clinics.application.clinic_service.ClinicRepository",
            return_value=mock_repo,
        ):
            svc = ClinicService(mock_session)
            result = await svc.create_clinic(
                tenant_id=str(tenant_id),
                name="Clínica Aurora Norte",
                slug="aurora-norte",
                country="AR",
                timezone="America/Argentina/Buenos_Aires",
                plan_tier="starter",
            )

        assert result.slug == "aurora-norte"
        mock_repo.create.assert_called_once()

    @pytest.mark.anyio
    async def test_create_clinic_raises_value_error_when_slug_taken(self) -> None:
        """Raises ValueError when slug already exists for tenant."""
        from unittest.mock import patch

        from src.modules.vitalia.clinics.application.clinic_service import ClinicService
        from src.modules.vitalia.clinics.infrastructure.repositories.clinic_repository import (
            ClinicRepository,
        )

        tenant_id = uuid4()
        existing = _make_domain_clinic(tenant_id=tenant_id, slug="aurora-norte")

        mock_repo = AsyncMock(spec=ClinicRepository)
        mock_repo.get_by_slug = AsyncMock(return_value=existing)  # slug taken!

        mock_session = AsyncMock()

        with patch(
            "src.modules.vitalia.clinics.application.clinic_service.ClinicRepository",
            return_value=mock_repo,
        ):
            svc = ClinicService(mock_session)
            with pytest.raises(ValueError, match="slug"):
                await svc.create_clinic(
                    tenant_id=str(tenant_id),
                    name="Otra Clínica Aurora",
                    slug="aurora-norte",  # duplicate slug!
                    country="AR",
                    timezone="America/Argentina/Buenos_Aires",
                    plan_tier="growth",
                )

        mock_repo.create.assert_not_called()
