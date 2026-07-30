# cap: observability.otel-sentry-graceful-degradation
# story-origin: TBD
"""OpenTelemetry tracer provider setup + Sentry SDK initialisation for Vitalia.

Responsibilities:
  1. build_otel_resource() — creates OTel Resource with canonical attrs:
       service.name = "vitalia-backend"
       service.namespace = "vitalia"
       deployment.environment = from env var DEPLOYMENT_ENV (default "development")
  2. setup_otel() — configures TracerProvider + BatchSpanProcessor (OTLP/Jaeger or no-op)
       Returns the root tracer for the vitalia-backend service.
  3. maybe_init_sentry() — initialises Sentry SDK when DSN is provided.
       DSN MUST come from env vars (SENTRY_DSN) — never hardcoded.

Anti-patterns explicitly avoided:
  ❌ Hardcoded SENTRY_DSN or OTEL_EXPORTER_OTLP_ENDPOINT in code
  ❌ SimpleSpanProcessor (blocking — breaks turn latency SLA)
  ❌ Sync-only export (BatchSpanProcessor ensures async batching)

Per T-infra-5 spec:
  Resource attrs: service.name="vitalia-backend", service.namespace="vitalia",
                  deployment.environment from env.

downstream-regression-na: brand-local otel setup; no cross-brand consumers
"""

from __future__ import annotations

import os

import structlog

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Optional imports — graceful degradation when OTel SDK not installed
# ---------------------------------------------------------------------------
try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import Tracer

    _OTEL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _OTEL_AVAILABLE = False  # type: ignore[assignment]

try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    _OTLP_AVAILABLE = True
except ImportError:
    _OTLP_AVAILABLE = False


def build_otel_resource(environment: str | None = None) -> "Resource":
    """Build an OTel Resource with canonical Vitalia service attributes.

    Args:
        environment: deployment.environment value. If None, reads DEPLOYMENT_ENV
                     env var. Defaults to "development" when neither is set.

    Returns:
        opentelemetry.sdk.resources.Resource with:
          service.name = "vitalia-backend"
          service.namespace = "vitalia"
          deployment.environment = <resolved>
    """
    if not _OTEL_AVAILABLE:  # pragma: no cover
        raise ImportError("opentelemetry-sdk is required for build_otel_resource()")

    resolved_env = environment or os.environ.get("DEPLOYMENT_ENV", "development")

    return Resource(
        attributes={
            "service.name": "vitalia-backend",
            "service.namespace": "vitalia",
            "deployment.environment": resolved_env,
        }
    )


def setup_otel(
    *,
    environment: str | None = None,
    sentry_dsn: str | None = None,
    otlp_endpoint: str | None = None,
) -> "Tracer":
    """Configure the global OTel TracerProvider and return the root vitalia tracer.

    Uses BatchSpanProcessor to avoid blocking the ARQ cron hot-path.
    Falls back to a no-op exporter when no OTLP endpoint is configured,
    so the tracer is always valid (useful for local dev + unit tests).

    Args:
        environment: deployment environment string. Reads DEPLOYMENT_ENV when None.
        sentry_dsn: Sentry DSN string. Reads SENTRY_DSN env var when None.
                    No-op when both are absent.
        otlp_endpoint: OTLP gRPC endpoint URL. Reads OTEL_EXPORTER_OTLP_ENDPOINT
                       env var when None. No-op exporter when both are absent.

    Returns:
        opentelemetry.trace.Tracer for service "vitalia-backend".
    """
    if not _OTEL_AVAILABLE:  # pragma: no cover
        raise ImportError("opentelemetry-sdk is required for setup_otel()")

    resource = build_otel_resource(environment=environment)
    provider = TracerProvider(resource=resource)

    # Resolve OTLP endpoint (env var takes precedence over kwarg)
    resolved_endpoint = otlp_endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", None)

    if resolved_endpoint and _OTLP_AVAILABLE:
        exporter = OTLPSpanExporter(endpoint=resolved_endpoint)
        # BatchSpanProcessor is MANDATORY — SimpleSpanProcessor blocks the caller
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info(
            "otel_otlp_exporter_configured",
            endpoint=resolved_endpoint,
            service="vitalia-backend",
        )
    else:
        logger.debug(
            "otel_noop_exporter_configured",
            reason="no OTLP endpoint or SDK unavailable",
            service="vitalia-backend",
        )

    trace.set_tracer_provider(provider)

    # Init Sentry after provider is registered
    resolved_sentry_dsn = sentry_dsn or os.environ.get("SENTRY_DSN", None)
    maybe_init_sentry(sentry_dsn=resolved_sentry_dsn)

    return trace.get_tracer("vitalia-backend")


def maybe_init_sentry(*, sentry_dsn: str | None) -> None:
    """Initialise Sentry SDK when a DSN is provided.

    DSN MUST come from caller or env var SENTRY_DSN — never hardcoded here.

    Args:
        sentry_dsn: Sentry DSN string or None to skip initialisation.
    """
    if not sentry_dsn:
        logger.debug("sentry_init_skipped", reason="no DSN provided")
        return

    try:
        import sentry_sdk  # noqa: PLC0415 — optional dep

        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=0.1,
            environment=os.environ.get("DEPLOYMENT_ENV", "development"),
            release=os.environ.get("APP_VERSION", "unknown"),
        )
        logger.info("sentry_init_ok", has_dsn=True)
    except ImportError:  # pragma: no cover
        logger.warning("sentry_sdk_not_installed", reason="pip install sentry-sdk")
