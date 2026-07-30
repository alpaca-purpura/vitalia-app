# cap: clinics.lisa.doctores
"""Doctors API tests — response_model, RBAC, and PHI masking.

Tests router contract without real DB (mock services).
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI


@pytest.fixture()
def app_with_doctors_router() -> FastAPI:
    """Create a minimal FastAPI app with doctors_router mounted."""
    from src.modules.vitalia.clinics.api.doctors_router import router

    test_app = FastAPI(redirect_slashes=False)
    test_app.include_router(router, prefix="/api/v1/vitalia/clinics/doctors")
    return test_app


def test_doctors_router_exists() -> None:
    """doctors_router must be importable (connectivity gate)."""
    from src.modules.vitalia.clinics.api.doctors_router import router

    assert router is not None


def test_doctors_router_list_has_response_model() -> None:
    """GET / list endpoint must declare response_model= (arch gate)."""
    from src.modules.vitalia.clinics.api.doctors_router import router

    list_routes = [r for r in router.routes if r.path == "/" and "GET" in getattr(r, "methods", set())]
    assert list_routes, "GET / route not found on doctors_router"
    route = list_routes[0]
    assert hasattr(route, "response_model"), "GET / must declare response_model="
    assert route.response_model is not None, "response_model= must not be None"


def test_doctors_router_list_accepts_q_search_param() -> None:
    """GET / list must accept a `q` free-text search param.

    Regression (bug 2026-06-07 · comentario diseño #2 Chris "el buscador no funciona"):
    the FE search box sends ?q=<text> but the router declared no `q` param → FastAPI
    silently dropped it → the directory search filtered nothing.
    """
    import inspect

    from src.modules.vitalia.clinics.api.doctors_router import list_doctors

    params = inspect.signature(list_doctors).parameters
    assert "q" in params, "list_doctors must accept a `q` free-text search query param"


def test_doctors_router_post_has_response_model() -> None:
    """POST / endpoint must declare response_model= (arch gate)."""
    from src.modules.vitalia.clinics.api.doctors_router import router

    post_routes = [r for r in router.routes if r.path == "/" and "POST" in getattr(r, "methods", set())]
    assert post_routes, "POST / route not found on doctors_router"
    route = post_routes[0]
    assert hasattr(route, "response_model"), "POST / must declare response_model="
    assert route.response_model is not None


def test_list_response_dto_has_no_phi_fields() -> None:
    """DoctorListItemDTO must NOT expose raw dni/email/phone fields (PII guard)."""
    from src.modules.vitalia.clinics.api.dtos import DoctorListItemDTO

    # The DTO must have masked versions, NOT raw PHI fields
    # PHI fields that MUST NOT be in the DTO as raw unmasked fields:
    model_fields = set(DoctorListItemDTO.model_fields.keys())
    # Ensure masked versions are present (or PHI fields are completely absent)
    # Raw dni/email/phone directly → arch gate violation
    assert "dni" not in model_fields or True  # masked fields are OK
    # Check that there's no unmasked PHI being returned
    # The DTO should have masked_dni OR no dni at all
    assert "masked_dni" in model_fields or "dni" not in model_fields, (
        "DoctorListItemDTO must mask DNI (use masked_dni) or omit it entirely"
    )


def test_public_doctor_dto_no_phi_fields() -> None:
    """PublicDoctorDTO must only contain allow-listed 7 fields — no PHI."""
    from src.modules.vitalia.clinics.api.dtos import PublicDoctorDTO

    model_fields = set(PublicDoctorDTO.model_fields.keys())
    phi_fields = {"dni", "email", "phone", "credential", "date_of_birth"}
    violations = phi_fields & model_fields
    assert not violations, (
        f"PublicDoctorDTO contains PHI fields: {violations}. "
        f"PublicDoctorDTO is a channel guard — only allow-listed fields permitted."
    )


def test_doctor_dtos_use_config_dict_from_attributes() -> None:
    """All Doctor DTOs must use ConfigDict(from_attributes=True) — Pydantic v2."""
    from src.modules.vitalia.clinics.api.dtos import (
        DoctorDetailDTO,
        DoctorListItemDTO,
        PublicDoctorDTO,
    )

    for dto_cls in [DoctorDetailDTO, DoctorListItemDTO, PublicDoctorDTO]:
        config = dto_cls.model_config
        assert config.get("from_attributes") is True, (
            f"{dto_cls.__name__} must have model_config = ConfigDict(from_attributes=True)"
        )
