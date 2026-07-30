# downstream-regression-na: engine package __init__ re-exports only, no logic
"""Engine repository utilities — promotion lifts from brand implementations.

Provides reusable abstract base classes for common repository patterns
that appear across multiple brand verticals.

Available:
  - CompoundScopeRepositoryBase: Dual-filter async repo base (tenant_id + scope_id).
    Brand consumer specifies the scope axis name via ``scope_field`` constructor arg.
    Lifted from vitalia/_shared/repositories/phi_repository.py per proposal
    2026-05-20-core-platform-extensions-slice-1.md.
"""

from luana_core_platform.repositories.compound_scope_repository import CompoundScopeRepositoryBase

__all__ = ["CompoundScopeRepositoryBase"]
