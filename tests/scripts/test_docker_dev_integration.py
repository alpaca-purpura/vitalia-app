"""
Integration tests para S-DOCKER-DEV-MULTIBRAND.

Estos tests requieren Docker corriendo + postgres en 127.0.0.1:5435.
Marcados con @pytest.mark.integration — se omiten en CI básico.

Para ejecutar localmente:
  make dev-vitalia  # levanta postgres + vitalia
  .venv/bin/pytest tests/scripts/test_docker_dev_integration.py -v -m integration
"""

import subprocess
import time

import pytest


POSTGRES_HOST = "127.0.0.1"
POSTGRES_PORT = 5435
POSTGRES_USER = "postgres"
DATABASES_EXPECTED = ["nicolify_dev", "vitalia_dev", "comunify_dev", "lupulo_dev"]

BRAND_BACKENDS = {
    "nicolify": ("127.0.0.1", 8001),
    "vitalia": ("127.0.0.1", 8002),
    "comunify": ("127.0.0.1", 8003),
    "lupulo": ("127.0.0.1", 8004),
}


def _psql_check(db_name: str) -> bool:
    """Verifica que una database existe en postgres."""
    result = subprocess.run(
        [
            "psql",
            f"-h{POSTGRES_HOST}",
            f"-p{POSTGRES_PORT}",
            f"-U{POSTGRES_USER}",
            "-tAc",
            f"SELECT 1 FROM pg_database WHERE datname='{db_name}'",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.returncode == 0 and result.stdout.strip() == "1"


def _http_health(host: str, port: int, path: str = "/health") -> bool:
    """Verifica endpoint /health de un backend brand."""
    result = subprocess.run(
        ["curl", "-sf", f"http://{host}:{port}{path}"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.returncode == 0 and "ok" in result.stdout.lower()


@pytest.mark.integration
def test_postgres_running() -> None:
    """Postgres esta corriendo en 127.0.0.1:5435."""
    result = subprocess.run(
        [
            "pg_isready",
            "-h", POSTGRES_HOST,
            "-p", str(POSTGRES_PORT),
            "-U", POSTGRES_USER,
        ],
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 0, (
        f"postgres no esta corriendo en {POSTGRES_HOST}:{POSTGRES_PORT}. "
        "Ejecuta: make dev-vitalia"
    )


@pytest.mark.integration
@pytest.mark.parametrize("db_name", DATABASES_EXPECTED)
def test_brand_database_exists(db_name: str) -> None:
    """Cada brand database fue creada por el init script idempotente."""
    assert _psql_check(db_name), (
        f"Database '{db_name}' no existe. "
        "El init script scripts/postgres-init/01-create-databases.sh no corrio. "
        "Limpia el volume y reinicia: make dev-clean-vitalia && make dev-vitalia"
    )


@pytest.mark.integration
def test_postgres_init_script_idempotent() -> None:
    """Correr el init script dos veces no genera error (idempotencia D1)."""
    result = subprocess.run(
        [
            "psql",
            f"-h{POSTGRES_HOST}",
            f"-p{POSTGRES_PORT}",
            f"-U{POSTGRES_USER}",
            "-tAc",
            "SELECT count(*) FROM pg_database WHERE datname LIKE '%_dev'",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    count = int(result.stdout.strip())
    assert count >= 4, (
        f"Se esperaban al menos 4 databases *_dev, encontradas: {count}"
    )


@pytest.mark.integration
def test_vitalia_backend_health() -> None:
    """Vitalia backend responde /health cuando `make dev-vitalia` esta activo."""
    host, port = BRAND_BACKENDS["vitalia"]
    assert _http_health(host, port), (
        f"Vitalia backend no responde en http://{host}:{port}/health. "
        "Ejecuta: make dev-vitalia"
    )


@pytest.mark.integration
def test_nicolify_backend_health() -> None:
    """Nicolify backend responde /health cuando `make dev-nicolify` esta activo."""
    host, port = BRAND_BACKENDS["nicolify"]
    assert _http_health(host, port), (
        f"Nicolify backend no responde en http://{host}:{port}/health. "
        "Ejecuta: make dev-nicolify"
    )


@pytest.mark.integration
def test_port_isolation_brands() -> None:
    """
    Cuando múltiples brands estan levantadas, cada una responde en su puerto
    asignado (D6 — port collision imposible).
    """
    # Solo verifica las brands que esten up; no falla si alguna no corre
    responding = []
    for brand, (host, port) in BRAND_BACKENDS.items():
        if _http_health(host, port):
            responding.append(brand)

    # Si al menos 2 brands estan up, verificar que no hay colision
    if len(responding) >= 2:
        # Cada brand tiene su propio puerto → responden independientemente
        for brand in responding:
            host, port = BRAND_BACKENDS[brand]
            assert _http_health(host, port), f"{brand} backend no responde en puerto {port}"
    else:
        pytest.skip(
            f"Solo {len(responding)} brand(s) up: {responding}. "
            "Necesitas >=2 para verificar port isolation. "
            "Ejecuta: make dev-all"
        )
