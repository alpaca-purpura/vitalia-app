# cap: admin.admin-streamlit-service
# story-origin: TBD
"""Vitalia admin Streamlit application.

Entry point: src.modules.vitalia.admin.app (run via streamlit run app.py).
Registry-based navigation with 2 pages (T-4 scope): tenants + usuarios.

Structure:
    app.py          — main entry point, st.navigation registry
    pages/          — thin wrappers delegating to modules/
    modules/        — business logic (render_*() functions)
    _shared/        — cross-module utilities (auth, db session)
"""
