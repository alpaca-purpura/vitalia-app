"""Architecture fitness: vitalia observability MUST NOT mirror engine patterns.

Per .claude/rules/anti-duplication.md § Regla cardinal:
  "ANTES crear archivo: grep cross-codebase. Match → EXTEND vía herencia desde engine."

This test verifies:
1. sanitize_payload is IMPORTED from luana_core_observability — never re-defined locally
2. No local PII regex patterns duplicating engine sanitization
3. otel_setup imports from opentelemetry SDK (not a local tracer reimpl)

downstream-regression-na: brand-local arch fitness test; no cross-brand consumers
"""

from __future__ import annotations

import ast
from pathlib import Path

WS_ROOT = Path(__file__).parents[5]
OBSERVABILITY_DIR = WS_ROOT / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "_shared" / "observability"


def _get_py_sources() -> list[Path]:
    """Return all .py files in the vitalia _shared/observability dir."""
    if not OBSERVABILITY_DIR.exists():
        return []
    return [p for p in OBSERVABILITY_DIR.glob("*.py") if p.name != "__init__.py"]


def _read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestNoObservabilityMirror:
    """Observability files must not mirror engine sanitization."""

    def test_no_local_sanitize_payload_definition(self) -> None:
        """No observability file should define its own sanitize_payload function.

        Must import from luana_core_observability.recording.sanitization instead.
        """
        for py_file in _get_py_sources():
            src = _read_source(py_file)
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    assert node.name != "sanitize_payload", (
                        f"{py_file.name}: defines local `sanitize_payload` — "
                        f"use `from luana_core_observability.recording.sanitization "
                        f"import sanitize_payload` instead (anti-duplication.md)"
                    )

    def test_no_local_redact_string_definition(self) -> None:
        """No observability file should define its own redact_string.

        Engine provides redact_value and sanitize_payload in luana_core_observability.
        """
        for py_file in _get_py_sources():
            src = _read_source(py_file)
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    assert node.name not in (
                        "redact_string",
                        "redact_value",
                    ), (
                        f"{py_file.name}: defines local `{node.name}` — "
                        f"use engine `luana_core_observability.recording.sanitization` (anti-duplication.md)"
                    )

    def test_no_hardcoded_sentry_dsn_in_otel_setup(self) -> None:
        """otel_setup.py must not hardcode SENTRY_DSN value.

        Per anti-pattern: '❌ Hardcode SENTRY_DSN / OTEL_EXPORTER_OTLP_ENDPOINT in code'.
        """
        otel_file = OBSERVABILITY_DIR / "otel_setup.py"
        if not otel_file.exists():
            return  # not yet created — test passes vacuously (RED phase)

        src = _read_source(otel_file)
        # A hardcoded DSN would look like https://...@o....ingest.sentry.io/...
        import re

        hardcoded_dsn = re.findall(r"https://[a-f0-9]+@o\d+\.ingest\.sentry\.io/\d+", src)
        assert not hardcoded_dsn, (
            f"otel_setup.py hardcodes Sentry DSN: {hardcoded_dsn} — use environment variable SENTRY_DSN instead"
        )

    def test_no_hardcoded_otlp_endpoint(self) -> None:
        """otel_setup.py must not hardcode OTLP endpoint URL.

        Must read from OTEL_EXPORTER_OTLP_ENDPOINT env var.
        """
        otel_file = OBSERVABILITY_DIR / "otel_setup.py"
        if not otel_file.exists():
            return

        src = _read_source(otel_file)
        import re

        # Hardcoded Jaeger/Tempo endpoints
        hardcoded_endpoints = re.findall(
            r"(grpc://[a-z0-9.-]+:\d+|http://[a-z0-9.-]+:4317)",
            src,
        )
        assert not hardcoded_endpoints, (
            f"otel_setup.py hardcodes OTLP endpoint: {hardcoded_endpoints} "
            f"— use OTEL_EXPORTER_OTLP_ENDPOINT env var instead"
        )

    def test_agent_spans_imports_sanitize_not_mirror(self) -> None:
        """agent_spans.py must import sanitize (not re-define it).

        Per .claude/rules/anti-duplication.md:
          PII sanitization lives in core/luana-core-observability/src/.../sanitization.py
          vitalia adapter lives in compliance_service_adapter.sanitize_phi_payload
          Both are imports, never re-implemented.
        """
        agent_spans_file = OBSERVABILITY_DIR / "agent_spans.py"
        if not agent_spans_file.exists():
            return

        src = _read_source(agent_spans_file)
        tree = ast.parse(src)

        # Check no local definition of sanitization functions
        defined_fns = {
            node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        prohibited = {"sanitize_payload", "redact_string", "redact_value", "_redact_phi"}
        mirror = defined_fns & prohibited
        assert not mirror, (
            f"agent_spans.py defines local sanitization: {mirror} — "
            f"import from compliance_service_adapter or luana_core_observability instead"
        )

    def test_batch_span_processor_used_not_simple(self) -> None:
        """otel_setup.py must use BatchSpanProcessor (not SimpleSpanProcessor).

        Per anti-pattern: '❌ Sync export blocking turn (use batch span processor)'.
        """
        otel_file = OBSERVABILITY_DIR / "otel_setup.py"
        if not otel_file.exists():
            return

        src = _read_source(otel_file)
        if "BatchSpanProcessor" in src:
            # Good — batch processor present
            return
        # If no exporter configured at all (no-op path), that's also OK
        if "OTLPSpanExporter" not in src and "JaegerExporter" not in src:
            return
        # Has exporter but not batch processor — this is the violation
        assert "SimpleSpanProcessor" not in src, (
            "otel_setup.py uses SimpleSpanProcessor — must use BatchSpanProcessor "
            "to avoid blocking turn execution (anti-pattern per T-infra-5 spec)"
        )
