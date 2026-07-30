#!/usr/bin/env python3
"""check_seam_coverage.py — HB-95/HB-96 seam-testing gate.

"Cubierto" = ejercido contra el COLABORADOR REAL del otro lado de la costura (seam),
no "existe un test verde". Un test que mockea el colaborador bajo prueba NO cubre esa costura.

SSoT doctrina:
  docs/learnings/2026-06-23-coverage-means-real-collaborator-seam-testing.md
  .claude/rules/test-design-doctrine.md § Cobertura = colaborador real, no mock

Dos checks sobre un 04-validators.yaml:

  HB-95 (declaración) — /architect declara `test_construction_plan.seam_coverage`:
      cada entry = {sc, seam, test_type, target}. `seam` ∈ SEAMS · `test_type` ∈ TEST_TYPES
      y permitido para esa costura. `unit-mocked`/`unit`/`mocked` PROHIBIDO para escenario de costura.
      Sin el bloque → UNDECLARED (advisory por default; FAIL con --strict).

  HB-96 (mock-only) — para una costura code-db/router/component-shell, el archivo `target`
      NO puede ser mock-only (solo mockea el colaborador del otro lado). Heurística grep:
      tiene marcadores de mock Y no tiene marcador de colaborador real → MOCK-ONLY (= MISSING).
      Escape por test: una línea `# seam-ok: <razón>` exenta ese archivo (auditor escruta).

Usage:
  check_seam_coverage.py --report <04-validators.yaml> [--story-dir <dir>] [--strict]
  check_seam_coverage.py --self-check
Exit: 0 OK · 1 FAIL (banned/invalid/mock-only) · 2 UNDECLARED (advisory salvo --strict)
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - degradación si falta PyYAML
    print("::warning:: PyYAML ausente → check_seam_coverage degrada (no bloquea)")
    sys.exit(0)

SEAMS = {"code-db", "fe-be", "router", "auth", "component-shell"}
TEST_TYPES = {"integration-realdb", "contract", "router", "e2e-live", "live-verify"}
# valores que delatan cobertura mockeada de una costura → siempre FAIL para escenario de costura
BANNED_TYPES = {"unit", "unit-mocked", "mocked", "unit-mock"}

# qué test_type ejerce de verdad cada costura (la tabla del doctrina, mecanizada)
SEAM_ALLOWED: dict[str, set[str]] = {
    "code-db": {"integration-realdb"},
    "fe-be": {"contract", "e2e-live"},
    "router": {"router", "integration-realdb", "e2e-live"},
    "auth": {"live-verify", "e2e-live"},
    "component-shell": {"e2e-live", "integration-realdb"},
}

# costuras cuyo `target` es un archivo de test local grepeable para el mock-scan (HB-96)
MOCK_SCANNABLE = {"code-db", "router", "component-shell"}
MOCK_MARKERS = re.compile(r"\b(MagicMock|AsyncMock|Mock\(|mock\.patch|patch\(|sentinel\.)\b")
# marcador de "toca el colaborador real" (DB real / router real). Lista conservadora + extensible.
REAL_COLLAB_MARKERS = re.compile(
    r"\b(db_session|async_session|AsyncSession|get_db|TestClient|httpx\.AsyncClient"
    r"|asyncpg|create_async_engine|create_engine|pytest\.mark\.integration"
    r"|real_db|postgres|render\(|screen\.|RenderResult)\b"
)
SEAM_OK_ESCAPE = re.compile(r"#\s*seam-ok:", re.IGNORECASE)


def _entries(validators: dict) -> list[dict]:
    plan = (validators or {}).get("test_construction_plan") or {}
    s2t = plan.get("seam_coverage")
    return s2t if isinstance(s2t, list) else []


def validate_declaration(validators: dict) -> tuple[list[str], bool]:
    """HB-95. Returns (problems, declared?)."""
    problems: list[str] = []
    plan = (validators or {}).get("test_construction_plan") or {}
    if "seam_coverage" not in plan:
        return problems, False
    entries = _entries(validators)
    if not entries:
        problems.append("seam_coverage presente pero vacío")
        return problems, True
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            problems.append(f"entry[{i}] no es un mapping")
            continue
        sc = e.get("sc", f"<entry {i}>")
        seam = e.get("seam")
        tt = e.get("test_type")
        target = e.get("target")
        if seam not in SEAMS:
            problems.append(f"{sc}: seam inválido '{seam}' (∈ {sorted(SEAMS)})")
            continue
        if tt in BANNED_TYPES:
            problems.append(f"{sc}: test_type '{tt}' PROHIBIDO para escenario de costura '{seam}' (mock ≠ cobertura)")
            continue
        if tt not in TEST_TYPES:
            problems.append(f"{sc}: test_type inválido '{tt}' (∈ {sorted(TEST_TYPES)})")
            continue
        if tt not in SEAM_ALLOWED[seam]:
            problems.append(f"{sc}: test_type '{tt}' no ejerce la costura '{seam}' (permitidos: {sorted(SEAM_ALLOWED[seam])})")
        if not target:
            problems.append(f"{sc}: falta `target` (path del test/archivo que ejerce la costura)")
    return problems, True


def _resolve(target: str, search_roots: list[Path]) -> Path | None:
    """Resuelve `target` contra raíces candidatas (ws-root, story-dir). None si no existe."""
    p = Path(target)
    if p.is_absolute():
        return p if p.exists() else None
    for r in search_roots:
        cand = r / target
        if cand.exists():
            return cand
    return None


def scan_mock_only(validators: dict, search_roots: list[Path]) -> list[str]:
    """HB-96. Un `target` de costura grepeable no puede ser mock-only."""
    problems: list[str] = []
    for e in _entries(validators):
        if not isinstance(e, dict):
            continue
        seam, target = e.get("seam"), e.get("target")
        if seam not in MOCK_SCANNABLE or not target:
            continue
        path = _resolve(target, search_roots)
        if path is None:
            # target inexistente lo cazan otros gates (test_construction_plan); acá no opinamos.
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if SEAM_OK_ESCAPE.search(text):
            continue
        if MOCK_MARKERS.search(text) and not REAL_COLLAB_MARKERS.search(text):
            sc = e.get("sc", "?")
            problems.append(
                f"{sc}: MOCK-ONLY (=MISSING) — {target} mockea el colaborador de la costura '{seam}' "
                f"y no toca el colaborador real (sin DB/router/render real). Escape: `# seam-ok: <razón>`."
            )
    return problems


def run_report(validators_path: Path, story_dir: Path | None, strict: bool) -> int:
    try:
        validators = yaml.safe_load(validators_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        # YAML inválido lo gatea HB-93 (frontmatter/yaml gate); acá degradamos con mensaje claro.
        line = getattr(getattr(exc, "problem_mark", None), "line", None)
        where = f" (línea ~{line + 1})" if line is not None else ""
        print(f"::error:: {validators_path}: YAML inválido{where} — no se puede chequear costuras (arreglá el YAML primero · HB-93)")
        return 1
    decl_problems, declared = validate_declaration(validators)
    search_roots: list[Path] = []
    if story_dir:
        # ws-root (git toplevel del archivo) + story-dir como raíces de resolución de targets.
        import subprocess

        try:
            top = subprocess.run(
                ["git", "-C", str(validators_path.parent), "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            if top:
                search_roots.append(Path(top))
        except Exception:
            pass
        search_roots.append(story_dir)
    mock_problems = scan_mock_only(validators, search_roots) if (search_roots and declared) else []

    if not declared:
        msg = "seam_coverage NO declarado — /architect debe declarar seam+test_type por escenario de costura (HB-95)"
        if strict:
            print(f"::error:: {validators_path}: {msg}")
            return 2
        print(f"::warning:: {validators_path}: {msg} [advisory]")
        return 0

    problems = decl_problems + mock_problems
    if problems:
        print(f"::error:: {validators_path}: cobertura de costura inválida:")
        for p in problems:
            print(f"  ✗ {p}")
        return 1
    n = len(_entries(validators))
    print(f"✓ {validators_path}: {n} escenario(s) de costura declarados con test real-collaborator válido")
    return 0


# ── self-check (la prueba: un caso que ANTES pasaba falso-verde debe FALLAR) ──
_FALSE_GREEN = """
test_construction_plan:
  seam_coverage:
    - { sc: SC-create, seam: code-db, test_type: unit-mocked, target: t_create_mock.py }
