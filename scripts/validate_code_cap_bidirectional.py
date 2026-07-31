#!/usr/bin/env python3
"""Bidirectional validator code↔cap mapping (cement 2026-05-28).

Cross-checks 2 niveles (atomics killed 2026-05-28 — ver docs/process/lifecycle.md):

3. **Scenarios e2e_test path existence**: `cap.scenarios[*].e2e_test` declarado debe
   existir en filesystem + contener `test(` o `test.describe(`. Missing → HARD pre-push block.

4. **Access roles ↔ runtime decorators (P4)**: roles en `cap.access.entry_points[*].requires_role`
   coinciden con `@require_phi_access(roles=[...])` decorators del código. HARD para vitalia
   (es salud; PHI access no puede ser advisory), advisory para otras brands.

Output:
  `{brand}/docs/product/capabilities/_bidirectional-validation.json` (gitignored R3 v2)

Usage:
  python3 scripts/validate_code_cap_bidirectional.py --brand vitalia
  python3 scripts/validate_code_cap_bidirectional.py --brand vitalia --strict
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


# ── Resolver único (HB-51 · Capa 1/5) — SSoT de "qué cap es este header" ──────
# Importado por path para no depender de sys.path (scripts/ no es un paquete).
def _import_sibling(name: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parent / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


resolve_cap = _import_sibling("resolve_cap")
validate_system_map = _import_sibling("validate_system_map")
validate_caps_schema = _import_sibling("validate_caps_schema")

# Header regex (kept for cross-check 4 file association via code-index)
HEADER_PY_CAP = re.compile(r"^\s*#\s*cap:\s*(.+?)\s*$", re.MULTILINE)
HEADER_TS_CAP = re.compile(r"^\s*//\s*cap:\s*(.+?)\s*$", re.MULTILINE)

# Decorator detection patterns for cross-check 4
DECORATOR_RE = re.compile(
    r"@require_phi_access\s*\(\s*roles\s*=\s*\[([^\]]*)\]\s*\)",
    re.MULTILINE,
)

# Additional PHI/role enforcement mechanisms recognized by cross-check 4.
# The codebase enforces access gates via several idioms beyond the
# @require_phi_access decorator. cross_check_4 must recognize ALL of them,
# otherwise it reports false drift where enforcement actually exists.

# 1. FastAPI Depends factory: require_brand_owner_access() (rbac.py:65)
#    Used as `Depends(require_brand_owner_access())` or `Depends(_brand_owner_required)`.
DEPENDS_BRAND_OWNER_RE = re.compile(r"require_brand_owner_access\s*\(", re.MULTILINE)

# 2. Helper call: _assert_phi_access(role) (e.g. inbox/api/router.py:300)
ASSERT_PHI_RE = re.compile(r"_assert_phi_access\s*\(", re.MULTILINE)

# 3. Inline frozenset/list role gate: `if <role_var> not in <NAME>: ... raise ... 403`
#    where <NAME> looks like a PHI/role allowlist (_PHI_ROLES, ALLOWED_PHI_ROLES,
#    _NPS_SUMMARY_ROLES, etc.). We detect the gate idiom by the frozenset name
#    convention + a `not in` membership check.
INLINE_ROLE_GATE_NAME_RE = re.compile(
    r"\bnot\s+in\s+("
    r"_?[A-Z][A-Z0-9_]*(?:PHI|ROLES|ROLE)[A-Z0-9_]*"  # _PHI_ROLES, ALLOWED_PHI_ROLES, _NPS_SUMMARY_ROLES
    r")\b",
    re.MULTILINE,
)

# JS/TS Playwright test detection (cross_check_3, non-.py files).
# Recognizes the plain runner AND fixture-extended runners. Playwright's
# canonical pattern for authenticated suites is `const authTest = test.extend<...>()`
# followed by `authTest(...)` / `authTest.describe(...)` — the derived runner never
# literally contains the substring "test(" (capital T in "authTest"), so a naive
# substring scan reports false drift on real, passing suites. We therefore match:
#   - test(  /  test.describe(                 (plain Playwright runner)
#   - test.extend<...>  /  test.extend(        (fixture definition ⇒ file has tests)
#   - <name>Test(  /  <name>Test.describe(     (fixture-extended runner call, capital T)
#   - <name>Test.extend<...>                   (chained fixture extension)
# The plain-runner alternatives are a strict superset of the old substring check,
# so no previously-passing file regresses. Capital-T anchoring avoids matching
# innocuous identifiers like `latest(` / `fastest(`.
JS_TEST_RE = re.compile(
    r"\btest\s*\("  # test(
    r"|\btest\s*\.\s*describe\s*\("  # test.describe(
    r"|\btest\s*\.\s*extend\s*[<(]"  # test.extend<...>  /  test.extend(
    r"|\b[A-Za-z_$][\w$]*Test\s*\("  # authTest(
    r"|\b[A-Za-z_$][\w$]*Test\s*\.\s*(?:describe|extend)\s*[<(]"  # authTest.describe( / .extend(
)

# Pytest test pattern: matches 'def test_foo', 'def test(', 'def test_anything'.
# Used by cross_check_3 when the declared e2e_test path has a .py extension.
# JS_TEST_RE above is used for .ts / .tsx / any other extension.
PYTEST_PATTERN = re.compile(r"\bdef test", re.MULTILINE)


# ---------------------------------------------------------------------------
# Cap loading
# ---------------------------------------------------------------------------


def _parse_frontmatter(path: Path) -> dict[str, Any] | None:
    """Parse YAML frontmatter from cap file."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    lines = text.splitlines(keepends=True)
    cursor = 0
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped in {"", "\n"}:
            cursor += len(line)
            continue
        break

    body = text[cursor:]
    if body.startswith("---"):
        after = body[3:].lstrip("\n")
        yaml_text = after.split("\n---", 1)[0]
    else:
        # Caps reconciladas (reconcile_capabilities.py) NO traen fence `---` de apertura:
        # comentarios + key:values. YAML = hasta el primer separador `---` o EOF. Sin esto
        # 2/3 caps de nicolify quedaban invisibles a los gates (las veía el resolver pero no
        # load_capabilities → inconsistencia).
        yaml_text = re.split(r"(?m)^---[ \t]*$", body, maxsplit=1)[0]

    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return None

    if not isinstance(data, dict):
        return None
    return data


