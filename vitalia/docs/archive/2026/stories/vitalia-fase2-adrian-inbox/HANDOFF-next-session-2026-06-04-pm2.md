# HANDOFF — Adrián Inbox + Shell responsive (→ done)

> **Escrito 2026-06-04 (sesión pm2).** Branch `wip/vitalia`, worktree hub `~/Proyectos/luana-vitalia`.
> **Hub COMPARTIDO** con sesión(es) concurrente(s) (embudo `code:crm` + refactor de arch-tests). Commitear SIEMPRE por pathspec, NUNCA `git add .`. `STORY_CLOSURE_GATE_SKIP=1` con razón (embudo está `developed`).
> Esta sesión terminó de DESARROLLAR las 2 stories; **falta el demo de Chris + /auditor + merge**. Chris tiene comentarios pendientes que dará en la sesión nueva.

## TL;DR — qué pasó

Se completó **TODO el desarrollo** de 2 stories hermanas (ambas `developing`, code-complete + **live-verified** en dev-app, esperando demo Chris):
1. **`vitalia-fase2-adrian-inbox`** — UI polish (3 batches: bugs + color + labels). 14 obs de Chris → ~10 resueltas, resto (abajo) pendiente.
2. **`vitalia-bugfix-shell-valeria-responsive`** — responsive de Valeria (3 puntos de Chris). Desbloquea el squeeze que tapaba AC-4/5/7 del inbox.

Todo gate-green (tsc/eslint/vitest) + live-verified por Playwright contra `dev-app.vitalialat.com`.

## Commits de esta sesión (wip/vitalia, todos pusheados, en orden)

| SHA | Qué | Verificación |
|---|---|---|
| `0dddae86` | inbox batch 1 — #5 channel badges · #3 voz route (`/{tenantId}/lisa/marca/voz-y-tono`) · #7 servicio de interés | ✅ live |
| `aa5efa04` | inbox batch 2 — #5b stage colors (`StageBadge` + `lib/stages/lead-stage-meta.ts`) · #8 filtros con color de canal | ✅ live |
| `fcd083de` | inbox batch 3a — #2 "Pausar" · #1 "Perfil" + #1b close X en sidebar · #13 actividad clarity (lucide) | ✅ live |
| `bfdc5277` | inbox — `dod_evidence` de los 3 batches en checkpoint | docs |
| `29451ef6` | **shell — Sonner `<Toaster>` montado** (estaba huérfano sin commitear; sin él los `toast()` del shell+inbox eran no-ops) | — |
| `b60817cb` | inbox — `StageBadge` deja de importar `LeadStage` de crm-shared (type `string`) → fix arch FSD | tsc+6 tests |
| `614bfbd5` | **shell Track B** — rail default + 30/70 + tablet drawer (8 files) | ✅ live · 146 shell tests |
| `86e939a0` | shell — checkpoint `idea→developing` + `dod_evidence` | docs |

`origin/main` intacto (no tocar). El branch avanza con sesiones concurrentes → `git log --oneline -8` al arrancar.

## ✅ DONE + green + live-verified (NO re-tocar)

### Inbox (commits 0dddae86 / aa5efa04 / fcd083de)
- **#5** ConversationItem: emoji map → `<ChannelBadge iconOnly>` (channel-meta SSoT, lucide + color). LIVE: WhatsApp green, Instagram pink.
- **#3** VoiceStyleChip: roto `/brand-studio/estilo` (404) → tenant-scoped `/{tenantId}/lisa/marca/voz-y-tono` (vía `useParams` en ThreadHeader). CTA se oculta sin href. LIVE: href correcto + ruta carga.
- **#7** ContactSidebar: "Servicio de interés" prominente arriba (cian + Stethoscope), wired `lead.service_interest` en AdrianInboxView + InboxPageClient. **Contrato real BE→FE confirmado** (no imaginado). LIVE: "Ortodoncia invisible".
- **#5b** `lead-stage-meta.ts` (SSoT) + `StageBadge` (Tailwind palette dark-aware): stage chips coloreados en list + sidebar. `data-testid` override conserva `stage-chip` (e2e POM). LIVE.
- **#8** FilterChips: channel chips con color de canal soft + `ring-current` pressed. LIVE.
- **#2/#1/#1b/#13** labels lucide + close X en el detalle + actividad clarity. LIVE.
- **#6** cursor-pointer: scan → no `<div onClick>` en inbox (clickables son button/li). No-op.

