# cap: admin.admin-streamlit-service
# story-origin: TBD
"""Admin page wrapper — Usuarios (thin, delegates to modules/users.py).

Per admin-panel.md: pages/*.py are THIN wrappers only.
All logic lives in modules/*.py render_*() functions.
"""

from __future__ import annotations

from src.modules.vitalia.admin.modules.users import render_users_page

render_users_page()
