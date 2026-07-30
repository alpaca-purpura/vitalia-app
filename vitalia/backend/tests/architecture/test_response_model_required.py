"""Architecture fitness: every FastAPI route decorator MUST include response_model=.

Per 03-arch-be.md § 10 + vitalia/.claude/rules/hipaa-lite.md § Access control:
  `response_model=` is MANDATORY on every route (PII allowlist enforcement).
  Routes without response_model= risk leaking PHI fields beyond the intended
  API contract — especially critical for a HIPAA-lite compliant brand.

Scans all *_router.py and *routes*.py files under vitalia/backend/src/ using
AST analysis of route decorator arguments.

Known-violations allowlist follows ratchet pattern (shrink-only).

downstream-regression-na: brand-local arch fitness test; no cross-brand consumers
"""

from __future__ import annotations

import ast
from pathlib import Path

WS_ROOT = Path(__file__).resolve().parents[4]
VITALIA_SRC = WS_ROOT / "vitalia" / "backend" / "src"

# HTTP method decorators that require response_model=
ROUTE_DECORATOR_ATTRS: frozenset[str] = frozenset(["get", "post", "put", "patch", "delete", "head", "options"])

# Routes that are legitimately exempt from response_model=
# Format: "relative/path/to/file.py::function_name"
# Allowed exceptions:
#   - StreamingResponse endpoints (binary content like PDF)
#   - Response endpoints returning file downloads
#   - Routes that return raw Response objects (e.g., health check)
KNOWN_RESPONSE_MODEL_EXEMPT: frozenset[str] = frozenset(
    [
        # Example: "src/modules/vitalia/api/routes.py::get_receipt_pdf"
        # Add exemptions with justification in commit message.
    ]
)

# Files to SKIP entirely (not vitalia route files, or test fixtures)
SKIP_FILE_SUFFIXES: tuple[str, ...] = ("conftest.py", "__init__.py")


def _route_files() -> list[Path]:
    """Find all potential route files under vitalia/backend/src/."""
    if not VITALIA_SRC.exists():
        return []

    candidates: list[Path] = []
    for p in VITALIA_SRC.rglob("*.py"):
        name = p.name
        if any(name.endswith(s) for s in SKIP_FILE_SUFFIXES):
            continue
        # Include files named *router*.py or *routes*.py
        if "router" in name or "route" in name:
            candidates.append(p)
    return candidates


def _relative(p: Path) -> str:
    return str(p.relative_to(WS_ROOT))


def _is_route_decorator(decorator: ast.expr) -> bool:
    """Return True if a decorator is a router HTTP method call."""
    # Pattern: @router.get(...), @router.post(...), etc.
    if isinstance(decorator, ast.Call):
        func = decorator.func
        if isinstance(func, ast.Attribute):
            return func.attr in ROUTE_DECORATOR_ATTRS
    return False


def _has_response_model_kwarg(decorator: ast.Call) -> bool:
    """Return True if the decorator call includes response_model= keyword argument."""
    for kw in decorator.keywords:
        if kw.arg == "response_model":
            return True
    return False


def _is_streaming_response_return(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Heuristic: function annotated with StreamingResponse or Response return type.

    These are legitimately exempt because response_model= doesn't apply to
    streaming/binary responses. We check the return annotation.
    """
    annotation = func_node.returns
    if annotation is None:
        return False

    annotation_str = ast.unparse(annotation) if hasattr(ast, "unparse") else ""
    # FastAPI StreamingResponse, Response, FileResponse don't use response_model
    streaming_types = {"StreamingResponse", "Response", "FileResponse"}
    return any(t in annotation_str for t in streaming_types)


class TestResponseModelRequired:
    """All FastAPI route decorators must declare response_model= (PII defense)."""

    def test_route_files_exist(self) -> None:
        """Sanity: at least one route file must exist."""
        files = _route_files()
        assert len(files) >= 1, (
            "No router/routes files found under vitalia/backend/src/. "
            "Expected at least one routes.py or router.py per 03-arch-be.md."
        )

    def test_all_routes_declare_response_model(self) -> None:
        """Every @router.get/post/patch/delete must have response_model= kwarg.

        HIPAA-lite: response_model= is the PII allowlist enforcement gate.
        Without it, PHI fields may leak in responses to unpermitted roles.

        Exemptions (streaming/binary responses) can be added to
        KNOWN_RESPONSE_MODEL_EXEMPT.
        """
        violations: list[str] = []

        for route_file in _route_files():
            source = route_file.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(route_file))
            except SyntaxError:
                continue  # Caught by ruff lint gate

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue

                func_name = node.name
                rel_file = _relative(route_file)
                exempt_key = f"{rel_file}::{func_name}"

                if exempt_key in KNOWN_RESPONSE_MODEL_EXEMPT:
                    continue

                # Check if function has a streaming return annotation (heuristic exempt)
                if _is_streaming_response_return(node):
                    continue

                for decorator in node.decorator_list:
                    if not _is_route_decorator(decorator):
                        continue

                    if not isinstance(decorator, ast.Call):
                        continue

                    if not _has_response_model_kwarg(decorator):
                        method = decorator.func.attr if isinstance(decorator.func, ast.Attribute) else "?"  # type: ignore[union-attr]
                        violations.append(
                            f"{rel_file}:{node.lineno}: "
                            f"@router.{method}(...) on `{func_name}` "
                            f"is missing response_model= kwarg"
                        )

        assert violations == [], (
            "FastAPI routes missing response_model= detected.\n"
            "response_model= is MANDATORY (PII allowlist per hipaa-lite.md + "
            "03-arch-be.md § 10 + .tessl/tiles/maria/fastapi/rules/pii-sanitisation.md).\n\n"
            + "\n".join(violations)
            + "\n\nFix: add `response_model=YourResponseDTO` to each route decorator.\n"
            "If the route returns a StreamingResponse/FileResponse (binary), "
            "add to KNOWN_RESPONSE_MODEL_EXEMPT with justification."
        )

    def test_route_files_use_async_def(self) -> None:
        """Route handler functions must be declared as async def.

        Sync route handlers block the FastAPI event loop. All vitalia routes
        must be async per 03-arch-be.md § 10 + backend-ddd.md.
        """
        violations: list[str] = []
        _sync_exempt: frozenset[str] = frozenset([])  # Shrink-only baseline

        for route_file in _route_files():
            source = route_file.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(route_file))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef):
                    continue  # Only care about sync defs

                # Skip private helpers and non-route functions
                if node.name.startswith("_"):
                    continue

                rel_file = _relative(route_file)
                exempt_key = f"{rel_file}::{node.name}"
                if exempt_key in _sync_exempt:
                    continue

                # Check if any decorator is a route decorator
                has_route_decorator = any(_is_route_decorator(dec) for dec in node.decorator_list)
                if has_route_decorator:
                    violations.append(
                        f"{rel_file}:{node.lineno}: `{node.name}` is a sync `def` route handler — must be `async def`"
                    )

        assert violations == [], (
            "Sync route handlers detected:\n" + "\n".join(violations) + "\n\nAll route handlers must be `async def` "
            "(per 03-arch-be.md § 10 'Async-first')."
        )
