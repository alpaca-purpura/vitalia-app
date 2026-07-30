# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Lucas growth setter slot prompts (Anthropic prompt caching).

Per 03-arch-agentic § 5.3 — Lucas 3-slot cache architecture:
  SLOT 1 — Lucas growth setter persona       (cacheable per-brand)
  SLOT 2 — Stage-specific reasoning frame    (cacheable per-stage)
                                              ↑ cache_control marker HERE (1h TTL — batch nature) ↑
  SLOT 3 — Tenant data + period stats        (variable, NOT cached)

TTL 1h: batch nature — slots 1+2 reused across all tenants per cron run.
Break-even at 3 reads (Anthropic prompt caching). Cron runs 5 stages × N tenants
per day = high read multiple, makes 1h economical.

Forbidden in cache prefix (slots 1+2):
  - Timestamps · Conversation IDs · Turn counters · `{tenant_name}` interpolated
  - Period inline (period belongs in SLOT 3 — variable per tenant)
"""