def load_capabilities(brand: str, workspace_root: Path) -> dict[str, dict[str, Any]]:
    """Load all caps for brand. Returns dict slug → frontmatter + path."""
    caps_root = workspace_root / brand / "docs" / "product" / "capabilities"
    if not caps_root.exists():
        return {}

    caps: dict[str, dict[str, Any]] = {}
    for yaml_path in caps_root.rglob("*.yaml"):
        if yaml_path.name.startswith("_"):
            continue
        data = _parse_frontmatter(yaml_path)
        if data is None:
            continue
        module = yaml_path.parent.name
        slug = data.get("slug") or yaml_path.stem
        cap_id = f"{module}.{slug}"
        data["_cap_id"] = cap_id
        data["_path"] = str(yaml_path.relative_to(workspace_root))
        data["_module"] = module
        caps[cap_id] = data
    return caps


# ---------------------------------------------------------------------------
# Cross-check 3 — Scenarios e2e_test path existence
# ---------------------------------------------------------------------------


def cross_check_3(
    caps: dict[str, dict],
    workspace_root: Path,
) -> dict[str, Any]:
    """For each cap.scenarios[*].e2e_test, verify path exists + contains test patterns."""
    results: list[dict] = []
    total = 0
    passing = 0
    drift = 0

    for cap_id, cap_data in caps.items():
        scenarios = cap_data.get("scenarios") or []
        if not isinstance(scenarios, list):
            continue
        for scenario in scenarios:
            if not isinstance(scenario, dict):
                continue
            e2e_test = scenario.get("e2e_test")
            if not e2e_test:
                continue
            total += 1
            full_path = workspace_root / e2e_test
            if not full_path.exists():
                drift += 1
                results.append(
                    {
                        "cap_id": cap_id,
                        "scenario_id": scenario.get("id", "<unknown>"),
                        "declared_e2e_test": e2e_test,
                        "status": "missing_file",
                        "drift_reason": "e2e_test path doesn't exist",
                    }
                )
                continue

            try:
                content = full_path.read_text(encoding="utf-8")
            except OSError:
                drift += 1
                results.append(
                    {
                        "cap_id": cap_id,
                        "scenario_id": scenario.get("id"),
                        "declared_e2e_test": e2e_test,
                        "status": "read_error",
                        "drift_reason": "could not read file",
                    }
                )
                continue

            # Path-aware pattern check: pytest for .py, Playwright (incl.
            # fixture-extended runners like authTest) for others.
            if full_path.suffix == ".py":
                has_pattern = bool(PYTEST_PATTERN.search(content))
            else:
                has_pattern = bool(JS_TEST_RE.search(content))
            if has_pattern:
                passing += 1
            else:
                drift += 1
                results.append(
                    {
                        "cap_id": cap_id,
                        "scenario_id": scenario.get("id"),
                        "declared_e2e_test": e2e_test,
                        "status": "no_test_pattern",
                        "drift_reason": (
                            "file exists but contains no test pattern "
                            "('def test' for .py; 'test('/'test.describe('/'test.extend' "
                            "or a fixture-extended runner like 'authTest(' for .ts/.tsx)"
                        ),
                    }
                )

    return {
        "total": total,
        "pass": passing,
        "drift": drift,
        "details": results,
    }


# ---------------------------------------------------------------------------
# Cross-check 4 — Access roles ↔ runtime decorators
# ---------------------------------------------------------------------------


def detect_enforcement(content: str) -> dict[str, Any]:
    """Detect ALL PHI/role enforcement mechanisms present in a Python file.

    The codebase gates access via several idioms (not only @require_phi_access):

    - ``@require_phi_access(roles=[...])`` decorator (rbac.py)
    - ``Depends(require_brand_owner_access())`` FastAPI dependency (rbac.py:65)
    - ``_assert_phi_access(role)`` helper (inbox/api/router.py:300)
    - inline ``if <role> not in <FROZENSET>: raise ...403`` where the frozenset is
      named like ``_PHI_ROLES`` / ``ALLOWED_PHI_ROLES`` / ``_NPS_SUMMARY_ROLES``
      (scheduling/api/agenda_router.py, fidelizacion/api/nps_endpoints.py)

    Returns dict with:
      - ``enforced`` (bool): any mechanism present
      - ``mechanisms`` (list[str]): which mechanisms matched
      - ``decorator_roles`` (set[str]): roles parsed from @require_phi_access (if any)
    """
    mechanisms: list[str] = []
    decorator_roles: set[str] = set()

    for match in DECORATOR_RE.finditer(content):
        if "require_phi_access" not in mechanisms:
            mechanisms.append("require_phi_access")
        for r in re.findall(r"['\"](\w+)['\"]", match.group(1)):
            decorator_roles.add(r)

    if DEPENDS_BRAND_OWNER_RE.search(content):
        mechanisms.append("require_brand_owner_access")

    if ASSERT_PHI_RE.search(content):
        mechanisms.append("_assert_phi_access")

    for m in INLINE_ROLE_GATE_NAME_RE.finditer(content):
        gate_name = m.group(1)
        # only count it if there's a raise/HTTPException 403 in the file
        if "403" in content or "HTTP_403_FORBIDDEN" in content or "PHIAccessDeniedError" in content:
            mechanisms.append(f"inline_role_gate:{gate_name}")

    return {
        "enforced": bool(mechanisms),
        "mechanisms": mechanisms,
        "decorator_roles": decorator_roles,
    }


