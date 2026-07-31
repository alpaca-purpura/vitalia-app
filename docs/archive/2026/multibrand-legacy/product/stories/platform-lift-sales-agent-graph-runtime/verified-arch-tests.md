# verified-arch-tests.md — código de tests proven por el architect (copy-paste)

> El architect probó RED→GREEN cada ESC en este worktree. Acá están las **implementaciones permanentes de los arch tests**, listas para que el dev-team las cree en `core/luana-core-sales-agent/tests/architecture/` (crear el dir + `__init__.py`).
>
> **Por qué subproceso en ESC-4:** `configure_mappers()` es estado GLOBAL; el conftest del paquete registra modelos sintéticos (`AppointmentModel`) que contaminan el registry y vuelven el test no-determinístico (ver 03-arch § Realidad del entorno). Correr la probe en un **subproceso** garantiza un import-state limpio y determinístico — exactamente como el spike del architect. NO uses el conftest del paquete para este test.
>
> **TDD:** crear el test PRIMERO (RED contra el código actual sin fix), luego aplicar el diff del ESC (GREEN). Los 3 diffs exactos están en `03-arch.md § TL;DR`.

---

## `tests/architecture/test_esc4_relationship_module_qualified.py`

```python
"""ESC-4 — engine LeadModel.messages must be module-qualified so a brand MessageModel
homonym on the shared Base does not break configure_mappers().

Runs the mapper-init probe in a SUBPROCESS for a deterministic import state
(the package conftest registers synthetic models that pollute the global registry).
Architect-verified: RED (InvalidRequestError: Multiple classes found for path
"MessageModel") before the fix; GREEN after qualifying crm.py LeadModel.messages.
"""

import subprocess
import sys
import textwrap

_PROBE = textwrap.dedent(
    """
    import uuid
    from luana_core_platform.domain.base_entity import Base
    from luana_core_platform.infrastructure.models import crm  # LeadModel/SaleModel/CustomerProfileModel
    from luana_core_sales_agent.infrastructure.models.message_model import MessageModel  # engine
    # relationship targets LeadModel needs resolvable:
    from luana_core_scheduling.infrastructure.models.appointment_model import AppointmentModel  # noqa: F401
    from luana_core_iam.infrastructure.models.tenant_model import TenantModel  # noqa: F401
    from luana_core_offer_studio.infrastructure.models.product_model import ProductModel  # noqa: F401
    from sqlalchemy import Column, String  # noqa: F401
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.orm import configure_mappers

    # Brand homonym (e.g. vitalia MessageModel -> vitalia_messages): SAME class name,
    # different table, NO relationships. This is the collision source.
    class MessageModel(Base):  # noqa: F811
        __tablename__ = "brand_messages_probe"
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        tenant_id = Column(UUID(as_uuid=True), nullable=True)

    configure_mappers()
    print("CONFIGURE_OK")
    """
)


def test_engine_leadmodel_messages_resolves_with_brand_homonym() -> None:
    result = subprocess.run(
        [sys.executable, "-c", _PROBE],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        "ESC-4 regression — configure_mappers() failed with a brand MessageModel "
        f"homonym on the shared Base:\n{result.stderr[-2000:]}"
    )
    assert "CONFIGURE_OK" in result.stdout
```

> El subproceso hereda el `PYTHONPATH` del proceso pytest. El validator ya exporta el override (ver 04-validators). En entorno canónico (uv editable) corre sin override.

---

## `tests/architecture/test_esc5_templates_cwd_independent.py`

```python
"""ESC-5 — PromptLoader resolves its templates from the engine package, independent
of cwd. Architect-verified: RED (TemplateNotFound from a foreign cwd) before the fix.
"""

from luana_core_sales_agent.infrastructure.prompts.base import PromptLoader


def test_templates_resolve_from_arbitrary_cwd(monkeypatch, tmp_path) -> None:
    # Simulate a brand process running from a cwd that is NOT the engine package root.
    monkeypatch.chdir(tmp_path)
    loader = PromptLoader()
    # Must NOT raise jinja2.TemplateNotFound:
    loader.fs_env.get_template("message_completeness.j2")


def test_default_templates_dir_is_engine_package_relative() -> None:
    loader = PromptLoader()
    assert loader.templates_dir.endswith(
        "luana_core_sales_agent/infrastructure/prompts/templates"
    )


def test_explicit_override_still_honored(tmp_path) -> None:
    # Back-compat: explicit absolute dir is used as-is.
    (tmp_path / "x.j2").write_text("hi")
    loader = PromptLoader(templates_dir=str(tmp_path))
    assert loader.fs_env.get_template("x.j2").render() == "hi"
```

---

## `tests/architecture/test_esc6_prompt_version_tenant_id.py`

```python
"""ESC-6 — PromptVersion must expose tenant_id so the HYBRID/DB prompt-load path
builds its queries. Architect-verified: RED (AttributeError) before the column.
"""

import uuid

from sqlalchemy import desc, select

from luana_core_sales_agent.infrastructure.models.prompt_version_model import PromptVersion


def test_prompt_version_has_tenant_id_column() -> None:
    assert hasattr(PromptVersion, "tenant_id")
    assert "tenant_id" in PromptVersion.__table__.columns


def test_prompt_load_query_branches_build() -> None:
    tid = uuid.uuid4()
    # specific-override branch (base.py:84-96)
    q1 = (
        select(PromptVersion)
        .where(PromptVersion.key == "k", PromptVersion.is_active, PromptVersion.tenant_id == tid)
        .order_by(desc(PromptVersion.version))
    )
    # system-default branch (base.py:103-115)
    q2 = (
        select(PromptVersion)
        .where(PromptVersion.key == "k", PromptVersion.is_active, PromptVersion.tenant_id.is_(None))
        .order_by(desc(PromptVersion.version))
    )
    assert "tenant_id" in str(q1)
    assert "IS NULL" in str(q2).upper()
```

---

## Notas de ejecución para el dev-team

- Crear `core/luana-core-sales-agent/tests/architecture/__init__.py` (vacío) si no existe.
- Correr cada arch test con PYTHONPATH override (ver 04-validators) — in-worktree. En canónico (uv editable), sin override.
- ESC-4: si el subproceso falla por `ModuleNotFoundError` de un paquete (`luana_core_offer_studio`, etc.), agregá su `src` al PYTHONPATH del validator (el architect usó: sales-agent + platform + scheduling + iam + offer-studio). En canónico (uv editable) no hace falta.
- NO correr estos arch tests a través del conftest pesado del paquete si causa el ruido de `AppointmentModel` (el de ESC-4 ya es subproceso aislado; ESC-5/6 son livianos y no dependen del registry global).
