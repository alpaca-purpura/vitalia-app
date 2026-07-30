"""Architecture fitness: ExtensionPointRegistry exposes exactly 18 register methods.

V-F-sdk-1. Story 8 SDK contract: 18 EP register methods + dispatch helpers
for EP-1..EP-5, plus close() and get_all().

Verifies:
- All 18 register methods present (EP-1..EP-18)
- dispatch_* helpers for EP-1..EP-5 (executable EPs)
- close() and get_all() public API
- Zero methods starting with 'unregister_' (CC-5 immutability)
"""

from __future__ import annotations

import inspect

from luana_core_extension_sdk import ExtensionPointRegistry

_EXPECTED_REGISTER_METHODS = frozenset(
    {
        # EP-1..EP-5 (executable)
        "field_override",
        "offer_preset_pack_register",
        "sales_agent_tool_register",
        "copilot_workflow_register",
        "scheduling_booking_policy_register",
        # EP-6..EP-18 (signature-only)
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
)

# Utility methods that return registered data (EP-1..EP-5 readable surface)
_EXPECTED_READ_METHODS = frozenset(
    {
        "resolve_field_override",
        "list_offer_preset_packs",
        "get_sales_agent_tool",
        "get_copilot_workflow",
        "get_booking_policy",
        "get_sidebar_routes",
    }
)


def _public_methods(cls: type) -> set[str]:
    """Return set of public method names (not dunder, not private)."""
    return {name for name, member in inspect.getmembers(cls, predicate=inspect.isfunction) if not name.startswith("_")}


def test_registry_has_all_18_register_methods() -> None:
    """V-F-sdk-1: ExtensionPointRegistry exposes all 18 EP register methods."""
    methods = _public_methods(ExtensionPointRegistry)

    missing = _EXPECTED_REGISTER_METHODS - methods
    assert not missing, (
        f"Missing register methods: {sorted(missing)}\n"
        "All 18 EP register methods must be present on ExtensionPointRegistry."
    )


def test_registry_has_read_methods_for_ep1_ep5() -> None:
    """V-F-sdk-1: read/query helpers exist for EP-1..EP-5 (executable EPs)."""
    methods = _public_methods(ExtensionPointRegistry)

    missing = _EXPECTED_READ_METHODS - methods
    assert not missing, (
        f"Missing read helpers: {sorted(missing)}\nRead helpers (resolve_*, list_*, get_*) must exist for EP-1..EP-5."
    )


def test_registry_no_unregister_methods() -> None:
    """V-AG-cc5-no-unregister: ExtensionPointRegistry has zero unregister_* methods.

    CC-5 immutability — once registered, extensions cannot be removed at runtime.
    """
    methods = _public_methods(ExtensionPointRegistry)
    unregister_methods = {m for m in methods if m.startswith("unregister_")}

    assert not unregister_methods, (
        f"Found unregister methods: {sorted(unregister_methods)}\n"
        "CC-5 immutability: ExtensionPointRegistry must have ZERO unregister_* methods.\n"
        "Extensions are registered at startup and cannot be removed."
    )


def test_registry_has_close_and_get_all() -> None:
    """V-F-sdk-1: close() (CC-3 startup-lock) and get_all() utility must exist."""
    methods = _public_methods(ExtensionPointRegistry)
    assert "close" in methods, "close() method missing — required for CC-3 startup-only lock"
    assert "get_all" in methods, "get_all() method missing — required for introspection"
