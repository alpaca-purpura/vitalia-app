"""Architecture fitness — A2: no PII / dynamic interpolation in cacheable slots.

Per Story 11 T-prompts-1 acceptance criterion A2:
  No `{tenant_name}` interpolated mid-block, no patient PII (name/phone/email),
  no timestamps, no random IDs, no conversation_id in slots 1-4 + 6 (cacheable
  cross-tenant). Slot 5 (BRAND_VOICE) is per-tenant — varies legitimately.
  Slot 7-10 NOT cached — exempt.

Spec sources:
  * 02-design-agentic.md § 10.4 forbidden in cache prefix (creep guard)
  * 03-arch-agentic.md § 8.4 idem
  * .claude/rules/sales-agent-brand-voice.md § slot 5 cache prefix invariance
  * 06-tickets.yaml::T-prompts-1 acceptance A2

Validates the LITERAL TEMPLATE TEXT — not runtime substitution. The dynamic
placeholders that LIVE in slot 4 (e.g. `{doctor_specialty}`, `{doctor_name}`,
`{clinic_name}`, `{emergency_line_by_country}`) are LLM-side substitution markers
(model fills at generation time using slot 8 task-specific data). They do NOT
get Python-side interpolated pre-compose, so they preserve cache prefix
invariance. The test's job is to ensure NO Python-side dynamic interpolation
sneaks in.

Pure file inspection — no LLM call, no Postgres required.
"""

from __future__ import annotations

import re

import pytest

from src.modules.vitalia.agentic.prompts.compose import (
    SLOT_1_STATIC_IDENTITY,
    SLOT_2_STATIC_TOOLS_HINT,
    SLOT_6_CHANNEL_FORMAT_HINT,
    cacheable_prefix_blocks,
    load_slot_3_sales_playbook,
    load_slot_4_medical_safety_rails,
)

# ─────────────────────────────────────────────────────────────────────────────
# Forbidden interpolation markers — Python-side dynamic substitution patterns
# ─────────────────────────────────────────────────────────────────────────────

# Patterns indicating Python str.format / f-string interpolation that WOULD
# happen pre-compose (and thus invalidate cache prefix). The test inspects raw
# template text — if these tokens appear in slot 1-4 or 6, it means dynamic
# substitution is happening cross-tenant in cacheable region (forbidden).
_FORBIDDEN_DYNAMIC_TOKENS = [
    "{tenant_name}",  # most common slip — would vary per tenant in cache prefix
    "{tenant_id}",  # cache key, must not appear in content
    "{conversation_id}",  # per-conversation ID, breaks cache prefix
    "{turn_counter}",  # per-turn, breaks cache prefix
    "{turn_id}",  # idem
    "{request_id}",  # random per-request
    "{idempotency_key}",  # random per-request
    "{timestamp}",  # any timestamp form
    "{utcnow}",  # idem
    "{datetime}",  # idem
    "{patient_name}",  # patient PII
    "{patient_phone}",  # patient PII
    "{patient_email}",  # patient PII
    "{patient_dni}",  # patient PII (national IDs LatAm)
    "{patient_rfc}",  # patient PII (Mexico RFC)
    "{patient_rut}",  # patient PII (Chile RUT)
]


# Per-tenant LLM-side substitution markers — ALLOWED in slot 4 (model fills at
# generation time, NOT Python-side pre-compose). Cache prefix invariant because
# the literal `{doctor_specialty}` text is byte-identical cross-tenant.
_ALLOWED_LLM_SIDE_MARKERS = {
    "{doctor_specialty}",
    "{doctor_name}",
    "{clinic_name}",
    "{emergency_line_by_country}",
    "{condición}",  # used in Slot 4 ASÍ NO examples (verbatim Spanish prohibition)
    "{medicación}",  # idem
    "{alternativa}",  # idem
}


# Email regex (RFC 5322 simplified) — surfaces literal email addresses
_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Phone regex — international LATAM phone patterns (heuristic: +CC followed by
# 8+ digits or just 10+ consecutive digits). Avoids false positives on year
# strings (e.g. "2026") by requiring 8+ digit run.
_PHONE_PATTERN = re.compile(r"\+\d{2,3}[\s\-]?\d{3,}[\s\-]?\d{3,}|(?<!\d)\d{10,}(?!\d)")

# ISO timestamp regex — covers "2026-05-13T14:30:00Z" and similar
_TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}(:\d{2})?Z?")


