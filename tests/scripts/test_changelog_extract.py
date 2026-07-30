"""
tests/scripts/test_changelog_extract.py
TDD para scripts/extract_changelog_section.py

Casos cubiertos (P11 de 05-guidelines.md + Scenario 7 de 01-spec.md):
  - test_happy: sección [Sin lanzar] con contenido → retorna el contenido
  - test_empty_section: sección [Sin lanzar] vacía → retorna "Sin cambios documentados."
  - test_missing_file: archivo no existe → exit 1 + mensaje claro
  - test_missing_section: sección solicitada ausente → exit 0 + "Sin cambios documentados."
  - test_multiple_brands: funciona con distintos brand slugs
  - test_cli_args: CLI acepta --brand y --section
  - test_does_not_include_other_sections: el output no incluye contenido de otras secciones
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent.parent / "scripts" / "extract_changelog_section.py"
PYTHON = Path(sys.executable)


def run_script(brand: str, section: str, tmp_path: Path) -> subprocess.CompletedProcess:
    """Ejecuta el script con --brand y --section, en el tmp_path como cwd."""
    return subprocess.run(
        [str(PYTHON), str(SCRIPT), "--brand", brand, "--section", section],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )


def write_changelog(tmp_path: Path, brand: str, content: str) -> Path:
    """Crea {brand}/CHANGELOG-PUBLIC.md con el content dado."""
    brand_dir = tmp_path / brand
    brand_dir.mkdir(parents=True, exist_ok=True)
    changelog = brand_dir / "CHANGELOG-PUBLIC.md"
    changelog.write_text(content, encoding="utf-8")
    return changelog


class TestHappyPath:
    def test_happy_single_entry_unreleased(self, tmp_path: Path) -> None:
        """Sección [Sin lanzar] con contenido → retorna ese contenido."""
        content = textwrap.dedent("""\
            # Registro de cambios — Vitalia

            ## [Sin lanzar]

            ### Agregado
            - Reservas prepagadas implementadas.
            - Seguimiento post-tratamiento activado.

            ## [0.1.0] — 2026-05-15

            ### Agregado
            - Lanzamiento inicial.
        """)
        write_changelog(tmp_path, "vitalia", content)

        result = run_script("vitalia", "Unreleased", tmp_path)

        assert result.returncode == 0, f"Se esperaba exit 0, got {result.returncode}. stderr: {result.stderr}"
        assert "Reservas prepagadas implementadas." in result.stdout
        assert "Seguimiento post-tratamiento activado." in result.stdout

    def test_happy_returns_only_unreleased_section(self, tmp_path: Path) -> None:
        """El output no incluye contenido de otras secciones (0.1.0, etc.)."""
        content = textwrap.dedent("""\
            # Registro de cambios — Nicolify

            ## [Sin lanzar]

            ### Agregado
            - Funcionalidad nueva en desarrollo.

            ## [0.2.0] — 2026-04-01

            ### Cambiado
            - Cambio en versión anterior (NO debe aparecer).

            ## [0.1.0] — 2026-03-01

            ### Agregado
            - Versión muy anterior (NO debe aparecer).
        """)
        write_changelog(tmp_path, "nicolify", content)

        result = run_script("nicolify", "Unreleased", tmp_path)

        assert result.returncode == 0
        assert "Funcionalidad nueva en desarrollo." in result.stdout
        assert "Cambio en versión anterior (NO debe aparecer)." not in result.stdout
        assert "Versión muy anterior (NO debe aparecer)." not in result.stdout

    def test_happy_with_multiple_subsections(self, tmp_path: Path) -> None:
        """Sección [Sin lanzar] con múltiples subsecciones (Agregado, Corregido, etc.)."""
        content = textwrap.dedent("""\
            # Registro de cambios — Comunify

            ## [Sin lanzar]

            ### Agregado
            - Motor de comunidades refactorizado.

            ### Corregido
            - Error en el pago de suscripciones.

            ## [1.0.0] — 2026-05-15
        """)
        write_changelog(tmp_path, "comunify", content)

        result = run_script("comunify", "Unreleased", tmp_path)

        assert result.returncode == 0
        assert "Motor de comunidades refactorizado." in result.stdout
        assert "Error en el pago de suscripciones." in result.stdout


class TestEmptySection:
    def test_empty_section_returns_placeholder(self, tmp_path: Path) -> None:
        """Sección [Sin lanzar] vacía → retorna 'Sin cambios documentados.'"""
        content = textwrap.dedent("""\
            # Registro de cambios — Lupulo

            ## [Sin lanzar]

            ## [0.0.1] — 2026-05-15

            ### Agregado
            - Placeholder inicial.
        """)
        write_changelog(tmp_path, "lupulo", content)

        result = run_script("lupulo", "Unreleased", tmp_path)

        assert result.returncode == 0, f"Se esperaba exit 0. stderr: {result.stderr}"
        assert "Sin cambios documentados." in result.stdout

    def test_empty_section_only_whitespace(self, tmp_path: Path) -> None:
        """Sección [Sin lanzar] con solo espacios/líneas vacías → placeholder."""
        content = "# Cambios\n\n## [Sin lanzar]\n\n\n\n## [0.1.0] — 2026-01-01\n"
        write_changelog(tmp_path, "vitalia", content)

        result = run_script("vitalia", "Unreleased", tmp_path)

        assert result.returncode == 0
        assert "Sin cambios documentados." in result.stdout


class TestMissingFile:
    def test_missing_file_exits_nonzero(self, tmp_path: Path) -> None:
        """Archivo CHANGELOG-PUBLIC.md inexistente → exit 1 + mensaje claro."""
        result = run_script("brand_inexistente", "Unreleased", tmp_path)

        assert result.returncode == 1, f"Se esperaba exit 1, got {result.returncode}"
        # Debe indicar el problema en stderr o stdout
        error_output = result.stderr + result.stdout
        assert "brand_inexistente" in error_output or "CHANGELOG-PUBLIC.md" in error_output or "not found" in error_output.lower()

    def test_missing_file_does_not_crash_silently(self, tmp_path: Path) -> None:
        """Archivo missing no debe producir traceback Python sin mensaje útil."""
        result = run_script("no_existe", "Unreleased", tmp_path)

        assert result.returncode != 0
        # No debe ser un traceback sin manejar (aunque puede haber traceback si es intencional)
        # Lo que verificamos es que el exit code sea distinto de 0
        assert result.returncode == 1


class TestMissingSection:
    def test_missing_section_returns_placeholder(self, tmp_path: Path) -> None:
        """Sección solicitada no existe → exit 0 + 'Sin cambios documentados.'"""
        content = textwrap.dedent("""\
            # Registro de cambios

            ## [0.1.0] — 2026-05-15

            ### Agregado
            - Algo.
        """)
        write_changelog(tmp_path, "vitalia", content)

        result = run_script("vitalia", "Unreleased", tmp_path)

        assert result.returncode == 0
        assert "Sin cambios documentados." in result.stdout

    def test_nonexistent_custom_section(self, tmp_path: Path) -> None:
        """Sección personalizada que no existe → exit 0 + placeholder."""
        content = "# Cambios\n\n## [Sin lanzar]\n\n- Algo.\n"
        write_changelog(tmp_path, "nicolify", content)

        result = run_script("nicolify", "SeccionQueNoExiste", tmp_path)

        assert result.returncode == 0
        assert "Sin cambios documentados." in result.stdout


class TestMultipleBrands:
    def test_multiple_brands_independent(self, tmp_path: Path) -> None:
        """El script funciona independientemente para cada brand slug."""
        brands = {
            "nicolify": "- Funcionalidad CRM multi-tenant.",
            "vitalia": "- Reservas prepagadas habilitadas.",
            "comunify": "- Escalera de valor publicada.",
            "lupulo": "- Placeholder restaurante.",
        }
        for brand, entry in brands.items():
            content = f"# Cambios\n\n## [Sin lanzar]\n\n### Agregado\n{entry}\n\n## [0.1.0] — 2026-05-15\n"
            write_changelog(tmp_path, brand, content)

        for brand, entry in brands.items():
            result = run_script(brand, "Unreleased", tmp_path)
            assert result.returncode == 0, f"Falló para brand={brand}: {result.stderr}"
            assert entry in result.stdout, f"Contenido incorrecto para brand={brand}"


class TestCliInterface:
    def test_script_exists(self) -> None:
        """El script existe en la ruta esperada."""
        assert SCRIPT.exists(), f"Script no encontrado en {SCRIPT}"

    def test_help_does_not_crash(self, tmp_path: Path) -> None:
        """--help no genera error."""
        result = subprocess.run(
            [str(PYTHON), str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        # --help retorna 0 en argparse por defecto
        assert result.returncode == 0
        assert "--brand" in result.stdout
        assert "--section" in result.stdout

    def test_missing_args_exits_nonzero(self, tmp_path: Path) -> None:
        """Sin args requeridos → exit distinto de 0."""
        result = subprocess.run(
            [str(PYTHON), str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode != 0
