# cap: platform.product-map-zonas
"""Tests for scripts/map_zones_migration.py.

TDD RED-first per tdd-mandatory.md + test-design-doctrine.md.
Naturaleza: script de migración → contract tests (halt/idempotencia/box-invalid/full-retag).

Tests:
  - test_unmapped_cap_halts (SC-3): cap sin mapeo → exit 1 + lista, no escribe default
  - test_rerun_is_noop (SC-4): segunda corrida = cero diffs (idempotencia)
  - test_invalid_box_rejected (SC-5): box inventado → HALT
  - test_config_infra_valeria_fully_retagged (SC-1): todas las caps retageadas correctamente
  - test_valeria_agenda_to_mateo: valeria.agenda → agent_owner:mateo + map_box:mateo
  - test_valeria_shell_to_plataforma_tecnica: valeria.shell → map_box:plataforma-tecnica
  - test_user_visible_aligned_to_zone: Infra caps → user_visible: false
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Module loader helper
# ---------------------------------------------------------------------------


def _load_module():
    """Load map_zones_migration.py as module (without executing main)."""
    scripts_dir = Path(__file__).parent.parent
    spec = importlib.util.spec_from_file_location(
        "map_zones_migration",
        scripts_dir / "map_zones_migration.py",
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules["map_zones_migration"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# Fixtures: SYSTEM-MAP + cap YAMLs in tmp_path
# ---------------------------------------------------------------------------

SYSTEM_MAP_MINIMAL = {
    "brand": "vitalia",
    "version": "2.0",
    "zones": [
        {
            "id": "agentes",
            "name": "Agentes",
            "tier": "core",
            "user_visible": True,
            # v2.0: agent boxes are plain strings (no absorbs — agent_owner drives mapping)
            "boxes": ["lisa", "mateo", "adrian", "lucas", "camila"],
            "notes": "",
        },
        {
            "id": "plataforma",
            "name": "Plataforma",
            "tier": "supporting",
            "user_visible": True,
            "legacy_home": "config",
            # v2.0: boxes are objects with id + absorbs (target_boxes promoted to 1st-level)
            "boxes": [
                {"id": "acceso", "name": "Acceso", "absorbs": ["config.auth", "config.iam"]},
                {"id": "onboarding", "name": "Onboarding", "absorbs": ["config.onboarding_clinic"]},
                {
                    "id": "configuracion",
                    "name": "Configuración",
                    "absorbs": [
                        "config.cuenta",
                        "config.clinics",
                        "config.conexiones",
                        "config.patients-records",
                        "config.admin",
                        "config.avanzado",
                    ],
                },
            ],
        },
        {
            "id": "infraestructura",
            "name": "Infraestructura",
            "tier": "enabling",
            "user_visible": False,
            "legacy_home": "infra",
            # v2.0: boxes are objects with id + absorbs (target_boxes promoted to 1st-level)
            "boxes": [
                {
                    "id": "seguridad-cumplimiento",
                    "name": "Seguridad & Cumplimiento",
                    "absorbs": ["config.compliance", "infra.scaffolding"],
                },
                {"id": "observabilidad", "name": "Observabilidad", "absorbs": ["infra.observability"]},
                {
                    "id": "plataforma-tecnica",
                    "name": "Plataforma técnica",
                    "absorbs": ["infra.platform", "infra.payment"],
                },
                {
                    "id": "motor-agentico",
                    "name": "Motor agéntico",
                    "absorbs": ["infra.copilot", "infra.agentic-engine", "infra.sales-agent-engine"],
                },
            ],
        },
    ],
    "agents": [
        {"id": "lisa", "functional_areas": [{"id": "marca"}, {"id": "servicios"}]},
        {"id": "mateo", "functional_areas": [{"id": "agenda"}, {"id": "bookings"}]},
        {"id": "adrian", "functional_areas": [{"id": "embudo"}, {"id": "crm"}]},
        {"id": "lucas", "functional_areas": [{"id": "atribucion"}, {"id": "bowtie"}]},
        {"id": "camila", "functional_areas": [{"id": "reputacion"}, {"id": "reactivar"}]},
        {"id": "config", "functional_areas": []},
        {"id": "infra", "functional_areas": []},
        {"id": "valeria", "functional_areas": [{"id": "agenda"}, {"id": "bookings"}, {"id": "shell"}]},
    ],
    "cross_agent_flows": [],
    "data_ownership": {},
    "agent_orchestration": [],
    "metadata": {
        "last_modified": "2026-05-30",
        "schema_version": "2.0",
    },
}


def _write_system_map(base: Path, sm: dict | None = None) -> Path:
    arch_dir = base / "vitalia" / "docs" / "architecture"
    arch_dir.mkdir(parents=True, exist_ok=True)
    sm_path = arch_dir / "SYSTEM-MAP.yaml"
    sm_path.write_text(yaml.dump(sm or SYSTEM_MAP_MINIMAL, allow_unicode=True))
    return sm_path


def _write_cap(caps_dir: Path, module: str, slug: str, fields: dict) -> Path:
    """Write a minimal cap YAML file under caps_dir/{module}/{slug}.yaml."""
    mod_dir = caps_dir / module
    mod_dir.mkdir(parents=True, exist_ok=True)
    cap_path = mod_dir / f"{slug}.yaml"

    defaults = {
        "capability_id": f"vitalia.{module}.{slug}",
        "slug": slug,
        "status": "live",
        "tech_module": module,
        "module": module,
        "nature": "feature",
        "user_visible": True,
    }
    defaults.update(fields)

    # Write as YAML frontmatter (--- header ---\n body)
    cap_path.write_text("---\n" + yaml.dump(defaults, allow_unicode=True) + "---\n\n# body\n")
    return cap_path


def _setup_brand(tmp_path: Path) -> tuple[Path, Path]:
    """Create brand dir structure, return (brand_dir, caps_dir)."""
    brand_dir = tmp_path / "vitalia"
    caps_dir = brand_dir / "docs" / "product" / "capabilities"
    caps_dir.mkdir(parents=True, exist_ok=True)
    _write_system_map(tmp_path)
    return brand_dir, caps_dir


# ---------------------------------------------------------------------------
# SC-3: HALT-no-silent if cap cannot be mapped
# ---------------------------------------------------------------------------


def test_unmapped_cap_halts(tmp_path):
    """SC-3: cap with functional_area not in any absorbs + not a known slug override
    must cause HALT (exit 1) and print the unmapped cap. NEVER assigns default."""
    mod = _load_module()
    _, caps_dir = _setup_brand(tmp_path)

    # Cap with an area that doesn't match any absorbs (config.unknown_area)
    _write_cap(
        caps_dir,
        "custom",
        "unknown-cap",
        {
            "agent_owner": "config",
            "functional_area": "config.unknown_area",  # NOT in SYSTEM-MAP absorbs
        },
    )

    with pytest.raises(SystemExit) as exc_info:
        mod.run_migration(
            brand_dir=tmp_path / "vitalia",
            repo_root=tmp_path,
            dry_run=False,
            apply=True,
            strict=True,
        )
    assert exc_info.value.code == 1, "Must exit 1 when caps cannot be mapped"

    # Verify the file was NOT written a default box
    cap_file = caps_dir / "custom" / "unknown-cap.yaml"
    content = cap_file.read_text()
    assert "map_box" not in content, "HALT-no-silent: should not write default map_box"


# ---------------------------------------------------------------------------
# SC-4: Idempotency — re-run is no-op
# ---------------------------------------------------------------------------


def test_rerun_is_noop(tmp_path):
    """SC-4: Running migration twice produces no additional diffs."""
    mod = _load_module()
    _, caps_dir = _setup_brand(tmp_path)

    _write_cap(
        caps_dir,
        "auth",
        "clerk-middleware",
        {
            "agent_owner": "config",
            "functional_area": "config.auth",
            "user_visible": True,
        },
    )

    brand_dir = tmp_path / "vitalia"

    # First run
    mod.run_migration(
        brand_dir=brand_dir,
        repo_root=tmp_path,
        dry_run=False,
        apply=True,
    )

    # Read content after first run
    cap_path = caps_dir / "auth" / "clerk-middleware.yaml"
    content_after_first = cap_path.read_text()

    # Second run
    mod.run_migration(
        brand_dir=brand_dir,
        repo_root=tmp_path,
        dry_run=False,
        apply=True,
    )

    content_after_second = cap_path.read_text()
    assert content_after_first == content_after_second, "Idempotency violated: second run produced different output"


# ---------------------------------------------------------------------------
# SC-5: Invalid box rejected
# ---------------------------------------------------------------------------


def test_invalid_box_rejected(tmp_path):
    """SC-5: A cap with a fabricated map_box should fail validation.
    The migration script must reject caps that derive to an invalid box."""
    mod = _load_module()
    _, caps_dir = _setup_brand(tmp_path)

    # Write a cap that already has a fabricated/invalid map_box
    _write_cap(
        caps_dir,
        "auth",
        "clerk-middleware",
        {
            "agent_owner": "config",
            "functional_area": "config.auth",
            "map_box": "caja-inventada",  # INVALID box
            "user_visible": True,
        },
    )

    brand_dir = tmp_path / "vitalia"

    # Validation should reject invalid map_box values
    with pytest.raises(SystemExit) as exc_info:
        mod.run_migration(
            brand_dir=brand_dir,
            repo_root=tmp_path,
            dry_run=False,
            apply=True,
            strict=True,
        )
    assert exc_info.value.code == 1, "Should exit 1 when a cap has invalid map_box"


# ---------------------------------------------------------------------------
# SC-1: Full retag — config/infra/valeria fully retagged
# ---------------------------------------------------------------------------


def test_config_infra_valeria_fully_retagged(tmp_path):
    """SC-1: After migration, all config/infra/valeria agent_owner caps
    have map_box set correctly per the absorbs table."""
    mod = _load_module()
    _, caps_dir = _setup_brand(tmp_path)

    # A set of representative caps
    test_caps = [
        ("auth", "clerk-middleware", {"agent_owner": "config", "functional_area": "config.auth", "user_visible": True}),
        ("iam", "iam-scaffold", {"agent_owner": "config", "functional_area": "config.iam", "user_visible": True}),
        (
            "onboarding",
            "clinic-onboarding",
            {"agent_owner": "config", "functional_area": "config.onboarding_clinic", "user_visible": True},
        ),
        ("admin", "admin-service", {"agent_owner": "config", "functional_area": "config.admin", "user_visible": True}),
        (
            "compliance",
            "hipaa-lite",
            {"agent_owner": "config", "functional_area": "config.compliance", "user_visible": True},
        ),
        (
            "observability",
            "api-health",
            {"agent_owner": "infra", "functional_area": "infra.observability", "user_visible": False},
        ),
        (
            "platform",
            "design-tokens",
            {"agent_owner": "infra", "functional_area": "infra.platform", "user_visible": False},
        ),
        (
            "copilot",
            "medical-kb-rag",
            {"agent_owner": "infra", "functional_area": "infra.copilot", "user_visible": False},
        ),
        (
            "agentic",
            "eval-goldens",
            {"agent_owner": "infra", "functional_area": "infra.agentic-engine", "user_visible": False},
        ),
        (
            "payment",
            "payment-gateways",
            {"agent_owner": "infra", "functional_area": "infra.payment", "user_visible": False},
        ),
        (
            "scheduling",
            "valeria-agenda",
            {"agent_owner": "valeria", "functional_area": "valeria.agenda", "user_visible": True},
        ),
        (
            "booking",
            "booking-widget",
            {"agent_owner": "valeria", "functional_area": "valeria.bookings", "user_visible": True},
        ),
        (
            "shell-organism",
            "shell-vitalia",
            {"agent_owner": "valeria", "functional_area": "valeria.shell", "user_visible": True},
        ),
    ]

    for module, slug, fields in test_caps:
        _write_cap(caps_dir, module, slug, fields)

    brand_dir = tmp_path / "vitalia"
    mod.run_migration(
        brand_dir=brand_dir,
        repo_root=tmp_path,
        dry_run=False,
        apply=True,
    )

    # Expected mappings
    expected = {
        ("auth", "clerk-middleware"): ("acceso", True),
        ("iam", "iam-scaffold"): ("acceso", True),
        ("onboarding", "clinic-onboarding"): ("onboarding", True),
        ("admin", "admin-service"): ("configuracion", True),
        ("compliance", "hipaa-lite"): ("seguridad-cumplimiento", False),
        ("observability", "api-health"): ("observabilidad", False),
        ("platform", "design-tokens"): ("plataforma-tecnica", False),
        ("copilot", "medical-kb-rag"): ("motor-agentico", False),
        ("agentic", "eval-goldens"): ("motor-agentico", False),
        ("payment", "payment-gateways"): ("plataforma-tecnica", False),
        ("scheduling", "valeria-agenda"): ("mateo", True),
        ("booking", "booking-widget"): ("mateo", True),
        ("shell-organism", "shell-vitalia"): ("plataforma-tecnica", False),
    }

    for (module, slug), (expected_box, expected_visible) in expected.items():
        cap_path = caps_dir / module / f"{slug}.yaml"
        content = cap_path.read_text()
        if content.startswith("---\n"):
            parts = content.split("\n---\n", 2)
            yaml_text = parts[0][4:] if len(parts) >= 2 else content[4:]
        else:
            yaml_text = content
        data = yaml.safe_load(yaml_text) or {}

        assert data.get("map_box") == expected_box, (
            f"{module}/{slug}: expected map_box={expected_box!r}, got {data.get('map_box')!r}"
        )
        assert data.get("user_visible") == expected_visible, (
            f"{module}/{slug}: expected user_visible={expected_visible}, got {data.get('user_visible')}"
        )


# ---------------------------------------------------------------------------
# Valeria agenda/bookings → mateo
# ---------------------------------------------------------------------------


def test_valeria_agenda_to_mateo(tmp_path):
    """valeria.agenda caps must get agent_owner: mateo + map_box: mateo."""
    mod = _load_module()
    _, caps_dir = _setup_brand(tmp_path)

    _write_cap(
        caps_dir,
        "scheduling",
        "valeria-agenda",
        {
            "agent_owner": "valeria",
            "functional_area": "valeria.agenda",
            "user_visible": True,
        },
    )

    brand_dir = tmp_path / "vitalia"
    mod.run_migration(brand_dir=brand_dir, repo_root=tmp_path, dry_run=False, apply=True)

    cap_path = caps_dir / "scheduling" / "valeria-agenda.yaml"
    content = cap_path.read_text()
    if content.startswith("---\n"):
        parts = content.split("\n---\n", 2)
        yaml_text = parts[0][4:] if len(parts) >= 2 else content[4:]
    else:
        yaml_text = content
    data = yaml.safe_load(yaml_text) or {}

    assert data["agent_owner"] == "mateo"
    assert data["map_box"] == "mateo"
    assert data["user_visible"] is True


# ---------------------------------------------------------------------------
# Shell (valeria.shell) → plataforma-tecnica / Infra
# ---------------------------------------------------------------------------


def test_valeria_shell_to_plataforma_tecnica(tmp_path):
    """valeria.shell must go to plataforma-tecnica (Infra, user_visible: false)."""
    mod = _load_module()
    _, caps_dir = _setup_brand(tmp_path)

    _write_cap(
        caps_dir,
        "shell-organism",
        "shell-vitalia",
        {
            "agent_owner": "valeria",
            "functional_area": "valeria.shell",
            "user_visible": True,  # must be flipped to False (Infra zone)
        },
    )

    brand_dir = tmp_path / "vitalia"
    mod.run_migration(brand_dir=brand_dir, repo_root=tmp_path, dry_run=False, apply=True)

    cap_path = caps_dir / "shell-organism" / "shell-vitalia.yaml"
    content = cap_path.read_text()
    if content.startswith("---\n"):
        parts = content.split("\n---\n", 2)
        yaml_text = parts[0][4:] if len(parts) >= 2 else content[4:]
    else:
        yaml_text = content
    data = yaml.safe_load(yaml_text) or {}

    assert data["map_box"] == "plataforma-tecnica"
    assert data["user_visible"] is False


# ---------------------------------------------------------------------------
# user_visible must align to zone (Infra → false)
# ---------------------------------------------------------------------------


def test_user_visible_aligned_to_zone(tmp_path):
    """All Infraestructura caps must have user_visible: false after migration."""
    mod = _load_module()
    _, caps_dir = _setup_brand(tmp_path)

    infra_caps = [
        ("observability", "api-health", "infra.observability"),
        ("platform", "tokens", "infra.platform"),
        ("copilot", "rag", "infra.copilot"),
        ("agentic", "tools", "infra.agentic-engine"),
    ]
    for module, slug, fa in infra_caps:
        _write_cap(
            caps_dir,
            module,
            slug,
            {
                "agent_owner": "infra",
                "functional_area": fa,
                "user_visible": True,  # all set to True — must flip to False
            },
        )

    brand_dir = tmp_path / "vitalia"
    mod.run_migration(brand_dir=brand_dir, repo_root=tmp_path, dry_run=False, apply=True)

    for module, slug, _ in infra_caps:
        cap_path = caps_dir / module / f"{slug}.yaml"
        content = cap_path.read_text()
        if content.startswith("---\n"):
            parts = content.split("\n---\n", 2)
            yaml_text = parts[0][4:] if len(parts) >= 2 else content[4:]
        else:
            yaml_text = content
        data = yaml.safe_load(yaml_text) or {}
        assert data["user_visible"] is False, (
            f"{module}/{slug} is Infra zone but user_visible={data.get('user_visible')!r}"
        )


# ---------------------------------------------------------------------------
# dry_run: no writes
# ---------------------------------------------------------------------------


def test_dry_run_does_not_write(tmp_path):
    """--dry-run must not modify any file."""
    mod = _load_module()
    _, caps_dir = _setup_brand(tmp_path)

    _write_cap(
        caps_dir,
        "auth",
        "clerk-middleware",
        {
            "agent_owner": "config",
            "functional_area": "config.auth",
            "user_visible": True,
        },
    )

    cap_path = caps_dir / "auth" / "clerk-middleware.yaml"
    original_content = cap_path.read_text()

    brand_dir = tmp_path / "vitalia"
    mod.run_migration(brand_dir=brand_dir, repo_root=tmp_path, dry_run=True, apply=False)

    assert cap_path.read_text() == original_content, "dry_run must not modify files"


# ---------------------------------------------------------------------------
# Already-fully-tagged cap (idempotency: no double-apply)
# ---------------------------------------------------------------------------


def test_already_tagged_cap_unchanged(tmp_path):
    """Cap that already has the correct map_box AND correct functional_area must not be modified.
    Idempotence: after a first run sets everything, a second run produces no diff."""
    mod = _load_module()
    _, caps_dir = _setup_brand(tmp_path)

    # Write cap FULLY migrated (agent_owner + map_box + functional_area all correct post-migration)
    _write_cap(
        caps_dir,
        "auth",
        "clerk-middleware",
        {
            "agent_owner": "acceso",  # agent_owner updated from config→acceso
            "functional_area": "acceso.auth",  # already re-mapped (post first-run value)
            "map_box": "acceso",
            "user_visible": True,
        },
    )

    cap_path = caps_dir / "auth" / "clerk-middleware.yaml"
    before = cap_path.read_text()

    brand_dir = tmp_path / "vitalia"
    mod.run_migration(brand_dir=brand_dir, repo_root=tmp_path, dry_run=False, apply=True)

    after = cap_path.read_text()
    assert before == after, "Already-fully-correct cap must not be re-written (idempotent)"
