#!/usr/bin/env python3
"""emit.py — embedded telemetry emitter (KIT-03 · the ONLINE plane of medicion.schema).

Runs in the CLIENT DATA-PLANE, wired by the plugin's Claude Code hooks (Stop ·
SubagentStop · SessionEnd — see hooks/hooks.json). Each firing parses the NEW lines of
the session transcript (byte-offset incremental), assembles trace/spans conforming to
``telemetry/medicion.schema.yaml`` (byte-synced copy of the L0 contract — the factory
gate enforces equality), writes them to a LOCAL SINK outside the repo, and — only if
the machine has egress config — POSTs the SAFE STRATUM as OTLP GenAI-semconv spans to
the operator backend (Langfuse; receiver proven in OBS-11).

THE KEY (Option A / I-53): a walk over every ``egreso: sensible`` field (harvested from
the schema at runtime, never hardcoded) runs BEFORE any egress; one violation = nothing
is emitted. v1 does not even capture prompt/output (only ``output_hash``); the capture
capability exists behind ``--capture-sensible`` solely so the factory check can prove
the walk bites (negative test) — it is never wired into the hooks.

FAIL-OPEN (RN-1): in hook mode this process ALWAYS exits 0; telemetry must never block,
break, or noticeably slow a session. ``--strict`` (factory checks only) surfaces errors
as nonzero exits.

Dual-mode (RN-7): works installed as a plugin (${CLAUDE_PLUGIN_ROOT}) and as a plain
``cp -r`` of core-harness/ (path-relative fallback).

Config (outside the repo — never committed):
  env  PRENTER_TELEMETRY_SINK_DIR · _OTLP_ENDPOINT · _OTLP_PUBLIC_KEY · _OTLP_SECRET_KEY
  file ~/.config/prenter/observatorio.yaml → ``telemetry:`` block, falling back to the
       top-level ``otlp_endpoint``/``otlp_public_key``/``otlp_secret_key`` keys the
       operator already has (zero-edit reuse). No config → local sink only, zero egress.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "medicion.schema.yaml"
DEFAULT_SINK = Path.home() / ".prenter" / "telemetry"
CONFIG_PATH = Path.home() / ".config" / "prenter" / "observatorio.yaml"
POST_TIMEOUT_S = 10

# $/MTok per model-id prefix (official reference cached 2026-06-24; longest prefix wins).
# cache read = 0.1x input · cache write 5m = 1.25x · 1h = 2x. Unknown model → cost omitted.
TARIFAS = {
    "claude-fable-5": (10.0, 50.0),
    "claude-mythos": (10.0, 50.0),
    "claude-opus-4": (5.0, 25.0),
    "claude-sonnet-5": (3.0, 15.0),
    "claude-sonnet-4": (3.0, 15.0),
    "claude-haiku-4": (1.0, 5.0),
}


# ---------------------------------------------------------------- config
def load_config() -> dict:
    cfg = {"sink_dir": None, "otlp_endpoint": None, "otlp_public_key": None, "otlp_secret_key": None}
    try:
        if CONFIG_PATH.is_file():
            import yaml  # the kit already depends on PyYAML; fail-open if absent

            raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
            tel, backend = raw.get("telemetry") or {}, raw.get("backend") or {}
            for key in cfg:
                # telemetry: block > backend: block (operator's existing file, zero edits) > top-level
                cfg[key] = tel.get(key, backend.get(key, raw.get(key)))
    except Exception:
        pass  # unreadable config is not the session's problem (RN-1)
    for key in cfg:
        env = os.environ.get("PRENTER_TELEMETRY_" + key.upper())
        if env:
            cfg[key] = env
    cfg["sink_dir"] = Path(cfg["sink_dir"]) if cfg["sink_dir"] else DEFAULT_SINK
    return cfg


def sensitive_fields() -> set[str]:
    """Harvest ``egreso: sensible`` field names from the schema (RN-2 — never hardcoded)."""
    import yaml

    med = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    return {
        name
        for block in med.values()
        if isinstance(block, dict)
        for name, spec in block.items()
        if isinstance(spec, dict) and spec.get("egreso") == "sensible"
    }


# ---------------------------------------------------------------- transcript parsing
# Echoes of local slash-commands travel as `user` lines with string content and no
# `origin` — same shape as a headless prompt. These wrappers tell them apart (KIT-07).
COMMAND_WRAPPERS = ("<command-name>", "<local-command-stdout>", "<local-command-caveat>")


def _starts_turn(line: dict) -> bool:
    """Turn-detection v2 (KIT-07). Interactive human prompts carry a truthy ``origin``;
    headless ``claude -p`` prompts carry none — so a plain-string ``user`` line without
    ``origin`` also opens a turn, unless it is harness noise: meta lines, sidechain
    (subagent) prompts, tool results, or local-command wrappers."""
    if line.get("type") != "user":
        return False
    if line.get("origin"):
        return True
    if line.get("isMeta") or line.get("isSidechain") or line.get("sourceToolUseID") is not None:
        return False
    content = (line.get("message") or {}).get("content")
    return isinstance(content, str) and not content.lstrip().startswith(COMMAND_WRAPPERS)


def _ts(line: dict):
    raw = line.get("timestamp")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _turn_has_usage(turn: dict) -> bool:
    return any(ln.get("type") == "assistant" and (ln.get("message") or {}).get("usage")
               for ln in turn["lines"])


def parse_turns(path: Path, start_offset: int, mode: str):
    """Read transcript lines from ``start_offset``; group them into turns.

    A turn starts at a ``user`` line that ``_starts_turn`` accepts (interactive prompt
    with ``origin``, or headless prompt without it — KIT-07); tool results / meta lines
    continue the current turn. Only COMPLETE lines are consumed (a partial trailing line
    stays for the next firing).

    ``mode`` decides the fate of the TRAILING open turn:
      - ``"hold"`` (SubagentStop, fires mid-turn): always held back — neither emitted nor
        consumed — so its remaining lines land in one span on the next Stop/SessionEnd.
      - ``"stop"`` (Stop): closed, UNLESS it has no assistant usage yet — in print-mode
        (``claude -p``) Stop can fire before the assistant lines are flushed to the
        transcript (caught in the 0.5.1 beta smoke); the usage-less turn is held for
        SessionEnd instead of emitting an empty span.
      - ``"final"`` (SessionEnd): everything closes — last chance, emit what there is.
    Returns (turns, consumed_offset).
    """
    turns, current = [], None
    consumed = start_offset
    with open(path, "rb") as fh:
        fh.seek(start_offset)
        for raw in fh:
            if not raw.endswith(b"\n"):
                break  # partial line still being written — leave it for the next firing
            try:
                line = json.loads(raw)
            except json.JSONDecodeError:
                consumed += len(raw)
                continue
            if _starts_turn(line):
                current = {"lines": [line], "_starts_at": consumed}
                turns.append(current)
            elif current is not None:
                current["lines"].append(line)
            consumed += len(raw)
    if turns and (mode == "hold" or (mode == "stop" and not _turn_has_usage(turns[-1]))):
        held = turns.pop()  # open turn stays for the next firing
        consumed = held["_starts_at"]
    return turns, consumed


def _turn_spans(turn: dict, seq: int, capture_sensible: bool) -> list[dict]:
    """One turn → a main span (+ one child span if sidechain traffic is visible)."""
    lines = turn["lines"]
    stamps = [t for t in (_ts(ln) for ln in lines) if t]
    latency_ms = int((max(stamps) - min(stamps)).total_seconds() * 1000) if len(stamps) > 1 else None

    usage_by_msg, side_usage = {}, {}
    skill = model = None
    final_text: list[str] = []
    loaded, results_by_tool = [], {}
    for ln in lines:
        if ln.get("type") == "user" and ln.get("sourceToolUseID") is not None:
            content = ln.get("toolUseResult")
            if isinstance(content, str):
                results_by_tool[ln["sourceToolUseID"]] = content
        if ln.get("type") != "assistant":
            continue
        msg = ln.get("message") or {}
        bucket = side_usage if ln.get("isSidechain") else usage_by_msg
        if msg.get("usage") and msg.get("id"):
            bucket[msg["id"]] = msg["usage"]  # same message spans N lines → dedupe by id
        if not ln.get("isSidechain"):
            skill = skill or ln.get("attributionSkill")
            model = model or msg.get("model")
            for block in msg.get("content") or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text" and block.get("text"):
                    final_text.append(block["text"])
                elif block.get("type") == "tool_use" and block.get("name") == "Read":
                    fpath = (block.get("input") or {}).get("file_path", "")
                    result = results_by_tool.get(block.get("id"), "")
                    loaded.append({
                        "path": fpath,
                        "tokens": max(1, len(result) // 4) if result else 0,
                        "hash": hashlib.sha256((result or fpath).encode()).hexdigest()[:16],
                    })

    def aggregate(bucket: dict) -> dict:
        tok = {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0}
        write_5m = write_1h = 0
        for u in bucket.values():
            tok["input"] += u.get("input_tokens", 0)
            tok["output"] += u.get("output_tokens", 0)
            tok["cache_read"] += u.get("cache_read_input_tokens", 0)
            tok["cache_creation"] += u.get("cache_creation_input_tokens", 0)
            sub = u.get("cache_creation") or {}
            write_5m += sub.get("ephemeral_5m_input_tokens", 0)
            write_1h += sub.get("ephemeral_1h_input_tokens", 0)
        if write_5m + write_1h == 0:  # sub-breakdown absent → assume default 5m TTL
            write_5m = tok["cache_creation"]
        return tok | {"_write_5m": write_5m, "_write_1h": write_1h}

    def costo(tok: dict, model_id: str | None):
        rate = next((TARIFAS[p] for p in sorted(TARIFAS, key=len, reverse=True)
                     if model_id and model_id.startswith(p)), None)
        if not rate:
            return None
        inp, outp = rate
        usd = (tok["input"] * inp + tok["output"] * outp + tok["cache_read"] * inp * 0.1
               + tok["_write_5m"] * inp * 1.25 + tok["_write_1h"] * inp * 2.0) / 1e6
        return {"usd": round(usd, 6)}

    def strip(tok: dict) -> dict:
        return {k: v for k, v in tok.items() if not k.startswith("_")}

    main_tok = aggregate(usage_by_msg)
    context_sizes = [u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                     + u.get("cache_creation_input_tokens", 0) for u in usage_by_msg.values()]
    span_id = hashlib.sha256(f"{seq}:{turn.get('_session', '')}".encode()).hexdigest()[:16]
    output_joined = "\n".join(final_text)
    span = {
        "id": span_id,
        "nodo": skill or "conversacion",
        "tokens": strip(main_tok),
        "manifest": {
            "total_context_tokens": max(context_sizes) if context_sizes else 0,
            "cache_hit_tokens": max((u.get("cache_read_input_tokens", 0) for u in usage_by_msg.values()), default=0),
            "loaded_files": loaded,
        },
    }
    if model:
        span["modelo"] = model
    if latency_ms is not None:
        span["latencia_ms"] = latency_ms
    cost = costo(main_tok, model)
    if cost:
        span["costo"] = cost
    if output_joined:
        span["output_hash"] = hashlib.sha256(output_joined.encode()).hexdigest()
        if capture_sensible:  # NEVER default — exists so the factory check can prove THE KEY
            span["output"] = output_joined
    span["_start"] = min(stamps).isoformat() if stamps else None
    span["_end"] = max(stamps).isoformat() if stamps else None

    spans = [span]
    if side_usage:
        side_tok = aggregate(side_usage)
        child = {
            "id": hashlib.sha256((span_id + ":sub").encode()).hexdigest()[:16],
            "parent": span_id,
            "nodo": "subagente",
            "tokens": strip(side_tok),
            "manifest": {"total_context_tokens": max((u.get("input_tokens", 0)
                         + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                         for u in side_usage.values()), default=0)},
            "_start": span["_start"], "_end": span["_end"],
        }
        side_cost = costo(side_tok, model)
        if side_cost:
            child["costo"] = side_cost
        spans.append(child)
    return spans


# ---------------------------------------------------------------- THE KEY + OTLP egress
def _walk(obj, path="", parent=None):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield (path + "." + str(k)).lstrip("."), k, v, parent
            yield from _walk(v, path + "." + str(k), k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]", parent)


def verify_key(trazas: list[dict], sens: set[str]):
    """Returns the violating (path, field) or None. Narrow inherited exception: tokens.output INT."""
    for kpath, leaf, val, parent in _walk(trazas):
        if leaf in sens and not (parent == "tokens" and isinstance(val, int)):
            return kpath, leaf
    return None


def _attr(k, v):
    if isinstance(v, bool):
        return {"key": k, "value": {"boolValue": v}}
    if isinstance(v, int):
        return {"key": k, "value": {"intValue": str(v)}}
    if isinstance(v, float):
        return {"key": k, "value": {"doubleValue": v}}
    return {"key": k, "value": {"stringValue": str(v)}}


def _nanos(iso: str | None, fallback_ns: int) -> int:
    if not iso:
        return fallback_ns
    try:
        return int(datetime.fromisoformat(iso).timestamp() * 1e9)
    except ValueError:
        return fallback_ns


def otlp_payload(trazas: list[dict], project: str) -> dict:
    """medicion.schema traces → OTLP/HTTP JSON (GenAI semconv + medicion.* attributes).
    Same safe stratum as the sink — zero prompt/output (THE KEY already verified)."""
    import time

    now = time.time_ns()
    otlp_spans = []
    for t in trazas:
        tid = hashlib.sha256(t["id"].encode()).hexdigest()[:32]
        ids = {s["id"]: hashlib.sha256((t["id"] + s["id"]).encode()).hexdigest()[:16] for s in t["spans"]}
        for s in t["spans"]:
            tok = s.get("tokens") or {}
            man = s.get("manifest") or {}
            attrs = [
                _attr("medicion.pipeline", t["pipeline"]),
                _attr("medicion.nodo", s["nodo"]),
                _attr("gen_ai.request.model", s.get("modelo", "")),
                _attr("gen_ai.usage.input_tokens", tok.get("input", 0)),
                _attr("gen_ai.usage.output_tokens", tok.get("output", 0)),
                _attr("medicion.tokens.cache_read", tok.get("cache_read", 0)),
                _attr("medicion.tokens.cache_creation", tok.get("cache_creation", 0)),
                _attr("medicion.manifest.total_context_tokens", man.get("total_context_tokens", 0)),
                _attr("medicion.manifest.cache_hit_tokens", man.get("cache_hit_tokens", 0)),
            ]
            if s.get("costo"):
                attrs.append(_attr("medicion.costo.usd", s["costo"].get("usd", 0)))
            if s.get("output_hash"):
                attrs.append(_attr("medicion.output_hash", s["output_hash"]))
            span = {
                "traceId": tid,
                "spanId": ids[s["id"]],
                "name": s["nodo"],
                "kind": 1,
                "startTimeUnixNano": str(_nanos(s.get("_start"), now)),
                "endTimeUnixNano": str(_nanos(s.get("_end"), now)),
                "attributes": attrs,
            }
            if s.get("parent"):
                span["parentSpanId"] = ids.get(s["parent"], "")
            otlp_spans.append(span)
    return {"resourceSpans": [{
        "resource": {"attributes": [_attr("service.name", "prenter-kit-telemetry"),
                                    _attr("service.namespace", project)]},
        "scopeSpans": [{"scope": {"name": "core-harness/telemetry", "version": "1"}, "spans": otlp_spans}],
    }]}


def post_otlp(cfg: dict, payload: dict) -> bool:
    import base64

    body = json.dumps(payload).encode()
    auth = base64.b64encode(f"{cfg['otlp_public_key']}:{cfg['otlp_secret_key']}".encode()).decode()
    req = urllib.request.Request(cfg["otlp_endpoint"], data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Basic " + auth})
    with urllib.request.urlopen(req, timeout=POST_TIMEOUT_S) as resp:
        return 200 <= resp.status < 300


# ---------------------------------------------------------------- sink + offsets
def emit(transcript: Path, session_id: str, project: str, cfg: dict,
         mode: str, capture_sensible: bool, no_egress: bool) -> str:
    proj_dir = cfg["sink_dir"] / project
    proj_dir.mkdir(parents=True, exist_ok=True)
    sink = proj_dir / "trazas.jsonl"
    offsets_file = proj_dir / "offsets.json"
    offsets = {}
    if offsets_file.is_file():
        try:
            offsets = json.loads(offsets_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            offsets = {}
    state = offsets.get(session_id) or {"ingest": 0, "egress": 0, "seq": 0}

    turns, consumed = parse_turns(transcript, state["ingest"], mode)
    new_spans = []
    for turn in turns:
        turn["_session"] = session_id
        new_spans += _turn_spans(turn, state["seq"], capture_sensible)
        state["seq"] += 1
    if new_spans:
        clean = [{k: v for k, v in s.items() if not k.startswith("_") or k in ("_start", "_end")}
                 for s in new_spans]
        traza = {"id": session_id, "pipeline": "produccion", "spans": clean}
        with open(sink, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(traza, ensure_ascii=False) + "\n")
    state["ingest"] = consumed

    def persist():
        offsets[session_id] = state
        offsets_file.write_text(json.dumps(offsets), encoding="utf-8")

    # ingest persists BEFORE egress: a failed POST must never re-ingest (no dup spans);
    # the egress offset stays behind and retries naturally on the next firing.
    persist()

    report = f"{len(new_spans)} span(s) nuevos → {sink}"
    if cfg.get("otlp_endpoint") and not no_egress:
        lines = sink.read_text(encoding="utf-8").splitlines() if sink.is_file() else []
        pending = [json.loads(l) for l in lines[state["egress"]:]]
        if pending:
            violation = verify_key(pending, sensitive_fields())
            if violation:
                raise RuntimeError(
                    f"LLAVE violada en el payload de egreso: '{violation[1]}' en {violation[0]} — NO se emite nada")
            if post_otlp(cfg, otlp_payload(pending, project)):
                state["egress"] = len(lines)
                persist()
                report += f" · POST OTLP ok ({len(pending)} traza(s), solo estrato seguro)"
    return report


# ---------------------------------------------------------------- entrypoints
def main() -> int:
    ap = argparse.ArgumentParser(description="core-harness embedded telemetry emitter (KIT-03)")
    ap.add_argument("--transcript", help="transcript JSONL (default: from hook stdin)")
    ap.add_argument("--session-id", help="session id (default: from hook stdin / file stem)")
    ap.add_argument("--project", help="project name (default: cwd basename)")
    ap.add_argument("--sink", help="sink dir override")
    ap.add_argument("--event", default="stop", help="hook event (stop|subagentstop|sessionend)")
    ap.add_argument("--strict", action="store_true", help="factory checks: surface errors as exit!=0")
    ap.add_argument("--capture-sensible", action="store_true",
                    help="capture output into spans (negative-test only; NEVER wired into hooks)")
    ap.add_argument("--no-egress", action="store_true", help="sink only, skip OTLP even if configured")
    args = ap.parse_args()

    transcript, session_id, project, event = args.transcript, args.session_id, args.project, args.event
    if not transcript and not sys.stdin.isatty():
        try:
            hook = json.loads(sys.stdin.read() or "{}")
            transcript = hook.get("transcript_path")
            session_id = session_id or hook.get("session_id")
            project = project or os.path.basename(hook.get("cwd") or "")
            event = (hook.get("hook_event_name") or event).lower()
        except json.JSONDecodeError:
            pass
    if not transcript or not Path(transcript).is_file():
        return 0  # nothing to do — never a session error (RN-1)
    transcript = Path(transcript)
    session_id = session_id or transcript.stem
    project = project or os.path.basename(os.getcwd()) or "proyecto"

    cfg = load_config()
    if args.sink:
        cfg["sink_dir"] = Path(args.sink)
    mode = {"stop": "stop", "sessionend": "final"}.get(event, "hold")
    print(emit(transcript, session_id, project, cfg, mode,
               args.capture_sensible, args.no_egress), file=sys.stderr)
    return 0


if __name__ == "__main__":
    if "--strict" in sys.argv:
        sys.exit(main())
    try:
        main()
    except Exception as exc:  # fail-open: telemetry must never break a session (RN-1)
        print(f"telemetry emit skipped: {exc}", file=sys.stderr)
    sys.exit(0)
