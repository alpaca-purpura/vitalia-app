"""Tests for BrandContext frozen dataclass — V-F-sdk-5.

TDD: these tests are written FIRST (RED phase before brand_context.py exists).
"""

from __future__ import annotations


def test_brand_context_frozen():
    """BrandContext must be immutable (frozen=True dataclass)."""

    from luana_core_extension_sdk.brand_context import BrandContext

    assert BrandContext.__dataclass_params__.frozen is True


def test_brand_context_9_fields():
    """BrandContext must have exactly 9 fields per §7.5.2 D3."""
    from dataclasses import fields

    from luana_core_extension_sdk.brand_context import BrandContext

    names = {f.name for f in fields(BrandContext)}
    expected = {
        "tenant_id",
        "brand_slug",
        "plan_tier",
        "locale",
        "feature_flags",
        "tenant_profile_id",
        "vertical_kind",
        "compliance_flags",
        "pii_policy",
    }
    assert names == expected


def test_brand_context_mutation_raises():
    """Mutation on frozen BrandContext must raise FrozenInstanceError (CC-5 immutable)."""
    import dataclasses
    from uuid import uuid4

    from luana_core_extension_sdk.brand_context import BrandContext

    ctx = BrandContext(
        tenant_id=uuid4(),
        brand_slug="test-brand",
        plan_tier="free",
        locale="es-AR",
        feature_flags={},
        tenant_profile_id=uuid4(),
        vertical_kind="marketing",
        compliance_flags={},
        pii_policy="standard",
    )
    try:
        ctx.tenant_id = uuid4()  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        pass
    else:
        raise AssertionError("Expected FrozenInstanceError")


def test_brand_context_no_pii_safe_to_log():
    """All 9 fields are IDs + slugs + flag maps + locale strings — none are PII.

    Per §7.2 spec — BrandContext can be safely included in trace logs.
    """
    import dataclasses
    from uuid import uuid4

    from luana_core_extension_sdk.brand_context import BrandContext

    ctx = BrandContext(
        tenant_id=uuid4(),
        brand_slug="test-brand",
        plan_tier="free",
        locale="es-AR",
        feature_flags={},
        tenant_profile_id=uuid4(),
        vertical_kind="marketing",
        compliance_flags={},
        pii_policy="standard",
    )
    # No email / phone / address / DOB attributes
    field_names = {f.name for f in dataclasses.fields(ctx)}
    pii_patterns = {"email", "phone", "address", "dob", "birth", "ssn", "card"}
    leaks = [f for f in field_names for p in pii_patterns if p in f.lower()]
    assert not leaks
