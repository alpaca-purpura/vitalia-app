# luana-core-extraction

**Version:** 0.0.1-alpha  
**Lift origin:** `AISALESHT/backend/src/shared/application/extraction/base_orchestrator.py`  
**Lift commit:** `313d1cc` (feat(luana-core-extraction): lift extraction orchestrator)

## Overview

Wave-based LLM extraction base class. Any module that owns an LLM extraction
pipeline (brand, offer, buyer_persona, landing) subclasses this to get
scheduling, progress emission, and wave composition for free.

## Key exports

- `luana_core_extraction.base_orchestrator.BaseExtractionOrchestrator` — abstract base for wave-based LLM extraction pipelines; subclass and implement `_merge_and_save()` + `run()`
