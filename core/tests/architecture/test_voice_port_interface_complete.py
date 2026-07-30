"""Architecture fitness: BrandVoicePort Protocol interface complete.

Per 03-arch.md §7.4 + D-T3 + ADR-001 §2.4. BrandVoicePort exposes
exactly 2 public async methods (frozen surface):

- `compile_system_instruction(tenant_id: UUID) -> str` — slot 5 BRAND_VOICE
- `get_voice_metadata(tenant_id: UUID) -> dict` — cache invalidation + routing

The surface is FROZEN at Story 7 introduction — adding a method requires
architect ratification per Story 7 §6 halt criterion #2.

V-AG-4 validator.
"""

from __future__ import annotations

import inspect
from typing import get_type_hints
from uuid import UUID

from luana_core_brand_studio.application.ports.brand_voice_port import BrandVoicePort


def test_brand_voice_port_is_protocol():
    """BrandVoicePort is a typing.Protocol (hexagonal port discipline)."""
    # Protocol classes have _is_protocol attribute = True
    assert getattr(BrandVoicePort, "_is_protocol", False), (
        "BrandVoicePort MUST be a typing.Protocol (D-T3 hexagonal port)."
    )


def test_brand_voice_port_exposes_compile_system_instruction():
    """compile_system_instruction must be async + accept tenant_id: UUID + return str."""
    assert hasattr(BrandVoicePort, "compile_system_instruction"), (
        "BrandVoicePort MUST expose `compile_system_instruction` (D-T3 §2.4)."
    )
    method = BrandVoicePort.compile_system_instruction
    assert inspect.iscoroutinefunction(method), "compile_system_instruction MUST be async."
    sig = inspect.signature(method)
    params = list(sig.parameters.keys())
    # self + tenant_id
    assert "tenant_id" in params, "compile_system_instruction MUST accept `tenant_id` parameter."
    hints = get_type_hints(method)
    assert hints.get("tenant_id") is UUID, (
        f"compile_system_instruction `tenant_id` must be UUID, got {hints.get('tenant_id')}."
    )
    assert hints.get("return") is str, f"compile_system_instruction return type must be str, got {hints.get('return')}."


def test_brand_voice_port_exposes_get_voice_metadata():
    """get_voice_metadata must be async + accept tenant_id: UUID + return dict."""
    assert hasattr(BrandVoicePort, "get_voice_metadata"), "BrandVoicePort MUST expose `get_voice_metadata` (D-T3 §2.4)."
    method = BrandVoicePort.get_voice_metadata
    assert inspect.iscoroutinefunction(method), "get_voice_metadata MUST be async."
    sig = inspect.signature(method)
    params = list(sig.parameters.keys())
    assert "tenant_id" in params, "get_voice_metadata MUST accept `tenant_id` parameter."
    hints = get_type_hints(method)
    assert hints.get("tenant_id") is UUID, f"get_voice_metadata `tenant_id` must be UUID, got {hints.get('tenant_id')}."
    assert hints.get("return") is dict, f"get_voice_metadata return type must be dict, got {hints.get('return')}."


def test_brand_voice_port_surface_frozen():
    """Public surface FROZEN at exactly 2 async methods.

    Adding methods requires architect ratification (Story 7 §6 halt criterion #2).
    """
    # Get public (non-dunder, non-private) methods
    public_methods = {
        name
        for name in dir(BrandVoicePort)
        if not name.startswith("_") and callable(getattr(BrandVoicePort, name, None))
    }

    expected = {"compile_system_instruction", "get_voice_metadata"}

    extra = public_methods - expected
    missing = expected - public_methods

    assert not missing, f"BrandVoicePort missing required methods: {missing} (D-T3 §2.4)."
    assert not extra, (
        f"BrandVoicePort surface DRIFT — extra methods detected: {extra}. "
        "Surface FROZEN per Story 7 §6 halt #2. Adding methods requires "
        "architect ratification."
    )
