#!/usr/bin/env python3
"""
migrate_to_release_schema.py — Phase 3 data migration (one-shot, idempotent).

Migrates Vitalia checkpoints to schema v2:
  - Creates 9 release YAMLs (F0..F8) at {brand}/docs/product/releases/F{n}.yaml
  - Adds release / cap_target / cap_change_type / parent_story frontmatter fields
    to active (28) + archive (~27) checkpoints. KEEPS legacy outcome + phase
    (deprecation gradual).
  - Creates chris-input.md per story (active + archive) from canonical template.
  - Updates brand-level checkpoint with current_release + releases_active.

Refs:
  - docs/specs/templates/release-template.yaml
  - docs/specs/templates/00-chris-input-template.md
  - docs/specs/templates/checkpoint-template.md
  - .claude/plans/ok-lo-apruebo-realiza-cheeky-harbor.md § Phase 3

Usage:
  python3 scripts/migrate_to_release_schema.py vitalia [--dry-run] [--mapping path.yaml]
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Constants — release catalog (verbatim from plan § Phase 3.1)
# ---------------------------------------------------------------------------

RELEASE_CATALOG: list[dict[str, Any]] = [
    {
        "id": "F0",
        "name": "Infra base · dev stack + auth + copilot tools + IAM",
        "description": (
            "Bloque infra inicial · dev stack multibrand + auth funcional + "
            "copilot tools + adopción luana-core-iam."
        ),
        "status": "shipped",
        "shipped_date": "2026-05-15",
        "order": 0,
    },
    {
        "id": "F1",
        "name": "Shell esqueleto · ribbon + routing + tokens + layout + empty",
        "description": (
            "Fase 1 shell-organism · 11 stories cementadas (F1-S0 stack-stability → "
            "F1-S10 empty-states). Topbar global + ribbon 6 tabs + sub-tabs + "
            "routing shell + design tokens + tenant switcher + Valeria rail/chat + "
            "layout 5050 + empty states."
        ),
        "status": "shipped",
        "shipped_date": "2026-05-26",
        "order": 1,
    },
    {
        "id": "F2",
        "name": "Migración progresiva · primer valor Valeria + Lisa",
        "description": (
            "Fase 2 inicial · primer valor end-to-end. F2-S1 valeria-agenda LIVE, "
            "F2-S7 lisa-marca LIVE. Sigue valeria-pacientes + adrián primer valor + "
            "config-onboarding-clinica + lisa-landing-public."
        ),
        "status": "in_progress",
        "shipped_date": None,
        "order": 2,
    },
    {
        "id": "F3",
        "name": "Adrián vendiendo + Payment infra crítico",
        "description": (
            "Adrián vendiendo end-to-end · embudo + propuestas + outbound. "
            "Payment adapter MVP + fiscal emission PE (TIER 2 service-blockers)."
        ),
        "status": "planning",
        "shipped_date": None,
        "order": 3,
    },
    {
        "id": "F4",
        "name": "Adrián completo + Config tenant base",
        "description": (
            "Adrián completo · resto sub-tabs + Config cuenta/conexiones/avanzado "
            "tenant base."
        ),
        "status": "planning",
        "shipped_date": None,
        "order": 4,
    },
    {
        "id": "F5",
        "name": "Lisa marca completa + onboarding clínica",
        "description": (
            "Lisa marca completa · doctores + servicios + compliance + onboarding "
            "clínica funcional."
        ),
        "status": "planning",
        "shipped_date": None,
        "order": 5,
    },
    {
        "id": "F6",
        "name": "Lisa landing pública + Lucas marketing core",
        "description": (
            "Lisa landing pública (público externo) + Lucas marketing core "
            "(lanzar + en-vuelo + recursos)."
        ),
        "status": "planning",
        "shipped_date": None,
        "order": 6,
    },
    {
        "id": "F7",
        "name": "Camila cohortes core · voz + multiplicar + reactivar",
        "description": (
            "Camila core conversacional · voz + multiplicar (cohortes promotores) + "
            "reactivar (cohortes sin actividad)."
        ),
        "status": "planning",
        "shipped_date": None,
        "order": 7,
    },
    {
        "id": "F8",
        "name": "Tail · marketing extension + finanzas + low prio",
        "description": (
            "Tail · Lucas mercado + resultados (analytics deep) + Camila reputación + "
            "pricing decision + service stories low prio."
        ),
        "status": "planning",
        "shipped_date": None,
        "order": 8,
    },
]


# ---------------------------------------------------------------------------
# Slug → release mapping (heuristics per plan § Phase 3.1)
# ---------------------------------------------------------------------------


def infer_release_id(
    story_id: str,
    outcome: str | None,
    phase: str | None,
    state: str | None,
    mapping_override: dict[str, str] | None = None,
) -> tuple[str | None, str | None]:
    """
    Return (release_id, warning).

    Order:
      1. mapping_override (user-supplied YAML)
      2. outcome=admin-iam-adopt → F0
      3. outcome=dev-environment-multibrand → F0
      4. outcome=vitalia-mvp-ui-foundation + phase=fase-1 → F1
      5. outcome=vitalia-mvp-ui-foundation + phase=fase-2 → F2
      6. slug heuristics (adrian/lisa/lucas/camila/fiscal/payment/config/shell/...)
      7. fallback null → warning
    """
    if mapping_override and story_id in mapping_override:
        return mapping_override[story_id], None

    # Explicit outcome mappings
    if outcome == "admin-iam-adopt":
        return "F0", None
    if outcome == "dev-environment-multibrand":
        return "F0", None
    if outcome == "vitalia-mvp-ui-foundation":
        if phase == "fase-1":
            return "F1", None
        if phase == "fase-2":
            return "F2", None
        # phase legacy not in {fase-1, fase-2} → fall through to slug heuristics

    # Slug-based heuristics
    slug = story_id.lower()

    # Fase prefix detection (covers archived checkpoints with duplicate `phase:` field
    # where YAML parser kept the workflow phase value instead of fase-N)
    if "fase1" in slug or "-fase-1-" in slug:
        return "F1", None
    if "fase2" in slug:
        # specific subcategories
        if "lisa-landing" in slug:
            return "F6", None
        return "F2", None

    # Pre-shell-organism legacy stories (archived done) — map to F0/F1 historical
    # All under outcome=vitalia-mvp-ui-foundation but phase is workflow/status (not fase-N).
    legacy_f0_keywords = (
        "auth-base", "copilot-tools-impl", "dev-stack", "ux-discovery",
        "shell-organism",
    )
    if any(k in slug for k in legacy_f0_keywords):
        return "F0", None
    if "slice-1" in slug:
        # Slice 1 was the pre-shell-organism phase → F0/F1 territory.
        # If still-active (not in archive — won't happen, all dropped/done) map to F1.
        return "F0", None

    # FIX from F1 (parked race-fix or similar)
    if "shell" in slug and state == "parked":
        return "F1", None

    # F8 specific
    if "pricing" in slug and "decision" in slug:
        return "F8", None

    # Service stories
    if "fiscal" in slug or "payment" in slug:
        if state == "refining" or state == "refined":
            return "F3", None
        return "F8", None

    # Adrián
    if "adrian" in slug or "adrián" in slug:
        return "F3", None

    # Lucas marketing core vs tail
    if "lucas" in slug:
        if "lanzar" in slug or "envuelo" in slug or "en-vuelo" in slug or "recursos" in slug:
            return "F6", None
        if "mercado" in slug or "resultados" in slug:
            return "F8", None
        return "F6", None

    # Lisa
    if "lisa" in slug:
        if "landing" in slug:
            return "F6", None
        # marca/doctores/servicios/compliance
        return "F5", None

    # Camila
    if "camila" in slug:
        if "voz" in slug or "multiplicar" in slug or "reactivar" in slug:
            return "F7", None
        if "reputacion" in slug or "reputación" in slug:
            return "F8", None
        return "F7", None

    # Valeria
    if "valeria" in slug:
        return "F2", None

    # Config
    if "config" in slug:
        # config-onboarding-clinica is F5, others F4
        if "onboarding" in slug:
            return "F5", None
        return "F4", None

    # Shell-related fallback
    if "shell" in slug:
        return "F1", None

    # adopt iam (active variant)
    if "adopt-luana-core-iam" in slug:
        return "F0", None

    # No match — null + warning for Chris ratify
    return None, f"slug '{story_id}' did not match any heuristic · release=null"


# ---------------------------------------------------------------------------
# cap_target + cap_change_type inference
# ---------------------------------------------------------------------------


def build_cap_index(brand_root: Path) -> dict[str, dict[str, str]]:
    """Map story_id → {cap_slug, cap_module} for every cap whose
    story_introduced points at that story."""
    caps_dir = brand_root / "docs" / "product" / "capabilities"
    index: dict[str, dict[str, str]] = {}
    if not caps_dir.exists():
        return index

    for cap_path in caps_dir.rglob("*.yaml"):
        try:
            cap_data = load_yaml_safe(cap_path)
        except Exception:
            continue
        if not isinstance(cap_data, dict):
            continue
        story_intro = cap_data.get("story_introduced")
        slug = cap_data.get("slug") or cap_path.stem
        module = cap_data.get("module") or cap_path.parent.name
        if story_intro and isinstance(story_intro, str):
            index[story_intro] = {"slug": slug, "module": module}
    return index


def infer_cap_target(
    story_id: str,
    state: str | None,
    cap_index: dict[str, dict[str, str]],
    legacy_capability: str | None,
) -> tuple[str | None, str, str | None]:
    """
    Return (cap_target, cap_change_type, warning).

    Decision:
      - story exists in cap_index (done with cap_introduced=story) → (slug, new, None)
      - slug contains v2/extension/refactor/race-fix → (legacy_capability or null, extend, warn)
      - slug contains "fix" → (legacy_capability or null, fix, warn if no target)
      - state=idea & no obvious target → (legacy_capability, new, warn)
      - otherwise → (legacy_capability, new, warn if state≠idea)
    """
    slug = story_id.lower()

    # 1. Story already produced a cap (archived done) — new
    if story_id in cap_index:
        return cap_index[story_id]["slug"], "new", None

    # 2. v2/extension/refactor/race-fix → extend
    if any(k in slug for k in ("-v2", "-extension", "-refactor", "-race-fix")):
        if legacy_capability:
            return (
                legacy_capability,
                "extend",
                f"story '{story_id}' inferred as extend of '{legacy_capability}' · Chris ratify",
            )
        return None, "extend", f"story '{story_id}' inferred as extend · cap_target=null · Chris ratify"

    # 3. -fix → fix
    if "-fix" in slug or slug.endswith("fix"):
        if legacy_capability:
            return (
                legacy_capability,
                "fix",
                f"story '{story_id}' inferred as fix of '{legacy_capability}' · Chris ratify",
            )
        return None, "fix", f"story '{story_id}' inferred as fix · cap_target=null · Chris ratify"

    # 4. idea / refining / refined — cap_target=legacy_capability if present, else null
    if legacy_capability:
        return (
            legacy_capability,
            "new",
            None if state in {"idea", "refining", "refined"} else f"story '{story_id}' state={state} cap_target='{legacy_capability}' · Chris ratify cap_change_type",
        )
    return (
        None,
        "new",
        f"story '{story_id}' state={state} no legacy capability and not in cap_index · cap_target=null · Chris ratify",
    )


# ---------------------------------------------------------------------------
# YAML helpers (preserve comments + key order via in-place frontmatter edit)
# ---------------------------------------------------------------------------


def load_yaml_safe(path: Path) -> Any:
    """Safe-load YAML — supports both pure YAML files and markdown frontmatter."""
    raw = path.read_text(encoding="utf-8")
    if raw.lstrip().startswith("---"):
        # markdown frontmatter — extract block between first two `---`
        m = re.match(r"^\s*---\s*\n(.*?)\n---\s*(\n|$)", raw, re.DOTALL)
        if m:
            return yaml.safe_load(m.group(1))
    # pure YAML
    return yaml.safe_load(raw)


def load_checkpoint_frontmatter(path: Path) -> tuple[dict[str, Any], list[str], list[str]]:
    """
    Parse a checkpoint.md or any .md with --- frontmatter.

    Returns (parsed_dict, frontmatter_lines, body_lines).
    frontmatter_lines does NOT include the surrounding --- markers.
    """
    raw = path.read_text(encoding="utf-8").splitlines(keepends=False)
    if not raw or not raw[0].strip().startswith("---"):
        return {}, [], raw

    # Find closing ---
    end_idx = None
    for i in range(1, len(raw)):
        if raw[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return {}, [], raw

    fm_lines = raw[1:end_idx]
    body_lines = raw[end_idx + 1 :]

    # Strip inline comments before yaml load (preserve in fm_lines though)
    fm_text = "\n".join(fm_lines)
    try:
        parsed = yaml.safe_load(fm_text) or {}
        if not isinstance(parsed, dict):
            parsed = {}
    except yaml.YAMLError:
        parsed = {}

    return parsed, fm_lines, body_lines


def upsert_frontmatter_keys(
    fm_lines: list[str],
    new_keys: list[tuple[str, str, str]],
) -> list[str]:
    """
    Idempotent upsert of (key, value, comment) tuples into frontmatter lines.

    - If key already present (at column 0, not nested), SKIP (idempotent).
    - If absent, append after the last existing line that matches the same "section"
      heuristic or at the end of the block (just before next --- marker).

    Args:
      fm_lines: lines between the two `---` markers (no markers included).
      new_keys: list of (key, value, comment_suffix).
                 value already pre-formatted as YAML scalar.

    Returns: new fm_lines list.
    """
    existing_keys = set()
    for line in fm_lines:
        # match top-level keys: ^[a-zA-Z_][a-zA-Z0-9_-]*:
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_-]*)\s*:", line)
        if m:
            existing_keys.add(m.group(1))

    additions: list[str] = []
    for key, value, comment in new_keys:
        if key in existing_keys:
            continue
        comment_part = f"   # {comment}" if comment else ""
        additions.append(f"{key}: {value}{comment_part}")

    if not additions:
        return fm_lines

    # Append at end of frontmatter (just before closing ---)
    # Avoid double-empty-line at end
    result = list(fm_lines)
    if result and result[-1].strip() == "":
        result.pop()
    # Insert a separator comment for clarity
    result.append("")
    result.append("# Schema v2 migration (cement 2026-05-27)")
    result.extend(additions)
    return result


def write_checkpoint(
    path: Path,
    fm_lines: list[str],
    body_lines: list[str],
    dry_run: bool,
) -> None:
    """Write back the .md file with frontmatter + body."""
    if dry_run:
        return
    out = ["---"] + fm_lines + ["---"] + body_lines
    # Ensure trailing newline
    content = "\n".join(out)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# chris-input.md generation
# ---------------------------------------------------------------------------

CHRIS_INPUT_TEMPLATE_ACTIVE = """---
story_id: {story_id}
created_at: {ts}
last_modified: {ts}
notes_count: 0
refs_count: 0
conversation_count: 1
---

