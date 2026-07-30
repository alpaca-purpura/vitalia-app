---
name: chrome-devtools-verify
description: "Live frontend verification via Chrome DevTools MCP (oficial Google, v0.21+). Use cuando: verificar bug fix UI en vivo SIN escribir spec.ts desechable, reproducir bug paso a paso con screenshots + console + DOM inspection, performance audit (LCP/INP/CLS), V8 heap snapshot, network requests live. Coexiste con playwright-expert (NO compiten: Chrome MCP = debugging conversacional, Playwright = automation tests CI). Triggers: 'verificá en el navegador', 'abrí chrome', 'pasame screenshot', 'reproducí el bug en vivo', 'inspect DOM', 'console log', 'performance trace', 'chrome-devtools-mcp', 'live verify UI fix'."
---
<!-- voseo-allowed: skill triggers + ejemplos diálogo Chris (voseo natural) por spanish-text.md exception R25 -->


# Chrome DevTools MCP — Live Frontend Verification (Linux Mint nativo)

> **Reinstantiated 2026-05-27** desde DEPRECATED status (era WSL2-only). Ahora cubre setup Linux Mint nativo + Chrome MCP v0.21+ oficial Google. Coexiste con `playwright-expert` sin conflict.

**Stack:** Linux Mint nativo + Node 20 LTS (nvm) + Chrome stable + npx chrome-devtools-mcp.

## When to use this skill (✅)

- Bug fix UI: verificar visualmente post-cambio sin escribir spec.ts formal
- Reproducir bug user-reported paso a paso (interactivo, screenshots intermedios)
- Inspect DOM live ("¿qué hay en este elemento?", "¿por qué este botón no se ve?")
- Console + network errors live (CORS, 401 Clerk, X-Tenant-ID missing, etc.)
- Performance audit ad-hoc (LCP/INP/CLS via Lighthouse + V8 heap snapshots)
- Memory leak hunt en streaming agents (Camila copilot Vitalia, etc.)
- Verificación rápida post-CSS-change antes de decidir si vale agregar smoke formal

## When NOT to use (❌ → playwright-expert)

- E2E smoke tests cementados en CI (`{brand}/frontend/e2e/specs/smoke/*.spec.ts`)
- Auth Clerk lifecycle automatizado (storageState freshness, retry+sanity, testing token)
- Regression tests versionados
- Sharding paralelo en CI
- Cross-browser testing (Chromium/Firefox/WebKit)
- Cualquier cosa que deba correr autoreproducible en CI

## Tabla decisión

| Caso de uso | Chrome MCP | Playwright |
|---|---|---|
| "Mostrame el screenshot de /agenda ahora" | ✅ | ❌ overkill |
| "Reproducí el bug paso a paso" | ✅ | ⚠️ posible pero más fricción |
| "Inspect DOM del header roto" | ✅ | ❌ |
| "Verificá hot-fix UI rápido" | ✅ | ❌ overkill |
| "Performance audit LCP/INP" | ✅ | ⚠️ posible pero verbose |
| Smoke test cementado CI | ❌ | ✅ |
| Regression test versionado | ❌ | ✅ |
| Auth Clerk lifecycle automation | ❌ | ✅ (`playwright-expert`) |
| Cross-browser (Safari iOS) | ❌ | ✅ |

## Setup (one-time, Linux Mint nativo)

### Verificación de requisitos

```bash
node --version              # ≥20 LTS (verificar nvm install 20 si falta)
which google-chrome || which google-chrome-stable
# Si falta Chrome: https://www.google.com/chrome/ (Mint maneja .deb directo via apt)
```

### Opción A — Comando one-liner (recomendado scope user para todos los proyectos)

```bash
claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest
```

### Opción B — Manual con flags Linux (recomendado para Mint con Wayland posible)

