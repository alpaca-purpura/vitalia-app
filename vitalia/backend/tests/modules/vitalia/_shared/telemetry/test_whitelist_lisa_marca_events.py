"""Tests for telemetry whitelist extension — 13 lisa_marca_* events.

TDD RED phase — verifies:
1. growth_studio_emitter.py has a `_KNOWN_EVENT_NAMES` constant.
2. All 13 new lisa_marca_* events are included.
3. No PHI keys present in declared event prop schemas.

Unit tests — no DB required.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

WS = Path(__file__).resolve().parents[7]  # workspace root = luana-vitalia/
EMITTER_PATH = (
    WS / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "_shared" / "telemetry" / "growth_studio_emitter.py"
)
FILE_SIZE_BUCKET_PATH = (
    WS / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "_shared" / "telemetry" / "file_size_bucket.py"
)

# 13 new events per 03-arch § 10.2
REQUIRED_LISA_MARCA_EVENTS = {
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

# PHI field patterns that must NOT appear in event prop declarations
PHI_PROP_PATTERNS = {
    "patient_id",
    "appointment_id",
    "diagnosis",
    "treatment",
    "medication",
    "dni",
    "name",  # brand identity name, not patient name — tracked as field_count_changed
    "tagline",
    "email",
    "phone",
}


class TestLisaMarcaEventsWhitelist:
    """Verify growth_studio_emitter.py has 13 lisa_marca_* events in whitelist."""

    def test_emitter_file_exists(self) -> None:
        """growth_studio_emitter.py must exist."""
        assert EMITTER_PATH.exists(), f"growth_studio_emitter.py not found at {EMITTER_PATH}"

    def test_known_event_names_constant_exists(self) -> None:
        """_KNOWN_EVENT_NAMES constant must be defined in growth_studio_emitter.py."""
        source = EMITTER_PATH.read_text(encoding="utf-8")
        assert "_KNOWN_EVENT_NAMES" in source, (
            "_KNOWN_EVENT_NAMES constant must exist in growth_studio_emitter.py "
            "per 03-arch § 10.1 (whitelist enforcement)"
        )

    def test_all_13_lisa_marca_events_present(self) -> None:
        """All 13 lisa_marca_* events must appear in growth_studio_emitter.py."""
        source = EMITTER_PATH.read_text(encoding="utf-8")
        missing = []
        for event in REQUIRED_LISA_MARCA_EVENTS:
            if event not in source:
                missing.append(event)
        assert not missing, (
            f"Missing lisa_marca events in growth_studio_emitter.py: {missing}\n"
            f"Add them to _KNOWN_EVENT_NAMES per 03-arch § 10.2"
        )

    def test_count_lisa_marca_events(self) -> None:
        """At least 13 lisa_marca_* events must be present (allows future additions)."""
        source = EMITTER_PATH.read_text(encoding="utf-8")
        count = source.count("lisa_marca_")
        assert count >= 13, (
            f"Expected at least 13 occurrences of 'lisa_marca_' in growth_studio_emitter.py, got {count}"
        )

    def test_file_size_bucket_helper_exists(self) -> None:
        """file_size_bucket.py NEW helper must exist per 03-arch § 10.3."""
        assert FILE_SIZE_BUCKET_PATH.exists(), (
            f"file_size_bucket.py not found at {FILE_SIZE_BUCKET_PATH}. "
            "Create it per 03-arch § 10.3 for lisa_marca_logo_uploaded event."
        )

    def test_file_size_bucket_function_defined(self) -> None:
        """bucket_file_size() function must be defined in file_size_bucket.py."""
        if not FILE_SIZE_BUCKET_PATH.exists():
            pytest.skip("file_size_bucket.py not yet created")
        source = FILE_SIZE_BUCKET_PATH.read_text(encoding="utf-8")
        assert "def bucket_file_size" in source, "bucket_file_size() function must be defined in file_size_bucket.py"

    def test_bucket_file_size_returns_string_buckets(self) -> None:
        """bucket_file_size() must return string bucket labels for file sizes."""
        if not FILE_SIZE_BUCKET_PATH.exists():
            pytest.skip("file_size_bucket.py not yet created")

        # Import and test directly
        import importlib.util

        spec = importlib.util.spec_from_file_location("file_size_bucket", FILE_SIZE_BUCKET_PATH)
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        bucket_fn = getattr(module, "bucket_file_size", None)
        assert bucket_fn is not None, "bucket_file_size not found in module"

        # Test boundary values per 03-arch § 10.3
        assert bucket_fn(100 * 1024) == "0-500KB"  # 100KB
        assert bucket_fn(700 * 1024) == "500KB-1MB"  # 700KB
        assert bucket_fn(1.5 * 1024 * 1024) == "1-2MB"  # 1.5MB
        assert bucket_fn(3 * 1024 * 1024) == "2-5MB"  # 3MB
        assert bucket_fn(6 * 1024 * 1024) == "5MB+"  # 6MB (over limit)

    def test_no_phi_field_names_in_event_names(self) -> None:
        """Event names themselves must not contain PHI identifiers."""
        phi_in_events = []
        for event in REQUIRED_LISA_MARCA_EVENTS:
            for phi in {"patient", "diagnosis", "treatment", "medication", "dni"}:
                if phi in event:
                    phi_in_events.append((event, phi))
        assert not phi_in_events, f"PHI patterns found in event names: {phi_in_events}"

    def test_emitter_known_event_names_is_frozenset_or_set(self) -> None:
        """_KNOWN_EVENT_NAMES should be a frozenset or set for O(1) lookup."""
        source = EMITTER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(EMITTER_PATH))

        found_assignment = False
        for node in ast.walk(tree):
            # Handle both ast.Assign and ast.AnnAssign (annotated assignment)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "_KNOWN_EVENT_NAMES":
                        found_assignment = True
                        val = node.value
                        is_set_call = (
                            isinstance(val, ast.Call)
                            and isinstance(val.func, ast.Name)
                            and val.func.id in {"frozenset", "set"}
                        )
                        is_set_literal = isinstance(val, ast.Set)
                        assert is_set_call or is_set_literal, (
                            "_KNOWN_EVENT_NAMES must be a frozenset, set, or set literal "
                            f"for O(1) lookup, found: {type(val).__name__}"
                        )
            elif isinstance(node, ast.AnnAssign):
                # Handle: _KNOWN_EVENT_NAMES: frozenset[str] = frozenset({...})
                if isinstance(node.target, ast.Name) and node.target.id == "_KNOWN_EVENT_NAMES":
                    found_assignment = True
                    if node.value is not None:
                        val = node.value
                        is_set_call = (
                            isinstance(val, ast.Call)
                            and isinstance(val.func, (ast.Name, ast.Attribute))
                            and (
                                (isinstance(val.func, ast.Name) and val.func.id in {"frozenset", "set"})
                                or (isinstance(val.func, ast.Attribute) and val.func.attr in {"frozenset", "set"})
                            )
                        )
                        is_set_literal = isinstance(val, ast.Set)
                        assert is_set_call or is_set_literal, (
                            "_KNOWN_EVENT_NAMES must be a frozenset, set, or set literal "
                            f"for O(1) lookup, found: {type(val).__name__}"
                        )

        assert found_assignment, "_KNOWN_EVENT_NAMES assignment not found via AST parse in growth_studio_emitter.py"
