# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""Vitalia copilot observability recording — callback handler + turn envelope subclasses.

Per anti-duplication §0 cardinal: subclasses ONLY. Plumbing lives in engine
luana_core_observability.recording.{base_callback_handler, turn_envelope}.
"""

from __future__ import annotations

from src.modules.vitalia.copilot.observability.recording.callback_handler import (
    VitaliaCopilotCallbackHandler,
)
from src.modules.vitalia.copilot.observability.recording.turn_envelope import (
    VitaliaCopilotObservabilityContext,
)

__all__ = [
    "VitaliaCopilotCallbackHandler",
    "VitaliaCopilotObservabilityContext",
]
