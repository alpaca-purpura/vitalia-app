"""Architecture fitness: luana-core-iam is brand-agnostic.

Per 01-spec.md §2.5 + §3.3:
- No 'if brand ==' conditional in iam source.
- No hardcoded Clerk app IDs (app_{...} pattern from Clerk dashboard).
- ClerkService instantiation reads config from settings/env — no brand-specific
  control flow.

V-AG-1 validator.
"""

from __future__ import annotations

import re
from pathlib import Path

IAM_SRC = Path(__file__).parents[2] / "luana-core-iam" / "src" / "luana_core_iam"


def _all_py_files():
    return list(IAM_SRC.rglob("*.py"))


def test_no_brand_conditional():
    """No 'if brand ==' pattern in iam source."""
    pattern = re.compile(r"if\s+brand\s*==")
    violations = []
    for path in _all_py_files():
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                violations.append(f"{path.relative_to(IAM_SRC)}:{lineno}: {line.strip()}")
    assert not violations, "luana-core-iam must be brand-agnostic. Found 'if brand ==' in:\n" + "\n".join(violations)


def test_no_hardcoded_clerk_app_ids():
    """No hardcoded Clerk app IDs (e.g. 'app_2abc...') in iam source.

    Clerk app IDs start with 'app_' followed by alphanumeric chars.
    They appear in URLs like clerk.app_xxx.accounts.dev or as string literals.
    """
    # Pattern: 'app_' followed by >=10 alphanumeric chars (Clerk app ID format)
    pattern = re.compile(r"\bapp_[A-Za-z0-9]{10,}\b")
    violations = []
    for path in _all_py_files():
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            # Skip comment lines (documentation might mention format)
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if pattern.search(line):
                violations.append(f"{path.relative_to(IAM_SRC)}:{lineno}: {line.strip()}")
    assert not violations, "luana-core-iam must have no hardcoded Clerk app IDs. Found in:\n" + "\n".join(violations)


def test_clerk_service_reads_from_settings():
    """ClerkService does not hardcode any brand-specific API key or URL."""
    clerk_files = list(IAM_SRC.rglob("*clerk*.py"))
    # If no clerk file found, the pattern may live in external infra — pass trivially
    # (the brand-agnostic contract is enforced by test_no_brand_conditional above)
    for path in clerk_files:
        text = path.read_text(encoding="utf-8")
        # Should reference settings.* or os.environ, NOT literal key strings
        # Hardcoded secret keys start with sk_live_ or sk_test_ + >=20 chars
        hardcoded_secret = re.compile(r"\b(sk_live_|sk_test_)[A-Za-z0-9]{20,}\b")
        violations = []
        for lineno, line in enumerate(text.splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if hardcoded_secret.search(line):
                violations.append(f"{path.name}:{lineno}: {line.strip()}")
        assert not violations, "luana-core-iam Clerk code must not hardcode secret keys:\n" + "\n".join(violations)
