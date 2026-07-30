# Admin Panel (Streamlit)

> **Slim pointer (W1-Phase2 eviction 2026-06-09 · tier: project).** Cuerpo operativo + ex-always-on body (estructura, prohibidos, contract/smoke tests) en `backend-expert` skill → `references/admin-panel.md`.

Trigger: tocás `{brand}/backend/src/modules/{brand}/admin/**` (opcional per brand).

No-skip 1-liner: lógica SOLO en `modules/` (pages = wrappers thin) · `st.set_page_config` solo en `app.py` · sin import cruzado entre modules (salvo `_shared`) · admin común cross-brand → lift `/pm-luana`.
