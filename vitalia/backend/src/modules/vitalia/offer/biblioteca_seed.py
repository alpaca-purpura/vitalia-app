# cap: lisa.servicios
"""Biblioteca seed — Tier-1 medical service presets (dental + estética).

Brand-local DATA for the EP-2 ``medical_services_v1`` preset pack. ``extensions.py``
imports and spreads :data:`MEDICAL_SERVICES_V1_PRESETS` into the ``PresetPack``;
``BibliotecaService`` reads it directly for name+synonym typeahead. This is NOT
agentic logic — pure curated data, scoped per ``clinic_type`` (``dental`` /
``estetica``). No ``_CATALOG_VERSION`` bump (it is a brand preset pack, not an
engine catalog). Each preset is an editable starting point — Lisa owns the copy.
"""

from __future__ import annotations

from typing import Any

# Curated Tier-1 library. Each dict is an editable prefill; ``synonyms`` power the
# typeahead so "fundas" surfaces "Carillas de porcelana" / "Diseño de sonrisa".
MEDICAL_SERVICES_V1_PRESETS: tuple[dict[str, Any], ...] = (
    {
        "canonical_ref": "diseno_de_sonrisa",
        "name": "Diseño de sonrisa",
        "synonyms": ["fundas", "carillas premium", "smile design"],
        "clinic_type": "dental",
        "category": "Estética dental",
        "modality": "sesiones",
        "keywords": ["estética dental", "sonrisa", "carillas"],
    },
    {
        "canonical_ref": "carillas_porcelana",
        "name": "Carillas de porcelana",
        "synonyms": ["fundas", "carillas", "veneers"],
        "clinic_type": "dental",
        "category": "Estética dental",
        "modality": "sesiones",
        "keywords": ["carillas", "porcelana", "estética dental"],
    },
    {
        "canonical_ref": "limpieza_dental",
        "name": "Limpieza dental",
        "synonyms": ["profilaxis", "destartraje", "higiene dental"],
        "clinic_type": "dental",
        "category": "Odontología general",
        "modality": "unica",
        "keywords": ["limpieza", "profilaxis", "higiene"],
    },
    {
        "canonical_ref": "ortodoncia_invisible",
        "name": "Ortodoncia invisible",
        "synonyms": ["alineadores", "invisalign", "férulas"],
        "clinic_type": "dental",
        "category": "Ortodoncia",
        "modality": "recurrente",
        "keywords": ["ortodoncia", "alineadores", "invisible"],
    },
    {
        "canonical_ref": "implante_dental",
        "name": "Implante dental",
        "synonyms": ["implantes", "tornillo dental"],
        "clinic_type": "dental",
        "category": "Implantología",
        "modality": "sesiones",
        "keywords": ["implante", "implantología"],
    },
    {
        "canonical_ref": "botox_facial",
        "name": "Botox facial",
        "synonyms": ["toxina botulínica", "bótox", "antiarrugas"],
        "clinic_type": "estetica",
        "category": "Medicina estética",
        "modality": "recurrente",
        "keywords": ["botox", "toxina botulínica", "arrugas"],
    },
    {
        "canonical_ref": "acido_hialuronico",
        "name": "Ácido hialurónico",
        "synonyms": ["rellenos", "fillers", "relleno facial"],
        "clinic_type": "estetica",
        "category": "Medicina estética",
        "modality": "recurrente",
        "keywords": ["ácido hialurónico", "rellenos", "fillers"],
    },
    {
        "canonical_ref": "limpieza_facial_profunda",
        "name": "Limpieza facial profunda",
        "synonyms": ["hydrafacial", "peeling", "facial"],
        "clinic_type": "estetica",
        "category": "Estética facial",
        "modality": "sesiones",
        "keywords": ["limpieza facial", "hydrafacial", "peeling"],
    },
    {
        "canonical_ref": "depilacion_laser",
        "name": "Depilación láser",
        "synonyms": ["láser", "depilación definitiva"],
        "clinic_type": "estetica",
        "category": "Estética corporal",
        "modality": "sesiones",
        "keywords": ["depilación", "láser", "definitiva"],
    },
)