# ─────────────────────────────────────────────────────────────────────────────
# Slot fixtures (raw text, no Python-side substitution applied)
# ─────────────────────────────────────────────────────────────────────────────


def _all_cacheable_slot_texts() -> dict[str, str]:
    """Return dict of slot_name → raw template text for slots 1-4 + 6.

    Slot 5 (BRAND_VOICE per-tenant) NOT included — varies legitimately per
    tenant from personality_profiles.system_instruction.
    Slot 7-10 NOT cached — exempt from this test.
    """
    return {
        "slot_1_static_identity": SLOT_1_STATIC_IDENTITY,
        "slot_2_static_tools_hint": SLOT_2_STATIC_TOOLS_HINT,
        "slot_3_sales_playbook": load_slot_3_sales_playbook(),
        "slot_4_medical_safety_rails": load_slot_4_medical_safety_rails(),
        # Slot 6 has 4 channel variants — test each
        "slot_6_whatsapp": SLOT_6_CHANNEL_FORMAT_HINT["whatsapp"],
        "slot_6_im_dm": SLOT_6_CHANNEL_FORMAT_HINT["im_dm"],
        "slot_6_email": SLOT_6_CHANNEL_FORMAT_HINT["email"],
        "slot_6_web": SLOT_6_CHANNEL_FORMAT_HINT["web"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# A2 — no Python-side dynamic interpolation in cacheable slots
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("slot_name,slot_text", list(_all_cacheable_slot_texts().items()))
def test_no_forbidden_dynamic_interpolation_in_cacheable_slot(slot_name: str, slot_text: str) -> None:
    """A2: cacheable slots must NOT contain forbidden dynamic interpolation tokens.

    Forbidden tokens (e.g. `{tenant_name}`) would mean Python-side substitution
    is happening pre-compose, varying the prefix per tenant/request and
    invalidating Anthropic prompt cache. Per 02-design § 10.4 + 03-arch § 8.4.
    """
    forbidden_found = [tok for tok in _FORBIDDEN_DYNAMIC_TOKENS if tok in slot_text]
    assert not forbidden_found, (
        f"Slot '{slot_name}' contains forbidden dynamic interpolation tokens: "
        f"{forbidden_found}. These would vary per tenant/request and break cache "
        f"prefix invariance per 02-design § 10.4 (creep guard). Move dynamic "
        f"content to Slot 7-10 (NOT cached) or LLM-side substitution markers "
        f"(allowed: {sorted(_ALLOWED_LLM_SIDE_MARKERS)})."
    )


@pytest.mark.parametrize("slot_name,slot_text", list(_all_cacheable_slot_texts().items()))
def test_no_email_addresses_in_cacheable_slot(slot_name: str, slot_text: str) -> None:
    """A2: cacheable slots must NOT contain literal email addresses (PII)."""
    matches = _EMAIL_PATTERN.findall(slot_text)
    assert not matches, (
        f"Slot '{slot_name}' contains literal email address(es) {matches}. "
        f"Patient/clinic emails are PII — per 02-design § 10.4 forbidden in cache "
        f"prefix. Move dynamic emails to Slot 8 task-specific (NOT cached) or "
        f"sanitize via shared sanitize_payload."
    )


@pytest.mark.parametrize("slot_name,slot_text", list(_all_cacheable_slot_texts().items()))
def test_no_phone_numbers_in_cacheable_slot(slot_name: str, slot_text: str) -> None:
    """A2: cacheable slots must NOT contain literal phone numbers (PII)."""
    matches = _PHONE_PATTERN.findall(slot_text)
    # Filter out empty group captures from alternation — keep only non-empty matches
    real_matches = [m for m in matches if (m if isinstance(m, str) else any(m))]
    assert not real_matches, (
        f"Slot '{slot_name}' contains literal phone number(s) {real_matches}. "
        f"Patient/clinic phones are PII — per 02-design § 10.4 forbidden in cache "
        f"prefix. Move dynamic phones to Slot 8 task-specific (NOT cached)."
    )


@pytest.mark.parametrize("slot_name,slot_text", list(_all_cacheable_slot_texts().items()))
def test_no_timestamps_in_cacheable_slot(slot_name: str, slot_text: str) -> None:
    """A2: cacheable slots must NOT contain literal timestamps (would change per turn)."""
    matches = _TIMESTAMP_PATTERN.findall(slot_text)
    assert not matches, (
        f"Slot '{slot_name}' contains literal timestamp(s) {matches}. "
        f"Timestamps would vary per turn and break cache prefix per "
        f"02-design § 10.4 (creep guard). Move per-turn data to Slot 8."
    )


# ─────────────────────────────────────────────────────────────────────────────
# A2 — Slot 4 LLM-side markers ARE allowed (acknowledge cross-design)
# ─────────────────────────────────────────────────────────────────────────────


def test_slot_4_uses_only_allowed_llm_side_markers() -> None:
    """A2: Slot 4 LLM-side substitution markers (`{doctor_specialty}` etc.)
    must come from the allowlist — protects against accidental new dynamic
    placeholder slipping in (would silently break cache prefix if Python-side
    substituted in future).

    Allowed markers are LLM-substituted at generation time (model reads slot 8
    task-specific context to fill them) — they appear LITERALLY in the cache
    prefix as the `{name}` token, byte-identical cross-tenant.
    """
    slot_4 = load_slot_4_medical_safety_rails()
    found_markers = set(re.findall(r"\{[a-zA-Záéíóúñ_]+\}", slot_4))
    not_allowed = found_markers - _ALLOWED_LLM_SIDE_MARKERS
    assert not not_allowed, (
        f"Slot 4 contains placeholder(s) NOT in the allowlist: {not_allowed}. "
        f"Allowed LLM-side markers: {sorted(_ALLOWED_LLM_SIDE_MARKERS)}. "
        f"Adding a new marker here requires extending _ALLOWED_LLM_SIDE_MARKERS "
        f"AND verifying the orchestrator/specialist-runtime fills it AT generation "
        f"time (NOT Python-side pre-compose, which would break cache prefix)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# A2 — cacheable_prefix_blocks() byte-equal across tenants (slots 1-4 + 6)
# ─────────────────────────────────────────────────────────────────────────────


def test_cacheable_prefix_byte_equal_across_distinct_tenants() -> None:
    """A2 cement: cacheable prefix slots 1-4 + 6 byte-equal cross-tenant.

    Two distinct tenants with the SAME channel + DIFFERENT brand_voice MUST
    produce byte-identical content for slots 1-4 + 6 (only Slot 5 BRAND_VOICE
    legitimately varies). Validates that the compose pipeline does NOT inject
    tenant-specific data into shared slots.
    """
    aurora_voice = "Voz Aurora AR voseo: 'che, mirá, qué onda'"
    mindful_voice = "Voz Mindful CL neutro: 'tú, mira, ¿qué tal?'"

    aurora_blocks = cacheable_prefix_blocks(channel="whatsapp", brand_voice_compiled=aurora_voice)
    mindful_blocks = cacheable_prefix_blocks(channel="whatsapp", brand_voice_compiled=mindful_voice)

    # Slots 1, 2, 3, 4, 6 (indices 0, 1, 2, 3, 5) MUST byte-match.
    # Slot 5 (index 4) is BRAND_VOICE — legitimately differs.
    invariant_indices = [0, 1, 2, 3, 5]
    for idx in invariant_indices:
        assert aurora_blocks[idx]["text"] == mindful_blocks[idx]["text"], (
            f"Slot at index {idx} differs between Aurora vs Mindful tenants. "
            f"Cacheable cross-tenant slots (1-4 + 6) MUST be byte-identical so "
            f"Anthropic prompt cache prefix matches per spec § 8.4."
        )

    # Sanity: slot 5 DOES differ (would be a test bug if not).
    assert aurora_blocks[4]["text"] != mindful_blocks[4]["text"], (
        "Slot 5 BRAND_VOICE should differ between distinct tenants — test fixture is wrong if they match."
    )


def test_cacheable_prefix_each_block_has_cache_control_marker() -> None:
    """A2: every cacheable slot block carries `cache_control: ephemeral` marker.

    Per spec § 8.2 — Anthropic Messages API cache only activates on blocks with
    explicit `cache_control` annotation. Missing marker = no cache hit possible.
    """
    blocks = cacheable_prefix_blocks(channel="whatsapp", brand_voice_compiled="any voice")
    for idx, block in enumerate(blocks):
        assert block.get("cache_control") == {"type": "ephemeral"}, (
            f"Cacheable slot at index {idx} missing cache_control marker. "
            f"Anthropic prompt cache requires explicit cache_control on each "
            f"block per spec § 8.2."
        )
