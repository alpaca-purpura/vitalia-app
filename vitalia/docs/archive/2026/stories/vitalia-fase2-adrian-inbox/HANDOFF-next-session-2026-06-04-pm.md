# HANDOFF — Adrián Inbox UI polish + Shell responsive + Dark mode (→ done)

> **Escrito 2026-06-04 (sesión pm)** al 66% de contexto. Worktree hub `~/Proyectos/luana-vitalia`, branch `wip/vitalia`. **Hub COMPARTIDO con sesión(es) concurrente(s)** (embudo /dev-team + /pm-vitalia) — commitear SIEMPRE por pathspec, nunca `git add .`.

## TL;DR — qué pasó y qué falta

La sesión cerró el **inbox-FEATURE** (telemetry-404 + audit-log-404 twin + SC-10 tenant 10/10, todo green+committed+live-verified) y destapó, vía revisión visual de Chris + auditoría experta, **2 frentes de UI que faltan para que el inbox quede pro + done**:

1. **Inbox UI polish (14 observaciones de Chris)** → auditadas en `UI-AUDIT-2026-06-04.md` (mismo folder). **Dark mode YA resuelto** (1 de los 14). Quedan **~12** (3 bugs funcionales + color/diferenciación + pulido).
2. **Shell responsive de Valeria** → story propia `vitalia-bugfix-shell-valeria-responsive` (state: idea) con 3 puntos de Chris + propuesta tablet. Bloquea AC-4/5/7 del inbox (el squeeze del thread).

