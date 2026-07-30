# cap: lisa.servicios
"""RED-first unit tests for BibliotecaService (T-2 § 6).

Typeahead over the EP-2 preset seed: matches on name + synonyms, scoped to the
tenant clinic_type. "Usar plantilla" returns an editable prefill carrying the
canonical_ref; "crear personalizado" path is handled by the catalog service
(canonical_ref=None), not here.
"""

from __future__ import annotations

from src.modules.vitalia.offer.application.services.biblioteca_service import BibliotecaService


def test_typeahead_matches_synonym_fundas_to_carillas():
    svc = BibliotecaService()
    results = svc.search(query="fundas", clinic_type="dental")
    refs = {r.canonical_ref for r in results}
    assert "carillas_porcelana" in refs
    assert "diseno_de_sonrisa" in refs  # also lists "fundas" as synonym


def test_typeahead_matches_name_prefix():
    svc = BibliotecaService()
    results = svc.search(query="botox", clinic_type="estetica")
    assert any(r.canonical_ref == "botox_facial" for r in results)


def test_typeahead_scoped_to_clinic_type():
    svc = BibliotecaService()
    # "limpieza" exists in BOTH dental (limpieza_dental) and estetica (limpieza_facial)
    dental = {r.canonical_ref for r in svc.search(query="limpieza", clinic_type="dental")}
    estetica = {r.canonical_ref for r in svc.search(query="limpieza", clinic_type="estetica")}
    assert "limpieza_dental" in dental
    assert "limpieza_dental" not in estetica
    assert "limpieza_facial_profunda" in estetica


def test_empty_query_lists_all_for_clinic_type():
    svc = BibliotecaService()
    dental = svc.search(query="", clinic_type="dental")
    assert len(dental) >= 1
    assert all(r.clinic_type == "dental" for r in dental)


def test_get_template_returns_prefill_with_canonical_ref():
    svc = BibliotecaService()
    prefill = svc.get_template(canonical_ref="botox_facial")
    assert prefill is not None
    assert prefill.canonical_ref == "botox_facial"
    assert prefill.name == "Botox facial"
    assert prefill.category == "Medicina estética"


def test_get_template_unknown_ref_returns_none():
    svc = BibliotecaService()
    assert svc.get_template(canonical_ref="does_not_exist") is None
