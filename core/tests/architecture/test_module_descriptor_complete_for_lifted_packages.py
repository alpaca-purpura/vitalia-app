"""Architecture fitness: ModuleDescriptor entries complete for lifted Stories 2-5 packages.

Per 03-arch.md §7.6 + D-T6 cement. After `discover_providers()` runs,
the module registry MUST contain entries for every lifted package
exposing a `copilot_provider/`:

- brand (Story 5)
- offer (Story 5)
- crm (Story 4)
- analytics (Story 4)
- landing (Story 4)
- connections (Story 4)
- commercial_calendar (Story 3)
- social_proof (Story 3)

Each ModuleDescriptor must have populated fields: `module_id`, `label`,
`description`, `route_prefix`.

Discovery wiring uses entry-points (`nicolify.copilot_providers` group)
declared in each package's pyproject.toml. The convention-scan fallback
(``src.modules.*`` filesystem walk) returns empty in luana-platform
context — entry-points is the sole transport.

V-AG-6 validator.
"""

from __future__ import annotations

import pytest

EXPECTED_MODULE_IDS = {
    "brand",
    "offer",
    "crm",
    "analytics",
    "landing",
    "connections",
    "commercial_calendar",
    "social_proof",
}


@pytest.fixture(autouse=True)
def reset_discovery_cache():
    """Reset module registry + discovery cache between tests."""
    from luana_core_copilot.application.discovery import reset_discovery
    from luana_core_copilot.domain.module_registry import reset_module_registry_cache

    reset_discovery()
    reset_module_registry_cache()
    yield
    reset_discovery()
    reset_module_registry_cache()


def test_discovery_finds_all_lifted_providers():
    """`discover_providers()` returns providers for all 8 Stories 2-5 packages."""
    from luana_core_copilot.application.discovery import discover_providers

    providers = discover_providers()
    found_ids = set(providers.keys())
    missing = EXPECTED_MODULE_IDS - found_ids

    assert not missing, (
        "V-AG-6 D-T6 cement violation: not all lifted copilot_providers "
        "discovered via entry-points.\n"
        f"Expected: {sorted(EXPECTED_MODULE_IDS)}\n"
        f"Found:    {sorted(found_ids)}\n"
        f"Missing:  {sorted(missing)}\n\n"
        "Check each missing package's pyproject.toml — must declare:\n"
        '  [project.entry-points."nicolify.copilot_providers"]\n'
        '  <module_id> = "<py_pkg>.copilot_provider:provider"',
    )


def test_module_registry_complete_for_lifted_packages():
    """`get_module_registry()` returns ModuleDescriptor for all 8 lifted packages.

    Note: some providers may return `module_data() is None` (e.g. analytics
    uses SQL queries, not Pydantic introspection) — those still appear in
    `discover_providers()` but NOT in `get_module_registry()`.
    """
    from luana_core_copilot.domain.module_registry import get_module_registry

    registry = get_module_registry()
    found_ids = set(registry.keys())
    missing = EXPECTED_MODULE_IDS - found_ids

    assert not missing, (
        "V-AG-6 D-T6 cement violation: module_registry missing entries.\n"
        f"Expected: {sorted(EXPECTED_MODULE_IDS)}\n"
        f"Found:    {sorted(found_ids)}\n"
        f"Missing:  {sorted(missing)}\n\n"
        "If a provider intentionally returns module_data()=None, it should still "
        "be discoverable but won't appear in module_registry. Adjust EXPECTED_MODULE_IDS "
        "in this test to exclude such providers if applicable.",
    )


def test_module_descriptor_fields_populated():
    """Each ModuleDescriptor has populated required fields."""
    from luana_core_copilot.domain.module_registry import get_module_registry

    registry = get_module_registry()
    incomplete: list[str] = []

    required_fields = ("module_id", "label", "description", "route_prefix")

    for module_id, descriptor in registry.items():
        for field in required_fields:
            value = getattr(descriptor, field, None)
            if not value or not isinstance(value, str):
                incomplete.append(f"{module_id}.{field} = {value!r}")

    assert not incomplete, (
        "V-AG-6 D-T6 cement violation: ModuleDescriptor required fields not populated.\n"
        "Required: module_id, label, description, route_prefix.\n\n"
        "Incomplete:\n" + "\n".join(incomplete)
    )
