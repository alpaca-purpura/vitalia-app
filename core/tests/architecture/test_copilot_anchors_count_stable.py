"""Architecture fitness: [COPILOT-*] anchor registry size is STABLE.

Per 03-arch.md §7.8 + copilot-expert skill "Anchors" section.

The copilot module uses inline marker comments of the form ``[COPILOT-<NAME>]``
to identify protected code paths that documentation references. The total
unique anchor count across luana-core-copilot/ and the business modules'
copilot_provider/ subfolders is a stable invariant that may only change with
explicit registry update + architect ratification.

Current value (post Story 6 T-16 unlift, 2026-05-11): **33 unique anchors**.

The architect-spec ADR-001 §7.8 wrote "36" but the actual post-lift count is
33 — Story 5+6 anchor inventory uses overlapping anchors across copilot/
proper and business modules' copilot_provider/ subfolders (e.g.
``[COPILOT-PROVIDER-PATTERN]`` appears in both surfaces but counts once in the
union). This test cements the empirical reality post Story 6 close.

Adding a NEW anchor:
  1. Decide its name (`[COPILOT-NEW-NAME]`).
  2. Place inline comment in the appropriate source file.
  3. Bump EXPECTED_ANCHOR_COUNT below by 1 in the same commit.
  4. Auditor verifies the architect rationale for the bump.

V-AG-8 validator.
"""

from __future__ import annotations

import re
from pathlib import Path

CORE_DIR = Path(__file__).parents[2]
COPILOT_SRC = CORE_DIR / "luana-core-copilot" / "src" / "luana_core_copilot"

ANCHOR_PATTERN = re.compile(r"\[COPILOT-[A-Z0-9-]+\]")

# Post Story 6 T-16 UNLIFT (2026-05-11) — 33 unique anchors in the union of
# luana-core-copilot/ + all business modules' copilot_provider/ subfolders.
EXPECTED_ANCHOR_COUNT = 33


def _collect_all_anchors() -> set[str]:
    """Union of anchors across copilot/ + every business module's copilot_provider/."""
    anchors: set[str] = set()

    if COPILOT_SRC.exists():
        for py in COPILOT_SRC.rglob("*.py"):
            text = py.read_text(encoding="utf-8")
            anchors.update(ANCHOR_PATTERN.findall(text))

    # Also scan business modules' copilot_provider/ subfolders
    for pkg in sorted(CORE_DIR.glob("luana-core-*")):
        for cp_dir in pkg.rglob("copilot_provider"):
            if not cp_dir.is_dir():
                continue
            for py in cp_dir.rglob("*.py"):
                text = py.read_text(encoding="utf-8")
                anchors.update(ANCHOR_PATTERN.findall(text))

    return anchors


def test_copilot_anchor_count_stable():
    """Exact union count of [COPILOT-*] anchors must equal EXPECTED_ANCHOR_COUNT."""
    anchors = _collect_all_anchors()

    actual = len(anchors)

    assert actual == EXPECTED_ANCHOR_COUNT, (
        f"V-AG-8 anchor registry drift: expected {EXPECTED_ANCHOR_COUNT}, got {actual}.\n\n"
        "Adding a new anchor or removing one requires explicit registry update + "
        "architect ratification. Bump EXPECTED_ANCHOR_COUNT in this test file in "
        "the same commit.\n\n"
        f"Current anchor set ({actual}):\n" + "\n".join(f"  {a}" for a in sorted(anchors))
    )


def test_anchor_uniqueness():
    """Anchor names are well-formed (regex match) and unique by name."""
    anchors = _collect_all_anchors()
    malformed = [a for a in anchors if not ANCHOR_PATTERN.fullmatch(a)]
    assert not malformed, f"Malformed anchors: {malformed}"

    # Already a set — uniqueness is structural. Just affirm > 0.
    assert anchors, "No [COPILOT-*] anchors found — registry must be non-empty post Story 6"
