# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""Vitalia copilot observability — schema mirror + recording subclasses.

Per .claude/rules/anti-duplication.md § 0 cardinal:
- All shared abstractions (BaseAgentCallbackHandler, BaseObservabilityContext,
  sanitize_payload, FXResolver, PricingResolver) MUST be imported from
  luana_core_observability — NEVER mirrored.
- Only vitalia-specific overrides live in `recording/callback_handler.py` and
  `recording/turn_envelope.py` (the two abstract persisters and abstract hooks).
"""

from __future__ import annotations
