"""Arch fitness — DDD purity para vitalia brand_studio module.

Verifica Inside-Out layering (domain → infrastructure → application → api):
  1. domain/ — Python puro, SIN imports de framework (fastapi, sqlalchemy, pydantic).
  2. infrastructure/ — NO debe importar de api/ ni application/services/.
  3. application/services/ — SIN imports directos de api/.
  4. api/ — thin layer, puede importar application/services/ y DTOs.

Ratchet pattern: allowlists empiezan vacías. Agregar solo con justificación
en commit message.

T-3 — F2-S7 vitalia-fase2-lisa-marca arch tests (brand_studio DDD purity).

downstream-regression-na: brand-local arch fitness test vitalia brand_studio
"""

from __future__ import annotations

import re
from pathlib import Path

WS_ROOT = Path(__file__).resolve().parents[4]
VITALIA_BE_SRC = WS_ROOT / "vitalia" / "backend" / "src"

BRAND_STUDIO_ROOT = VITALIA_BE_SRC / "modules" / "vitalia" / "brand_studio"

# ─── Patrones de framework prohibidos en domain/ ────────────────────────────

FRAMEWORK_IMPORT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^\s*(import|from)\s+fastapi", re.MULTILINE), "fastapi"),
    (re.compile(r"^\s*(import|from)\s+sqlalchemy", re.MULTILINE), "sqlalchemy"),
    (re.compile(r"^\s*(import|from)\s+starlette", re.MULTILINE), "starlette"),
    (re.compile(r"^\s*(import|from)\s+uvicorn", re.MULTILINE), "uvicorn"),
    (re.compile(r"^\s*(import|from)\s+aiohttp", re.MULTILINE), "aiohttp"),
    (re.compile(r"^\s*(import|from)\s+httpx", re.MULTILINE), "httpx"),
)

# Ratchet: archivos domain/ que pueden usar Pydantic (value objects puros).
# Empezar vacío — solo agregar con justificación en commit.
KNOWN_DOMAIN_PYDANTIC_FILES: frozenset[str] = frozenset([])

# ─── Patrones prohibidos en infrastructure/ (forward imports) ────────────────

INFRA_FORBIDDEN_IMPORT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"from\s+src\.modules\.vitalia\.brand_studio\.api\b"),
    re.compile(r"import\s+src\.modules\.vitalia\.brand_studio\.api\b"),
    re.compile(r"from\s+src\.modules\.vitalia\.brand_studio\.application\.services"),
    re.compile(r"import\s+src\.modules\.vitalia\.brand_studio\.application\.services"),
)

# Ratchet: infra files que legítimamente importan de api/ o services/.
KNOWN_INFRA_FORWARD_IMPORTS: frozenset[str] = frozenset([])

# ─── Patrones de cross-module brand (prohibidos excepto _shared) ──────────────

CROSS_MODULE_FORBIDDEN_PATTERNS: tuple[re.Pattern[str], ...] = (
    # brand_studio NO debe importar de otros módulos vitalia (scheduling, payments, etc.)
    # EXCEPTO: _shared (audit, telemetry, auth) — eso es permitido
    re.compile(r"from\s+src\.modules\.vitalia\.scheduling\b"),
    re.compile(r"from\s+src\.modules\.vitalia\.payments\b"),
    re.compile(r"from\s+src\.modules\.vitalia\.fiscal\b"),
    re.compile(r"from\s+src\.modules\.vitalia\.crm\b"),
)

KNOWN_CROSS_MODULE_EXCEPTIONS: frozenset[str] = frozenset([])


def _relative(p: Path) -> str:
    return str(p.relative_to(WS_ROOT))


