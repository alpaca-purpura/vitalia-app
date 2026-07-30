"""Arch fitness: DDD purity for vitalia scheduling/payments/fiscal modules.

Verifies Inside-Out layering (domain → infrastructure → application → api):
  1. domain/ — pure Python, NO framework imports (fastapi, sqlalchemy, pydantic).
     Only Python stdlib + siblings within domain/ are allowed.
  2. infrastructure/ — MUST NOT import from api/ or application/services/.
     (May import domain/ — that is the Inside-Out contract.)
  3. application/ports/ — interfaces must be ABCs (abstract base classes),
     not concrete implementations.
  4. api/ — MUST NOT import domain/ directly; must pass through application
     services (thin router contract).

Ratchet pattern: KNOWN_VIOLATIONS lists are empty (new modules start clean).
Add entries ONLY with justified commit message.

T-9 — F2-S1 vitalia-fase2-valeria-agenda arch tests.

downstream-regression-na: brand-local arch fitness test; no cross-brand consumers
"""

from __future__ import annotations

import re
from pathlib import Path

# ─── Workspace roots ──────────────────────────────────────────────────────────

WS_ROOT = Path(__file__).resolve().parents[4]
VITALIA_BE_SRC = WS_ROOT / "vitalia" / "backend" / "src"

# Module roots under vitalia BE src
SCHEDULING_ROOT = VITALIA_BE_SRC / "modules" / "vitalia" / "scheduling"
PAYMENTS_ROOT = VITALIA_BE_SRC / "modules" / "vitalia" / "payments"
FISCAL_ROOT = VITALIA_BE_SRC / "modules" / "vitalia" / "fiscal"

MODULE_ROOTS: tuple[Path, ...] = (SCHEDULING_ROOT, PAYMENTS_ROOT, FISCAL_ROOT)

# ─── Framework imports that MUST NOT appear in domain/ ────────────────────────

#: Patterns that indicate a framework import (forbidden in domain/).
#: Each tuple: (pattern, description)
FRAMEWORK_IMPORT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^\s*(import|from)\s+fastapi", re.MULTILINE), "fastapi"),
    (re.compile(r"^\s*(import|from)\s+sqlalchemy", re.MULTILINE), "sqlalchemy"),
    # Pydantic v2 in domain/ is allowed ONLY for pure value objects with no SQLAlchemy deps.
    # Arch decision: domain entities use @dataclass (frozen=True) exclusively in F2-S1.
    # If a future domain entity requires Pydantic, add it to KNOWN_DOMAIN_PYDANTIC_FILES.
    (re.compile(r"^\s*(import|from)\s+pydantic", re.MULTILINE), "pydantic"),
    (re.compile(r"^\s*(import|from)\s+starlette", re.MULTILINE), "starlette"),
    (re.compile(r"^\s*(import|from)\s+uvicorn", re.MULTILINE), "uvicorn"),
    (re.compile(r"^\s*(import|from)\s+aiohttp", re.MULTILINE), "aiohttp"),
    (re.compile(r"^\s*(import|from)\s+httpx", re.MULTILINE), "httpx"),
)

# Ratchet: domain files allowed to use Pydantic (e.g. pure value objects where Pydantic adds validation).
# Start clean — populate only with justified commit message.
KNOWN_DOMAIN_PYDANTIC_FILES: frozenset[str] = frozenset([])

# ─── infrastructure/ import allowlist ────────────────────────────────────────

#: Patterns that indicate api/ or application/services/ imports (forbidden in infra/).
INFRA_FORBIDDEN_IMPORT_PATTERNS: tuple[re.Pattern[str], ...] = (
    # No direct import of api/ sub-paths from infra/
    re.compile(r"from\s+src\.modules\.vitalia\.\w+\.api\b"),
    re.compile(r"import\s+src\.modules\.vitalia\.\w+\.api\b"),
    # No import of application/services/ from infra/ (services depend on infra, not vice versa)
    re.compile(r"from\s+src\.modules\.vitalia\.\w+\.application\.services"),
    re.compile(r"import\s+src\.modules\.vitalia\.\w+\.application\.services"),
)

# Ratchet: infra files legitimately importing api/ or services/ (should be zero).
KNOWN_INFRA_FORWARD_IMPORTS: frozenset[str] = frozenset([])

# ─── api/ direct domain import patterns (forbidden — must go through application) ──

#: Pattern for api/ files importing domain/ directly (bypasses application layer).
API_DIRECT_DOMAIN_IMPORT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"from\s+src\.modules\.vitalia\.\w+\.domain\b"),
    re.compile(r"import\s+src\.modules\.vitalia\.\w+\.domain\b"),
)

