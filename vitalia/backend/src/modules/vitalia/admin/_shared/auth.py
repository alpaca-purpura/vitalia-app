# cap: admin.admin-streamlit-service
# story-origin: TBD
"""Admin authentication — bcrypt password verification against env-var hash.

Security model (D8 from CONTEXT-BRIEF):
- Single super-admin password stored as bcrypt hash in VITALIA_ADMIN_PASSWORD_HASH env var
- No session tokens — Streamlit session_state used for login persistence within a session
- Admin panel runs in a separate K8s container (D7), not exposed via main API

Usage:
    if not st.session_state.get("admin_authenticated"):
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if verify_admin_password(password):
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
"""

from __future__ import annotations

import os

import bcrypt
import structlog

logger = structlog.get_logger()

_ADMIN_PASSWORD_HASH_ENV = "VITALIA_ADMIN_PASSWORD_HASH"


def verify_admin_password(plain_password: str) -> bool:
    """Verify plain_password against VITALIA_ADMIN_PASSWORD_HASH env var bcrypt hash.

    Returns False for empty/whitespace passwords regardless of hash.
    Returns False if env var is not configured (fail-secure).
    Logs warning (without password) on verification failure.

    Args:
        plain_password: Plain text password to verify

    Returns:
        True if password matches the configured hash, False otherwise
    """
    # Reject empty/whitespace passwords immediately (fail-secure)
    if not plain_password or not plain_password.strip():
        logger.warning("admin_auth_empty_password_rejected")
        return False

    pw_hash = os.environ.get(_ADMIN_PASSWORD_HASH_ENV, "")
    if not pw_hash:
        logger.error(
            "admin_auth_hash_not_configured",
            env_var=_ADMIN_PASSWORD_HASH_ENV,
        )
        return False

    try:
        is_valid: bool = bcrypt.checkpw(
            plain_password.encode("utf-8"),
            pw_hash.encode("utf-8"),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "admin_auth_bcrypt_error",
            error=str(exc),
        )
        return False

    if not is_valid:
        logger.warning("admin_auth_password_mismatch")

    return is_valid
