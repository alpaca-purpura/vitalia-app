#!/usr/bin/env python3
"""
scripts/generate_infra_matrix.py
Auto-genera docs/portfolio/INFRA-MATRIX.md desde {brand}/config/brand.yaml::infra.

SSoT: cada {brand}/config/brand.yaml::infra (el detalle vive ahi).
Este script es el indexador — NO editar INFRA-MATRIX.md manualmente.

Uso:
    make infra-matrix
    # o directamente:
    .venv/bin/python scripts/generate_infra_matrix.py

S-DOCKER-DEV-MULTIBRAND T-8 — 2026-05-15
Pattern: metadata-en-su-lugar + auto-gen index
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml  # pyyaml — disponible en venv raiz

REPO_ROOT = Path(__file__).parent.parent
OUTPUT = REPO_ROOT / "docs" / "portfolio" / "INFRA-MATRIX.md"


def _discover_brands() -> list[str]:
    """Auto-discover brand slugs by globbing {brand}/config/brand.yaml.

    Devuelve lista ordenada alfabeticamente. Cualquier directorio raiz con
    config/brand.yaml es considerado brand (incluye placeholders bootstrap).
    """
    return sorted(p.parent.parent.name for p in REPO_ROOT.glob("*/config/brand.yaml"))


BRANDS = _discover_brands()

HEADER = "<!-- AUTO-GENERATED via make infra-matrix — DO NOT EDIT MANUALLY -->\n"


def load_brand_infra(brand: str) -> dict:
    """Lee {brand}/config/brand.yaml y retorna la seccion infra."""
    config_path = REPO_ROOT / brand / "config" / "brand.yaml"
    if not config_path.exists():
        return {}
    with config_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("infra", {})


def generate_matrix(brands_infra: dict[str, dict]) -> str:
    """Genera la tabla markdown de infra cross-brand."""
    lines = [
        HEADER,
        "# INFRA-MATRIX — Puertos, dominios y databases por brand\n",
        (
            "> Generado automaticamente por `make infra-matrix`. "
            "SSoT: `{brand}/config/brand.yaml::infra`. "
            "NO editar manualmente.\n"
        ),
        "## Entorno dev local\n",
        "| Brand | Backend port | Frontend port | DB name | Redis DB | Qdrant prefix | Dev domain |",
        "|---|---|---|---|---|---|---|",
    ]
    for brand, infra in brands_infra.items():
        dev = infra.get("dev", {})
        lines.append(
            f"| {brand} "
            f"| {dev.get('backend_port', 'n/a')} "
            f"| {dev.get('frontend_port', 'n/a')} "
            f"| {dev.get('database_name', 'n/a')} "
            f"| {dev.get('redis_db', 'n/a')} "
            f"| {dev.get('qdrant_collection_prefix', 'n/a')} "
            f"| {dev.get('domain', 'n/a')} |"
        )

    lines += [
        "",
        "## Entorno produccion\n",
        "| Brand | Prod domain | Servidor |",
        "|---|---|---|",
    ]
    for brand, infra in brands_infra.items():
        prod = infra.get("prod", {})
        lines.append(
            f"| {brand} "
            f"| {prod.get('domain', 'tbd')} "
            f"| {prod.get('server', 'tbd')} |"
        )

    lines += [
        "",
        "## Puertos compartidos (shared infra)\n",
        "| Servicio | Host port | Container port | Notas |",
        "|---|---|---|---|",
        "| postgres | 5435 | 5432 | Shared — 1 instancia, N databases (D1) |",
        "| qdrant | 6333/6334 | 6333/6334 | Opt-in profile `vector` (D3) |",
        "| redis | 6379 | 6379 | Opt-in profile `cache` (D3) |",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    brands_infra = {brand: load_brand_infra(brand) for brand in BRANDS}
    content = generate_matrix(brands_infra)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"INFRA-MATRIX.md updated ({len(BRANDS)} brands).")


if __name__ == "__main__":
    main()
