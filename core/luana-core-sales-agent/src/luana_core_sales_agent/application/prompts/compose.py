"""Cache-friendly system-prompt composer for sales_agent specialists (S3).

OpenAI prompt cache (April 2026) requires ≥1024 contiguous tokens of unchanged
prefix to activate. Kimi K2.6 and DeepSeek V3/V4 ship the same auto-cache
contract over OpenAI-compatible APIs (no ``cache_control`` annotations, just
prefix stability). This module is the single source of truth for fragment
ordering — every other piece of the sales orchestrator declares which slot
its content goes into and ``compose_system_prompt`` enforces the canonical
sequence.

Order rationale (cacheable prefix → volatile tail):

    1. STATIC_IDENTITY      — universally cacheable across tenants.
    2. STATIC_TOOLS_HINT    — tools description, stable per route.
    3. SALES_PLAYBOOK_HINT  — humanization + signals + active specialist body.
    4. AGENT_IDENTITY       — per-tenant WHO+WHAT (brand+offers+team+legal). NO voice.
    5. BRAND_VOICE          — per-tenant HOW (PersonalityProfile.system_instruction).
    6. CHANNEL_FORMAT_HINT  — placeholder for S5 channel registry split.
    7. CAMPAIGN_CONTEXT     — PR-7 outbound campaign instructions (emitted only when outbound_mode=True).
    --- CACHE BOUNDARY (≥1024 tokens by design above this line) ---
    8. STAGE_HINT           — current_state + lead_score + turn_count.
    9. LEAD_SIGNALS         — qualification_answers + buying_signals + objections.
    10. SESSION_CONTINUITY  — session_gap_hours + last_session_summary + RAG.
    11. TOOL_REQUEST_FORMAT — closing instruction for [TOOL_REQUEST: {...}] blocks.

Adding a new fragment? Append to ``PromptFragment``, slot it into either
``CACHEABLE_FRAGMENTS`` or ``VOLATILE_FRAGMENTS``, and update the matching
arch-test snapshot. Order changes are deliberate — the test file is the
audit log.

# [SALES-AGENT-CACHE-PREFIX-S3] -> docs/domains/sales-agent/redesign-2026-04/phases/S3-prompt-cache-boundary.md
"""

from __future__ import annotations

import json
from enum import StrEnum
from typing import TYPE_CHECKING

import structlog

from luana_core_sales_agent.infrastructure.prompts.base import prompt_loader
from luana_core_channels.format import get_channel_format

if TYPE_CHECKING:
    from collections.abc import Mapping

    from luana_core_brand_studio.application.ports.brand_voice_port import (
        BrandVoicePort,
    )
    from luana_core_sales_agent.application.orchestrator.state import AgentState


logger = structlog.get_logger(__name__)


class PromptFragment(StrEnum):
    """Named slots in the system prompt assembly.

    The string value is also used in trace recorder payloads so changing
    one is a wire-format change.
    """

    # ── Cacheable prefix (stable across turns) ────────────────────────
    STATIC_IDENTITY = "static_identity"
    STATIC_TOOLS_HINT = "static_tools_hint"
    SALES_PLAYBOOK_HINT = "sales_playbook_hint"
    AGENT_IDENTITY = "agent_identity"
    BRAND_VOICE = "brand_voice"
    CHANNEL_FORMAT_HINT = "channel_format_hint"
    CAMPAIGN_CONTEXT = "campaign_context"  # PR-7: per-campaign invariant within turn
    # ── Volatile tail (changes per turn) ──────────────────────────────
    STAGE_HINT = "stage_hint"
    LEAD_SIGNALS = "lead_signals"
    SESSION_CONTINUITY = "session_continuity"
    TOOL_REQUEST_FORMAT = "tool_request_format"


CACHEABLE_FRAGMENTS: tuple[PromptFragment, ...] = (
    PromptFragment.STATIC_IDENTITY,
    PromptFragment.STATIC_TOOLS_HINT,
    PromptFragment.SALES_PLAYBOOK_HINT,
    PromptFragment.AGENT_IDENTITY,
    PromptFragment.BRAND_VOICE,
    PromptFragment.CHANNEL_FORMAT_HINT,
    PromptFragment.CAMPAIGN_CONTEXT,  # PR-7: emitted only when outbound_mode=True
)

