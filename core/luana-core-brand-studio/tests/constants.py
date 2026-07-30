"""Shared test constants for luana-core-brand-studio tests.

Mirrors the AISALESHT tests/modules/conftest.py constants for tenant isolation tests.
"""

import uuid

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")
USER_A = uuid.UUID("cccc0000-0000-0000-0000-000000000001")
