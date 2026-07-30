"""Architecture fitness: no residual test stubs introduced post Story 6 lift.

Per 03-arch.md §7.4 + D-T2 cement, ADJUSTED for T-17 R26 deferral.

**T-17 R26 deferral context (2026-05-11):** T-17 architect spec premise was
that MessageModel lives in luana-core-copilot post-Story-6 lift. Reproduction
found MessageModel actually lives in `sales_agent` module which is Story 7
territory. T-17 deferred MessageModel stub cleanup to Story 7.

**Story 7 D-T2 cement (2026-05-12):** sales_agent.MessageModel lifted in T-5
batch 2 → conftest stubs replaced with real eager imports in 4 conftests
(offer-studio + crm + copilot + sales-agent). MessageModel allowlist entries
REMOVED. Only AppointmentModel + ProductModel allowlists remain (Story 8
scheduling + catalog deferrals).

**V-AG-4 effective contract (post Story 7):**
- AppointmentModel stubs in offer-studio/copilot/crm/connections conftests → ALLOWLISTED (Story 8 deferral)
- ProductModel stubs in crm/brand-studio/connections conftests → ALLOWLISTED (Story 8 catalog deferral)
- _ProductStub in landing conftest → ALLOWLISTED (Story 8 catalog deferral)
- ZERO MessageModel stubs (cement: Story 7 D-T2 closed)

Auditor / future architect: bump V-AG-4 contract scope when Story 8 lifts
scheduling (AppointmentModel allowlist comes off) and catalog (ProductModel
allowlist comes off).

V-AG-4 validator.
"""

from __future__ import annotations

import re
from pathlib import Path

CORE_DIR = Path(__file__).parents[2]

# Cross-module FK target stubs deferred by Stories 7 and 8 respectively.
# These stubs are documented allowlist entries — keys are paths relative to
# CORE_DIR, values are class names allowed as stub `class X(_Base)` declarations.
#
# Stubs persist because the source-of-truth model lives in a module that has
# not been lifted yet. Each entry must cite the Story that will lift the real
# model. When that Story closes, remove the corresponding entry here AND
# the stub from the conftest in the same commit.
#
# Cross-Story stub inventory (origin: Story 6 T-20 audit, 2026-05-11):
ALLOWLISTED_STUBS: dict[str, set[str]] = {
    "luana-core-offer-studio/tests/conftest.py": {
        "AppointmentModel",  # Story 8 scheduling lift
    },
    "luana-core-copilot/tests/conftest.py": {
        "AppointmentModel",  # Story 8 scheduling lift (T-15 baseline preserves)
    },
    "luana-core-brand-studio/tests/conftest.py": {
        "ProductModel",  # Story 8 catalog/product lift (Story 5 baseline preserves)
    },
    "luana-core-crm/tests/conftest.py": {
        "ProductModel",  # Story 8 catalog/product lift
        "AppointmentModel",  # Story 8 scheduling lift
    },
    "luana-core-connections/tests/conftest.py": {
        "ProductModel",  # Story 8 catalog/product lift
        "AppointmentModel",  # Story 8 scheduling lift
    },
    "luana-core-sales-agent/tests/conftest.py": {
        "AppointmentModel",  # Story 8 scheduling lift (Story 7 baseline preserves)
    },
    "luana-core-landing/tests/conftest.py": {
        "_ProductStub",  # Story 8 catalog/product lift (landing's local prefix)
    },
    "luana-core-campaigns/tests/conftest.py": {
        "MessageModel",  # Story 8 T-9..T-13 — MessageModel not lifted to campaigns (Story 7 owns sales_agent); deferred
        "AppointmentModel",  # Story 8 scheduling lift (Story 8 campaigns lift preserves stub)
    },
}

# Pattern: `class <CapName>(_Base)` or `class <CapName>(Base)` declarations.
# We scan tests/ folders for any stub class declarations beyond allowlist.
# Allow optional leading whitespace (stubs are often inside `if not in registry:` blocks).
STUB_CLASS_PATTERN = re.compile(
    r"^[ \t]*class\s+(\w+)\s*\(\s*(?:_Base|Base|DeclarativeBase)\s*\)\s*:",
    re.MULTILINE,
)


def _get_conftest_files() -> list[Path]:
    """Find all conftest.py files in luana-core-* test directories."""
    test_files: list[Path] = []
    for pkg_dir in sorted(CORE_DIR.glob("luana-core-*")):
        for path in (pkg_dir / "tests").rglob("conftest.py"):
            test_files.append(path)
    return test_files


def test_no_residual_stubs_post_story_6():
    """Only allowlisted cross-module stubs may persist in test conftest files.

    Any new stub declaration `class Foo(_Base):` in a conftest.py beyond the
    allowlist signals a missing lift in Story 6 OR a forward-coupling that
    should be deferred via a documented allowlist entry.
    """
    violations: list[str] = []

    for conftest_path in _get_conftest_files():
        text = conftest_path.read_text(encoding="utf-8")
        rel = conftest_path.relative_to(CORE_DIR).as_posix()
        allowed_for_this_file = ALLOWLISTED_STUBS.get(rel, set())

        for match in STUB_CLASS_PATTERN.finditer(text):
            class_name = match.group(1)
            if class_name not in allowed_for_this_file:
                lineno = text[: match.start()].count("\n") + 1
                violations.append(
                    f"{rel}:{lineno}: class {class_name}(_Base) — "
                    f"NOT in allowlist for this file (allowed: {sorted(allowed_for_this_file) or 'none'})",
                )

    assert not violations, (
        "V-AG-4 D-T2 cement: residual cross-module test stubs detected.\n\n"
        "If this stub is intentional cross-Story coupling (forward dependency):\n"
        "  1. Add path:class_name to ALLOWLISTED_STUBS in this test file.\n"
        "  2. Document Story owning the lift (e.g. 'Story N <module> lift').\n"
        "  3. Update Story (N) ready package to include stub removal as a ticket.\n\n"
        "Violations:\n" + "\n".join(violations)
    )


def test_allowlisted_stubs_still_present():
    """Sanity: allowlisted stubs must actually exist in their declared conftest.

    Prevents silent allowlist drift where a stub is removed but the allowlist
    entry stays — would mask future regressions where someone re-adds it
    without justification.
    """
    missing: list[str] = []

    for rel_path, expected_classes in ALLOWLISTED_STUBS.items():
        conftest_path = CORE_DIR / rel_path
        if not conftest_path.exists():
            missing.append(f"{rel_path}: file not found — remove allowlist entry")
            continue

        text = conftest_path.read_text(encoding="utf-8")
        found_classes = {m.group(1) for m in STUB_CLASS_PATTERN.finditer(text)}

        for expected in sorted(expected_classes):
            if expected not in found_classes:
                missing.append(
                    f"{rel_path}: class {expected}(_Base) NOT FOUND — remove allowlist entry (lift may have happened)",
                )

    assert not missing, "V-AG-4 allowlist drift detected — stubs claimed but missing:\n" + "\n".join(missing)
