"""luana-core-extension-sdk public API.

18 extension points formalized contract for the Luana platform.
- EP-1..EP-5 critical: EXECUTABLE (registry stores + dispatch helpers callable from core)
- EP-6..EP-18 backlog: SIGNATURE-ONLY (registry stores; dispatch raises NotImplementedError)
- Cross-cutting policies CC-1..CC-5: runtime enforcement
"""

from __future__ import annotations

from luana_core_extension_sdk.brand_context import BrandContext
from luana_core_extension_sdk.exceptions import (
    DuplicateRegistrationError,
    ExtensionSDKError,
    NamespaceViolationError,
    RegistrationClosedError,
)
from luana_core_extension_sdk.extension_points import ExtensionPointRegistry
from luana_core_extension_sdk.models import (
    AssetTemplateDef,
    BookingPolicy,
    BookingResult,
    CampaignStepDef,
    CampaignTemplateDef,
    ChannelAdapterDef,
    ExtractorDef,
    FieldDef,
    FieldOverride,
    GuardrailDef,
    GuardrailResult,
    KbPackDef,
    LandingTemplateDef,
    LifecycleStageDef,
    MetricDef,
    PlanTierDef,
    PresetPack,
    SidebarRouteDef,
    SignupResult,
    ToolDef,
    WizardStepDef,
    WorkflowDef,
)
from luana_core_extension_sdk.protocols import (
    FieldOverrideHandler,
    GuardrailCheck,
    SignupHandler,
)

__version__ = "0.0.8-alpha"

__all__ = [
    "BrandContext",
    "ExtensionPointRegistry",
    # Exceptions
    "ExtensionSDKError",
    "DuplicateRegistrationError",
    "NamespaceViolationError",
    "RegistrationClosedError",
    # 18 DataClass models
    "FieldOverride",
    "FieldDef",
    "PresetPack",
    "ToolDef",
    "WorkflowDef",
    "BookingPolicy",
    "BookingResult",
    "SidebarRouteDef",
    "ExtractorDef",
    "ChannelAdapterDef",
    "MetricDef",
    "LandingTemplateDef",
    "CampaignStepDef",
    "CampaignTemplateDef",
    "AssetTemplateDef",
    "GuardrailDef",
    "GuardrailResult",
    "KbPackDef",
    "LifecycleStageDef",
    "PlanTierDef",
    "WizardStepDef",
    "SignupResult",
    # Protocols
    "FieldOverrideHandler",
    "GuardrailCheck",
    "SignupHandler",
]