# chris-input.md · {story_id}

> **Qué es este archivo:** acá Chris escribe notas + referencias + Claude responde con verdicts. Es la cocina de la story (la conversación) — separada del spec/design/arch (los outputs ratificados).
>
> **3 secciones secuenciales** (mantener el orden + emojis para que parser + cockpit funcionen):
> - 💭 Notas — Chris escribe en lenguaje natural antes/durante refinement
> - 📎 Referencias — links, imágenes, story-refs, learning-refs, doc-refs
> - 💬 Conversación — turn-by-turn cronológico Chris ↔ Claude con verdicts
>
> Doc canónico: `docs/process/chris-input-protocol.md`.

## 💭 Notas

> Chris: escribe acá tus notas en lenguaje natural. Cualquier cosa que te ayude a pensar la story.
>
> Cada entry abre con `### YYYY-MM-DD HH:MM` (timestamp).

### {date_header}
Sin notas todavía · Chris escribe aquí.

## 📎 Referencias

> Chris: pega links, sube imágenes (drag-drop o botón adjuntar), cita texto de buyer personas, referencia otras stories (`F2-S1`) o learnings (`2026-MM-DD-slug`).
>
> Tipos válidos: 🔗 link · 🖼 img · 💬 text · 📖 story-ref · 📚 learning-ref · 📄 doc.
>
> Formato: `- **(emoji) (tipo)** · (valor)` + opcional `  > (comentario)` en siguiente línea.