# HB-59: matchea un route-decorator FastAPI por el último segmento literal del path
# (robusto a prefijos de router: `@router.get("/events")` con prefix `/medical-compliance`).
_ROUTE_DECO_RE_TMPL = r"@\w+\.(?:get|post|put|patch|delete)\(\s*[\"'][^\"']*\b{seg}\b"


def _shared_file_enforcement_for_path(
    workspace_root: Path, shared_files: list[str], path: str | None
) -> tuple[list[str], set[str]]:
    """HB-59 — busca el enforcement de un endpoint que vive en un god-file
    `# cap: __shared__` (excluido del index per-cap), detectándolo SOLO en el
    cuerpo de ESA función (decorador→def→body, hasta el próximo endpoint a col 0).

    No escanea el god-file entero a propósito: atribuir el gate de un endpoint
    VECINO daría un false-"enforced" (false-negative de seguridad). El bloque
    se corta en el siguiente `@deco`/`def` a columna 0 tras el `def` de esta
    función → captura sus decoradores apilados + Depends(...) + gate inline, nada más.
    Devuelve (mechanisms, decorator_roles). Vacío si no hay match o no hay gate.
    """
    if not path:
        return [], set()
    segs = [s for s in path.strip("/").split("/") if s and "{" not in s]
    if not segs:
        return [], set()
    route_re = re.compile(_ROUTE_DECO_RE_TMPL.format(seg=re.escape(segs[-1])))
    mechs: list[str] = []
    roles: set[str] = set()
    for rel in shared_files:
        full = workspace_root / rel
        if full.suffix != ".py" or not full.exists():
            continue
        try:
            content = full.read_text(encoding="utf-8")
        except OSError:
            continue
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if not route_re.search(line):
                continue
            block = [line]
            seen_def = False
            for nxt in lines[i + 1 :]:
                is_col0 = bool(nxt) and not nxt[:1].isspace()
                starts_unit = nxt.startswith(("@", "def ", "async def "))
                if seen_def and is_col0 and starts_unit:
                    break  # próximo endpoint a col 0 → fin del cuerpo de esta función
                block.append(nxt)
                if nxt.startswith(("def ", "async def ")):
                    seen_def = True
            det = detect_enforcement("\n".join(block))
            mechs.extend(det["mechanisms"])
            roles |= det["decorator_roles"]
    return mechs, roles


def cross_check_4(
    caps: dict[str, dict],
    workspace_root: Path,
    brand: str,
) -> dict[str, Any]:
    """For each cap.access.entry_points[*].requires_role, cross-check enforcement in code.

    Recognizes ALL enforcement mechanisms (see ``detect_enforcement``), not just
    the ``@require_phi_access`` decorator. An entry_point whose associated code
    has ANY recognized mechanism counts as ENFORCED (no drift).

    SKIP rules (no cross-check, not counted):
      - entry_point ``path`` is null (no HTTP surface to gate)
      - cap is ``user_visible: false`` + ``nature: extension-point``
        (BE-only extension point, no HTTP PHI endpoint)

    Related files are resolved from ``_code-index.json`` cap_to_files (headers
    ``# cap: <cap_id>``).
    """
    results: list[dict] = []
    total = 0
    passing = 0
    drift = 0
    skipped = 0

    # Pre-load code index if exists (cap → files via headers)
    code_index_path = workspace_root / brand / "docs" / "product" / "capabilities" / "_code-index.json"
    code_index: dict[str, list[str]] = {}
    shared_files: list[str] = []
    if code_index_path.exists():
        try:
            ci = json.loads(code_index_path.read_text())
            # HB-59: preferí resolved_cap_to_files (keyea el cap_id CANÓNICO → cubre
            # headers alias como `lisa.servicios` ≠ cap_id `offer.lisa-servicios`);
            # fallback a cap_to_files (back-compat + tests viejos que escriben solo eso).
            code_index = ci.get("resolved_cap_to_files") or ci.get("cap_to_files", {})
            shared_files = ci.get("shared_files", []) or []
        except (json.JSONDecodeError, OSError):
            code_index = {}

    for cap_id, cap_data in caps.items():
        access = cap_data.get("access")
        if not isinstance(access, dict):
            continue
        entry_points = access.get("entry_points") or []
        if not isinstance(entry_points, list):
            continue

        # SKIP whole cap if it's a BE-only extension point (no HTTP PHI endpoint)
        cap_user_visible = cap_data.get("user_visible")
        cap_nature = cap_data.get("nature")
        cap_is_extension_point = (cap_user_visible is False) and (cap_nature == "extension-point")

        # Get files associated with this cap via code-index headers (# cap:)
        related_files: set[str] = set(code_index.get(cap_id, []))

        # Detect enforcement mechanisms across all related backend files (once per cap)
        cap_mechanisms: list[str] = []
        cap_decorator_roles: set[str] = set()
        for rel_file in related_files:
            full = workspace_root / rel_file
            if not full.exists() or full.suffix != ".py":
                continue
            try:
                content = full.read_text(encoding="utf-8")
            except OSError:
                continue
            det = detect_enforcement(content)
            cap_mechanisms.extend(det["mechanisms"])
            cap_decorator_roles |= det["decorator_roles"]

        for entry in entry_points:
            if not isinstance(entry, dict):
                continue
            declared_roles = set(entry.get("requires_role") or [])
            entry_type = entry.get("entry_type", "ui")
            path = entry.get("path")

            if not declared_roles:
                # No roles declared, no cross-check needed
                continue

            # SKIP: null path (no HTTP surface) OR BE-only extension point
            if path is None or cap_is_extension_point:
                skipped += 1
                continue

            total += 1

            # HB-59: si el cap no tiene enforcement en sus archivos per-cap, el
            # endpoint puede vivir en un god-file `# cap: __shared__` (excluido del
            # index per-cap). Buscá el enforcement en el CUERPO de ESA función
            # específica (no en todo el god-file → cero false-positive de un endpoint
            # vecino enforced). Sólo aplica a entradas con `path` (api real).
            eff_mechanisms = list(cap_mechanisms)
            eff_roles = set(cap_decorator_roles)
            if not eff_mechanisms and shared_files:
                sh_mechs, sh_roles = _shared_file_enforcement_for_path(workspace_root, shared_files, path)
                if sh_mechs:
                    eff_mechanisms = sh_mechs
                    eff_roles = sh_roles

            if eff_mechanisms:
                # Enforcement present via at least one recognized mechanism.
                # If a @require_phi_access decorator declares roles, prefer the
                # exact-match semantics for that (catches role drift). Otherwise
                # (Depends / _assert_phi_access / inline frozenset gate) the
                # mechanism's allowlist lives in code constants we don't fully
                # parse — presence of the gate is sufficient to count ENFORCED.
                if eff_roles and declared_roles != eff_roles:
                    drift += 1
                    results.append(
                        {
                            "cap_id": cap_id,
                            "path": path,
                            "entry_type": entry_type,
                            "declared_roles": sorted(declared_roles),
                            "runtime_roles": sorted(eff_roles),
                            "mechanisms": sorted(set(eff_mechanisms)),
                            "status": "role_mismatch",
                            "drift_reason": (
                                f"cap declares roles {sorted(declared_roles)} but "
                                f"@require_phi_access decorator declares "
                                f"{sorted(eff_roles)}"
                            ),
                        }
                    )
                else:
                    passing += 1
                continue

            # No enforcement mechanism found · only drift if entry_type=api (BE)
            if entry_type == "api":
                drift += 1
                results.append(
                    {
                        "cap_id": cap_id,
                        "path": path,
                        "entry_type": entry_type,
                        "declared_roles": sorted(declared_roles),
                        "runtime_roles": [],
                        "mechanisms": [],
                        "status": "no_enforcement_found",
                        "drift_reason": (
                            "cap declares requires_role but no recognized enforcement "
                            "mechanism (@require_phi_access / require_brand_owner_access / "
                            "_assert_phi_access / inline role frozenset gate) in associated code"
                        ),
                    }
                )
            else:
                # UI entry — not all routes have decorators (some Clerk middleware level)
                passing += 1

    return {
        "total": total,
        "pass": passing,
        "drift": drift,
        "skipped": skipped,
        "details": results,
    }


