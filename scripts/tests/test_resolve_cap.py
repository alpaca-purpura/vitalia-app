# voseo-allowed: test interno de maquinaria (no user-facing)
"""Tests de scripts/resolve_cap.py — HB-43.

Hermético: fixture tmp con todas las formas REALES de `cap_target` que rompían el
locator (path-style · functional_area dotted · área multi-cap · capability_id · slug
pelado) + un cap con doc-cola YAML malformado (footgun #2: `---` múltiples). Drift-proof:
NO depende de la data viva de vitalia.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location("resolve_cap", Path(__file__).resolve().parents[1] / "resolve_cap.py")
rc = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(rc)  # type: ignore[union-attr]


# Segundo documento DELIBERADAMENTE malformado (colon suelto en prosa) — replica
# el footgun real de adrian-embudo.yaml: safe_load_all reventaba todo el stream.
_TAIL_MALFORMED = "\n---\n# notas\nesto es prosa: con un colon suelto que rompe yaml aquí: sí\n"


def _cap(slug: str, *, cap_id: str, module: str, fa: str = "", main_component: str = "") -> str:
    body = f"---\ncapability_id: {cap_id}\nslug: {slug}\nstatus: planned\ntech_module: {module}\nmodule: {module}\n"
    if fa:
        body += f"functional_area: {fa}\n"
    if main_component:
        body += f"dev_preview:\n  main_component: {main_component}\n  route: /x/{slug}\n"
    return body + _TAIL_MALFORMED


@pytest.fixture()
def caps(tmp_path: Path) -> Path:
    """Árbol fixture de capabilities/ con las formas footgun."""
    root = tmp_path / "capabilities"
    files = {
        "crm/adrian-embudo.yaml": _cap(
            "adrian-embudo",
            cap_id="vitalia.crm.adrian-embudo",
            module="crm",
            main_component="features/crm/components/embudo/AdrianEmbudoView.tsx",
        ),
        "clinics/lisa-doctores.yaml": _cap(
            "lisa-doctores",
            cap_id="vitalia-lisa-doctores",
            module="clinics",
            fa="lisa.doctores",
            main_component="features/lisa/components/doctores/View.tsx",
        ),
        # ÁREA: dos caps comparten functional_area adrian.inbox
        "copilot/inbox-tools.yaml": _cap(
            "inbox-tools",
            cap_id="vitalia-inbox-tools",
            module="copilot",
            fa="adrian.inbox",
        ),
        "sales_agent/inbox-handler.yaml": _cap(
            "inbox-handler",
            cap_id="vitalia-inbox-handler",
            module="sales_agent",
            fa="adrian.inbox",
        ),
        # Deben ser EXCLUIDOS del scan
        "_template.yaml": "---\nslug: __template__\n",
    }
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    (root / "README.md").write_text("# caps\n", encoding="utf-8")
    return root


def _slugs(paths: list[Path]) -> set[str]:
    return {p.stem for p in paths}


# ── Resolución por forma de cap_target ──────────────────────────────────────
def test_path_style_resolves_single(caps: Path) -> None:
    # "crm/adrian-embudo" (module/slug path) → exactamente 1
    assert _slugs(rc.resolve("vitalia", "crm/adrian-embudo", root=caps)) == {"adrian-embudo"}


def test_functional_area_dotted_resolves_single(caps: Path) -> None:
    # "lisa.doctores" (functional_area · NO existe dir lisa/) → clinics/lisa-doctores
    assert _slugs(rc.resolve("vitalia", "lisa.doctores", root=caps)) == {"lisa-doctores"}


def test_dotted_collapses_to_dashed_slug(caps: Path) -> None:
    # "lisa.doctores" también matchea por slug dashed == lisa-doctores
    res = rc.resolve("vitalia", "lisa.doctores", root=caps)
    assert len(res) == 1


def test_area_multi_cap_returns_all(caps: Path) -> None:
    # "adrian.inbox" es un ÁREA (2 caps) → devuelve AMBAS (navegar el barrio)
    assert _slugs(rc.resolve("vitalia", "adrian.inbox", root=caps)) == {"inbox-tools", "inbox-handler"}


def test_capability_id_full_resolves(caps: Path) -> None:
    assert _slugs(rc.resolve("vitalia", "vitalia.crm.adrian-embudo", root=caps)) == {"adrian-embudo"}


def test_bare_slug_resolves(caps: Path) -> None:
    assert _slugs(rc.resolve("vitalia", "adrian-embudo", root=caps)) == {"adrian-embudo"}


def test_unknown_resolves_empty(caps: Path) -> None:
    assert rc.resolve("vitalia", "fantasma.inexistente", root=caps) == []


def test_template_and_readme_excluded(caps: Path) -> None:
    slugs = _slugs(rc.cap_files("vitalia", root=caps))
    assert "__template__" not in slugs
    assert all(not s.startswith("_") for s in slugs)
    # README.md no es .yaml → no aparece de todos modos
    assert len(rc.cap_files("vitalia", root=caps)) == 4


# ── Extract (lo que el agente consume) ──────────────────────────────────────
def test_extract_shows_main_component(caps: Path) -> None:
    block = rc._extract_block(caps / "crm/adrian-embudo.yaml")
    assert "main_component" in block
    assert "AdrianEmbudoView" in block


def test_extract_survives_malformed_tail_doc(caps: Path) -> None:
    # FOOTGUN #2 regression: doc-cola malformado NO debe tumbar el extract
    block = rc._extract_block(caps / "crm/adrian-embudo.yaml")
    assert "no parseable" not in block
    assert "slug: adrian-embudo" in block


# ── main() exit codes ───────────────────────────────────────────────────────
def test_main_null_returns_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert rc.main(["vitalia", "null"]) == 2
    assert "UNRESOLVED" in capsys.readouterr().err


def test_main_bad_usage_returns_1() -> None:
    assert rc.main(["solo-un-arg"]) == 1


# ════════════════════════════════════════════════════════════════════════════
# TWO-WAY canonical resolution (HB-51 · Capa 1)
# ════════════════════════════════════════════════════════════════════════════
#
# Fixture que replica la REALIDAD del incidente inbox: una functional_area
# (`adrian.inbox`) compartida por 3 caps — 1 LIVE canónica + 1 deprecated +
# 1 deprecated-superseded — y una colisión cap_id-vs-alias (`brand_studio.lisa-marca`
# es cap_id de una cap Y `{module}.{fa-dashed}` de otra).


def _cap2(slug: str, *, module: str, status: str, fa: str = "", superseded_by: str = "") -> str:
    body = (
        f"---\ncapability_id: vitalia.{module}.{slug}\nslug: {slug}\n"
        f"status: {status}\ntech_module: {module}\nmodule: {module}\n"
    )
    if fa:
        body += f"functional_area: {fa}\n"
    if superseded_by:
        body += f"superseded_by: {superseded_by}\n"
    return body + "\n---\n# body\n"


@pytest.fixture()
def caps2(tmp_path: Path) -> Path:
    rc.clear_resolver_cache()
    root = tmp_path / "capabilities"
    files = {
        # área adrian.inbox: 1 live canónica + 2 muertas (igual que prod)
        "inbox/adrian-inbox.yaml": _cap2("adrian-inbox", module="inbox", status="live", fa="adrian.inbox"),
        "copilot/inbox-tools-extensions.yaml": _cap2(
            "inbox-tools-extensions", module="copilot", status="deprecated", fa="adrian.inbox"
        ),
        "sales_agent/inbox-handler-mode-occ.yaml": _cap2(
            "inbox-handler-mode-occ",
            module="sales_agent",
            status="deprecated",
            fa="adrian.inbox",
            superseded_by="inbox.adrian-inbox",
        ),
        # mateo-agenda: header `scheduling.mateo-agenda` == {module}.{fa-dashed}
        "scheduling/valeria-agenda.yaml": _cap2(
            "valeria-agenda", module="scheduling", status="live", fa="mateo.agenda"
        ),
        # lisa-doctores: header `clinics.lisa.doctores` == {module}.{fa-dotted}
        "clinics/lisa-doctores.yaml": _cap2("lisa-doctores", module="clinics", status="partial", fa="lisa.doctores"),
        # colisión cap_id-vs-alias: cap_id `brand_studio.lisa-marca` (cap A) ==
        # {module}.{fa-dashed} de cap B (fa lisa.marca) → tier-priority debe ganar A.
        "brand_studio/lisa-marca.yaml": _cap2("lisa-marca", module="brand_studio", status="live", fa="lisa.marca"),
        "brand_studio/medical-sections.yaml": _cap2(
            "medical-sections", module="brand_studio", status="live", fa="lisa.marca"
        ),
    }
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root


def test_cap_id_form_resolves_canonical(caps2: Path) -> None:
    assert rc.resolve_cap_ids("vitalia", "inbox.adrian-inbox", root=caps2) == {"inbox.adrian-inbox"}


def test_functional_area_alias_resolves_to_area_set(caps2: Path) -> None:
    # `adrian.inbox` es ÁREA (1:N) → set de las 3 caps (sin filtro)
    assert rc.resolve_cap_ids("vitalia", "adrian.inbox", root=caps2) == {
        "inbox.adrian-inbox",
        "copilot.inbox-tools-extensions",
        "sales_agent.inbox-handler-mode-occ",
    }


def test_functional_area_alias_live_only_is_single(caps2: Path) -> None:
    # live_only filtra deprecated + superseded → solo la canónica
    assert rc.resolve_cap_ids("vitalia", "adrian.inbox", live_only=True, root=caps2) == {"inbox.adrian-inbox"}


def test_acceptance_two_forms_same_canonical(caps2: Path) -> None:
    # ★ ACCEPTANCE del handoff: ambas formas → mismo cap_id canónico
    assert rc.canonical_cap_id("vitalia", "adrian.inbox", root=caps2) == "inbox.adrian-inbox"
    assert rc.canonical_cap_id("vitalia", "inbox.adrian-inbox", root=caps2) == "inbox.adrian-inbox"
    assert rc.canonical_cap_id("vitalia", "adrian.inbox", root=caps2) == rc.canonical_cap_id(
        "vitalia", "inbox.adrian-inbox", root=caps2
    )


def test_module_fa_dashed_header_resolves(caps2: Path) -> None:
    # `scheduling.mateo-agenda` (forma {module}.{fa-dashed}) → scheduling.valeria-agenda
    assert rc.resolve_cap_ids("vitalia", "scheduling.mateo-agenda", root=caps2) == {"scheduling.valeria-agenda"}


def test_module_fa_dotted_header_resolves(caps2: Path) -> None:
    # `clinics.lisa.doctores` (forma {module}.{fa-dotted}) → clinics.lisa-doctores
    assert rc.resolve_cap_ids("vitalia", "clinics.lisa.doctores", root=caps2) == {"clinics.lisa-doctores"}


def test_tier_priority_cap_id_wins_over_alias(caps2: Path) -> None:
    # `brand_studio.lisa-marca` es cap_id (cap A) Y {module}.{fa-dashed} (cap B).
    # Identidad gana → SOLO cap A. Sin esto, G1/index asociarían el archivo a 2 caps.
    assert rc.resolve_cap_ids("vitalia", "brand_studio.lisa-marca", root=caps2) == {"brand_studio.lisa-marca"}


def test_orphan_header_resolves_empty(caps2: Path) -> None:
    # ★ El bug origen: header → cap inexistente = set vacío (G1 lo cazará en ROJO)
    assert rc.resolve_cap_ids("vitalia", "sales_agent.adrian-override-context", root=caps2) == set()
    assert rc.canonical_cap_id("vitalia", "sales_agent.adrian-override-context", root=caps2) is None


def test_special_markers_resolve_empty(caps2: Path) -> None:
    for marker in ("__shared__", "__orphan__", "__skip__", "TBD", ""):
        assert rc.resolve_cap_ids("vitalia", marker, root=caps2) == set()


def test_functional_area_of_reverse(caps2: Path) -> None:
    assert rc.functional_area_of("vitalia", "inbox.adrian-inbox", root=caps2) == "adrian.inbox"
    assert rc.functional_area_of("vitalia", "no.existe", root=caps2) is None


def test_cap_id_of_path(caps2: Path) -> None:
    assert rc.cap_id_of(caps2 / "inbox/adrian-inbox.yaml", root=caps2) == "inbox.adrian-inbox"
