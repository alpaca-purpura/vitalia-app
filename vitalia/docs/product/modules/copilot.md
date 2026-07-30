---
module: copilot
brand: vitalia
last_updated: 2026-05-20
---

# copilot — KB médico RAG + extractors PDF + Valeria wizard onboarding agentic

Extensión brand de `core/luana-core-copilot`. 3 KB packs (dental ~150 chunks, psychology ~200 + crisis boundary, psychiatry 131 + forced disclaimer) registrados vía EP-14. 2 PDF extractors 4-wave vision-based (genérico + dental con FDI notation) heredando `BaseExtractionOrchestrator` (no mirror).

Wave 3-4 (2026-05-18 vitalia-copilot-tools-impl): Valeria wizard supervisor LangGraph + 4 tools (extract_tenant_context, confirm_slot, simulate_personality, complete_onboarding) + deepagents SubAgentMiddleware extract_subagent isolation + AsyncPostgresSaver checkpointer + 5-slot prompt cache architecture + VitaliaCopilotCallbackHandler subclass (anti-dup §0).

## Capabilities

<!-- auto-list:start -->
- `medical-kb-rag` (live)
- `medical-pdf-extractors` (live)
- `valeria-wizard-onboarding-agentic` (live · 2026-05-18)
- `inbox-tools-extensions` (live · 2026-05-20)
<!-- auto-list:end -->
