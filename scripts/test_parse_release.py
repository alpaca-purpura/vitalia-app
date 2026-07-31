"""
scripts/test_parse_release.py

Helper de test para el regex de parse-release de cd-prod.yml.
Usado por los validators de 04-validators.yaml (scenario_happy_release_to_prod_parse
y scenario_negative_invalid_branch_format).

Uso:
    # Test de branch valido (verifica brand + version extraidos)
    python scripts/test_parse_release.py --fixture "release/vitalia-v0.3.0" \\
        --expect-brand vitalia --expect-version "0.3.0"

    # Test de branch invalido (verifica que retorna exit 1)
    python scripts/test_parse_release.py --fixture "release/invalido-vbroken" \\
        --expect-exit 1

Exit codes:
    0 — La verificacion paso (el fixture se comporto como se esperaba).
    1 — La verificacion fallo (comportamiento inesperado).
"""

from __future__ import annotations

import argparse
import re
import sys

# Brands conocidas (whitelist igual que en cd-prod.yml — single-brand standalone)
KNOWN_BRANDS = {"vitalia"}

# Pattern SemVer con prerelease opcional: X.Y.Z o X.Y.Z-rc1, X.Y.Z-alpha.1, etc.
RELEASE_PATTERN = re.compile(
    r"^release/([a-z][a-z0-9-]*)-v([0-9]+\.[0-9]+\.[0-9]+.*)$"
)
SEMVER_BASE_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+")


def parse_branch(branch: str) -> tuple[str, str] | None:
    """
    Intenta extraer (brand, version) del nombre del branch.

    Retorna (brand, version) si el formato es valido y el brand esta en el whitelist.
    Retorna None si el formato es invalido o el brand no es conocido.
    """
    match = RELEASE_PATTERN.match(branch)
    if not match:
        return None

    brand = match.group(1)
    version = match.group(2)

    # Verificar que la version base es SemVer valido
    if not SEMVER_BASE_PATTERN.match(version):
        return None

    # Verificar whitelist de brands
    if brand not in KNOWN_BRANDS:
        return None

    return brand, version


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida el regex de parse-release de cd-prod.yml con un fixture dado.",
    )
    parser.add_argument(
        "--fixture",
        required=True,
        help="Nombre del branch a parsear (ej: 'release/vitalia-v0.3.0').",
    )
    parser.add_argument(
        "--expect-brand",
        dest="expect_brand",
        default=None,
        help="Brand esperado tras el parseo (ej: vitalia).",
    )
    parser.add_argument(
        "--expect-version",
        dest="expect_version",
        default=None,
        help="Version esperada tras el parseo (ej: 0.3.0).",
    )
    parser.add_argument(
        "--expect-exit",
        dest="expect_exit",
        type=int,
        default=None,
        help="Exit code esperado del parseo: 0 (exito) o 1 (fallo). "
        "Si no se especifica junto con --expect-brand/--expect-version, "
        "se asume --expect-exit 0.",
    )
    args = parser.parse_args()

    result = parse_branch(args.fixture)

    # Determinar si el parse fue exitoso
    parse_ok = result is not None

    if args.expect_exit is not None:
        # Modo de verificacion de exit code
        expected_ok = args.expect_exit == 0
        if parse_ok != expected_ok:
            if expected_ok:
                print(
                    f"FALLO: Se esperaba que '{args.fixture}' fuera valido (exit 0), "
                    f"pero el parseo fallo.",
                    file=sys.stderr,
                )
            else:
                brand, version = result  # type: ignore[misc]
                print(
                    f"FALLO: Se esperaba que '{args.fixture}' fuera invalido (exit 1), "
                    f"pero fue parseado como brand={brand} version={version}.",
                    file=sys.stderr,
                )
            return 1

        print(f"OK: '{args.fixture}' → exit {args.expect_exit} (como se esperaba).")
        return 0

    # Modo de verificacion de brand + version
    if not parse_ok:
        print(
            f"FALLO: '{args.fixture}' no pudo ser parseado. "
            "Formato esperado: release/{{brand}}-vX.Y.Z",
            file=sys.stderr,
        )
        return 1

    brand, version = result  # type: ignore[misc]
    errors: list[str] = []

    if args.expect_brand is not None and brand != args.expect_brand:
        errors.append(f"brand esperado='{args.expect_brand}', obtenido='{brand}'")

    if args.expect_version is not None and version != args.expect_version:
        errors.append(f"version esperada='{args.expect_version}', obtenida='{version}'")

    if errors:
        print(f"FALLO en '{args.fixture}': {'; '.join(errors)}", file=sys.stderr)
        return 1

    print(f"OK: '{args.fixture}' → brand={brand} version={version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
