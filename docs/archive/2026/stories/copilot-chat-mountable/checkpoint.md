---
brand: platform
story_id: copilot-chat-mountable
story_type: technical-story        # engine fix · user_visible: false · zona Infraestructura
state: done                        # /pm-luana merge a main (squash) — engine fix shipped
phase: MERGED
reconciled: true                   # scope reconciliado: T-4 deferido por decisión Chris (G)
audit_verdict: APPROVED            # /auditor 2026-06-16 — CHECKPOINTS.md (0 findings código; 1 doc-coherence Carril-R fixeado: 04-validators reconciliado al descope; upstream HB-79)
merged_by: /pm-luana
merged_at: 2026-06-16
last_artifact: 07-merge.md
followups:
  - "proposal 2026-06-16-copilot-chat-brand-mountable → migrated (vive en wip/comunify; la marca /pm-comunify al re-montar)"
  - "comunify-shell-organism T-agentic v2: re-mount /chat engine (quitar guard try/except) — /pm-comunify sesión aparte"
  - "T-4 follow-up: completar approach C + retirar shim — /pm-luana cuando convenga (FOLLOWUP-T4-complete-C.md)"
chris_verify:
  required: true
  signoff:
    by: Chris
    date: 2026-06-16
    result: SATISFIED_WITH_FOLLOWUPS   # ship unblock; T-4 (completar C) → follow-up story
    notes: "Unblock /chat brand-mountable logrado + verificado (driver subprocess GREEN + R3-light 3 marcas). Shipear T-1/T-2/T-3; deferir T-4 (retirar shim) a story follow-up — el shim deprecado funciona."
  rounds: ["scope: T-4 deferido (47 settings + 61 database shim-users) — story follow-up"]
scope_change: "T-4/T-5-full removidos del scope de esta story (Chris G-decision). Story = unblock (T-1/T-2/T-3). Follow-up T-4 trackeado abajo."
tickets_done:
  - "T-1 config/database lazy + shim (commit bb8e34f8)"
  - "T-2 chat import-path → get_settings() + partial off-path (commit 13665a80) — driver subprocess GREEN"
  - "T-3 bump copilot 0.3.0 + platform 0.5.0 + CHANGELOG (commit 680144a0)"
followup_deferred:
  - "T-4 completar approach-C: migrar ~47 settings + ~61 database shim-users en 12 paquetes (connections 13, copilot 9, sales-agent 5, llm 3, campaigns 3, ...) + retirar el shim deprecado. Story nueva cuando convenga (shim funciona mientras tanto). Ver FOLLOWUP-T4-complete-C.md."
unblock_verified: "driver subprocess GREEN (chat.py importable env multibrand-only) + R3-light (3 marcas import OK) + suites tocadas GREEN (copilot 1641/platform 290/events 76/assets 58)"
module: core-platform              # build-claim bucket (core refactor)
user_visible: false
cap_change_type: fix               # corrige comportamiento del engine (import-time eager Settings), no crea cap nueva
cap_target: null
verification_nature: técnica       # gates + verificación-por-efecto (boot + 401/200), sin demo UI
demo_required: false
demo_skip_reason: "engine refactor sin UI — verificación = boot de marca con env multibrand + /chat responde 401/200 + R3 suite"
target_packages:
  - core/luana-core-platform        # config.py:317 (Settings eager) + database.py:32 (engine eager) + shim back-compat
  - core/luana-core-copilot         # api/chat.py (contract import-clean) + bump minor + CHANGELOG
  - core/luana-core-iam             # api/dependencies.py (drag database→config)
  - core/luana-core-connections     # consumers del global settings
  - core/luana-core-events          # consumer del global settings
semver_bump: minor                 # additive (shim deprecado durante transición); cero break standalone (no existe) + cero break 4 marcas
worktree: ~/Proyectos/luana-core-copilot-mountable (wip/core-copilot-mountable)
proposal: docs/promotion-protocol/proposals/2026-06-16-copilot-chat-brand-mountable.md  # state: accepted (vive en wip/comunify)
approach_signed:
  by: Chris
  date: 2026-06-16
  decision: "C — full lazy refactor: get_settings() en los ~55 call-sites, sin global mutable (shim back-compat deprecado durante transición para semver minor)"
  rejected: ["A lazy-module-boundary", "B router-factory"]
autonomous_mode: false             # build = /dev-team con ratificación final Chris del ready-package
next_action: "Chris ratifica el ready-package (blast-radius del cambio a luana_core_platform) → /dev-team build T-1 (desde el worktree core, uv sync primero). autonomous_mode: false."
last_modified: 2026-06-16
---

# copilot-chat-mountable — checkpoint

Engine fix: el `/chat` de `core/luana-core-copilot` no es brand-mountable porque importarlo instancia el `Settings` monolítico legacy (`luana_core_platform.core.config`) a import-time. Approach **C** (full lazy refactor a `get_settings()`) ratificado por Chris 2026-06-16. Build en worktree core efímero. Ver `00-contract-spec.md`.
