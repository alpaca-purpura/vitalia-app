# Admin Panel (Streamlit)

## Arquitectura

```
backend/src/admin/
  app.py              # Entry. PAGE_SPECS (registry) + st.navigation + st.Page
  pages/{slug}.py     # Thin wrappers — un call a render_* por archivo. URL = /{slug}
  modules/{name}.py   # render_*() implementations (all logic here)
  modules/_shared.py  # Cross-module helpers (tenant selector, SQL, flags)
```

- Cada opción del sidebar = 1 `PageSpec(slug, title, icon)` + 1 `pages/{slug}.py` + 1 `modules/{name}.py::render_*()`.
- URL derivada del slug: `/{slug}` (bookmarkeable, F5 preserva).
- `st.set_page_config` solo en `app.py`. Pages NO lo llaman.

## Agregar nueva opción

1. `src/admin/modules/{name}.py` con `def render_{name}() -> None`.
2. `src/admin/pages/{slug}.py`:
   ```python
   from src.admin.modules.{name} import render_{name}
   render_{name}()
   ```
3. Append `PageSpec(slug=..., title=..., icon=...)` en `PAGE_SPECS` de `app.py`.
4. Correr tests:
   ```bash
   cd backend && .venv/bin/pytest tests/admin/ tests/architecture/test_admin_panel.py -x -q
   ```

## Prohibido

- ❌ Lógica en `pages/*.py` (solo wrapper, 1 call a render_*).
- ❌ `st.set_page_config` fuera de `app.py`.
- ❌ Import cruzado `modules/A` → `modules/B` (excepto `_shared`).
- ❌ Slug no-kebab-case o duplicado.
- ❌ Módulo bajo `modules/` sin `render_*` (va a `_shared.py` si es helper).

## Tests de regresión

Corre en `/test-backend` + `/test-all`:

| Test | Qué valida |
|---|---|
| `tests/architecture/test_admin_panel.py` | pages ↔ registry parity, todos los modules tienen render_* |
| `tests/admin/test_admin_contract.py` | AST parse: wiring correcto, slug único, no cross-module imports |
| `tests/admin/test_admin_smoke.py` | `AppTest` renderiza cada página headless sin exception |

Smoke mockea DB/Qdrant vía `tests/admin/conftest.py`. Edit ese conftest cuando agregues repo/servicio nuevo que use el admin.

## Por qué existe esto

El panel rompía en cada refactor cross-module porque sus imports viven dentro de `render_*()` y no los veía ningún test. Los smoke tests fuerzan render end-to-end tras cualquier cambio en repos/servicios/DTOs. La arquitectura registry-based + contract tests evita "nueva opción sin URL" o "módulo huérfano".

## Límites Docker

`admin_dashboard_dev` en `docker-compose.yml`:
- `memory: 1024M` (antes 128M → OOM silencioso al navegar).
- `cpus: '1.0'` (antes 0.50 → renders lentos).

Si vuelve a hang sin error: `docker events --filter container=luana-dev-{brand}_admin_dev-1` → si aparece `oom`, subir `memory:`.

---

## Ex always-on rule body (evicted W1-Phase2 2026-06-09 — era `.claude/rules/admin-panel.md`)

Admin panel es **opcional per brand**. Cada brand que necesite admin lo hostea en `{brand}/backend/src/modules/{brand}/admin/`.

Registry-based `st.navigation`. Cada sidebar option = 1 `PageSpec` + 1 `pages/{slug}.py` wrapper + 1 `modules/{name}.py::render_*()`. Lógica solo en `modules/`.

Paths per brand:

```
{brand}/backend/src/modules/{brand}/admin/
├── app.py                 # entry, st.set_page_config único
├── pages/{slug}.py        # wrappers thin
├── modules/{name}.py      # render_*() lógica
└── _shared/               # utilidades cross-module dentro de la admin
```

**Prohibido:** lógica en `pages/*.py`, `st.set_page_config` fuera `app.py`, import cruzado `modules/A → modules/B` (excepto `_shared`), slug duplicado, import cross-brand (cada admin es brand-aislado).

### Multibrand awareness (post reorg 2026-05-15)

- Cada brand decide si bootstrap admin panel o no (no es obligatorio).
- Lógica admin común a todas las brands → candidate para `core/luana-core-platform/src/luana_core_platform/admin/` (requiere `/pm-luana` promotion gate).
