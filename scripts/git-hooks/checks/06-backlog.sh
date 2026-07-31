# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
# 6. R33 BACKLOG.yaml + BACKLOG.md freshness (origen 2026-05-05) — MULTIBRAND
# (refactor 2026-05-15 post multibrand reorg)
# Gate: FULL only (wip/* branches skip — backlog regen during WIP commits
# adds noise; regen happens at squash-merge to main)
# ─────────────────────────────────────────────────────────────────
# BACKLOG.{yaml,md} auto-generated por scripts/generate_backlog.py desde
# sources (ideas-pool.yaml, outcomes/, stories/, capabilities/, modules/).
#
# Trigger: any staged change touching backlog source paths:
#   - docs/product/(ideas-pool.yaml|outcomes/|stories/|capabilities/|modules/)
#                                                        (platform/legacy)
#   - {brand}/docs/product/(ideas-pool.yaml|outcomes/|stories/|capabilities/|modules/)
#                                                        (per-brand)
#   - docs/projects/active/+/checkpoint.md               (legacy projects)
#
# Action por trigger:
#   - Path raíz docs/product/... → invocar generator legacy (regen platform
#     BACKLOG + auto-stage).
#   - Path {brand}/docs/product/... → generator con --brand.
#
# Note: pm-nico/pis/active/ removed Wave 2 (2026-05-06) — generator returns []
# defensively. Path NOT included in trigger regex anymore.

if [ "${GATE_LEVEL}" = "full" ]; then

BACKLOG_SOURCES_TOUCHED=$(git diff --cached --name-only --diff-filter=ACMRD 2>/dev/null \
  | grep -E '^(docs/(product/(ideas-pool\.yaml|outcomes/|stories/|capabilities/|modules/)|projects/active/.+/checkpoint\.md)|[a-z][a-z0-9_-]*/docs/product/(ideas-pool\.yaml|outcomes/|stories/|capabilities/|modules/))' \
  || true)

if [ -n "${BACKLOG_SOURCES_TOUCHED}" ]; then
  GENERATOR="${REPO_ROOT}/scripts/generate_backlog.py"
  # Prefer root venv (uv workspace), fallback legacy backend venv
  if [ -x "${REPO_ROOT}/.venv/bin/python" ]; then
    VENV_PY="${REPO_ROOT}/.venv/bin/python"
  elif [ -x "${REPO_ROOT}/backend/.venv/bin/python" ]; then
    VENV_PY="${REPO_ROOT}/backend/.venv/bin/python"
  else
    VENV_PY=""
  fi

  # Detectar brands tocadas vs paths raíz.
  BRAND_BACKLOG_TOUCHED=$(echo "${BACKLOG_SOURCES_TOUCHED}" \
    | grep -E '^[a-z][a-z0-9_-]*/docs/product/' \
    | cut -d/ -f1 | sort -u || true)
  ROOT_BACKLOG_TOUCHED=$(echo "${BACKLOG_SOURCES_TOUCHED}" \
    | grep -E '^docs/' || true)

  if [ -n "${VENV_PY}" ] && [ -f "${GENERATOR}" ]; then
    # Caso 1: paths raíz docs/product/ → invocar generator legacy.
    # NOTE 2026-05-20: BACKLOG.* es gitignored (.gitignore § "Auto-generated docs").
    # Regeneramos working-tree local para mantener fresh, NO auto-stage.
    if [ -n "${ROOT_BACKLOG_TOUCHED}" ]; then
      if ! "${VENV_PY}" "${GENERATOR}" --check >/tmp/backlog-check.txt 2>&1; then
        # Drift detected — regenerate local (gitignored, no stage)
        "${VENV_PY}" "${GENERATOR}" >/tmp/backlog-regen.txt 2>&1 || true
        printf "\033[33m"
        cat <<EOF
─────────────────────────────────────────────────────────────
R33 BACKLOG auto-regenerated (platform/legacy) — gitignored
─────────────────────────────────────────────────────────────
Sources changed → docs/product/BACKLOG.{yaml,md} regenerated localmente
(gitignored desde 2026-05-20). NO se incluye en el commit.

Cuando necesites la vista actualizada: cat docs/product/BACKLOG.md

Generator output:
$(tail -10 /tmp/backlog-regen.txt)
─────────────────────────────────────────────────────────────
EOF
        printf "\033[0m"
      fi
    fi

    # Caso 2: paths per-brand → invocar generator con --brand per cada brand.
    # Same gitignored policy aplica per-brand.
    if [ -n "${BRAND_BACKLOG_TOUCHED}" ]; then
      while IFS= read -r BRAND; do
        [ -z "${BRAND}" ] && continue
        if ! "${VENV_PY}" "${GENERATOR}" --check --brand "${BRAND}" >/tmp/backlog-check-${BRAND}.txt 2>&1; then
          # Drift detected — regenerate local (gitignored, no stage)
          "${VENV_PY}" "${GENERATOR}" --brand "${BRAND}" >/tmp/backlog-regen-${BRAND}.txt 2>&1 || true
          printf "\033[33m"
          cat <<EOF
─────────────────────────────────────────────────────────────
R33 BACKLOG auto-regenerated (brand: ${BRAND}) — gitignored
─────────────────────────────────────────────────────────────
Sources changed → ${BRAND}/docs/product/BACKLOG.{yaml,md,TLDR.md}
regenerados localmente (gitignored desde 2026-05-20). NO incluidos en commit.

Vista actualizada: cat ${BRAND}/docs/product/BACKLOG.md

Generator output:
$(tail -10 /tmp/backlog-regen-${BRAND}.txt)
─────────────────────────────────────────────────────────────
EOF
          printf "\033[0m"
        fi
      done <<< "${BRAND_BACKLOG_TOUCHED}"
    fi
  else
    printf "\033[33m"
    echo "WARNING: skipping R33 backlog generator — venv or script missing."
    printf "\033[0m"
  fi
fi

fi  # end GATE_LEVEL=full guard (section 6)

