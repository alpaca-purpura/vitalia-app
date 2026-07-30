# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# 12. Story closure gate (origen 2026-05-18 — caso vitalia auditor-no-disparado)
# ─────────────────────────────────────────────────────────────────────────────
# SSoT: .claude/rules/story-closure-gate.md (Layer 4 enforcement)
#
# NOTE: numerada Section 12 porque main introdujo Section 11 (worktree D11
# enforcement) concurrentemente en commit 25bd3bf (mismo cement-date 2026-05-18).
# Las dos secciones son complementarias y operan en distintos planos:
#   Section 11 (main) → bloquea commits directos a 'main' branch
#   Section 12 (este) → bloquea cross-story commits dentro del mismo worktree
#
# Bloquea stage de archivos de story B si story A del mismo worktree esta en
# state ∈ {developed, reviewing} SIN defer_audit:true.
#
# Razon: caso vitalia 2026-05-18. /dev-team cerro infra-cross-cutting en
# state=developed (sin auditar/mergear) y arranco copilot-tools-impl en mismo
# worktree. Esta seccion bloquea ese patron.
#
# Toggle override: STORY_CLOSURE_GATE_SKIP=1 (solo emergencias documentadas)
#
# ★ HB-33 (2026-06-08): MODULE-AWARE. ADR-009 + WIP-cap-v2 (story-closure-gate.md)
# permiten stories PARALELAS en módulos DISTINTOS (≤1 abierta por bucket code:{module}).
# El gate ahora bloquea SOLO si la staged story comparte `module:` con una open story.
# Cross-módulo (ej. crm vs inbox) = permitido. Conservador si el módulo es desconocido.

if [ "${STORY_CLOSURE_GATE_SKIP:-0}" != "1" ]; then
  # Stories tocadas por este commit (paths {brand}/docs/product/stories/{id}/...)
  STAGED_STORIES=$(git diff --cached --name-only 2>/dev/null \
    | grep -oE "^[a-z]+/docs/product/stories/[a-z0-9_-]+/" \
    | sort -u \
    || true)

  # Listar stories en state developed|reviewing sin defer_audit + su módulo (HB-33)
  OPEN_STORIES_LIST=""
  OPEN_MODULES=""                 # módulos (espacio-separados) de las open stories
  # Brand enum from the seam (project.config.yaml · harness_config.py) — no hardcoded list
  # (charter §3 DIP · W5b). Loud-degrade to empty (a fresh/unconfigured repo has no brand
  # dirs to sweep anyway; the warn surfaces a deleted config rather than silent-passing).
  SC_BRANDS="$("${REPO_ROOT}/.venv/bin/python" "${REPO_ROOT}/scripts/harness_config.py" brands.loop_order 2>/dev/null | tr '\n' ' ')"
  [ -z "${SC_BRANDS}" ] && echo "WARN: project.config.yaml brands.loop_order unreadable — story-closure brand sweep degraded" >&2
  for B in ${SC_BRANDS}; do
    [ -d "${REPO_ROOT}/${B}/docs/product/stories" ] || continue
    for cp in "${REPO_ROOT}/${B}/docs/product/stories/"*/checkpoint.md; do
      [ -f "$cp" ] || continue
      STORY_ID=$(basename "$(dirname "$cp")")
      STATE=$(grep -E "^state:" "$cp" 2>/dev/null | head -1 | awk '{print $2}' || echo "")
      DEFER=$(grep -E "^defer_audit:" "$cp" 2>/dev/null | awk '{print $2}' || echo "")
      if [[ "$STATE" =~ ^(developed|reviewing)$ ]] && [[ "$DEFER" != "true" ]]; then
        OPEN_STORIES_LIST+="${B}/docs/product/stories/${STORY_ID}/|"
        OMOD=$(grep -E "^module:" "$cp" 2>/dev/null | head -1 | awk '{print $2}' || echo "")
        OPEN_MODULES+="${OMOD:-__unknown__} "
      fi
    done
  done

  # Si hay stories OPEN sin defer_audit + commit toca files de OTRA story →
  # BLOCK SOLO si comparten módulo (HB-33 · ADR-009 permite paralelo cross-módulo).
  if [ -n "${OPEN_STORIES_LIST}" ] && [ -n "${STAGED_STORIES}" ]; then
    # Un open story con módulo desconocido = comodín conservador (bloquea todo).
    OPEN_HAS_UNKNOWN_MODULE=0
    case " ${OPEN_MODULES} " in *" __unknown__ "*) OPEN_HAS_UNKNOWN_MODULE=1 ;; esac

    OFFENDING_STAGED=""
    for staged in ${STAGED_STORIES}; do
      # La staged story ES una open story misma → permitido (trabajás en ella).
      if [[ "${OPEN_STORIES_LIST}" == *"${staged}"* ]]; then continue; fi
      # Módulo de la staged story (desde su checkpoint).
      SCP="${REPO_ROOT}/${staged}checkpoint.md"
      SMOD="__unknown__"
      if [ -f "$SCP" ]; then
        SMOD=$(grep -E "^module:" "$SCP" 2>/dev/null | head -1 | awk '{print $2}' || echo "")
        [ -z "$SMOD" ] && SMOD="__unknown__"
      fi
      # ¿Colisiona con el módulo de alguna open story?
      if [ "$OPEN_HAS_UNKNOWN_MODULE" = "1" ] || [ "$SMOD" = "__unknown__" ]; then
        OFFENDING_STAGED+="  - ${staged} (módulo: ${SMOD} — no se pudo probar cross-módulo)"$'\n'
      else
        case " ${OPEN_MODULES} " in
          *" ${SMOD} "*) OFFENDING_STAGED+="  - ${staged} (módulo: ${SMOD} — colisiona con open story)"$'\n' ;;
        esac
      fi
    done

    if [ -n "${OFFENDING_STAGED}" ]; then
      printf "\033[31m"
      cat <<EOF
─────────────────────────────────────────────────────────────
PRE-COMMIT BLOCKED: Story closure gate (Section 12, Layer 4).
─────────────────────────────────────────────────────────────
Hay stories abiertas en state developed/reviewing sin defer_audit:true
en este worktree:

$(echo "${OPEN_STORIES_LIST}" | tr '|' '\n' | sed 's/^/  - /' | grep -v '^  - $' || true)

Pero este commit toca files de OTRAS stories que comparten módulo (o cuyo
módulo no se pudo probar distinto — HB-33):

${OFFENDING_STAGED}
ADR-009 PERMITE stories paralelas en módulos DISTINTOS; el gate solo bloquea
cuando comparten el bucket code:{module}. Si tu story es cross-módulo y aún
así aparece acá, asegurate de que su checkpoint.md tenga el campo \`module:\`.
Resolver primero la story open (auto-handoff /auditor → /pm-{brand} merge).
SSoT: .claude/rules/story-closure-gate.md

Acciones disponibles:
  1. Continuar story open hasta state=done (default forward-motion)
  2. Si tu story es de OTRO módulo: agregá \`module: <bucket>\` a su checkpoint.md
  3. Ratificar defer_audit:true en checkpoint.md con razon documentada
  4. Override emergencia: STORY_CLOSURE_GATE_SKIP=1 git commit ...
     (solo si Chris ratifico explicitamente)

NEVER use --no-verify.
─────────────────────────────────────────────────────────────
EOF
      printf "\033[0m"
      exit 1
    fi
  fi
fi

