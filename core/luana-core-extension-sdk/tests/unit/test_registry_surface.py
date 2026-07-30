"""V-F-sdk-1 — ExtensionPointRegistry exposes 18 register methods.

Per 06-tickets.yaml T-5 + 03-arch-be.md §1.3 step 4 + outcome §7.5.3.
"""

from __future__ import annotations

import inspect

import pytest


def test_extension_point_registry_importable() -> None:
    """Smoke — class importable from package public API."""
    from luana_core_extension_sdk import ExtensionPointRegistry

    assert inspect.isclass(ExtensionPointRegistry)


def test_18_register_methods_exposed() -> None:
    """V-F-sdk-1 — Per outcome §7.5.3 + checkpoint binding_decisions.ep_signatures_summary.

    18 register methods (one per EP-1..EP-18).
    """
    from luana_core_extension_sdk import ExtensionPointRegistry

    expected_register_methods = {
        # EP-1..EP-5 critical
        "field_override",
        "offer_preset_pack_register",
        "sales_agent_tool_register",
        "copilot_workflow_register",
        "scheduling_booking_policy_register",
        # EP-6..EP-18 backlog
        "sidebar_routes_register",
        "extractor_register",
        "channel_adapter_register",
        "metric_register",
        "landing_template_register",
        "campaign_template_register",
        "asset_template_register",
        "sales_agent_guardrail_register",
        "copilot_kb_pack_register",
        "crm_lifecycle_stage_register",
        "iam_signup_handler",
        "tenant_plan_tier_register",
        "onboarding_wizard_steps_register",
    }

    actual_methods = {m for m in dir(ExtensionPointRegistry) if not m.startswith("_")}
    missing = expected_register_methods - actual_methods
    assert not missing, f"Missing register methods: {missing}"


def test_no_unregister_methods_exposed() -> None:
    """V-AG-cc5-no-unregister + CC-5 — Registry immutable post-startup.

    Per outcome §7.5.1 CC-5 "Inmutable post-startup (no unregister_*)".
    """
    from luana_core_extension_sdk import ExtensionPointRegistry

    r = ExtensionPointRegistry()
    unregister_methods = [m for m in dir(r) if m.startswith("unregister")]
    assert not unregister_methods, f"Registry exposes unregister_* methods (CC-5 violation): {unregister_methods}"


def test_close_method_exists_and_locks() -> None:
    """CC-3 — close() locks registry; subsequent registrations raise."""
    from luana_core_extension_sdk import ExtensionPointRegistry
    from luana_core_extension_sdk.exceptions import RegistrationClosedError
    from luana_core_extension_sdk.models import PresetPack

    r = ExtensionPointRegistry()
    assert hasattr(r, "close") and callable(r.close)
    r.close()
    pack = PresetPack(
        name="test-brand.test_pack",
        presets=(),
        applies_to_brand="test-brand",
        description="x",
    )
    with pytest.raises(RegistrationClosedError):
        r.offer_preset_pack_register(pack)


def test_constructor_accepts_optional_adapters() -> None:
    """Per §1.3 step 4 — constructor accepts Optional adapter args."""
    from luana_core_extension_sdk import ExtensionPointRegistry

    # No args — graceful default None
    r1 = ExtensionPointRegistry()
    assert r1 is not None

    # With kwargs — accepts Any (duck typed)
    r2 = ExtensionPointRegistry(
        sales_agent_tool_registry_adapter=None,
        copilot_workflow_registry_adapter=None,
    )
    assert r2 is not None


def test_get_all_introspection_helper_exists() -> None:
    """Test-only API — get_all(ep_id) returns list of _Registration."""
    from luana_core_extension_sdk import ExtensionPointRegistry

    r = ExtensionPointRegistry()
    assert hasattr(r, "get_all") and callable(r.get_all)

    # Empty registry
    assert r.get_all("EP-1") == []
    assert r.get_all("EP-18") == []

    # Invalid EP raises
    with pytest.raises(ValueError, match="Unknown EP"):
        r.get_all("EP-999")