Editar `~/.claude.json` agregando bajo `mcpServers`:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "chrome-devtools-mcp@latest",
        "--isolated",
        "--no-usage-statistics",
        "--chromeArg=--no-first-run",
        "--chromeArg=--no-default-browser-check",
        "--chromeArg=--disable-search-engine-choice-screen"
      ],
      "env": {}
    }
  }
}
```

Si Mint corre Wayland (probable en sesiones modernas), agregar:
```json
"--chromeArg=--ozone-platform=wayland"
```

Si aparece "No usable sandbox!" (AppArmor restrictivo):
```bash
echo 'export CHROME_DEVEL_SANDBOX=/opt/google/chrome/chrome-sandbox' >> ~/.bashrc
source ~/.bashrc
```
o fallback:
```json
"--chromeArg=--no-sandbox"
```
(SOLO dev, NUNCA prod).

### Verificación post-setup

```bash
# Reiniciar Claude Code
claude mcp list                       # debe aparecer chrome-devtools
```

Dentro de sesión, pedir: *"navegá a http://localhost:3002 y dame screenshot + console messages"*. Si responde con imagen + logs → setup OK.

## Auth Clerk lifecycle (caso especial)

Chrome MCP por default usa `--isolated` (profile temporal, sin cookies). Para flujos auth Clerk donde necesitás sesión ya logueada, **NO usar `--isolated`** — attach a Chrome real con remote debugging:

```bash
# Terminal separada: Chrome con debugging port + user-data-dir dedicado
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-mcp-debug &

# Loguearte UNA VEZ manualmente en http://localhost:3002 (o 3001/3003/3004 según brand)
```

Luego en Claude pedile que use Chrome MCP con `--browser-url=http://127.0.0.1:9222`. Opcional: agregar segunda config nombrada en `~/.claude.json` (ej. `chrome-devtools-attached`).

## Use cases ejemplo

### Caso 1: Verificar bug fix UI en Vitalia
```
Chris: "fijate si el header de /agenda/nueva sigue roto post fix"
Claude: usa chrome-devtools mcp:
  - navigate a http://localhost:3002/agenda/nueva
  - take_screenshot (full page)
  - inspect header element
  - report visual + DOM state
```

### Caso 2: Reproducir bug Camila no responde
```
Chris: "Camila no responde después del 2do mensaje"
Claude: chrome-devtools mcp:
  - navigate a /copilot
  - type message 1, submit
  - take_screenshot post respuesta 1
  - type message 2, submit
  - capture network requests + console messages
  - report dónde quiebra
```

### Caso 3: Performance audit pre-merge
```
Chris: "antes de mergear, audita /agenda/[id]/edit performance"
Claude: chrome-devtools mcp:
  - performance_trace start
  - navigate + interact con form
  - performance_trace stop
  - performance_analyze_insight (LCP / INP / CLS)
  - report top 3 issues + recomendaciones
```

## Tools disponibles (41 total, agrupadas)

| Categoría | Tools clave |
|---|---|
| **Input automation** | click, drag, fill, fill_form, hover, press_key, type_text, upload_file, click_at, handle_dialog |
| **Navigation** | new_page, navigate_page, list_pages, select_page, close_page, wait_for |
| **Debugging** | evaluate_script, take_screenshot, take_snapshot, list_console_messages, get_console_message, lighthouse_audit, screencast_start/stop |
| **Network** | list_network_requests, get_network_request (con bodies) |
| **Performance** | start/stop_trace, performance_analyze_insight |
| **Memory** | V8 heap snapshots (class nodes, retainers, summary) |
| **Emulation** | emulate (device/network), resize_page |
| **Extensions** | install/list/reload/trigger/uninstall extensions |

Detalle completo: `https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/tool-reference.md`

## ★ Footgun — `click()` sintético no dispara `onClick` de React (HB-101)

El `click()` del MCP es un evento sintético que **NO dispara el handler `onClick` de React** en botones con `onClick` puro (vistos en vitalia: `FreeDoctorsList`, "Crear paciente", "Crear cita"): el click "funciona" (sin error, sin Network, sin nada) pero no hay POST → se pierden turnos creyendo que es un bug de la app cuando es el harness de testing. Los pickers/combobox de **Radix** SÍ responden al `click()` del MCP; los botones con `onClick` puro NO.

**Workaround verificado** — `evaluate_script` con `el.click()` nativo SÍ dispara React:

```js
// evaluate_script
const btn = [...document.querySelectorAll('button')].find(b => b.textContent.includes('Crear cita'));
btn?.click();   // click nativo → el onClick de React dispara
```

Heurística: si un click "no hace nada" (sin error, sin request en Network), sospechá esto ANTES de declarar bug de la app.

## Anti-patterns prohibidos

