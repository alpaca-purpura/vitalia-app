# luana-core-llm

**Version:** 0.0.1-alpha  
**Lift origin:** `AISALESHT/backend/src/shared/infrastructure/llm/`  
**Lift commit:** `ecc53cc` (feat(luana-core-llm): lift LLM infrastructure)

## Overview

LLM routing and provider infrastructure. Single dispatch path via LiteLLM Proxy.
No per-provider adapters — all model calls go through `LiteLLMService`.

## Key exports

- `luana_core_llm.factory.LLMFactory` — `get_service(role)` → `LiteLLMService`
- `luana_core_llm.router.MultiRoleLLMRouter` — routes by `ModelRole` enum
- `luana_core_llm.providers.litellm.LiteLLMService` — single runtime dispatch provider
- `luana_core_llm.enums.ModelRole` — NANO / FAST / REASONING / AGENT / VISION / EMBEDDING roles
