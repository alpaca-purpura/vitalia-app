"""Arch fitness — D2-voice anti-creep guard: health_voice_validator MUST NOT exist.

Decisión de arquitectura D2-voice (CONTEXT-BRIEF.md 2026-05-27):
  NO crear health_voice_validator.py — la validación de voz usa SOLO el blocklist
  configurable (ProhibitedPhraseRepository) como soft warning. Cualquier validator LLM
  o regla-based sería scope creep fuera del contrato del ticket.

Este test es un ratchet permanente: si en el futuro alguien introduce accidentalmente
health_voice_validator.py, este test falla de inmediato.

downstream-regression-na: brand-local arch fitness guard vitalia brand_studio
"""

from __future__ import annotations

from pathlib import Path

WS_ROOT = Path(__file__).resolve().parents[4]
VITALIA_SRC = WS_ROOT / "vitalia" / "backend" / "src"


class TestNoHealthVoiceValidator:
    """D2-voice anti-creep: health_voice_validator.py debe no existir en brand_studio."""

    def test_health_voice_validator_file_absent(self) -> None:
        """health_voice_validator.py NO debe existir bajo vitalia/backend/src/.

        Decisión D2-voice: la validación de frases problemáticas usa SOLO el
        soft-warning blocklist (ProhibitedPhraseRepository). No se introduce
        un validador LLM ni regla-based separado.

        Si este test falla, alguien creó health_voice_validator.py en violación
        del contrato arquitectónico — remover el archivo y usar blocklist.
        """
        violations: list[Path] = []

        if VITALIA_SRC.exists():
            for candidate in VITALIA_SRC.rglob("health_voice_validator*.py"):
                violations.append(candidate)

        assert violations == [], (
            "D2-voice anti-creep VIOLATION: health_voice_validator.py encontrado.\n"
            "Archivos prohibidos:\n" + "\n".join(f"  {p.relative_to(WS_ROOT)}" for p in violations) + "\n\n"
            "Decisión D2-voice: la validación de voz usa SOLO el blocklist configurable "
            "(ProhibitedPhraseRepository). Remover el archivo creado y usar "
            "VoiceBlocklistService.list_for_tenant() para el soft warning de UI."
        )

    def test_no_health_voice_validator_class_defined(self) -> None:
        """La clase HealthVoiceValidator NO debe definirse en ningún archivo brand_studio.

        Guard complementario: alguien podría renombrar el archivo pero dejar la clase.
        """
        if not VITALIA_SRC.exists():
            return

        brand_studio_src = VITALIA_SRC / "modules" / "vitalia" / "brand_studio"
        if not brand_studio_src.exists():
            return

        violations: list[str] = []
        for py_file in brand_studio_src.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            if "class HealthVoiceValidator" in content:
                violations.append(str(py_file.relative_to(WS_ROOT)))

        assert violations == [], (
            "D2-voice anti-creep VIOLATION: HealthVoiceValidator clase encontrada en:\n"
            + "\n".join(f"  {v}" for v in violations)
            + "\n\n"
            "Esta clase representa scope creep fuera del contrato D2-voice. "
            "Removerla y usar el soft-warning blocklist configurable."
        )

    def test_no_llm_voice_validation_import(self) -> None:
        """brand_studio NO debe importar módulos de validación LLM-based de voz.

        Garantiza que el anti-creep aplica también a imports de módulos externos.
        """
        if not VITALIA_SRC.exists():
            return

        brand_studio_src = VITALIA_SRC / "modules" / "vitalia" / "brand_studio"
        if not brand_studio_src.exists():
            return

        # Patrones prohibidos de import de validador de voz
        forbidden_imports = [
            "health_voice_validator",
            "HealthVoiceValidator",
            "voice_validator",
            "VoiceValidator",
        ]

        violations: list[str] = []
        for py_file in brand_studio_src.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            for pattern in forbidden_imports:
                if f"import {pattern}" in content or f"from {pattern}" in content:
                    violations.append(f"{py_file.relative_to(WS_ROOT)}: import '{pattern}'")

        assert violations == [], (
            "D2-voice anti-creep VIOLATION: imports de validador de voz detectados:\n"
            + "\n".join(f"  {v}" for v in violations)
            + "\n\nUsar VoiceBlocklistService.list_for_tenant() en su lugar."
        )
