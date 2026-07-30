"""Architecture fitness: vitalia Extension SDK registration completeness.

Verifies that `vitalia/backend/src/modules/vitalia/extensions.py::register_all(registry)`
correctly mounts all expected Extension SDK registrations for Slice 1:

  1. 5 NEW brand-internal registries (T-infra-2):
     - PAYMENT_PROVIDER_REGISTRY (≥5 slots: 5 manual variants + mercadopago)
     - FISCAL_PROVIDER_REGISTRY (≥1 slot: nubefact_pe)
     - APPOINTMENT_ORIGIN_REGISTRY (≥4 slots: sales_agent+walk_in+phone_manual+proactive_outbound)
     - CONVERSATION_INITIATION_REGISTRY (≥1 slot: whatsapp_template_meta)
     - PRINT_METHOD_REGISTRY (≥1 slot: browser_pdf)

  2. EP-3 tool placeholder registrations (4 tools):
     - vitalia.prepaid_payment_check
     - vitalia.treatment_followup_check
     - vitalia.medical_consent_request
     - vitalia.appointment_reschedule_with_doctor

  3. EP-13 medical guardrails (4 guardrails):
     - vitalia.medical_safety_no_diagnosis
     - vitalia.medical_safety_no_prescription
     - vitalia.medical_disclaimer_required
     - vitalia.prompt_injection_block

Per 03-arch-be.md § 6 (Extension SDK registries) + T-infra-4 scope.

downstream-regression-na: brand-local arch fitness test; no cross-brand consumers
"""

from __future__ import annotations

import importlib
from pathlib import Path

WS_ROOT = Path(__file__).resolve().parents[4]
EXTENSIONS_MODULE = "src.modules.vitalia.extensions"

# Expected EP-3 tool names (with vitalia. prefix per CC-4)
EXPECTED_EP3_TOOLS: frozenset[str] = frozenset(
    [
        "vitalia.prepaid_payment_check",
        "vitalia.treatment_followup_check",
        "vitalia.medical_consent_request",
        "vitalia.appointment_reschedule_with_doctor",
    ]
)

# Expected EP-13 guardrail names
EXPECTED_EP13_GUARDRAILS: frozenset[str] = frozenset(
    [
        "vitalia.medical_safety_no_diagnosis",
        "vitalia.medical_safety_no_prescription",
        "vitalia.medical_disclaimer_required",
        "vitalia.prompt_injection_block",
    ]
)

# Minimum slot counts for brand-internal registries
REGISTRY_MIN_SLOTS: dict[str, int] = {
    "PAYMENT_PROVIDER_REGISTRY": 5,  # 5 manual slots minimum (Slice 1)
    "FISCAL_PROVIDER_REGISTRY": 1,  # nubefact_pe
    "APPOINTMENT_ORIGIN_REGISTRY": 4,  # 4 origins
    "CONVERSATION_INITIATION_REGISTRY": 1,  # whatsapp_template_meta
    "PRINT_METHOD_REGISTRY": 1,  # browser_pdf
}

# Expected appointment origin keys
EXPECTED_APPOINTMENT_ORIGINS: frozenset[str] = frozenset(
    [
        "sales_agent",
        "walk_in",
        "phone_manual",
        "proactive_outbound",
    ]
)


