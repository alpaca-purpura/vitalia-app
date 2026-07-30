---
module: onboarding
brand: vitalia
last_updated: 2026-05-18
---

# onboarding — Wizard Brand Studio + 3 pasos clínica

Onboarding multi-step para clínicas Vitalia. Dos niveles complementarios:

1. **Bootstrap rápido (3 pasos)**: tipo (dental/psicología/psiquiatría/wellness) → perfil + país + moneda → plan tier (49/199/599 USD). Integrado con Clerk para provisioning de tenant.
2. **Wizard conversacional agentic (Slice 1 2026-05-18)**: chat-LEFT 50/50 con Valeria + voz Adrián REAL backend wire desde primer setup + slot-filling adaptativo NLU + extracción URL/doc (audio Whisper DEFERRED Slice 2 per Chris OQ-3). 9 componentes FE + 6 hooks + 4 Valeria tools + LangGraph supervisor con AsyncPostgresSaver. KPIs target: ≥95% completion rate, ≤$0.10 USD/session, ≥30% cache hit rate iter 2+.

## Capabilities

<!-- auto-list:start -->
- `clinic-onboarding-3step` (live)
- `wizard-brand-studio-slice-1` (live)
<!-- auto-list:end -->