VOLATILE_FRAGMENTS: tuple[PromptFragment, ...] = (
    PromptFragment.STAGE_HINT,
    PromptFragment.LEAD_SIGNALS,
    PromptFragment.SESSION_CONTINUITY,
    PromptFragment.TOOL_REQUEST_FORMAT,
)

PROMPT_FRAGMENT_ORDER: tuple[PromptFragment, ...] = (
    CACHEABLE_FRAGMENTS + VOLATILE_FRAGMENTS
)

CACHE_BOUNDARY_MARKER: str = "\n\n<!-- ==== CACHE BOUNDARY (S3) ==== -->\n\n"
"""Inserted between the cacheable prefix and the volatile tail. Renders as
an HTML comment in markdown (LLM ignores it) but is greppable in trace
inspections to confirm the boundary is where it should be."""

_FRAGMENT_SEPARATOR: str = "\n\n"


def compose_system_prompt(fragments: Mapping[PromptFragment, str]) -> str:
    """Assemble fragments in canonical S3 cache-friendly order.

    Empty / missing fragments are skipped. Each rendered fragment has its
    leading and trailing whitespace stripped; double-newline separates
    consecutive fragments. The cache-boundary marker is inserted only when
    at least one fragment exists on each side (skips it for trivial bootstrap
    cases).

    Pure data: deterministic, side-effect free, thread-safe.
    """
    cache_parts = _take(fragments, CACHEABLE_FRAGMENTS)
    volatile_parts = _take(fragments, VOLATILE_FRAGMENTS)

    if not cache_parts and not volatile_parts:
        return ""
    if not volatile_parts:
        return _FRAGMENT_SEPARATOR.join(cache_parts)
    if not cache_parts:
        return _FRAGMENT_SEPARATOR.join(volatile_parts)

    return (
        _FRAGMENT_SEPARATOR.join(cache_parts)
        + CACHE_BOUNDARY_MARKER
        + _FRAGMENT_SEPARATOR.join(volatile_parts)
    )


def _take(
    fragments: Mapping[PromptFragment, str],
    slots: tuple[PromptFragment, ...],
) -> list[str]:
    """Pull fragments by slot order, dropping empty / whitespace-only entries."""
    out: list[str] = []
    for slot in slots:
        raw = fragments.get(slot, "")
        cleaned = (raw or "").strip()
        if cleaned:
            out.append(cleaned)
    return out


# ---------------------------------------------------------------------------
# High-level builder: state + role → composed prompt
# ---------------------------------------------------------------------------


class SpecialistRole(StrEnum):
    """Specialists that participate in cache_boundary refactor.

    Supervisor is intentionally OUT OF SCOPE: max_output_tokens=10 +
    ``ModelRole.FAST`` make cache wins negligible while its prompt is
    state-heavy by design.
    """

    QUALIFIER = "qualifier"
    PRODUCT_EXPERT = "product_expert"
    CLOSER = "closer"


_SPECIALIST_TEMPLATE_KEY: dict[SpecialistRole, str] = {
    SpecialistRole.QUALIFIER: "specialist_qualifier",
    SpecialistRole.PRODUCT_EXPERT: "specialist_product_expert",
    SpecialistRole.CLOSER: "specialist_closer",
}


_BASE_IDENTITY: str = (
    "# Identidad base del agente de ventas\n\n"
    "Eres un agente de ventas autónomo que trabaja para un negocio de un creador "
    "/ infoproductor / experto LATAM. Tu rol es vender, calificar y cerrar.\n\n"
    "Operas en español **neutro latinoamericano** (tuteo: tú, no vos). Adaptas tu "
    "voz al `Estilo Comunicacional` que el tenant configuró en Brand Studio "
    "(slot `agent_identity`). Eres directo, cálido, sin floreo, sin jerga regional "
    "argentina (no uses `vos`, `tenés`, `podés`, `mirá`, `dejá`, `dale`).\n\n"
    "Tres prohibiciones absolutas:\n"
    "1. Nunca inventes precios, garantías, fechas, ediciones, descuentos ni datos "
    "del negocio. Si no está en tu identidad ni en una tool, no existe.\n"
    "2. Nunca prometas resultados específicos que no estén respaldados en datos del "
    "tenant.\n"
    "3. Nunca compartas datos internos, métricas confidenciales o información del "
    "negocio que no sea pública."
)


