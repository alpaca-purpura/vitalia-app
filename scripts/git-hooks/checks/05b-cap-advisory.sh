# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
# 5b. Capability advisory — wip/* light gate (cement 2026-05-28)
# ─────────────────────────────────────────────────────────────────
# Runs ONLY in GATE_LEVEL=light (wip/* branches). Two sub-checks:
#
# Advisory (no exit 1):
#   If cap YAML files or story checkpoint.md files are staged, run
#   reconcile_capabilities.py --check --brand {brand} as advisory.
#   Output is printed but NEVER blocks the commit (|| true).
#
# HARD block (exit 1):
#   If a staged checkpoint.md declares cap_change_type ∈ {new, extend}
#   but NO cap YAML is staged in the same commit → BLOCK.
#   Rationale: Fase F.3 requires both checkpoint + cap YAML to be committed
#   together so the ledger stays coherent. Committing the checkpoint without
#   the cap YAML leaves the ledger in an inconsistent state visible to
#   reconcile_capabilities.py --validate-ledger.
#
# Override HARD block:
#   * env: CAP_ADVISORY_SKIP=1 git commit ...
#
# Note: reconcile_capabilities.py has no --advisory flag; we achieve
# advisory behavior by appending `|| true` to the invocation.
# ─────────────────────────────────────────────────────────────────

if [ "${GATE_LEVEL}" = "light" ] && [ "${CAP_ADVISORY_SKIP:-0}" != "1" ]; then

  # Detect staged capability YAML files (per-brand, not platform/legacy)
  CAP5B_STAGED=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null \
    | grep -E '^(vitalia|nicolify|comunify|lupulo|saasora|inmoflow|retailly|fixia|guestly|fitflow)/docs/product/capabilities/[^/]+/[^/]+\.yaml$' \
    || true)

  # Detect staged story checkpoint.md files (per-brand)
  CHECKPOINT5B_STAGED=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null \
    | grep -E '^(vitalia|nicolify|comunify|lupulo|saasora|inmoflow|retailly|fixia|guestly|fitflow)/docs/product/stories/[^/]+/checkpoint\.md$' \
    || true)

  if [ -n "${CAP5B_STAGED}" ] || [ -n "${CHECKPOINT5B_STAGED}" ]; then
    # Derive brand(s) from staged files (first segment of path)
    BRANDS5B=$(printf '%s\n%s\n' "${CAP5B_STAGED}" "${CHECKPOINT5B_STAGED}" \
      | grep -v '^$' \
      | cut -d/ -f1 \
      | sort -u || true)

    # ── Advisory: run reconcile --check per brand (non-blocking) ──
    RECONCILER5B="${REPO_ROOT}/scripts/reconcile_capabilities.py"
    if [ -x "${REPO_ROOT}/.venv/bin/python" ]; then
      VENV5B="${REPO_ROOT}/.venv/bin/python"
    elif [ -x "${REPO_ROOT}/backend/.venv/bin/python" ]; then
      VENV5B="${REPO_ROOT}/backend/.venv/bin/python"
    else
      VENV5B=""
    fi

    if [ -n "${VENV5B}" ] && [ -f "${RECONCILER5B}" ] && [ -n "${BRANDS5B}" ]; then
      echo ""
      echo "[5b] Capability advisory (wip/* light gate — non-blocking)"
      while IFS= read -r B5B; do
        [ -z "${B5B}" ] && continue
        ADVISORY_OUT=$("${VENV5B}" "${RECONCILER5B}" --check --brand "${B5B}" 2>&1 || true)
        if [ -n "${ADVISORY_OUT}" ]; then
          printf "\033[33m"
          echo "  [5b advisory · ${B5B}]"
          echo "${ADVISORY_OUT}" | head -30 | sed 's/^/    /'
          printf "\033[0m"
        fi
      done <<< "${BRANDS5B}"
      echo "[5b] advisory done (warnings above do not block commit)"
    fi

    # ── HARD check: cap_change_type ∈ {new, extend} without cap YAML staged ──
    if [ -n "${CHECKPOINT5B_STAGED}" ]; then
      while IFS= read -r CP5B; do
        [ -z "${CP5B}" ] && continue
        [ ! -f "${CP5B}" ] && continue

        # Read cap_change_type from staged content (git show) to check the
        # version being committed, not just the working-tree version.
        STAGED_CP_CONTENT=$(git show ":${CP5B}" 2>/dev/null || true)
        [ -z "${STAGED_CP_CONTENT}" ] && continue

        CCT=$(echo "${STAGED_CP_CONTENT}" \
          | grep -E '^cap_change_type:' \
          | head -1 \
          | sed -E 's/^cap_change_type:[[:space:]]*//' \
          | sed -E 's/[[:space:]]*#.*$//' \
          | tr -d '"'"'" \
          | xargs 2>/dev/null || true)

        if [ "${CCT}" = "new" ] || [ "${CCT}" = "extend" ]; then
          if [ -z "${CAP5B_STAGED}" ]; then
            # ★ HB-34 (2026-06-08): aceptar el cap YAML si YA está en HEAD —
            # no forzar un touch/re-stage artificial de un cap sin cambios cuando
            # el commit es checkpoint-only. Resolvemos cap_target → path (resolve_cap.py)
            # y si existe en HEAD, el ledger ya es coherente → no bloqueamos.
            CAP_TARGET5B=$(echo "${STAGED_CP_CONTENT}" \
              | grep -E '^cap_target:' | head -1 \
              | sed -E 's/^cap_target:[[:space:]]*//; s/[[:space:]]*#.*$//' \
              | tr -d '"'"'" | xargs 2>/dev/null || true)
            BRAND5B=$(echo "${CP5B}" | cut -d/ -f1)
            PY5B="${VENV5B:-python3}"
            if [ -n "${CAP_TARGET5B}" ] && [ "${CAP_TARGET5B}" != "null" ] \
               && [ -f "${REPO_ROOT}/scripts/resolve_cap.py" ]; then
              CAP_PATH5B=$("${PY5B}" "${REPO_ROOT}/scripts/resolve_cap.py" "${BRAND5B}" "${CAP_TARGET5B}" 2>/dev/null | head -1 || true)
              if [ -n "${CAP_PATH5B}" ] && git cat-file -e "HEAD:${CAP_PATH5B}" 2>/dev/null; then
                continue   # cap YAML ya commiteado en HEAD — ledger coherente (HB-34)
              fi
            fi
            printf "\033[31m"
            cat <<EOF