(sin referencias todavía)

## 💬 Conversación

> Append-only · turn-by-turn cronológico.
> Chris responde a Claude editando + agregando un entry nuevo.
> Claude appendea verdict al cierre de cada turn de su skill.
>
> Verdict labels: ✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE.

### {date_header} · 🤖 claude · `scripts/migrate_to_release_schema.py` · ✓ APLICADO
Story migrada al schema v2: `release={release}`, `cap_target={cap_target}`, `cap_change_type={cap_change_type}`. Legacy `outcome` + `phase` preservados durante deprecation gradual.

Cuando estés listo para refinar, llena 💭 Notas + 📎 Referencias arriba e invoca `/po-ux vitalia {story_id}` (o `/po` si es service story, o `/ux-agentico` si es agentic).
"""

CHRIS_INPUT_TEMPLATE_ARCHIVED = """---
story_id: {story_id}
created_at: {ts}
last_modified: {ts}
notes_count: 0
refs_count: 0
conversation_count: 1
archived: true
---

# chris-input.md · {story_id}

> **Story cementada · este file es histórico read-only post-archive R2.**
>
> Story alcanzó `state=done` antes del schema v2 chris-input. Se crea este file durante migración Phase 3 para coherencia estructural cross-stories. No appendear nuevos turns acá — usa la story sucesora si aplica.

