---
name: harness-issue
description: "Captura sin fricción de una deficiencia del harness (skill/rule/hook/agent/cockpit/template/doc de proceso) al backlog docs/process/harness-backlog.md, SIN frenar el trabajo de producto en curso. Usá cuando notes algo roto, stale, contradictorio, duplicado o confuso en las herramientas internas y quieras anotarlo para arreglarlo después en lote. NO arregla nada — solo captura. Triggers: '/harness-issue', 'anotá al harness backlog', 'harness backlog', 'esta skill está rota', 'esta rule contradice', 'el harness tiene un problema', 'anotá esto del harness'."
allowed-tools: Read, Edit, Bash
model: haiku
---

# /harness-issue — captura al harness backlog

Appendeá UNA fila a `docs/process/harness-backlog.md` y nada más. Sos un capturador, no un fixer.

## Pasos

1. Tomá la descripción del item de `$ARGUMENTS` (o de lo que el usuario acabe de señalar).
2. Inferí la **severidad**:
   - 🔴 **silent-killer** — rompe funcionalidad sin error visible (skill no registra, hook muerto, gate que no corre).
   - 🟡 **quick-win** — fix mecánico (typo, path stale, model ID viejo, brand name).
   - 🔵 **decision** — requiere criterio de Chris (retirar algo, política, trade-off).
   - 🟣 **wave** — cambio grande/estructural (refactor masivo, feature nueva del harness).
   - Si no podés inferirla con confianza, **preguntá** antes de escribir.
3. Calculá el próximo `id` (HB-N) leyendo el último del backlog. Fecha = `date -u +%Y-%m-%d`.
4. Appendeá la fila a la tabla con estado `reported`:
   `| HB-N | <fecha> | <sev> | <descripción concisa> | reported | <ref opcional> |`
5. Confirmá en UNA línea: `capturado -> HB-N (<sev>)`. NO propongas el fix, NO edites el archivo afectado.

## Reglas

- NUNCA arregles el item acá (separación de concerns — el fix va en lote/sesión dedicada, ver `docs/process/harness-lifecycle.md`).
- NUNCA `git add .` ni commits (la captura es solo el append; el commit del backlog va con el resto del trabajo).
- Si el item es 🔴 silent-killer, además de capturar, avisá explícito a Chris que conviene fix inmediato (excepción de la regla de oro).
