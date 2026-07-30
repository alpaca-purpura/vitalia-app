"""Shared PII detection library for the pre-commit eval-data gates (HB-18).

Used by ``scripts/scan_seed_pii.py`` (eval tenant seeds, whitelist-aware) and
``scripts/scan_goldens_pii.py`` (sales_agent goldens, strict — no whitelist).
Both are invoked by ``scripts/git-hooks/pre-commit`` §8/§9 against the *full*
fixture directory (not just the staged diff), so PII introduced in a previously
clean file is caught on any later commit that touches the dir.

Detection philosophy (deliberately conservative — this feeds a HARD gate):
  - We flag only HIGH-confidence real-PII vectors so the gate never false-blocks
    legitimate *synthetic* fixtures. The repo's synthetic-first convention uses
    placeholders that this scanner treats as clean by construction:
      * emails on example.* / test / localhost domains
      * phones with the +99 synthetic country code (e.g. "+99 0 1234 5678")
      * bare digit runs as fake national IDs (e.g. DNI "12345678") — NOT flagged
  - Two vectors are flagged:
      1. EMAIL on a real consumer mail domain (gmail/hotmail/yahoo/…).
      2. PHONE in international format with a real LatAm/ES/US country code,
         excluding obviously-synthetic digit patterns (repeated/sequential).
  - National-format phones (no country code) and free-text real names are OUT OF
    SCOPE for v1: detecting them generically false-positives on synthetic DNIs
    and Spanish placeholder names. Documented limitation — see
    ``.claude/rules/pii-sanitisation.md``.

Exit-code contract (entrypoints): 0=clean, 1=PII detected, 2=error.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Real consumer mail domains — a hit here is high-confidence PII. Synthetic
# fixtures never use these (they use example.com / @example.* per convention).
REAL_EMAIL_DOMAINS: frozenset[str] = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "hotmail.com",
        "hotmail.es",
        "outlook.com",
        "outlook.es",
        "live.com",
        "live.com.mx",
        "msn.com",
        "yahoo.com",
        "yahoo.es",
        "yahoo.com.mx",
        "ymail.com",
        "icloud.com",
        "me.com",
        "protonmail.com",
        "proton.me",
        "gmx.com",
        "gmx.es",
        "zoho.com",
        "aol.com",
    }
)

# Real country codes that show up in LatAm/ES/US data. +99 is the synthetic
# sentinel used by the repo's placeholders, so it is intentionally absent.
REAL_PHONE_COUNTRY_CODES: tuple[str, ...] = (
    "1",  # US/CA
    "34",  # ES
    "51",  # PE
    "52",  # MX
    "54",  # AR
    "55",  # BR
    "56",  # CL
    "57",  # CO
    "58",  # VE
    "502",  # GT
    "503",  # SV
    "504",  # HN
    "505",  # NI
    "506",  # CR
    "507",  # PA
    "591",  # BO
    "593",  # EC
    "595",  # PY
    "598",  # UY
)

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@([A-Za-z0-9.\-]+\.[A-Za-z]{2,})")
# International phone: +<cc><sep?><7..13 digits with optional separators>.
_PHONE_RE = re.compile(r"\+(\d{1,3})[\s().\-]?(\d[\d\s().\-]{6,}\d)")


@dataclass(frozen=True)
class Finding:
    relpath: str
    lineno: int
    kind: str  # "email" | "phone"
    snippet: str


def _digits_only(s: str) -> str:
    return re.sub(r"\D", "", s)


def _is_synthetic_phone(national_digits: str) -> bool:
    """True if the national part looks like a deliberate placeholder."""
    d = national_digits
    if len(set(d)) <= 1:  # all same digit: 0000000, 1111111
        return True
    if d in ("12345678", "123456789", "1234567890"):
        return True
    if d.startswith("01234") or d.startswith("12345"):
        return True
    return False


def _scan_text(relpath: str, text: str, whitelist_terms: frozenset[str]) -> list[Finding]:
    findings: list[Finding] = []
    for i, raw in enumerate(text.splitlines(), start=1):
        line = raw
        # Whitelist: skip lines containing any whitelisted literal term.
        if whitelist_terms and any(term and term in line for term in whitelist_terms):
            continue

        for m in _EMAIL_RE.finditer(line):
            domain = m.group(1).lower()
            if domain in REAL_EMAIL_DOMAINS:
                findings.append(Finding(relpath, i, "email", m.group(0)))

        for m in _PHONE_RE.finditer(line):
            cc = m.group(1)
            national = _digits_only(m.group(2))
            if cc not in REAL_PHONE_COUNTRY_CODES:
                continue
            if len(national) < 7:  # too short to be a real subscriber number
                continue
            if _is_synthetic_phone(national):
                continue
            findings.append(Finding(relpath, i, "phone", m.group(0).strip()))

    return findings


def _load_whitelist(root: Path) -> frozenset[str]:
    """Read ``.eval-whitelist`` (one literal term per line, ``#`` comments)."""
    wl = root / ".eval-whitelist"
    if not wl.is_file():
        return frozenset()
    terms: set[str] = set()
    for line in wl.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            terms.add(s)
    return frozenset(terms)


def scan_directory(root: Path, *, use_whitelist: bool) -> list[Finding]:
    """Scan every ``*.yaml`` / ``*.yml`` under ``root`` for PII.

    ``use_whitelist`` enables the per-dir ``.eval-whitelist`` escape (seeds);
    goldens pass ``use_whitelist=False`` (strict, synthetic-first invariant).
    """
    root = root.resolve()
    whitelist_terms = _load_whitelist(root) if use_whitelist else frozenset()
    findings: list[Finding] = []
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in (".yaml", ".yml") or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = str(path.relative_to(root))
        findings.extend(_scan_text(rel, text, whitelist_terms))
    return findings


def format_findings(findings: list[Finding]) -> str:
    lines = []
    for f in findings:
        lines.append(f"  {f.relpath}:{f.lineno}  [{f.kind}]  {f.snippet}")
    return "\n".join(lines)