# ═══════════════════════════════════════════════════════════════════════════
# HB-51 · Gates determinísticos G1-G6 (cap-format enforcement máximo)
# ═══════════════════════════════════════════════════════════════════════════
#
# G1-G6 corren sobre el resolver único (resolve_cap.py). Cada uno devuelve el
# mismo shape {total,pass,drift,details} que los cross_checks. Negative tests:
# scripts/tests/test_validate_code_cap_bidirectional.py. ADVISORY hasta backfill
# (slice 8), después HARD via --cap-gates-hard (pre-commit 5c/5d + pre-push 4d).

# Captura SOLO el cap-token (charset cap-id) o una lista `[...]`. Frena en el
# primer carácter ajeno (espacio, `#` de un comentario inline tipo lint-ignore,
# `"`/`)`/`;` de un header embebido en un string literal) → robusto contra ruido inline.
_CAP_TOKEN = r"(\[[^\]]*\]|[A-Za-z0-9._/-]+)"
_HEADER_PY = re.compile(r"^\s*#\s*cap:\s*" + _CAP_TOKEN, re.MULTILINE)
_HEADER_TS = re.compile(r"^\s*//\s*cap:\s*" + _CAP_TOKEN, re.MULTILINE)
_SPECIAL = frozenset({"__shared__", "__orphan__", "__skip__", "TBD"})


def _scan_code_headers(brand: str, workspace_root: Path) -> dict[str, list[str]]:
    """Escanea backend/src + frontend/src → {header_token: [sample_file, ...]}.

    Gate-self-contained: NO depende de `_code-index.json` (que puede estar stale en
    pre-push). Lee solo las primeras 20 líneas (el header vive arriba).
    """
    out: dict[str, list[str]] = {}
    targets = [
        (workspace_root / brand / "backend" / "src", "*.py", _HEADER_PY),
        (workspace_root / brand / "frontend" / "src", "*.ts", _HEADER_TS),
        (workspace_root / brand / "frontend" / "src", "*.tsx", _HEADER_TS),
    ]
    for root, ext, pat in targets:
        if not root.is_dir():
            continue
        for p in root.rglob(ext):
            if "__pycache__" in p.parts:
                continue
            name = p.name
            if name.endswith((".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx")):
                continue
            if any(part == "__tests__" for part in p.parts):
                continue
            try:
                with p.open(encoding="utf-8") as fh:
                    head = "".join(fh.readline() for _ in range(20))
            except (OSError, UnicodeDecodeError):
                continue
            m = pat.search(head)
            if not m:
                continue
            raw = m.group(1).strip()
            # Notación multi-cap `[a.b, c.d]` → cada token por separado
            tokens = (
                [t.strip() for t in raw[1:-1].split(",") if t.strip()]
                if raw.startswith("[") and raw.endswith("]")
                else [raw]
            )
            for tok in tokens:
                if tok in _SPECIAL:
                    continue
                out.setdefault(tok, []).append(str(p.relative_to(workspace_root)))
    return out


