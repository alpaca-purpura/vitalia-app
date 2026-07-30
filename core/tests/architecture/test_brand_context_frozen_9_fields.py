"""Architecture fitness: BrandContext is frozen dataclass with exactly 9 fields.

V-F-sdk-5. Story 8 canonical BrandContext contract:
- frozen=True (immutable — CC-5)
- slots=True (memory efficiency + frozen enforcement)
- kw_only=True (explicit field assignment)
- Exactly 9 fields: tenant_id, brand_slug, plan_tier, locale, feature_flags,
  tenant_profile_id, vertical_kind, compliance_flags, pii_policy
- No PII fields (email, phone, address, dob, ssn, ip_address, etc.)

Any change to BrandContext field count or mutability is a contract break
requiring architect sign-off.
"""

from __future__ import annotations

import dataclasses

from luana_core_extension_sdk import BrandContext

_EXPECTED_FIELDS = frozenset(
    {
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
)

_EXPECTED_FIELD_COUNT = 9

_PII_FIELD_PATTERNS = {
    "email",
    "phone",
    "mobile",
    "address",
    "street",
    "zip",
    "postal",
    "dob",
    "birth",
    "ssn",
    "national_id",
    "tax_id",
    "ip_address",
    "client_ip",
    "account_number",
    "card_number",
    "iban",
    "name",  # person name — PII
    "first_name",
    "last_name",
    "full_name",
}


def test_brand_context_is_dataclass() -> None:
    """V-F-sdk-5: BrandContext must be a dataclass."""
    assert dataclasses.is_dataclass(BrandContext), (
        "BrandContext is not a dataclass.\nMust use @dataclass(frozen=True, slots=True, kw_only=True)."
    )


def test_brand_context_frozen() -> None:
    """V-F-sdk-5: BrandContext must be frozen (immutable post-construction)."""
    ctx = BrandContext(
        tenant_id="t1",
        brand_slug="test-brand",
        plan_tier="starter",
        locale="es-419",
        feature_flags=frozenset(),
        tenant_profile_id=None,
        vertical_kind=None,
        compliance_flags=frozenset(),
        pii_policy="strict",
    )
    try:
        ctx.tenant_id = "mutated"  # type: ignore[misc]
        assert False, "BrandContext should raise FrozenInstanceError on mutation"
    except dataclasses.FrozenInstanceError:
        pass  # Expected — CC-5 immutability confirmed


def test_brand_context_field_count() -> None:
    """V-F-sdk-5: BrandContext has exactly 9 fields."""
    fields = dataclasses.fields(BrandContext)
    assert len(fields) == _EXPECTED_FIELD_COUNT, (
        f"BrandContext has {len(fields)} fields, expected {_EXPECTED_FIELD_COUNT}.\n"
        f"Current: {[f.name for f in fields]}\n"
        f"Expected: {sorted(_EXPECTED_FIELDS)}\n\n"
        "Changing BrandContext field count requires architect sign-off."
    )


def test_brand_context_exact_fields() -> None:
    """V-F-sdk-5: BrandContext has exactly the 9 expected fields by name."""
    field_names = {f.name for f in dataclasses.fields(BrandContext)}

    missing = _EXPECTED_FIELDS - field_names
    extra = field_names - _EXPECTED_FIELDS

    assert not missing, f"Missing BrandContext fields: {sorted(missing)}"
    assert not extra, (
        f"Unexpected BrandContext fields: {sorted(extra)}\n"
        "Adding fields requires architect sign-off + V-F-sdk-5 update."
    )


def test_brand_context_no_pii_fields() -> None:
    """V-F-sdk-5 + PII sanitisation: BrandContext must not contain PII field names."""
    field_names = {f.name.lower() for f in dataclasses.fields(BrandContext)}

    pii_violations = []
    for field_name in field_names:
        for pattern in _PII_FIELD_PATTERNS:
            if pattern in field_name:
                pii_violations.append(f"  field '{field_name}' matches PII pattern '{pattern}'")

    assert not pii_violations, (
        "BrandContext contains PII field names.\n"
        "BrandContext is passed to EP handlers — PII fields would expose sensitive data.\n\n"
        "PII violations:\n" + "\n".join(pii_violations)
    )
