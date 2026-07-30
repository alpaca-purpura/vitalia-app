"""Copilot prompt loader (overrides shared PromptLoader to use this package's templates).

Canonical PromptLoader class: ``luana_core_platform.infrastructure.prompts.base``.

This package re-exports `PromptLoader` but instantiates its OWN `prompt_loader`
singleton pointing at the local templates directory inside this package. The
shared default path (``src/modules/copilot/infrastructure/prompts/templates``)
is an AISALESHT relic; luana-platform layout places templates under
``core/luana-core-copilot/src/luana_core_copilot/infrastructure/prompts/templates``.

This override is the recommended pattern per M8 (parallel-safety.md): extend
shared layer by providing a local instance, do NOT modify shared default.
"""

from pathlib import Path

from luana_core_platform.infrastructure.prompts.base import PromptLoader

# Local templates directory inside this package
_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

# Override singleton: instantiate with absolute path to local templates
prompt_loader = PromptLoader(templates_dir=str(_TEMPLATES_DIR))

__all__ = ["PromptLoader", "prompt_loader"]
