# shellcheck shell=bash
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL,
# CURRENT_BRANCH, STAGED_*, set -euo pipefail). DO NOT add a shebang or 'set -e'; 'exit 1' aborta el commit.
# ─────────────────────────────────────────────────────────────────────────────
# Section 20 — Story-folder YAML structural validity + archive-state (HB-93 + HB-102 + HB-91)
# ─────────────────────────────────────────────────────────────────────────────
# Un checkpoint.md con frontmatter YAML inválido (HB-93) o un 04-validators.yaml /
# 06-tickets.yaml mal-formado (HB-102) llegó a `developed` sin que ningún gate lo
# cazara → el cockpit (prenter, Go-yaml) no parsea la story y NO renderiza sus
# artefactos (demo-script incluido). El gate 17 cubre SOLO keys duplicadas; este
# cubre la validez ESTRUCTURAL completa (indentación, flow-mapping, etc.).
# Además (HB-91): un checkpoint.md que se mueve a docs/archive/ DEBE estar
# `state: done` — Fase F debe flipearlo en el MISMO commit del git mv, si no el
# cockpit pinta developed/reviewing sobre algo ya merged.
#
# Override emergencia: STORY_YAML_SKIP=1 git commit ...
# SSoT: docs/process/harness-backlog.md HB-93/HB-102.
# ─────────────────────────────────────────────────────────────────────────────
if [ "${STORY_YAML_SKIP:-0}" != "1" ]; then
  STORY_YAML_FILES=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null \
    | grep -E '/(checkpoint\.md|04-validators\.yaml|06-tickets\.yaml)$' || true)
  if [ -n "$STORY_YAML_FILES" ]; then
    if [ -x "${REPO_ROOT}/.venv/bin/python" ]; then
      STORY_YAML_PY="${REPO_ROOT}/.venv/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
      STORY_YAML_PY="python3"
    else
      STORY_YAML_PY=""
      echo "WARNING: python no encontrado — skipping story-YAML validity (Section 20)." >&2
    fi
    if [ -n "$STORY_YAML_PY" ]; then
      # xargs-free: pasamos la lista como args (paths sin espacios por convención del repo).
      # shellcheck disable=SC2086
      if ! STORY_YAML_OUT=$("$STORY_YAML_PY" "${REPO_ROOT}/scripts/validate_story_yaml.py" $STORY_YAML_FILES 2>&1); then
        printf "\033[31m"
        cat <<EOF

─────────────────────────────────────────────────────────────
STORY-FOLDER INTEGRITY (HB-93 / HB-102 / HB-91)

$STORY_YAML_OUT

YAML inválido (checkpoint frontmatter / 04-validators / 06-tickets) rompe
el parse del cockpit → la story no renderiza (ni su demo-script). Un
checkpoint movido a docs/archive/ debe estar state: done (Fase F lo flipea
en el git mv). Arreglá lo de arriba antes de commitear.

Override emergencia: STORY_YAML_SKIP=1 git commit ...
SSoT: docs/process/harness-backlog.md HB-93/HB-102/HB-91
─────────────────────────────────────────────────────────────
EOF
        printf "\033[0m"
        exit 1
      fi
    fi
  fi
fi
