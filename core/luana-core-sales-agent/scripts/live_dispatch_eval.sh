#!/usr/bin/env bash
# Live-dispatch eval for sales_agent brand tools (the live-trajectory gate the
# synthetic pass^k runner lacks — it scores scripted golden turns, never runs the
# graph live, so it can't catch a non-dispatching agent).
#
# K fresh-chat Telegram webhooks (unique chat_id per trial = fresh conversation,
# no debounce collision) → the agent runs the real graph → count the durable
# "sales_agent.tool_dispatched" seam log (one per execution, post per-turn dedup,
# independent of data outcome). Per-conversation rate = distinct user_id dispatched.
#
# Usage:  bash live_dispatch_eval.sh [K] [MSG] [STAGGER_s] [DRAIN_s]
# Defaults target vitalia dev (:8002 + luana-dev-vitalia container); edit URL/CONT
# + the tool-name grep for another brand. The synthetic-chat sendMessage 400 is EXPECTED.
# ponytail: no framework, just curl + docker logs grep.
#
# ⚠️ RESTART the backend before each run (`docker restart luana-dev-<brand>_backend_dev-1`):
# each trial spawns a ~50s graph background task; back-to-back runs accumulate them and
# exhaust the dev DB pool → webhooks hang (HTTP 000) → false 0/K. A fresh backend + gentle
# STAGGER (≥10s) keeps concurrency low enough to measure cleanly.
set -u
K=${1:-20}
MSG=${2:-"¿quién me atiende para blanqueamiento dental? recomendame el especialista y mandame el link de su perfil"}
STAGGER=${3:-8}      # seconds between fires (bounds concurrency ~ graph_time/STAGGER)
DRAIN=${4:-100}      # seconds to wait after last fire for graphs to finish
URL=http://127.0.0.1:8002/api/v1/connections/telegram/webhook
CONT=luana-dev-vitalia_backend_dev-1

base=$(( (RANDOM*RANDOM) % 800000000 + 100000000 ))
echo "[eval] K=$K stagger=${STAGGER}s drain=${DRAIN}s base=$base"
echo "[eval] msg: $MSG"
t0=$SECONDS
for i in $(seq 1 "$K"); do
  cid=$(( base + i ))
  upd=$(( base + 400000 + i ))
  now=$(date +%s)
  curl -s -m 25 -X POST "$URL" -H 'Content-Type: application/json' \
    -d "{\"update_id\":$upd,\"message\":{\"message_id\":$i,\"date\":$now,\"chat\":{\"id\":$cid,\"type\":\"private\"},\"from\":{\"id\":$cid,\"is_bot\":false,\"first_name\":\"Probe$i\"},\"text\":\"$MSG\"}}" >/dev/null
  printf '.'
  sleep "$STAGGER"
done
echo ""
echo "[eval] all fired, draining ${DRAIN}s..."
sleep "$DRAIN"
window=$(( SECONDS - t0 + 10 ))

logs=$(docker logs "$CONT" --since "${window}s" 2>&1 | sed 's/\x1b\[[0-9;]*m//g')
# Dispatch = the graph reached the tool-executor seam and ran a brand tool
# (vitalia.share_doctor_profile / vitalia.match_service_and_specialist), counted at
# the durable "sales_agent.tool_dispatched" log — independent of data outcome
# (a not_found result is still a dispatch). One per execution (post per-turn dedup).
fired=$(printf '%s\n' "$logs" | grep -c "telegram_webhook_dispatched")
disp_lines=$(printf '%s\n' "$logs" | grep -E "sales_agent.tool_dispatched" | grep -cE "share_doctor_profile|match_service_and_specialist")
# Honest per-conversation rate: distinct user_id that dispatched ≥1 brand tool.
convos=$(printf '%s\n' "$logs" | grep -E "sales_agent.tool_dispatched" \
  | grep -oE "user_id=[a-f0-9-]+" | sort -u | wc -l)
echo "================ RESULT ================"
echo "fired (webhook accepted): $fired / $K"
echo "total dispatch executions (incl. loops): $disp_lines"
echo "CONVERSATIONS that dispatched >=1: $convos / $K  => rate $(awk "BEGIN{printf \"%.2f\", $convos/$K}")"
echo "======================================="