def gate_g1_header_resolves(brand: str, workspace_root: Path) -> dict[str, Any]:
    """G1 — todo header `# cap:`/`// cap:` resuelve a ≥1 cap REAL (cap_id o alias).

    Header → cap inexistente = FAIL (caza el incidente origen: `inbox.adrian-inbox`
    huérfano). Usa resolve_cap.resolve_cap_ids (≥1 ⇒ resuelve · functional_area es
    área 1:N, por eso ≥1, no ==1).
    """
    headers = _scan_code_headers(brand, workspace_root)
    results: list[dict] = []
    total = 0
    passing = 0
    drift = 0
    for token, files in sorted(headers.items()):
        total += 1
        ids = resolve_cap.resolve_cap_ids(
            brand, token, root=workspace_root / brand / "docs" / "product" / "capabilities"
        )
        if ids:
            passing += 1
        else:
            drift += 1
            results.append(
                {
                    "header": token,
                    "status": "orphan_header",
                    "sample_files": files[:3],
                    "drift_reason": f"header `# cap: {token}` no resuelve a ninguna cap (cap_id ni functional_area)",
                }
            )
    return {"total": total, "pass": passing, "drift": drift, "details": results}


def _system_map_live_areas(brand: str, workspace_root: Path) -> list[str]:
    """functional_areas `status:live` que el COCKPIT RENDERIZA (mirror de buildZoneTree).

    Recorre `zones[].boxes` (no `agents[]` crudo): un box string → su agente en `agents[]`;
    un box objeto → sus functional_areas. Así excluye los pseudo-agentes legacy `config`/`infra`
    (NO referenciados por ninguna zona → invisibles en el cockpit), cuyas áreas migraron a las
    cajas v2.0 (acceso/configuracion/observabilidad/…). Sin esto, G2 reportaría 15 áreas
    legacy huérfanas que el cockpit nunca muestra (falso drift).
    """
    sm = _load_system_map(brand, workspace_root)
    if sm is None:
        return []
    agents_by_id = {a.get("id"): a for a in (sm.get("agents") or []) if isinstance(a, dict)}
    live: list[str] = []
    for zone in sm.get("zones") or []:
        for box in zone.get("boxes") or []:
            if isinstance(box, str):  # ref a un agente especialista
                agent = agents_by_id.get(box)
                bid = box
                areas = (agent.get("functional_areas") if agent else []) or []
            elif isinstance(box, dict):
                bid = box.get("id")
                areas = box.get("functional_areas") or []
            else:
                continue
            for area in areas:
                if isinstance(area, dict) and area.get("status") == "live" and bid and area.get("id"):
                    live.append(f"{bid}.{area['id']}")
    return live


def gate_g2_live_area_has_cap(brand: str, workspace_root: Path, caps: dict[str, dict]) -> dict[str, Any]:
    """G2 — toda functional_area `status:live` (que el cockpit renderiza) tiene ≥1 cap
    NON-SUPERSEDED (cualquier status).

    0 caps = FAIL (caza "la caja Inbox vacía en el cockpit"). El umbral es non-superseded
    (cualquier status), NO live: un área con una cap `partial`/`planned` NO está visualmente
    vacía (el cockpit la pinta). El bug origen era 0 caps (el YAML no existía).
    """
    # fa exacta → caps non-superseded (cualquier status). Mismo criterio que el cockpit
    # (capsByFunctionalArea excluye solo superseded_by).
    from collections import defaultdict

    by_fa: dict[str, list[str]] = defaultdict(list)
    for cap_id, cap_data in caps.items():
        if cap_data.get("superseded_by"):
            continue
        fa = cap_data.get("functional_area")
        if fa:
            by_fa[fa].append(cap_id)

    live_areas = _system_map_live_areas(brand, workspace_root)
    results: list[dict] = []
    total = passing = drift = 0
    for area in live_areas:
        total += 1
        if by_fa.get(area):
            passing += 1
        else:
            drift += 1
            results.append(
                {
                    "functional_area": area,
                    "status": "live_area_no_cap",
                    "drift_reason": (
                        f"área live '{area}' en SYSTEM-MAP sin ninguna cap non-superseded (caja vacía en el cockpit)"
                    ),
                }
            )
    return {"total": total, "pass": passing, "drift": drift, "details": results}


def _load_system_map(brand: str, workspace_root: Path) -> dict[str, Any] | None:
    sm_path = workspace_root / brand / "docs" / "architecture" / "SYSTEM-MAP.yaml"
    if not sm_path.exists():
        return None
    try:
        sm = yaml.safe_load(sm_path.read_text(encoding="utf-8"))
        return sm if isinstance(sm, dict) else None
    except yaml.YAMLError:
        return None


# Paths-no (no son archivos en disco): endpoints, rutas Next, comandos, vars.
_NOT_A_PATH = re.compile(r"^\s*(GET|POST|PUT|PATCH|DELETE)\b|/\{|\$\{|^/api/|\s")


def _collect_cap_paths(cap_data: dict) -> list[str]:
    """Extrae paths repo-relativos declarados en un cap (anti-hallucination · G4).

    Conservador: solo strings que parecen archivos del repo (sin espacios, sin
    ${WS}, sin `/{param}`, con extensión de código). Tolera sufijo `::symbol`.
    """
    found: list[str] = []

    def _emit(val: Any) -> None:
        if not isinstance(val, str):
            return
        s = val.split("::", 1)[0].strip()  # db.py::symbol → db.py
        if not s or _NOT_A_PATH.search(s):
            return
        if not s.endswith((".py", ".ts", ".tsx", ".sql", ".yaml", ".yml", ".md")):
            return
        found.append(s)

    def _walk(node: Any) -> None:
        if isinstance(node, str):
            _emit(node)
        elif isinstance(node, list):
            for x in node:
                _walk(x)
        elif isinstance(node, dict):
            for x in node.values():
                _walk(x)

    dp = cap_data.get("dev_preview")
    if isinstance(dp, dict):
        _emit(dp.get("main_component"))
        _emit(dp.get("e2e_test"))
    _walk(cap_data.get("code_pointers"))
    for br in cap_data.get("business_rules") or []:
        if isinstance(br, dict):
            _emit(br.get("code_ref"))
    # dedup preservando orden
    seen: set[str] = set()
    return [p for p in found if not (p in seen or seen.add(p))]