# Exceptions for api/ domain imports:
# API layer may import domain exceptions (for HTTPException mapping — thin router pattern).
# May also import domain enums used in Pydantic DTOs declared in api/dtos/.
# These are explicit allowlisted patterns (not file-level exceptions).
API_DOMAIN_IMPORT_ALLOWED_SUBMODULES: tuple[re.Pattern[str], ...] = (
    # domain/exceptions is OK to import in api/ (for HTTPException mapping)
    re.compile(r"from\s+src\.modules\.vitalia\.\w+\.domain\.exceptions"),
    # domain enum files used by DTO field validation
    re.compile(
        r"from\s+src\.modules\.vitalia\.\w+\.domain\.[a-z_]+(enum|enums|status|origin|method|type|view|filter|slot)"
    ),
)

# Ratchet: api/ files legitimately importing non-exception domain paths.
KNOWN_API_DIRECT_DOMAIN_IMPORTS: frozenset[str] = frozenset([])


# ─── Helper utilities ─────────────────────────────────────────────────────────


def _python_files_in(directory: Path) -> list[Path]:
    """Return all .py files under directory, excluding __pycache__."""
    if not directory.exists():
        return []
    return [p for p in directory.rglob("*.py") if "__pycache__" not in p.parts and p.name != "__init__.py"]


def _relative(p: Path) -> str:
    """Return path relative to WS_ROOT for readable test output."""
    try:
        return str(p.relative_to(WS_ROOT))
    except ValueError:
        return str(p)


# ─── Test classes ──────────────────────────────────────────────────────────────


