"""V-F-sdk-4 — CC-1..CC-5 cross-cutting policies enforced at runtime.

Per 01-spec §5.4 scenarios C1-C5 + outcome §7.5.1 + 06-tickets.yaml T-5.

Cross-cutting policies (verbatim from outcome §7.5.1):
- CC-1 Signature pattern per-EP natural (data → DataClass, behavior → Callable)
- CC-2 Default append + override case-by-case via mode flag
- CC-3 Startup-only registration universal
- CC-4 Strict raise on duplicate + namespaced obligatorio (brand_slug prefix)
- CC-5 Inmutable post-startup (no unregister_*)
"""

from __future__ import annotations

import pytest
from luana_core_extension_sdk import (
    ExtensionPointRegistry,
    PlanTierDef,
    PresetPack,
    WizardStepDef,
)
from luana_core_extension_sdk.exceptions import (
    DuplicateRegistrationError,
    NamespaceViolationError,
    RegistrationClosedError,
)

# ─────────────────────────────────────────────────────────────────────
# C1 — Duplicate registration raises (CC-4)
# ─────────────────────────────────────────────────────────────────────


def test_c1_duplicate_registration_raises() -> None:
    """Second register with same name + same EP → DuplicateRegistrationError."""
    r = ExtensionPointRegistry()

    pack = PresetPack(
        name="test-brand.duplicate_pack",
        presets=(),
        applies_to_brand="test-brand",
    )
    r.offer_preset_pack_register(pack)

    with pytest.raises(DuplicateRegistrationError, match="already registered"):
        r.offer_preset_pack_register(pack)


def test_c1_same_name_different_ep_ok() -> None:
    """Same name across DIFFERENT EPs is allowed (uniqueness scoped per-EP)."""
    from luana_core_extension_sdk import (
        SidebarRouteDef,
    )

    r = ExtensionPointRegistry()

    # EP-2
    pack = PresetPack(
        name="test-brand.shared_name",
        presets=(),
        applies_to_brand="test-brand",
    )
    r.offer_preset_pack_register(pack)

    # EP-6 with same name (different EP) — allowed
    route = SidebarRouteDef(
        slug="test-brand.shared_name",
        label="Shared",
        icon="x",
    )
    r.sidebar_routes_register(route)

    assert len(r.get_all("EP-2")) == 1
    assert len(r.get_all("EP-6")) == 1


# ─────────────────────────────────────────────────────────────────────
# C2 — Namespace violation raises (CC-4)
# ─────────────────────────────────────────────────────────────────────


def test_c2_bare_name_without_brand_prefix_raises() -> None:
    """Name without `{brand_slug}.` prefix → NamespaceViolationError."""
    r = ExtensionPointRegistry()

    pack = PresetPack(
        name="bare_name_no_prefix",  # ← violates CC-4
        presets=(),
        applies_to_brand="test-brand",
    )
    with pytest.raises(NamespaceViolationError, match="must be namespaced"):
        r.offer_preset_pack_register(pack)


def test_c2_unknown_brand_slug_raises() -> None:
    """Brand slug not in allowlist → NamespaceViolationError."""
    r = ExtensionPointRegistry()

    pack = PresetPack(
        name="acme-corp.my_pack",  # ← acme-corp not in allowlist
        presets=(),
        applies_to_brand="test-brand",
    )
    with pytest.raises(NamespaceViolationError, match="Accepted prefixes"):
        r.offer_preset_pack_register(pack)


def test_c2_valid_brand_slug_succeeds() -> None:
    """All 5 allowlisted brand slugs accept registrations."""
    for brand in ("nicolify", "vitalia", "comunify", "lupulo", "test-brand"):
        r = ExtensionPointRegistry()
        pack = PresetPack(
            name=f"{brand}.test_pack",
            presets=(),
            applies_to_brand=brand,
        )
        r.offer_preset_pack_register(pack)
        assert len(r.get_all("EP-2")) == 1


# ─────────────────────────────────────────────────────────────────────
# C3 — Startup-only registration (CC-3)
# ─────────────────────────────────────────────────────────────────────


def test_c3_post_close_registration_raises() -> None:
    """After registry.close(), all register_* methods raise RegistrationClosedError."""
    r = ExtensionPointRegistry()
    r.close()

    pack = PresetPack(name="test-brand.x", presets=(), applies_to_brand="test-brand")
    with pytest.raises(RegistrationClosedError, match="CC-3"):
        r.offer_preset_pack_register(pack)


