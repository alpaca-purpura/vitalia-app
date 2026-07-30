# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""Vitalia copilot KB packs — registered via EP-14 in extensions.py.

Skeleton package created Story 11 T-extensions-1. KB pack ingestion lands in:
  T-kb-1 → medical_kb_dental_v1
  T-kb-2 → medical_kb_psychology_v1
  T-kb-3 → medical_kb_psychiatry_v1

Each pack: brand-scoped Qdrant collection (cross-tenant share — medical reference
content, not per-tenant PHI). tenant_scope='brand' enforced via KbPackDef.
"""
