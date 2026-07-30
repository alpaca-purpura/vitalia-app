"""Architecture gate: growth_studio_event payloads must not contain PHI.

Verifies that vitalia_growth_studio_event telemetry events (brand-local table)
never include PHI fields in their payloads. PHI must use only bucketed/aggregated
values or opaque IDs.

Per ADR-vitalia-004 § 8 (Telemetry) and vitalia/.claude/rules/hipaa-lite.md:
  - Tabla brand-local `vitalia_growth_studio_event` (NO `copilot_trace_event`)
  - Bucketed amounts (never raw monetary values)
  - No PHI fields: patient_id, appointment_id, diagnosis, name, email, phone, dni

T-3 F1 EXTEND — vitalia-fase2-lisa-marca (F2-S7).
"""

from __future__ import annotations

from pathlib import Path

import pytest

WS = Path(__file__).resolve().parents[4]  # workspace root = luana-vitalia/

EMITTER_PATH = (
    WS / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "_shared" / "telemetry" / "growth_studio_emitter.py"
)

TELEMETRY_SRC_DIR = WS / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "_shared" / "telemetry"

# PHI fields that must NEVER appear as prop/payload keys in growth_studio_event emissions
PHI_PROP_KEYS_FORBIDDEN = frozenset(
    {
        "patient_id",
        "appointment_id",
        "diagnosis",
        "treatment_plan",
        "medication",
        "patient_name",
        "patient_email",
        "patient_phone",
        "patient_dni",
        "patient_cuit",
    }
)

# lisa_marca_* events declared in 03-arch § 10.2 — must be in emitter
REQUIRED_LISA_MARCA_EVENTS = frozenset(
    {
        "lisa_marca_viewed",
        "lisa_marca_subsubtab_changed",
        "lisa_marca_identity_saved",
        "lisa_marca_visuals_saved",
        "lisa_marca_personality_saved",
        "lisa_marca_contact_saved",
        "lisa_marca_voice_warning_shown",
        "lisa_marca_voice_warning_overridden",
        "lisa_marca_logo_uploaded",
        "lisa_marca_logo_oversized",
        "lisa_marca_extract_website_clicked",
        "lisa_marca_team_preview_clicked",
        "lisa_marca_clinic_config_edit_clicked",
    }
)


class TestGrowthStudioEventNoPHI:
    """Arch gate: vitalia_growth_studio_event must never contain PHI."""

    def test_emitter_file_exists(self) -> None:
        """GrowthStudioEmitter must exist in brand-local _shared/telemetry/."""
        assert EMITTER_PATH.exists(), (
            f"growth_studio_emitter.py not found at {EMITTER_PATH}. Create per ADR-vitalia-004 § 8."
        )

    def test_emitter_uses_brand_local_table_not_engine_table(self) -> None:
        """Emitter must use vitalia_growth_studio_event, not copilot_trace_event."""
        if not EMITTER_PATH.exists():
            pytest.skip("emitter not yet created")
        source = EMITTER_PATH.read_text(encoding="utf-8")
        assert "vitalia_growth_studio_event" in source or "growth_studio_event" in source, (
            "GrowthStudioEmitter must use brand-local table vitalia_growth_studio_event "
            "(ADR-vitalia-004 § 8), NOT copilot_trace_event (engine table)."
        )
        assert "copilot_trace_event" not in source, (
            "GrowthStudioEmitter MUST NOT use copilot_trace_event (engine table). "
            "Use vitalia_growth_studio_event brand-local table per ADR-vitalia-004 § 8."
        )

    def test_no_phi_field_names_in_emitter_props(self) -> None:
        """Emitter must not contain PHI field names as prop keys."""
        if not EMITTER_PATH.exists():
            pytest.skip("emitter not yet created")
        source = EMITTER_PATH.read_text(encoding="utf-8")
        violations = []
        for phi_key in PHI_PROP_KEYS_FORBIDDEN:
            if phi_key in source:
                violations.append(phi_key)
        assert not violations, (
            f"PHI field names found in growth_studio_emitter.py: {violations}. "
            "Remove them — growth_studio_event must never contain PHI per hipaa-lite.md."
        )

    def test_all_13_lisa_marca_events_in_emitter(self) -> None:
        """All 13 lisa_marca_* events must appear in emitter (whitelist enforcement)."""
        if not EMITTER_PATH.exists():
            pytest.skip("emitter not yet created")
        source = EMITTER_PATH.read_text(encoding="utf-8")
        missing = [e for e in REQUIRED_LISA_MARCA_EVENTS if e not in source]
        assert not missing, (
            f"Missing lisa_marca_* events in growth_studio_emitter.py: {missing}. "
            "Add to _KNOWN_EVENT_NAMES per 03-arch § 10.2."
        )

    def test_emit_event_method_uses_bucketed_amounts(self) -> None:
        """emit_event calls must use bucketed values for monetary/size fields."""
        if not EMITTER_PATH.exists():
            pytest.skip("emitter not yet created")
        source = EMITTER_PATH.read_text(encoding="utf-8")
        # Raw PHI-like monetary props must not be passed directly
        forbidden_raw_keys = ["amount_exact", "payment_amount_raw", "monthly_revenue"]
        violations = [k for k in forbidden_raw_keys if k in source]
        assert not violations, (
            f"Raw monetary values found in emitter: {violations}. "
            "Use bucketed values per ADR-vitalia-004 § 8 (e.g., amount_bucket)."
        )

    def test_telemetry_dir_no_phi_in_filenames(self) -> None:
        """Telemetry source files must not have PHI-containing names."""
        if not TELEMETRY_SRC_DIR.exists():
            pytest.skip("telemetry dir not yet created")
        phi_patterns = ["patient", "diagnosis", "treatment", "medication"]
        violations = []
        for f in TELEMETRY_SRC_DIR.iterdir():
            if f.is_file():
                for pattern in phi_patterns:
                    if pattern in f.name.lower():
                        violations.append(f.name)
        assert not violations, (
            f"PHI-containing filenames in telemetry dir: {violations}. Telemetry must be PHI-free per hipaa-lite.md."
        )