def gate_g3_cap_has_home(brand: str, workspace_root: Path, caps: dict[str, dict]) -> dict[str, Any]:
    """G3 — toda functional_area declarada por un cap mapea a un box.area REAL del SYSTEM-MAP."""
    sm = _load_system_map(brand, workspace_root)
    if sm is None:
        return {"total": 0, "pass": 0, "drift": 0, "details": [], "skipped_reason": "no SYSTEM-MAP"}
    valid_areas = validate_system_map.extract_valid_areas(sm)
    results: list[dict] = []
    total = passing = drift = 0
    for cap_id, cap_data in caps.items():
        fa = cap_data.get("functional_area")
        if not fa:
            continue
        total += 1
        if validate_system_map.is_valid_area(fa, valid_areas):
            passing += 1
        else:
            drift += 1
            results.append(
                {
                    "cap_id": cap_id,
                    "functional_area": fa,
                    "status": "fa_not_in_system_map",
                    "drift_reason": f"functional_area '{fa}' no existe en SYSTEM-MAP (cap sin hogar en el mapa)",
                }
            )
    return {"total": total, "pass": passing, "drift": drift, "details": results}


def gate_g4_paths_exist(brand: str, workspace_root: Path, caps: dict[str, dict]) -> dict[str, Any]:
    """G4 — todos los paths declarados por un cap LIVE/BETA (main_component, e2e_test,
    code_pointers, business_rules.code_ref) existen en disco. Path inventado = FAIL
    (anti-hallucination con dientes).

    Scope live/beta: una cap `deprecated`/`sunset` puede declarar paths cuyo código YA se
    removió, y una `partial`/`planned` paths AÚN no creados — exigirles existencia sería
    falso drift. La claim fuerte "acá vive el código shipped" la hacen las caps live/beta.
    """
    results: list[dict] = []
    total = passing = drift = 0
    for cap_id, cap_data in caps.items():
        if (cap_data.get("status") or "").lower() not in ("live", "beta"):
            continue
        for rel in _collect_cap_paths(cap_data):
            total += 1
            if (workspace_root / rel).exists():
                passing += 1
            else:
                drift += 1
                results.append(
                    {
                        "cap_id": cap_id,
                        "declared_path": rel,
                        "status": "path_missing",
                        "drift_reason": f"path declarado '{rel}' no existe en disco (¿inventado / movido?)",
                    }
                )
    return {"total": total, "pass": passing, "drift": drift, "details": results}


def gate_g5_superseded_valid(brand: str, workspace_root: Path, caps: dict[str, dict]) -> dict[str, Any]:
    """G5 — `superseded_by` (scalar) + `supersedes` (list) referencian caps REALES."""
    caps_root = workspace_root / brand / "docs" / "product" / "capabilities"
    results: list[dict] = []
    total = passing = drift = 0

    def _check(cap_id: str, ref: str, field: str) -> None:
        nonlocal total, passing, drift
        if not ref or not isinstance(ref, str):
            return
        total += 1
        if resolve_cap.resolve_cap_ids(brand, ref, root=caps_root):
            passing += 1
        else:
            drift += 1
            results.append(
                {
                    "cap_id": cap_id,
                    field: ref,
                    "status": "broken_supersession",
                    "drift_reason": f"{field} '{ref}' no resuelve a ninguna cap real (cadena de supersesión rota)",
                }
            )

    for cap_id, cap_data in caps.items():
        _check(cap_id, cap_data.get("superseded_by"), "superseded_by")
        sup = cap_data.get("supersedes")
        if isinstance(sup, list):
            for ref in sup:
                _check(cap_id, ref, "supersedes")
        elif isinstance(sup, str):
            _check(cap_id, sup, "supersedes")
    return {"total": total, "pass": passing, "drift": drift, "details": results}


def gate_g6_map_coverage(brand: str, workspace_root: Path, caps: dict[str, dict]) -> dict[str, Any]:
    """G6 — toda cap LIVE non-superseded tiene functional_area cubierta por una caja del mapa
    (si no, es invisible en el cockpit)."""
    sm = _load_system_map(brand, workspace_root)
    if sm is None:
        return {"total": 0, "pass": 0, "drift": 0, "details": [], "skipped_reason": "no SYSTEM-MAP"}
    valid_areas = validate_system_map.extract_valid_areas(sm)
    results: list[dict] = []
    total = passing = drift = 0
    for cap_id, cap_data in caps.items():
        status = (cap_data.get("status") or "").lower()
        superseded = cap_data.get("superseded_by")
        if status not in ("live", "beta") or superseded:
            continue
        total += 1
        fa = cap_data.get("functional_area")
        if fa and validate_system_map.is_valid_area(fa, valid_areas):
            passing += 1
        else:
            drift += 1
            results.append(
                {
                    "cap_id": cap_id,
                    "functional_area": fa,
                    "status": "live_cap_not_on_map",
                    "drift_reason": (
                        f"cap live '{cap_id}' con functional_area={fa!r} no cubierta por ninguna caja del mapa "
                        "(invisible en el cockpit)"
                    ),
                }
            )
    return {"total": total, "pass": passing, "drift": drift, "details": results}


def gate_g7_cockpit_readable(brand: str, workspace_root: Path) -> dict[str, Any]:
    """G7 — toda cap parsea bajo YAML ESTRICTO (igual que gray-matter/js-yaml del cockpit).

    Claves duplicadas (`map_box`/`last_modified` ×2, etc.) pasan en PyYAML (tolerante)
    pero el cockpit TIRA YAMLException → la cap queda INVISIBLE en el mapa (caja vacía,
    error silencioso · caso 15 caps vitalia 2026-06-05, la caja Inbox entre ellas). Este
    gate hace al validador tan estricto como el consumidor real."""
    caps_root = workspace_root / brand / "docs" / "product" / "capabilities"
    results: list[dict] = []
    total = passing = drift = 0
    if not caps_root.is_dir():
        return {"total": 0, "pass": 0, "drift": 0, "details": []}
    for f in sorted(caps_root.rglob("*.yaml")):
        if f.name.startswith("_") or f.name == "README.md":
            continue
        total += 1
        err = validate_caps_schema.strict_parse_error(f)
        if err is None:
            passing += 1
        else:
            drift += 1
            results.append(
                {
                    "cap_id": f"{f.parent.name}.{f.stem}",
                    "path": str(f.relative_to(workspace_root)),
                    "status": "cockpit_unreadable",
                    "drift_reason": f"el cockpit no puede leer esta cap → invisible en el mapa: {err}",
                }
            )
    return {"total": total, "pass": passing, "drift": drift, "details": results}


