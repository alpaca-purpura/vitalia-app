"""Application configuration via pydantic-settings."""

from __future__ import annotations

import re
import warnings
from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings

from luana_core_platform.core.enums import AIProvider, ModelRole, PromptSource


class Settings(BaseSettings):
    """Environment-driven application settings.

    MULTIBRAND CONTRACT (2026-06-16, completes the brand-mountable lift):
    every field below either has a default or is optional, so ``Settings()``
    instantiates under a *minimal multibrand env* (``DATABASE_URL`` +
    ``REDIS_URL`` + LLM keys) WITHOUT the legacy "Visionarias Brain" vars
    (``POSTGRES_*``/``WHATSAPP_*``/``QDRANT_URL``/``TRAEFIK_NETWORK``/…).
    This is what lets any brand mount core routers (copilot ``/chat``, iam
    ``auth_router``) with its own config. Subsystems that genuinely NEED a
    legacy field validate it at point-of-use (fail-loud), never as a blanket
    import/instantiation crash. See ``database_url`` + ``core.security``.
    """

    # API Config
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Visionarias Brain"
    LOG_LEVEL: str = "INFO"  # legacy-standalone overrides via .env
    DOMAIN_NAME: str = ""  # legacy-standalone only (Traefik routing)
    TRAEFIK_NETWORK: str = ""  # legacy-standalone only

    # Security — empty under multibrand; encryption helpers fail-loud if used
    # without it (see core.security.get_encryption_key).
    API_SECRET_KEY: str = ""

    # WhatsApp / Meta — legacy-standalone channel; empty under multibrand
    WHATSAPP_API_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""

    # Evolution API (Self-Hosted)
    EVOLUTION_API_URL: str = ""
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_API_VERSION: str = "v1"  # Options: "v1", "v2"

    # Telegram (sales_agent legacy global)
    TELEGRAM_BOT_TOKEN: str = ""

    # ── Copilot Telegram bot (PI-5 PR-1) ─────────────────────────────────
    # Global Nicolify copilot bot — DISTINTO de TELEGRAM_BOT_TOKEN (sales_agent).
    # D-PI5-001 + D-PI5-005 separación física. NUNCA per-tenant.
    COPILOT_TELEGRAM_BOT_TOKEN: str = ""
    # Random secret validated en webhook header X-Telegram-Bot-Api-Secret-Token.
    # Setear via setWebhook con secret_token (D-PI5-028 anti-pattern A10).
    COPILOT_TELEGRAM_WEBHOOK_SECRET_TOKEN: str = ""
    # TTL magic link en segundos — D-PI5-019 (15 min default)
    COPILOT_TELEGRAM_LINK_TOKEN_TTL_SECONDS: int = 900
    # Bot username (sin @) usado para construir deep link t.me/{username}?start=TOKEN
    # Brand-specific — MUST override en {brand}/.env.dev (e.g., nicolify_copilot_bot,
    # vitalia_copilot_bot, etc.). Engine no asume brand (proposal 2026-05-19).
    COPILOT_TELEGRAM_BOT_USERNAME: str = ""

    # Frontend URL pública (para construir CTA URLs hacia web from bot responses)
    # Brand-specific — MUST override en {brand}/.env.dev (e.g., https://app.nicolify.com,
    # https://dev-app.vitalialat.com, etc.). Engine no asume brand (proposal 2026-05-19).
    FRONTEND_URL: str = ""

    # Google Calendar
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""  # Set in .env per environment

    # -- Meta (Facebook/Instagram) --
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_VERIFY_TOKEN: str = ""
    META_REDIRECT_URI: str = ""  # Set in .env per environment
    META_CONFIG_ID: str = ""  # Facebook Login for Business configuration ID

    # Shopify
    SHOPIFY_API_KEY: str = ""
    SHOPIFY_API_SECRET: str = ""
    SHOPIFY_APP_URL: str = ""  # The URL where the app is hosted (e.g. https://api.visionarias.ai)

    # OpenAI — empty under multibrand brands that route exclusively via LiteLLM
    OPENAI_API_KEY: str = ""

    # DeepSeek (OpenAI-compatible API)
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    # Kimi / Moonshot (OpenAI-compatible API)
    KIMI_API_KEY: str = ""
    KIMI_BASE_URL: str = "https://api.moonshot.ai/v1"

    # Qwen / Alibaba DashScope (OpenAI-compatible intl endpoint)
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_BASE_URL: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

    # --- AI Model Registry ---
    # Each role maps to a concrete model. Override per-role via env vars.
    # NANO defaults to gpt-4o-mini until OpenAI catalog exposes a smaller tier
    # in our deployed envs (override via AI_MODEL_NANO env var).
    AI_MODEL_NANO: str = "gpt-4o-mini"
    AI_MODEL_REASONING: str = "gpt-4o"
    AI_MODEL_FAST: str = "gpt-4o-mini"
    AI_MODEL_VISION: str = "gpt-4o"
    AI_MODEL_AGENT: str = "gpt-4o"
    AI_MODEL_EMBEDDING: str = "text-embedding-3-large"

    def get_model(self, role: ModelRole) -> str:
        """Resolve a semantic role to a concrete model name.

        S4 PR-1 (PI-2): DB-FIRST resolution via LLMConfigService when available.
        Falls back to env vars when service not yet initialized (boot ordering)
        or DB unreachable. Cero breaking change para los 14 callers existentes
        (signature str-returning preservada — D-1 architect).

        Performance: cache hit <1ms p99, miss <5ms (single indexed SELECT).
        Async DB I/O is invoked lazily; sync fast path uses cache only.
        """
        try:
            from luana_core_llm.application.config_service import (
                get_llm_config_service,
            )

            service = get_llm_config_service()
            if service is not None:
                return service.resolve_sync_cached_only(role).model
        except Exception:  # noqa: BLE001 — graceful degradation
            pass
        return self._get_model_from_env(role)

    def _get_model_from_env(self, role: ModelRole) -> str:
        """Pre-S4 PR-1 logic preserved verbatim — env-only resolution."""
        _map = {
            ModelRole.NANO: self.AI_MODEL_NANO,
            ModelRole.REASONING: self.AI_MODEL_REASONING,
            ModelRole.FAST: self.AI_MODEL_FAST,
            ModelRole.VISION: self.AI_MODEL_VISION,
            ModelRole.AGENT: self.AI_MODEL_AGENT,
            ModelRole.EMBEDDING: self.AI_MODEL_EMBEDDING,
        }
        return _map[role]

    def get_provider_for_role(self, role: ModelRole) -> AIProvider:
        """Resolve which provider serves a given role.

        Per-role override (``AI_PROVIDER_<ROLE>``) wins; falls back to global
        ``AI_PROVIDER``. Lets us run e.g. NANO/FAST on OpenAI for low TTFB
        while REASONING/AGENT/HEAVY route to DeepSeek/Kimi for cost.
        """
        _overrides = {
            ModelRole.NANO: self.AI_PROVIDER_NANO,
            ModelRole.REASONING: self.AI_PROVIDER_REASONING,
            ModelRole.FAST: self.AI_PROVIDER_FAST,
            ModelRole.VISION: self.AI_PROVIDER_VISION,
            ModelRole.AGENT: self.AI_PROVIDER_AGENT,
            ModelRole.EMBEDDING: self.AI_PROVIDER_EMBEDDING,
        }
        return _overrides.get(role) or self.AI_PROVIDER

    @property
    def openai_model(self) -> str:
        """Return the default reasoning model name."""
        return self.AI_MODEL_REASONING

    @property
    def openai_fast_model(self) -> str:
        """Return the fast model name."""
        return self.AI_MODEL_FAST

    @property
    def openai_embedding_model(self) -> str:
        """Return the embedding model name."""
        return self.AI_MODEL_EMBEDDING

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-pro"

    # Provider Selection — global default, overridable per-role below.
    AI_PROVIDER: AIProvider = AIProvider.OPENAI  # openai/gemini/deepseek/kimi/qwen

    # Per-role provider override (optional). Empty/unset → fall back to AI_PROVIDER.
    AI_PROVIDER_NANO: AIProvider | None = None
    AI_PROVIDER_REASONING: AIProvider | None = None
    AI_PROVIDER_FAST: AIProvider | None = None
    AI_PROVIDER_VISION: AIProvider | None = None
    AI_PROVIDER_AGENT: AIProvider | None = None
    AI_PROVIDER_EMBEDDING: AIProvider | None = None
    PROMPT_SOURCE: PromptSource = PromptSource.HYBRID  # hybrid, file, db

    # Brand Extraction Profile: "safe" (2-wave, low rate-limit) or "fast" (all-concurrent, high rate-limit)
    BRAND_EXTRACTION_PROFILE: str = "safe"

    # Redis — empty tolerated; get_redis_client() degrades gracefully to None
    REDIS_URL: str = ""  # e.g. redis://redis:6379/0

    # Qdrant — brands may set QDRANT_URL directly, OR QDRANT_HOST/QDRANT_PORT (derived below).
    QDRANT_URL: str = ""  # e.g. http://qdrant:6333 — explicit wins over HOST/PORT
    QDRANT_HOST: str = ""  # e.g. qdrant — engine derives QDRANT_URL from HOST/PORT when URL empty
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = ""  # Optional if running locally without auth, but required for prod
    # Brand-specific — MUST override en {brand}/.env.dev (e.g., visionarias_knowledge for nicolify
    # legacy, vitalia_knowledge, comunify_knowledge, etc.). Engine no asume brand (proposal
    # 2026-05-19). Data isolation crítico (HIPAA-lite, GDPR per brand).
    QDRANT_COLLECTION: str = ""
    QDRANT_COLLECTION_HYBRID: str = ""
    QDRANT_VECTOR_SIZE: int = 3072  # Default for text-embedding-3-large
    QDRANT_SPARSE_MODEL: str = "Qdrant/bm25"  # or "prithivida/Splade_PP_en_v1"

    @model_validator(mode="after")
    def _derive_qdrant_url(self) -> "Settings":
        """Derive QDRANT_URL from QDRANT_HOST/QDRANT_PORT when not set explicitly.

        ESC (2026-06-22): brands configure Qdrant via QDRANT_HOST/QDRANT_PORT but the engine
        vector clients read QDRANT_URL; without reconciliation the URL stays "" →
        QdrantClient(url="") → RAG silently misconfigured. Single canonical accessor:
        explicit QDRANT_URL wins; otherwise compose http://{host}:{port}.
        """
        if not self.QDRANT_URL and self.QDRANT_HOST:
            self.QDRANT_URL = f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"
        return self

    # ── Database ─────────────────────────────────────────────────────────
    # DATABASE_URL is the CANONICAL multibrand env (matches each brand's
    # docker-compose + their own backend/src/db.py). When set it wins over
    # the legacy POSTGRES_* composition (see database_url property). The
    # POSTGRES_* fields are the legacy-standalone fallback only.
    DATABASE_URL: str = ""
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    POSTGRES_HOST: str = ""  # legacy fallback (e.g. postgres)
    POSTGRES_PORT: int = 5432

    # Production Domains
    API_DOMAIN: str = ""
    DASHBOARD_DOMAIN: str = ""
    API_URL: str = ""  # Internal URL for webhooks — set per environment
    UPLOAD_DIR: str = "static/uploads"

    # Storage Provider: "LOCAL" or "R2"
    STORAGE_PROVIDER: str = "LOCAL"

    # Cloudflare Domains (Custom Domains feature)
    CLOUDFLARE_ZONE_ID: str = ""
    CLOUDFLARE_API_TOKEN: str = ""
    CLOUDFLARE_KV_NAMESPACE_ID: str = ""

    # Cloudflare R2
    CLOUDFLARE_ACCOUNT_ID: str = ""
    R2_BUCKET_NAME: str = ""
    R2_ENDPOINT_URL: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_PUBLIC_URL: str = ""  # Public base URL, e.g. https://assets-dev.nicolify.com

    # Clerk
    CLERK_SECRET_KEY: str = ""
    CLERK_WEBHOOK_SECRET: str = ""

    # Tavily (web search for AI agents)
    TAVILY_API_KEY: str = ""

    # Sentry / Environment
    SENTRY_DSN: str = ""
    SENTRY_WORKER_DSN: str = ""  # Workers project DSN — falls back to SENTRY_DSN if empty
    ENVIRONMENT: str = "dev"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.1
    SENTRY_RELEASE: str = "dev"

    # CORS
    CORS_ORIGINS: list[str] = []

    # ── LiteLLM Proxy (PI-2 S3 PR-2) ────────────────────────────────────
    # Endpoint del proxy. Default brand-agnostic = localhost:4000 (post proposal 2026-05-19).
    # Cada brand override en {brand}/.env.dev — production typically:
    #   nicolify: http://visionarias_litellm:4000/v1 (legacy container name)
    #   vitalia/comunify/lupulo: http://luana-{env}-{brand}_litellm-1:4000/v1
    LITELLM_BASE_URL: str = "http://localhost:4000/v1"
    # Master key del proxy. En dev: sk-litellm-master-dev (warning si default).
    # En prod: rotation policy per-environment via secrets manager (Q4 — open).
    LITELLM_MASTER_KEY: str = "sk-litellm-master-dev"
    # Salt key (LiteLLM encrypts stored credentials con este key — cannot
    # change post-deployment without re-keying).
    LITELLM_SALT_KEY: str = "sk-litellm-salt-dev"

    # ── GrowthBook per-tenant LLM override (PI-2 S4 PR-2) ────────────────
    # Self-hosted Docker svc visionarias_growthbook expone API + admin UI.
    # Empty string = disabled (LLMConfigService bypasses GrowthBook eval).
    # Per-tenant override flag scheme: ``llm_model_override_<role_lower>``
    # con value JSON ``{"provider": "openai", "model": "gpt-4o-mini"}``.
    GROWTHBOOK_API_HOST: str = ""
    GROWTHBOOK_CLIENT_KEY: str = ""

    # ── Copilot media + voice limits (PI-2 S1 PR-1) ──────────────────────
    # Applies to /media/upload and /voice/upload-and-transcribe.
    # Per-tenant overrides stored in copilot_tenant_limits table.
    COPILOT_MEDIA_MAX_BYTES: int = 25 * 1024 * 1024  # 25 MiB default
    COPILOT_VOICE_RATE_LIMIT_PER_MIN: int = 6  # requests/min (Q3: cost $0.006/min Whisper x 6 RPM)
    COPILOT_MEDIA_UPLOAD_RATE_LIMIT_PER_MIN: int = 30  # requests/min (Q5: compute BE protection)

    # ── Outbox pattern feature flags (PI-1 S0 PR-1) ───────────────────────
    # Default OFF. Flip per-module after cutover testing.
    # When ON, EventBusAdapter routes publish() to outbox INSERT instead of
    # legacy in-memory dispatch.
    USE_OUTBOX_PATTERN_SALES_AGENT: bool = True
    USE_OUTBOX_PATTERN_COPILOT: bool = True
    USE_OUTBOX_PATTERN_BRAND: bool = True
    USE_OUTBOX_PATTERN_DEFAULT: bool = False

    # Outbox dispatcher
    OUTBOX_MAX_RETRIES: int = 5

    # Idempotency
    IDEMPOTENCY_DEFAULT_TTL_SECONDS: int = 86400

    # Campaign observability retention (PI-1 S0 PR-1)
    CAMPAIGN_TRACE_RETENTION_DAYS: int = 30
    CAMPAIGN_LLM_CALL_RETENTION_DAYS: int = 90

    # PR-8: ventana de reconocimiento inbound de campaña (en horas)
    # Tiempo máximo después de SENT en que un lead que responde se atribuye a la campaña.
    # Default 24h. Hard cap 72h (configuración por tenant en PI-2 si escala).
    CAMPAIGNS_INBOUND_RECOGNITION_WINDOW_HOURS: int = 24

    @field_validator("CAMPAIGNS_INBOUND_RECOGNITION_WINDOW_HOURS")
    @classmethod
    def _validate_inbound_window(cls, v: int) -> int:
        """Valida que la ventana de reconocimiento inbound esté en [1, 72]."""
        if v < 1 or v > 72:
            msg = "CAMPAIGNS_INBOUND_RECOGNITION_WINDOW_HOURS debe estar en [1, 72]"
            raise ValueError(msg)
        return v

    @property
    def database_url(self) -> str:
        """Canonical SYNC PostgreSQL URL (``postgresql://`` scheme).

        Resolution order (multibrand-first):
          1. ``DATABASE_URL`` if set — normalized to the sync scheme so sync
             consumers (``create_engine``) work; async consumers re-add
             ``+asyncpg`` via their existing ``.replace("postgresql://", …)``.
             Brands commonly set the asyncpg form in docker-compose.
          2. else compose from ``POSTGRES_*`` (legacy-standalone env).
          3. else raise — loud at first DB use, never a blanket import-time
             crash (that is the whole point of the multibrand contract).
        """
        if self.DATABASE_URL:
            return re.sub(r"^postgresql\+\w+://", "postgresql://", self.DATABASE_URL)
        if self.POSTGRES_USER and self.POSTGRES_HOST:
            return (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        msg = (
            "No database configured: set DATABASE_URL (multibrand, canonical) "
            "or POSTGRES_USER/HOST/... (legacy-standalone)."
        )
        raise RuntimeError(msg)

    class Config:
        """Pydantic settings configuration."""

        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Return the singleton Settings instance (lazy, created on first call).

    Use this instead of the module-level ``settings`` global.  The @lru_cache
    ensures only one Settings object is ever constructed, identical to the old
    eager singleton — but deferred to first call so that importing this module
    does NOT trigger pydantic-settings env validation at import time.

    This is the T-1 core fix for the brand-mountable copilot unblock.
    """
    return Settings()


def __getattr__(name: str) -> object:
    """Module-level PEP 562 __getattr__ — back-compat shim for legacy callers.

    Callers using ``from luana_core_platform.core.config import settings``
    or ``import luana_core_platform.core.config; config.settings`` continue to
    work but receive a DeprecationWarning.  Migrate to ``get_settings()``
    (T-4 off-path migration).

    NOTE: this shim is intentionally NOT used in the import-path of chat.py
    (those modules are migrated in T-2 to call get_settings() inside functions).
    The shim only saves off-path consumers that run in envs where legacy env
    vars ARE present.
    """
    if name == "settings":
        warnings.warn(
            "luana_core_platform.core.config.settings is deprecated — "
            "usa get_settings() en vez del global `settings`. "
            "Migra los call-sites a get_settings() (T-4 off-path).",
            DeprecationWarning,
            stacklevel=2,
        )
        return get_settings()
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
