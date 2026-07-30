# voseo-allowed: test interno de maquinaria (no user-facing)
"""Tests de scripts/validate_caps_schema.py (HB-51 · Capa 3).

Negative tests con dientes: cada regla del schema (status enum, functional_area
formato, module required, change_log.type, fence-less parse) probada en ROJO.
Hermético: caps en tmp, NO depende de la data viva.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "validate_caps_schema", Path(__file__).resolve().parents[1] / "validate_caps_schema.py"
)
vcs = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(vcs)  # type: ignore[union-attr]


def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "cap.yaml"
    p.write_text(body, encoding="utf-8")
    return p


_OK = (
    "---\n"
    "capability_id: vitalia.inbox.adrian-inbox\n"
    "module: inbox\n"
    "slug: adrian-inbox\n"
    "status: live\n"
    "functional_area: adrian.inbox\n"
    "nature: feature\n"
    "change_log:\n"
    "  - story_id: s\n    type: new\n    summary: x\n"
    "---\n# body\n"
)


def test_valid_cap_passes(tmp_path: Path) -> None:
    errs, _ = vcs.validate_cap(_write(tmp_path, _OK))
    assert errs == []


def test_invalid_status_is_error(tmp_path: Path) -> None:
    body = _OK.replace("status: live", "status: zombie")
    errs, _ = vcs.validate_cap(_write(tmp_path, body))
    assert any("status" in e for e in errs)


def test_bad_functional_area_format_is_error(tmp_path: Path) -> None:
    body = _OK.replace("functional_area: adrian.inbox", "functional_area: adrian_inbox")  # sin punto
    errs, _ = vcs.validate_cap(_write(tmp_path, body))
    assert any("functional_area" in e for e in errs)


def test_functional_area_with_underscore_segment_ok(tmp_path: Path) -> None:
    # `onboarding.onboarding_clinic` y `lisa.landing_public` son áreas REALES (snake)
    body = _OK.replace("functional_area: adrian.inbox", "functional_area: onboarding.onboarding_clinic")
    errs, _ = vcs.validate_cap(_write(tmp_path, body))
    assert errs == []


def test_missing_module_is_error(tmp_path: Path) -> None:
    body = _OK.replace("module: inbox\n", "")
    errs, _ = vcs.validate_cap(_write(tmp_path, body))
    assert any("module" in e for e in errs)


def test_tech_module_satisfies_module_requirement(tmp_path: Path) -> None:
    body = _OK.replace("module: inbox", "tech_module: inbox")
    errs, _ = vcs.validate_cap(_write(tmp_path, body))
    assert errs == []


def test_bad_change_log_type_is_error(tmp_path: Path) -> None:
    body = _OK.replace("    type: new", "    type: frobnicate")
    errs, _ = vcs.validate_cap(_write(tmp_path, body))
    assert any("change_log" in e and "type" in e for e in errs)


def test_missing_slug_is_error(tmp_path: Path) -> None:
    body = _OK.replace("slug: adrian-inbox\n", "")
    errs, _ = vcs.validate_cap(_write(tmp_path, body))
    assert any("slug" in e.lower() for e in errs)


def test_nature_off_canon_is_warning_not_error(tmp_path: Path) -> None:
    body = _OK.replace("nature: feature", "nature: diagnostic")
    errs, warns = vcs.validate_cap(_write(tmp_path, body))
    assert errs == []
    assert any("nature" in w for w in warns)


def test_duplicate_key_is_error(tmp_path: Path) -> None:
    """★ Caso 2026-06-05: clave duplicada pasa en PyYAML (tolerante) pero el cockpit
    (gray-matter/js-yaml) la RECHAZA → cap invisible en el mapa. validate_cap debe
    cazarla (ser tan estricto como el consumidor real)."""
    body = _OK.replace("status: live\n", "status: live\nmap_box: adrian\n")  # luego agregamos el dup
    body = body.replace("functional_area: adrian.inbox\n", "functional_area: adrian.inbox\nmap_box: adrian\n")
    errs, _ = vcs.validate_cap(_write(tmp_path, body))
    assert any("duplicada" in e or "cockpit" in e for e in errs), errs


def test_strict_parse_error_detects_dup(tmp_path: Path) -> None:
    body = "---\nslug: x\nstatus: live\nmodule: m\nlast_modified: 2026-05-29\nlast_modified: 2026-05-30\n---\n# b\n"
    assert vcs.strict_parse_error(_write(tmp_path, body)) is not None


def test_strict_parse_clean_is_none(tmp_path: Path) -> None:
    assert vcs.strict_parse_error(_write(tmp_path, _OK)) is None


def test_fenceless_reconcile_style_parses(tmp_path: Path) -> None:
    # Caps reconciladas: comentarios + bare YAML, SIN fence `---`
    body = (
        "# capability schema v4\n"
        "# Reconciled by scripts/reconcile_capabilities.py\n"
        'capability_id: "abel.icp-buyer"\n'
        'module: "abel"\n'
        'slug: "icp-buyer"\n'
        "status: wip\n"
    )
    errs, _ = vcs.validate_cap(_write(tmp_path, body))
    assert errs == [], f"cap fence-less debe parsear, got {errs}"
