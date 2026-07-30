"""Tests for models.py — 18 DataClass models per §1.3 step 3.

TDD: these tests written FIRST (RED phase before models.py exists).
"""

from __future__ import annotations

import dataclasses

# All 18 expected model class names per 03-arch-be.md §1.3 step 3
EXPECTED_MODEL_NAMES = {
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
    "SignupResult",
    "PlanTierDef",
    "WizardStepDef",
}


def test_all_18_models_importable():
    """All 18 DataClass models must be importable from models.py."""
    from luana_core_extension_sdk import models

    for name in EXPECTED_MODEL_NAMES:
        assert hasattr(models, name), f"Missing model: {name}"


def test_all_18_models_are_dataclasses():
    """All 18 models must be dataclasses."""
    from luana_core_extension_sdk import models

    for name in EXPECTED_MODEL_NAMES:
        cls = getattr(models, name)
        assert dataclasses.is_dataclass(cls), f"{name} is not a dataclass"


def test_all_frozen_dataclasses():
    """All 18 models must be frozen (CC-5 immutable per §1.4 guideline)."""
    from luana_core_extension_sdk import models

    for name in EXPECTED_MODEL_NAMES:
        cls = getattr(models, name)
        params = cls.__dataclass_params__
        assert params.frozen is True, f"{name} is not frozen"


def test_field_override_fields():
    """FieldOverride has expected fields per §1.3."""
    from luana_core_extension_sdk.models import FieldOverride

    field_names = {f.name for f in dataclasses.fields(FieldOverride)}
    assert "name" in field_names
    assert "default_value" in field_names
    assert "label" in field_names
    assert "hint" in field_names
    assert "required" in field_names


def test_tool_def_has_handler():
    """ToolDef must have handler Callable field per EP-3."""
    from luana_core_extension_sdk.models import ToolDef

    field_names = {f.name for f in dataclasses.fields(ToolDef)}
    assert "handler" in field_names
    assert "name" in field_names
    assert "description" in field_names
    assert "input_schema" in field_names


def test_brand_context_not_in_models():
    """BrandContext is in brand_context.py, NOT in models.py."""
    from luana_core_extension_sdk import models

    assert not hasattr(models, "BrandContext")


def test_guardrail_def_has_pre_send_and_pre_receive():
    """GuardrailDef has pre_send_check + pre_receive_check per §7.5.3 EP-13 extended scope."""
    from luana_core_extension_sdk.models import GuardrailDef

    field_names = {f.name for f in dataclasses.fields(GuardrailDef)}
    assert "pre_send_check" in field_names
    assert "pre_receive_check" in field_names


def test_kb_pack_def_has_tenant_scope():
    """KbPackDef has tenant_scope field (brand | tenant | both) per §7.5.3 EP-14."""
    from luana_core_extension_sdk.models import KbPackDef

    field_names = {f.name for f in dataclasses.fields(KbPackDef)}
    assert "tenant_scope" in field_names