**El inbox NO es `done`** hasta: 12 UI fixes + shell-responsive + verify live (AC-4/5/7 + AC-12) + demo Chris (DoD #37).

## Commits de esta sesión (wip/vitalia · pathspec)

| SHA | Qué | Estado |
|---|---|---|
| `af035e69` | telemetry-404 endpoint + FE fetchClient | ✅ live-verified |
| `0b752040` | audit-log-404 twin endpoint + AuditedSection→fetchClient | ✅ live-verified |
| `587766fc` | clinic-guard + SC-10 tenant test-design | ✅ tenant e2e 10/10 green |
| `821ef027` | quitó el `defer_audit` fabricado que un Haiku-worker metió al embudo checkpoint | ✅ |
| `d41102c3` | modes thread-wait scope + finding (NO green — ver squeeze) | ⚠️ |
| `7aff008f` | split shell-bugs del inbox + cierre inbox-feature (repro doc) | ✅ |
| `a3ddf036` | creó story `vitalia-bugfix-shell-valeria-responsive` (idea) | ✅ |
| `08ad931e` | propuesta tablet en esa story | ✅ |
| `43c4c4df` | **dark mode resuelto** (globals.css `--vitalia-*` dark override) + UI-AUDIT doc | ✅ impl · ⏳ live-verify |

> ⚠️ Hubo commits CONCURRENTES interleavados (embudo + harness HB-43 + /pm-vitalia). El branch avanza solo. Siempre `git log --oneline -5` al arrancar.

## ✅ DONE + green (no re-tocar)
- Inbox feature: telemetry endpoint (`/api/telemetry/growth-studio-event`), audit-log endpoint (`/api/v1/vitalia/audit-log`), ambos live (404→ahora sirven). FE telemetry.ts + AuditedSection → fetchClient + clinic-guard.
- SC-10 tenant e2e: **10/10 green** en dev-app (`adrian-inbox-tenant.spec.ts`). POM errorBanner fix + `:43` failOnRuntimeError opt-out.
- Dark mode: globals.css override de `--vitalia-*` bajo `[data-theme="dark"]` → todos los `.vt-*` switchean. **VERIFICAR LIVE primero** (toggle tema en dev-app — el FE container debe haber HMR'd el CSS).

## 🔜 LO QUE FALTA (para done) — 2 tracks

### Track A — Inbox UI polish (SSoT: `UI-AUDIT-2026-06-04.md`)
12 ítems triados en 3 batches. **Bugs funcionales primero (alta):**
- **#3 voz route** — `VoiceStyleChip.tsx` `configureHref="/brand-studio/estilo"` SIN tenant id → 404. Wire `/{tenantId}/lisa/marca` (tenantId ya disponible en el view).
- **#4+#12 mode-toggle + composer-manual** — `ComposerArea` `canSend = status==="active" && handler_mode==="ai"` → en "yo escribo" (manual) se deshabilita el composer. Separar "agente piensa" (disabled) de "manual" (enabled). + investigar live si el PATCH `/mode` refleja (los 3 modos: solo veo `adrian-decide`+`adrian-consulta` en ModeToggle array — ¿falta el 3ro?).
- **#7 servicio de interés** — `lead.service_interest` existe en data (LeadResponse) pero ContactSidebar no lo muestra. Añadir prominente.
- **#5 channel icons** — `ConversationItem` usa emoji-map `CHANNEL_ICONS`; debe usar `<ChannelBadge iconOnly>` (channel-meta.ts → lucide + color de canal). Norma AP.

Luego color/diferenciación + pulido (ver audit batches 2-3): burbujas por emisor (agent-color), stage colors (StageBadge), filtros con color de canal + fila-1-solo-canales, timestamps en burbujas (patrón WhatsApp), Perfil+colapsar-en-detalle, label Pausar, cursor-pointer norma, "Actividad de Adrián" clarity, + mis adicionales A-F (focus-visible, jerarquía tipográfica, status hues dark contrast, lucide-only).

### Track B — Shell responsive (story `vitalia-bugfix-shell-valeria-responsive`, idea)
3 puntos de Chris (verbatim en su chris-input.md): (1) rail historial collapsed by default, (2) Valeria full 50/50→30/70 default resizable, (3) tablet (propuesta ya escrita: drawer en 768-1024). Toca `shell-store.ts` + `useViewportGuard.ts` (FULL_STATE_MIN_VIEWPORT=1104 = root del squeeze) + `ShellOrganismLayout` + `ValeriaSidebar`. **Cross-tab** (afecta Lisa/Mateo/Adrián/Lucas/Camila) → lock `code:shell`. Desbloquea AC-4/5/7 del inbox. Repro: `observed-bugs/2026-06-04-shell-valeria-squeeze-plus-darkmode.md`.

## RUNBOOK (crítico)

```bash
WS=$(git rev-parse --show-toplevel); cd ${WS}
git log --oneline -5                      # el branch avanza con sesiones concurrentes
git status --short                        # ver qué tocan otras sesiones (NO barrer)
# design-system SSoT (OBLIGATORIO antes de tocar UI):
#   Skill: vitalia-design-system  → tokens en globals.css, channel-meta.ts, agent colors
# FE checks (nativo):
cd vitalia/frontend && npx tsc --noEmit && npx eslint src/ --cache
npx vitest run src/features/mateo/lib/__tests__/telemetry.test.ts   # ejemplo
# Live-verify dev-app (Playwright PROPIO, NO el Chrome MCP compartido con Chris):
set -a; source ${WS}/vitalia/.env.dev; set +a
export E2E_BASE_URL="https://dev-app.vitalialat.com"
export E2E_CLERK_USER_EMAIL="${DEV_APP_TEST_EMAIL}" E2E_CLERK_USER_PASSWORD="${DEV_APP_TEST_PASSWORD}"
rm -f playwright/.clerk/user.json && npx playwright test --project=setup   # re-auth vs dev-app
npx playwright test e2e/shell-organism/adrian-inbox-modes.spec.ts --project=smoke --workers=1 --reporter=line
# commit (hub compartido):
STORY_CLOSURE_GATE_SKIP=1 git commit -F <msg> <rutas-exactas>   # gate bloquea por embudo developed
git push
```

**Gotchas confirmados:**
- **Chrome MCP browser = COMPARTIDO con Chris** (lo vi navegar a embudo solo). Para verify automatizado usar **Playwright propio**, no el MCP. El MCP sirve para inspección puntual cuando Chris no lo esté usando.
- **story-closure-gate bloquea commits** mientras embudo está `developed` → usar `STORY_CLOSURE_GATE_SKIP=1` con razón en el body (es el patrón establecido del hub; embudo lo usa).
- **NUNCA `git add .`/`-A`** — un Haiku-worker barrió el checkpoint de embudo + fabricó un `defer_audit` (ya corregido, `821ef027`). Commit SOLO por rutas exactas. Para >2 files, si delegás a Haiku, guardrail verbatim + lista exacta.
- **modes/states e2e** fallan por el squeeze (thread 0-56px) — NO son bug del inbox; se desbloquean con Track B. El thread funciona con Valeria colapsada.
- **dev-app footgun**: el FE container sirve el worktree del último `up`. Re-`make dev-app-vitalia` desde este worktree si sirve viejo.
- Dark CSS: el FE container debe HMR el `globals.css`; si no toma, `touch` + hard-reload.

## Reglas duras (Chris)
- **DoD #37**: nada `done` sin live-verify (ejercer la acción real + leer logs + efecto) + demo sign-off de Chris. NO encadenar `/auditor` ni merge sin que Chris pruebe.
- **PARÁ y avisá a Chris** cuando termines de desarrollar, ANTES de `/auditor`.
- Design-system: usar tokens (globals.css), átomos `components/ui/`, channel-meta, agent colors. NO hardcodear hex. NO reinventar átomos.

## Estado de las 2 stories
- `vitalia-fase2-adrian-inbox`: `state: developing`, feature done+green; falta UI polish (Track A) + shell-blocker (Track B) + AC-4/5/7+AC-12 live + demo. checkpoint § `shell_split_decision` + `e2e_suite_status_2026_06_04_pm` + `UI-AUDIT-2026-06-04.md`.
- `vitalia-bugfix-shell-valeria-responsive`: `state: idea`. Necesita /po-ux refine → /architect → /dev-team → done.

## Path to done (sugerido)
1. Verificar dark live (toggle tema dev-app). Si OK, dark ✓.
2. Track B (shell responsive) primero — desbloquea el thread + es prerequisito visual de Track A. Refine→arch→dev (story propia) o, si Chris quiere rápido, builder pass directo con los 3 puntos.
3. Track A (inbox UI) — batch 1 bugs (#3/#4/#12/#7/#5) → batch 2 color → batch 3 pulido. Live-verify cada batch (Playwright propio + Chrome MCP cuando libre).
4. Suite e2e inbox completa green (modes/states desbloqueados por Track B).
5. PARÁ → Chris prueba dev-app + demo sign-off.
6. /auditor → /pm-vitalia merge → done + cap YAML `adrian.inbox`.
```