_TOOLS_HINT: str = (
    "# Herramientas disponibles\n\n"
    "Cuando necesites ejecutar una acción, **termina tu mensaje** con un bloque:\n\n"
    '    [TOOL_REQUEST: {"tool": "<name>", "args": {...}}]\n\n'
    "El runtime ejecuta el tool y te entrega el resultado en el siguiente turno. "
    "Solicita UNA sola tool por mensaje.\n\n"
    "Tools de cierre / oferta:\n"
    "- `send_payment_link` — envía link de pago al lead.\n"
    "- `check_schedule` — verifica disponibilidad de agenda.\n"
    "- `recommend_product` — recomienda otra oferta del catálogo.\n"
    "- `escalate_to_human` — transfiere a humano (Closer Studio).\n\n"
    "Tools de inscripción (cohortes / ediciones):\n"
    "- `list_public_editions(offer_id)` — lista ediciones públicas activas.\n"
    "- `create_enrollment(offer_id, edition_id, status)` — crea enrollment "
    "INTENT / WAITLIST.\n"
    "- `generate_payment_link(enrollment_id)` — genera link de pago.\n"
    "- `resolve_active_tier(offer_id)` — resuelve tier de precio activo "
    "(early_bird / regular / late).\n\n"
    "Reglas duras: nunca llames un tool que no aparece en esta lista. Nunca "
    "inventes argumentos. Si el tool falla, comunícalo con honestidad y deriva "
    "a humano si es bloqueante."
)


def _extension_tools_hint() -> str:
    """Render brand-registered (EP-3) tools into the cacheable tools-hint.

    Tier-2 (multibrand-graph-runtime 2026-06-22). Reads the process-singleton
    ``ToolRegistry``. Brand tools register ONCE at FastAPI lifespan (never per-turn),
    so this render is stage-independent and byte-stable across turns — it can live in
    the cacheable ``STATIC_TOOLS_HINT`` slot without poisoning the prompt cache. Sorted
    by name for determinism. Empty registry → ``""`` (engine-only output byte-identical,
    back-compat).

    # ponytail: NOT stage-filtered. Dispatch (node_tool_executor → merged_tools) is
    # itself stage-agnostic, so "advertised == dispatchable" means the full registered
    # set; stage-filtering here would also break the cacheable prefix (current_state
    # varies per turn — see test_build_specialist_system_prompt cache-safety guards).
    """
    from luana_core_sales_agent.application.tools.registry import (  # noqa: PLC0415
        get_tool_registry,
    )

    tools = get_tool_registry().extension_tools()
    if not tools:
        return ""

    lines: list[str] = [
        "# Herramientas de marca",
        "",
        "Estas herramientas las provee la marca para su vertical. **Si el prospecto pide "
        "o necesita algo que una de estas herramientas cubre, USALA en vez de responder "
        "de memoria** — terminá tu mensaje con UN bloque `[TOOL_REQUEST: {...}]` usando el "
        "nombre EXACTO (con prefijo de marca). Leé la descripción para saber cuándo aplica. "
        "Nunca inventes el nombre; si el tool falla, comunicálo con honestidad.",
        "",
    ]
    for name in sorted(tools):
        # Collapse internal whitespace/newlines so a multi-line description can't
        # break the one-bullet-per-tool markdown (purely cosmetic; the value is
        # static per-process either way, so cache stability never depended on it).
        tool = tools[name]
        desc = " ".join((tool.description or "").split())
        lines.append(f"- `{name}` — {desc}" if desc else f"- `{name}`")
        # Concrete imperative example (matches the proven specialist_closer pattern —
        # models follow few-shot examples far more reliably than abstract directives).
        # Args derived DYNAMICALLY from the tool's own input_schema (brand-agnostic:
        # the engine never hardcodes a brand tool's args), minus state-injected keys
        # (tenant_id/clinic_id/lead_id/… come from state, not the LLM). Static per
        # process → cache-safe.
        example_args = _example_tool_args(getattr(tool, "input_schema", None))
        lines.append(
            f'  Ejemplo: [TOOL_REQUEST: {{"tool": "{name}", "args": {example_args}}}]'
        )
    return "\n".join(lines)


# Args the engine injects from per-turn state — the LLM must NOT supply them, so they
# are excluded from the rendered example (mirror of tool_bridge authoritative/fallback
# keys; keep in sync if those change).
_STATE_INJECTED_ARG_KEYS: frozenset[str] = frozenset(
    {"tenant_id", "clinic_id", "lead_id", "user_id", "conversation_id"},
)


