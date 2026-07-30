# telemetry/ — the kit's embedded telemetry (the ONLINE plane · KIT-03)

> **What this is:** every real run of a skill/agent in an install emits spans conforming
> to the `medicion` contract — tokens · cost · context manifest · latency · output hash —
> so the Observatory (P4) measures REAL production data, not fixtures. This is the sensor
> that ships INSIDE the kit (data-plane); the ANALYSIS is operator-only and lives outside
> the repo (Option A · I-53). Spec: `products/kit/specs/KIT-03-telemetria-embebida.md`
> (frozen 2026-07-02).

## How it works

`hooks/hooks.json` wires **Stop · SubagentStop · SessionEnd** to [`emit.py`](./emit.py).
Each firing:

1. Parses the NEW lines of the session transcript (byte-offset incremental, per session).
   A turn = one human prompt → one span; `attributionSkill` names the node (else
   `"conversacion"`); sidechain traffic becomes a child span (`"subagente"`).
   SubagentStop fires mid-turn, so the open turn is HELD BACK until Stop/SessionEnd.
   Stop also holds a trailing turn that has no assistant usage yet — in print-mode
   (`claude -p`) it can fire before the response lines are flushed; SessionEnd closes
   everything (KIT-07).
2. Appends the trace (`medicion.schema` shape — see the byte-synced copy
   [`medicion.schema.yaml`](./medicion.schema.yaml); the factory gate enforces equality
   with the L0 SSoT) to the **local sink**: `~/.prenter/telemetry/<project>/trazas.jsonl`
   — outside the repo, never committed.
3. If the machine has egress config: walks **THE KEY** (every `egreso: sensible` field,
   harvested from the schema at runtime) over the pending payload — one violation and
   NOTHING is emitted — then POSTs OTLP GenAI-semconv spans to the operator backend
   (Langfuse). A failed POST freezes the egress offset and retries on the next firing.

**Fail-open:** in hook mode the emitter always exits 0. Telemetry must never block,
break, or noticeably slow a session.

## Config (per machine — NEVER in the repo)

```yaml
# ~/.config/prenter/observatorio.yaml
telemetry:                      # optional block; falls back to backend:/top-level keys
  sink_dir: ~/.prenter/telemetry
  otlp_endpoint: http://localhost:3000/api/public/otel/v1/traces
  otlp_public_key: pk-…
  otlp_secret_key: sk-…
```

Env overrides: `PRENTER_TELEMETRY_SINK_DIR` / `_OTLP_ENDPOINT` / `_OTLP_PUBLIC_KEY` /
`_OTLP_SECRET_KEY`. **No config → local sink only, zero egress** (safe default).

## What crosses the border (Option A)

Only the SAFE STRATUM: token counts · derived cost · manifest sizes/paths · latency ·
hashes · ids. **v1 does not even capture prompt/output content** — only `output_hash`.
The `--capture-sensible` flag exists solely so the factory's negative test can prove THE
KEY bites; it is never wired into the hooks and never egresses regardless.

## Known gaps (v1, honest)

- Per-subagent fine attribution depends on what the MAIN transcript exposes
  (`isSidechain` lines); subagents with separate transcripts aggregate into the parent
  turn's child span at best.
- Turn detection v2 (KIT-07): interactive prompts carry a truthy `origin`; headless
  `claude -p` prompts carry none, so plain-string `user` lines without `origin` ALSO open
  turns — excluding meta/sidechain/tool-result lines and local-command wrappers
  (`<command-name>` · `<local-command-stdout>` · `<local-command-caveat>`). A NEW kind of
  injected plain-string line would open a spurious turn until its wrapper joins the
  exclusion list in `emit.py`.
- Native Claude Code OTel (`CLAUDE_CODE_ENABLE_TELEMETRY`) was evaluated and NOT adopted
  as the channel: api-request granularity, traces still beta, and egress would bypass
  THE KEY. Running it in parallel double-counts — don't.

## Factory gate

`tooling/scripts/check_telemetria_kit.py` (step in `gen_all`): contract sync (byte-equal
with L0) · emission over the synthetic fixture (`testdata/`) · idempotency by offsets ·
hold-back · frozen egress offset on dead backend · THE-KEY negative test.