### Shell (commit 614bfbd5) — `vitalia-bugfix-shell-valeria-responsive`
- **Point 1** default `valeriaState: 'full' → 'rail'` (`src/stores/shell-store.ts`). Historial collapsed by default.
- **Point 2** `defaultValeriaPct: 50 → 30` (`ShellOrganismLayoutClient.tsx`). Agente 70%, sigue resizable + persistido. LIVE 1280: Valeria 381px (29.8%), **inbox thread 250px (era 56px)**.
- **Point 3** tablet (768–1024) = Valeria drawer, agente full-width. Breakpoint `md→lg` en ValeriaSidebar/TopBarGlobal/ShellOrganismLayoutClient/useViewportGuard. **Clave:** el Valeria Panel ahora es `collapsible collapsedSize={0}` + colapsa `< lg` vía `isLg` matchMedia (si no, el Group reservaba 30% vacío). ValeriaSidebar sigue montado → drawer portal funciona. LIVE 800: inbox 800px (full), burger abre drawer.
- Cross-tab OK (lisa/marca = Valeria 30%). 146 shell unit tests green.

## 🔜 LO QUE FALTA (para `done`) — leer esto

### A) Path to done (ambas stories)
1. **Chris demo** en dev-app (1280 / 1024 / 800) — tiene comentarios. **Hard-refresh obligatorio** (ver gotcha #1).
2. **/auditor** (con `<brand>: vitalia`) — debe re-verificar **inbox AC-4/5/7 + AC-12** (que Track B desbloquea: thread usable) + cross-tab shell regression-guard de stories shell ya done.
3. **/pm-vitalia merge** → `done` (ambas) + cap YAML (`adrian.inbox`) + SYSTEM-MAP del shell.
4. Re-verificar inbox AC-4/5/7 live tras el merge del shell (el thread ya es usable, ejercer mode toggle + composer real).

### B) Track A inbox — items NO hechos (decidir con Chris si entran a esta story o a follow-up)
- **#4/#12** composer-en-manual + mode toggle (3 modos). **DEFERIDOS por squeeze — AHORA el thread es usable (Track B), se pueden hacer.** `ComposerArea` `canSend = status==='active' && handler_mode==='ai'` deshabilita el composer en "yo escribo" (manual) → separar "agente piensa" (disabled) de "manual" (enabled). + investigar live el PATCH `/mode` (¿3er modo en el array?).
- **#9** burbujas por emisor (agent-color paciente/Adrián/humano) — `MessageBubble`. También deferido por squeeze, ahora hacible.
- **#10** timestamps en burbujas (patrón WhatsApp) — `MessageBubble`.
- **#11** filtros: fila-1 = solo canales, resto bajo "Más filtros" — `FilterChips` (restructure).
- **A–F** (adicionales auditoría): focus-visible consistente, jerarquía tipográfica, contraste status hues dark, lucide-only (KIND_ICONS de ActivityStream siguen emoji).
- SSoT del triaje: `UI-AUDIT-2026-06-04.md` (mismo folder).

## ⚠️ GOTCHAS CRÍTICOS (esto te va a morder — leer)

### #1 — Dev-app sirve código VIEJO tras editar (el más importante)
Turbopack dev emite **nombres de chunk ESTABLES** (`globals_0m9gcrk.css` no cambia aunque cambie el contenido) + el container es **inotify-ciego al bind-mount del host** → los edits SOLO compilan al **arrancar** el container, y el browser cachea los chunks de nombre-estable 4h. **Receta para ver tu código fresco en dev-app:**
```bash
cd ~/Proyectos/luana-vitalia
docker stop luana-dev-vitalia_frontend_dev-1
docker run --rm -v "$(pwd)/vitalia/frontend:/fe" alpine sh -c 'rm -rf /fe/.next'   # .next es root-owned → alpine
docker start luana-dev-vitalia_frontend_dev-1
# esperar "✓ Ready", luego en el browser: Empty Cache + Hard Reload (o Playwright reload ignoreCache)
```
**Sin esto, "no veo mi cambio" = cache, no bug.** (HB candidate: setear `WATCHPACK_POLLING=true` en el compose FE arreglaría el HMR — NO hacerlo mid-feature.)

### #2 — Chrome MCP murió, usar Playwright
El servidor Chrome MCP crasheó (`Browser.setContentsSize: Restore window to normal state`) y no volvió. Para live-verify: **Playwright spec desechable** importando `@playwright/test` DIRECTO (NO `e2e/fixtures/base.ts` — su gate anti-burbuja false-failea sobre el dev-tools `nextjs-portal` + el favicon 500 pre-existente). Patrón que funcionó:
```bash
cd vitalia/frontend
set -a; source ../.env.dev; set +a
export E2E_BASE_URL="https://dev-app.vitalialat.com"
npx playwright test e2e/shell-organism/_zz-tu-spec.smoke.spec.ts \
  --project=smoke --no-deps --workers=1 --reporter=line --timeout=120000
# --no-deps = reusa el storageState (playwright/.clerk/user.json) sin re-auth
# .toBeAttached() para items del thread-header (squeeze) · .toBeVisible() para list/sidebar
# clear localStorage keys /shell|panel|resizable|valeria/ + reload = probar FRESH defaults
# borrar el _zz-*.spec al terminar (no commitear)
```

### #3 — Hub compartido + arch reds que NO son tuyos
Una sesión concurrente está refactorizando los **allowlists de los arch tests FE** (`test_fsd_boundaries`/`test_no_cross_feature_imports`/`test_no_hardcoded_colors` están ` M` sin commitear, con paths viejos `features/inbox/`). Hay **3 arch reds que NO son de este trabajo**: `AdrianInboxView→crm-shared` (import pre-existente), `embudo/page→embudo-server` (sesión embudo), `FrozenLeadRow [diagnosis]` (recuperar). **NO tocar esos test files** (los owna la otra sesión). Se resuelven cuando ellos commiteen el refactor.

### #4 — Dato sembrado + persistencia
- Sembré `service_interest='Ortodoncia invisible'` en el lead de la conv `11111111-1111-5111-8111-111111111111` (dev DB) para ver el caso positivo de #7. Las 4 leads de Sanaré tenían `service_interest=NULL`.
- El `localStorage` persistido (`vitalia-shell-state` + layout react-resizable-panels) **pisa los defaults nuevos** → para probar Point 1+2 fresh hay que limpiar esas keys.

### #5 — Dark mode = OK (no es bug)
El "dark medio aplicado" que viste era el cache gotcha #1, NO código. `43c4c4df` (override de `--vitalia-*` bajo `[data-theme=dark]`) es correcto — verificado live con CSS fresco. Hard-refresh y se ve.

## Reglas duras (Chris)
- **DoD #37**: nada `done` sin live-verify (acción real + logs + efecto) + **demo sign-off de Chris**.
- **PARÁ antes de /auditor** — Chris prueba primero. NO encadenar /auditor ni merge sin su sign-off.
- Design-system: cargar skill `vitalia-design-system` ANTES de tocar UI. Tokens (globals.css), átomos, channel-meta, agent colors. NO hardcodear hex.
- Commit por pathspec + `STORY_CLOSURE_GATE_SKIP=1` (razón en body). NUNCA `git add .`.

## Estado de las 2 stories
- `vitalia-fase2-adrian-inbox`: `developing`. UI polish done+live; falta items B + AC-4/5/7 live (post Track B) + demo + auditor + merge. checkpoint § `ui_polish_dod_evidence_2026_06_04`.
- `vitalia-bugfix-shell-valeria-responsive`: `developing`. 3 puntos done+live (`dod_evidence` en checkpoint). `tablet_decision: drawer-en-tablet-split-1024`. Lock `code:shell` ya liberado.
