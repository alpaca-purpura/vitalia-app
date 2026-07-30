---
module: observability
brand: vitalia
last_updated: 2026-05-18
---

# observability — OpenTelemetry + Sentry + Vitalia callback subclasses

Stack de tracing distribuído (OTel BatchSpanProcessor) + alertas declarative IaC (Sentry) con graceful degradation cuando SDKs absent (dev venv).

11 NAMED cron span constants en `cron_spans.py`. PHI sanitization en agent_spans via import from `compliance/` (anti-duplication compliant — sanitize_phi_payload de engine).

Wave 3 (2026-05-18 vitalia-copilot-tools-impl): VitaliaCopilotCallbackHandler + VitaliaSalesAgentCallbackHandler subclasses heredan engine `BaseAgentCallbackHandler` (anti-dup §0 cardinal — ratchet enforced via arch fitness 25+ forbidden override methods). Overrides solo persist hooks con vitalia-specific fields (clinic_id + compliance_level=hipaa_lite).

## Capabilities

<!-- auto-list:start -->
- `vitalia-otel-sentry-graceful-degradation` (live)
- `vitalia-callback-subclasses` (live · 2026-05-18)
<!-- auto-list:end -->
