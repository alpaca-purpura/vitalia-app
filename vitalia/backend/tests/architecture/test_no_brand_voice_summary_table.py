"""Arch fitness — D2-voice anti-creep guard: brand_voice_summary tabla NO debe existir.

Decisión de arquitectura D2-voice (CONTEXT-BRIEF.md 2026-05-27):
  NO crear tabla brand_voice_summary como mirror LLM-distilled. Esta tabla sería
  una violación de anti-duplication.md (mirror cross-module prohibido) y del
  contrato D2-voice que establece personality_profiles.system_instruction como
  SSoT de la voz del brand.

Ratchet permanente: si en el futuro alguien introduce brand_voice_summary en
migraciones o modelos SQLAlchemy, este test falla de inmediato.

downstream-regression-na: brand-local arch fitness guard vitalia brand_studio
"""

from __future__ import annotations

from pathlib import Path

WS_ROOT = Path(__file__).resolve().parents[4]
VITALIA_BACKEND = WS_ROOT / "vitalia" / "backend"
VITALIA_SRC = VITALIA_BACKEND / "src"
VITALIA_MIGRATIONS = VITALIA_BACKEND / "alembic" / "versions"


class TestNoBrandVoiceSummaryTable:
    """D2-voice anti-creep: brand_voice_summary tabla y modelo NO deben existir."""

    def test_no_brand_voice_summary_in_migrations(self) -> None:
        """Ninguna migración debe crear la tabla brand_voice_summary.

        Decisión D2-voice: el SSoT de voz es personality_profiles.system_instruction.
        Una tabla brand_voice_summary sería un mirror LLM-distilled prohibido
        por anti-duplication.md y el contrato arquitectónico.
        """
        if not VITALIA_MIGRATIONS.exists():
            return

        violations: list[str] = []
        for migration_file in VITALIA_MIGRATIONS.glob("*.py"):
            content = migration_file.read_text(encoding="utf-8")
            # Buscar cualquier forma de crear esta tabla
            if "brand_voice_summary" in content:
                violations.append(str(migration_file.relative_to(WS_ROOT)))

        assert violations == [], (
            "D2-voice anti-creep VIOLATION: brand_voice_summary encontrada en migraciones:\n"
            + "\n".join(f"  {v}" for v in violations)
            + "\n\n"
            "Decisión D2-voice: NO crear tabla brand_voice_summary como mirror LLM-distilled. "
            "El SSoT de voz es personality_profiles.system_instruction. "
            "Remover la migración o revertir el cambio."
        )

    def test_no_brand_voice_summary_model(self) -> None:
        """Ningún modelo SQLAlchemy debe definir la tabla brand_voice_summary.

        Guard para evitar que se introduzca el modelo SQLA aunque no haya migración.
        """
        if not VITALIA_SRC.exists():
            return

        violations: list[str] = []
        for py_file in VITALIA_SRC.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            # Detecta declaración de tabla en SQLA: __tablename__ = "brand_voice_summary"
            if "__tablename__" in content and "brand_voice_summary" in content:
                violations.append(str(py_file.relative_to(WS_ROOT)))

        assert violations == [], (
            "D2-voice anti-creep VIOLATION: modelo SQLAlchemy con __tablename__ = 'brand_voice_summary' "
            "detectado en:\n" + "\n".join(f"  {v}" for v in violations) + "\n\n"
            "Remover el modelo — no existe ni debe existir esta tabla."
        )

    def test_no_brand_voice_summary_class_defined(self) -> None:
        """La clase BrandVoiceSummary NO debe definirse en ningún archivo.

        Guard complementario para detectar la clase incluso sin __tablename__.
        """
        if not VITALIA_SRC.exists():
            return

        violations: list[str] = []
        for py_file in VITALIA_SRC.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            if "class BrandVoiceSummary" in content:
                violations.append(str(py_file.relative_to(WS_ROOT)))

        assert violations == [], (
            "D2-voice anti-creep VIOLATION: clase BrandVoiceSummary detectada en:\n"
            + "\n".join(f"  {v}" for v in violations)
            + "\n\n"
            "Esta clase representa scope creep fuera del contrato D2-voice. "
            "Removerla. El SSoT de voz es personality_profiles.system_instruction."
        )

    def test_no_brand_voice_summary_code_references_in_brand_studio(self) -> None:
        """brand_studio NO debe referenciar brand_voice_summary en código ejecutable.

        Cubre casos como: from ... import brand_voice_summary, SELECT FROM brand_voice_summary,
        BrandVoiceSummary() instantiation, etc.

        Excluye: referencias en comentarios o docstrings (anti-creep documentation
        que describe el patrón prohibido — eso es documentación, no violación).
        """
        if not VITALIA_SRC.exists():
            return

        brand_studio_src = VITALIA_SRC / "modules" / "vitalia" / "brand_studio"
        if not brand_studio_src.exists():
            return

        import ast

        violations: list[str] = []
        for py_file in brand_studio_src.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            if "brand_voice_summary" not in content:
                continue

            # Detectar referencias en código AST (no en strings/docstrings de nivel módulo)
            try:
                tree = ast.parse(content, filename=str(py_file))
            except SyntaxError:
                continue

            rel_file = str(py_file.relative_to(WS_ROOT))

            for node in ast.walk(tree):
                # Detectar imports: from X import brand_voice_summary / import brand_voice_summary
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    node_str = ast.unparse(node) if hasattr(ast, "unparse") else ""
                    if "brand_voice_summary" in node_str.lower():
                        violations.append(f"{rel_file}: import statement")

                # Detectar __tablename__ = "brand_voice_summary" (SQLAlchemy model)
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if (
                            isinstance(target, ast.Name)
                            and target.id == "__tablename__"
                            and isinstance(node.value, ast.Constant)
                            and "brand_voice_summary" in str(node.value.value)
                        ):
                            violations.append(f"{rel_file}: __tablename__ = 'brand_voice_summary'")

                # Detectar llamadas a BrandVoiceSummary() o instancias
                if isinstance(node, ast.Call):
                    func = node.func
                    call_str = ast.unparse(func) if hasattr(ast, "unparse") else ""
                    if "BrandVoiceSummary" in call_str:
                        violations.append(f"{rel_file}: BrandVoiceSummary() call")

        assert violations == [], (
            "D2-voice anti-creep VIOLATION: código ejecutable referencia brand_voice_summary:\n"
            + "\n".join(f"  {v}" for v in violations)
            + "\n\nRemover el código. "
            "(Nota: referencias en docstrings/comentarios anti-creep son permitidas "
            "— son documentación del patrón prohibido, no violaciones.)"
        )
