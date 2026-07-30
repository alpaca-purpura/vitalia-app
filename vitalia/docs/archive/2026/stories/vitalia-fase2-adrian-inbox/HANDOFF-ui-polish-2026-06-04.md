# HANDOFF — Adrián Inbox UI polish (5 rondas de comentarios de Chris)

> **Escrito 2026-06-04.** Branch `wip/vitalia`, worktree hub `~/Proyectos/luana-vitalia`. Story `vitalia-fase2-adrian-inbox` sigue **`developing`** (NO done). Esta sesión aplicó **5 rondas** de comentarios UI de Chris al inbox, todas live-verified (dev-app, light+dark) + pusheadas. Falta: **demo/sign-off de Chris → /auditor (vitalia) → /pm-vitalia merge → done.**
>
> **HUB COMPARTIDO** con sesiones concurrentes (embudo + refactor arch-tests). Commit SIEMPRE por pathspec, NUNCA `git add .`/`-A`. `STORY_CLOSURE_GATE_SKIP=1` (razón en body; embudo hermano está `developed`).

## Commit chain de esta sesión (wip/vitalia, todos pusheados, en orden)

| SHA | Ronda | Qué |
|---|---|---|
| `f7f0949b` | 1 | auto-select last-viewed→newest + empty-state rico (icono+skeleton) + selección visible + timestamps + burbujas legibles dark + wire MessageBubble real (antes scaffold) |
| `2de2afab` | 2 | SSoT logos reales + turn-labels + filtro 1-línea + avatar_url terreno + wallpaper v1 |
| `9aedd1d6` | 2-fix | **los 2 archivos NUEVOS del SSoT** (`git commit <pathspec>` los SALTÓ — gotcha #5) |
| `f75084cd` | 2.5 | wallpaper v2 — por red social (tinte + watermark logo real) |
| `b1255842` | 3 | burbujas color-de-red + watermark más tenue + turn-pills con fondo |
| `9b01d6aa` | 4 | sombra burbujas + nombre seleccionado foreground + watermark 1.5% + TikTok/Telegram/Facebook |
| `a64ed3f0` | 5 | read-receipts ✓/✓✓ + burbuja saliente 14% + auto-colapsar contacto en angosto |

`origin/main` intacto. `git log --oneline -8` al arrancar (avanza con sesiones concurrentes).

## ✅ DONE + live-verified (NO re-hacer) — qué se construyó

**Lista de conversaciones** (`ConversationItem.tsx`, `ConversationListPanel.tsx`, `FilterChips.tsx`):
- Auto-select: re-abre la última conv vista (`lib/last-viewed-conv.ts`, localStorage UUID no-PHI) o la más nueva (SSR `initialData` + client). Empty real (0 convs) = `InboxEmptyPanel` (icono lucide + mensaje + skeleton) en thread Y contacto.
- Card seleccionada: fondo del **color de la red** (color-mix 12%) + rail de marca + nombre **foreground** (negro/blanco, combina con cualquier red). Sin ícono de canal a la izquierda.
- Logo REAL de la red abajo-derecha (a la altura del estado).
- Filtro: **una línea horizontal scrolleable** [Todas][WhatsApp][Instagram][Telegram][TikTok][Facebook][Email] con logos reales + "Más filtros" (flags/etapa/modo/período). Status REMOVIDO.

**Thread** (`InboxThread.tsx`, `MessageBubble.tsx`, `ThreadHeader.tsx`):
- `MessageBubble` real cableado (antes scaffold plomo). Orientación WhatsApp: paciente IZQ surface, Adrián/humano DER.
- Burbujas SÓLIDAS con sombra (`shadow-sm`) → despegan del fondo. Saliente = **color de la red** (color-mix 14% sobre `--vt-bubble-base`, opaco), paciente = surface blanco.
- **Read-receipts** ✓/✓✓ en salientes (`Message.delivery_status`, default `sent`=✓).
- Timestamps HH:mm por burbuja + separadores de día (Hoy/Ayer/fecha).
- **Turn-labels** en pill con fondo: "Adrián · Auto" (cian) / "Tú · Manual" (azul) / nombre paciente. Reemplazan los avatares A/H per-burbuja (ganan ancho).
- **Fondo POR RED SOCIAL**: tinte del color (4%) + watermark del logo real tileado (opacity 1.5%, muy tenue). WhatsApp=verde, IG=rosa, etc. Genéricos (email/web) = solo tinte.
- ThreadHeader: avatar (`<img avatar_url>` si existe, si no monograma) + nombre + logo real de la red.
- **Auto-colapsar contacto** cuando el agent-panel <960px (ResizeObserver en `inbox-desktop`) → el header del thread gana aire. Solo colapsa, nunca auto-abre (respeta toggle "Perfil").

**SSoT NUEVO** (lift candidate a `core/@luana`): `src/lib/channels/social-channels.ts` (logos reales simple-icons + colores via `var(--channel-*-bg)`) + `src/components/shared/channels/SocialLogo.tsx`. Reusable para badges/filtros/futuras conexiones.

**globals.css** (clases nuevas, exento de arch-test): `.vt-bg-adrian-soft`, `.vt-bg-chat-wash`, `:root --vt-bubble-base`.

## ⚠️ GOTCHAS CRÍTICOS (te van a morder)

1. **Dev-app sirve código VIEJO tras editar** (Turbopack chunks nombre estable + container inotify-ciego). Para ver fresco:
   ```bash
   cd ~/Proyectos/luana-vitalia
   docker stop luana-dev-vitalia_frontend_dev-1
   docker run --rm -v "$(pwd)/vitalia/frontend:/fe" alpine sh -c 'rm -rf /fe/.next'
   docker start luana-dev-vitalia_frontend_dev-1; sleep 6
   ```
   Browser de Chris: **Empty-Cache + Hard-Reload**. **El "logo Vitalia desapareció" de Chris = ESTE cache** (investigado: logo intacto, assets 200, presente light+dark). NO es bug.

2. **Chrome MCP murió** → live-verify con **Playwright desechable** importando `@playwright/test` DIRECTO (NO `e2e/fixtures/base.ts` — su anti-burbuja false-failea). Receta:
   ```bash
   cd vitalia/frontend && set -a; source ../.env.dev; set +a
   export E2E_BASE_URL="https://dev-app.vitalialat.com"
   npx playwright test e2e/shell-organism/_zz-X.smoke.spec.ts --project=smoke --no-deps --workers=1 --reporter=line --timeout=160000
   # borrar el _zz-*.spec al terminar (no commitear)
   ```
   Dark: setear **AMBOS** `localStorage.theme` Y `localStorage["vitalia-theme"]` = "dark" (la storageKey real es `vitalia-theme`). Limpiar `lastConv|inbox|conv` para probar auto-select fresh. Tenant `e69a691d-070e-5caf-a053-6e74642ec100`. Ruta `/{tenantId}/adrian/inbox`.

3. **Hub compartido** → commit por pathspec con `STORY_CLOSURE_GATE_SKIP=1`. Hay **2 arch reds PRE-EXISTENTES NO míos** (`AdrianInboxView→crm-shared` import + `embudo/page→embudo-server`) que owna la sesión de arch-refactor — `test_fsd_boundaries`/`test_no_cross_feature_imports`/`test_no_hardcoded_colors`/`agent-catalog.test` están ` M` sin commitear: **NO los toques ni los commitees**.

4. **Arch-test `no-hardcoded-colors` (FE-A1)**: PROHIBIDO hex/`rgb(`/`hsl(` literal en `.ts`/`.tsx`. Usá clases utilitarias de globals.css o `color-mix(in srgb, var(--token) N%, var(--otro))`. **Correlo SIEMPRE antes de commitear UI**: `npx vitest run src/__tests__/architecture/test_no_hardcoded_colors.test.ts`. (Me mordió 2 veces.)

5. **Haiku git worker** con `git commit <pathspec>` **SALTA archivos NUEVOS untracked** → para archivos nuevos hacé `git add <ruta-exacta>` ANTES del commit (caso `9aedd1d6`).

## 🔜 PATH TO DONE (DoD #37 — regla dura)
1. **Chris prueba en dev-app** (hard-refresh) + da sign-off. **NO encadenar /auditor sin su sign-off.**
2. `/auditor` con `<brand>: vitalia` (re-verifica inbox AC-4/5/7/12 + cat 9 fidelidad visual + 13 anti-dup).
3. `/pm-vitalia` merge → `done` + cap YAML `adrian.inbox` + `git mv` story a `archive/`.

**Follow-ups abiertos (no bloquean estética):**
- BE: poblar `Lead.avatar_url` + `Message.delivery_status` (terreno FE listo, default monograma/✓).
- SSoT social-channels → lift a `core/@luana` vía `/pm-luana` cuando ≥2 brands.
- Header del thread en angosto: ya mitigado con auto-colapso; si Chris quiere más, auto-colapsar también en tablet.

## Gates (todas las rondas)
tsc 0 · eslint 0 · **vitest 208/208** · arch `no-hardcoded-colors` 2/2. Live-verified light+dark, 0 console errors.

## Lock
Lock `code:adrian` adquirido esta sesión (`scripts/git/session-lock.sh acquire code:adrian`). Liberar al cerrar si aplica.

## SSoT del estado
- `checkpoint.md` § `ui_polish_dod_evidence_2026_06_04_pm{2,3,4,5,6}` — evidencia por ronda.
- Este handoff.
