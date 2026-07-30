#!/usr/bin/env python3
"""Scan sales_agent golden YAMLs for real PII (HB-18) — STRICT, no whitelist.

Invoked by ``scripts/git-hooks/pre-commit`` §9 against the full goldens dir
``{brand}/backend/tests/agentic_evals/sales_agent/goldens/`` (per-brand or
legacy root). Synthetic-first invariant (spec D10): zero PII in goldens, NO
whitelist exceptions — any real PII is a bug.

Usage:  python scan_goldens_pii.py <dir>
Exit:   0=clean, 1=PII detected, 2=error
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _pii_scan_lib import format_findings, scan_directory  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: scan_goldens_pii.py <dir>", file=sys.stderr)
        return 2
    root = Path(argv[1])
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    try:
        findings = scan_directory(root, use_whitelist=False)
    except Exception as exc:  # noqa: BLE001 — gate must not crash silently
        print(f"error scanning {root}: {exc}", file=sys.stderr)
        return 2
    if findings:
        print(f"PII detected in goldens dir {root} ({len(findings)} finding(s)):", file=sys.stderr)
        print(format_findings(findings), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