def _example_tool_args(input_schema: dict | None) -> str:
    """Render a minimal JSON example of the LLM-supplied args for a brand tool.

    Brand-agnostic: reads the tool's own ``input_schema.properties``, drops the
    state-injected keys, and shows up to 3 remaining arg names with ``"<...>"``
    placeholders. Empty → ``{}`` (the tool is fully state-driven). Stable per
    process (the schema is fixed at registration) → cache-safe.
    """
    props: dict = {}
    if isinstance(input_schema, dict):
        raw = input_schema.get("properties")
        if isinstance(raw, dict):
            props = raw
    llm_keys = [k for k in props if k not in _STATE_INJECTED_ARG_KEYS]
    if not llm_keys:
        return "{}"
    shown = llm_keys[:3]
    body = ", ".join(f'"{k}": "<...>"' for k in shown)
    return "{" + body + "}"


def _compose_tools_hint() -> str:
    """Engine tools-hint ⊕ brand extension tools-hint (cacheable slot 2 content)."""
    brand = _extension_tools_hint()
    return f"{_TOOLS_HINT}\n\n{brand}" if brand else _TOOLS_HINT


def _render_static_specialist_body(role: SpecialistRole) -> str:
    """Render the specialist Jinja template with NO state kwargs.

    All ``{% if state_var %}`` guards in the templates are written so that
    missing kwargs render as empty (Jinja ``Undefined`` is falsy in default
    env). The output is therefore the static framework + rules + format
    sections only — cacheable cross-tenant.

    PromptVersionModel overrides for ``specialist_<role>`` keys land here
    naturally: the override replaces the body, still cached.
    """
    key = _SPECIALIST_TEMPLATE_KEY[role]
    try:
        return prompt_loader.render(key)
    except Exception:
        logger.exception("compose_specialist_render_failed", role=role.value)
        return ""


def _stage_hint(state: AgentState) -> str:
    parts: list[str] = ["# Estado del turno"]
    parts.append(f"- Stage actual: {state.get('current_state') or 'rapport'}")
    parts.append(f"- Lead score: {state.get('lead_score') or 0}")
    parts.append(f"- Turno: {state.get('turn_count') or 0}")
    intent = state.get("detected_intent")
    if intent:
        parts.append(f"- Intent detectado: {intent}")
    last_specialist = state.get("last_specialist") if hasattr(state, "get") else None
    if last_specialist:
        parts.append(f"- Último especialista: {last_specialist}")
    return "\n".join(parts)


def _lead_signals(state: AgentState) -> str:
    qual = state.get("qualification_answers") or {}
    signals = state.get("buying_signals") or []
    objections = state.get("objection_history") or []
    if not (qual or signals or objections):
        return ""

    parts: list[str] = ["# Señales acumuladas"]
    if qual:
        parts.append(
            f"- Calificación recopilada: {json.dumps(qual, ensure_ascii=False, sort_keys=True)}"
        )
    if signals:
        parts.append(
            f"- Señales de compra ({len(signals)}): {json.dumps(signals, ensure_ascii=False, sort_keys=True)}"
        )
    if objections:
        unresolved = [o for o in objections if not o.get("resolved")]
        parts.append(
            f"- Objeciones acumuladas ({len(objections)} total, {len(unresolved)} sin resolver): "
            f"{json.dumps(objections, ensure_ascii=False, sort_keys=True)}",
        )
    return "\n".join(parts)


def _session_continuity(state: AgentState) -> str:
    parts: list[str] = []
    gap = state.get("session_gap_hours")
    if gap is not None:
        parts.append(f"- Tiempo desde la última sesión: {round(float(gap), 1)} horas")
        if gap < 6:
            parts.append("  - **NO saludes**: continúa directo donde quedaron.")
        elif gap < 24:
            parts.append(
                '  - Saludo breve: "¡Hola de nuevo!" + referencia breve a lo que quedó.'
            )
        elif gap < 168:
            parts.append("  - Saludo cálido + mención breve de en qué quedaron.")
        else:
            parts.append(
                "  - Re-contacto: saludo + recordatorio de quién eres + cómo le va."
            )

    summary = state.get("last_session_summary")
    if summary:
        parts.append(f"- Resumen de sesión anterior: {summary}")

    consecutive = state.get("consecutive_questions") or 0
    if consecutive >= 3:
        parts.append(
            f"- ⚠️ Has hecho {consecutive} preguntas consecutivas como qualifier. "
            "Da valor antes de la próxima pregunta.",
        )

    rag = state.get("context_rag")
    if rag:
        parts.append(f"\n## Contexto adicional (knowledge base)\n{rag}")

    if not parts:
        return ""
    return "# Continuidad de sesión\n" + "\n".join(parts)


