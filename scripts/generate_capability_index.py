#!/usr/bin/env python3
"""
generate_capability_index.py — Auto-gen user-facing capability index per brand.

Lee:
- {brand}/docs/product/capabilities/{module}/*.yaml (cap YAMLs schema v3)

Genera (idempotente, overwrite):
- {brand}/docs/product/areas/{agent_owner}.md      (1 file per agente)
- docs/portfolio/{brand}-capabilities.md            (índice user-facing global)

ADR: vitalia/docs/architecture/ADR-vitalia-005-capability-model-4-dimensions.md
SSoT schema: docs/process/capability-protocol.md Sec 7-9 (v3 cement 2026-05-27).

Uso:
    python3 scripts/generate_capability_index.py --brand vitalia
    python3 scripts/generate_capability_index.py --brand vitalia --check
    python3 scripts/generate_capability_index.py --all-brands
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

# Agent catalog (per ADR-vitalia-005 — vitalia mapping · otras brands declaran propio en su ADR)
VITALIA_AGENTS: list[dict[str, Any]] = [
    {"id": "lisa", "emoji": "🏥", "name": "Lisa", "subtitle": "Mi Clínica"},
    {"id": "valeria", "emoji": "🗓", "name": "Valeria", "subtitle": "Mi Día"},
    {"id": "adrian", "emoji": "💼", "name": "Adrián", "subtitle": "Vender"},
    {"id": "lucas", "emoji": "📣", "name": "Lucas", "subtitle": "Marketing"},
    {"id": "camila", "emoji": "🌟", "name": "Camila", "subtitle": "Reputación + cohortes"},
    {"id": "config", "emoji": "⚙", "name": "Configurar", "subtitle": "tenant · iam · compliance · admin"},
    {"id": "infra", "emoji": "🔧", "name": "Infra Vitalia", "subtitle": "observability · platform · payment · scaffolding"},
]

BRAND_AGENTS = {
    "vitalia": VITALIA_AGENTS,
    # single-brand: solo vitalia (catálogo agentes en project.config.yaml::agent_roster)
}


def load_capabilities(brand_dir: Path) -> list[dict[str, Any]]:
    """Lee todos los YAMLs en {brand}/docs/product/capabilities/{module}/*.yaml."""
    caps_dir = brand_dir / "docs" / "product" / "capabilities"
    if not caps_dir.exists():
        return []
    caps = []
    for module_dir in sorted(caps_dir.iterdir()):
        if not module_dir.is_dir() or module_dir.name.startswith("_"):
            continue
        for yaml_file in sorted(module_dir.glob("*.yaml")):
            if yaml_file.name.startswith("_"):
                continue
            try:
                content = yaml_file.read_text(encoding="utf-8")
                # 3 layouts soportados:
                # (a) Markdown frontmatter:  "---\n<yaml>\n---\n<body>"
                # (b) YAML puro:             "<yaml>" (sin --- en ningún lado)
                # (c) YAML con body marker:  "<yaml>\n---\n<body>" (sin --- leading)
                if content.startswith("---\n"):
                    parts = content.split("\n---\n", 2)
                    if len(parts) >= 2:
                        yaml_text = parts[0][4:]  # strip leading "---\n"
                    else:
                        yaml_text = content[4:]
                elif "\n---\n" in content:
                    yaml_text = content.split("\n---\n", 1)[0]
                else:
                    yaml_text = content
                data = yaml.safe_load(yaml_text) or {}
                if not isinstance(data, dict):
                    continue
                data["_path"] = yaml_file.relative_to(REPO_ROOT).as_posix()
                data["_module"] = module_dir.name
                caps.append(data)
            except (yaml.YAMLError, OSError) as e:
                print(f"WARN: skip {yaml_file}: {e}", file=sys.stderr)
    return caps


def render_agent_md(brand: str, agent: dict[str, Any], caps: list[dict[str, Any]]) -> str:
    """Genera el .md user-facing para un agente."""
    # Filter caps que NO son superseded + son owned por este agent
    relevant = [c for c in caps if c.get("agent_owner") == agent["id"] and not c.get("superseded_by")]
    # Group por functional_area
    by_area: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in relevant:
        area = c.get("functional_area") or f"{agent['id']}.sin-area"
        by_area[area].append(c)

    lines: list[str] = []
    lines.append("<!-- AUTO-GENERATED por scripts/generate_capability_index.py — NO editar a mano. -->")
    lines.append(f"<!-- Regenerar: python3 scripts/generate_capability_index.py --brand {brand} -->")
    lines.append("")
    lines.append(f"# {agent['emoji']} {agent['name']} — {agent['subtitle']}")
    lines.append("")
    lines.append(f"> Capacidades user-facing del agente **{agent['name']}** en {brand.title()}.")
    lines.append(f"> Auto-generado desde `{brand}/docs/product/capabilities/*/*.yaml` (schema v3, ADR-{brand}-005).")
    lines.append("")
    lines.append(f"**Total capabilities:** {len(relevant)}  ·  **Áreas funcionales:** {len(by_area)}")
    lines.append("")

    if not relevant:
        lines.append("_Sin capabilities declaradas todavía._")
        lines.append("")
        return "\n".join(lines)

    # Sort areas alfabéticamente
    for area in sorted(by_area.keys()):
        area_caps = by_area[area]
        area_short = area.replace(f"{agent['id']}.", "")
        lines.append(f"## {area_short}")
        lines.append("")
        for cap in sorted(area_caps, key=lambda c: c.get("slug", "")):
            name = cap.get("user_facing_name") or f"{cap.get('module')}/{cap.get('slug')}"
            slug = cap.get("slug", "?")
            module = cap.get("module") or cap.get("tech_module") or "?"
            status = cap.get("status", "?")
            desc = cap.get("user_facing_description") or ""
            # Compactar descripción multi-line a single line
            desc_compact = " ".join(desc.split()) if desc else ""
            if len(desc_compact) > 200:
                desc_compact = desc_compact[:197] + "…"

            lines.append(f"### {name}")
            lines.append("")
            lines.append(f"- **Status:** `{status}`  ·  **Cap:** [`{module}/{slug}`](../capabilities/{module}/{slug}.yaml)")
            dp = cap.get("dev_preview") or {}
            if dp.get("route"):
                lines.append(f"- **Ruta:** `{dp['route']}`")
            if dp.get("how_to_navigate"):
                lines.append(f"- **Cómo llegar:** {dp['how_to_navigate']}")
            if dp.get("main_component"):
                lines.append(f"- **Componente principal:** `{dp['main_component']}`")
            api_eps = dp.get("api_endpoints") or []
            if api_eps:
                eps_str = " · ".join(f"`{ep}`" for ep in api_eps[:3])
                lines.append(f"- **API:** {eps_str}")
            if dp.get("e2e_test"):
                lines.append(f"- **E2E:** `{dp['e2e_test']}`")
            atomics = cap.get("atomics") or []
            if atomics:
                lines.append(f"- **Atomics:** {len(atomics)}")
            if desc_compact:
                lines.append("")
                lines.append(f"  {desc_compact}")
            lines.append("")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"_Última regeneración: ver git log de este archivo._")
    lines.append("")
    return "\n".join(lines)


def render_index_md(brand: str, caps: list[dict[str, Any]], agents: list[dict[str, Any]]) -> str:
    """Genera docs/portfolio/{brand}-capabilities.md — vista cross-agent."""
    # Filter superseded
    visible = [c for c in caps if not c.get("superseded_by") and c.get("user_visible") is not False]

    # Count caps por agent
    by_agent: dict[str, int] = defaultdict(int)
    for c in visible:
        owner = c.get("agent_owner") or "(sin agent_owner)"
        by_agent[owner] += 1

    total_visible = len(visible)
    total_all = len([c for c in caps if not c.get("superseded_by")])
    total_infra = total_all - total_visible
    total_superseded = len(caps) - total_all

    lines: list[str] = []
    lines.append("<!-- AUTO-GENERATED por scripts/generate_capability_index.py — NO editar a mano. -->")
    lines.append(f"<!-- Regenerar: python3 scripts/generate_capability_index.py --brand {brand} -->")
    lines.append("")
    lines.append(f"# {brand.title()} · Capabilities (user-facing)")
    lines.append("")
    lines.append(f"> Vista cross-agent del producto {brand.title()} en lenguaje humano.")
    lines.append(f"> Auto-generado desde `{brand}/docs/product/capabilities/*/*.yaml` (schema v3, ADR-{brand}-005).")
    lines.append("")
    lines.append(f"**Total caps user-facing:** {total_visible}  ·  **Infra:** {total_infra}  ·  **Superseded:** {total_superseded}")
    lines.append("")

    lines.append("## Por agente")
    lines.append("")
    lines.append("| Agente | Caps user-facing |")
    lines.append("|---|---|")
    for agent in agents:
        count = by_agent.get(agent["id"], 0)
        link = f"[{count}](../../{brand}/docs/product/areas/{agent['id']}.md)" if count > 0 else f"{count}"
        lines.append(f"| {agent['emoji']} **{agent['name']}** — {agent['subtitle']} | {link} |")
    lines.append("")

    # Orphans (sin agent_owner)
    orphans = [c for c in visible if not c.get("agent_owner")]
    if orphans:
        lines.append(f"## ⚠️ Capabilities sin agent_owner ({len(orphans)})")
        lines.append("")
        lines.append("Estas caps necesitan refining para declarar `agent_owner` + `functional_area` per ADR-vitalia-005:")
        lines.append("")
        for c in orphans:
            module = c.get("module") or c.get("tech_module") or "?"
            slug = c.get("slug", "?")
            lines.append(f"- `{module}/{slug}` — [{c.get('_path')}](../../{c.get('_path')})")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Drill-down per agente")
    lines.append("")
    for agent in agents:
        count = by_agent.get(agent["id"], 0)
        if count == 0:
            continue
        rel_path = f"../../{brand}/docs/product/areas/{agent['id']}.md"
        lines.append(f"- {agent['emoji']} [{agent['name']}]({rel_path}) — {count} capabilities · {agent['subtitle']}")
    lines.append("")

    return "\n".join(lines)


def write_or_check(path: Path, content: str, check: bool) -> bool:
    """Escribe content a path. Si check=True, retorna False si difiere (no escribe)."""
    if check:
        if not path.exists():
            print(f"STALE: {path} no existe", file=sys.stderr)
            return False
        existing = path.read_text(encoding="utf-8")
        if existing.strip() != content.strip():
            print(f"STALE: {path} difiere", file=sys.stderr)
            return False
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def process_brand(brand: str, check: bool) -> bool:
    """Genera areas/{agent}.md + docs/portfolio/{brand}-capabilities.md. Retorna True si OK."""
    brand_dir = REPO_ROOT / brand
    if not brand_dir.exists():
        print(f"ERROR: brand dir no existe: {brand_dir}", file=sys.stderr)
        return False

    agents = BRAND_AGENTS.get(brand)
    if not agents:
        print(f"WARN: brand {brand} no tiene catálogo de agentes definido en BRAND_AGENTS. Skip.", file=sys.stderr)
        return True

    caps = load_capabilities(brand_dir)
    if not caps:
        print(f"WARN: brand {brand} sin caps. Skip.", file=sys.stderr)
        return True

    all_ok = True
    # Render per-agent markdown
    areas_dir = brand_dir / "docs" / "product" / "areas"
    for agent in agents:
        md = render_agent_md(brand, agent, caps)
        out_path = areas_dir / f"{agent['id']}.md"
        ok = write_or_check(out_path, md, check)
        all_ok = all_ok and ok
        if not check:
            print(f"  wrote {out_path.relative_to(REPO_ROOT)}")

    # Render índice cross-agent
    portfolio_md = render_index_md(brand, caps, agents)
    portfolio_path = REPO_ROOT / "docs" / "portfolio" / f"{brand}-capabilities.md"
    ok = write_or_check(portfolio_path, portfolio_md, check)
    all_ok = all_ok and ok
    if not check:
        print(f"  wrote {portfolio_path.relative_to(REPO_ROOT)}")

    return all_ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brand", help="Brand slug (vitalia)")
    parser.add_argument("--all-brands", action="store_true", help="Iterate all brands with catálogo defined")
    parser.add_argument("--check", action="store_true", help="Exit 1 si content stale (no write)")
    args = parser.parse_args()

    if not args.brand and not args.all_brands:
        parser.error("--brand SLUG o --all-brands requerido")

    if args.all_brands:
        brands = list(BRAND_AGENTS.keys())
    else:
        brands = [args.brand]

    all_ok = True
    for brand in brands:
        print(f"=== {brand} ===")
        ok = process_brand(brand, args.check)
        all_ok = all_ok and ok

    if args.check and not all_ok:
        print("\nFAIL: regen necesaria. Corré sin --check.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
