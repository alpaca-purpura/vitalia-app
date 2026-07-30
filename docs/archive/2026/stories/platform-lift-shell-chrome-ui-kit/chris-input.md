---
story_id: platform-lift-shell-chrome-ui-kit
created_at: 2026-06-11T00:00:00-05:00
last_modified: 2026-06-11T00:00:00-05:00
notes_count: 0
refs_count: 4
conversation_count: 1
---

# chris-input.md · platform-lift-shell-chrome-ui-kit

> **Qué es este archivo:** acá Chris escribe notas + referencias + Claude responde con verdicts. Cocina de la story (la conversación) — separada del spec/design/arch.
>
> Doc canónico: `docs/process/chris-input-protocol.md`.

## 💭 Notas

### 2026-06-11
Sin notas adicionales todavía · Chris escribe aquí.

## 📎 Referencias

- **📄 doc** · `docs/promotion-protocol/proposals/2026-06-01-lift-shell-organism-to-core.md` (accepted 2026-06-06 · § Estado post hardening = handoff de entrada)
- **📖 story-ref** · `vitalia-shell-core-hardening` (done 2026-06-11 — chrome hardened, predecesora directa)
- **📄 doc** · `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` v1.4 + `ADR-vitalia-006` (SSR-safe store)
- **📚 learning-ref** · memoria `shell-core-hardening-done-lift-pending` + `2026-06-06-n3-entity-workspace-layout-from-nicolify`

## 💬 Conversación

> Append-only · turn-by-turn cronológico. Verdict labels: ✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE.

