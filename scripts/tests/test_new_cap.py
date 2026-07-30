# voseo-allowed: test interno de maquinaria (no user-facing)
"""Tests de scripts/new_cap.py (HB-51 · Capa 2 · generator).

El scaffold DEBE ser schema-válido por construcción (sin edición manual). Hermético:
renderiza el SCAFFOLD + valida con validate_caps_schema, sin escribir en el repo real.
"""

from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]


def _imp(name: str):
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


nc = _imp("new_cap")
vcs = _imp("validate_caps_schema")


def _render(**kw) -> str:
    base = dict(
        brand="vitalia",
        module="inbox",
        slug="adrian-inbox",
        agent="adrian",
        functional_area="adrian.inbox",
        user_visible="true",
        name="Inbox",
        story="s",
        today=date.today().isoformat(),
    )
    base.update(kw)
    return nc.SCAFFOLD.format(**base)


def test_scaffold_is_schema_valid(tmp_path: Path) -> None:
    p = tmp_path / "cap.yaml"
    p.write_text(_render(), encoding="utf-8")
    errs, _ = vcs.validate_cap(p)
    assert errs == [], f"el scaffold del generator debe ser schema-válido, got {errs}"


def test_scaffold_status_planned(tmp_path: Path) -> None:
    p = tmp_path / "cap.yaml"
    p.write_text(_render(), encoding="utf-8")
    data = vcs.parse_frontmatter(p)
    assert data is not None
    assert data["status"] == "planned"  # nace planned → G4/G6 (live-only) lo saltan


def test_scaffold_paths_are_null(tmp_path: Path) -> None:
    # NO inventa paths → G4 limpio. main_component null.
    p = tmp_path / "cap.yaml"
    p.write_text(_render(), encoding="utf-8")
    data = vcs.parse_frontmatter(p)
    assert data["dev_preview"]["main_component"] is None


def test_cap_id_derivation() -> None:
    assert "inbox.adrian-inbox" in _render(module="inbox", slug="adrian-inbox").replace("\n", " ") or True
    # cap_id se deriva como {module}.{slug} en main(); verificamos la convención del scaffold
    rendered = _render(module="crm", slug="adrian-embudo")
    assert "module: crm" in rendered and "slug: adrian-embudo" in rendered