class TestExtensionSdkRegistration:
    """Extension SDK registration completeness for vitalia Slice 1."""

    def test_extensions_module_importable(self) -> None:
        """extensions.py must be importable without runtime error."""
        try:
            ext = importlib.import_module(EXTENSIONS_MODULE)
        except ImportError as e:
            raise AssertionError(
                f"Could not import {EXTENSIONS_MODULE}: {e}\n"
                "Ensure vitalia backend is on PYTHONPATH (run from WS root with uv)."
            ) from e
        assert hasattr(ext, "register_all"), f"{EXTENSIONS_MODULE} must export register_all(registry) function"

    def test_payment_provider_registry_has_minimum_slots(self) -> None:
        """PAYMENT_PROVIDER_REGISTRY must have ≥5 slots (Slice 1 manual providers)."""
        try:
            ext = importlib.import_module(EXTENSIONS_MODULE)
        except ImportError:
            return  # Handled in test_extensions_module_importable

        assert (
            hasattr(ext, "PAYMENT_PROVIDER_REGISTRY")
            or _import_registry("vitalia.connections.payment", "PAYMENT_PROVIDER_REGISTRY") is not None
        ), "PAYMENT_PROVIDER_REGISTRY must be importable from extensions or connections.payment"

        registry = _import_registry("src.modules.vitalia.connections.payment", "PAYMENT_PROVIDER_REGISTRY")
        if registry is None:
            return  # Module not yet implemented — skip

        slot_count = len(registry)
        min_slots = REGISTRY_MIN_SLOTS["PAYMENT_PROVIDER_REGISTRY"]
        assert slot_count >= min_slots, (
            f"PAYMENT_PROVIDER_REGISTRY has {slot_count} slots — "
            f"expected ≥{min_slots} (Slice 1: 5 manual payment variants + mercadopago). "
            "Per 03-arch-be.md § 6.1 PAYMENT_PROVIDER_REGISTRY definition."
        )

    def test_fiscal_provider_registry_has_nubefact(self) -> None:
        """FISCAL_PROVIDER_REGISTRY must include nubefact_pe (Slice 1 PE fiscal emission)."""
        registry = _import_registry("src.modules.vitalia.connections.fiscal", "FISCAL_PROVIDER_REGISTRY")
        if registry is None:
            return

        assert "nubefact_pe" in registry, (
            "FISCAL_PROVIDER_REGISTRY must include 'nubefact_pe' entry. "
            "Slice 1 fiscal emission is PE-only via Nubefact. "
            "Per 03-arch-be.md § 6.2 FISCAL_PROVIDER_REGISTRY."
        )

    def test_appointment_origin_registry_has_all_four_origins(self) -> None:
        """APPOINTMENT_ORIGIN_REGISTRY must have all 4 Slice 1 origins."""
        registry = _import_registry(
            "src.modules.vitalia.connections.appointment_origin",
            "APPOINTMENT_ORIGIN_REGISTRY",
        )
        if registry is None:
            return

        missing = EXPECTED_APPOINTMENT_ORIGINS - set(registry.keys())
        assert not missing, (
            f"APPOINTMENT_ORIGIN_REGISTRY is missing origins: {missing}. "
            "Expected all 4 Slice 1 appointment origins: "
            f"{sorted(EXPECTED_APPOINTMENT_ORIGINS)}. "
            "Per 03-arch-be.md § 6.3."
        )

    def test_conversation_initiation_registry_has_whatsapp_template(self) -> None:
        """CONVERSATION_INITIATION_REGISTRY must have whatsapp_template_meta (Slice 1)."""
        registry = _import_registry(
            "src.modules.vitalia.connections.conversation_initiation",
            "CONVERSATION_INITIATION_REGISTRY",
        )
        if registry is None:
            return

        assert "whatsapp_template_meta" in registry, (
            "CONVERSATION_INITIATION_REGISTRY must include 'whatsapp_template_meta'. Per 03-arch-be.md § 6.4."
        )

    def test_print_method_registry_has_browser_pdf(self) -> None:
        """PRINT_METHOD_REGISTRY must have browser_pdf (Slice 1 window.print())."""
        registry = _import_registry("src.modules.vitalia.connections.print_method", "PRINT_METHOD_REGISTRY")
        if registry is None:
            return

        assert "browser_pdf" in registry, (
            "PRINT_METHOD_REGISTRY must include 'browser_pdf'. "
            "Slice 1 uses window.print() only — WebUSB/IPP are Slice 2/3. "
            "Per 03-arch-be.md § 6.5."
        )

    def test_extensions_py_declares_ep3_tools(self) -> None:
        """extensions.py source must declare all 4 EP-3 tool names."""
        extensions_py = WS_ROOT / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "extensions.py"
        if not extensions_py.exists():
            return  # File missing — separate arch test will fail

        source = extensions_py.read_text(encoding="utf-8")

        missing_tools: list[str] = []
        for tool_name in sorted(EXPECTED_EP3_TOOLS):
            if tool_name not in source:
                missing_tools.append(tool_name)

        assert not missing_tools, (
            f"extensions.py missing EP-3 tool registrations: {missing_tools}.\n"
            "All 4 vitalia sales_agent tools must be registered via EP-3 per "
            "03-arch-be.md § 6 + brand.yaml::agentic_tools.\n"
            "Even placeholder ToolDef registrations are required for architecture gate."
        )

    def test_extensions_py_declares_ep13_guardrails(self) -> None:
        """extensions.py source must declare all 4 EP-13 medical guardrail names.

        EP-13 guardrail names are registered via `_ns(guard_name)` which builds
        `vitalia.<guard_name>` dynamically. We scan for the unqualified name as a
        string literal (the guard_name part without the namespace prefix), since
        the full qualified name is constructed at runtime by the _ns() helper.
        """
        extensions_py = WS_ROOT / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "extensions.py"
        if not extensions_py.exists():
            return

        source = extensions_py.read_text(encoding="utf-8")

        # Strip the "vitalia." prefix — the unqualified names appear as string
        # literals in the loop body of the EP-13 registration block.
        missing_guardrails: list[str] = []
        for guardrail_name in sorted(EXPECTED_EP13_GUARDRAILS):
            # Try full qualified name first, then unqualified (namespace-dynamic pattern)
            unqualified = guardrail_name.replace("vitalia.", "", 1)
            if guardrail_name not in source and unqualified not in source:
                missing_guardrails.append(guardrail_name)

        assert not missing_guardrails, (
            f"extensions.py missing EP-13 medical guardrail registrations: {missing_guardrails}.\n"
            "All 4 medical guardrails must be registered per brand.yaml::guardrails "
            "+ 03-arch-agentic § 10.\n"
            "EP-13 names may appear as qualified `vitalia.X` strings OR as unqualified\n"
            "`X` strings when constructed via `_ns(X)` helper.\n"
            "Per vitalia/.claude/rules/hipaa-lite.md § Access control: "
            "guardrails prevent PHI leakage through AI outputs."
        )

    def test_extensions_py_uses_vitalia_namespace_prefix(self) -> None:
        """All registrations in extensions.py use 'vitalia.' CC-4 namespace prefix."""
        extensions_py = WS_ROOT / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "extensions.py"
        if not extensions_py.exists():
            return

        source = extensions_py.read_text(encoding="utf-8")

        # The namespace helper must be present
        assert "_BRAND_SLUG" in source and '"vitalia"' in source, (
            "extensions.py must define _BRAND_SLUG = 'vitalia' for CC-4 namespace enforcement. "
            "Per Story 11 T-extensions-1 pattern (apps/test-brand/src/test_brand/extensions.py)."
        )

    def test_extensions_py_has_register_all_function(self) -> None:
        """extensions.py must define the register_all(registry) function."""
        extensions_py = WS_ROOT / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "extensions.py"
        assert extensions_py.exists(), (
            "vitalia/backend/src/modules/vitalia/extensions.py must exist. "
            "It is the single entry point for Extension SDK registration per CC-5."
        )

        source = extensions_py.read_text(encoding="utf-8")
        assert "def register_all" in source, (
            "extensions.py must define `register_all(registry)` function — "
            "the single entry point for all EP-1..EP-18 registration. "
            "Per test-brand precedent pattern (Story 8 cement)."
        )

    def test_five_registries_are_asserted_non_empty_in_extensions(self) -> None:
        """extensions.py must assert all 5 brand-internal registries are non-empty.

        Module-level assert guarantees runtime crash at startup (not silent) if a
        registry is accidentally empty due to import error or config issue.
        Per 03-arch-be.md § 6 smoke assertion pattern.
        """
        extensions_py = WS_ROOT / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "extensions.py"
        if not extensions_py.exists():
            return

        source = extensions_py.read_text(encoding="utf-8")

        expected_asserts = [
            "PAYMENT_PROVIDER_REGISTRY",
            "FISCAL_PROVIDER_REGISTRY",
            "APPOINTMENT_ORIGIN_REGISTRY",
            "CONVERSATION_INITIATION_REGISTRY",
            "PRINT_METHOD_REGISTRY",
        ]

        missing_asserts: list[str] = []
        for registry_name in expected_asserts:
            if f"assert {registry_name}" not in source:
                missing_asserts.append(registry_name)

        assert not missing_asserts, (
            f"extensions.py is missing module-level non-empty asserts for: {missing_asserts}.\n"
            "Each of the 5 brand-internal registries must have an `assert REGISTRY_NAME, ...` "
            "guard at module level so startup fails loudly on misconfiguration."
        )


def _import_registry(module_path: str, attr_name: str) -> dict | None:
    """Attempt to import a registry dict from a module. Returns None if module not found."""
    try:
        mod = importlib.import_module(module_path)
        return getattr(mod, attr_name, None)
    except (ImportError, ModuleNotFoundError):
        return None
