# T-8 — Impl Log
# CHANGELOG-PUBLIC.md × 4 brands + script extract_changelog_section.py + tests TDD

## TDD ejecutado

Tests escritos PRIMERO en `tests/scripts/test_changelog_extract.py` (13 casos):
- TestHappyPath (3 tests): sección con contenido, no incluye otras secciones, múltiples subsecciones
- TestEmptySection (2 tests): sección vacía, solo whitespace → "Sin cambios documentados."
- TestMissingFile (2 tests): archivo no existe → exit 1 + mensaje claro
- TestMissingSection (2 tests): sección ausente → exit 0 + placeholder
- TestMultipleBrands (1 test): 4 brands independientes
- TestCliInterface (3 tests): script existe, --help no crashea, sin args → exit != 0

RED→GREEN: todos los tests pasaron en la primera ejecución después de implementar el script.

## Deliverables

- CREADO: `tests/scripts/test_changelog_extract.py` (TDD-first, 13 tests)
- CREADO: `scripts/extract_changelog_section.py`
  - CLI: --brand {slug} --section {section}
  - Mapea "Unreleased" → "[Sin lanzar]" y variantes
  - Exit 0 con contenido o "Sin cambios documentados." si vacío/ausente
  - Exit 1 si CHANGELOG-PUBLIC.md no existe

- CREADO: `nicolify/CHANGELOG-PUBLIC.md` — Keep-a-Changelog ES-AR, [Sin lanzar] + [0.1.0]
- CREADO: `vitalia/CHANGELOG-PUBLIC.md` — idem, menciona Story 11 (reservas prepagadas)
- CREADO: `comunify/CHANGELOG-PUBLIC.md` — idem, menciona Story 12 (comunidades, escalera valor)
- CREADO: `lupulo/CHANGELOG-PUBLIC.md` — [Sin lanzar] + [0.0.1] placeholder

## Acceptance criteria result

- A1: pytest tests/scripts/test_changelog_extract.py → 13/13 PASS → PASS
- A2: changelogs sin voseo → 4/4 PASS → PASS
- A3: ruff check + format → 0 errores → PASS
- A4: validators scenario_happy_changelog_extract + changelogs_spanish_neutro → PASS

## State: DONE