class TestSchedulingModuleDddPurity:
    """DDD Inside-Out layering for vitalia scheduling/payments/fiscal modules.

    All three modules share the same DDD invariants:
      domain → infrastructure → application → api
    """

    def test_module_dirs_exist(self) -> None:
        """At least one of scheduling/payments/fiscal must exist (sanity gate)."""
        existing = [m for m in MODULE_ROOTS if m.exists()]
        assert existing, (
            "None of the expected module directories exist under "
            "vitalia/backend/src/modules/vitalia/. "
            "Expected: scheduling/, payments/, fiscal/"
        )

    def test_domain_has_no_framework_imports(self) -> None:
        """domain/ MUST NOT import fastapi, sqlalchemy, pydantic, starlette, httpx.

        Domain layer is pure Python — framework-agnostic. Only stdlib + domain siblings allowed.
        Violations indicate framework leakage into domain objects.
        """
        violations: list[str] = []

        for module_root in MODULE_ROOTS:
            domain_dir = module_root / "domain"
            for py_file in _python_files_in(domain_dir):
                rel = _relative(py_file)
                source = py_file.read_text(encoding="utf-8")

                for pattern, framework in FRAMEWORK_IMPORT_PATTERNS:
                    # Special case: pydantic allowed in KNOWN_DOMAIN_PYDANTIC_FILES
                    if framework == "pydantic" and rel in KNOWN_DOMAIN_PYDANTIC_FILES:
                        continue

                    if pattern.search(source):
                        violations.append(
                            f"{rel}: imports '{framework}' (forbidden in domain/ — "
                            "domain must be pure Python, no framework deps)"
                        )

        assert violations == [], (
            "DDD purity violation — domain/ imports framework code:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nFix: move framework-dependent code to infrastructure/ or application/. "
            "Domain layer must only use Python stdlib + domain siblings."
        )

    def test_infrastructure_does_not_import_api_or_services(self) -> None:
        """infrastructure/ MUST NOT import api/ or application/services/.

        Inside-Out rule: dependencies flow inward only.
        infrastructure/ → domain/  (allowed)
        api/ → application/ → infrastructure/ (allowed)
        infrastructure/ → api/  (FORBIDDEN — forward dependency)
        infrastructure/ → application/services/  (FORBIDDEN — circular)
        """
        violations: list[str] = []

        for module_root in MODULE_ROOTS:
            infra_dir = module_root / "infrastructure"
            for py_file in _python_files_in(infra_dir):
                rel = _relative(py_file)
                if rel in KNOWN_INFRA_FORWARD_IMPORTS:
                    continue
                source = py_file.read_text(encoding="utf-8")

                for pattern in INFRA_FORBIDDEN_IMPORT_PATTERNS:
                    if pattern.search(source):
                        violations.append(
                            f"{rel}: contains forbidden import matching '{pattern.pattern}' "
                            "(infrastructure/ MUST NOT depend on api/ or application/services/)"
                        )

        assert violations == [], (
            "DDD layering violation — infrastructure/ imports api/ or application/services/:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nFix: refactor the dependency inversion. If infra needs application logic, "
            "extract a domain interface (ABC) that infra implements."
        )

    def test_application_ports_are_abcs(self) -> None:
        """application/ports/ files MUST define ABC interfaces (no concrete implementations).

        Ports are abstract contracts (Dependency Inversion Principle).
        Concrete implementations belong in infrastructure/ or application/ (non-ports).
        """
        violations: list[str] = []

        for module_root in MODULE_ROOTS:
            ports_dir = module_root / "application" / "ports"
            for py_file in _python_files_in(ports_dir):
                rel = _relative(py_file)
                source = py_file.read_text(encoding="utf-8")

                # Port files must reference ABC (either as base class or import)
                has_abc = (
                    "ABC" in source
                    or "abstractmethod" in source
                    or "from abc import" in source
                    or "import abc" in source
                )

                if not has_abc:
                    violations.append(
                        f"{rel}: application/ports/ file does not use ABC/abstractmethod. "
                        "Ports must be abstract interfaces (no concrete logic)."
                    )

        if violations:
            assert False, (
                "DDD ports violation — application/ports/ files missing ABC:\n"
                + "\n".join(f"  - {v}" for v in violations)
                + "\n\nFix: inherit from ABC + decorate abstract methods with @abstractmethod. "
                "Concrete implementations belong in infrastructure/ or application/ (non-ports)."
            )

    def test_api_does_not_import_domain_directly(self) -> None:
        """api/ MUST NOT import domain/ directly (must go through application services).

        Exception: domain/exceptions may be imported for HTTPException mapping.
        Exception: domain enums may be imported for DTO type annotations.
        All other domain imports from api/ bypass the application layer (thin-router violation).
        """
        violations: list[str] = []

        for module_root in MODULE_ROOTS:
            api_dir = module_root / "api"
            for py_file in _python_files_in(api_dir):
                rel = _relative(py_file)
                if rel in KNOWN_API_DIRECT_DOMAIN_IMPORTS:
                    continue
                source = py_file.read_text(encoding="utf-8")

                for pattern in API_DIRECT_DOMAIN_IMPORT_PATTERNS:
                    matches = list(pattern.finditer(source))
                    for m in matches:
                        # Extract the full source line at match position (not just the captured group)
                        # m.group(0) only captures up to `domain` (word boundary), but the
                        # allowed-submodule patterns need `domain.exceptions` / `domain.enums.*`
                        match_start = m.start()
                        line_start = source.rfind("\n", 0, match_start) + 1
                        line_end = source.find("\n", match_start)
                        if line_end == -1:
                            line_end = len(source)
                        full_import_line = source[line_start:line_end].strip()
                        # Check if this is an allowed exception (exceptions or enums)
                        is_allowed = any(
                            allowed.search(full_import_line) for allowed in API_DOMAIN_IMPORT_ALLOWED_SUBMODULES
                        )
                        if not is_allowed:
                            violations.append(
                                f"{rel}: api/ imports domain/ directly: `{full_import_line}` "
                                "(api/ must call application services, not domain objects directly)"
                            )

        assert violations == [], (
            "DDD thin-router violation — api/ imports domain/ directly:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nFix: move domain logic calls into an application service method. "
            "api/ layer should only: validate DTO → call service → map exception → return response."
        )

    def test_domain_files_have_no_sqla_models(self) -> None:
        """domain/ files MUST NOT declare SQLAlchemy mapped models (DeclarativeBase, mapped_column).

        SQLAlchemy models belong in infrastructure/models/ (or persistence/models/).
        Domain entities are pure Python dataclasses or Pydantic models without ORM mapping.
        """
        violations: list[str] = []

        sqla_model_patterns = (
            re.compile(r"class\s+\w+\s*\(\s*Base\s*\)"),  # class Foo(Base)
            re.compile(r"DeclarativeBase"),
            re.compile(r"mapped_column"),
            re.compile(r"relationship\("),
            re.compile(r"from sqlalchemy.orm import.*Mapped"),
        )

        for module_root in MODULE_ROOTS:
            domain_dir = module_root / "domain"
            for py_file in _python_files_in(domain_dir):
                rel = _relative(py_file)
                source = py_file.read_text(encoding="utf-8")

                for pattern in sqla_model_patterns:
                    if pattern.search(source):
                        violations.append(
                            f"{rel}: domain/ contains SQLAlchemy ORM construct "
                            f"matching '{pattern.pattern}'. ORM models belong in infrastructure/."
                        )
                        break  # One violation per file is enough

        assert violations == [], (
            "DDD purity violation — domain/ contains SQLAlchemy ORM code:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nFix: move ORM model class to infrastructure/models/ or persistence/models/. "
            "Domain entities must be pure Python dataclasses or ABCs."
        )

    def test_no_cross_module_imports_between_business_modules(self) -> None:
        """scheduling/payments/fiscal MUST NOT import each other directly.

        Cross-module imports bypass DDD boundaries. Use application ports (ABCs)
        and dependency injection for cross-module communication.

        Exception: scheduling/application/ports/ may declare cross-module port ABCs.
        The implementations (in payments/ or fiscal/) may import those ABCs to implement them.
        """
        violations: list[str] = []

        # Ratchet: known legitimate cross-module imports (composition-root wiring pattern).
        # api/ (composition root) may import concrete port implementations from sibling modules
        # to perform DI wiring. This is the ONLY exception to cross-module isolation.
        # Add entries ONLY with justified commit message citing the DI wiring reason.
        known_cross_module: frozenset[str] = frozenset(
            [
                # charge_router.py (payments/api) wires FiscalEmitPortImpl (fiscal) into
                # ChargeOrchestrator for the charge-saga composition root. This is DI wiring,
                # not domain logic coupling. Documented in 03-arch § 6.1 charge-saga.
                "vitalia/backend/src/modules/vitalia/payments/api/charge_router.py",
            ]
        )

        # Pairs to check: (importer_root, forbidden_import_pattern)
        checks = [
            # scheduling MUST NOT import payments implementation (only port ABC)
            (
                SCHEDULING_ROOT,
                re.compile(r"from\s+src\.modules\.vitalia\.payments\.(?!application\.payment_charge_port_impl|api)"),
                "scheduling/ imports from payments/ beyond port impl",
            ),
            # scheduling MUST NOT import fiscal implementation
            (
                SCHEDULING_ROOT,
                re.compile(r"from\s+src\.modules\.vitalia\.fiscal\.(?!application\.fiscal_emit_port_impl|api)"),
                "scheduling/ imports from fiscal/ beyond port impl",
            ),
            # payments MUST NOT import fiscal (separate concerns)
            # Exception: charge_router.py (composition root) wires FiscalEmitPortImpl — see ratchet above
            (
                PAYMENTS_ROOT,
                re.compile(r"from\s+src\.modules\.vitalia\.fiscal"),
                "payments/ imports from fiscal/ (cross-module forbidden)",
            ),
            # fiscal MUST NOT import payments (separate concerns)
            (
                FISCAL_ROOT,
                re.compile(r"from\s+src\.modules\.vitalia\.payments"),
                "fiscal/ imports from payments/ (cross-module forbidden)",
            ),
        ]

        for module_root, pattern, description in checks:
            for py_file in _python_files_in(module_root):
                rel = _relative(py_file)
                if rel in known_cross_module:
                    continue
                source = py_file.read_text(encoding="utf-8")
                if pattern.search(source):
                    violations.append(f"{rel}: {description}")

        assert violations == [], (
            "DDD cross-module import violation:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nFix: use port interfaces (ABCs) + dependency injection for cross-module "
            "communication. Never import business module internals directly across modules."
        )

    def test_application_services_do_not_import_api(self) -> None:
        """application/services/ MUST NOT import api/ or dtos/.

        DTOs are consumed by routes; services should operate on domain objects.
        If a service needs DTO types, that indicates a layering inversion.
        """
        violations: list[str] = []

        api_import_in_services = (
            re.compile(r"from\s+src\.modules\.vitalia\.\w+\.api"),
            re.compile(r"import\s+src\.modules\.vitalia\.\w+\.api"),
        )

        for module_root in MODULE_ROOTS:
            services_dir = module_root / "application" / "services"
            for py_file in _python_files_in(services_dir):
                rel = _relative(py_file)
                source = py_file.read_text(encoding="utf-8")

                for pattern in api_import_in_services:
                    if pattern.search(source):
                        violations.append(
                            f"{rel}: application/services/ imports from api/ "
                            "(api DTOs must not leak into application layer)"
                        )

        assert violations == [], (
            "DDD layering violation — application/services/ imports api/:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nFix: services should accept primitive types or domain objects. "
            "Keep DTOs in api/ layer only."
        )
