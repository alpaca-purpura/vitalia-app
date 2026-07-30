# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Lucas growth setter LangGraph workflows package.

Story: vitalia-copilot-tools-impl T-ag-workflows-2 (R23 Opus 4.7 production AGENTIC code).

Exposes:
- LucasAnalysisState — TypedDict state schema per 03-arch-agentic § 2.3.
- build_lucas_daily_analysis_graph — factory per 03-arch-agentic § 3.4.
- LucasAnalysisPromptCompiler — Anthropic prompt cache slot composer per § 5.3.

Anti-duplication audit (per .claude/rules/anti-duplication.md):
- Uses langgraph official `StateGraph` + `MemorySaver` (no mirror).
- No equivalent ReAct graph in `core/luana-core-*/` (vitalia-specific medical growth).
- `AsyncPostgresSaver` deferred — `langgraph.checkpoint.postgres` package not installed
  yet; tests use `MemorySaver` (matches `treatment_followup_workflow` pattern D10).
"""

from src.modules.vitalia.agentic.lucas.workflows.lucas_analysis_state import (
    LucasAnalysisState,
    Stage,
)
from src.modules.vitalia.agentic.lucas.workflows.lucas_daily_analysis_graph import (
    build_lucas_daily_analysis_graph,
)
from src.modules.vitalia.agentic.lucas.workflows.lucas_prompt_compiler import (
    LucasAnalysisPromptCompiler,
)

__all__ = [
    "LucasAnalysisPromptCompiler",
    "LucasAnalysisState",
    "Stage",
    "build_lucas_daily_analysis_graph",
]