"""
_INVALID_SEAM = """
test_construction_plan:
  seam_coverage:
    - { sc: SC-x, seam: code-cache, test_type: integration-realdb, target: t.py }
"""
_WRONG_TYPE = """
test_construction_plan:
  seam_coverage:
    - { sc: SC-auth, seam: auth, test_type: integration-realdb, target: t.py }
"""
_GOOD = """
test_construction_plan:
  seam_coverage:
    - { sc: SC-create, seam: code-db, test_type: integration-realdb, target: t_create_realdb.py }
    - { sc: SC-login, seam: auth, test_type: live-verify, target: live }
"""
_UNDECLARED = "test_construction_plan:\n  backend: {}\n"

_MOCK_ONLY_TEST = "from unittest.mock import AsyncMock\n\ndef test_create():\n    repo = AsyncMock()\n    repo.add(row)\n"
_REAL_DB_TEST = "import pytest\n\n@pytest.mark.integration\nasync def test_create(db_session):\n    await db_session.execute(insert)\n"


def _self_check() -> int:
    fails = 0

    def expect(name: str, got: bool, want: bool) -> None:
        nonlocal fails
        ok = got == want
        print(f"  {'✓' if ok else '✗'} {name}: {'FAIL-detected' if got else 'clean'} (esperado {'FAIL' if want else 'clean'})")
        if not ok:
            fails += 1

    # HB-95 declaration logic
    expect("false-green (unit-mocked en costura)", bool(validate_declaration(yaml.safe_load(_FALSE_GREEN))[0]), True)
    expect("seam inválido", bool(validate_declaration(yaml.safe_load(_INVALID_SEAM))[0]), True)
    expect("test_type no ejerce la costura", bool(validate_declaration(yaml.safe_load(_WRONG_TYPE))[0]), True)
    expect("buena declaración", bool(validate_declaration(yaml.safe_load(_GOOD))[0]), False)
    _, declared = validate_declaration(yaml.safe_load(_UNDECLARED))
    expect("undeclared detectado", not declared, True)

    # HB-96 mock-scan (el caso pedido: test que mockea la DB → MOCK-ONLY)
    with tempfile.TemporaryDirectory() as d:
        dd = Path(d)
        (dd / "t_create_mock.py").write_text(_MOCK_ONLY_TEST)
        (dd / "t_create_realdb.py").write_text(_REAL_DB_TEST)
        vbad = yaml.safe_load(
            "test_construction_plan:\n  seam_coverage:\n"
            "    - { sc: SC-create, seam: code-db, test_type: integration-realdb, target: t_create_mock.py }\n"
        )
        vgood = yaml.safe_load(
            "test_construction_plan:\n  seam_coverage:\n"
            "    - { sc: SC-create, seam: code-db, test_type: integration-realdb, target: t_create_realdb.py }\n"
        )
        expect("mock-DB test → MOCK-ONLY", bool(scan_mock_only(vbad, [dd])), True)
        expect("real-DB test → clean", bool(scan_mock_only(vgood, [dd])), False)

    print(f"\nself-check: {'OK' if fails == 0 else f'{fails} FALLO(S)'}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="HB-95/HB-96 seam-testing gate")
    ap.add_argument("--report", type=Path, help="04-validators.yaml a chequear")
    ap.add_argument("--story-dir", type=Path, help="dir de la story (resuelve targets para el mock-scan)")
    ap.add_argument("--strict", action="store_true", help="UNDECLARED → exit 2 (default advisory)")
    ap.add_argument("--self-check", action="store_true", help="corre los fixtures de prueba")
    args = ap.parse_args()
    if args.self_check:
        return _self_check()
    if args.report:
        return run_report(args.report, args.story_dir, args.strict)
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
