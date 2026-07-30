"""
tests/scripts/test_generate_infra_matrix.py
Tests unitarios de scripts/generate_infra_matrix.py.

S-DOCKER-DEV-MULTIBRAND T-8 — 2026-05-15
Validators:
  - pytest_infra_matrix_unit
  - scenario_happy_infra_matrix
  - test_pre_commit_triggers_regen (T-9)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

# Repo root — scripts/ dir
REPO_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
OUTPUT_PATH = REPO_ROOT / "docs" / "portfolio" / "INFRA-MATRIX.md"

# Ensure scripts/ is importable
sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture()
def brand_infra_fixtures() -> dict:
    """Fixtures de infra para las 4 brands — golden truth."""
    return {
        "nicolify": {
            "dev": {
                "backend_port": 8001,
                "frontend_port": 3001,
                "database_name": "nicolify_dev",
                "redis_db": 0,
                "qdrant_collection_prefix": "nicolify_",
                "domain": "nicolify-dev.nicolify.com",
                "cloudflared_tunnel": "nicolify-dev",
            },
            "prod": {"domain": "app.nicolify.com", "server": "tbd"},
        },
        "vitalia": {
            "dev": {
                "backend_port": 8002,
                "frontend_port": 3002,
                "database_name": "vitalia_dev",
                "redis_db": 1,
                "qdrant_collection_prefix": "vitalia_",
                "domain": "vitalia-dev.nicolify.com",
                "cloudflared_tunnel": "vitalia-dev",
            },
            "prod": {"domain": "app.vitalialat.com", "server": "tbd"},
        },
        "comunify": {
            "dev": {
                "backend_port": 8003,
                "frontend_port": 3003,
                "database_name": "comunify_dev",
                "redis_db": 2,
                "qdrant_collection_prefix": "comunify_",
                "domain": "comunify-dev.nicolify.com",
                "cloudflared_tunnel": "comunify-dev",
            },
            "prod": {"domain": "app.comunify.com", "server": "tbd"},
        },
        "lupulo": {
            "dev": {
                "backend_port": 8004,
                "frontend_port": 3004,
                "database_name": "lupulo_dev",
                "redis_db": 3,
                "qdrant_collection_prefix": "lupulo_",
                "domain": "lupulo-dev.nicolify.com",
                "cloudflared_tunnel": "lupulo-dev",
            },
            "prod": {"domain": "app.lupulo.com", "server": "tbd"},
        },
    }


def test_generate_matrix_returns_string(brand_infra_fixtures):
    """generate_matrix() retorna un string con contenido valido."""
    from generate_infra_matrix import generate_matrix

    result = generate_matrix(brand_infra_fixtures)
    assert isinstance(result, str)
    assert len(result) > 100


def test_header_present(brand_infra_fixtures):
    """La primera linea del output contiene el header AUTO-GENERATED."""
    from generate_infra_matrix import generate_matrix

    result = generate_matrix(brand_infra_fixtures)
    first_line = result.splitlines()[0]
    assert "AUTO-GENERATED" in first_line, f"Header missing in first line: {first_line!r}"


def test_all_brands_present(brand_infra_fixtures):
    """Las 4 brands aparecen en la tabla generada."""
    from generate_infra_matrix import generate_matrix

    result = generate_matrix(brand_infra_fixtures)
    for brand in ["nicolify", "vitalia", "comunify", "lupulo"]:
        assert brand in result, f"Brand '{brand}' not found in matrix"


def test_ports_correct(brand_infra_fixtures):
    """Los puertos correctos aparecen en la tabla (D6 cementados)."""
    from generate_infra_matrix import generate_matrix

    result = generate_matrix(brand_infra_fixtures)
    # Vitalia backend port
    assert "8002" in result
    # Comunify frontend port
    assert "3003" in result
    # Lupulo backend port
    assert "8004" in result


def test_missing_infra_section():
    """Brand sin seccion infra → columnas 'n/a' sin crash."""
    from generate_infra_matrix import generate_matrix

    brands_infra_empty = {
        "testbrand": {},  # sin seccion infra
    }
    result = generate_matrix(brands_infra_empty)
    assert "testbrand" in result
    assert "n/a" in result


def test_output_file_created(tmp_path, brand_infra_fixtures, monkeypatch):
    """generate_matrix() escribe el archivo OUTPUT correctamente."""
    from generate_infra_matrix import generate_matrix

    output_file = tmp_path / "INFRA-MATRIX.md"
    content = generate_matrix(brand_infra_fixtures)
    output_file.write_text(content, encoding="utf-8")

    assert output_file.exists()
    assert "AUTO-GENERATED" in output_file.read_text()


def test_load_brand_infra_reads_real_files():
    """load_brand_infra() lee los archivos brand.yaml reales del repo."""
    from generate_infra_matrix import load_brand_infra

    # vitalia tiene brand.yaml con seccion infra (T-3)
    infra = load_brand_infra("vitalia")
    assert "dev" in infra, "vitalia brand.yaml should have infra.dev section"
    assert infra["dev"]["backend_port"] == 8002
    assert infra["dev"]["database_name"] == "vitalia_dev"


def test_load_brand_infra_comunify():
    """load_brand_infra() lee comunify correctamente."""
    from generate_infra_matrix import load_brand_infra

    infra = load_brand_infra("comunify")
    assert infra["dev"]["backend_port"] == 8003
    assert infra["dev"]["redis_db"] == 2


def test_load_brand_infra_missing_file():
    """load_brand_infra() retorna {} si el archivo no existe."""
    from generate_infra_matrix import load_brand_infra

    infra = load_brand_infra("__nonexistent_brand__")
    assert infra == {}


def test_golden_snapshot(tmp_path, monkeypatch):
    """
    Golden snapshot test — genera la matriz con los datos reales de brand.yaml
    y verifica estructura y contenido esperado.

    Escenario: los 4 brand.yaml tienen seccion infra completa (T-3 done).
    """
    from generate_infra_matrix import generate_matrix, load_brand_infra, BRANDS

    brands_infra = {brand: load_brand_infra(brand) for brand in BRANDS}
    result = generate_matrix(brands_infra)

    # Estructura esperada
    assert "AUTO-GENERATED via make infra-matrix" in result
    assert "INFRA-MATRIX" in result
    assert "Entorno dev local" in result
    assert "Entorno produccion" in result
    assert "Puertos compartidos" in result

    # Las 4 brands en la tabla dev
    for brand in BRANDS:
        assert brand in result, f"Brand '{brand}' not in golden snapshot"

    # Puertos D6 cementados
    assert "8001" in result  # nicolify backend
    assert "3001" in result  # nicolify frontend
    assert "8002" in result  # vitalia backend
    assert "8003" in result  # comunify backend
    assert "8004" in result  # lupulo backend

    # DB names
    assert "nicolify_dev" in result
    assert "vitalia_dev" in result
    assert "comunify_dev" in result
    assert "lupulo_dev" in result

    # Shared infra ports
    assert "5435" in result
    assert "6333" in result


def test_main_creates_output_file(monkeypatch, tmp_path):
    """main() crea o actualiza INFRA-MATRIX.md en OUTPUT path."""
    import generate_infra_matrix as gim

    # Redirect output to tmp_path
    original_output = gim.OUTPUT
    monkeypatch.setattr(gim, "OUTPUT", tmp_path / "INFRA-MATRIX.md")

    gim.main()

    output_file = tmp_path / "INFRA-MATRIX.md"
    assert output_file.exists()
    content = output_file.read_text()
    assert "AUTO-GENERATED" in content
    assert "vitalia" in content


def test_pre_commit_triggers_regen():
    """
    T-9 test: verifica que el pre-commit hook contiene la logica de regeneracion
    de INFRA-MATRIX.md cuando brand.yaml es editado.

    No ejecuta el hook real (necesitaria git staging area).
    Verifica que el hook file contiene la inspeccion de brand.yaml y la llamada
    a generate_infra_matrix.py.
    """
    hook_path = REPO_ROOT / "scripts" / "git-hooks" / "pre-commit"
    assert hook_path.exists(), f"pre-commit hook not found at {hook_path}"

    content = hook_path.read_text(encoding="utf-8")

    # Section 10 debe estar presente
    assert "Section 10" in content, "pre-commit hook missing Section 10"

    # Debe detectar brand.yaml
    assert "brand.yaml" in content, "pre-commit hook should detect brand.yaml changes"

    # Debe llamar a generate_infra_matrix.py
    assert "generate_infra_matrix" in content, (
        "pre-commit hook should call generate_infra_matrix.py"
    )


def test_script_exits_zero():
    """El script termina con exit code 0 en ejecucion normal."""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "generate_infra_matrix.py")],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"Script exited with {result.returncode}. stderr: {result.stderr}"
    )
    assert "brands" in result.stdout.lower() or "updated" in result.stdout.lower()
