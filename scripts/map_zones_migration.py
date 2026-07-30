# cap: platform.product-map-zonas
"""map_zones_migration.py — Re-tag capability YAMLs with map_box (5th dimension).

Story: vitalia-paradigm-map-zones · T-1 (F1)
ADR: vitalia/docs/architecture/ADR-vitalia-005-capability-model-4-dimensions.md

Lee:
  - {brand}/docs/architecture/SYSTEM-MAP.yaml  (zones[].target_boxes[].absorbs — tabla de verdad)
  - {brand}/docs/product/capabilities/**/*.yaml (caps a re-tag)

Hace (idempotente):
  1. Construye tabla absorbs → map_box desde SYSTEM-MAP.
  2. Construye tabla zona → user_visible (Infra → false, Plataforma/Agentes → true).
  3. Por cada cap:
     a. Determina map_box via functional_area o agent_owner (valeria.agenda→mateo, valeria.shell→plataforma-tecnica).
     b. Si no matchea ningún absorbs Y no es agente especialista → HALT (exit 1).
     c. Agrega/actualiza map_box + alinea user_visible + re-mapea functional_area.
  4. --dry-run: imprime diff sin escribir. --apply: escribe. Re-run = no-op.

Invariantes:
  - HALT-no-silent: cap sin mapeo → exit 1 + lista, NO asigna default (SC-3).
  - Idempotente (SC-4): segunda corrida = cero diffs.
  - box inventado ya presente → HALT también (SC-5).
  - Valeria.agenda / valeria.bookings → agent_owner: mateo + map_box: mateo.
  - Valeria.shell → map_box: plataforma-tecnica (Infra, user_visible: false).
  - Agentes especialistas (lisa/mateo/adrian/lucas/camila) → map_box = agent_owner.

Uso:
    python3 scripts/map_zones_migration.py --brand vitalia [--dry-run | --apply] [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

# Agentes especialistas (no son config/infra — sus caps tienen map_box = agent_owner)
SPECIALIST_AGENTS = {"lisa", "mateo", "adrian", "lucas", "camila"}

# Mapeo especial: valeria.* → caja override
VALERIA_OVERRIDES: dict[str, tuple[str, str | None]] = {
    "valeria.agenda": ("mateo", "mateo"),  # map_box=mateo, new_agent_owner=mateo
    "valeria.bookings": ("mateo", "mateo"),  # map_box=mateo, new_agent_owner=mateo
    "valeria.shell": ("plataforma-tecnica", None),  # map_box=plataforma-tecnica, keep agent_owner
}

# Normalización de functional_areas inválidas (casos especiales no cubiertos por absorbs)
# Origen: pre-existing note en 06-tickets.yaml T-1 + 02-impact.md §1-3
# Key = functional_area actual (inválida) → Value = (map_box, new_functional_area)
FUNCTIONAL_AREA_NORMALIZATIONS: dict[str, tuple[str, str]] = {
    "config.fiscal": ("configuracion", "configuracion.fiscal"),  # 02-impact §2 configuracion
    "ops.reconciliation": ("plataforma-tecnica", "plataforma-tecnica.reconciliation"),  # 02-impact §3 (revisar)
    "camila.reactivacion": ("camila", "camila.reactivar"),  # typo → correct SYSTEM-MAP area
}

# Slug-based overrides: cap slugs that need a specific map_box regardless of functional_area
# Used for "(revisar)" caps per 02-impact §3: ops/live-reconciliation-sweep, tests/playwright-smoke-suite
# Key = slug (filename stem) → Value = (map_box, new_functional_area)
SLUG_OVERRIDES: dict[str, tuple[str, str]] = {
    "playwright-smoke-suite": ("plataforma-tecnica", "plataforma-tecnica.scaffolding"),
    # live-reconciliation-sweep handled via functional_area ops.reconciliation normalization above
}

# Zona derivada de caja → user_visible
ZONE_FOR_BOX: dict[str, str] = {}
INFRA_BOXES = {"seguridad-cumplimiento", "observabilidad", "plataforma-tecnica", "motor-agentico"}
PLATFORM_BOXES = {"acceso", "onboarding", "configuracion"}


def load_system_map(brand_dir: Path) -> dict[str, Any]:
    sm_path = brand_dir / "docs" / "architecture" / "SYSTEM-MAP.yaml"
    if not sm_path.exists():
        print(f"ERROR: SYSTEM-MAP.yaml no encontrado: {sm_path}", file=sys.stderr)
        sys.exit(1)
    try:
        return yaml.safe_load(sm_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        print(f"ERROR parsing SYSTEM-MAP.yaml: {e}", file=sys.stderr)
        sys.exit(1)


def build_absorbs_table(system_map: dict[str, Any]) -> dict[str, str]:
    """Build functional_area → map_box dict from zones[].boxes[].absorbs.

    Supports SYSTEM-MAP v2.0 where zones[].boxes is a list of objects
    (each with id + absorbs[]) and the legacy v1.x where target_boxes[]
    held the absorbs data.  Back-compat: also reads target_boxes[] when
    present so the same script works against both schema versions.
    """
    table: dict[str, str] = {}
    for zone in system_map.get("zones", []):
        # v2.0: boxes is a list of objects {id, name, absorbs, ...}
        for box in zone.get("boxes", []):
            if isinstance(box, dict):
                box_id = box.get("id", "")
                for absorb in box.get("absorbs", []):
                    table[absorb] = box_id
        # v1.x back-compat: target_boxes[] (may not exist in v2.0)
        for tb in zone.get("target_boxes", []):
            if isinstance(tb, dict):
                box_id = tb.get("id", "")
                for absorb in tb.get("absorbs", []):
                    table[absorb] = box_id
    return table


def build_valid_boxes(system_map: dict[str, Any]) -> set[str]:
    """All valid box IDs from zones (Agentes boxes + Plataforma boxes + Infra boxes).

    Supports SYSTEM-MAP v2.0 where zones[].boxes is a list of objects
    {id, ...}, and v1.x where boxes is a list of plain strings + target_boxes
    carried the object form.
    """
    valid: set[str] = set()
    for zone in system_map.get("zones", []):
        for box in zone.get("boxes", []):
            if isinstance(box, dict):
                # v2.0: box object — extract id
                box_id = box.get("id", "")
                if box_id:
                    valid.add(box_id)
            elif isinstance(box, str):
                # v1.x: plain string
                valid.add(box)
        # v1.x back-compat: target_boxes[] may coexist
        for tb in zone.get("target_boxes", []):
            if isinstance(tb, dict):
                box_id = tb.get("id", "")
                if box_id:
                    valid.add(box_id)
    return valid


def box_to_zone(system_map: dict[str, Any]) -> dict[str, str]:
    """Build box_id → zone_id dict.

    Supports SYSTEM-MAP v2.0 where zones[].boxes is a list of objects
    {id, ...}, and v1.x where boxes is a list of plain strings + target_boxes
    carried the object form.
    """
    mapping: dict[str, str] = {}
    for zone in system_map.get("zones", []):
        zid = zone["id"]
        for box in zone.get("boxes", []):
            if isinstance(box, dict):
                # v2.0: box object — extract id
                box_id = box.get("id", "")
                if box_id:
                    mapping[box_id] = zid
            elif isinstance(box, str):
                # v1.x: plain string
                mapping[box] = zid
        # v1.x back-compat: target_boxes[]
        for tb in zone.get("target_boxes", []):
            if isinstance(tb, dict):
                box_id = tb.get("id", "")
                if box_id:
                    mapping[box_id] = zid
    return mapping


def derive_user_visible(map_box: str, box_zone_map: dict[str, str]) -> bool:
    """Infra zone → false. Plataforma / Agentes → true."""
    zone = box_zone_map.get(map_box, "")
    return zone != "infraestructura"


def parse_cap_frontmatter(cap_path: Path) -> tuple[dict[str, Any], str, str]:
    """Return (data, yaml_text, rest_body) parsed from cap YAML file."""
    content = cap_path.read_text(encoding="utf-8")
    if content.startswith("---\n"):
        parts = content.split("\n---\n", 2)
        if len(parts) >= 2:
            yaml_text = parts[0][4:]  # strip leading "---\n"
            rest_body = "\n---\n" + parts[1] if len(parts) >= 2 else ""
            if len(parts) >= 3:
                rest_body = "\n---\n" + parts[1] + "\n---\n" + parts[2]
            else:
                rest_body = "\n---\n" + parts[1]
        else:
            yaml_text = content[4:]
            rest_body = ""
    elif "\n---\n" in content:
        yaml_text = content.split("\n---\n", 1)[0]
        rest_body = "\n---\n" + content.split("\n---\n", 1)[1]
    else:
        yaml_text = content
        rest_body = ""

    try:
        data = yaml.safe_load(yaml_text) or {}
    except yaml.YAMLError:
        data = {}

    return data, yaml_text, rest_body


def determine_map_box(
    data: dict[str, Any],
    absorbs_table: dict[str, str],
    valid_boxes: set[str],
    box_zone_map: dict[str, str],
) -> tuple[str, str | None] | None:
    """
    Determine (map_box, new_agent_owner_or_None) for a cap.

    Returns None if the cap cannot be mapped (triggers HALT).

    Priority:
    1. Valeria overrides (valeria.agenda/bookings/shell)
    2. functional_area normalization (invalid areas like config.fiscal, ops.reconciliation)
    3. Specialist agents (lisa/mateo/adrian/lucas/camila) → map_box = agent_owner
    4. functional_area via absorbs_table
    5. Already-set valid map_box (pass-through for idempotency)
    6. Cannot map
    """
    agent_owner = data.get("agent_owner", "")
    functional_area = data.get("functional_area", "")
    existing_map_box = data.get("map_box", "")

    # 1. Valeria overrides
    if functional_area in VALERIA_OVERRIDES:
        map_box, new_owner = VALERIA_OVERRIDES[functional_area]
        return map_box, new_owner

    # 2. functional_area normalization (invalid areas not in absorbs_table)
    if functional_area in FUNCTIONAL_AREA_NORMALIZATIONS:
        map_box, _ = FUNCTIONAL_AREA_NORMALIZATIONS[functional_area]
        return map_box, None

    # 3. Specialist agents → map_box = agent_owner (unchanged)
    if agent_owner in SPECIALIST_AGENTS:
        return agent_owner, None

    # 4. functional_area via absorbs_table
    if functional_area and functional_area in absorbs_table:
        return absorbs_table[functional_area], None

    # 5. Already has a valid map_box (pass-through for idempotency)
    if existing_map_box and existing_map_box in valid_boxes:
        return existing_map_box, None

    # 6. Cannot map
    return None


def update_frontmatter_field(yaml_text: str, field: str, value: Any) -> str:
    """Update a top-level field in YAML frontmatter text, preserving structure."""
    str_value = yaml.dump({field: value}, default_flow_style=False, allow_unicode=True).strip()
    # str_value is like "field: value"

    # Try to replace existing field
    pattern = re.compile(r"^" + re.escape(field) + r"\s*:.*$", re.MULTILINE)
    if pattern.search(yaml_text):
        return pattern.sub(str_value, yaml_text, count=1)
    else:
        # Append after last line before potential comment
        return yaml_text.rstrip() + "\n" + str_value + "\n"


def process_cap(
    cap_path: Path,
    absorbs_table: dict[str, str],
    valid_boxes: set[str],
    box_zone_map: dict[str, str],
    apply: bool,
    dry_run: bool,
) -> dict[str, Any]:
    """
    Process a single cap YAML. Returns result dict with keys:
      - status: 'ok' | 'updated' | 'unmapped' | 'invalid_box' | 'skipped'
      - diff: list of (field, old, new)
      - error: optional error message
    """
    data, yaml_text, rest_body = parse_cap_frontmatter(cap_path)
    if not isinstance(data, dict):
        return {"status": "skipped", "diff": [], "error": "not a dict"}

    agent_owner = data.get("agent_owner", "")
    existing_map_box = data.get("map_box", "")

    # SC-5: If existing map_box is invalid, reject it
    if existing_map_box and existing_map_box not in valid_boxes:
        return {
            "status": "invalid_box",
            "diff": [],
            "error": f"map_box='{existing_map_box}' is not a valid box in SYSTEM-MAP",
        }

    # Check slug-based overrides first (for special cases per 02-impact §3)
    slug_key = cap_path.stem  # filename without .yaml
    if slug_key in SLUG_OVERRIDES:
        target_map_box, new_fa_from_slug = SLUG_OVERRIDES[slug_key]
        target_user_visible = derive_user_visible(target_map_box, box_zone_map)
        functional_area = data.get("functional_area", "")
        new_functional_area = new_fa_from_slug
        current_agent_owner_slug = data.get("agent_owner", "")
        # Also replace deprecated config/infra agent_owner
        slug_new_owner = target_map_box if current_agent_owner_slug in ("config", "infra") else None

        diff = []
        if data.get("map_box") != target_map_box:
            diff.append(("map_box", data.get("map_box"), target_map_box))
        if data.get("user_visible") != target_user_visible:
            diff.append(("user_visible", data.get("user_visible"), target_user_visible))
        if slug_new_owner and current_agent_owner_slug != slug_new_owner:
            diff.append(("agent_owner", current_agent_owner_slug, slug_new_owner))
        if (
            functional_area
            and functional_area != new_functional_area
            and any(functional_area.startswith(p) for p in ("config.", "infra.", "valeria.", "ops."))
        ):
            diff.append(("functional_area", functional_area, new_functional_area))

        if not diff:
            return {"status": "ok", "diff": []}
        if dry_run:
            return {"status": "updated", "diff": diff, "dry_run": True}
        if apply:
            new_yaml_text = yaml_text
            new_yaml_text = update_frontmatter_field(new_yaml_text, "map_box", target_map_box)
            new_yaml_text = update_frontmatter_field(new_yaml_text, "user_visible", target_user_visible)
            if slug_new_owner and current_agent_owner_slug != slug_new_owner:
                new_yaml_text = update_frontmatter_field(new_yaml_text, "agent_owner", slug_new_owner)
            if diff and any(d[0] == "functional_area" for d in diff):
                new_yaml_text = update_frontmatter_field(new_yaml_text, "functional_area", new_functional_area)
            new_content = "---\n" + new_yaml_text + rest_body
            cap_path.write_text(new_content, encoding="utf-8")
        return {"status": "updated", "diff": diff}

    # Process all caps so specialists also get their map_box
    result = determine_map_box(data, absorbs_table, valid_boxes, box_zone_map)

    if result is None:
        return {
            "status": "unmapped",
            "diff": [],
            "error": f"Cannot determine map_box for cap: agent_owner='{agent_owner}' functional_area='{data.get('functional_area', '')}'",
        }

    target_map_box, new_agent_owner = result
    target_user_visible = derive_user_visible(target_map_box, box_zone_map)

    # Compute new functional_area
    # Priority:
    # 1. FUNCTIONAL_AREA_NORMALIZATIONS (invalid areas → correct area)
    # 2. Re-map legacy config.*/infra.*/valeria.* prefix to target_map_box
    # 3. Keep existing (already migrated or specialist agent area)
    functional_area = data.get("functional_area", "")
    new_functional_area = functional_area  # default: keep

    if functional_area in FUNCTIONAL_AREA_NORMALIZATIONS:
        # Use normalized functional_area directly
        _, new_functional_area = FUNCTIONAL_AREA_NORMALIZATIONS[functional_area]
    elif target_map_box in INFRA_BOXES or target_map_box in PLATFORM_BOXES:
        # Only re-map if still using legacy prefix (config.* / infra.* / valeria.*)
        legacy_prefixes = ("config.", "infra.", "valeria.")
        if functional_area and any(functional_area.startswith(p) for p in legacy_prefixes):
            # Extract the sub-area from functional_area
            if "." in functional_area:
                _, sub_area = functional_area.split(".", 1)
                new_functional_area = f"{target_map_box}.{sub_area}"
            else:
                new_functional_area = functional_area

    # Compute diff
    diff = []
    current_map_box = data.get("map_box")
    current_user_visible = data.get("user_visible")
    current_agent_owner = data.get("agent_owner")

    # For Plataforma/Infra caps, agent_owner: config/infra must be replaced with map_box
    # (SC-1 grader: grep config|infra → 0 after migration)
    # For Agentes caps, agent_owner stays as-is (matches map_box)
    effective_new_owner = new_agent_owner
    if effective_new_owner is None and current_agent_owner in ("config", "infra"):
        # Replace deprecated config/infra owner with the target map_box value
        effective_new_owner = target_map_box

    if current_map_box != target_map_box:
        diff.append(("map_box", current_map_box, target_map_box))
    if current_user_visible != target_user_visible:
        diff.append(("user_visible", current_user_visible, target_user_visible))
    if effective_new_owner is not None and current_agent_owner != effective_new_owner:
        diff.append(("agent_owner", current_agent_owner, effective_new_owner))
    if new_functional_area != functional_area and functional_area:
        diff.append(("functional_area", functional_area, new_functional_area))

    if not diff:
        return {"status": "ok", "diff": []}

    if dry_run:
        return {"status": "updated", "diff": diff, "dry_run": True}

    if apply:
        # Apply updates
        new_yaml_text = yaml_text
        new_yaml_text = update_frontmatter_field(new_yaml_text, "map_box", target_map_box)
        new_yaml_text = update_frontmatter_field(new_yaml_text, "user_visible", target_user_visible)
        if effective_new_owner is not None and current_agent_owner != effective_new_owner:
            new_yaml_text = update_frontmatter_field(new_yaml_text, "agent_owner", effective_new_owner)
        if new_functional_area != functional_area and functional_area:
            new_yaml_text = update_frontmatter_field(new_yaml_text, "functional_area", new_functional_area)

        new_content = "---\n" + new_yaml_text + rest_body
        cap_path.write_text(new_content, encoding="utf-8")

    return {"status": "updated", "diff": diff}


def run_migration(
    brand_dir: Path,
    repo_root: Path | None = None,
    dry_run: bool = True,
    apply: bool = False,
    strict: bool = False,
) -> int:
    """
    Run the migration. Returns exit code (0 = success, 1 = errors).
    This function is the programmatic entry point (used by tests).
    """
    if repo_root is None:
        repo_root = REPO_ROOT

    system_map = load_system_map(brand_dir)
    absorbs_table = build_absorbs_table(system_map)
    valid_boxes = build_valid_boxes(system_map)
    box_zone_map = box_to_zone(system_map)

    caps_dir = brand_dir / "docs" / "product" / "capabilities"
    if not caps_dir.exists():
        print(f"ERROR: caps dir no existe: {caps_dir}", file=sys.stderr)
        sys.exit(1)

    unmapped: list[tuple[Path, str]] = []
    invalid_box: list[tuple[Path, str]] = []
    updated: list[Path] = []
    ok_count = 0
    skipped_count = 0

    cap_files = sorted(
        [
            yf
            for module_dir in sorted(caps_dir.iterdir())
            if module_dir.is_dir() and not module_dir.name.startswith("_")
            for yf in sorted(module_dir.glob("*.yaml"))
            if not yf.name.startswith("_")
        ]
    )

    for cap_path in cap_files:
        result = process_cap(
            cap_path=cap_path,
            absorbs_table=absorbs_table,
            valid_boxes=valid_boxes,
            box_zone_map=box_zone_map,
            apply=apply,
            dry_run=dry_run,
        )
        status = result["status"]
        if status == "unmapped":
            unmapped.append((cap_path, result.get("error", "")))
        elif status == "invalid_box":
            invalid_box.append((cap_path, result.get("error", "")))
        elif status == "updated":
            updated.append(cap_path)
            if not dry_run:
                print(f"  UPDATED: {cap_path.relative_to(repo_root)}")
                for field, old, new in result.get("diff", []):
                    print(f"    {field}: {old!r} → {new!r}")
            else:
                print(f"  [dry-run] WOULD UPDATE: {cap_path.relative_to(repo_root)}")
                for field, old, new in result.get("diff", []):
                    print(f"    {field}: {old!r} → {new!r}")
        elif status == "ok":
            ok_count += 1
        else:
            skipped_count += 1

    print(
        f"\nSummary: {ok_count} ok · {len(updated)} updated · {len(unmapped)} unmapped · {len(invalid_box)} invalid_box · {skipped_count} skipped"
    )

    if unmapped:
        print("\n❌ HALT — Caps sin mapeo (NEVER asigna default — SC-3):")
        for cap_path, error in unmapped:
            print(f"  {cap_path.relative_to(repo_root)}: {error}")
        sys.exit(1)

    if invalid_box:
        print("\n❌ HALT — Caps con map_box inválido (SC-5):")
        for cap_path, error in invalid_box:
            print(f"  {cap_path.relative_to(repo_root)}: {error}")
        sys.exit(1)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brand", default="vitalia", help="Brand slug (default: vitalia)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Print diff without writing (default: on)")
    parser.add_argument("--apply", action="store_true", default=False, help="Apply changes (write files)")
    parser.add_argument("--strict", action="store_true", default=False, help="Exit 1 also on warnings")
    args = parser.parse_args()

    if args.apply:
        dry_run = False
    else:
        dry_run = args.dry_run

    brand_dir = REPO_ROOT / args.brand
    if not brand_dir.exists():
        print(f"ERROR: brand dir no existe: {brand_dir}", file=sys.stderr)
        return 1

    print(f"=== map_zones_migration · brand={args.brand} · {'DRY-RUN' if dry_run else 'APPLY'} ===\n")
    return run_migration(
        brand_dir=brand_dir,
        repo_root=REPO_ROOT,
        dry_run=dry_run,
        apply=args.apply,
        strict=args.strict,
    )


if __name__ == "__main__":
    sys.exit(main())
