# cap: brand_studio.brand-studio-medical-sections
# story-origin: vitalia-fase2-s7-TBD
"""Vitalia brand_studio brand-extension module.

Brand-local wrapper for engine luana_core_brand_studio.
Adds audit_log + telemetry + voice_preview cache + prohibited_phrases.

Anti-creep guards (per .claude/rules/sales-agent-brand-voice.md):
  - NO health_voice_validator.py (arch test enforces)
  - NO brand_voice_summary table (arch test enforces)
  - NO LLM validator, NO fine-tuning per tenant
"""
