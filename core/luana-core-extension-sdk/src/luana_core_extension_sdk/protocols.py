"""Protocol interfaces for extension handlers — per §1.3 step 5.

3 Protocols: FieldOverrideHandler, SignupHandler, GuardrailCheck.
All @runtime_checkable per §1.3 step 5 verbatim.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from luana_core_extension_sdk.brand_context import BrandContext
    from luana_core_extension_sdk.models import (
        FieldDef,
        FieldOverride,
        GuardrailResult,
        SignupResult,
    )


@runtime_checkable
class FieldOverrideHandler(Protocol):
    """Protocol for EP-1 field_override handlers.

    Called by ExtensionPointRegistry.resolve_field_override(field, ctx).
    First non-None result wins (deterministic by registration order).
    """

    def __call__(
        self,
        field: "FieldDef",
        ctx: "BrandContext",
    ) -> "Optional[FieldOverride]":
        """Return FieldOverride if this handler applies, else None."""
        ...


@runtime_checkable
class SignupHandler(Protocol):
    """Protocol for EP-16 IAM signup handlers.

    Called by ExtensionPointRegistry.dispatch_signup(clerk_user, ctx).
    """

    def __call__(
        self,
        clerk_user: object,
        ctx: "BrandContext",
    ) -> "SignupResult":
        """Process signup and return SignupResult (approved / pending_review / rejected)."""
        ...


@runtime_checkable
class GuardrailCheck(Protocol):
    """Protocol for EP-13 guardrail pre_send_check and pre_receive_check callables.

    Per §7.5.3 EP-13 extended scope: both pre-send + pre-receive phases supported.
    """

    def __call__(
        self,
        message: str,
        ctx: "BrandContext",
    ) -> "GuardrailResult":
        """Check message and return GuardrailResult (blocked / rewritten / warn)."""
        ...
