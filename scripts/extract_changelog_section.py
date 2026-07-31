"""
scripts/extract_changelog_section.py

Extrae una sección de {brand}/CHANGELOG-PUBLIC.md y la imprime por stdout.

Uso:
    python scripts/extract_changelog_section.py --brand vitalia --section Unreleased
    python scripts/extract_changelog_section.py --brand vitalia --section Unreleased

Salida:
    - Contenido de la sección solicitada (sin la línea de cabecera ## [...]).
    - "Sin cambios documentados." si la sección está vacía o no existe.
    - Exit 1 si el archivo CHANGELOG-PUBLIC.md no existe.

Secciones en CHANGELOG-PUBLIC.md siguen el formato Keep-a-Changelog ES-AR:
    ## [Sin lanzar]       ← sección Unreleased
    ## [X.Y.Z] — YYYY-MM-DD

El argumento --section acepta "Unreleased" (mapea a "[Sin lanzar]") o el nombre
literal de la cabecera (ej. "Sin lanzar").
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PLACEHOLDER_EMPTY = "Sin cambios documentados."

# Mapa de alias de sección: key = argumento CLI, value = texto que puede
# aparecer en la cabecera ## [...]
SECTION_ALIASES: dict[str, list[str]] = {
    "Unreleased": ["Sin lanzar", "Unreleased"],
    "Sin lanzar": ["Sin lanzar", "Unreleased"],
}


def _resolve_section_patterns(section: str) -> list[str]:
    """Retorna los textos de cabecera a buscar para la sección solicitada."""
    return SECTION_ALIASES.get(section, [section])


def _extract_section(content: str, section: str) -> str | None:
    """
    Extrae el bloque de texto correspondiente a la sección solicitada.

    Retorna:
        - El contenido del bloque (puede ser vacío o whitespace-only).
        - None si la sección no existe en el archivo.
    """
    patterns = _resolve_section_patterns(section)

    lines = content.splitlines()
    section_start: int | None = None

    # Buscar la línea de inicio de la sección (## [Sin lanzar] o variantes)
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Cabecera de nivel 2: ## [texto] o ## texto — ...
        if stripped.startswith("## "):
            # Extraer el texto dentro de los corchetes o después de ##
            header_match = re.match(r"^##\s+\[([^\]]+)\]", stripped)
            if header_match:
                header_text = header_match.group(1).strip()
            else:
                # ## texto sin corchetes
                header_text = stripped[3:].strip()

            if header_text in patterns:
                section_start = i
                break

    if section_start is None:
        return None

    # Recolectar líneas hasta la siguiente sección de nivel 2 (o fin del archivo)
    section_lines: list[str] = []
    for line in lines[section_start + 1 :]:
        if re.match(r"^##\s+", line):
            break
        section_lines.append(line)

    return "\n".join(section_lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extrae una sección de {brand}/CHANGELOG-PUBLIC.md.",
    )
    parser.add_argument(
        "--brand",
        required=True,
        help="Slug del brand (vitalia).",
    )
    parser.add_argument(
        "--section",
        required=True,
        help="Nombre de la sección a extraer (ej: Unreleased, 'Sin lanzar').",
    )
    args = parser.parse_args()

    changelog_path = Path(args.brand) / "CHANGELOG-PUBLIC.md"

    if not changelog_path.exists():
        print(
            f"Error: {changelog_path} no encontrado. "
            f"Verifica que el brand '{args.brand}' existe y tiene CHANGELOG-PUBLIC.md.",
            file=sys.stderr,
        )
        return 1

    content = changelog_path.read_text(encoding="utf-8")
    block = _extract_section(content, args.section)

    if block is None:
        # Sección no encontrada → placeholder, exit 0
        print(PLACEHOLDER_EMPTY)
        return 0

    stripped_block = block.strip()

    if not stripped_block:
        # Sección vacía → placeholder, exit 0
        print(PLACEHOLDER_EMPTY)
        return 0

    print(stripped_block)
    return 0


if __name__ == "__main__":
    sys.exit(main())