- ❌ Spammear `take_screenshot` cada turn (cada screenshot consume context — usar con criterio)
- ❌ Usar `--isolated` cuando necesitás auth Clerk (no carga cookies — usa attach mode)
- ❌ Reemplazar smoke Playwright con Chrome MCP en CI (Chrome MCP NO es para CI — Playwright sí)
- ❌ Performance trace en producción (puede impactar UX real users — solo local dev)
- ❌ Asumir que `--no-sandbox` es OK en prod (NUNCA — sólo dev local)
- ❌ Tocar componentes shared/ vía Chrome MCP "para arreglar bug visual rápido" sin escalate (rompe `playwright_visual_scope` de la story per `.claude/rules/architect-autonomous-mode.md`)
- ❌ Declarar "el botón no funciona / hay un bug" cuando el MCP `click()` no disparó un `onClick` puro de React — probá `evaluate_script` con `el.click()` nativo PRIMERO (ver § Footgun · HB-101)

## DoD Live Verification Gate (Critical Rule #37)

Cuando uso Chrome DevTools MCP para **cerrar la verificación live de una story** (no solo debugging ad-hoc), el resultado alimenta el **gate DoD #37** (`.claude/rules/definition-of-done-live-verify.md`): ninguna story user-reachable llega a `done` sin que la acción real se ejerza en el stack corriendo. Obligaciones:
- Ejercer la **acción real del usuario** (sobre todo writes: crear/editar/guardar/eliminar) — NUNCA un `GET 200` sobre un placeholder.
- Leer el panel **Console** (0 errores rojos = burbuja Next / hidratación) + **Network** (sin 4xx/5xx en `/api/`) + confirmar el **efecto** (toast OK, fila aparece, valor persiste al recargar) + logs del backend sin traceback.
- Registrar evidencia en `checkpoint.md::dod_evidence` (action + observed + backend_log). Verde de gates ≠ verificado.

Dev-app por marca: `make dev-app-{brand}` (o `localhost:300X` fallback). Tabla SSoT + usuario de prueba: `definition-of-done-live-verify.md § Infra por brand`.

★ **Lane sin sesión Clerk (HB-89):** antes de ejercer writes autenticados en una lane que NO es el Chrome personal de Chris, correr `make lane-auth-<brand>` una vez por lane (re-correr si >4h). Sin esto el perfil MCP de la lane (`~/.cache/chrome-devtools-mcp/luana-<brand>-$LUANA_LANE`) no tiene sesión Clerk → los writes redirigen a `/sign-in` y la live-verify falla en falso. El target siembra el perfil con la MISMA sesión @clerk/testing que usa el harness e2e (cerrá la MCP Chrome de esa lane antes de sembrar — el perfil no puede estar lockeado).

## Coexistencia con playwright-expert

- **Chrome MCP** = debugging interactivo + verificación ad-hoc + performance live
- **Playwright** (`playwright-expert` skill) = tests automatizados + CI + auth Clerk lifecycle + cross-browser

Profiles separados (Chrome MCP usa `--isolated` o user-data-dir custom; Playwright usa `{brand}/frontend/playwright/.clerk/`). NO se pisan.

## Referencias

- [Chrome DevTools MCP repo oficial](https://github.com/ChromeDevTools/chrome-devtools-mcp)
- [Chrome DevTools (MCP) for your AI agent — Chrome Developers Blog](https://developer.chrome.com/blog/chrome-devtools-mcp)
- [Tool reference (41 tools full)](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/tool-reference.md)
- [Playwright vs Chrome DevTools MCP: Driving vs Debugging — Steve Kinney](https://stevekinney.com/writing/driving-vs-debugging-the-browser)
- [Setting up Chrome DevTools MCP with Claude Code on Linux (Wayland)](https://alexanderzeitler.com/articles/chrome-devtools-mcp-with-claude-code-on-linux-wayland/)
- `.claude/rules/definition-of-done-live-verify.md` — DoD live-verify gate (#37) que esta verificación alimenta (Chrome MCP = live; Playwright = golden persistido)
- `.claude/skills/playwright-expert/SKILL.md` — counterpart para tests automatizados
- `.claude/rules/architect-autonomous-mode.md` — `playwright_visual_scope` discipline (aplica también cuando uso Chrome MCP para verificar)
