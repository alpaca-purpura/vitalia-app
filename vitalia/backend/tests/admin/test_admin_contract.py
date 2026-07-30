"""Admin contract tests — fn-be-admin-contract validator.

Verifies:
- PAGE_SPECS is a non-empty tuple of PageSpec objects
- No duplicate slugs
- Each PageSpec has slug, title, icon (str fields)
- Admin module is importable (structural)

These tests do NOT require Streamlit to be running — they test the
registry contract at import time.
"""

from __future__ import annotations


def test_page_specs_importable() -> None:
    """PAGE_SPECS can be imported from admin.app — RED before admin.app exists."""
    from src.modules.vitalia.admin.app import PAGE_SPECS  # noqa: PLC0415

    assert PAGE_SPECS is not None


def test_page_specs_is_non_empty() -> None:
    """PAGE_SPECS must have at least one PageSpec (tenants + usuarios = 2 minimum)."""
    from src.modules.vitalia.admin.app import PAGE_SPECS  # noqa: PLC0415

    assert len(PAGE_SPECS) >= 2, f"Expected ≥2 page specs, got {len(PAGE_SPECS)}"


def test_page_specs_no_duplicate_slugs() -> None:
    """No two PageSpecs may share the same slug (unique URL paths required)."""
    from src.modules.vitalia.admin.app import PAGE_SPECS  # noqa: PLC0415

    slugs = [spec.slug for spec in PAGE_SPECS]
    dupes = sorted(set(s for s in slugs if slugs.count(s) > 1))
    assert len(slugs) == len(set(slugs)), f"Duplicate slugs found: {dupes}"


def test_page_specs_all_have_required_fields() -> None:
    """Every PageSpec must have slug, title, icon as non-empty strings."""
    from src.modules.vitalia.admin.app import PAGE_SPECS  # noqa: PLC0415

    for spec in PAGE_SPECS:
        assert isinstance(spec.slug, str) and spec.slug.strip(), f"Spec missing/empty slug: {spec!r}"
        assert isinstance(spec.title, str) and spec.title.strip(), f"Spec missing/empty title: {spec!r}"
        assert isinstance(spec.icon, str) and spec.icon.strip(), f"Spec missing/empty icon: {spec!r}"


def test_page_specs_contains_tenants_and_usuarios() -> None:
    """PAGE_SPECS must include 'tenants' and 'usuarios' pages (T-4 scope minimum)."""
    from src.modules.vitalia.admin.app import PAGE_SPECS  # noqa: PLC0415

    slugs = {spec.slug for spec in PAGE_SPECS}
    assert "tenants" in slugs, f"'tenants' page missing from PAGE_SPECS. Slugs: {slugs}"
    assert "usuarios" in slugs, f"'usuarios' page missing from PAGE_SPECS. Slugs: {slugs}"


def test_page_specs_callable_page_modules() -> None:
    """Each module referenced in PAGE_SPECS must expose a callable render function."""
    from src.modules.vitalia.admin.app import PAGE_SPECS  # noqa: PLC0415

    for spec in PAGE_SPECS:
        # Verify the page module function reference is callable
        assert callable(spec.render_fn), f"PageSpec '{spec.slug}' has non-callable render_fn: {spec.render_fn!r}"


def test_admin_auth_module_importable() -> None:
    """Admin _shared/auth module is importable with verify_admin_password callable."""
    from src.modules.vitalia.admin._shared.auth import verify_admin_password  # noqa: PLC0415

    assert callable(verify_admin_password)


def test_admin_db_module_importable() -> None:
    """Admin _shared/db module is importable with get_sync_session callable."""
    from src.modules.vitalia.admin._shared.db import get_sync_session  # noqa: PLC0415

    assert callable(get_sync_session)