def gate_g8_user_visible_has_description(
    brand: str, workspace_root: Path, caps: dict[str, dict]
) -> dict[str, Any]:
    """G8 — toda cap status:live/beta + user_visible:true DEBE tener `user_facing_description`
    (non-placeholder).

    Sin ella el cockpit «✨ Qué puedo hacer» no tiene QUÉ decir y cae a un fallback vacío
    (HB-52/HB-56 · F2 cap-levels). Gate de PRESENCIA forward-looking: 0 violaciones hoy
    (baseline limpio) → bloquea SOLO futuras regresiones (una cap nueva no
    puede ir live+visible sin describir qué hace para el usuario)."""
    results: list[dict] = []
    total = passing = drift = 0
    for cap_id, cap_data in caps.items():
        status = (cap_data.get("status") or "").lower()
        if status not in ("live", "beta") or cap_data.get("superseded_by"):
            continue
        if cap_data.get("user_visible") is not True:
            continue
        total += 1
        ufd = cap_data.get("user_facing_description")
        ok = bool(ufd) and not (isinstance(ufd, str) and ("{" in ufd or not ufd.strip()))
        if ok:
            passing += 1
        else:
            drift += 1
            results.append(
                {
                    "cap_id": cap_id,
                    "status": "user_visible_no_description",
                    "drift_reason": (
                        f"cap live user_visible '{cap_id}' sin user_facing_description "
                        "(el cockpit no puede decir qué hace · «✨ Qué puedo hacer» vacío)"
                    ),
                }
            )
    return {"total": total, "pass": passing, "drift": drift, "details": results}


def gate_g9_user_visible_has_scenario(
    brand: str, workspace_root: Path, caps: dict[str, dict]
) -> dict[str, Any]:
    """G9 — toda cap status:live/beta + user_visible:true DEBE tener ≥1 `scenario` (caso de uso).

    Una cap de valor sin scenarios es una caja sin contenido funcional verificable: «✨ Qué
    puedo hacer» no lista casos de uso y no hay nada que el `cross_check_3` pueda atar a un
    e2e_test (HB-56 · F2 cap-levels). Gate de PRESENCIA forward-looking: 0 violaciones hoy
    (los stubs sin scenarios son deprecated/planned/infra user_visible:false, NO caps de valor
    live). El «≥1 scenario al merge» de new_cap.py deja de ser paper-rule y pasa a mecánico."""
    results: list[dict] = []
    total = passing = drift = 0
    for cap_id, cap_data in caps.items():
        status = (cap_data.get("status") or "").lower()
        if status not in ("live", "beta") or cap_data.get("superseded_by"):
            continue
        if cap_data.get("user_visible") is not True:
            continue
        total += 1
        scenarios = cap_data.get("scenarios")
        if isinstance(scenarios, list) and len(scenarios) >= 1:
            passing += 1
        else:
            drift += 1
            results.append(
                {
                    "cap_id": cap_id,
                    "status": "user_visible_no_scenario",
                    "drift_reason": (
                        f"cap live user_visible '{cap_id}' sin scenarios "
                        "(≥1 caso de uso requerido para una cap de valor · sin él «✨ Qué puedo hacer» queda mudo)"
                    ),
                }
            )
    return {"total": total, "pass": passing, "drift": drift, "details": results}


def gate_g10_stale_forward_decl(brand: str, workspace_root: Path, caps: dict[str, dict]) -> dict[str, Any]:
    """G10 — una `functional_area` con una cap LIVE no debe cargar también una cap
    forward-declared (`planned`/`idea`/`partial`/`wip`) user_visible NON-superseded.

    Caza la "caja fantasma" del cockpit (HB-90): un placeholder forward-declared
    (ej. `offer_studio/medical-services-offer-preset` planned) sobrevive sin
    `superseded_by` cuando la cap real (`offer/lisa-servicios` live) shippea en la
    MISMA área → el cockpit pinta 2 cajas. FLAG-only (no auto-drop: decidir
    superseded vs dropped es juicio de `/pm-{brand}`, no de un gate determinístico).
    """
    from collections import defaultdict

    by_fa: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for cap_id, cap_data in caps.items():
        if cap_data.get("superseded_by") or cap_data.get("user_visible") is not True:
            continue
        fa = cap_data.get("functional_area")
        if fa:
            by_fa[fa].append((cap_id, (cap_data.get("status") or "").lower()))

    pre_decl = {"planned", "idea", "partial", "wip"}
    live = {"live", "beta"}
    results: list[dict] = []
    total = passing = drift = 0
    for fa, members in by_fa.items():
        if not any(status in live for _, status in members):
            continue
        total += 1
        stale = [cid for cid, status in members if status in pre_decl]
        if stale:
            for cid in stale:
                drift += 1
                results.append(
                    {
                        "cap_id": cid,
                        "functional_area": fa,
                        "status": "stale_forward_decl",
                        "drift_reason": (
                            f"cap forward-declared '{cid}' sigue activa mientras una cap live cubre "
                            f"'{fa}' → marcá superseded_by + status dropped/superseded (caja fantasma en el cockpit)"
                        ),
                    }
                )
        else:
            passing += 1
    return {"total": total, "pass": passing, "drift": drift, "details": results}


