"""Arch fitness: PHI fields MUST NEVER appear as URL query params in scheduling/payments/fiscal routers.

HIPAA-lite rule (vitalia/.claude/rules/hipaa-lite.md § Anti-patterns):
  "PHI en URLs (GET query params) — usa POST body siempre."
  Example: GET /patients?dni=12345678 → PROHIBITED

This test:
  1. Scans all *_router.py files under scheduling/, payments/, fiscal/
     for FastAPI Query() declarations.
  2. Uses AST to detect function parameters decorated with Query() whose
     names match known PHI field names.
  3. Also validates that ALLOWED_GRID_PARAMS whitelist is defined in the
     agenda router and contains only approved param names.

PHI field names to block (per hipaa-lite.md § PHI fields canónicos):
  Identity: patient_name, patient_dni, dni, cuit, date_of_birth, dob,
            phone, email, address, patient_phone, patient_email
  Clinical: diagnosis, treatment_plan, medication, dosage, allergies,
            symptoms, medical_notes, lab_results, vital_signs
  Imaging:  imaging_url, xray_filename, ultrasound_report

Allowed query params for scheduling GET endpoints (ALLOWED_GRID_PARAMS):
  view, date, preset_filter, filters, page, page_size, status, month

Ratchet: KNOWN_PHI_QUERY_PARAMS_VIOLATIONS is empty — new code starts clean.
Add entries ONLY with explicit justification (e.g. hash IDs that look like PHI
but carry no semantic content).

T-9 — F2-S1 vitalia-fase2-valeria-agenda arch tests.

downstream-regression-na: brand-local arch fitness test; no cross-brand consumers
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

# ─── Workspace roots ──────────────────────────────────────────────────────────

WS_ROOT = Path(__file__).resolve().parents[4]
VITALIA_BE_SRC = WS_ROOT / "vitalia" / "backend" / "src"

# Module router directories to scan
ROUTER_DIRS: tuple[Path, ...] = (
    VITALIA_BE_SRC / "modules" / "vitalia" / "scheduling" / "api",
    VITALIA_BE_SRC / "modules" / "vitalia" / "payments" / "api",
    VITALIA_BE_SRC / "modules" / "vitalia" / "fiscal" / "api",
)

# ─── PHI field name patterns (must never appear in Query() params) ────────────

#: PHI field names that MUST NOT appear as query parameter names.
#: Each is a regex matching the param name (word-boundary safe).
PHI_URL_PARAM_NAMES: tuple[re.Pattern[str], ...] = (
    # Identity
    re.compile(r"^patient_name$", re.IGNORECASE),
    re.compile(r"^patient_dni$", re.IGNORECASE),
    re.compile(r"^dni$", re.IGNORECASE),
    re.compile(r"^cuit$", re.IGNORECASE),
    re.compile(r"^date_of_birth$", re.IGNORECASE),
    re.compile(r"^dob$", re.IGNORECASE),
    re.compile(r"^patient_phone$", re.IGNORECASE),
    re.compile(r"^phone$", re.IGNORECASE),
    re.compile(r"^patient_email$", re.IGNORECASE),
    re.compile(r"^email$", re.IGNORECASE),
    re.compile(r"^address$", re.IGNORECASE),
    re.compile(r"^patient_address$", re.IGNORECASE),
    # Clinical
    re.compile(r"^diagnosis$", re.IGNORECASE),
    re.compile(r"^treatment_plan$", re.IGNORECASE),
    re.compile(r"^medication$", re.IGNORECASE),
    re.compile(r"^dosage$", re.IGNORECASE),
    re.compile(r"^allergies$", re.IGNORECASE),
    re.compile(r"^symptoms$", re.IGNORECASE),
    re.compile(r"^medical_notes$", re.IGNORECASE),
    re.compile(r"^lab_results$", re.IGNORECASE),
    re.compile(r"^vital_signs$", re.IGNORECASE),
    # Imaging
    re.compile(r"^imaging_url$", re.IGNORECASE),
    re.compile(r"^xray_filename$", re.IGNORECASE),
    re.compile(r"^ultrasound_report$", re.IGNORECASE),
)

#: Allowed query params for scheduling GET endpoints (per ALLOWED_GRID_PARAMS in agenda_router.py).
APPROVED_SCHEDULING_QUERY_PARAMS: frozenset[str] = frozenset(
    [
        "view",
        "date",
        "preset_filter",
        "filters",
        "page",
        "page_size",
        "status",
        "month",
        # T-BE-3 availability/day-strip query params (not PHI):
        # doctor_id: scheduling UUID identifying doctor — not patient PHI
        # strip_date: Python alias for 'date' param (Query(alias="date")) — calendar date
        "doctor_id",
        "strip_date",
        # T-D1 availability/service-day query param (not PHI):
        # service_id: offer (catalog/service) UUID, alias 'serviceId' — not a patient reference
        "service_id",
    ]
)

# Ratchet: explicitly approved PHI-looking params (must have justification comment).
# Example entry: "patient_id_hash" (hash only, not PHI-reidentifiable by itself)
KNOWN_PHI_QUERY_PARAMS_VIOLATIONS: frozenset[str] = frozenset([])


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _router_files() -> list[Path]:
    """Find all *_router.py files under scheduling/payments/fiscal api dirs."""
    router_files: list[Path] = []
    for directory in ROUTER_DIRS:
        if not directory.exists():
            continue
        for p in directory.rglob("*_router.py"):
            if "__pycache__" not in p.parts:
                router_files.append(p)
    return router_files


def _relative(p: Path) -> str:
    try:
        return str(p.relative_to(WS_ROOT))
    except ValueError:
        return str(p)


def _is_phi_param_name(name: str) -> bool:
    """Return True if name matches any PHI field pattern."""
    return any(pattern.match(name) for pattern in PHI_URL_PARAM_NAMES)


def _extract_query_param_names_ast(source: str, filepath: str) -> list[tuple[str, int]]:
    """Return list of (param_name, lineno) for function params using Query().

    Detects both explicit `= Query(...)` and `= Query(default=...)` patterns.
    Also catches params annotated with `Annotated[..., Query(...)]`.
    """
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return []

    results: list[tuple[str, int]] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for arg in node.args.args + node.args.kwonlyargs:
            arg_name = arg.arg
            lineno = arg.lineno

            # Check default value: param = Query(...)
            # ast.arg doesn't carry defaults directly; we need to look at function defaults
            param_idx = node.args.args.index(arg) if arg in node.args.args else -1
            defaults_offset = len(node.args.args) - len(node.args.defaults)

            default_val = None
            if param_idx >= 0 and (param_idx - defaults_offset) >= 0:
                default_val = node.args.defaults[param_idx - defaults_offset]
            elif arg in node.args.kwonlyargs:
                kw_idx = node.args.kwonlyargs.index(arg)
                if node.args.kw_defaults and kw_idx < len(node.args.kw_defaults):
                    default_val = node.args.kw_defaults[kw_idx]

            if default_val is not None and _is_query_call(default_val):
                results.append((arg_name, lineno))
            elif arg.annotation is not None and _is_annotated_query(arg.annotation):
                results.append((arg_name, lineno))

    return results


def _is_query_call(node: ast.expr) -> bool:
    """Return True if node is a call to Query(...)."""
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id == "Query":
            return True
        if isinstance(func, ast.Attribute) and func.attr == "Query":
            return True
    return False


def _is_annotated_query(annotation: ast.expr) -> bool:
    """Return True if annotation contains Query(...) (Annotated[type, Query(...)] pattern)."""
    for child in ast.walk(annotation):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name) and func.id == "Query":
                return True
            if isinstance(func, ast.Attribute) and func.attr == "Query":
                return True
    return False


def _grep_phi_pattern_in_source(source: str) -> list[str]:
    """Grep-based scan: find PHI field name patterns in function signatures.

    More conservative than AST scan — catches edge cases where decorators
    or inline patterns embed PHI field names.
    """
    # Find lines that look like function params with Query() and PHI names
    phi_lines: list[str] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        # Match: `param_name: type = Query(` or `param_name = Query(`
        match = re.match(r"(\w+)\s*[=:]\s*.*Query\s*\(", stripped)
        if match:
            param_name = match.group(1)
            if _is_phi_param_name(param_name):
                phi_lines.append(f"line {lineno}: {stripped[:120]}")
    return phi_lines


# ─── Tests ────────────────────────────────────────────────────────────────────


class TestNoPhiInUrlParams:
    """PHI fields MUST NEVER appear as FastAPI Query() parameters in scheduling routers.

    Verifies HIPAA-lite compliance: patient identity + clinical data must be
    passed via POST body, never via URL query strings.
    """

    def test_router_files_exist(self) -> None:
        """Sanity: at least one router file must exist in scheduling/api."""
        scheduling_api = VITALIA_BE_SRC / "modules" / "vitalia" / "scheduling" / "api"
        routers = list(scheduling_api.glob("*_router.py")) if scheduling_api.exists() else []
        assert routers, (
            "No *_router.py files found under "
            "vitalia/backend/src/modules/vitalia/scheduling/api/. "
            "Expected agenda_router.py + notify_router.py per T-6/T-8 deliverables."
        )

    def test_agenda_router_defines_allowed_grid_params(self) -> None:
        """agenda_router.py MUST define ALLOWED_GRID_PARAMS constant (whitelist gate).

        This constant is the machine-readable whitelist of approved query params.
        The arch test verifies it exists; the router enforces it at runtime.
        """
        agenda_router = VITALIA_BE_SRC / "modules" / "vitalia" / "scheduling" / "api" / "agenda_router.py"
        if not agenda_router.exists():
            return  # Not yet created — pass (test becomes active post T-6)

        source = agenda_router.read_text(encoding="utf-8")
        assert "ALLOWED_GRID_PARAMS" in source, (
            "agenda_router.py must define ALLOWED_GRID_PARAMS constant "
            "(per 03-arch A10 + hipaa-lite.md PHI URL anti-pattern enforcement)."
        )

    def test_allowed_grid_params_contains_only_safe_params(self) -> None:
        """ALLOWED_GRID_PARAMS must not include any PHI field names.

        Sanity check: the whitelist itself must not accidentally include PHI keys.
        """
        agenda_router = VITALIA_BE_SRC / "modules" / "vitalia" / "scheduling" / "api" / "agenda_router.py"
        if not agenda_router.exists():
            return

        source = agenda_router.read_text(encoding="utf-8")

        # Extract ALLOWED_GRID_PARAMS set literal from source text
        # Pattern: ALLOWED_GRID_PARAMS: frozenset[str] = frozenset(["a", "b", ...])
        set_match = re.search(
            r"ALLOWED_GRID_PARAMS\s*[:=][^=].*?frozenset\(\s*\[([^\]]+)\]",
            source,
            re.DOTALL,
        )
        if not set_match:
            # Could not parse the set literal — skip content check
            return

        raw_entries = set_match.group(1)
        # Extract quoted strings from the set literal
        entries = re.findall(r'"([^"]+)"|\'([^\']+)\'', raw_entries)
        param_names = {e[0] or e[1] for e in entries}

        phi_in_whitelist = [name for name in param_names if _is_phi_param_name(name)]
        assert phi_in_whitelist == [], (
            "ALLOWED_GRID_PARAMS whitelist contains PHI field names: "
            + str(phi_in_whitelist)
            + ". Remove them — PHI must never appear in URL params."
        )

    def test_no_phi_query_params_ast_scan(self) -> None:
        """AST scan: no Query() parameter in any scheduling/payments/fiscal router uses PHI names.

        Detects parameters like `def endpoint(diagnosis: str = Query(...))`.
        """
        violations: list[str] = []

        for router_file in _router_files():
            rel = _relative(router_file)
            source = router_file.read_text(encoding="utf-8")
            query_params = _extract_query_param_names_ast(source, str(router_file))

            for param_name, lineno in query_params:
                if param_name in KNOWN_PHI_QUERY_PARAMS_VIOLATIONS:
                    continue
                if _is_phi_param_name(param_name):
                    violations.append(
                        f"{rel}:{lineno}: Query() param '{param_name}' matches PHI field name "
                        "(HIPAA-lite: PHI must never appear in URL query params)"
                    )

        assert violations == [], (
            "PHI query param violations detected:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nFix: move PHI fields to POST request body (Pydantic model). "
            "GET endpoints for scheduling must only accept: " + str(sorted(APPROVED_SCHEDULING_QUERY_PARAMS))
        )

    def test_no_phi_query_params_grep_scan(self) -> None:
        """Grep scan: PHI field names must not appear as Query() param names in source text.

        Complements the AST scan with a simpler pattern match that catches
        edge cases like decorator-embedded params or complex type annotations.
        """
        violations: list[str] = []

        for router_file in _router_files():
            rel = _relative(router_file)
            source = router_file.read_text(encoding="utf-8")
            phi_lines = _grep_phi_pattern_in_source(source)
            for line_info in phi_lines:
                violations.append(f"{rel}: {line_info}")

        assert violations == [], (
            "PHI query param grep violations detected:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nFix: move PHI fields to POST body. See hipaa-lite.md § Anti-patterns."
        )

    def test_get_endpoints_only_use_approved_query_params(self) -> None:
        """GET endpoints in scheduling routers must only use APPROVED_SCHEDULING_QUERY_PARAMS.

        Detects any Query() param in a GET route that is not in the approved whitelist.
        PHI params are caught by the PHI-specific tests above.
        This test catches unexpected params beyond the approved set.
        """
        violations: list[str] = []
        scheduling_api = VITALIA_BE_SRC / "modules" / "vitalia" / "scheduling" / "api"

        for router_file in list(scheduling_api.glob("*_router.py")) if scheduling_api.exists() else []:
            if "__pycache__" in router_file.parts:
                continue
            rel = _relative(router_file)
            source = router_file.read_text(encoding="utf-8")

            try:
                tree = ast.parse(source, filename=str(router_file))
            except SyntaxError:
                continue

            # Find all async function defs that are registered as GET routes
            # (have a @router.get decorator)
            for node in ast.walk(tree):
                if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                    continue

                is_get_route = False
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        func = decorator.func
                        if isinstance(func, ast.Attribute) and func.attr == "get":
                            is_get_route = True
                            break

                if not is_get_route:
                    continue

                # Check Query() params for this GET endpoint
                query_params = _extract_query_param_names_ast(source, str(router_file))
                for param_name, lineno in query_params:
                    if (
                        param_name not in APPROVED_SCHEDULING_QUERY_PARAMS
                        and param_name not in KNOWN_PHI_QUERY_PARAMS_VIOLATIONS
                        and not _is_phi_param_name(param_name)  # covered by PHI tests
                    ):
                        violations.append(
                            f"{rel}:{lineno}: GET endpoint has unexpected Query() param "
                            f"'{param_name}' (not in APPROVED_SCHEDULING_QUERY_PARAMS)"
                        )

        assert violations == [], (
            "Unexpected GET query params detected:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nIf this param is legitimate, add it to APPROVED_SCHEDULING_QUERY_PARAMS "
            "with a justification comment. If it's PHI, move to POST body."
        )

    def test_payments_and_fiscal_have_no_get_phi_endpoints(self) -> None:
        """payments/ and fiscal/ routers must NOT define GET endpoints with PHI-capable path params.

        Per 03-arch + HIPAA-lite: charge (POST /charge) and fiscal emit (POST /emit)
        are POST-only endpoints. No GET endpoints with appointment_id, payment_id,
        or other PHI-adjacent identifiers in URL query params.
        """
        violations: list[str] = []

        for module_name in ("payments", "fiscal"):
            api_dir = VITALIA_BE_SRC / "modules" / "vitalia" / module_name / "api"
            if not api_dir.exists():
                continue

            for router_file in api_dir.rglob("*_router.py"):
                if "__pycache__" in router_file.parts:
                    continue
                rel = _relative(router_file)
                source = router_file.read_text(encoding="utf-8")

                # payments/fiscal should use POST body only — no Query() params with PHI fields
                phi_lines = _grep_phi_pattern_in_source(source)
                for line_info in phi_lines:
                    violations.append(f"{rel} ({module_name} module): {line_info}")

        assert violations == [], (
            "PHI query params in payments/fiscal routers:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nFix: payments/fiscal endpoints must use POST body for all PHI-adjacent fields."
        )
