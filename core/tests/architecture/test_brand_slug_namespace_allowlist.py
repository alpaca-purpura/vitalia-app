"""Architecture fitness: brand slug namespace allowlist enforcement (CC-4).

V-AG-namespace-allowlist. ExtensionPointRegistry enforces CC-4 — only
explicitly allowlisted brand slugs may register extensions.

Tests:
- Bare name (no brand slug prefix) → NamespaceViolationError
- Unknown brand slug prefix → NamespaceViolationError
- Valid brand slug prefix → registers without error

Allowlisted slugs (Story 8 v0.1.0): nicolify, vitalia, comunify, lupulo, test-brand.
"""

from __future__ import annotations

import pytest
from luana_core_extension_sdk import ExtensionPointRegistry
from luana_core_extension_sdk.exceptions import NamespaceViolationError
from luana_core_extension_sdk.models import SidebarRouteDef


def _fresh_registry() -> ExtensionPointRegistry:
    return ExtensionPointRegistry(
        sales_agent_tool_registry_adapter=None,
        copilot_workflow_registry_adapter=None,
    )


_VALID_BRAND_SLUGS = ["nicolify", "vitalia", "comunify", "lupulo", "test-brand"]

_INVALID_NAMES = [
    "smoke_route",  # bare name — no prefix
    "unknown-brand.smoke",  # unregistered brand slug
    "VITALIA.smoke",  # wrong case (should be lowercase)
    "vitalia-extra.smoke",  # slug not in allowlist
    ".smoke_route",  # empty prefix
]


def test_bare_name_raises_namespace_violation() -> None:
    """CC-4: bare name without brand slug prefix raises NamespaceViolationError."""
    registry = _fresh_registry()
    with pytest.raises(NamespaceViolationError):
        registry.sidebar_routes_register(SidebarRouteDef(slug="no_prefix", label="No prefix", icon="x", order=1))


def test_unknown_brand_slug_raises_namespace_violation() -> None:
    """CC-4: unrecognized brand slug prefix raises NamespaceViolationError."""
    registry = _fresh_registry()
    with pytest.raises(NamespaceViolationError):
        registry.sidebar_routes_register(
            SidebarRouteDef(
                slug="unknown-brand.smoke",
                label="Unknown",
                icon="x",
                order=1,
            )
        )


@pytest.mark.parametrize("brand_slug", _VALID_BRAND_SLUGS)
def test_valid_brand_slug_prefix_succeeds(brand_slug: str) -> None:
    """CC-4: all allowlisted brand slugs can register without error."""
    registry = _fresh_registry()
    # Use sidebar route — EP-6 stub accepts DataClass registration without dispatch
    registry.sidebar_routes_register(
        SidebarRouteDef(
            slug=f"{brand_slug}.test_route",
            label="Test",
            icon="zap",
            order=99,
        )
    )
    # Verify it was recorded (get_all returns _Registration objects with .payload)
    registered = registry.get_all("EP-6")
    assert len(registered) == 1
    assert registered[0].payload.slug == f"{brand_slug}.test_route"


@pytest.mark.parametrize("invalid_name", _INVALID_NAMES)
def test_invalid_names_raise_namespace_violation(invalid_name: str) -> None:
    """CC-4: invalid names (bare, wrong slug, wrong case) raise NamespaceViolationError."""
    registry = _fresh_registry()
    with pytest.raises(NamespaceViolationError, match="namespace"):
        registry.sidebar_routes_register(SidebarRouteDef(slug=invalid_name, label="X", icon="x", order=1))