### 2026-06-11 · 👤 Chris · input de creación (lift autónomo end-to-end)
> /pm-luana ejecuta el LIFT del shell-chrome a @luana/ui-kit — sesión autónoma completa (RATIFICO autonomous_mode: true verbatim para toda la cadena: refinar→arch→build→audit→merge; trabajá hasta el done sin pausas. Yo estoy descansando — escalá SOLO si encontrás un breaking-change imposible de decidir solo, y aun así documentá+parqueá esa pieza y seguí con el resto, dejando HANDOFF-next-session.md). [+ contexto fuentes en orden, objetivo chrome brand-agnostic props+CSS vars, criterios de éxito verbatim (68/68 + 7/7 contra kit, nicolify converge, grep tokens = 0, SEMVER documentado, allowlists shrink mismo commit, live-verify #37, proposal migrated), aprendizajes obligatorios del hardening, workspace hub vitalia + SCOPE_GATE_SKIP sancionado, subagents heredan Fable 5]

### 2026-06-11 · 🤖 claude · `/pm-luana` · ✓ APLICADO
Step 0 GREEN (hub canónico vitalia, wip/vitalia sync con origin/main, lock `code:shell` adquirido). Closure-gate: embudo DEFERRED (ok) · `nicolify-r1-abel-icp-buyer` en reviewing = jurisdicción /pm-nicolify, módulo ≠ shell → no bloquea (WIP cap module-scoped). Fuentes leídas en el orden pedido (memoria → proposal accepted → archive hardening 07-merge/T-5/03-arch § Decisión B). Story platform creada en `docs/product/stories/platform-lift-shell-chrome-ui-kit/` (checkpoint + chris-input juntos, R4) — `state: refining`, autonomous_mode true verbatim, aprendizajes del hardening pre-cargados en el checkpoint para que builders no los redescubran. Proposal queda `accepted` hasta el merge (→ `migrated`). Próximo: /po spec → /architect → /dev-team → /auditor → merge.

### 2026-06-11 · 🤖 claude · `/po` · ✓ APLICADO
01-spec.md v1 escrito (`refining → refined`). 9 scenarios: SC-1/2/3 happy (vitalia full verde contra kit · nicolify converge · kit brand-agnostic versionado) + SC-4 negative (mirror residual/cross-import) + SC-5/6/9 edge (máquina v4 props-capture · localStorage legacy · escape-valve pieza imposible Bif-1) + SC-7 adversarial (fuga brand al kit: grep + defaults props neutros) + SC-8 live-verify #37. RN-1..9 formalizan los criterios verbatim de Chris (conducta-no-cambia con suite 68+7 como contrato · brand-agnostic estricto · un-solo-origen · fixes v4 sagrados · ratchet shrink · SEMVER+proposal · convergencia nicolify sancionada · store SSR-safe de @luana/hooks · live-verify). Sin loop de ratificación: criterios YA dictados verbatim (autonomous). Corte file-by-file → /architect.

### 2026-06-11 · 🤖 claude · `/architect` (architect-orchestrator) · ✓ APLICADO
Ready package cerrado (`refined → ready`, 5 artefactos + 03-arch-fe). Decisiones: **corte** coupling-driven (máquina/layout/primitives → kit con props/inyección; agent-catalog/avatares/tokens/mock-chat/Tenant*/LogoMark/ThemeToggle → brand; TopBarGlobal → `TopBarShell` con slots por acople a TenantSwitcher) · **API** `ShellLayout` + sub-exports, stores INYECTADOS (`createShellStore` factory consume @luana/hooks, kit nunca importa stores brand) · **localStorage** vitalia conserva keys `vitalia-shell-state`/`vitalia-shell-split-agentic` (harness e2e 68+7 intacto, SC-6); nicolify migra `luanaState→supervisorOpen` · **ssr:false** wrapper vive en el KIT (mata duplicación del patrón frágil v4) · **SEMVER 0.3.0→0.4.0 minor** + flag colisión `Group` (barrel NO re-exporta react-resizable-panels) · **hallazgo real:** vitalia NO auto-escanea el kit en Tailwind → deliverable `@source` (sin él las clases JIT `@[24rem]`/`grid-cols-[minmax]` mueren silenciosas — gate visual, no tsc). 7 tickets DAG secuencial T-K1→K2→K3→V1→V2→N1→G, todos `model_preference: inherit` (Fable 5), fixes v4 SAGRADOS verbatim. Próximo: /dev-team.

### 2026-06-11 · 🤖 claude · `/dev-team` (7 tickets, autonomous) · ✓ APLICADO
`developing → developed`. **KIT:** organism/shell completo (30+ componentes, store factory, routing) — 259/259, version 0.4.0, grep brand-token lógica = 0. **VITALIA:** consume ShellLayout vía Wire (testIds legacy inyectados, keys localStorage conservadas, @source JIT), chrome local BORRADO + allowlist mirror encogida — suite final **84 passed / 1 fixme-deuda / 0 failed** + resizer-matrix 7/7 + tsc/eslint/vitest/arch verdes. **NICOLIFY:** converge — máquina legacy retirada (30 archivos), Wire con catálogo Luana/Abel/Brenda/Christian/Sara/Norvil, 514/514 + arch 46/46 (mirror cross-brand MUERTO). **Fix-loop Bif-3 (5 bugs del port, cero asserts tocados):** re-port verbatim ShellLayoutClient (D1-D5: Group siempre montado, shellReady, isCollapsed-retry/expand-first/snap-up, push ±actual) · useStoreHydration (ADR-006: sin él el store JAMÁS persiste) · TooltipProvider · userBubbleBgClass del supervisor · sub-label /75. **Edge-redirects N3:** censo refutó "solo landing" — 4 redirect() in-render más → proxy 307 (con kit el Rendered-more-hooks era determinista). **★ HALLAZGO MAYOR (upstream deficiency → auditor + CIL):** runs "verdes" del hardening escaneaban shell COLGADO (axe 0-violations fantasma + 2 asserts imposibles: dark .dark-class, ribbon `<a>`); destapado por el edge-redirect — deuda real destapada: ~10 contrastes dark en feature inbox (fixme rastreado CIL L3) + fixes WCAG quirúrgicos (mateo D20, cyan palette, aria roles). Live-verify #37: dod_evidence registrado (Playwright autenticado real-backend + 0 tracebacks BE/1741 reqs). 3 builders murieron mid-ticket (~140 tool-uses) — patrón continuation funcionó. Próximo: /auditor (autonomous, G saltada).

### 2026-06-11 · 🤖 claude · `/auditor` (auditor-frontend consolidado + gate-runner) · ✓ APLICADO
**APPROVED** (CHECKPOINTS.md C1-C5). Gates 12/12 (gate-output.json): kit 259 + vitalia tsc/eslint/vitest-2073/arch-187 + nicolify tsc/vitest-514/arch-117 + grep brand 0 + mirror-basename 0 + e2e 84/85+fixme (run externo citado). **RN-4 fidelity:** ShellLayoutClient verificado effect-por-effect vs fuente `3c1597dd~1` — solo renames brand→generic, fixes v4 sagrados intactos. **Harness adjustments validados** como contrato-real (no debilitan conducta): allowlist quirúrgico all-zeros, soft-nav assert refleja Ribbon real (el `<a href>` era assert-fantasma verificado contra fuente), fixme inbox-dark = deuda destapada-no-causada. **Scope exacto** = autorizado (kit+vitalia+nicolify; 0 Python engine; 0 cross-import). **CONN:** ShellLayout ≥2 consumers; SubTabContent correctamente brand-local. **Upstream deficiency** (verde-fantasma e2e del hardening) → **HB-68** registrado + § Upstream deficiency en review (resondrada la cadena T-7 hardening, no esta story). Phase D: gherkin-matrix SC-1..9 completa (SC-9 N/A — Bif-1 no ocurrió). Próximo: /pm-luana merge (07-merge + proposal migrated + archive).

### 2026-06-11 · 🤖 claude · `/pm-luana` (Fase F merge) · ✓ APLICADO
**DONE.** 07-merge.md 5 secciones · proposal `2026-06-01-lift-shell-organism-to-core` → **migrated** (SEMVER 0.4.0 minor + lift_summary) · archive R2 → `docs/archive/2026/stories/platform-lift-shell-chrome-ui-kit/` (mismo commit `3cb9d5a0`) · SHELL-DESIGN-CONTRACT v1.5 (chrome vive en kit) · cap-doctor vitalia ✅ 0 deriva · portfolio regen (outputs gitignored R3). Cadena autónoma completa refinar→spec→arch→build(7 tickets, 3 builders muertos + continuation)→audit→merge en una sesión, cero escalation (Bif-1 nunca ocurrió). Deuda visible: CIL L3 inbox-dark (fixme) + tsc kit-wide test-types · HB-68 (gate anti-shell-colgado). Siguiente natural: opt-in comunify/lupulo al chrome del kit + story de feature para inbox-dark.
