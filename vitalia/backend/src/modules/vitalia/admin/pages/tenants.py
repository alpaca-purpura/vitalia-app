# cap: admin.streamlit-tenants-users
# story-origin: TBD
"""Admin page wrapper — Tenants & Clinics (thin, delegates to modules/tenants.py).

Per admin-panel.md: pages/*.py are THIN wrappers only.
All logic lives in modules/*.py render_*() functions.
"""

from __future__ import annotations

from src.modules.vitalia.admin.modules.tenants import render_tenants_page

render_tenants_page()