def _campaign_context(state: AgentState) -> str:
    """PR-7 — slot 7 per-campaign invariant within outbound turn.

    Emitted ONLY when ``outbound_mode=True`` AND ``campaign_instructions``
    non-empty. Preserves cache prefix per-tenant: slots 1-6
    (STATIC_IDENTITY → CHANNEL_FORMAT_HINT) remain byte-equal across inbound
    and outbound for the same tenant. Campaign-specific instructions land
    AFTER channel format so the per-tenant cache prefix stays invariante.
    Cache hit rate ≥60% per-tenant preserved (sales-agent-brand-voice.md
    SACRA invariant).

    Builder NEVER injects ``{tenant_name}`` or ``{campaign_name}`` mid-block
    — instructions are emitted verbatim from ``campaign_instructions``.
    Only slot 4 ``AGENT_IDENTITY`` carries tenant identifiers.

    # [SALES-AGENT-OUTBOUND-PR7]
    """
    if not state.get("outbound_mode"):
        return ""

    instructions = (state.get("campaign_instructions") or "").strip()
    if not instructions:
        return ""

    return (
        "# Contexto de campaña\n\n"
        "Estás iniciando una conversación outbound. El usuario aún no respondió. "
        "Tu primer turno debe abrir la conversación según las siguientes "
        "instrucciones de campaña, manteniendo la voz de marca declarada arriba.\n\n"
        f"## Instrucciones de campaña\n\n{instructions}"
    )


def _channel_format_hint(state: AgentState) -> str:
    """S5 — slot 6 cacheable per-tenant.

    Resuelve ``state.channel_type`` via ``shared.agent_observability.channels``
    registry y devuelve el ``structure_hint`` declarativo del canal. Cuando
    ``channel_type`` viene None / '' / unknown, ``get_channel_format`` cae al
    baseline ``chat`` — el slot queda con un hint válido en vez de vacío,
    favoreciendo cache hit estable cross-turn.
    """
    channel_type = state.get("channel_type")
    if not channel_type:
        return ""
    fmt = get_channel_format(channel_type)
    return f"# Reglas del canal ({fmt.label_es})\n\n{fmt.structure_hint}"


def _tool_request_format() -> str:
    return (
        "# Formato de cierre\n\n"
        "Si necesitas ejecutar una herramienta, agrega al final del mensaje:\n\n"
        '    [TOOL_REQUEST: {"tool": "<name>", "args": {...}}]\n\n'
        "Si detectaste señales de compra u objeciones nuevas, agrega:\n\n"
        '    [SIGNALS: {"buying": [...], "objections": [...]}]\n\n'
        "Si recolectaste datos de calificación, agrega:\n\n"
        '    [QUALIFICATION_DATA: {"name": "...", "business_type": "...", ...}]'
    )


def build_specialist_system_prompt(state: AgentState, role: SpecialistRole) -> str:
    """Resolve fragments from ``state`` and ``role`` then compose.

    Cacheable slots come from constants + Jinja static render + tenant
    ``agent_identity``. Volatile slots come from per-turn state. The output
    is a single string with ``CACHE_BOUNDARY_MARKER`` between halves —
    OpenAI / Kimi / DeepSeek auto-detect the stable prefix.
    """
    fragments: dict[PromptFragment, str] = {
        PromptFragment.STATIC_IDENTITY: _BASE_IDENTITY,
        PromptFragment.STATIC_TOOLS_HINT: _compose_tools_hint(),
        PromptFragment.SALES_PLAYBOOK_HINT: _render_static_specialist_body(role),
        PromptFragment.AGENT_IDENTITY: state.get("agent_identity") or "",
        PromptFragment.BRAND_VOICE: state.get("brand_voice") or "",
        PromptFragment.CHANNEL_FORMAT_HINT: _channel_format_hint(state),
        PromptFragment.CAMPAIGN_CONTEXT: _campaign_context(state),  # PR-7
        PromptFragment.STAGE_HINT: _stage_hint(state),
        PromptFragment.LEAD_SIGNALS: _lead_signals(state),
        PromptFragment.SESSION_CONTINUITY: _session_continuity(state),
        PromptFragment.TOOL_REQUEST_FORMAT: _tool_request_format(),
    }
    return compose_system_prompt(fragments)


