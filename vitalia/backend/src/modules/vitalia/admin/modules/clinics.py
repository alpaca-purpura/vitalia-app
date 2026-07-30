# cap: admin.clinics-crud
# story-origin: TBD
"""Admin module — Clinic branches management for Vitalia.

Uses ClinicService (application layer) indirectly via raw sync query
since ClinicService is async (FastAPI context). Admin uses sync session
(Streamlit context). Queries vitalia_clinic_branches directly via SQLA 2.0.

HIPAA invariants:
  - Dual filter (tenant_id + clinic_id) on all PHI-adjacent queries
  - Audit log written SYNC via write_audit_log_sync
  - No raw SQL to phantom tables (vitalia_clinics, vitalia_tenants)
  - All queries use SQLA 2.0 select() idiom
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger()


def render_clinics_page() -> None:
    """Render the Clinic Branches management page in Streamlit.

    Tab layout:
        Tab 1 — Listado de sucursales
        Tab 2 — Registrar nueva sucursal
    """
    try:
        import streamlit as st  # noqa: PLC0415
    except ImportError:
        logger.error("streamlit_not_installed")
        raise

    st.header("Sucursales Clínicas")
    st.caption("Gestión de sucursales registradas en Vitalia.")

    tab_list, tab_crear = st.tabs(["Listado", "Registrar sucursal"])

    with tab_list:
        _render_clinic_list()

    with tab_crear:
        _render_create_clinic_form()


def _render_clinic_list() -> None:
    """Render list of clinic branches via SQLA 2.0 select()."""
    try:
        import streamlit as st  # noqa: PLC0415
    except ImportError:
        return

    from sqlalchemy import select  # noqa: PLC0415

    from src.modules.vitalia.admin._shared.db import get_sync_session  # noqa: PLC0415
    from src.modules.vitalia.clinics.infrastructure.models.clinic_model import ClinicModel  # noqa: PLC0415

    st.subheader("Sucursales activas")

    try:
        with get_sync_session() as session:
            models = (
                session.execute(
                    select(ClinicModel)
                    .where(ClinicModel.deleted_at.is_(None))
                    .order_by(ClinicModel.created_at.desc())
                    .limit(100)
                )
                .scalars()
                .all()
            )

        if not models:
            st.info("No hay sucursales registradas aún.")
            return

        data = [
            {
                "ID": str(m.id),
                "Tenant ID": str(m.tenant_id),
                "Nombre": m.name,
                "Slug": m.slug,
                "País": m.country,
                "Plan": m.plan_tier,
                "Activa": "Sí" if m.is_active else "No",
                "Creada": m.created_at.strftime("%Y-%m-%d") if m.created_at else "—",
            }
            for m in models
        ]
        st.dataframe(data, use_container_width=True)

    except Exception as exc:  # noqa: BLE001
        logger.error("admin_clinic_list_error", error=str(exc))
        st.error(f"Error al cargar sucursales: {exc}")


def _render_create_clinic_form() -> None:
    """Render clinic branch creation form.

    Links to an existing tenant via slug lookup.
    Writes audit log SYNC via write_audit_log_sync.
    """
    try:
        import streamlit as st  # noqa: PLC0415
    except ImportError:
        return

    import uuid as uuid_mod  # noqa: PLC0415

    from luana_core_iam.infrastructure.repositories.tenant_repository import (  # noqa: PLC0415
        TenantRepository,
    )
    from sqlalchemy import select  # noqa: PLC0415

    from src.modules.vitalia.admin._shared.db import get_sync_session  # noqa: PLC0415
    from src.modules.vitalia.audit.audit_writer import write_audit_log_sync  # noqa: PLC0415
    from src.modules.vitalia.clinics.infrastructure.models.clinic_model import ClinicModel  # noqa: PLC0415

    st.subheader("Registrar nueva sucursal")
    st.caption("Vincula una sucursal clínica a un tenant existente.")

    with st.form("form_crear_sucursal", clear_on_submit=False):
        tenant_slug = st.text_input("Slug del tenant *", placeholder="aurora-dental-ar")
        clinic_name = st.text_input("Nombre de la sucursal *", placeholder="Clínica Aurora — Sucursal Norte")
        clinic_slug = st.text_input("Slug de la sucursal *", placeholder="aurora-norte")
        country = st.selectbox("País *", options=["AR", "MX", "CO", "CL", "PE", "BR", "UY", "EC"])
        timezone_opt = st.selectbox(
            "Zona horaria *",
            options=[
                "America/Argentina/Buenos_Aires",
                "America/Mexico_City",
                "America/Bogota",
                "America/Santiago",
                "America/Lima",
                "America/Sao_Paulo",
                "America/Montevideo",
                "America/Guayaquil",
            ],
        )
        plan_tier = st.selectbox("Plan", options=["starter", "growth", "scale"])
        submitted = st.form_submit_button("Registrar sucursal")

    if not submitted:
        return

    errors: list[str] = []
    if not tenant_slug.strip():
        errors.append("El slug del tenant es obligatorio.")
    if not clinic_name.strip():
        errors.append("El nombre de la sucursal es obligatorio.")
    if not clinic_slug.strip():
        errors.append("El slug de la sucursal es obligatorio.")

    if errors:
        for err in errors:
            st.error(err)
        return

    _t_slug = tenant_slug.strip().lower()
    _c_slug = clinic_slug.strip().lower()
    _name = clinic_name.strip()
    admin_user_id = str(uuid_mod.uuid4())

    try:
        with get_sync_session() as session:
            tenant_repo = TenantRepository(session)
            tenant = tenant_repo.get_by_slug(_t_slug)

            if not tenant:
                st.error(f"No se encontró un tenant con slug '{_t_slug}'.")
                return

            # Check slug uniqueness within tenant
            existing = (
                session.execute(
                    select(ClinicModel)
                    .where(ClinicModel.tenant_id == tenant.id)
                    .where(ClinicModel.slug == _c_slug)
                    .where(ClinicModel.deleted_at.is_(None))
                )
                .scalars()
                .first()
            )

            if existing:
                st.warning(f"Ya existe una sucursal con slug '{_c_slug}' para este tenant.")
                return

            clinic_id = uuid_mod.uuid4()
            new_clinic = ClinicModel(
                id=clinic_id,
                tenant_id=tenant.id,
                name=_name,
                slug=_c_slug,
                country=country,
                timezone=timezone_opt,
                plan_tier=plan_tier,
                is_active=True,
                onboarding_completed=False,
            )
            session.add(new_clinic)

            write_audit_log_sync(
                session,
                tenant_id=str(tenant.id),
                clinic_id=str(clinic_id),
                user_id=admin_user_id,
                action="clinic.created",
                resource_type="clinic",
                resource_id=str(clinic_id),
                payload={"name": _name, "slug": _c_slug, "country": country, "plan_tier": plan_tier},
            )
            session.commit()

        st.success(
            f"Sucursal '{_name}' registrada exitosamente.\n\n**Clinic ID:** `{clinic_id}`\n**Tenant ID:** `{tenant.id}`"
        )
        logger.info("admin_clinic_created", clinic_id=str(clinic_id), slug=_c_slug)

    except Exception as exc:  # noqa: BLE001
        logger.error("admin_create_clinic_error", error=str(exc), slug=_c_slug)
        st.error(f"Error al registrar la sucursal: {exc}")