def test_c3_close_is_idempotent() -> None:
    """Calling close() twice is safe (CC-3 lock idempotent)."""
    r = ExtensionPointRegistry()
    r.close()
    r.close()  # No exception


# ─────────────────────────────────────────────────────────────────────
# C4 — Inmutable post-startup (CC-5)
# ─────────────────────────────────────────────────────────────────────


def test_c4_no_unregister_field_override_method() -> None:
    """Per CC-5 — no unregister_* methods anywhere."""
    r = ExtensionPointRegistry()
    assert not hasattr(r, "unregister_field_override")
    assert not hasattr(r, "unregister_offer_preset_pack")
    assert not hasattr(r, "unregister")


def test_c4_no_methods_starting_with_unregister() -> None:
    """Class introspection — no public/private unregister_* methods."""
    r = ExtensionPointRegistry()
    methods = [m for m in dir(r) if "unregister" in m.lower()]
    assert not methods, f"CC-5 violation: {methods}"


# ─────────────────────────────────────────────────────────────────────
# C5 — Override mode restricted to EP-17 + EP-18 only (CC-2)
# ─────────────────────────────────────────────────────────────────────


def test_c5a_override_mode_on_ep1_raises() -> None:
    """EP-1 does NOT permit mode='override'."""
    r = ExtensionPointRegistry()

    def handler(field, ctx):
        return None

    with pytest.raises(ValueError, match="does not support mode='override'"):
        r.field_override(handler, name="test-brand.h", mode="override")


def test_c5b_override_mode_on_ep17_succeeds() -> None:
    """EP-17 tenant_plan_tier_register permits mode='override'."""
    r = ExtensionPointRegistry()

    tier1 = PlanTierDef(
        tier_id="test-brand.free",
        label="Free v1",
        price_monthly=0.0,
        currency="USD",
        features=("basic",),
    )
    r.tenant_plan_tier_register(tier1)
    assert len(r.get_all("EP-17")) == 1

    # Override replaces (default mode would raise duplicate)
    tier2 = PlanTierDef(
        tier_id="test-brand.free",
        label="Free v2",
        price_monthly=0.0,
        currency="USD",
        features=("basic", "extra"),
    )
    r.tenant_plan_tier_register(tier2, mode="override")
    all_eps = r.get_all("EP-17")
    assert len(all_eps) == 1
    assert all_eps[0].payload.label == "Free v2"


def test_c5c_override_mode_on_ep18_succeeds() -> None:
    """EP-18 onboarding_wizard_steps_register permits mode='override'."""
    r = ExtensionPointRegistry()

    step1 = WizardStepDef(
        step_id="test-brand.welcome",
        title="Welcome v1",
        component_ref="WelcomeStep",
    )
    r.onboarding_wizard_steps_register(step1)

    step2 = WizardStepDef(
        step_id="test-brand.welcome",
        title="Welcome v2",
        component_ref="WelcomeStep",
    )
    r.onboarding_wizard_steps_register(step2, mode="override")

    eps = r.get_all("EP-18")
    assert len(eps) == 1
    assert eps[0].payload.title == "Welcome v2"


def test_c5d_invalid_mode_raises() -> None:
    """Any mode other than 'append'/'override' → ValueError."""
    r = ExtensionPointRegistry()
    tier = PlanTierDef(
        tier_id="test-brand.x",
        label="x",
        price_monthly=0.0,
        currency="USD",
        features=(),
    )
    with pytest.raises(ValueError, match="Invalid mode"):
        r.tenant_plan_tier_register(tier, mode="REPLACE")  # type: ignore[arg-type]


def test_c5e_override_mode_on_ep5_raises() -> None:
    """EP-5 does NOT permit mode='override'."""
    from luana_core_extension_sdk import BookingPolicy, BookingResult

    r = ExtensionPointRegistry()

    def can_confirm(slot, ctx):
        return BookingResult(allowed=True)

    policy = BookingPolicy(name="test-brand.p", can_confirm=can_confirm)
    with pytest.raises(ValueError, match="does not support mode='override'"):
        r.scheduling_booking_policy_register(policy, mode="override")
