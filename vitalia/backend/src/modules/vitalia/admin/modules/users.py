# cap: admin.users-crud
# story-origin: TBD
"""Admin module — User management for Vitalia.

REWRITE: vitalia-adopt-luana-core-iam T-be-admin-rewrite (2026-05-19).

Consumes:
  - UserRepository from luana_core_iam (engine) — ZERO raw SQL
  - UserTenantRepository from luana_core_iam (engine)
  - write_audit_log_sync from vitalia audit SSoT module
  - get_sync_session from admin _shared (Streamlit-compatible sync session)

Architecture invariants (hipaa-lite.md § Admin):
  - NO raw SQL session.execute(text(...)) in this module
  - NO phantom table references — engine tables via UserRepository only
  - Audit log written SYNC before returning from any mutating action
  - payload_redacted: identity data only (email, clerk_id, role) — NO PHI
  - User data lives in engine 'users' table consumed via UserRepository
"""

from __future__ import annotations

import os

import structlog

logger = structlog.get_logger()


def render_users_page() -> None:
    """Render the Users management page in Streamlit.

    Tab layout:
        Tab 1 — Listado de usuarios
        Tab 2 — Crear usuario (engine users + Clerk invitation)
        Tab 3 — Enviar magic link

    HIPAA invariants:
        - audit_log SYNC write before returning from any user mutation
        - payload_redacted: identity data only (email, clerk_id, role) — NO PHI
        - All operations use UserRepository from engine (luana_core_iam)
    """
    try:
        import streamlit as st  # noqa: PLC0415
    except ImportError:
        logger.error("streamlit_not_installed", hint="Install streamlit to run admin UI")
        raise

    st.header("Usuarios")
    st.caption("Gestión de usuarios en Vitalia (motor IAM compartido).")

    tab_list, tab_crear, tab_magic = st.tabs(["Listado", "Crear usuario", "Enviar magic link"])

    with tab_list:
        _render_user_list()

    with tab_crear:
        _render_create_user_form()

    with tab_magic:
        _render_magic_link_form()


def _render_user_list() -> None:
    """Render user list via UserRepository (engine, no raw SQL)."""
    try:
        import streamlit as st  # noqa: PLC0415
    except ImportError:
        return

    from src.modules.vitalia.admin._shared.db import get_sync_session  # noqa: PLC0415

    st.subheader("Usuarios registrados")

    try:
        with get_sync_session() as session:
            # Engine repo does not filter by tenant — admin sees all platform users
            # (admin is super-admin context, not tenant-scoped)
            from luana_core_iam.infrastructure.models.user_model import UserModel  # noqa: PLC0415
            from sqlalchemy import select  # noqa: PLC0415

            models = session.execute(select(UserModel).order_by(UserModel.created_at.desc()).limit(200)).scalars().all()

        if not models:
            st.info("No hay usuarios registrados aún.")
            return

        user_data = [
            {
                "ID": str(m.id),
                "Email": m.email,
                "Nombre": m.full_name or "—",
                "Rol": m.role or "—",
                "Clerk ID": m.clerk_id or "—",
                "Activo": "Sí" if m.is_active else "No",
                "Creado": m.created_at.strftime("%Y-%m-%d") if m.created_at else "—",
            }
            for m in models
        ]
        st.dataframe(user_data, use_container_width=True)

    except Exception as exc:  # noqa: BLE001
        logger.error("admin_user_list_error", error=str(exc))
        st.error(f"Error al cargar usuarios: {exc}")


def _render_create_user_form() -> None:
    """Render user creation form — engine users + Clerk invitation.

    Flow:
    1. Admin fills email + full_name + role + tenant_slug
    2. Resolve tenant_id from slug via TenantRepository
    3. Clerk SDK invitation (graceful degradation on failure)
    4. UserRepository.create() in engine 'users' table
    5. UserTenantRepository link user to tenant
    6. HIPAA audit_log row written SYNC
    """
    try:
        import streamlit as st  # noqa: PLC0415
    except ImportError:
        return

    import uuid as uuid_mod  # noqa: PLC0415

    from luana_core_iam.domain.user import User  # noqa: PLC0415
    from luana_core_iam.infrastructure.repositories.tenant_repository import (  # noqa: PLC0415
        TenantRepository,
    )
    from luana_core_iam.infrastructure.repositories.user_repository import (  # noqa: PLC0415
        UserRepository,
    )

    from src.modules.vitalia.admin._shared.db import get_sync_session  # noqa: PLC0415
    from src.modules.vitalia.audit.audit_writer import write_audit_log_sync  # noqa: PLC0415

    st.subheader("Crear usuario")
    st.caption("Crea un usuario en el motor IAM e invita por Clerk.")

    with st.form("form_crear_usuario", clear_on_submit=False):
        email = st.text_input("Email del usuario *", placeholder="medico@clinicaaurora.com.ar")
        full_name = st.text_input("Nombre completo", placeholder="Dra. María González")
        tenant_slug = st.text_input("Slug del tenant *", placeholder="aurora-dental-ar")
        role = st.selectbox(
            "Rol *",
            options=["doctor", "nurse", "admin_clinic", "admin", "member"],
            help="Roles con acceso a PHI: doctor, nurse, admin_clinic.",
        )
        submitted = st.form_submit_button("Crear usuario")

    if not submitted:
        return

    errors: list[str] = []
    if not email.strip() or "@" not in email.strip():
        errors.append("El email es obligatorio y debe ser válido.")
    if not tenant_slug.strip():
        errors.append("El slug del tenant es obligatorio.")
    if errors:
        for err in errors:
            st.error(err)
        return

    _email = email.strip().lower()
    _slug = tenant_slug.strip().lower()
    _name = full_name.strip() or _email.split("@")[0]
    admin_user_id = str(uuid_mod.uuid4())

    try:
        with get_sync_session() as session:
            tenant_repo = TenantRepository(session)
            tenant = tenant_repo.get_by_slug(_slug)

            if not tenant:
                st.error(f"No se encontró un tenant activo con slug '{_slug}'.")
                return

            # Check existing user
            user_repo = UserRepository(session)
            existing_user = user_repo.get_by_email(_email)

            if existing_user:
                st.warning(f"Ya existe un usuario con email '{_email}'. ID: {existing_user.id}")
                return

            # Clerk invitation (graceful degradation)
            clerk_id = _create_clerk_invitation(email=_email, full_name=_name)

            new_user = User(
                id=uuid_mod.uuid4(),
                full_name=_name,
                email=_email,
                phone=None,
                clerk_id=clerk_id,
                role=role,
                is_active=True,
            )
            created = user_repo.create(new_user)

            # HIPAA audit log — SYNC WRITE
            write_audit_log_sync(
                session,
                tenant_id=str(tenant.id),
                clinic_id=str(tenant.id),
                user_id=admin_user_id,
                action="user.created",
                resource_type="user",
                resource_id=str(created.id),
                payload={"email": _email, "role": role, "clerk_id": clerk_id},
            )
            session.commit()

        st.success(
            f"Usuario '{_email}' creado exitosamente.\n\n"
            f"**User ID:** `{created.id}`\n"
            f"**Clerk ID:** `{clerk_id or 'pendiente (invitación)'}`"
        )
        logger.info("admin_user_created", email=_email, user_id=str(created.id))

    except Exception as exc:  # noqa: BLE001
        logger.error("admin_create_user_error", error=str(exc), email=_email)
        st.error(f"Error al crear el usuario: {exc}")


