# cap: admin.streamlit-tenants-users
# story-origin: TBD
"""Admin module — Tenant management for Vitalia.

REWRITE: vitalia-adopt-luana-core-iam T-be-admin-rewrite (2026-05-19).

Consumes:
  - TenantRepository from luana_core_iam (engine) — ZERO raw SQL
  - write_audit_log_sync from vitalia audit SSoT module
  - get_sync_session from admin _shared (Streamlit-compatible sync session)

Architecture invariants (hipaa-lite.md § Admin):
  - NO raw SQL session.execute(text(...)) in this module
  - NO phantom table references — engine tables via TenantRepository only
  - Audit log written SYNC before returning from any mutating action
  - payload_redacted: identity data only (name, slug, country) — NO PHI
  - All reads filtered by tenant context (engine repo handles tenant_id via tenants table)
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger()


def render_tenants_page() -> None:
    """Render the Tenants management page in Streamlit.

    Tab layout:
        Tab 1 — Listado de tenants activos
        Tab 2 — Crear nuevo tenant
        Tab 3 — Ver detalle

    HIPAA invariants:
        - audit_log SYNC write before returning from any mutating action
        - payload_redacted: identity data only (name, slug) — NO PHI
        - All operations use TenantRepository from engine (luana_core_iam)
    """
    try:
        import streamlit as st  # noqa: PLC0415
    except ImportError:
        logger.error("streamlit_not_installed", hint="Install streamlit to run admin UI")
        raise

    st.header("Tenants")
    st.caption("Gestión de tenants activos en la plataforma Vitalia.")

    tab_list, tab_crear, tab_detalle = st.tabs(["Listado", "Crear nuevo tenant", "Detalle"])

    with tab_list:
        _render_tenant_list()

    with tab_crear:
        _render_create_tenant_form()

    with tab_detalle:
        _render_tenant_detail()


def _render_tenant_list() -> None:
    """Render the tenant listing tab — read-only view via TenantRepository."""
    try:
        import streamlit as st  # noqa: PLC0415
    except ImportError:
        return

    from luana_core_iam.infrastructure.repositories.tenant_repository import (  # noqa: PLC0415
        TenantRepository,
    )

    from src.modules.vitalia.admin._shared.db import get_sync_session  # noqa: PLC0415

    st.subheader("Tenants activos")

    try:
        with get_sync_session() as session:
            repo = TenantRepository(session)
            tenants = repo.get_all()

        if not tenants:
            st.info("No hay tenants registrados aún.")
            return

        tenant_data = [
            {
                "ID": str(t.id),
                "Nombre": t.name,
                "Slug": t.slug,
                "Activo": "Sí" if t.is_active else "No",
                "Onboarding": "Completo" if getattr(t, "is_onboarded", False) else "Pendiente",
                "Creado": t.created_at.strftime("%Y-%m-%d") if t.created_at else "—",
            }
            for t in tenants
        ]
        st.dataframe(tenant_data, use_container_width=True)

    except Exception as exc:  # noqa: BLE001
        logger.error("admin_tenant_list_error", error=str(exc))
        st.error(f"Error al cargar el listado de tenants: {exc}")


def _render_create_tenant_form() -> None:
    """Render tenant creation form — creates tenant row via TenantRepository.

    Creates a new tenant in the engine 'tenants' table.
    Writes audit log row SYNC before returning.
    """
    try:
        import streamlit as st  # noqa: PLC0415
    except ImportError:
        return

    import uuid as uuid_mod  # noqa: PLC0415

    from luana_core_iam.domain.tenant import Tenant  # noqa: PLC0415
    from luana_core_iam.infrastructure.repositories.tenant_repository import (  # noqa: PLC0415
        TenantRepository,
    )

    from src.modules.vitalia.admin._shared.db import get_sync_session  # noqa: PLC0415
    from src.modules.vitalia.audit.audit_writer import write_audit_log_sync  # noqa: PLC0415

    st.subheader("Crear nuevo tenant")
    st.caption("Los campos marcados con * son obligatorios.")

    with st.form("form_crear_tenant", clear_on_submit=False):
        tenant_name = st.text_input("Nombre del tenant *", placeholder="Clínica Aurora Dental AR")
        tenant_slug = st.text_input(
            "Slug (identificador URL) *",
            placeholder="aurora-dental-ar",
            help="Solo letras minúsculas, números y guiones. Debe ser único.",
        )
        submitted = st.form_submit_button("Crear tenant")

    if not submitted:
        return

    errors: list[str] = []
    if not tenant_name.strip():
        errors.append("El nombre del tenant es obligatorio.")
    if not tenant_slug.strip():
        errors.append("El slug es obligatorio.")
    elif not _is_valid_slug(tenant_slug.strip()):
        errors.append("El slug solo puede contener letras minúsculas, números y guiones.")

    if errors:
        for err in errors:
            st.error(err)
        return

    slug = tenant_slug.strip().lower()
    name = tenant_name.strip()
    admin_user_id = str(uuid_mod.uuid4())

    try:
        with get_sync_session() as session:
            repo = TenantRepository(session)

            existing = repo.get_by_slug(slug)
            if existing:
                st.warning(f"Ya existe un tenant con el slug '{slug}'. ID: {existing.id}")
                return

            new_tenant = Tenant(
                id=uuid_mod.uuid4(),
                name=name,
                slug=slug,
                is_active=True,
            )
            created = repo.create(new_tenant)

            # HIPAA-lite audit log — SYNC WRITE before returning
            write_audit_log_sync(
                session,
                tenant_id=str(created.id),
                clinic_id=str(created.id),  # tenant is own clinic root
                user_id=admin_user_id,
                action="tenant.created",
                resource_type="tenant",
                resource_id=str(created.id),
                payload={"name": name, "slug": slug},
            )
            session.commit()

        st.success(f"Tenant '{name}' creado exitosamente.\n\n**Tenant ID:** `{created.id}`")
        logger.info("admin_tenant_created", tenant_id=str(created.id), slug=slug)

    except Exception as exc:  # noqa: BLE001
        logger.error("admin_create_tenant_error", error=str(exc), slug=slug)
        st.error(f"Error al crear el tenant: {exc}")


def _render_tenant_detail() -> None:
    """Render tenant detail tab — look up by slug via TenantRepository."""
    try:
        import streamlit as st  # noqa: PLC0415
    except ImportError:
        return

    from luana_core_iam.infrastructure.repositories.tenant_repository import (  # noqa: PLC0415
        TenantRepository,
    )

    from src.modules.vitalia.admin._shared.db import get_sync_session  # noqa: PLC0415

    st.subheader("Detalle de tenant")

    slug_input = st.text_input("Buscar por slug", placeholder="aurora-dental-ar")

    if not slug_input.strip():
        st.caption("Ingresa un slug para buscar el tenant.")
        return

    try:
        with get_sync_session() as session:
            repo = TenantRepository(session)
            tenant = repo.get_by_slug(slug_input.strip().lower())

        if not tenant:
            st.warning(f"No se encontró ningún tenant con slug '{slug_input.strip()}'.")
            return

        st.json(
            {
                "id": str(tenant.id),
                "name": tenant.name,
                "slug": tenant.slug,
                "is_active": tenant.is_active,
                "is_onboarded": getattr(tenant, "is_onboarded", None),
                "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
            }
        )

    except Exception as exc:  # noqa: BLE001
        logger.error("admin_tenant_detail_error", error=str(exc))
        st.error(f"Error al buscar el tenant: {exc}")


def _is_valid_slug(slug: str) -> bool:
    """Validate slug: only lowercase letters, digits and hyphens."""
    import re  # noqa: PLC0415

    return bool(re.match(r"^[a-z0-9][a-z0-9\-]*[a-z0-9]$", slug))