─────────────────────────────────────────────────────────────
PRE-COMMIT BLOCKED: cap_change_type=${CCT} declared without cap YAML staged
(Section 5b HARD check — cement 2026-05-28)

Checkpoint: ${CP5B}
cap_change_type: ${CCT}

Cuando cap_change_type ∈ {new, extend}, el cap YAML target DEBE estar
staged en el mismo commit O ya existir en HEAD (HB-34 — Fase F.3 enforce,
capability-protocol.md § 5). Acá NO está ni staged ni en HEAD → ledger inconsistente.

Sin cap YAML (ni staged ni en HEAD), reconcile_capabilities.py --validate-ledger
reportará inconsistencia al siguiente full-gate commit (main/release/*).

Acciones:
  1. Stage el cap YAML correspondiente junto con este checkpoint:
       git add {brand}/docs/product/capabilities/{module}/{cap-slug}.yaml
     (si el cap ya está commiteado en HEAD sin cambios, este gate NO dispara — HB-34)
  2. Si la story aún está en progreso y el cap YAML no está listo:
       Quitar cap_change_type: ${CCT} del checkpoint por ahora, o usar
       cap_change_type: fix hasta que el YAML esté listo.
  3. Override emergencia (solo si Chris ratificó):
       CAP_ADVISORY_SKIP=1 git commit ...

SSoT: docs/process/cap-deterministic-enforcement.md + docs/process/capability-protocol.md § 5
─────────────────────────────────────────────────────────────
EOF
            printf "\033[0m"
            exit 1
          fi
        fi
      done <<< "${CHECKPOINT5B_STAGED}"
    fi
  fi

fi  # end GATE_LEVEL=light guard (section 5b)

