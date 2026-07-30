"""Tests for ARQ WorkerSettings — validate 15 cron jobs registered per spec.

Validator: be_test_workers_cron (04-validators.yaml)
TDD: RED first — these tests written before arq_settings.py exists.

T-mk-be-6 (2026-05-20): expanded from 11 → 15 cron jobs (4 marketing Wave 3 crons added).

downstream-regression-na: brand-local ARQ worker config; no cross-brand consumers
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Expected cron names from T-infra-8 spec + T-mk-be-6 (verbatim from arq_settings.py)
# ---------------------------------------------------------------------------
EXPECTED_CRON_NAMES = {
    # Fidelización crons (T-infra-8)
    "followup_24h",
    "reactivation_45d",
    "maintenance_90d",
    "deposit_reminder_24h",
    "appointment_reminder_24h",
    "appointment_reminder_2h",
    "nps_request_24h_post_appointment",
    "brand_studio_audit_30d",
    "lucas_weekly_recommendations",
    "channel_sync_state_15min",
    "audit_log_retention_sweep_monthly",
    # Marketing Wave 3 crons (T-mk-be-6)
    "channel_metrics_sync_meta",
    "channel_metrics_sync_google",
    "lucas_daily_analysis_sweep",
    "referrals_value_sync",
}

EXPECTED_FUNCTION_NAMES = {
    # Fidelización crons (T-infra-8)
    "followup_24h",
    "reactivation_45d",
    "maintenance_90d",
    "deposit_reminder_24h",
    "appointment_reminder_24h",
    "appointment_reminder_2h",
    "nps_request_24h_post_appointment",
    "brand_studio_audit_30d",
    "lucas_weekly_recommendations",
    "channel_sync_state_15min",
    "audit_log_retention_sweep_monthly",
    # Marketing Wave 3 crons (T-mk-be-6)
    "channel_metrics_sync_meta",
    "channel_metrics_sync_google",
    "lucas_daily_analysis_sweep",
    "referrals_value_sync",
}


def test_worker_settings_importable() -> None:
    """WorkerSettings should be importable from arq_settings."""
    from src.modules.vitalia._shared.workers.arq_settings import WorkerSettings  # noqa: PLC0415

    assert WorkerSettings is not None


def test_worker_settings_has_15_functions() -> None:
    """WorkerSettings.functions must list all 15 cron job functions (T-infra-8 + T-mk-be-6)."""
    from src.modules.vitalia._shared.workers.arq_settings import WorkerSettings  # noqa: PLC0415

    assert hasattr(WorkerSettings, "functions"), "WorkerSettings must have 'functions' attribute"
    assert len(WorkerSettings.functions) == 15, f"Expected 15 functions, got {len(WorkerSettings.functions)}"


def test_worker_settings_function_names_match_spec() -> None:
    """Each function in WorkerSettings.functions must match expected names."""
    from src.modules.vitalia._shared.workers.arq_settings import WorkerSettings  # noqa: PLC0415

    actual_names = {fn.__name__ for fn in WorkerSettings.functions}
    assert actual_names == EXPECTED_FUNCTION_NAMES, (
        f"Function name mismatch.\nExpected: {sorted(EXPECTED_FUNCTION_NAMES)}\nGot: {sorted(actual_names)}"
    )


def test_worker_settings_has_15_cron_jobs() -> None:
    """WorkerSettings.cron_jobs must have exactly 15 cron entries (T-infra-8 + T-mk-be-6)."""
    from src.modules.vitalia._shared.workers.arq_settings import WorkerSettings  # noqa: PLC0415

    assert hasattr(WorkerSettings, "cron_jobs"), "WorkerSettings must have 'cron_jobs' attribute"
    assert len(WorkerSettings.cron_jobs) == 15, f"Expected 15 cron_jobs, got {len(WorkerSettings.cron_jobs)}"


def test_worker_settings_cron_names_match_spec() -> None:
    """Each cron job name must match expected spec names."""
    from arq.cron import CronJob  # noqa: PLC0415

    from src.modules.vitalia._shared.workers.arq_settings import WorkerSettings  # noqa: PLC0415

    cron_names = set()
    for cron in WorkerSettings.cron_jobs:
        assert isinstance(cron, CronJob), f"Expected CronJob, got {type(cron)}"
        cron_names.add(cron.name)

    assert cron_names == EXPECTED_CRON_NAMES, (
        f"Cron name mismatch.\nExpected: {sorted(EXPECTED_CRON_NAMES)}\nGot: {sorted(cron_names)}"
    )


def test_worker_settings_cron_fns_match_functions() -> None:
    """Each cron job's coroutine function name must be in functions list."""
    from src.modules.vitalia._shared.workers.arq_settings import WorkerSettings  # noqa: PLC0415

    fn_names = {fn.__name__ for fn in WorkerSettings.functions}
    for cron in WorkerSettings.cron_jobs:
        assert cron.name in fn_names, f"Cron job '{cron.name}' has no matching function in WorkerSettings.functions"


def test_worker_settings_redis_settings_defined() -> None:
    """WorkerSettings must define redis_settings."""
    from src.modules.vitalia._shared.workers.arq_settings import WorkerSettings  # noqa: PLC0415

    assert hasattr(WorkerSettings, "redis_settings"), (
        "WorkerSettings must have 'redis_settings' (from env or RedisSettings object)"
    )


def test_worker_settings_keep_result() -> None:
    """WorkerSettings.keep_result should be 3600 (1h per spec)."""
    from src.modules.vitalia._shared.workers.arq_settings import WorkerSettings  # noqa: PLC0415

    assert WorkerSettings.keep_result == 3600, f"keep_result should be 3600 (1h), got {WorkerSettings.keep_result}"


def test_worker_settings_max_jobs() -> None:
    """WorkerSettings.max_jobs should be 50 per spec."""
    from src.modules.vitalia._shared.workers.arq_settings import WorkerSettings  # noqa: PLC0415

    assert WorkerSettings.max_jobs == 50, f"max_jobs should be 50, got {WorkerSettings.max_jobs}"


def test_worker_settings_health_check_interval() -> None:
    """WorkerSettings.health_check_interval should be 30 per spec."""
    from src.modules.vitalia._shared.workers.arq_settings import WorkerSettings  # noqa: PLC0415

    assert WorkerSettings.health_check_interval == 30, (
        f"health_check_interval should be 30, got {WorkerSettings.health_check_interval}"
    )
