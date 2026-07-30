"""Architecture fitness: ExtensionPointRegistry has no unregister_* methods.

V-AG-cc5-no-unregister. CC-5 immutability: once registered at startup,
extensions cannot be removed at runtime.

ExtensionPointRegistry class must have ZERO public methods starting with
'unregister_'. This is a permanent invariant — adding unregister support
requires re-evaluating CC-3 (startup-only) + CC-5 (immutable) simultaneously,
which is a major SDK version break.
"""

from __future__ import annotations

import inspect

from luana_core_extension_sdk import ExtensionPointRegistry


def test_no_unregister_methods_on_registry_class() -> None:
    """V-AG-cc5-no-unregister: ExtensionPointRegistry class has zero unregister_* methods."""
    all_members = inspect.getmembers(ExtensionPointRegistry)
    unregister_methods = [name for name, member in all_members if name.startswith("unregister_") and callable(member)]

    assert not unregister_methods, (
        "ExtensionPointRegistry has unregister_* method(s): " + str(unregister_methods) + "\n\n"
        "CC-5 immutability: extensions registered at startup cannot be removed.\n"
        "To add unregister support requires:\n"
        "  1. Re-evaluate CC-3 (startup-only lock) + CC-5 (immutable post-startup)\n"
        "  2. Major SDK version bump (v0.1.0 → v1.0.0 breaking change)\n"
        "  3. /architect sign-off + remove this test with justification\n"
        "  4. New Story with full contract specification"
    )


def test_no_unregister_in_public_api_surface() -> None:
    """V-AG-cc5-no-unregister: dir() inspection also shows no unregister entries."""
    public_surface = [name for name in dir(ExtensionPointRegistry) if not name.startswith("_")]
    unregister_entries = [name for name in public_surface if "unregister" in name.lower()]

    assert not unregister_entries, (
        "ExtensionPointRegistry public surface contains 'unregister' entries: "
        + str(unregister_entries)
        + "\n\nCC-5: no unregister support in v0.1.0 SDK."
    )
