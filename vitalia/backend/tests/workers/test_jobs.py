"""Tests for the 11 cron job functions (scaffold + implemented).

Validates:
  - Each job module is importable
  - Each job function is exported and async
  - Scaffold jobs raise NotImplementedError with story citation
  - Implemented jobs exist and accept ctx param (no NotImplementedError check)

T-be-services-3 (2026-05-18): lucas_weekly_recommendations moved from scaffold to
implemented — removed from NotImplementedError checks.

downstream-regression-na: brand-local cron job scaffolds; no cross-brand consumers
"""

from __future__ import annotations

import inspect

import pytest

# ---------------------------------------------------------------------------
# Jobs that have been fully implemented (no longer raise NotImplementedError).
# Updated: T-be-services-3 (2026-05-18) — lucas_weekly_recommendations implemented.
# ---------------------------------------------------------------------------
IMPLEMENTED_JOBS: set[str] = {
    "lucas_weekly_recommendations",
}

# ---------------------------------------------------------------------------
# Expected jobs: (module_path, fn_name, story_cite_pattern)
# story_cite_pattern is a regex checked against the NotImplementedError message
# (only relevant for scaffold/unimplemented jobs)
# ---------------------------------------------------------------------------
JOB_EXPECTATIONS = [
    (
        "src.modules.vitalia._shared.workers.jobs.followup_24h",
        "followup_24h",
        r"fidelizaci[oó]n|T-fidelizacion",
    ),
    (
        "src.modules.vitalia._shared.workers.jobs.reactivation_45d",
        "reactivation_45d",
        r"fidelizaci[oó]n|T-fidelizacion",
    ),
    (
        "src.modules.vitalia._shared.workers.jobs.maintenance_90d",
        "maintenance_90d",
        r"fidelizaci[oó]n|copilot|T-",
    ),
    (
        "src.modules.vitalia._shared.workers.jobs.deposit_reminder_24h",
        "deposit_reminder_24h",
        r"agenda|T-agenda",
    ),
    (
        "src.modules.vitalia._shared.workers.jobs.appointment_reminder_24h",
        "appointment_reminder_24h",
        r"agenda|T-agenda",
    ),
    (
        "src.modules.vitalia._shared.workers.jobs.appointment_reminder_2h",
        "appointment_reminder_2h",
        r"agenda|T-agenda",
    ),
    (
        "src.modules.vitalia._shared.workers.jobs.nps_request_24h_post_appointment",
        "nps_request_24h_post_appointment",
        r"fidelizaci[oó]n|T-fidelizacion",
    ),
    (
        "src.modules.vitalia._shared.workers.jobs.brand_studio_audit_30d",
        "brand_studio_audit_30d",
        r"marketing|T-marketing",
    ),
    (
        "src.modules.vitalia._shared.workers.jobs.lucas_weekly_recommendations",
        "lucas_weekly_recommendations",
        r"copilot|lucas|T-copilot",
    ),
    (
        "src.modules.vitalia._shared.workers.jobs.channel_sync_state_15min",
        "channel_sync_state_15min",
        r"inbox|T-inbox",
    ),
    (
        "src.modules.vitalia._shared.workers.jobs.audit_log_retention_sweep_monthly",
        "audit_log_retention_sweep_monthly",
        r"infra|hipaa|retention|T-infra",
    ),
]


@pytest.mark.parametrize(
    "module_path,fn_name,story_pattern",
    JOB_EXPECTATIONS,
    ids=[e[1] for e in JOB_EXPECTATIONS],
)
def test_job_module_importable(
    module_path: str,
    fn_name: str,
    story_pattern: str,
) -> None:
    """Each job module must be importable."""
    import importlib  # noqa: PLC0415

    mod = importlib.import_module(module_path)
    assert mod is not None


@pytest.mark.parametrize(
    "module_path,fn_name,story_pattern",
    JOB_EXPECTATIONS,
    ids=[e[1] for e in JOB_EXPECTATIONS],
)
def test_job_function_exists(
    module_path: str,
    fn_name: str,
    story_pattern: str,
) -> None:
    """Each job module must export an async function with the expected name."""
    import importlib  # noqa: PLC0415

    mod = importlib.import_module(module_path)
    fn = getattr(mod, fn_name, None)

    assert fn is not None, f"Function '{fn_name}' not found in module '{module_path}'"
    assert inspect.iscoroutinefunction(fn), f"Function '{fn_name}' must be async (iscoroutinefunction), got {type(fn)}"


@pytest.mark.parametrize(
    "module_path,fn_name,story_pattern",
    [e for e in JOB_EXPECTATIONS if e[1] not in IMPLEMENTED_JOBS],
    ids=[e[1] for e in JOB_EXPECTATIONS if e[1] not in IMPLEMENTED_JOBS],
)
@pytest.mark.asyncio
async def test_job_raises_not_implemented(
    module_path: str,
    fn_name: str,
    story_pattern: str,
) -> None:
    """Each scaffold (not yet implemented) job must raise NotImplementedError when called."""
    import importlib  # noqa: PLC0415

    mod = importlib.import_module(module_path)
    fn = getattr(mod, fn_name)

    ctx: dict = {"job_id": "test-id"}
    with pytest.raises(NotImplementedError):
        await fn(ctx)


@pytest.mark.parametrize(
    "module_path,fn_name,story_pattern",
    [e for e in JOB_EXPECTATIONS if e[1] not in IMPLEMENTED_JOBS],
    ids=[e[1] for e in JOB_EXPECTATIONS if e[1] not in IMPLEMENTED_JOBS],
)
@pytest.mark.asyncio
async def test_job_not_implemented_cites_story(
    module_path: str,
    fn_name: str,
    story_pattern: str,
) -> None:
    """NotImplementedError message must cite the originating story/ticket (scaffold jobs only)."""
    import importlib  # noqa: PLC0415
    import re  # noqa: PLC0415

    mod = importlib.import_module(module_path)
    fn = getattr(mod, fn_name)

    ctx: dict = {"job_id": "test-id"}
    with pytest.raises(NotImplementedError) as exc_info:
        await fn(ctx)

    message = str(exc_info.value)
    assert re.search(story_pattern, message, re.IGNORECASE), (
        f"NotImplementedError for '{fn_name}' should cite story matching pattern '{story_pattern}', got: '{message}'"
    )


@pytest.mark.parametrize(
    "module_path,fn_name,story_pattern",
    JOB_EXPECTATIONS,
    ids=[e[1] for e in JOB_EXPECTATIONS],
)
def test_job_function_accepts_ctx_param(
    module_path: str,
    fn_name: str,
    story_pattern: str,
) -> None:
    """Each job function must accept a single 'ctx' parameter (ARQ convention)."""
    import importlib  # noqa: PLC0415

    mod = importlib.import_module(module_path)
    fn = getattr(mod, fn_name)

    sig = inspect.signature(fn)
    params = list(sig.parameters.keys())

    assert "ctx" in params, f"Function '{fn_name}' must have a 'ctx' parameter (ARQ convention). Found params: {params}"
