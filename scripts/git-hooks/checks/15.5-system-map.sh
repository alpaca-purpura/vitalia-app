# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Section 15.5 — SYSTEM-MAP.yaml cross-vocabulary validation (cement 2026-05-27)
# ─────────────────────────────────────────────────────────────────────────────
# SSoT: vitalia/docs/architecture/ADR-vitalia-005-capability-model-4-dimensions.md
# Script: scripts/validate_system_map.py
#
# Gate: FULL only (wip/* branches skip — vocabulario puede estar drifting durante WIP)
# Solo corre si commit toca SYSTEM-MAP.yaml O capabilities/*.yaml O stories/checkpoint.md
#
# Override:
#   * env: SYSTEM_MAP_SKIP=1 git commit ...
# ─────────────────────────────────────────────────────────────────────────────

if [ "$GATE_LEVEL" = "full" ] && [ "${SYSTEM_MAP_SKIP:-0}" != "1" ]; then
  STAGED_SM=$(git diff --cached --name-only 2>/dev/null \
    | grep -E '(SYSTEM-MAP\.yaml|docs/product/capabilities/.*\.yaml|docs/product/stories/[^/]+/checkpoint\.md)' \
    || true)

  if [ -n "$STAGED_SM" ]; then
    # Identify affected brands
    SM_BRANDS=$(echo "$STAGED_SM" | sed -nE 's|^([a-z]+)/.*|\1|p' | sort -u)
    for SM_BRAND in $SM_BRANDS; do
      if [ -f "$SM_BRAND/docs/architecture/SYSTEM-MAP.yaml" ]; then
        printf "\033[36m[hook 15.5] Validating SYSTEM-MAP cross-vocabulary for %s...\033[0m\n" "$SM_BRAND"
        if ! "${REPO_ROOT}/.venv/bin/python" "${REPO_ROOT}/scripts/validate_system_map.py" --brand "$SM_BRAND" 2>&1; then
          printf "\033[31m"
          cat <<EOF

─────────────────────────────────────────────────────────────
SYSTEM-MAP CROSS-VOCABULARY VALIDATION FAILED ($SM_BRAND)

ADR: $SM_BRAND/docs/architecture/ADR-vitalia-005-capability-model-4-dimensions.md
Script: scripts/validate_system_map.py

Posibles causas:
  - Cap declara functional_area que NO existe en SYSTEM-MAP.yaml
  - Story declara cap_target con formato <agent>.<area> que NO existe en SYSTEM-MAP.yaml

Fixes:
  1. Si el área es nueva → agregarla a SYSTEM-MAP.yaml (status: planned)
  2. Si el name está mal → rename en cap/story para matchear SYSTEM-MAP
  3. Si es legacy/exploration → renombrar a área existente o usar otro slug

Override (emergencias documentadas):
  SYSTEM_MAP_SKIP=1 git commit ...
─────────────────────────────────────────────────────────────
EOF
          printf "\033[0m"
          exit 1
        fi
      fi
    done
  fi
fi