# ---------------------------------------------------------------------------
# D-T3 hexagonal consumer — Story 7 ADR-001 §2.4 BrandVoicePort wiring
# ---------------------------------------------------------------------------


async def compose_prompt(
    specialist: SpecialistRole | str,
    state: AgentState,
    voice_port: BrandVoicePort,
) -> str:
    """Compose the specialist system prompt with slot 5 sourced via D-T3 BrandVoicePort.

    Story 7 ADR-001 §2.4 + 03-arch-agentic.md §3 cardinal: cross-package
    consumers (luana-core-sales-agent) MUST consume voice via
    ``BrandVoicePort.compile_system_instruction`` — NEVER import
    ``PersonalityCompiler`` directly. ``BrandVoicePort`` lives in
    ``luana_core_brand_studio.application.ports`` and is a Protocol —
    sales-agent depends on the abstraction, brand_studio binds the concrete
    implementation in its composition root.

    Cache prefix invariants preserved:

    - Slot 5 BRAND_VOICE source changes from upstream
      ``knowledge_builder.build_brand_voice`` (sync, brand_port-backed) to
      ``await voice_port.compile_system_instruction(tenant_id)`` (async,
      Story 5 PersonalityCompiler-backed via brand-studio service binding).
    - Slot order remains identical (see ``PROMPT_FRAGMENT_ORDER`` SSoT).
    - ``CACHE_BOUNDARY_MARKER`` placement unchanged — Slots 1-7 cacheable
      prefix, Slots 8-11 volatile tail.
    - Per-tenant TTL 5min default (ephemeral cache_control) — voice
      recompiles when tenant edits ``PersonalityProfile`` in Brand Studio.

    Side effects on ``state``:

    - Writes ``state["brand_voice"]`` with the compiled voice text (empty
      string if tenant has no active profile — consumer falls back to
      specialist default).
    - Writes ``state["voice_metadata"]`` with
      ``{personality_profile_version, last_compiled_at, dimensions_summary}``
      for downstream cache invalidation + routing decisions.

    Args:
        specialist: ``SpecialistRole`` enum or string matching role value.
            Accepts both for back-compat with upstream callers passing the
            string-typed ``current_specialist`` from ``SalesAgentState``.
        state: ``AgentState`` (TypedDict) — read-write for slot 5 voice
            population.
        voice_port: ``BrandVoicePort`` Protocol implementation injected via
            DI from the orchestrator composition root.

    Returns:
        Single composed system prompt string in canonical S3 cache-friendly
        order, ready to feed to the specialist LLM as the system message.

    Raises:
        Never — voice_port failures are best-effort: an exception in
        ``compile_system_instruction`` is caught + logged + slot 5 falls
        back to empty (preserving turn liveness per S0-S12 resilience
        contract).
    """
    tenant_id = state.get("tenant_id")
    if tenant_id is None:
        # No tenant context — skip voice injection, fall back to specialist default.
        logger.warning("compose_prompt_missing_tenant_id")
    else:
        try:
            brand_voice_text = await voice_port.compile_system_instruction(tenant_id)
            voice_metadata = await voice_port.get_voice_metadata(tenant_id)
            state["brand_voice"] = brand_voice_text or ""
            state["voice_metadata"] = voice_metadata or {}
        except Exception:  # noqa: BLE001 — best-effort, preserve turn liveness
            logger.exception(
                "compose_prompt_voice_port_failed",
                tenant_id=str(tenant_id),
                specialist=str(specialist),
            )
            # Leave existing state["brand_voice"] in place (may be from prior turn).

    # Resolve specialist role enum (accept str or enum for callers passing
    # current_specialist directly from SalesAgentState).
    role = (
        specialist
        if isinstance(specialist, SpecialistRole)
        else SpecialistRole(str(specialist))
    )

    return build_specialist_system_prompt(state, role)


__all__ = (
    "CACHEABLE_FRAGMENTS",
    "CACHE_BOUNDARY_MARKER",
    "PROMPT_FRAGMENT_ORDER",
    "VOLATILE_FRAGMENTS",
    "PromptFragment",
    "SpecialistRole",
    "build_specialist_system_prompt",
    "compose_prompt",
    "compose_system_prompt",
)