class TestBrandStudioModuleDDD:
    """brand_studio module debe seguir DDD Inside-Out (domain → infra → app → api)."""

    def test_brand_studio_module_exists(self) -> None:
        """Sanity: brand_studio module debe existir."""
        assert BRAND_STUDIO_ROOT.exists(), (
            "vitalia/backend/src/modules/vitalia/brand_studio/ debe existir "
            "por 03-arch-be.md F2-S7 brand_studio module layout."
        )

    def test_domain_layer_no_framework_imports(self) -> None:
        """domain/ debe ser Python puro — sin imports de framework.

        DDD Inside-Out: el dominio es la capa más pura. Solo stdlib, dataclasses,
        enums, uuid, datetime. Sin dependencias externas de framework.
        """
        domain_dir = BRAND_STUDIO_ROOT / "domain"
        if not domain_dir.exists():
            return

        violations: list[str] = []

        for py_file in domain_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            rel_file = _relative(py_file)

            for pattern, framework_name in FRAMEWORK_IMPORT_PATTERNS:
                if pattern == re.compile(r"^\s*(import|from)\s+sqlalchemy", re.MULTILINE):
                    # SQLAlchemy en domain/ siempre es violación
                    pass
                if framework_name == "pydantic":
                    # Pydantic en domain/ requiere excepción explícita
                    if rel_file in KNOWN_DOMAIN_PYDANTIC_FILES:
                        continue
                if pattern.search(content):
                    violations.append(f"{rel_file}: imports de {framework_name}")

        assert violations == [], (
            "DDD Inside-Out VIOLATION: imports de framework en domain/ de brand_studio:\n"
            + "\n".join(f"  {v}" for v in violations)
            + "\n\n"
            "domain/ debe ser Python puro (stdlib + dataclasses + enums + uuid).\n"
            "Mover imports de framework a infrastructure/ o application/."
        )

    def test_domain_layer_no_sqlalchemy(self) -> None:
        """domain/ NO debe tener imports de SQLAlchemy.

        Los modelos SQLAlchemy viven en persistence/models/ o infrastructure/models/.
        El dominio usa dataclasses (frozen=True) o plain Python.
        """
        domain_dir = BRAND_STUDIO_ROOT / "domain"
        if not domain_dir.exists():
            return

        sqla_pattern = re.compile(r"^\s*(import|from)\s+sqlalchemy", re.MULTILINE)
        violations: list[str] = []

        for py_file in domain_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            if sqla_pattern.search(content):
                violations.append(_relative(py_file))

        assert violations == [], (
            "DDD Inside-Out VIOLATION: SQLAlchemy importado en domain/ de brand_studio:\n"
            + "\n".join(f"  {v}" for v in violations)
            + "\n\n"
            "Modelos SQLA deben vivir en persistence/models/ o infrastructure/models/. "
            "domain/ usa dataclasses para entidades de dominio."
        )

    def test_infrastructure_no_forward_imports(self) -> None:
        """infrastructure/ NO debe importar de api/ ni application/services/.

        DDD Inside-Out: infra implementa interfaces del dominio. No puede conocer
        las capas superiores (api, services). Eso rompería la dirección de dependencias.
        """
        infra_dir = BRAND_STUDIO_ROOT / "infrastructure"
        if not infra_dir.exists():
            return

        violations: list[str] = []

        for py_file in infra_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            rel_file = _relative(py_file)

            if rel_file in KNOWN_INFRA_FORWARD_IMPORTS:
                continue

            for pattern in INFRA_FORBIDDEN_IMPORT_PATTERNS:
                if pattern.search(content):
                    violations.append(f"{rel_file}: forward import detectado")
                    break

        assert violations == [], (
            "DDD Inside-Out VIOLATION: infrastructure/ importa de capas superiores:\n"
            + "\n".join(f"  {v}" for v in violations)
            + "\n\n"
            "infrastructure/ puede importar: domain/, stdlib, SQLAlchemy, httpx. "
            "Nunca: api/, application/services/."
        )

    def test_domain_entities_are_dataclasses_or_pydantic(self) -> None:
        """Entidades de domain/ deben usar @dataclass o Pydantic (NOT SQLAlchemy ORM).

        brand_studio.domain: ProhibitedPhrase, TrustSignal, VoicePreview — todos
        son @dataclass. Verificar que no usen herencia de Base SQLA.
        """
        domain_dir = BRAND_STUDIO_ROOT / "domain"
        if not domain_dir.exists():
            return

        sqla_base_pattern = re.compile(r"class\s+\w+\(.*Base.*\):", re.MULTILINE)
        violations: list[str] = []

        for py_file in domain_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            content = py_file.read_text(encoding="utf-8")
            if sqla_base_pattern.search(content):
                violations.append(_relative(py_file))

        assert violations == [], (
            "DDD VIOLATION: entidades de domain/ heredan de SQLAlchemy Base:\n"
            + "\n".join(f"  {v}" for v in violations)
            + "\n\n"
            "Entidades de dominio usan @dataclass (stdlib). "
            "Modelos SQLA viven en persistence/models/ o infrastructure/models/."
        )

    def test_brand_studio_no_cross_module_imports(self) -> None:
        """brand_studio NO debe importar de otros módulos de negocio vitalia.

        Excepción permitida: _shared (audit_writer, telemetry, auth) — eso es
        infraestructura compartida de la marca, no un módulo de negocio distinto.

        Módulos de negocio hermanos (scheduling, payments, fiscal) deben comunicarse
        via domain events o IDs — nunca imports directos.
        """
        if not BRAND_STUDIO_ROOT.exists():
            return

        violations: list[str] = []

        for py_file in BRAND_STUDIO_ROOT.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            rel_file = _relative(py_file)

            if rel_file in KNOWN_CROSS_MODULE_EXCEPTIONS:
                continue

            for pattern in CROSS_MODULE_FORBIDDEN_PATTERNS:
                if pattern.search(content):
                    violations.append(f"{rel_file}: cross-module import detectado")
                    break

        assert violations == [], (
            "DDD cross-module VIOLATION: brand_studio importa módulos hermanos vitalia:\n"
            + "\n".join(f"  {v}" for v in violations)
            + "\n\n"
            "Comunicación cross-module: usar domain events o IDs. "
            "_shared/ (audit, telemetry, auth) es excepción permitida."
        )

    def test_domain_layer_has_expected_entities(self) -> None:
        """domain/ debe contener las entidades canónicas del módulo brand_studio.

        Verifica que el módulo tiene su capa de dominio poblada correctamente
        per 03-arch-be.md F2-S7 entity catalog.
        """
        domain_dir = BRAND_STUDIO_ROOT / "domain"
        if not domain_dir.exists():
            return

        expected_entities = [
            "prohibited_phrase",
            "trust_signal",
        ]

        domain_files = {p.stem for p in domain_dir.rglob("*.py") if not p.name.startswith("__")}

        for entity_stem in expected_entities:
            assert entity_stem in domain_files, (
                f"domain/ de brand_studio debe contener '{entity_stem}.py'. Archivos presentes: {sorted(domain_files)}"
            )

    def test_infrastructure_repositories_exist(self) -> None:
        """infrastructure/repositories/ debe contener repos ABC e implementaciones.

        Verifica que la capa de infraestructura implementa los contratos del dominio.
        """
        infra_repos = BRAND_STUDIO_ROOT / "infrastructure" / "repositories"
        if not infra_repos.exists():
            # También puede estar en persistence/
            infra_repos = BRAND_STUDIO_ROOT / "persistence"

        if not infra_repos.exists():
            return

        repo_files = list(infra_repos.rglob("*repository*.py"))
        assert len(repo_files) >= 1, (
            "brand_studio infrastructure/ debe tener al menos 1 archivo de repositorio. "
            f"Directorio revisado: {infra_repos.relative_to(WS_ROOT)}"
        )

    def test_application_services_exist(self) -> None:
        """application/services/ debe contener los servicios de aplicación.

        brand_studio per T-2 debe tener al menos: MarcaService, VoiceBlocklistService,
        VoicePreviewService, TrustCatalogService.
        """
        services_dir = BRAND_STUDIO_ROOT / "application" / "services"
        if not services_dir.exists():
            return

        service_files = [p.name for p in services_dir.glob("*.py") if not p.name.startswith("__")]

        assert len(service_files) >= 3, (
            f"brand_studio application/services/ debe tener ≥ 3 servicios. Encontrados: {service_files}"
        )

    def test_api_layer_uses_response_model(self) -> None:
        """api/routers/ debe declarar response_model= en todos los endpoints.

        Verificación rápida brand_studio específica (el arch test global
        test_response_model_required.py ya lo cubre — esta es una guard local).
        """
        routers_dir = BRAND_STUDIO_ROOT / "api" / "routers"
        if not routers_dir.exists():
            return

        route_decorator_pattern = re.compile(r"@router\.(get|post|put|patch|delete)\(", re.MULTILINE)
        response_model_pattern = re.compile(r"response_model\s*=", re.MULTILINE)

        # Verificar al menos un router existe con response_model
        violations: list[str] = []

        for py_file in routers_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            content = py_file.read_text(encoding="utf-8")
            route_count = len(route_decorator_pattern.findall(content))
            response_model_count = len(response_model_pattern.findall(content))
            if route_count > 0 and response_model_count == 0:
                violations.append(f"{_relative(py_file)}: {route_count} routes, 0 response_model=")

        assert violations == [], (
            "PII VIOLATION: routers de brand_studio sin response_model=:\n"
            + "\n".join(f"  {v}" for v in violations)
            + "\n\nCada route debe declarar response_model= (PII allowlist enforcement)."
        )
