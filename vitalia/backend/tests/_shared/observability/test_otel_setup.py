"""Tests for OpenTelemetry tracer provider setup + Sentry SDK init.

TDD: RED-first. These tests define the contract for otel_setup.py.

Tests that require opentelemetry-sdk are marked with `requires_otel` and
skip gracefully when OTel is not installed in the venv.

downstream-regression-na: brand-local observability setup test; no cross-brand consumers
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

# Marker to skip tests needing opentelemetry SDK
try:
    import opentelemetry  # noqa: F401

    _OTEL_INSTALLED = True
except ImportError:
    _OTEL_INSTALLED = False

requires_otel = pytest.mark.skipif(not _OTEL_INSTALLED, reason="opentelemetry-sdk not installed")


@requires_otel
class TestOtelSetupResourceAttrs:
    """Resource attributes must match service name/namespace/environment contract."""

    def test_resource_attrs_service_name(self) -> None:
        """Resource must have service.name = 'vitalia-backend'."""
        from src.modules.vitalia._shared.observability.otel_setup import (
            build_otel_resource,
        )

        resource = build_otel_resource(environment="test")
        attrs = dict(resource.attributes)
        assert attrs.get("service.name") == "vitalia-backend"

    def test_resource_attrs_service_namespace(self) -> None:
        """Resource must have service.namespace = 'vitalia'."""
        from src.modules.vitalia._shared.observability.otel_setup import (
            build_otel_resource,
        )

        resource = build_otel_resource(environment="staging")
        attrs = dict(resource.attributes)
        assert attrs.get("service.namespace") == "vitalia"

    def test_resource_attrs_deployment_environment_from_arg(self) -> None:
        """deployment.environment must reflect the environment arg."""
        from src.modules.vitalia._shared.observability.otel_setup import (
            build_otel_resource,
        )

        resource = build_otel_resource(environment="production")
        attrs = dict(resource.attributes)
        assert attrs.get("deployment.environment") == "production"

    def test_resource_attrs_deployment_environment_from_env_var(self) -> None:
        """deployment.environment falls back to DEPLOYMENT_ENV env var."""
        from src.modules.vitalia._shared.observability.otel_setup import (
            build_otel_resource,
        )

        with patch.dict(os.environ, {"DEPLOYMENT_ENV": "staging-pe"}):
            resource = build_otel_resource()
        attrs = dict(resource.attributes)
        assert attrs.get("deployment.environment") == "staging-pe"

    def test_resource_attrs_environment_default_is_development(self) -> None:
        """deployment.environment defaults to 'development' when env var absent."""
        from src.modules.vitalia._shared.observability.otel_setup import (
            build_otel_resource,
        )

        env = {k: v for k, v in os.environ.items() if k != "DEPLOYMENT_ENV"}
        with patch.dict(os.environ, env, clear=True):
            resource = build_otel_resource()
        attrs = dict(resource.attributes)
        assert attrs.get("deployment.environment") == "development"


@requires_otel
class TestOtelTracerProvider:
    """Tracer provider setup (returns tracer, registers globally)."""

    def test_setup_otel_returns_tracer(self) -> None:
        """setup_otel() must return an opentelemetry Tracer instance."""
        from opentelemetry.trace import Tracer

        from src.modules.vitalia._shared.observability.otel_setup import setup_otel

        tracer = setup_otel(environment="test", sentry_dsn=None, otlp_endpoint=None)
        assert isinstance(tracer, Tracer)

    def test_setup_otel_noop_when_no_endpoint(self) -> None:
        """When otlp_endpoint is None, setup still returns a valid tracer (no-op exporter)."""
        from opentelemetry.trace import Tracer

        from src.modules.vitalia._shared.observability.otel_setup import setup_otel

        tracer = setup_otel(environment="test", sentry_dsn=None, otlp_endpoint=None)
        assert tracer is not None
        assert isinstance(tracer, Tracer)

    def test_no_hardcoded_sentry_dsn(self) -> None:
        """otel_setup.py MUST NOT hardcode SENTRY_DSN — must read from env."""
        import inspect

        from src.modules.vitalia._shared.observability import otel_setup

        src = inspect.getsource(otel_setup)
        # Must not contain a hardcoded DSN pattern (https://...@sentry.io/...)
        assert "sentry.io" not in src or "os.environ" in src or "os.getenv" in src


class TestSentryInit:
    """Sentry SDK initialisation from env vars only."""

    def test_sentry_init_skipped_when_dsn_none(self) -> None:
        """When sentry_dsn=None, sentry is not initialised."""
        with patch("sentry_sdk.init") as mock_sentry_init:
            from src.modules.vitalia._shared.observability.otel_setup import (
                maybe_init_sentry,
            )

            maybe_init_sentry(sentry_dsn=None)
            mock_sentry_init.assert_not_called()

    def test_sentry_init_called_with_dsn(self) -> None:
        """When sentry_dsn provided, sentry_sdk.init is called once with it."""
        with patch("sentry_sdk.init") as mock_sentry_init:
            from src.modules.vitalia._shared.observability.otel_setup import (
                maybe_init_sentry,
            )

            maybe_init_sentry(sentry_dsn="https://test@sentry.io/123")
            mock_sentry_init.assert_called_once()
            call_kwargs = mock_sentry_init.call_args[1]
            assert call_kwargs["dsn"] == "https://test@sentry.io/123"
