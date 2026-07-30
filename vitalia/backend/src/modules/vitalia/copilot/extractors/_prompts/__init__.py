# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""Jinja2 prompt templates for `MedicalKBExtractor` (T-extractors-1).

4 wave templates — each declares INVARIANT prefix (cacheable per Anthropic
prompt cache contract, slot 1-3) BEFORE any variable input. Variable
content (PDF page text + tenant-specific data) goes AFTER the
``<<CACHE_BOUNDARY>>`` marker.

Templates loaded by ``MedicalKBExtractor`` via plain string read (no
Jinja2 rendering — placeholders substituted with simple `.format(...)`
to keep cache prefix byte-identical across tenants).

Anthropic prompt cache invariants per `claude-api` skill:
  * Slot 1 (system role) — IDENTICAL across all calls of this template.
  * Slot 2 (output schema) — IDENTICAL.
  * Slot 3 (extraction rules) — IDENTICAL.
  * <<CACHE_BOUNDARY>> marker stripped before send; ``cache_control``
    parameter applied to the last invariant block.
  * Slot 4+ (variable PDF content) — per-call.

NEVER interpolate ``{tenant_name}``, ``{patient_id}``, timestamps, or
random IDs into the cache prefix — silent invalidator.
"""
