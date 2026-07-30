# cap: __shared__
"""T-1 verificación-por-efecto: importar config.py + database.py NO instancia
Settings ni crea el engine/redis a module-load.

RED fase: este test FALLA contra el código original (eager global `settings = Settings()`
y `_async_url = settings.database_url` en database.py).
GREEN fase: pasa una vez que config.py + database.py son lazy (@lru_cache).
"""

from __future__ import annotations

import sys
import warnings

import pytest


def _remove_platform_modules() -> None:
    """Remove all luana_core_platform.core.* modules from sys.modules so we get
    a clean import state for each test. This lets us test the module-load side-effect
    isolation that is the core invariant of T-1."""
    to_remove = [
        k
        for k in list(sys.modules)
        if k.startswith("luana_core_platform.core.config")
        or k.startswith("luana_core_platform.core.database")
        or k.startswith("luana_core_platform.core.rate_limit")
    ]
    for mod in to_remove:
        sys.modules.pop(mod, None)


class TestLazySettingsNoEager:
    """Invariant: importing config + database modules NEVER instantiates Settings
    or creates async/sync engine or redis client at module-load time."""

    def test_import_config_does_not_call_settings_init(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Importing luana_core_platform.core.config MUST NOT call Settings.__init__.

        Mechanism: monkeypatch Settings.__init__ to raise RuntimeError if called
        during import. Then import the module. If the original eager
        `settings = Settings()` still exists at module-scope, the import
        raises RuntimeError and the test fails (RED against original code).
        After the fix (get_settings() lazy + __getattr__ shim), the import
        succeeds and get_settings.cache_info().currsize == 0 (never called yet).
        """
        _remove_platform_modules()

        # Monkeypatch Settings.__init__ BEFORE importing — patch on the class
        # via the module so it fires during module-load too.
        # We patch pydantic_settings.BaseSettings.__init__ to detect eager init.
        import pydantic_settings

        init_called: list[str] = []

        original_init = pydantic_settings.BaseSettings.__init__

        def _spy_init(self_inner, *args, **kwargs):  # noqa: ANN001
            init_called.append(type(self_inner).__name__)
            return original_init(self_inner, *args, **kwargs)

        monkeypatch.setattr(pydantic_settings.BaseSettings, "__init__", _spy_init)

        _remove_platform_modules()
        import luana_core_platform.core.config  # noqa: F401 — import side-effect test

        # After import, Settings.__init__ must NOT have been called.
        # If the old `settings = Settings()` line is still there, init_called == ['Settings'].
        assert init_called == [], (
            f"Settings.__init__ was called at module-load time: {init_called}. "
            "This means config.py still has eager `settings = Settings()`. "
            "Implement get_settings() + __getattr__ shim to fix (T-1 Pieza 1)."
        )

    def test_get_settings_lru_cache_not_called_on_import(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """After importing config, get_settings() cache must show 0 calls (never invoked)."""
        _remove_platform_modules()

        # Set minimal multibrand-only env (no legacy POSTGRES_*/WHATSAPP_*/QDRANT_URL)
        # so that if get_settings() IS called lazily, it would still work.
        # We only assert it hasn't been called yet.

        from luana_core_platform.core.config import get_settings

        cache_info = get_settings.cache_info()
        assert cache_info.currsize == 0, (
            f"get_settings() was called during import (currsize={cache_info.currsize}). "
            "The function is lazy but something triggered it at import time."
        )

    def test_import_database_does_not_create_engine_or_redis(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Importing database.py MUST NOT call create_engine, create_async_engine,
        or redis.from_url at module-load time.

        Mechanism: monkeypatch all three factory calls to record invocations.
        If the original eager module-level code exists, they fire during import (RED).
        After the fix (lazy @lru_cache functions), imports are clean (GREEN).
        """
        _remove_platform_modules()

        import sqlalchemy
        import sqlalchemy.ext.asyncio

        calls: list[str] = []

        original_create_engine = sqlalchemy.create_engine
        original_create_async_engine = sqlalchemy.ext.asyncio.create_async_engine

        def _spy_create_engine(*args, **kwargs):
            calls.append("create_engine")
            return original_create_engine(*args, **kwargs)

        def _spy_create_async_engine(*args, **kwargs):
            calls.append("create_async_engine")
            return original_create_async_engine(*args, **kwargs)

        monkeypatch.setattr(sqlalchemy, "create_engine", _spy_create_engine)
        monkeypatch.setattr(
            sqlalchemy.ext.asyncio,
            "create_async_engine",
            _spy_create_async_engine,
        )

        # Also spy redis.from_url
        import redis as redis_mod

        original_from_url = redis_mod.from_url

        def _spy_from_url(*args, **kwargs):
            calls.append("redis.from_url")
            return original_from_url(*args, **kwargs)

        monkeypatch.setattr(redis_mod, "from_url", _spy_from_url)

        # Now import database — must not call any of the above
        _remove_platform_modules()

        # We need to set env so that if the shim triggers settings on import,
        # it at least resolves. But with the correct implementation, settings
        # is NOT triggered.
        import luana_core_platform.core.database  # noqa: F401

        assert calls == [], (
            f"database.py called {calls} at module-load time. "
            "This means the engine/redis creation is still eager. "
            "Implement get_async_engine()/get_engine()/get_redis_client() "
            "@lru_cache lazy functions to fix (T-1 Pieza 2)."
        )

    def test_lazy_functions_exported_from_database(self) -> None:
        """After the fix, database.py MUST export the lazy accessor functions."""
        import luana_core_platform.core.database as db

        assert hasattr(db, "get_async_engine"), "database.py must export get_async_engine() lazy function"
        assert hasattr(db, "get_engine"), "database.py must export get_engine() lazy function"
        assert hasattr(db, "get_redis_client"), "database.py must export get_redis_client() lazy function"
        assert callable(db.get_async_engine), "get_async_engine must be callable"
        assert callable(db.get_engine), "get_engine must be callable"
        assert callable(db.get_redis_client), "get_redis_client must be callable"

    def test_get_settings_exported_from_config(self) -> None:
        """After the fix, config.py MUST export get_settings() with @lru_cache."""
        from luana_core_platform.core.config import get_settings

        assert callable(get_settings), "get_settings must be callable"
        # Must have lru_cache interface
        assert hasattr(get_settings, "cache_info"), "get_settings must be decorated with @lru_cache"
        assert hasattr(get_settings, "cache_clear"), "get_settings must be decorated with @lru_cache"

    def test_shim_getattr_emits_deprecation_warning(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The module-level __getattr__('settings') shim must emit DeprecationWarning.

        This verifies back-compat: off-path consumers using
        `from luana_core_platform.core.config import settings`
        still work BUT get a deprecation warning (semver minor).
        """
        _remove_platform_modules()

        import luana_core_platform.core.config as cfg_mod

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            # Access the 'settings' attribute via module __getattr__ shim
            s = cfg_mod.settings  # noqa: F841 — testing side-effect

        deprecation_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert len(deprecation_warnings) >= 1, (
            "Accessing config.settings must emit DeprecationWarning via __getattr__ shim. "
            "The shim is needed for back-compat during transition (semver minor)."
        )
        warning_text = str(deprecation_warnings[0].message)
        assert "get_settings" in warning_text.lower() or "deprecat" in warning_text.lower(), (
            f"DeprecationWarning message should reference get_settings(), got: {warning_text}"
        )