def run_cap_gates(brand: str, workspace_root: Path, caps: dict[str, dict]) -> dict[str, dict[str, Any]]:
    """Dispatcher de los gates G1-G10 (HB-51 G1-G7 + F2 cap-levels G8/G9 + HB-90 G10).
    Devuelve {gate_id: result}. Registro OCP: CHECK 11 (machinery) auto-cubre G10+."""
    return {
        "G1": gate_g1_header_resolves(brand, workspace_root),
        "G2": gate_g2_live_area_has_cap(brand, workspace_root, caps),
        "G3": gate_g3_cap_has_home(brand, workspace_root, caps),
        "G4": gate_g4_paths_exist(brand, workspace_root, caps),
        "G5": gate_g5_superseded_valid(brand, workspace_root, caps),
        "G6": gate_g6_map_coverage(brand, workspace_root, caps),
        "G7": gate_g7_cockpit_readable(brand, workspace_root),
        "G8": gate_g8_user_visible_has_description(brand, workspace_root, caps),
        "G9": gate_g9_user_visible_has_scenario(brand, workspace_root, caps),
        "G10": gate_g10_stale_forward_decl(brand, workspace_root, caps),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Bidirectional code↔cap validator (cement 2026-05-28)")
    parser.add_argument("--brand", required=True)
    parser.add_argument("--out", default=None)
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if any HARD cross-check has drift > 0",
    )
    parser.add_argument("--repo", default=None)
    parser.add_argument(
        "--cap-gates-hard",
        action="store_true",
        help="HB-51: incluir gates G1-G6 (cap-format) en el set HARD (exit 1 si drift). "
        "ADVISORY por default hasta el backfill (slice 8).",
    )
    args = parser.parse_args()

    if args.repo:
        workspace_root = Path(args.repo).resolve()
    else:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
            workspace_root = Path(result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError):
            workspace_root = Path.cwd()

    out_path = (
        Path(args.out).resolve()
        if args.out
        else workspace_root / args.brand / "docs" / "product" / "capabilities" / "_bidirectional-validation.json"
    )

    # HARD set: cross_check_3 (scenario→e2e_test) always hard.
    # cross_check_4 (access roles ↔ @require_phi_access) is ADVISORY for now —
    # Fase 5 lo flipea a HARD para vitalia DESPUÉS de resolver el drift de acceso
    # existente (no se prende un gate HARD con fallas conocidas). Ver
    # docs/process/lifecycle.md § roadmap Fase 5.
    hard_set = {3}

    if args.verbose:
        print(f"Workspace : {workspace_root}")
        print(f"Brand     : {args.brand}")
        print(f"Hard      : {sorted(hard_set)}")
        print()

    caps = load_capabilities(args.brand, workspace_root)
    print(f"Loaded {len(caps)} caps from {args.brand}")

    print("Running cross-check 3 (scenarios e2e_test paths)...")
    cc3 = cross_check_3(caps, workspace_root)
    print(f"  total={cc3['total']} pass={cc3['pass']} drift={cc3['drift']}")

    print("Running cross-check 4 (access roles ↔ decorators)...")
    cc4 = cross_check_4(caps, workspace_root, args.brand)
    print(f"  total={cc4['total']} pass={cc4['pass']} drift={cc4['drift']}")

    # ── HB-51 · cap-format gates G1-G6 (resolver-backed) ────────────────────
    # Limpia el cache del resolver para reflejar caps recién staged/modificadas.
    resolve_cap.clear_resolver_cache()
    print("Running cap-format gates G1-G9 (HB-51 + F2 cap-levels)...")
    cap_gates = run_cap_gates(args.brand, workspace_root, caps)
    for gid in sorted(cap_gates):
        g = cap_gates[gid]
        print(f"  {gid}: total={g['total']} pass={g['pass']} drift={g['drift']}")
    cap_gate_drift = sum(g["drift"] for g in cap_gates.values())

    # G10 (HB-90 · caja fantasma forward-declared) es ADVISORY hasta el backfill
    # cross-brand de placeholders forward-declared — mismo principio "no se prende
    # un gate HARD con fallas conocidas" (ver hard_set/cc4 arriba). Cuenta para el
    # reporte (cap-doctor + SOFT_DRIFT) pero NO para el hard-fail del pre-push.
    ADVISORY_GATES = {"G10"}
    hard_cap_gate_drift = sum(g["drift"] for gid, g in cap_gates.items() if gid not in ADVISORY_GATES)

    drift_total = cc3["drift"] + cc4["drift"] + cap_gate_drift
    hard_drift = sum(cc["drift"] for i, cc in [(3, cc3), (4, cc4)] if i in hard_set)
    if args.cap_gates_hard:
        hard_drift += hard_cap_gate_drift

    verdict = "CLEAN" if drift_total == 0 else ("HARD_FAIL" if hard_drift > 0 else "SOFT_DRIFT")

    now_iso = datetime.now(tz=timezone.utc).astimezone().isoformat(timespec="seconds")
    output: dict[str, Any] = {
        "validated_at": now_iso,
        "brand": args.brand,
        "schema_version": "v5",
        "hard_checks": sorted(hard_set),
        "cap_gates_hard": bool(args.cap_gates_hard),
        "cross_check_3": cc3,
        "cross_check_4": cc4,
        "cap_gates": cap_gates,
        "summary": {
            "total_caps": len(caps),
            "drift_total": drift_total,
            "cap_gate_drift": cap_gate_drift,
            "drift_in_hard": hard_drift,
            "verdict": verdict,
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print(f"\nVerdict: {verdict}")
    print(f"Drift total: {drift_total} · cap-gate drift: {cap_gate_drift} · in HARD checks: {hard_drift}")
    print(f"Saved to: {out_path}")

    if args.strict and hard_drift > 0:
        print(f"[STRICT] {hard_drift} drift in HARD checks", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