## 💭 Notas

### {date_header}
(sin notas históricas · story cerrada antes del schema chris-input.md)

## 📎 Referencias

(sin referencias históricas)

## 💬 Conversación

### {date_header} · 🤖 claude · `scripts/migrate_to_release_schema.py` · ✓ APLICADO
Story cementada · este file es histórico read-only post-archive R2. Story migrada al schema v2: `release={release}`, `cap_target={cap_target}`, `cap_change_type={cap_change_type}`. Legacy `outcome` + `phase` preservados.
"""


def render_chris_input(
    story_id: str,
    release: str | None,
    cap_target: str | None,
    cap_change_type: str | None,
    archived: bool,
    now: datetime,
) -> str:
    ts = now.strftime("%Y-%m-%dT%H:%M:%S-05:00")
    date_header = now.strftime("%Y-%m-%d %H:%M")
    template = CHRIS_INPUT_TEMPLATE_ARCHIVED if archived else CHRIS_INPUT_TEMPLATE_ACTIVE
    return template.format(
        story_id=story_id,
        ts=ts,
        date_header=date_header,
        release=release or "null",
        cap_target=cap_target or "null",
        cap_change_type=cap_change_type or "null",
    )


# ---------------------------------------------------------------------------
# Release YAML generation
# ---------------------------------------------------------------------------


def render_release_yaml(
    release: dict[str, Any],
    brand: str,
    stories: list[str],
    now: datetime,
) -> str:
    rid = release["id"]
    ts = now.strftime("%Y-%m-%dT%H:%M:%S-05:00")
    shipped = release.get("shipped_date")
    shipped_yaml = f'"{shipped}"' if shipped else "null"

    # Stories block
    if stories:
        stories_lines = "stories:\n" + "\n".join(f"  - {s}" for s in stories)
    else:
        stories_lines = "stories: []"

    legacy_outcome = "null"
    legacy_phase = "null"
    if rid == "F1":
        legacy_outcome = '"vitalia-mvp-ui-foundation"'
        legacy_phase = '"fase-1"'
    elif rid == "F2":
        legacy_outcome = '"vitalia-mvp-ui-foundation"'
        legacy_phase = '"fase-2"'
    elif rid == "F0":
        legacy_outcome = '"admin-iam-adopt / dev-environment-multibrand"'

    body = f"""---
