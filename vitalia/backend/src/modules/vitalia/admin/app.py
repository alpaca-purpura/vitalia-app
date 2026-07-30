# cap: admin.admin-streamlit-service
# story-origin: TBD
"""Vitalia Admin — Streamlit entry point.

Registry-based navigation (T-4 scope: 2 pages only — tenants + usuarios).
Admin panel runs as a separate process from the main FastAPI app.

Usage:
    streamlit run src/modules/vitalia/admin/app.py

Auth: Single super-admin password via bcrypt against VITALIA_ADMIN_PASSWORD_HASH env var.

Architecture (per admin-panel.md):
- `app.py`       — entry point, st.set_page_config (UNIQUE call), st.navigation registry
- `pages/`       — thin wrappers (1 line: call render_*())
- `modules/`     — business logic (render_*() functions with HIPAA audit_log)
- `_shared/`     — auth.py (bcrypt) + db.py (sync session for Streamlit)

HIPAA-lite invariants enforced per module:
- audit_log SYNC write before returning from any mutating action
- payload_redacted: identity OK (clinic_name, email, slug); NO PHI fields
- Dual filter (tenant_id + clinic_id) on all queries
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Callable

import structlog

logger = structlog.get_logger()

# ── Path resolution — ensure src/ is importable ──────────────────────────────
# Streamlit runs app.py as __main__ from the backend/ root.
# Adjust sys.path so `src.modules.*` imports resolve.
_BACKEND_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)


# ── PageSpec registry ─────────────────────────────────────────────────────────


@dataclass
class PageSpec:
    """Specification for a single admin sidebar page.

    Attributes:
        slug: URL-safe page identifier (unique, used as url_path)
        title: Human-readable page title (Spanish neutro LatAm)
        icon: Streamlit-compatible emoji or material icon name
        render_fn: Callable that renders the page content
    """

    slug: str
    title: str
    icon: str
    render_fn: Callable[[], None]


# ── Module imports (late import avoids streamlit dependency at test time) ─────


def _get_tenants_render() -> Callable[[], None]:
    """Late import of tenants render function to avoid streamlit dependency."""
    from src.modules.vitalia.admin.modules.tenants import render_tenants_page  # noqa: PLC0415

    return render_tenants_page


def _get_users_render() -> Callable[[], None]:
    """Late import of users render function to avoid streamlit dependency."""
    from src.modules.vitalia.admin.modules.users import render_users_page  # noqa: PLC0415

    return render_users_page


def _get_clinics_render() -> Callable[[], None]:
    """Late import of clinics render function to avoid streamlit dependency."""
    from src.modules.vitalia.admin.modules.clinics import render_clinics_page  # noqa: PLC0415

    return render_clinics_page


# ── PAGE_SPECS registry ───────────────────────────────────────────────────────

PAGE_SPECS: tuple[PageSpec, ...] = (
    PageSpec(
        slug="tenants",
        title="Tenants",
        icon="🏢",
        render_fn=_get_tenants_render(),
    ),
    PageSpec(
        slug="usuarios",
        title="Usuarios",
        icon="👤",
        render_fn=_get_users_render(),
    ),
    PageSpec(
        slug="clinicas",
        title="Sucursales Clínicas",
        icon="🏥",
        render_fn=_get_clinics_render(),
    ),
)


# ── Navigation builder ────────────────────────────────────────────────────────


def _build_pages() -> list:  # noqa: ANN201
    """Materialize st.Page objects from PAGE_SPECS registry.

    Returns:
        List of st.Page instances for st.navigation()
    """
    import streamlit as st  # noqa: PLC0415

    return [
        st.Page(
            spec.render_fn,
            title=spec.title,
            icon=spec.icon,
            url_path=spec.slug,
        )
        for spec in PAGE_SPECS
    ]


# ── Auth guard ────────────────────────────────────────────────────────────────


def _require_auth() -> bool:
    """Render login wall if not authenticated. Returns True if authenticated.

    Uses Streamlit session_state for persistence within a session.
    """
    import streamlit as st  # noqa: PLC0415

    from src.modules.vitalia.admin._shared.auth import verify_admin_password  # noqa: PLC0415

    if st.session_state.get("admin_authenticated"):
        return True

    st.title("Vitalia Admin")
    st.caption("Acceso restringido — ingresa tu contraseña de administrador.")

    with st.form("login_form"):
        password = st.text_input(
            "Contraseña",
            type="password",
            placeholder="Contraseña de administrador",
        )
        submitted = st.form_submit_button("Entrar")

    if submitted:
        if verify_admin_password(password):
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta. Intenta nuevamente.")

    return False


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    """Streamlit app entry point — called once per page load.

    st.set_page_config MUST be called ONCE before any other st.* call
    (Streamlit enforces this — arch rule from admin-panel.md).
    """
    import streamlit as st  # noqa: PLC0415

    st.set_page_config(
        page_title="Vitalia Admin",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if not _require_auth():
        st.stop()
        return

    # Salir button in sidebar
    with st.sidebar:
        st.markdown("---")
        if st.button("Salir", key="btn_logout", use_container_width=True):
            st.session_state.admin_authenticated = False
            st.rerun()

    pages = _build_pages()
    nav = st.navigation(pages, position="sidebar")
    nav.run()


if __name__ == "__main__":
    main()
