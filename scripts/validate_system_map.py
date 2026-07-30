#!/usr/bin/env python3
"""
validate_system_map.py — Valida coherencia cross-vocabulario SYSTEM-MAP vs caps/stories.

Lee:
- {brand}/docs/architecture/SYSTEM-MAP.yaml (vocabulario canónico)
- {brand}/docs/product/capabilities/{module}/*.yaml (functional_area declaradas)
- {brand}/docs/product/stories/{id}/checkpoint.md (cap_target declarados)

Valida (3 checks):
1. Cada `functional_area:` en caps DEBE existir en SYSTEM-MAP.
2. Cada `cap_target:` en stories activas DEBE existir en SYSTEM-MAP.
3. Advisory: áreas `status: planned` por > 6 meses sin caps shipped.

ADR: vitalia/docs/architecture/ADR-vitalia-005-capability-model-4-dimensions.md
SSoT: docs/process/capability-protocol.md Sec 7-9 (v3 cement 2026-05-27).

Uso:
    python3 scripts/validate_system_map.py --brand vitalia
    python3 scripts/validate_system_map.py --brand vitalia --strict   (exit 1 si advisories)
    python3 scripts/validate_system_map.py --all-brands
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_system_map(brand_dir: Path) -> dict[str, Any] | None:
    sm_path = brand_dir / "docs" / "architecture" / "SYSTEM-MAP.yaml"
    if not sm_path.exists():
        return None
    try:
        return yaml.safe_load(sm_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        print(f"ERROR parsing {sm_path}: {e}", file=sys.stderr)
        return None


def extract_valid_areas(system_map: dict[str, Any]) -> set[str]:
    """Retorna set de functional_area válidos declarados en SYSTEM-MAP.

    Incluye:
    - Legacy format: `<agent>.<area>` (from agents[].functional_areas[])
    - v2.0 promoted boxes: `<box>.<area>` (from zones[].boxes[].functional_areas[])
    - v1.x draft target_boxes: `<box>.*` wildcard (from zones[].target_boxes[].id)

    Backward-compat: legacy agent.area format preserved during transition.
    """
    valid = set()

    # Legacy: agent.area format from agents[] (back-compat for specialist agents)
    for agent in system_map.get("agents", []):
        agent_id = agent.get("id")
        agent_fa = agent.get("functional_areas", [])
        # functional_areas can be a list of dicts or empty list
        if isinstance(agent_fa, list):
            for area in agent_fa:
                if isinstance(area, dict):
                    area_id = area.get("id")
                    if agent_id and area_id:
                        valid.add(f"{agent_id}.{area_id}")

    # v2.0: boxes are now first-class objects in zones[].boxes[]
    # Each box has functional_areas[] with explicit area ids
    for zone in system_map.get("zones", []):
        zone_boxes = zone.get("boxes", [])

        if isinstance(zone_boxes, list):
            for box in zone_boxes:
                if isinstance(box, str):
                    # v1.x format: boxes is a list of strings → wildcard accept
                    valid.add(f"{box}.*")
                elif isinstance(box, dict):
                    # v2.0 format: boxes is a list of objects with functional_areas
                    box_id = box.get("id")
                    if not box_id:
                        continue
                    # Accept box.* wildcard (for back-compat caps with any sub-area)
                    valid.add(f"{box_id}.*")
                    # Also accept explicit functional_area ids registered in the box
                    for fa in box.get("functional_areas", []):
                        if isinstance(fa, dict):
                            fa_id = fa.get("id")
                            if fa_id:
                                valid.add(f"{box_id}.{fa_id}")

        # v1.x: target_boxes still present as migration reference → accept as wildcards
        for tb in zone.get("target_boxes", []):
            if isinstance(tb, dict):
                box_id = tb.get("id")
                if box_id:
                    valid.add(f"{box_id}.*")

    return valid


def extract_valid_boxes(system_map: dict[str, Any]) -> set[str]:
    """Retorna set de box IDs válidos (12 cajas del mapa · v2.0).

    Incluye cajas de 1er nivel de zones[].boxes (string o object) y
    target_boxes[].id (para back-compat v1.x). También incluye IDs de
    agents[] como box válido (especialistas: lisa, mateo, adrian, lucas, camila).
    """
    valid_boxes: set[str] = set()

    for zone in system_map.get("zones", []):
        for box in zone.get("boxes", []):
            if isinstance(box, str):
                valid_boxes.add(box)
            elif isinstance(box, dict):
                box_id = box.get("id")
                if box_id:
                    valid_boxes.add(box_id)
        for tb in zone.get("target_boxes", []):
            if isinstance(tb, dict):
                box_id = tb.get("id")
                if box_id:
                    valid_boxes.add(box_id)

    # Agents are valid boxes too (specialist agents: lisa, mateo, adrian, lucas, camila)
    for agent in system_map.get("agents", []):
        agent_id = agent.get("id")
        if agent_id:
            valid_boxes.add(agent_id)

    return valid_boxes


def extract_zone_for_box(system_map: dict[str, Any]) -> dict[str, str]:
    """Retorna mapa box_id → zone_id para validar user_visible coherente."""
    box_to_zone: dict[str, str] = {}

    for zone in system_map.get("zones", []):
        zone_id = zone.get("id", "")
        for box in zone.get("boxes", []):
            if isinstance(box, str):
                box_to_zone[box] = zone_id
            elif isinstance(box, dict):
                box_id = box.get("id")
                if box_id:
                    box_to_zone[box_id] = zone_id
        for tb in zone.get("target_boxes", []):
            if isinstance(tb, dict):
                box_id = tb.get("id")
                if box_id:
                    box_to_zone[box_id] = zone_id

    # Agents belong to "agentes" zone
    for agent in system_map.get("agents", []):
        agent_id = agent.get("id")
        if agent_id and agent_id not in box_to_zone:
            box_to_zone[agent_id] = "agentes"

    return box_to_zone


def is_valid_area(fa: str, valid_areas: set[str]) -> bool:
    """Check if a functional_area is valid (exact match or box.* wildcard)."""
    if fa in valid_areas:
        return True
    # Check box.* wildcard: if fa is "acceso.auth", check if "acceso.*" is in valid
    if "." in fa:
        prefix, _ = fa.split(".", 1)
        if f"{prefix}.*" in valid_areas:
            return True
    return False


def extract_caps_functional_areas(brand_dir: Path) -> list[tuple[Path, str]]:
    """Retorna lista de (path, functional_area) de todos los cap YAMLs."""
    caps_dir = brand_dir / "docs" / "product" / "capabilities"
    if not caps_dir.exists():
        return []
    results = []
    for module_dir in sorted(caps_dir.iterdir()):
        if not module_dir.is_dir() or module_dir.name.startswith("_"):
            continue
        for yaml_file in sorted(module_dir.glob("*.yaml")):
            if yaml_file.name.startswith("_"):
                continue
            try:
                content = yaml_file.read_text(encoding="utf-8")
                if content.startswith("---\n"):
                    parts = content.split("\n---\n", 2)
                    yaml_text = parts[0][4:] if len(parts) >= 2 else content[4:]
                elif "\n---\n" in content:
                    yaml_text = content.split("\n---\n", 1)[0]
                else:
                    yaml_text = content
                data = yaml.safe_load(yaml_text) or {}
                if not isinstance(data, dict):
                    continue
                fa = data.get("functional_area")
                if fa:
                    results.append((yaml_file, fa))
            except (yaml.YAMLError, OSError):
                continue
    return results


def extract_stories_cap_targets(brand_dir: Path) -> list[tuple[Path, str]]:
    """Retorna lista de (path, cap_target) de stories activas (no archived)."""
    stories_dir = brand_dir / "docs" / "product" / "stories"
    if not stories_dir.exists():
        return []
    results = []
    for story_dir in sorted(stories_dir.iterdir()):
        if not story_dir.is_dir():
            continue
        cp = story_dir / "checkpoint.md"
        if not cp.exists():
            continue
        try:
            content = cp.read_text(encoding="utf-8")
            if not content.startswith("---\n"):
                continue
            parts = content.split("\n---\n", 2)
            if len(parts) < 2:
                continue
            yaml_text = parts[0][4:]
            data = yaml.safe_load(yaml_text) or {}
            cap_target = data.get("cap_target")
            if cap_target and cap_target != "null":
                results.append((cp, cap_target))
        except (yaml.YAMLError, OSError):
            continue
    return results


def find_planned_old_areas(
    system_map: dict[str, Any],
    caps_areas: list[tuple[Path, str]],
    threshold_days: int = 180,
) -> list[tuple[str, str, str | None]]:
    """Retorna lista de (full_id, name, target_release) de áreas planned > N días sin caps."""
    cement_date_str = system_map.get("cement_date") or system_map.get("metadata", {}).get("last_modified")
    if not cement_date_str:
        return []
    try:
        cement_date = datetime.fromisoformat(cement_date_str)
    except (ValueError, TypeError):
        return []

    now = datetime.now()
    threshold = now - timedelta(days=threshold_days)
    if cement_date > threshold:
        # SYSTEM-MAP es reciente · ningún área puede ser old todavía
        return []

    # Set de áreas con caps shipped
    areas_with_caps = {fa for _, fa in caps_areas}

    old_planned = []
    for agent in system_map.get("agents", []):
        agent_id = agent.get("id")
        for area in agent.get("functional_areas", []):
            full_id = f"{agent_id}.{area.get('id')}"
            if area.get("status") == "planned" and full_id not in areas_with_caps:
                old_planned.append((full_id, area.get("name"), area.get("target_release")))
    return old_planned


def validate_brand(brand: str, strict: bool = False) -> bool:
    """Valida el SYSTEM-MAP de un brand. Retorna True si pasa."""
    brand_dir = REPO_ROOT / brand
    if not brand_dir.exists():
        print(f"ERROR: brand dir no existe: {brand_dir}", file=sys.stderr)
        return False

    system_map = load_system_map(brand_dir)
    if system_map is None:
        print(f"INFO: brand {brand} no tiene SYSTEM-MAP.yaml todavía. Skip.")
        return True

    valid_areas = extract_valid_areas(system_map)
    valid_boxes = extract_valid_boxes(system_map)
    box_to_zone = extract_zone_for_box(system_map)

    # Zones where user_visible should be False
    infra_zones = {z.get("id") for z in system_map.get("zones", []) if not z.get("user_visible", True)}

    print(f"=== {brand} ===")
    print(f"  SYSTEM-MAP areas válidas: {len(valid_areas)}")
    print(f"  SYSTEM-MAP boxes válidos (12 target): {len(valid_boxes)}")

    all_ok = True
    errors: list[str] = []
    warnings: list[str] = []

    # Check 1: caps functional_area en SYSTEM-MAP (map_box-aware · back-compat)
    caps_areas = extract_caps_functional_areas(brand_dir)
    print(f"  Caps con functional_area declarada: {len(caps_areas)}")
    for cap_path, fa in caps_areas:
        if not is_valid_area(fa, valid_areas):
            rel_path = cap_path.relative_to(REPO_ROOT).as_posix()
            errors.append(
                f"CAP_FA_NOT_IN_SYSTEM_MAP: {rel_path} declara functional_area='{fa}' que NO existe en SYSTEM-MAP.yaml"
            )

    # Check 1b: caps map_box (if present) debe estar en valid_boxes — NEW v2.0 (map_box-aware)
    caps_dir = brand_dir / "docs" / "product" / "capabilities"
    if caps_dir.exists():
        for module_dir in sorted(caps_dir.iterdir()):
            if not module_dir.is_dir() or module_dir.name.startswith("_"):
                continue
            for yaml_file in sorted(module_dir.glob("*.yaml")):
                if yaml_file.name.startswith("_"):
                    continue
                try:
                    content = yaml_file.read_text(encoding="utf-8")
                    if content.startswith("---\n"):
                        parts = content.split("\n---\n", 2)
                        yaml_text = parts[0][4:] if len(parts) >= 2 else content[4:]
                    elif "\n---\n" in content:
                        yaml_text = content.split("\n---\n", 1)[0]
                    else:
                        yaml_text = content
                    data = yaml.safe_load(yaml_text) or {}
                    if not isinstance(data, dict):
                        continue
                    map_box = data.get("map_box")
                    if not map_box:
                        continue
                    rel_path = yaml_file.relative_to(REPO_ROOT).as_posix()
                    # Check: map_box must be a valid box
                    if map_box not in valid_boxes:
                        errors.append(
                            f"CAP_MAP_BOX_NOT_IN_SYSTEM_MAP: {rel_path} declara map_box='{map_box}' que NO existe en SYSTEM-MAP.yaml zones"
                        )
                    else:
                        # Check user_visible coherence: Infra zone → user_visible must be false
                        zone_id = box_to_zone.get(map_box, "")
                        user_visible = data.get("user_visible")
                        if zone_id in infra_zones and user_visible is True:
                            warnings.append(
                                f"CAP_USER_VISIBLE_MISMATCH: {rel_path} tiene map_box='{map_box}' (zona infra) pero user_visible=true (debería ser false)"
                            )
                except (yaml.YAMLError, OSError):
                    continue

    # Check 2: stories cap_target en SYSTEM-MAP
    stories_targets = extract_stories_cap_targets(brand_dir)
    print(f"  Stories con cap_target declarado: {len(stories_targets)}")
    for story_path, ct in stories_targets:
        # cap_target puede ser "<agent>.<area>", "<box>.<sub>", o "<slug-de-cap-existente>" (legacy)
        if "." in ct and not is_valid_area(ct, valid_areas):
            rel_path = story_path.relative_to(REPO_ROOT).as_posix()
            errors.append(
                f"STORY_CAP_TARGET_NOT_IN_SYSTEM_MAP: {rel_path} declara cap_target='{ct}' que NO existe en SYSTEM-MAP.yaml"
            )

    # Check 3: áreas planned > 6 meses sin caps (advisory)
    old_planned = find_planned_old_areas(system_map, caps_areas, threshold_days=180)
    for full_id, name, target_release in old_planned:
        warnings.append(
            f"PLANNED_AREA_STALE: {full_id} ({name}) sin caps shipped por > 6 meses · target_release: {target_release} · ¿considerar parked/dropped?"
        )

    # Report
    if errors:
        print(f"\n  ❌ {len(errors)} ERRORS:")
        for e in errors:
            print(f"    {e}")
        all_ok = False

    if warnings:
        print(f"\n  ⚠️ {len(warnings)} WARNINGS:")
        for w in warnings:
            print(f"    {w}")
        if strict:
            all_ok = False

    if not errors and not warnings:
        print("  ✅ PASS (cero issues)")

    return all_ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brand", help="Brand slug")
    parser.add_argument("--all-brands", action="store_true", help="Iterate all brands with SYSTEM-MAP")
    parser.add_argument("--strict", action="store_true", help="Exit 1 también si solo hay warnings")
    args = parser.parse_args()

    if not args.brand and not args.all_brands:
        parser.error("--brand SLUG o --all-brands requerido")

    if args.all_brands:
        brands = []
        for d in REPO_ROOT.iterdir():
            if d.is_dir() and (d / "docs" / "architecture" / "SYSTEM-MAP.yaml").exists():
                brands.append(d.name)
    else:
        brands = [args.brand]

    all_ok = True
    for brand in brands:
        ok = validate_brand(brand, args.strict)
        all_ok = all_ok and ok
        print()

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
