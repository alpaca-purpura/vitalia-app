# cap: __shared__
# story-origin: TBD
"""KEKClient — Key Encryption Key management for pgcrypto PHI columns.

Vitalia uses pgcrypto symmetric encryption for PHI columns:
  - treatment_plans.notes
  - re_engagement_events.payload_phi
  - channel_sync_state.oauth_token_encrypted

This client provides the KEK (Key Encryption Key) for pgcrypto operations.

Slice 1 implementation: env-var based (dev/staging).
Prod slot: replace with Vault/KMS adapter (HashiCorp Vault, AWS KMS, or GCP KMS).

NEVER hardcode the key in source code. Key MUST come from:
  - Dev: VITALIA_PHI_KEK env var (32+ byte hex string)
  - Staging: same env var injected via Docker Compose secrets
  - Prod: Vault/KMS provider (slot ready below)

hipaa-lite.md § Encryption at rest:
  "pgcrypto symmetric encryption con KEK rotada anualmente"
  "Backups DB encrypted con key separada (no la misma KEK runtime)"

downstream-regression-na: brand-local encryption key management for vitalia
"""

from __future__ import annotations

import os

import structlog

logger = structlog.get_logger()

# Environment variable name for the PHI encryption key
_KEK_ENV_VAR = "VITALIA_PHI_KEK"

# Minimum key length in bytes (32 bytes = 256-bit AES)
_MIN_KEY_LENGTH_BYTES = 32


class KEKConfigurationError(Exception):
    """Raised when the KEK is not properly configured."""


class KEKClient:
    """Key Encryption Key client for Vitalia PHI column encryption.

    Provides the symmetric key used by pgcrypto for encrypting/decrypting
    PHI columns. Key is loaded from environment variable in Slice 1.

    Prod upgrade path:
        1. Subclass KEKClient and override get_key()
        2. Inject via DI in main.py or as FastAPI dependency
        3. Per hipaa-lite.md: rotate KEK annually

    Usage:
        kek = KEKClient()
        key_hex = kek.get_key()
        # Use in pgcrypto: pgp_sym_encrypt(data, key_hex)
    """

    def __init__(self, env_var: str = _KEK_ENV_VAR) -> None:
        """Initialize the KEKClient.

        Args:
            env_var: Name of the environment variable containing the hex key.
                     Override for testing or multi-tenant key namespacing.
        """
        self._env_var = env_var
        self._cached_key: str | None = None

    def get_key(self) -> str:
        """Return the current KEK as a hex string.

        The key is cached after first read to avoid repeated env var lookups.
        Key rotation requires service restart (Slice 1) or live reload via
        Vault dynamic secrets (prod slot).

        Returns:
            Hex-encoded symmetric key for pgcrypto operations.

        Raises:
            KEKConfigurationError: If env var is not set or key is too short.
        """
        if self._cached_key is not None:
            return self._cached_key

        raw = os.getenv(self._env_var) or os.environ.get(self._env_var)
        if not raw:
            raise KEKConfigurationError(
                f"PHI encryption key not configured. "
                f"Set environment variable {self._env_var!r} to a 32+ byte hex string. "
                f"See vitalia/.claude/rules/hipaa-lite.md § Encryption at rest."
            )

        # Validate minimum key length (hex string → bytes: len/2)
        key_bytes = len(raw) // 2
        if key_bytes < _MIN_KEY_LENGTH_BYTES:
            raise KEKConfigurationError(
                f"PHI encryption key too short: {key_bytes} bytes "
                f"(minimum {_MIN_KEY_LENGTH_BYTES} bytes = 256-bit AES). "
                f'Regenerate with: python3 -c "import secrets; print(secrets.token_hex(32))"'
            )

        self._cached_key = raw
        logger.info(
            "kek_loaded",
            env_var=self._env_var,
            key_length_bytes=key_bytes,
            source="env_var",
        )
        return self._cached_key

    def invalidate_cache(self) -> None:
        """Invalidate the cached key (triggers reload on next get_key() call).

        Used for annual KEK rotation without service restart (prod path).
        """
        self._cached_key = None
        logger.info("kek_cache_invalidated", env_var=self._env_var)

    @classmethod
    def from_env(cls, env_var: str = _KEK_ENV_VAR) -> "KEKClient":
        """Factory method — create a KEKClient from environment variable.

        Args:
            env_var: Name of the environment variable (default: VITALIA_PHI_KEK).

        Returns:
            Configured KEKClient instance.
        """
        return cls(env_var=env_var)
