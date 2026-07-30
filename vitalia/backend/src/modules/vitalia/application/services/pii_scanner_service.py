# cap: __shared__
# story-origin: TBD
"""PiiScannerService — pre-persist PII detection for offer descriptions + testimonial inputs.

Vitalia medical vertical extension of the AISALESHT shared PII patterns.
Detects: email / phone / AR DNI / CL RUT / MX RFC / MX CURP + medical-specific.

Pattern SSoT:
  - Base patterns reused from luana_core_observability.recording.sanitization
    (which covers email / phone / LATAM national IDs / credit cards).
  - Vitalia-local additions: RUT CL (formatted) + AR DNI (formatted) +
    MX RFC (structural) + MX CURP (structural) — patterns aligned with
    AISALESHT/backend/scripts/_pii_patterns.py (Story D lifted SSoT).

Anti-duplication (anti-duplication.md):
  grep cross-codebase found NO existing OnboardingService / ComplianceEventService /
  PiiScannerService in luana-platform or AISALESHT (Step 0 GATE clear).
  sanitize_payload is consumed from luana_core_observability — NEVER re-implemented here.

References:
  - spec § 3.2.D + § 3.3.D (PII scan pre-persist offer + testimonial)
  - spec § 15.2 (V-AE-2: 10 PII inputs detected)
  - 03-arch-be.md § 9.7
  - 05-guidelines.md § 1.6
  - V-F-14: integration test smoke_pii_detection.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final

import structlog

logger = structlog.get_logger()


# ── PII Regex catalog (vitalia-local SSoT) ──────────────────────────────────
#
# Patterns aligned with AISALESHT/backend/scripts/_pii_patterns.py canonical
# set. Vitalia uses a compiled-regex version for performance (scan is
# synchronous hot path called pre-persist).
#
# Note: base sanitize_payload (luana_core_observability) handles redaction
# post-detection for audit log writes. This service handles PRE-PERSIST
# DETECTION (block or log) for offer.description + testimonial.quote.

_PATTERN_SPECS: dict[str, str] = {
    # Email — RFC 5321 practical subset
    "email": r"(?<![a-zA-Z0-9._%+-])([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?![a-zA-Z0-9.])",
    # International phone with country code (+54, +56, +52, etc.)
    "phone": r"(?<![\d])(\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{0,4})(?![\d])",
    # AR DNI formatted: 12.345.678 — lookahead excludes '-' to avoid false-positive on CL RUT
    "dni_ar": r"(?<![\d.])(\d{1,2}\.\d{3}\.\d{3})(?![\d.-])",
    # CL RUT formatted: 12.345.678-9 or 9.876.543-2 (digit or K suffix)
    # Pattern requires dots to distinguish from bare numeric sequences.
    "rut_cl": r"(?<![\d])(\d{1,2}\.\d{3}\.\d{3}-[\dkK])(?![\d])",
    # MX RFC — structural uppercase 12-13 chars (3-4 letters + 6 digits + 3 alphanum)
    "rfc_mx": r"(?<![A-Z])([A-ZÑ&]{3,4}\d{6}[A-Z\d]{3})(?![A-Z\d])",
    # MX CURP — structural 18 chars (4 letters + 6 digits + H|M + 5 letters + 1 alphanum + 1 digit)
    "curp_mx": r"(?<![A-Z])([A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z\d]\d)(?![A-Z\d])",
}

# Compiled pattern cache
_COMPILED_PATTERNS: dict[str, re.Pattern[str]] = {
    category: re.compile(pattern) for category, pattern in _PATTERN_SPECS.items()
}

# Categories that trigger a BLOCK (caller decides whether to reject or log+warn).
# Email and phone are blocking for offer/testimonial surfaces — they expose
# real contact info of patients/practitioners publicly.
BLOCKING_CATEGORIES: Final[frozenset[str]] = frozenset(
    {
        "email",
        "phone",
        "dni_ar",
        "rut_cl",
        "rfc_mx",
        "curp_mx",
    }
)


# ── Result model ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PiiScanResult:
    """Result of a PII scan.

    Attributes:
        detected: List of PII category names found in the text.
        blocked: True if any detected category is in BLOCKING_CATEGORIES.
    """

    detected: list[str] = field(default_factory=list)
    blocked: bool = False

    def __bool__(self) -> bool:
        return bool(self.detected)


# ── Service ──────────────────────────────────────────────────────────────────


class PiiScannerService:
    """Pre-persist PII detection for offer descriptions + testimonial inputs.

    Synchronous scan (no I/O) called in hot path before any offer.description
    or testimonial.quote is written to the DB. If blocked, callers MUST either
    reject the write or emit a ComplianceEventService.log_event call.

    Usage (D1 — services receive deps via DI, no direct DB access):
        scanner = PiiScannerService()
        result = scanner.scan(offer.description)
        if result.blocked:
            await compliance_svc.log_event("pii_detected", "high", ...)
            raise PiiDetectedError(result.detected)

    This service is stateless — shared singleton OK.
    """

    def scan(self, text: str) -> PiiScanResult:
        """Scan text for PII categories.

        Returns:
            PiiScanResult with detected categories and blocked flag.
            Empty detected list if no PII found.
        """
        if not text or not text.strip():
            return PiiScanResult(detected=[], blocked=False)

        detected: list[str] = []
        for category, pattern in _COMPILED_PATTERNS.items():
            if pattern.search(text):
                detected.append(category)

        blocked = any(c in BLOCKING_CATEGORIES for c in detected)

        if detected:
            logger.info(
                "pii_scanner_detected",
                categories=detected,
                blocked=blocked,
                text_length=len(text),
            )

        return PiiScanResult(detected=detected, blocked=blocked)
