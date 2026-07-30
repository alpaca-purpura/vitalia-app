# cap: __shared__
# story-origin: TBD
"""PHI masking utilities — HIPAA-lite compliant display projections.

Rule (vitalia/.claude/rules/hipaa-lite.md § PHI fields canónicos):
  Patient identity PHI must be masked before any API response.
  - patient.name → 'P. Apellido' format (initial + last name)
  - patient.dni  → '12.***.***' format (first 2 digits + asterisks)
  - patient.phone → masked: first 3 + asterisks
  - patient.email → masked: first 2 chars of local + domain

Usage:
    from src.modules.vitalia._shared.phi_masking import mask_name, mask_dni

    masked_name = mask_name("Pedro Hernández")   # → "P. Hernández"
    masked_dni  = mask_dni("12345678")           # → "12.***"
"""

from __future__ import annotations

__all__ = ["mask_name", "mask_dni", "mask_phone", "mask_email"]


def mask_name(full_name: str) -> str:
    """Mask a patient name to 'Initial. Apellido' format.

    Rule: first-name initial + period + last name.
    Fallback: if name is empty or single-char, returns 'P.' (placeholder initial).

    Examples:
        mask_name("Pedro Hernández")    → "P. Hernández"
        mask_name("Ana María González") → "A. González"
        mask_name("Juan")               → "J."
        mask_name("")                   → "P."

    Args:
        full_name: Raw patient full name (PHI).

    Returns:
        Masked name string safe for display in agenda grid / drawer.
    """
    if not full_name or not full_name.strip():
        return "P."

    parts = full_name.strip().split()
    initial = parts[0][0].upper() if parts[0] else "P"
    # Last name = last token in the list
    last_name = parts[-1] if len(parts) > 1 else ""

    if last_name:
        return f"{initial}. {last_name}"
    return f"{initial}."


def mask_dni(dni: str) -> str:
    """Mask a DNI/NIF to '12.***' format (first 2 digits + asterisks).

    Handles Argentine DNI (8 digits), Chilean RUT (8-9 chars), Colombian CC,
    Peruvian DNI (8 digits), Mexican CURP (18 chars), etc.

    Examples:
        mask_dni("12345678")  → "12.***"
        mask_dni("1234")      → "12**"
        mask_dni("AB12345")   → "AB***"

    Args:
        dni: Raw DNI/document number (PHI).

    Returns:
        Masked document string safe for audit display.
    """
    if not dni or not dni.strip():
        return "**"

    clean = dni.strip()
    if len(clean) <= 2:
        return clean + "**"

    prefix = clean[:2]
    return f"{prefix}.***"


def mask_phone(phone: str) -> str:
    """Mask a phone number to '+XX *** *** ***' format.

    Examples:
        mask_phone("+51987654321") → "+51 *** *** ***"
        mask_phone("987654321")   → "987 *** ***"

    Args:
        phone: Raw phone number (PHI).

    Returns:
        Masked phone string safe for display.
    """
    if not phone or not phone.strip():
        return "*** *** ***"

    clean = phone.strip()
    # Keep country code if present
    if clean.startswith("+"):
        country_code_end = min(3, len(clean))
        prefix = clean[:country_code_end]
        return f"{prefix} *** *** ***"

    # Domestic number: keep area code (first 3 digits)
    prefix = clean[:3]
    return f"{prefix} *** ***"


def mask_email(email: str) -> str:
    """Mask an email address to 'ab***@domain.com' format.

    Examples:
        mask_email("pedro@clinica.com") → "pe***@clinica.com"
        mask_email("a@b.com")          → "a***@b.com"

    Args:
        email: Raw email address (PHI).

    Returns:
        Masked email string safe for display.
    """
    if not email or "@" not in email:
        return "***@***.***"

    local, domain = email.split("@", 1)
    if not local:
        return f"***@{domain}"

    visible = local[:2] if len(local) >= 2 else local[:1]
    return f"{visible}***@{domain}"
