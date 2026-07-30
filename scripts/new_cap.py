#!/usr/bin/env python3
# voseo-allowed: doc interno de maquinaria (no user-facing)
"""new_cap.py — Capa 2 del enforcement determinístico (HB-51): GENERATOR de caps.

El formato de una cap deja de salir del criterio de Claude (prosa de un skill) y pasa
a CÓDIGO: este generator PRODUCE un YAML schema-válido por construcción. Claude NUNCA
hand-authorea una cap — corre `make new-cap` y llena el CONTENIDO en el scaffold.

Garantías (verify-first):
  · cap_id = `{module}.{slug}` derivado · REFUSE si ya existe (evita editar la equivocada
    — la causa del incidente origen: se editó la slice-1 en vez de crear la canónica).
  · status `planned` por default → pasa G4/G6 (que solo aplican a live/beta) sin paths reales.
  · scaffold con paths `null` + `# TODO` (NO inventa paths → G4 limpio).
  · functional_area opcional; si se da, valida formato + avisa si no está en el SYSTEM-MAP.
  · El YAML resultante pasa `validate_caps_schema.py` + los gates G1-G6 sin tocar nada a mano.

Uso:
    python3 scripts/new_cap.py --brand vitalia --module inbox --slug adrian-inbox \
        --agent adrian --area adrian.inbox --name "Inbox unificado" --story vitalia-fase2-x
    make new-cap BRAND=vitalia MODULE=inbox SLUG=adrian-inbox AREA=adrian.inbox

Exit: 0 creada · 1 error de uso · 2 cap_id ya existe (REFUSE).
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from datetime import date
from pathlib import Path

WS = Path(
    subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
)


def _import_sibling(name: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parent / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


resolve_cap = _import_sibling("resolve_cap")
validate_caps_schema = _import_sibling("validate_caps_schema")
validate_system_map = _import_sibling("validate_system_map")


SCAFFOLD = """\
---
capability_id: {brand}.{module}.{slug}
module: {module}
tech_module: {module}
slug: {slug}
status: planned                       # planned | beta | live | deprecated | sunset (subí a live SOLO con ≥1 scenario + e2e GREEN)
license: brand-local

# Dimensiones v3 (4 campos · ADR-vitalia-005)
agent_owner: {agent}                  # caja del mapa — ver SYSTEM-MAP.yaml `zones`
functional_area: {functional_area}    # <caja>.<area-kebab> — DEBE existir en SYSTEM-MAP
user_visible: {user_visible}
nature: feature                       # feature | scaffold | extension-point

user_facing_name: "{name}"
user_facing_description: >
  # TODO: 2-5 líneas Spanish neutro · qué hace desde la óptica del usuario · sin jerga.

# DEV_PREVIEW (paths null hasta que exista el código · NO inventar → G4 limpio)
dev_preview:
  route: null                         # TODO "/{agent}/{slug}" cuando exista
  how_to_navigate: null               # TODO pasos verbatim para llegar en dev
  main_component: null                # TODO path real cuando se construya
  api_endpoints: []                   # TODO
  e2e_test: null                      # TODO path spec
  fixtures_required: []
  storybook_url: null
  loom_demo: null

# Ledger
created_in_story: {story}
created_date: {today}
last_modified: {today}
parent_cap: null
derives_capabilities: []
superseded_by: null

change_log:
  - story_id: {story}
    date: {today}
    type: new
    summary: "# TODO: implementación inicial · qué hace en 1-2 líneas"
    scenarios_added: []               # TODO: ≥1 al merge si user_visible:true
    merge_sha: null
    status: in-progress

# v3.2 (llenar al merge · REQUIRED si user_visible:true)
access:
  entry_points: []                    # TODO
  forbidden_roles: []
  authentication: required

scenarios: []                         # TODO: ≥1 scenario (id/name/actor/given/when/then) al merge

business_rules: []                    # TODO

related_capabilities:
  depends_on: []
  enables: []
  similar: []
  obsoletes: []
---

# {name}

# TODO: resumen markdown · arquitectura interna · decisiones cardinales · referencias.
"""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brand", required=True)
    parser.add_argument("--module", required=True, help="tech_module (dir canónico kebab)")
    parser.add_argument("--slug", required=True, help="kebab · único dentro del module")
    parser.add_argument("--agent", default="TODO-agent", help="caja del mapa (lisa/mateo/adrian/lucas/camila/…)")
    parser.add_argument("--area", default="", help="functional_area `<box>.<area>` (opcional pero recomendado)")
    parser.add_argument("--name", default="", help="user_facing_name")
    parser.add_argument("--story", default="TBD", help="story-origin")
    parser.add_argument("--user-visible", default="true", choices=["true", "false"])
    args = parser.parse_args(argv)

    brand, module, slug = args.brand, args.module.strip(), args.slug.strip()
    cap_id = f"{module}.{slug}"
    caps_root = WS / brand / "docs" / "product" / "capabilities"
    target = caps_root / module / f"{slug}.yaml"

    # ── REFUSE si el cap_id ya existe (NO editar la equivocada) ──
    if target.exists():
        print(f"REFUSE: ya existe {target.relative_to(WS)} — editá esa cap o elegí otro slug.", file=sys.stderr)
        return 2
    resolve_cap.clear_resolver_cache()
    existing = resolve_cap.resolve_cap_ids(brand, cap_id, root=caps_root)
    if existing:
        print(f"REFUSE: el cap_id '{cap_id}' ya resuelve a {sorted(existing)} — no se duplica.", file=sys.stderr)
        return 2

    # ── functional_area: formato + existencia en SYSTEM-MAP (warn, no block) ──
    fa = args.area.strip()
    if fa:
        if not validate_caps_schema.FA_RE.match(fa):
            print(f"ERROR: functional_area '{fa}' no es `<box>.<area>` (2 segmentos kebab/snake).", file=sys.stderr)
            return 1
        sm = validate_system_map.load_system_map(WS / brand)
        if sm is not None:
            valid_areas = validate_system_map.extract_valid_areas(sm)
            if not validate_system_map.is_valid_area(fa, valid_areas):
                print(f"⚠️  functional_area '{fa}' NO existe en SYSTEM-MAP — agregala al mapa o el gate G3 fallará.")

    content = SCAFFOLD.format(
        brand=brand,
        module=module,
        slug=slug,
        agent=args.agent,
        functional_area=fa or "TODO.area  # ⚠️ requerido para aparecer en el mapa",
        user_visible=args.user_visible,
        name=args.name or f"{slug}",
        story=args.story,
        today=date.today().isoformat(),
    )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    # ── Self-verify: el scaffold pasa el schema sin edición ──
    errs, _ = validate_caps_schema.validate_cap(target)
    rel = target.relative_to(WS).as_posix()
    if errs:
        print(f"⚠️  scaffold creado pero con errores de schema (revisá): {errs}", file=sys.stderr)
    print(f"✅ cap creada (schema-válida): {rel}")
    print(f"   cap_id canónico: {cap_id}")
    print(
        "   Próximo: llená los `# TODO` (contenido), NO el formato. Subí status→live SOLO con ≥1 scenario + e2e GREEN."
    )
    if not fa:
        print("   ⚠️ Declará `functional_area` para que la cap aparezca en una caja del cockpit.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
