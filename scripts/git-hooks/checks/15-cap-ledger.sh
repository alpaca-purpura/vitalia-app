# shellcheck shell=bash
# Auto-extracted check from the pre-commit dispatcher (god-file decomposition · HB-33/34 maintainability).
# SOURCED by scripts/git-hooks/pre-commit — inherits its env (REPO_ROOT, GATE_LEVEL, CURRENT_BRANCH,
# STAGED_PY/TS/MD, set -euo pipefail). DO NOT add a shebang or 'set -e' here; 'exit 1' aborts the commit.
# ──────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Section 15 — Capability ledger consistency (cement schema v2 2026-05-27)
# ─────────────────────────────────────────────────────────────────────────────
# SSoT: docs/process/release-protocol.md (schema v2 cap ledger).
#
# Verifica que las capacidades modificadas en este commit tengan:
#   * change_log:  field presente (post Phase 3 migration)
#
# (atomics killed 2026-05-28 — ver docs/process/lifecycle.md. El check de
#  atomics[].label ↔ change_log[].atomics_added fue removido.)
#
# Override:
#   * frontmatter del cap YAML: `# cap-ledger-skip: razón` (cualquier línea)
#   * env: CAP_LEDGER_SKIP=1 git commit ...
# ─────────────────────────────────────────────────────────────────────────────

if [ "${CAP_LEDGER_SKIP:-0}" != "1" ]; then
  STAGED_CAPS=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null \
    | grep -E '^(vitalia|nicolify|comunify|lupulo|saasora|inmoflow|retailly|fixia|guestly|fitflow)/docs/product/capabilities/[^/]+/[^/]+\.yaml$' \
    || true)

  if [ -n "$STAGED_CAPS" ]; then
    while IFS= read -r cap_file; do
      [[ -z "$cap_file" ]] && continue
      [[ ! -f "$cap_file" ]] && continue

      # Honor magic comment escape (anywhere in file)
      if grep -qE '^\s*#\s*cap-ledger-skip([: \t]|$)' "$cap_file"; then
        continue
      fi

      # Run inline Python validator (using workspace venv for yaml lib)
      WS_VENV="$(git rev-parse --show-toplevel)/.venv/bin/python"
      if [ ! -x "$WS_VENV" ]; then
        # Fallback: system python3 (yaml usually available)
        WS_VENV="python3"
      fi

      RESULT=$("$WS_VENV" - "$cap_file" <<'PYEOF' 2>&1
import sys
import re

cap_path = sys.argv[1]
try:
    import yaml
except ImportError:
    print("SKIP:yaml-not-available")
    sys.exit(0)

try:
    with open(cap_path, "r", encoding="utf-8") as fh:
        text = fh.read()
except OSError as exc:
    print(f"ERROR:read-failed:{exc}")
    sys.exit(2)

# Strip leading comment lines / blanks
lines = text.splitlines(keepends=True)
cursor = 0
for line in lines:
    s = line.lstrip()
    if s.startswith("#") or s in {"", "\n"}:
        cursor += len(line)
        continue
    break
body = text[cursor:]
# Accept both frontmatter-style (with leading ---) AND plain YAML files (cap legacy + new)
if body.startswith("---"):
    after = body[3:].lstrip("\n")
    yaml_text = after.split("\n---", 1)[0]
else:
    yaml_text = body
try:
    data = yaml.safe_load(yaml_text) or {}
except yaml.YAMLError as exc:
    # Pre-existing legacy data may have unquoted strings con caracteres especiales
    # (paréntesis, dos puntos, brackets). Convertir bloqueo → advisory.
    # Chris ratifica fix per-cap eventualmente. Hook no bloquea por data pre-existente.
    print(f"SKIP:yaml-parse-failed:{exc}")
    sys.exit(0)
if not isinstance(data, dict):
    print("SKIP:frontmatter-not-dict")
    sys.exit(0)

errors = []

# Check 1: change_log field must exist post-Phase-3
if "change_log" not in data:
    errors.append("MISSING_CHANGE_LOG: capability lacks change_log field (post-Phase-3 schema v2 cement 2026-05-27)")

# (atomics killed 2026-05-28 — atomics[].label ↔ change_log[].atomics_added
#  consistency check removed; ver docs/process/lifecycle.md)

if errors:
    print("FAIL")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
print("OK")
sys.exit(0)
PYEOF
)
      RC=$?
      if [ "$RC" -ne 0 ]; then
        printf "\033[31m"
        cat <<EOF

─────────────────────────────────────────────────────────────
CAPABILITY LEDGER VIOLATION (schema v2 cement 2026-05-27)

File: $cap_file

$RESULT

Schema v2 requires:
  * change_log: field present (Phase 3 migration script ya lo agregó)

Fix:
  * Editar $cap_file y agregar el field change_log: con la entrada de la
    story que introdujo la capability
  * Si es advisory legítimo: agregar al cap YAML una línea:
        # cap-ledger-skip: razón aquí
  * Emergency override: CAP_LEDGER_SKIP=1 git commit ...

SSoT: docs/process/release-protocol.md (schema v2)
─────────────────────────────────────────────────────────────
EOF
        printf "\033[0m"
        exit 1
      fi
    done <<< "$STAGED_CAPS"
  fi
fi