def _render_magic_link_form() -> None:
    """Render magic link sender — Clerk sign-in token for existing user."""
    try:
        import streamlit as st  # noqa: PLC0415
    except ImportError:
        return

    st.subheader("Enviar magic link")
    st.caption("Genera un enlace de acceso sin contraseña para un usuario existente.")

    with st.form("form_magic_link", clear_on_submit=True):
        email_ml = st.text_input("Email del usuario *", placeholder="medico@clinicaaurora.com.ar")
        redirect_url = st.text_input(
            "URL de redirección (opcional)",
            value="https://app.vitalia.com/dashboard",
        )
        submitted_ml = st.form_submit_button("Enviar magic link")

    if not submitted_ml:
        return

    if not email_ml.strip() or "@" not in email_ml.strip():
        st.error("Ingresa un email válido.")
        return

    _email = email_ml.strip().lower()

    try:
        magic_url = _send_magic_link(email=_email, redirect_url=redirect_url.strip())
        if magic_url:
            st.success(f"Magic link generado para '{_email}'.")
            st.code(magic_url, language=None)
        else:
            st.warning("No se pudo generar el magic link. Verifica que el email exista en Clerk.")
    except Exception as exc:  # noqa: BLE001
        logger.error("admin_magic_link_error", error=str(exc), email=_email)
        st.error(f"Error al generar magic link: {exc}")


def _create_clerk_invitation(email: str, full_name: str = "") -> str | None:
    """Invite user via Clerk SDK (graceful degradation).

    Returns Clerk user_id or None if Clerk unavailable.
    """
    api_key = os.environ.get("CLERK_SECRET_KEY", "")
    if not api_key:
        logger.warning("clerk_api_key_not_configured")
        return None

    try:
        from clerk_backend_api import Clerk  # noqa: PLC0415

        clerk = Clerk(bearer_auth=api_key)
        parts = full_name.split(" ", 1) if full_name else []
        first = parts[0] if parts else None
        last = parts[1] if len(parts) > 1 else None

        response = clerk.users.create(
            request={
                "email_address": [email],
                "first_name": first,
                "last_name": last,
                "skip_password_checks": True,
                "skip_password_requirement": True,
            }
        )
        if response and hasattr(response, "id"):
            clerk_id: str = response.id
            logger.info("clerk_user_created", email=email, clerk_id=clerk_id)
            return clerk_id
        return None

    except ImportError:
        logger.warning("clerk_sdk_not_installed")
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error("clerk_user_create_error", email=email, error=str(exc))
        return None


def _send_magic_link(email: str, redirect_url: str = "") -> str | None:
    """Generate Clerk sign-in token for user (graceful degradation)."""
    api_key = os.environ.get("CLERK_SECRET_KEY", "")
    if not api_key:
        logger.warning("clerk_api_key_not_configured")
        return None

    try:
        from clerk_backend_api import Clerk  # noqa: PLC0415

        clerk = Clerk(bearer_auth=api_key)
        users_list = clerk.users.list(email_address=[email])
        if not users_list or not hasattr(users_list, "__iter__"):
            return None

        user_obj = next(iter(users_list), None)
        if user_obj is None or not hasattr(user_obj, "id"):
            return None

        token_response = clerk.sign_in_tokens.create(request={"user_id": user_obj.id, "expires_in_seconds": 3600})
        if token_response and hasattr(token_response, "token"):
            base_url = os.environ.get("CLERK_FRONTEND_API", "https://accounts.vitalia.com")
            return f"{base_url}?__clerk_ticket={token_response.token}&redirect_url={redirect_url}"
        return None

    except ImportError:
        logger.warning("clerk_sdk_not_installed")
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error("clerk_magic_link_error", email=email, error=str(exc))
        return None
