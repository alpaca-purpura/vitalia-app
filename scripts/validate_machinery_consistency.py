#!/usr/bin/env python3
# voseo-allowed: doc interno de maquinaria (no user-facing)
"""validate_machinery_consistency.py — anti-drift lock-in para la maquinaria agéntica.

Origen: auditoría 2026-05-28 (docs/process/audits/2026-05-28-agentic-machinery-audit.md).
El bug-class #1 fue DRIFT: la doctrina vive en rules/skills pero los templates que los
agentes copian (o los greps que ejecutan) quedaron atrás → artefactos no-conformes silenciosos.

Este script codifica los invariantes concretos que driftearon, para que NO vuelvan a pasar
inadvertidos. Cada CHECK es named + falla con mensaje accionable. Exit 1 si algún check falla.

Uso:
    python3 scripts/validate_machinery_consistency.py
    (o vía pre-commit Section / make machinery-check)

NO pretende ser un validador semántico general — es un guard de regresión para las clases
de drift reales encontradas. Agregá un CHECK cuando cementes un nuevo invariante doctrina↔template.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

WS = Path(
    subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
)

# Rules auto-load + templates que NO deben reintroducir el concepto muerto `atomics`
# (scenario es la unidad atómica desde lifecycle v4 2026-05-28). Se permiten líneas que
# mencionan la muerte del concepto ("MUERTO", "killed", "atomics↔headers", "Atomic write" DB).
ATOMICS_DEAD_FILES = [
    ".claude/rules/story-closure-gate.md",
    ".claude/rules/sistema-docs-schema.md",
    ".claude/rules/anti-duplication-refining.md",
]
ATOMICS_ALLOWED_CTX = re.compile(
    r"MUERT|killed|muert|atomics↔headers|Atomic write|atomics/outcome|"
    r"reemplaza|se reemplaza|v4 alignment|dead|deprecat",
    re.IGNORECASE,
)
ATOMICS_TOKEN = re.compile(r"atomics?_added|atomics?_modified|`atomics\[\]`|# atomics:|atomics iniciales|atomic nuevo")

# Paths pre-multibrand (reorg 2026-05-15) que NO deben aparecer como greps ejecutables en skills.
PREMULTIBRAND_PATHS = re.compile(r"(?<![\w/])backend/src/(shared|core)/")
PREMULTIBRAND_SCAN_FILES = [
    ".claude/skills/architect/references/be.md",
    ".claude/skills/architect/references/agentic.md",
]

# Rules nuevas que deben existir + estar registradas en CLAUDE.md tabla Critical Rules.
REQUIRED_RULES = [
    "anti-orphan-integration.md",
    "frontend-visual-fidelity.md",
    "test-design-doctrine.md",
]

# Conceptos obligatorios que TODO spec-template (raíz + overrides por marca) debe llevar.
# El template raíz docs/specs/templates/01-spec-template.md es el SSoT de la estructura del
# 01-spec; cuando se cementa un concepto ahí, los overrides por marca deben sincronizarse o
# generan drift silencioso (HB-29 2026-06-04: shell-template sin § Mapa funcional/§ Matriz).
# Concept-based (substring, NO header-exact) porque los overrides re-estructuran las secciones.
# Agregá un concepto cuando cementes uno nuevo en el raíz (y propagalo a los overrides).
MANDATORY_SPEC_CONCEPTS = [
    "Mapa funcional",  # capa humana del refinamiento (cement 2026-05-31)
    "Matriz de cobertura",  # puente humano↔verificación (cement 2026-05-31)
    "FIRMA 1",  # RONDA 1 input-spec gate (cement 2026-06-03)
    "FIRMA 2",  # RONDA 2 ejecutable gate (cement 2026-06-03)
]

# HB-43 (cap-as-locator): el resolver `resolve_cap.py` cablea la lectura de las caps
# (dev_preview/code_ref) en el pipeline. El bug original fue que el cable estaba ROTO
# (builder keyeaba 06-tickets vacío) → locator dormido. Este CHECK evita que vuelva a
# desconectarse silenciosamente: cada superficie del pipeline DEBE referenciar el resolver.
CAP_LOCATOR_WIRED_FILES = [
    ".claude/agents/builder-backend.md",
    ".claude/agents/builder-frontend.md",
    ".claude/agents/context-builder.md",
    ".claude/agents/architect-orchestrator.md",
    ".claude/skills/architect/SKILL.md",
]

failures: list[str] = []
warnings: list[str] = []
checks_run = 0


def check(name: str, ok: bool, detail: str) -> None:
    global checks_run
    checks_run += 1
    if ok:
        print(f"  ✓ {name}")
    else:
        print(f"  ✗ {name}\n      {detail}")
        failures.append(f"{name}: {detail}")


def warn(name: str, ok: bool, detail: str) -> None:
    """ADVISORY check: reporta pero NO bloquea (no afecta exit code). Para gates de
    rot/ratchet que NO deben friccionar commits legítimos (decisión Chris HB · 2026-06-08)."""
    global checks_run
    checks_run += 1
    if ok:
        print(f"  ✓ {name}")
    else:
        print(f"  ⚠ {name}\n      {detail}")
        warnings.append(f"{name}: {detail}")


# ── CHECK 1 — atomics muerto en rules auto-load ──────────────────────────────
def check_atomics_dead() -> None:
    bad: list[str] = []
    for rel in ATOMICS_DEAD_FILES:
        p = WS / rel
        if not p.exists():
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if ATOMICS_TOKEN.search(line) and not ATOMICS_ALLOWED_CTX.search(line):
                bad.append(f"{rel}:{i}: {line.strip()[:80]}")
    check(
        "CHECK 1 · atomics muerto (rules auto-load usan scenarios, no atomics)",
        not bad,
        "líneas con atomics sin contexto de muerte:\n      " + "\n      ".join(bad),
    )


# ── CHECK 2 — assignment block en 06-tickets-template ────────────────────────
def check_assignment_block() -> None:
    p = WS / "docs/specs/templates/06-tickets-template.yaml"
    txt = p.read_text(encoding="utf-8") if p.exists() else ""
    # ≥3 bloques assignment reales (T1/T2/T3), con primary_agent
    n_primary = len(re.findall(r"^\s{4}primary_agent:\s*builder-", txt, re.MULTILINE))
    check(
        "CHECK 2 · 06-tickets-template tiene assignment block (primary_agent en T1/T2/T3)",
        n_primary >= 3,
        f"esperaba ≥3 'primary_agent: builder-*' indentados, encontró {n_primary} (rule architect-autonomous-mode.md Step 7.5)",
    )


# ── CHECK 3 — greps pre-multibrand en architect skills ───────────────────────
def check_premultibrand_paths() -> None:
    bad: list[str] = []
    for rel in PREMULTIBRAND_SCAN_FILES:
        p = WS / rel
        if not p.exists():
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if PREMULTIBRAND_PATHS.search(line):
                bad.append(f"{rel}:{i}: {line.strip()[:80]}")
    check(
        "CHECK 3 · architect skills sin paths pre-multibrand (backend/src/{shared,core}/)",
        not bad,
        "NO-NEW-LAYER no-op risk:\n      " + "\n      ".join(bad),
    )


# ── CHECK 4 — dispatch-plan-template existe ──────────────────────────────────
def check_dispatch_plan_template() -> None:
    p = WS / "docs/specs/templates/dispatch-plan-template.md"
    check(
        "CHECK 4 · dispatch-plan-template.md existe (5º artefacto ready package)",
        p.exists(),
        "falta docs/specs/templates/dispatch-plan-template.md",
    )


# ── CHECK 5 — rules nuevas existen + registradas en CLAUDE.md ────────────────
def check_rules_registered() -> None:
    claude_md = (WS / "CLAUDE.md").read_text(encoding="utf-8")
    for rule in REQUIRED_RULES:
        p = WS / ".claude/rules" / rule
        check(f"CHECK 5 · rule existe: {rule}", p.exists(), f"falta .claude/rules/{rule}")
        check(
            f"CHECK 5 · rule registrada en CLAUDE.md: {rule}",
            rule in claude_md,
            f"{rule} no aparece en CLAUDE.md (tabla Critical Rules)",
        )


# ── CHECK 6 — refs .claude/rules/*.md en la MAQUINARIA resuelven ─────────────
# Scope: pipeline architect→dev-team→auditor + agentes (builders/auditores/etc).
# NO escanea skills PM brand-domain (referencian rules brand planeadas, p.ej. hipaa-lite.md —
# eso es deuda PM separada, no de la maquinaria; ver plan de hardening).
MACHINERY_SKILL_DIRS = [
    ".claude/skills/architect",  # incluye references/{be,fe,agentic}.md (rehomed W9-tail 2026-06-09)
    ".claude/skills/dev-team",
    ".claude/skills/auditor",
]


def check_rule_refs_resolve() -> None:
    ref_re = re.compile(r"\.claude/rules/([a-z0-9-]+\.md)")
    missing: set[str] = set()
    scan_paths = [WS / ".claude/agents"] + [WS / d for d in MACHINERY_SKILL_DIRS]
    for d in scan_paths:
        if not d.exists():
            continue
        for f in d.rglob("*.md"):
            for m in ref_re.finditer(f.read_text(encoding="utf-8", errors="ignore")):
                rule = m.group(1)
                if not (WS / ".claude/rules" / rule).exists():
                    missing.add(f"{rule} (citada en {f.relative_to(WS)})")
    check(
        "CHECK 6 · refs .claude/rules/*.md en la maquinaria resuelven en filesystem",
        not missing,
        "referencias a rules inexistentes:\n      " + "\n      ".join(sorted(missing)),
    )


# ── CHECK 7 — sub-auditores tienen tool Edit (Carril A v4.2) ─────────────────
def check_auditors_have_edit() -> None:
    bad: list[str] = []
    for name in ("auditor-backend", "auditor-frontend", "auditor-agentic"):
        p = WS / ".claude/agents" / f"{name}.md"
        if not p.exists():
            bad.append(f"{name}.md ausente")
            continue
        # Parsear el frontmatter completo (entre los dos primeros '---'), no un truncado fijo:
        # la línea `description:` puede ser muy larga y empujar `tools:` más allá de N chars.
        text = p.read_text(encoding="utf-8")
        fm_match = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
        frontmatter = fm_match.group(1) if fm_match else text[:3000]
        m = re.search(r"^tools:\s*(.+)$", frontmatter, re.MULTILINE)
        if not m or "Edit" not in m.group(1):
            bad.append(f"{name}.md sin 'Edit' en tools (Carril A v4.2)")
    check(
        "CHECK 7 · sub-auditores tienen tool Edit (self-fix Carril A v4.2)",
        not bad,
        "\n      ".join(bad),
    )


# ── pre-commit hook = dispatcher + sourced checks/ (god-file decomposition 2026-06-08)
def _precommit_hook_text() -> str:
    """Texto del HOOK SYSTEM completo: el dispatcher pre-commit + cada checks/NN-*.sh
    que sourcea. Tras la decomposición (HB-33/34), el cableado de cada gate vive en
    su check file, no en el monolito. Cualquier assertion de 'el pre-commit wirea X'
    debe mirar el sistema entero, no solo el dispatcher."""
    parts = []
    pc = WS / "scripts/git-hooks/pre-commit"
    if pc.exists():
        parts.append(pc.read_text(encoding="utf-8"))
    checks_dir = WS / "scripts/git-hooks/checks"
    if checks_dir.is_dir():
        for f in sorted(checks_dir.glob("*.sh")):
            parts.append(f.read_text(encoding="utf-8"))
    return "\n".join(parts)


# ── CHECK 8 — este validador está cableado en el pre-commit hook ─────────────
def check_self_wired_in_precommit() -> None:
    # Busca en el hook system (dispatcher + checks/) — el invoke vive en checks/18-machinery.sh
    wired = "validate_machinery_consistency" in _precommit_hook_text()
    check(
        "CHECK 8 · machinery-check cableado en el pre-commit hook (dispatcher + checks/)",
        wired,
        "el pre-commit no invoca validate_machinery_consistency.py (enforcement no activa). "
        "Nota: en worktrees el hook activo resuelve al checkout de main — activa al mergear.",
    )


# ── CHECK 9 — spec-template overrides sin drift vs raíz (HB-29/30) ───────────
def check_spec_template_drift() -> None:
    root = WS / "docs/specs/templates/01-spec-template.md"
    if not root.exists():
        check(
            "CHECK 9 · spec-template raíz existe",
            False,
            "falta docs/specs/templates/01-spec-template.md (SSoT estructura 01-spec)",
        )
        return
    # overrides por marca: {brand}/docs/specs/templates/01-spec-*-template.md
    overrides = sorted(WS.glob("*/docs/specs/templates/01-spec-*-template.md"))
    for tpl in [root, *overrides]:
        text = tpl.read_text(encoding="utf-8", errors="ignore")
        missing = [c for c in MANDATORY_SPEC_CONCEPTS if c not in text]
        rel = tpl.relative_to(WS)
        check(
            f"CHECK 9 · spec-template sin drift: {rel}",
            not missing,
            f"falta(n) concepto(s) cementado(s) {missing} — sincronizá con el raíz "
            "(HB-30: drift override↔raíz). Si cementaste un concepto nuevo en el raíz, "
            "propagalo a los overrides + agregalo a MANDATORY_SPEC_CONCEPTS.",
        )


# ── CHECK 10 — cap-as-locator cableado (HB-43) ───────────────────────────────
def check_cap_locator_wired() -> None:
    resolver = WS / "scripts/resolve_cap.py"
    check(
        "CHECK 10 · resolve_cap.py existe (cap-as-locator · HB-43)",
        resolver.is_file(),
        "falta scripts/resolve_cap.py — el resolver determinístico cap_target→YAML.",
    )
    if not resolver.is_file():
        return
    for rel in CAP_LOCATOR_WIRED_FILES:
        p = WS / rel
        if not p.exists():
            check(f"CHECK 10 · superficie existe: {rel}", False, f"falta {rel}")
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        check(
            f"CHECK 10 · cap-locator cableado: {rel}",
            "resolve_cap.py" in text,
            f"{rel} NO referencia resolve_cap.py — el cable cap-as-locator se desconectó "
            "(HB-43: el locator vuelve a quedar dormido). Re-cableá la lectura de la cap.",
        )


# ── CHECK 11 — cap-format enforcement determinístico G1-G6 cableado (HB-51) ──
# Anti-rot CON DIENTES: si alguien borra un gate, su negative test, o un script de
# las 8 capas, el CHECK falla. El enforcement determinístico NO debe poder
# desconectarse en silencio (es la lección recurrente advisory≠enforcement).
def check_cap_format_enforcement_wired() -> None:
    bidir = WS / "scripts/validate_code_cap_bidirectional.py"
    bidir_src = bidir.read_text(encoding="utf-8") if bidir.exists() else ""
    test_bidir = WS / "scripts/tests/test_validate_code_cap_bidirectional.py"
    test_src = test_bidir.read_text(encoding="utf-8") if test_bidir.exists() else ""

    # 11a · gate registry DERIVADO del validador (OCP · W6 Decisión-3a 2026-06-09) — NO un literal
    # congelado: deriva los gates de `def gate_gN_*` y los dispatchados de `run_cap_gates`, así un
    # G10 futuro queda AUTO-cubierto (agregar gate + dispatch + negative test = cubierto, sin tocar
    # este CHECK). El PISO atrapa el borrado por debajo de G1-G9 (HB-51 G1-G7 + F2 cap-levels G8/G9).
    EXPECTED_MIN_CAP_GATES = 9  # G1-G9. Bajar SOLO al remover un gate a propósito.
    defined_gates = sorted(set(re.findall(r"def gate_(g\d+)_", bidir_src)), key=lambda g: int(g[1:]))
    dispatch_body = bidir_src.split("def run_cap_gates", 1)[-1] if "def run_cap_gates" in bidir_src else ""
    dispatched_gates = {m.upper() for m in re.findall(r'"(G\d+)":\s*gate_', dispatch_body)}
    check(
        "CHECK 11 · registry de gates ≥ piso (deriva G1-G9 · OCP auto-cubre G10+)",
        len(defined_gates) >= EXPECTED_MIN_CAP_GATES,
        f"el registry derivó {[g.upper() for g in defined_gates]} (<{EXPECTED_MIN_CAP_GATES}) — "
        "un gate determinístico se borró (HB-51 Capa 4).",
    )
    check(
        "CHECK 11 · dispatcher run_cap_gates presente + --cap-gates-hard",
        "def run_cap_gates" in bidir_src and "--cap-gates-hard" in bidir_src,
        "falta run_cap_gates / flag --cap-gates-hard.",
    )

    # 11b · cada gate DEFINIDO está dispatchado + tiene su negative test EN ROJO (derivado del
    # registry → un G10 nuevo sin dispatch o sin test_g10_red falla acá AUTOMÁTICAMENTE).
    for gid in defined_gates:
        gid_u = gid.upper()
        has_test = f"def test_{gid}_red" in test_src
        check(
            f"CHECK 11 · gate {gid_u} dispatchado + negative test (con dientes)",
            gid_u in dispatched_gates and has_test,
            f"gate {gid_u}: dispatch={gid_u in dispatched_gates} test_{gid}_red={has_test} — "
            "un gate sin dispatch o sin negative test es decorativo (handoff §0.3).",
        )
    check(
        "CHECK 11 · test de reproducción del incidente (borrar cap inbox → G1+G2 RED)",
        "test_repro_delete_inbox_cap_trips_g1_and_g2" in test_src,
        "falta el test de regresión del incidente origen.",
    )

    # 11c · resolver two-way + scripts de las capas 2/3/8 existen
    rc = (WS / "scripts/resolve_cap.py").read_text(encoding="utf-8") if (WS / "scripts/resolve_cap.py").exists() else ""
    check(
        "CHECK 11 · resolver two-way (resolve_cap_ids + canonical_cap_id)",
        "def resolve_cap_ids" in rc and "def canonical_cap_id" in rc,
        "resolve_cap.py perdió la resolución two-way (HB-51 Capa 1).",
    )
    for script, layer in (
        ("scripts/new_cap.py", "Capa 2 generator"),
        ("scripts/validate_caps_schema.py", "Capa 3 schema"),
        ("scripts/cap_doctor.py", "Capa 8 health report"),
    ):
        check(
            f"CHECK 11 · {script} existe ({layer})",
            (WS / script).is_file(),
            f"falta {script} ({layer}).",
        )

    # 11d · el generator es consumido por el índice (Capa 5) + gates HARD cableados en hooks
    idx = WS / "scripts/generate_code_to_cap_index.py"
    idx_src = idx.read_text(encoding="utf-8") if idx.exists() else ""
    check(
        "CHECK 11 · index consume el resolver (Capa 5 · resolved_cap_to_files)",
        "resolve_cap" in idx_src and "resolved_cap_to_files" in idx_src,
        "generate_code_to_cap_index.py NO unifica vía resolver (las 2 convenciones divergen).",
    )
    pp = WS / "scripts/git-hooks/pre-push"
    # pre-commit: el 5e cap-gates-hard vive en checks/05e-cap-gates.sh (decomposición HB-33/34)
    check(
        "CHECK 11 · gates HARD cableados en pre-commit (checks/05e) + pre-push (4e)",
        ("cap-gates-hard" in _precommit_hook_text())
        and (pp.exists() and "cap-gates-hard" in pp.read_text(encoding="utf-8")),
        "los gates G1-G6 no están cableados HARD en los hooks (advisory≠enforcement).",
    )


# ── CHECK 12 — cap-display = función, no versión (HB-52 · proceso v5 W1) ──────
# Anti-rot CON DIENTES: «✨ Qué puedo hacer» SIEMPRE responde QUÉ HAGO, nunca la
# versión interna del SDD. Si alguien reintroduce v3.x/F.3/migrará en el empty-state
# de ScenariosSection, o borra el fallback a user_facing_description, el CHECK falla.
# (negative-test: re-insertar "Cap todavía v3.1 · migrará…" → exit 1.)
# ★ Pivote cockpit 2026-06-11 (ratificado Chris): la UI del cockpit vive en el
# repo prenter-harness (products/cockpit-ui/, embebida en el binario Go) — ya NO en
# tools/ de este workspace. El check evalúa la fuente externa si está presente
# en la máquina; ausente (ej. CI sin el repo hermano) → pass con nota.
COCKPIT_UI_ROOT = Path(os.environ.get("COCKPIT_UI_DIR", str(Path.home() / "Proyectos/prenter-harness/products/cockpit-ui")))
CAP_DISPLAY_FILE = "components/cap-drawer/sections/ScenariosSection.tsx"
CAP_DISPLAY_VERSION_JARGON = re.compile(r"v3\.\d|F\.3|migrar|Fase\s+F\.3", re.IGNORECASE)


def check_cap_display_no_version_jargon() -> None:
    if not COCKPIT_UI_ROOT.exists():
        check("CHECK 12 · cap-display (cockpit-ui externo no presente — no evaluable acá)", True, "")
        return
    p = COCKPIT_UI_ROOT / CAP_DISPLAY_FILE
    if not p.exists():
        check("CHECK 12 · ScenariosSection existe", False, f"falta {COCKPIT_UI_ROOT / CAP_DISPLAY_FILE}")
        return
    text = p.read_text(encoding="utf-8", errors="ignore")
    jargon = CAP_DISPLAY_VERSION_JARGON.search(text)
    check(
        "CHECK 12 · cap-display sin jerga de versión (HB-52)",
        jargon is None,
        f"{CAP_DISPLAY_FILE} muestra jerga de versión del SDD interno "
        f"(«{jargon.group(0) if jargon else ''}») en la vista funcional. "
        "«✨ Qué puedo hacer» SIEMPRE responde función, nunca versión (v3.x/F.3/migrará). "
        "Quitala + caé al texto funcional (user_facing_description).",
    )
    check(
        "CHECK 12 · cap-display tiene fallback funcional (user_facing_description)",
        "userFacingDescription" in text or "user_facing_description" in text,
        f"{CAP_DISPLAY_FILE} no referencia user_facing_description — el empty-state debe "
        "caer al texto funcional de la cap, no a un placeholder mudo (HB-52 invariante).",
    )


# ── CHECK 13-18 — spine G/R/auditor (proceso v5 W2 · story-closure-gate) ─────
# Anti-rot CON DIENTES del corazón del rediseño: G (Chris-verify) pausa antes del
# auditor, R (reconcile) precede al auditor, el signoff es UN solo campo, y la
# story en G NO deadlockea su módulo. Si cualquier cable se corta → CHECK falla.
DEVTEAM_SKILL = ".claude/skills/dev-team/SKILL.md"
CHECKPOINT_TMPL = "docs/specs/templates/checkpoint-template.md"
CLOSURE_RULE = ".claude/rules/story-closure-gate.md"
AUDITOR_SKILL = ".claude/skills/auditor/SKILL.md"
PM_SKILLS = [
    ".claude/skills/pm-vitalia/SKILL.md",
]
DOD37_RULE = ".claude/rules/definition-of-done-live-verify.md"


def _read(rel: str) -> str:
    p = WS / rel
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""


def check_g_pause_wired() -> None:
    t = _read(DEVTEAM_SKILL)
    check(
        "CHECK 13 · G · dev-team pausa-y-ofrece (AWAIT_CHRIS_VERIFY) en vez de auto-handoff",
        "AWAIT_CHRIS_VERIFY" in t and "autonomous_mode" in t,
        f"{DEVTEAM_SKILL} no cablea la pausa G (AWAIT_CHRIS_VERIFY) + rama autonomous_mode. "
        "Sin esto el dev-team auto-handoffea a /auditor sin que Chris verifique (proceso v5 §5.3).",
    )


def check_chris_verify_schema() -> None:
    t = _read(CHECKPOINT_TMPL)
    check(
        "CHECK 14 · checkpoint schema tiene chris_verify (signoff + rounds) + reconciled",
        "chris_verify:" in t and "rounds:" in t and "reconciled:" in t,
        f"{CHECKPOINT_TMPL} no tiene el bloque chris_verify (signoff/rounds) + reconciled. "
        "Es el hogar del signoff de G + el marcador de R (proceso v5 §5.3/§5.4).",
    )


def check_await_verify_wip_exempt() -> None:
    # ★ guard del deadlock: la story en G no debe contar contra developed≤1.
    dev = _read(DEVTEAM_SKILL)
    closure = _read(CLOSURE_RULE)
    dev_ok = "AWAIT_CHRIS_VERIFY" in dev and "PHASE" in dev and 'AWAIT_CHRIS_VERIFY"' in dev
    check(
        "CHECK 15 · WIP-cap exime AWAIT_CHRIS_VERIFY en dev-team REFUSE-gate (anti-deadlock)",
        dev_ok,
        f"{DEVTEAM_SKILL} no exime phase AWAIT_CHRIS_VERIFY en el gate module-scoped. "
        "Una story en G deadlockearía otra del mismo módulo (proceso v5 · story-closure-gate).",
    )
    check(
        "CHECK 15 · story-closure-gate documenta AWAIT_CHRIS_VERIFY como parked",
        "AWAIT_CHRIS_VERIFY" in closure,
        f"{CLOSURE_RULE} no documenta la exención WIP-cap de AWAIT_CHRIS_VERIFY.",
    )


def check_signoff_single_field() -> None:
    # anti-dup: el signoff vive en chris_verify.signoff (G). NADIE debe gatear por
    # demo_signoff.result (el viejo campo F, duplicado).
    for rel in (PM_SKILLS[0], DOD37_RULE):
        t = _read(rel)
        check(
            f"CHECK 16 · signoff único chris_verify (no demo_signoff.result activo): {rel}",
            "chris_verify.signoff" in t and "demo_signoff.result" not in t,
            f"{rel} aún gatea por demo_signoff.result (duplicado F+G) o no referencia "
            "chris_verify.signoff. El signoff es UN solo campo en G (proceso v5 §5.3).",
        )


def check_reconcile_step() -> None:
    for rel in PM_SKILLS:
        t = _read(rel)
        check(
            f"CHECK 17 · R · reconcile-step (pre-auditor) + reconciled marker: {rel}",
            "reconcile" in t.lower() and "reconciled" in t,
            f"{rel} no tiene el paso R (reconcile pre-auditor) + marcador reconciled. "
            "Sin R el auditor lee un spec stale (proceso v5 §5.4).",
        )
    closure = _read(CLOSURE_RULE)
    check(
        "CHECK 17 · story-closure-gate documenta Fase R (reconcile)",
        "RECONCILE" in closure.upper(),
        f"{CLOSURE_RULE} no documenta la Fase R entre developed y reviewing.",
    )


def check_auditor_reads_reconciled() -> None:
    t = _read(AUDITOR_SKILL)
    check(
        "CHECK 18 · auditor precondición reconciled + chris_verify.signoff + rounds-allowlist",
        "reconciled" in t and "chris_verify" in t and "rounds" in t,
        f"{AUDITOR_SKILL} no exige reconciled (o autonomous) ni lee chris_verify.signoff/rounds. "
        "El auditor guardián NO revierte scope ratificado pero un delta fuera de rounds sí es "
        "finding (proceso v5 §5.5).",
    )


# ── CHECK 19-21 — mutation gate diff-scoped (proceso v5 W3 · HB-54) ───────────
# Anti-rot del gate de mutación: el wrapper diff-scoped existe + DEGRADA advisory si
# el tool no está (D-B: mutmut/Stryker ausentes hoy) + el survivor heredado rutea a L4.
MUTATION_GATE = "scripts/mutation_gate.py"
ARCHITECT_SKILL = ".claude/skills/architect/SKILL.md"
VALIDATORS_TMPL = "docs/specs/templates/04-validators-template.yaml"


def check_mutation_gate_validators() -> None:
    val = _read(VALIDATORS_TMPL)
    arch = _read(ARCHITECT_SKILL)
    dod = _read(DOD37_RULE)
    check(
        "CHECK 19 · 04-validators technical_gates.mutation (enabled/mode/surfaces)",
        "mutation:" in val and "surfaces:" in val and "mode:" in val,
        f"{VALIDATORS_TMPL} no tiene el bloque technical_gates.mutation (enabled/mode/surfaces) "
        "que /architect marca por verification_nature (proceso v5 §5.6).",
    )
    check(
        "CHECK 19 · architect marca superficies mutation-críticas + #37 aloja el gate",
        ("technical_gates.mutation" in arch or "mutation_gate.py" in arch) and "mutation_gate.py" in dod,
        "architect no marca technical_gates.mutation o #37 §2 no aloja scripts/mutation_gate.py.",
    )


def check_mutation_degrade_advisory() -> None:
    t = _read(MUTATION_GATE)
    check(
        "CHECK 20 · mutation_gate.py DEGRADA advisory si el tool está ausente (no rompe ci-parity)",
        bool(t) and "tool is None" in t and "DEGRADADO" in t and "return 0" in t,
        f"{MUTATION_GATE} no degrada a advisory cuando mutmut/Stryker está ausente. "
        "Sin el degrade, instalar/desinstalar el tool rompería el gate global (D-B · proceso v5 §5.6).",
    )


def check_inherited_survivor_routes_l4() -> None:
    t = _read(MUTATION_GATE)
    check(
        "CHECK 21 · mutation_gate.py rutea survivors HEREDADOS a CIL carril L4 (no bloquean)",
        "L4" in t and "continuous-improvement" in t,
        f"{MUTATION_GATE} no rutea survivors de código heredado al carril L4 del CIL "
        "(capability-desfasada). Sin esto, mutar el diff bloquearía por test-debt viejo (proceso v5 §5.6).",
    )


# ── CHECK 22-24 — CIL 4 carriles + /harnesses-improvement + routing (W4) ──────
# Anti-rot del CIL: es un ROUTER (no 5º store), el ritual existe + invoca el deep-sweep,
# learning-capture rutea al carril (DIP), y el parser cockpit tipa carril ADDITIVE (D-C).
CIL_DOC = "docs/process/continuous-improvement.md"
HARNESS_IMPROVE_SKILL = ".claude/skills/harnesses-improvement/SKILL.md"
LEARNING_CAPTURE = ".claude/rules/learning-capture.md"
COCKPIT_PARSER = "lib/harness-backlog.ts"  # relativo a COCKPIT_UI_ROOT (pivote alpaca 2026-06-11)
HARNESS_AUDIT_WF = ".claude/workflows/harness-audit.js"


def check_cil_index_router() -> None:
    cil = _read(CIL_DOC)
    parser_path = COCKPIT_UI_ROOT / COCKPIT_PARSER
    parser = parser_path.read_text(encoding="utf-8", errors="ignore") if parser_path.exists() else ""
    check(
        "CHECK 22 · CIL es router a los 4 hogares existentes (L1 backlog · L2 learnings · L3 tech-debt · L4 cap_doctor)",
        bool(cil)
        and "harness-backlog" in cil
        and "learning-capture" in cil
        and "tech-debt" in cil
        and "cap_doctor" in cil,
        f"{CIL_DOC} no apunta a los 4 hogares (debe ser router, NO 5º store: L1→harness-backlog, "
        "L2→learning-capture, L3→tech-debt, L4→cap_doctor). proceso v5 §5.7.",
    )
    if not COCKPIT_UI_ROOT.exists():
        check("CHECK 22 · cockpit parser (cockpit-ui externo no presente — no evaluable acá)", True, "")
        return
    check(
        "CHECK 22 · cockpit parser tipa carril ADDITIVE (conserva severidad · D-C)",
        "HarnessCarril" in parser and "HarnessSeveridad" in parser,
        f"{COCKPIT_PARSER} no tipa carril manteniendo severidad — la extensión a 4-lanes "
        "debe ser additive (OCP), no reemplazar la dimensión severidad (D-C).",
    )


def check_harnesses_improvement_skill() -> None:
    skill = _read(HARNESS_IMPROVE_SKILL)
    audit_wf = WS / HARNESS_AUDIT_WF
    check(
        "CHECK 23 · /harnesses-improvement lee 4 carriles + invoca deep-sweep + sin ref colgante",
        bool(skill)
        and "L4" in skill
        and "harness-audit-2026" in skill
        and "continuous-improvement" in skill
        and audit_wf.exists(),
        f"{HARNESS_IMPROVE_SKILL} no existe / no lee los 4 carriles / no invoca el deep-sweep "
        "harness-audit-2026, o el workflow que referencia no existe (ref colgante). proceso v5 §5.7.",
    )


def check_learning_capture_routing() -> None:
    lc = _read(LEARNING_CAPTURE)
    cil = _read(CIL_DOC)
    check(
        "CHECK 24 · learning-capture rutea al carril (DIP · CIL no forkea la taxonomía)",
        "carril" in lc and "continuous-improvement" in lc and "learning-capture" in cil,
        f"{LEARNING_CAPTURE} no rutea al carril del CIL, o el CIL no depende de su taxonomía "
        "(DIP roto: el CIL no debe forkear los paths canónicos de learnings). proceso v5 §5.7.",
    )


# ── CHECK 25-27 — ledger de cobertura vivo (proceso v5 W5 · §5.2) ─────────────
# Anti-rot del ledger: la § Matriz tiene columna estado VIVA (productor dev-team la
# mantiene · auditor la congela) + piso HARD happy-path (func. nueva no difiere el core).
SPEC_TMPL = "docs/specs/templates/01-spec-template.md"


def check_ledger_estado_column() -> None:
    spec = _read(SPEC_TMPL)
    aud = _read(AUDITOR_SKILL)
    check(
        "CHECK 25 · 01-spec § Matriz tiene columna estado VIVA + auditor la congela",
        "LEDGER DE COBERTURA VIVO" in spec
        and "✅ construido" in spec
        and "Ledger de cobertura" in aud
        and "congela" in aud,
        f"{SPEC_TMPL} no tiene la columna estado viva en la § Matriz, o {AUDITOR_SKILL} no la "
        "congela en Phase D. Sin esto el ledger no responde 'qué NO está construido' (proceso v5 §5.2).",
    )


def check_ledger_producer_step() -> None:
    dev = _read(DEVTEAM_SKILL)
    check(
        "CHECK 26 · dev-team es PRODUCTOR del ledger (mantiene estado vivo en developing)",
        "PRODUCTOR" in dev and "✅ construido" in dev,
        f"{DEVTEAM_SKILL} no tiene el paso productor del ledger. Sin él la § Matriz nace en "
        "refined y llega STALE a G — Chris leería una foto vieja (proceso v5 §5.2 · fix REVIEW).",
    )


def check_ledger_happy_floor() -> None:
    spec = _read(SPEC_TMPL)
    dev = _read(DEVTEAM_SKILL)
    closure = _read(CLOSURE_RULE)
    check(
        "CHECK 27 · piso HARD happy-path (cap_change_type: new → core ✅, no se difiere)",
        ("PISO HARD" in spec and "cap_change_type" in spec) and "PISO HARD" in dev and "happy-path" in closure.lower(),
        "el piso HARD happy-path no está documentado en spec-template + dev-team + story-closure-gate. "
        "Funcionalidad nueva NO puede llegar a done con el core diferido (proceso v5 §5.2/principio 3).",
    )


# ── CHECK 28 — anti-rot de punteros del harness (ADVISORY · baseline-ratchet) ──
def check_harness_pointers() -> None:
    """Punteros workspace-rooted ROTOS en skills/agents/rules vs baseline. ADVISORY
    (no bloquea): solo reporta rot FRESCO (refs no baselined). Drená el baseline
    arreglando el puntero + corriendo scan_harness_pointers.py --update-baseline.
    SSoT del scan: scripts/scan_harness_pointers.py (HB · 2026-06-08)."""
    try:
        sys.path.insert(0, str(WS / "scripts"))
        from scan_harness_pointers import find_broken_pointers, load_baseline
    except Exception as e:  # noqa: BLE001 — scanner ausente/roto = advisory, no rompe machinery
        warn("CHECK 28 · harness pointers (advisory)", True, f"scanner no disponible ({e}) — skip")
        return
    broken = find_broken_pointers()
    baseline = load_baseline()
    new = broken - baseline
    fixed = baseline - broken
    detail = ""
    if new:
        detail += f"{len(new)} ref(s) workspace-rooted ROTOS NUEVOS (rot fresco):\n      " + "\n      ".join(
            f"✗ {b}" for b in sorted(new)
        )
        detail += "\n      → arreglá el puntero, o si es deliberado: scripts/scan_harness_pointers.py --update-baseline"
    if fixed:
        detail += (
            f"\n      ({len(fixed)} ref(s) del baseline YA arreglados — drenalos con --update-baseline)"
            if detail
            else f"{len(fixed)} ref(s) del baseline YA arreglados — drenalos con --update-baseline (shrink-only)"
        )
    warn(
        f"CHECK 28 · harness pointers sin rot nuevo (advisory · {len(broken)} baselined)",
        not new,
        detail or "ok",
    )



# ── CHECK 29 — core-harness/ proxy-clean (W10 anti-rot · el "cheap W8" automatizado) ──
# El kit extraíble NUNCA nombra tech/brand del producto-fuente (charter §0.5/§4 DoD).
# Patrón verbatim del charter; única excepción blessed: grep-bot skip-dirs genéricos (W3).
CORE_HARNESS_PROXY_TOKENS = re.compile(
    r"vitalia|nicolify|comunify|lupulo|ruff|pytest|mypy|alembic|clerk|next\.js|"
    r"tailwind|fastapi|sqlalchemy|core/luana-core|\.venv|dev-app|hipaa|phi"
)
CORE_HARNESS_PROXY_ALLOWED = {"agents/grep-bot.md"}  # build-artifact skip-dirs (.venv) — funcional, no smear


def check_core_harness_proxy_clean() -> None:
    root = WS / "core-harness"
    bad: list[str] = []
    if root.exists():
        for f in sorted(root.rglob("*")):
            if not f.is_file() or f.is_symlink():
                continue
            rel = str(f.relative_to(root))
            if rel in CORE_HARNESS_PROXY_ALLOWED:
                continue
            try:
                text = f.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if CORE_HARNESS_PROXY_TOKENS.search(line):
                    bad.append(f"core-harness/{rel}:{i}: {line.strip()[:80]}")
    check(
        "CHECK 29 · core-harness/ proxy-clean (0 tech/brand tokens fuera de grep-bot)",
        not bad,
        "el kit dejó de ser extraíble — token de proyecto en CORE:\n      " + "\n      ".join(bad[:10]),
    )


# ── CHECK 30 — LSP sync template↔instancias PM (W10 anti-rot) ────────────────
# Conceptos que _pm-sistema-template cementa y CADA pm-{brand} activa debe llevar
# (drift real cazado 2026-06-09: pm-comunify/pm-lupulo sin § Auto-chain rule).
# Concept-based (substring) como CHECK 9. Agregá un concepto al cementarlo en el template.
PM_TEMPLATE_CONCEPTS = ["Auto-chain rule", "story-closure-gate", "chris-input", "Step 0"]
PM_SKILL_FILES = [
    ".claude/skills/_pm-sistema-template/SKILL.md",
    ".claude/skills/pm-vitalia/SKILL.md",
]


def check_pm_template_instance_sync() -> None:
    missing: list[str] = []
    for rel in PM_SKILL_FILES:
        f = WS / rel
        if not f.exists():
            missing.append(f"{rel} (archivo ausente)")
            continue
        body = f.read_text(encoding="utf-8")
        for concept in PM_TEMPLATE_CONCEPTS:
            if concept not in body:
                missing.append(f"{rel}: falta concepto '{concept}'")
    check(
        "CHECK 30 · PM template↔instancias sync (conceptos cementados presentes en c/skill)",
        not missing,
        "LSP drift template↔instancia:\n      " + "\n      ".join(missing),
    )


# ── CHECK 31 — frontmatter model: = seam models.* (sync_model_tiers --check) ──
def check_model_tier_sync() -> None:
    """Modelos Claude SOLO viven en project.config.yaml::models (SLOT 12).

    Frontmatter `model:` de .claude/{agents,skills} (+espejos) es artefacto
    generado por `make models-sync`. Drift = alguien editó frontmatter a mano
    o agregó superficie sin mapearla en el seam.
    """
    import subprocess

    script = WS / "scripts" / "sync_model_tiers.py"
    if not script.exists():
        check("CHECK 31 · model-tier sync script existe", False, "falta scripts/sync_model_tiers.py")
        return
    proc = subprocess.run(
        [sys.executable, str(script), "--check"], capture_output=True, text=True, cwd=WS
    )
    check(
        "CHECK 31 · frontmatter model: = project.config.yaml::models (cero modelos hardcodeados)",
        proc.returncode == 0,
        (proc.stdout + proc.stderr).strip()[:800],
    )


# ── CHECK 32 — seam-testing gate (HB-94/95/96/97) con dientes + cableado ──────
def check_seam_gate_wired() -> None:
    """Cubierto = colaborador real, no mock. El gate scripts/check_seam_coverage.py
    debe (a) tener dientes (un false-green mockeado → FAIL en --self-check) y
    (b) estar cableado: declarado en template+architect (HB-95), corrido en
    dev-team Phase D + auditor (HB-96), doctrina cementada (HB-94).
    """
    import subprocess

    script = WS / "scripts" / "check_seam_coverage.py"
    if not script.exists():
        check("CHECK 32 · seam-coverage gate existe", False, "falta scripts/check_seam_coverage.py (HB-94..97)")
        return
    proc = subprocess.run(
        [sys.executable, str(script), "--self-check"], capture_output=True, text=True, cwd=WS
    )
    check(
        "CHECK 32 · check_seam_coverage --self-check pasa (gate con dientes: false-green mockeado → FAIL)",
        proc.returncode == 0,
        (proc.stdout + proc.stderr).strip()[:800],
    )
    val = _read(VALIDATORS_TMPL)
    arch = _read(ARCHITECT_SKILL)
    dev = _read(".claude/skills/dev-team/SKILL.md")
    aud = _read(AUDITOR_SKILL)
    tdd = _read(".claude/skills/dev-team/references/test-design-doctrine.md")
    check(
        "CHECK 32 · seam_coverage declarado en template + architect (HB-95)",
        "seam_coverage:" in val and "seam_coverage" in arch,
        "04-validators-template o architect SKILL no declaran seam_coverage.",
    )
    check(
        "CHECK 32 · seam gate cableado en dev-team Phase D + auditor (HB-96)",
        "check_seam_coverage.py" in dev and "check_seam_coverage.py" in aud,
        "dev-team Step 4.5 o auditor Phase D no corren check_seam_coverage.py.",
    )
    check(
        "CHECK 32 · doctrina seam cementada en test-design-doctrine (HB-94 · cubierto = colaborador real)",
        "colaborador real" in tdd,
        "test-design-doctrine reference no cementa la doctrina seam (cubierto = colaborador real).",
    )


def main() -> int:
    print("validate_machinery_consistency.py — anti-drift lock-in\n")
    check_atomics_dead()
    check_assignment_block()
    check_premultibrand_paths()
    check_dispatch_plan_template()
    check_rules_registered()
    check_rule_refs_resolve()
    check_auditors_have_edit()
    check_self_wired_in_precommit()
    check_spec_template_drift()
    check_cap_locator_wired()
    check_cap_format_enforcement_wired()
    check_cap_display_no_version_jargon()
    check_g_pause_wired()
    check_chris_verify_schema()
    check_await_verify_wip_exempt()
    check_signoff_single_field()
    check_reconcile_step()
    check_auditor_reads_reconciled()
    check_mutation_gate_validators()
    check_mutation_degrade_advisory()
    check_inherited_survivor_routes_l4()
    check_cil_index_router()
    check_harnesses_improvement_skill()
    check_learning_capture_routing()
    check_ledger_estado_column()
    check_ledger_producer_step()
    check_ledger_happy_floor()
    check_core_harness_proxy_clean()
    check_pm_template_instance_sync()
    check_model_tier_sync()
    check_seam_gate_wired()
    check_harness_pointers()  # CHECK 28 — advisory (no afecta exit)
    print(f"\n{checks_run} checks · {len(failures)} fallos · {len(warnings)} advisory")
    if warnings:
        print("\nADVISORY (no bloquea — atender en /harnesses-improvement):")
        for w in warnings:
            print(f"  ⚠ {w.splitlines()[0]}")
    if failures:
        print("\nFALLOS (drift detectado):")
        for f in failures:
            print(f"  - {f.splitlines()[0]}")
        return 1
    print("✓ machinery consistente — sin drift")
    return 0


if __name__ == "__main__":
    sys.exit(main())