# Release schema (v2 cement 2026-05-27)
# Doc: docs/process/release-protocol.md
# Path canónico: {brand}/docs/product/releases/{rid}.yaml

release_id: {rid}
brand: {brand}
name: "{release['name']}"
description: "{release['description']}"
status: {release['status']}
target_date: null
shipped_date: {shipped_yaml}
order: {release['order']}
created_at: {ts}
created_by: scripts/migrate_to_release_schema.py

{stories_lines}

# Legacy outcome mapping (transition phase)
maps_legacy_outcome: {legacy_outcome}
maps_legacy_phase: {legacy_phase}
---

# {rid} · {release['name']}

> {release['description']}

## Stories incluidas

<!-- Auto-poblado durante migración Phase 3 desde checkpoints reales -->

## Notas del release

(libre · Chris escribe aquí contexto adicional · decisiones · gotchas)
"""
    return body


# ---------------------------------------------------------------------------
# Brand-level checkpoint update
# ---------------------------------------------------------------------------


def update_brand_checkpoint(
    path: Path,
    current_release: str,
    releases_active: list[str],
    dry_run: bool,
) -> bool:
    """
    Idempotently inject current_release + releases_active into brand-level checkpoint.

    Returns True if file was modified (or would be modified, in dry_run).
    """
    if not path.exists():
        return False

    parsed, fm_lines, body_lines = load_checkpoint_frontmatter(path)
    if "current_release" in parsed and "releases_active" in parsed:
        return False  # already migrated

    additions: list[str] = ["", "# Schema v2 migration (cement 2026-05-27)"]
    if "current_release" not in parsed:
        additions.append(f"current_release: {current_release}")
    if "releases_active" not in parsed:
        active_yaml = "[" + ", ".join(releases_active) + "]"
        additions.append(f"releases_active: {active_yaml}")

    if dry_run:
        return True

    # Strip trailing empty lines in fm
    while fm_lines and fm_lines[-1].strip() == "":
        fm_lines.pop()

    new_fm = fm_lines + additions
    write_checkpoint(path, new_fm, body_lines, dry_run=False)
    return True


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


@dataclass
class MigrationReport:
    brand: str
    dry_run: bool
    timestamp: str
    releases_created: list[str] = field(default_factory=list)
    releases_existing: list[str] = field(default_factory=list)
    checkpoints_migrated: list[str] = field(default_factory=list)
    checkpoints_skipped_already_migrated: list[str] = field(default_factory=list)
    chris_inputs_created: list[str] = field(default_factory=list)
    chris_inputs_skipped_already_existing: list[str] = field(default_factory=list)
    brand_checkpoint_updated: bool = False
    warnings: list[dict[str, str]] = field(default_factory=list)


def list_stories(brand_root: Path) -> tuple[list[Path], list[Path]]:
    active_dir = brand_root / "docs" / "product" / "stories"
    archive_dir = brand_root / "docs" / "archive" / "2026" / "stories"

    active: list[Path] = []
    archive: list[Path] = []
    if active_dir.exists():
        for child in sorted(active_dir.iterdir()):
            if child.is_dir():
                active.append(child)
    if archive_dir.exists():
        for child in sorted(archive_dir.iterdir()):
            if child.is_dir():
                archive.append(child)
    return active, archive


def assign_stories_to_releases(
    story_dirs: list[Path],
    cap_index: dict[str, dict[str, str]],
    mapping_override: dict[str, str] | None,
    report: MigrationReport,
) -> dict[str, list[str]]:
    """Return {release_id: [story_id, ...]} aggregated by inferred release."""
    by_release: dict[str, list[str]] = {r["id"]: [] for r in RELEASE_CATALOG}

    for story_dir in story_dirs:
        cp_path = story_dir / "checkpoint.md"
        if not cp_path.exists():
            report.warnings.append(
                {
                    "story_id": story_dir.name,
                    "issue": "checkpoint.md missing — skipped from release assignment",
                }
            )
            continue
        parsed, _, _ = load_checkpoint_frontmatter(cp_path)
        outcome = parsed.get("outcome")
        phase = parsed.get("phase")
        state = parsed.get("state")
        release_id, warn = infer_release_id(
            story_dir.name, outcome, phase, state, mapping_override
        )
        if warn:
            report.warnings.append({"story_id": story_dir.name, "issue": warn})
        if release_id:
            by_release[release_id].append(story_dir.name)
    return by_release


def migrate_story_checkpoint(
    story_dir: Path,
    archived: bool,
    cap_index: dict[str, dict[str, str]],
    mapping_override: dict[str, str] | None,
    now: datetime,
    dry_run: bool,
    report: MigrationReport,
) -> None:
    cp_path = story_dir / "checkpoint.md"
    if not cp_path.exists():
        return

    parsed, fm_lines, body_lines = load_checkpoint_frontmatter(cp_path)
    story_id = parsed.get("story_id", story_dir.name)
    legacy_outcome = parsed.get("outcome")
    legacy_phase = parsed.get("phase")
    state = parsed.get("state")
    legacy_cap = parsed.get("capability") or parsed.get("capability_extends")

    # If already migrated (has `release` + `cap_target`), skip
    already = "release" in parsed and "cap_target" in parsed
    if already:
        report.checkpoints_skipped_already_migrated.append(story_id)
    else:
        # Infer release_id
        release_id, warn_rel = infer_release_id(
            story_id, legacy_outcome, legacy_phase, state, mapping_override
        )
        if warn_rel:
            report.warnings.append({"story_id": story_id, "issue": warn_rel})

        # Infer cap_target + cap_change_type
        cap_target, cap_change_type, warn_cap = infer_cap_target(
            story_id, state, cap_index, legacy_cap if isinstance(legacy_cap, str) else None
        )
        if warn_cap:
            report.warnings.append({"story_id": story_id, "issue": warn_cap})

        # Build the v2 keys to upsert
        new_keys: list[tuple[str, str, str]] = [
            ("release", release_id if release_id else "null", "release ID · ver releases/"),
            (
                "cap_target",
                cap_target if cap_target else "null",
                "capability slug target (v2 cement 2026-05-27)",
            ),
            (
                "cap_change_type",
                cap_change_type,
                "new | fix | extend | derive",
            ),
            ("parent_story", "null", "story padre si spawned · null si independiente"),
        ]
        new_fm = upsert_frontmatter_keys(fm_lines, new_keys)
        if new_fm != fm_lines:
            if not dry_run:
                write_checkpoint(cp_path, new_fm, body_lines, dry_run=False)
            report.checkpoints_migrated.append(story_id)

    # Generate chris-input.md (idempotent — skip if exists)
    chris_input_path = story_dir / "chris-input.md"
    if chris_input_path.exists():
        report.chris_inputs_skipped_already_existing.append(story_id)
    else:
        # Determine current cap_target + release (re-read parsed or use new values)
        if already:
            release_id = parsed.get("release")
            cap_target = parsed.get("cap_target")
            cap_change_type = parsed.get("cap_change_type")
        # else: variables remain from inference above

        content = render_chris_input(
            story_id=story_id,
            release=release_id if isinstance(release_id, str) else None,
            cap_target=cap_target if isinstance(cap_target, str) else None,
            cap_change_type=cap_change_type if isinstance(cap_change_type, str) else None,
            archived=archived,
            now=now,
        )
        if not dry_run:
            chris_input_path.write_text(content, encoding="utf-8")
        report.chris_inputs_created.append(story_id)


def create_release_yamls(
    brand_root: Path,
    brand: str,
    by_release: dict[str, list[str]],
    now: datetime,
    dry_run: bool,
    report: MigrationReport,
) -> None:
    releases_dir = brand_root / "docs" / "product" / "releases"
    if not dry_run:
        releases_dir.mkdir(parents=True, exist_ok=True)

    for release in RELEASE_CATALOG:
        rid = release["id"]
        path = releases_dir / f"{rid}.yaml"
        if path.exists():
            report.releases_existing.append(rid)
            continue
        stories = by_release.get(rid, [])
        content = render_release_yaml(release, brand, stories, now)
        if not dry_run:
            path.write_text(content, encoding="utf-8")
        report.releases_created.append(rid)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate Vitalia data to release schema v2 (Phase 3)."
    )
    parser.add_argument("brand_positional", nargs="?", default=None)
    parser.add_argument(
        "--brand",
        dest="brand_flag",
        default=None,
        help="Brand slug (also accepted as first positional arg). Default: vitalia.",
    )
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument(
        "--mapping",
        type=Path,
        default=None,
        help="YAML override map {story_id: release_id} (optional)",
    )
    args = parser.parse_args()
    # Resolve brand (positional wins if both supplied)
    args.brand = args.brand_positional or args.brand_flag or "vitalia"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("migrate-release-schema")

    # Resolve workspace root
    try:
        ws_root = Path(
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], text=True
            ).strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        ws_root = Path.cwd()
    brand_root = ws_root / args.brand
    if not brand_root.exists():
        log.error("Brand root not found: %s", brand_root)
        return 1

    now = datetime.now()
    report = MigrationReport(
        brand=args.brand,
        dry_run=args.dry_run,
        timestamp=now.isoformat(),
    )

    log.info(
        "Migration start · brand=%s dry_run=%s ws=%s",
        args.brand,
        args.dry_run,
        ws_root,
    )

    # Load mapping override
    mapping_override: dict[str, str] | None = None
    if args.mapping and args.mapping.exists():
        try:
            loaded = yaml.safe_load(args.mapping.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                mapping_override = {str(k): str(v) for k, v in loaded.items()}
                log.info("Loaded mapping override: %d entries", len(mapping_override))
        except Exception as exc:
            log.warning("Failed to load mapping override: %s", exc)

    # 0. Build cap_index for cap_target inference
    cap_index = build_cap_index(brand_root)
    log.info("Built cap_index · %d caps with story_introduced", len(cap_index))

    # 1. List stories (active + archive)
    active_dirs, archive_dirs = list_stories(brand_root)
    log.info("Stories · active=%d archive=%d", len(active_dirs), len(archive_dirs))

    # 2. Assign stories to releases (need all dirs combined to seed release YAML stories[])
    all_dirs = active_dirs + archive_dirs
    by_release = assign_stories_to_releases(
        all_dirs, cap_index, mapping_override, report
    )

    # 3. Create release YAMLs
    create_release_yamls(brand_root, args.brand, by_release, now, args.dry_run, report)

    # 4. Migrate checkpoints + create chris-input.md
    for story_dir in active_dirs:
        migrate_story_checkpoint(
            story_dir, archived=False, cap_index=cap_index,
            mapping_override=mapping_override, now=now, dry_run=args.dry_run, report=report,
        )
    for story_dir in archive_dirs:
        migrate_story_checkpoint(
            story_dir, archived=True, cap_index=cap_index,
            mapping_override=mapping_override, now=now, dry_run=args.dry_run, report=report,
        )

    # 5. Update brand-level checkpoint
    brand_cp = brand_root / "docs" / "product" / "checkpoint.md"
    in_progress_releases = [r["id"] for r in RELEASE_CATALOG if r["status"] == "in_progress"]
    planning_releases = [r["id"] for r in RELEASE_CATALOG if r["status"] == "planning"]
    current_release = in_progress_releases[0] if in_progress_releases else planning_releases[0] if planning_releases else "F0"
    releases_active = in_progress_releases + planning_releases
    report.brand_checkpoint_updated = update_brand_checkpoint(
        brand_cp, current_release, releases_active, args.dry_run
    )

    # 6. Write report JSON
    report_path = ws_root / "scripts" / f"migrate-report-{now.strftime('%Y-%m-%d')}.json"
    report_data = {
        "brand": report.brand,
        "dry_run": report.dry_run,
        "timestamp": report.timestamp,
        "releases_created": report.releases_created,
        "releases_existing": report.releases_existing,
        "checkpoints_migrated": report.checkpoints_migrated,
        "checkpoints_skipped_already_migrated": report.checkpoints_skipped_already_migrated,
        "chris_inputs_created": report.chris_inputs_created,
        "chris_inputs_skipped_already_existing": report.chris_inputs_skipped_already_existing,
        "brand_checkpoint_updated": report.brand_checkpoint_updated,
        "warnings": report.warnings,
    }
    if not args.dry_run:
        report_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # 7. stdout summary
    print("=" * 72)
    print(f"Migration Phase 3 · brand={report.brand} dry_run={report.dry_run}")
    print("=" * 72)
    print(f"Releases created          : {len(report.releases_created)}  {report.releases_created}")
    print(f"Releases pre-existing     : {len(report.releases_existing)}  {report.releases_existing}")
    print(f"Checkpoints migrated      : {len(report.checkpoints_migrated)}")
    print(f"Checkpoints already v2    : {len(report.checkpoints_skipped_already_migrated)}")
    print(f"chris-input.md created    : {len(report.chris_inputs_created)}")
    print(f"chris-input.md pre-existing: {len(report.chris_inputs_skipped_already_existing)}")
    print(f"Brand checkpoint updated  : {report.brand_checkpoint_updated}")
    print(f"Warnings                  : {len(report.warnings)}")
    if report.warnings and len(report.warnings) <= 20:
        for w in report.warnings:
            print(f"  WARN · {w['story_id']} · {w['issue']}")
    elif report.warnings:
        print(f"  (showing first 5 of {len(report.warnings)})")
        for w in report.warnings[:5]:
            print(f"  WARN · {w['story_id']} · {w['issue']}")
    print("=" * 72)
    if not args.dry_run:
        print(f"Report JSON: {report_path}")
    else:
        print("DRY RUN — no filesystem mutations performed.")
    return 0


# ---------------------------------------------------------------------------
# Inline tests (run via `python3 -c "from migrate_to_release_schema import *; _run_tests()"`)
# ---------------------------------------------------------------------------


def _run_tests() -> None:
    """Minimal sanity tests for the inference helpers."""
    # infer_release_id basic cases
    assert infer_release_id("vitalia-adopt-luana-core-iam", "admin-iam-adopt", None, "done")[0] == "F0"
    assert infer_release_id("vitalia-dev-stack-functional", "dev-environment-multibrand", None, "done")[0] == "F0"
    assert infer_release_id("vitalia-fase1-ribbon-6-tabs", "vitalia-mvp-ui-foundation", "fase-1", "done")[0] == "F1"
    assert infer_release_id("vitalia-fase2-valeria-pacientes", "vitalia-mvp-ui-foundation", "fase-2", "idea")[0] == "F2"
    assert infer_release_id("vitalia-fase2-adrian-embudo", "vitalia-mvp-ui-foundation", "fase-2", "idea")[0] == "F2"
    # Slug heuristics fallback
    assert infer_release_id("vitalia-fase2-lisa-landing-public", "vitalia-mvp-ui-foundation", "fase-2", "idea")[0] == "F2"
    assert infer_release_id("vitalia-pricing-decision", "vitalia-mvp-ui-foundation", None, "idea")[0] == "F8"
    assert infer_release_id("vitalia-payment-adapter-mvp", "vitalia-mvp-ui-foundation", None, "refined")[0] == "F3"
    assert infer_release_id("vitalia-fase1-shell-layout-5050-race-fix", "vitalia-mvp-ui-foundation", "fase-1", "parked")[0] == "F1"

    # infer_cap_target
    cap_idx = {"vitalia-fase2-lisa-marca": {"slug": "lisa-marca", "module": "brand_studio"}}
    t, ct, w = infer_cap_target("vitalia-fase2-lisa-marca", "done", cap_idx, "lisa.marca")
    assert ct == "new" and t == "lisa-marca"
    t, ct, w = infer_cap_target("vitalia-fase2-valeria-pacientes", "idea", cap_idx, "valeria.pacientes")
    assert ct == "new" and t == "valeria.pacientes"
    # race-fix matches "-race-fix" → extend
    t, ct, w = infer_cap_target("vitalia-fase1-shell-layout-5050-race-fix", "parked", cap_idx, None)
    assert ct == "extend", f"expected extend got {ct}"
    # plain "-fix" suffix → fix
    t, ct, w = infer_cap_target("some-story-fix", "parked", cap_idx, "shell.layout-5050")
    assert ct == "fix", f"expected fix got {ct}"

    # upsert_frontmatter_keys idempotent
    fm = ["story_id: x", "outcome: y", "state: idea"]
    new = upsert_frontmatter_keys(fm, [("release", "F2", "test")])
    assert any("release: F2" in line for line in new)
    new2 = upsert_frontmatter_keys(new, [("release", "F2", "test")])
    # second pass should not add anything
    count = sum(1 for line in new2 if "release: F2" in line)
    assert count == 1, f"idempotency broken: count={count}"

    print("✓ Inline tests passed")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        _run_tests()
        sys.exit(0)
    sys.exit(main())
