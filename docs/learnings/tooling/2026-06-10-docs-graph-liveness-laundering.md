# Grafo de consumo de docs: 3 fuentes de "liveness laundering" (y sus fixes)

**Fecha:** 2026-06-10 · **Carril CIL:** L2 (tooling transversal) · **Origen:** sesión DOCS-SWEEP (scan_docs_graph.py + barrido 158 files a legacy/)

## Problema

Primer pase del grafo de consumo de root `docs/`: **947/947 vivos, 0 huérfanos** — obviamente falso. Tres mecanismos inflaban la vida:

1. **Substring brand-path:** el regex `docs/...` matcheaba DENTRO de `vitalia/docs/product/stories/` → paths brand-scoped contaban como refs a root docs. Fix: lookbehind `(?<![\w/.-])docs/`.
2. **Dir-edges desde docs:** un doc vivo que menciona un dir al pasar (`docs/process/` en prosa) revivía TODO su contenido (fan-outs >1000 desde un solo doc). Fix: dir-edges cuentan SOLO desde superficies vivas (skills/scripts/hooks), nunca docs↔docs.
3. **Glob que cruza `/`:** `fnmatch` traduce `*` a `.*` → `docs/learnings/*-*.md` matcheaba subdirs enteros. Fix: glob path-aware (`*` = `[^/]*`).

Con los 3 fixes: 947 → 910 → veredictos honestos (37 huérfanos reales + clases por strength).

## Reglas durables

- **strength = peor link del camino** (file > glob > dir): un doc "vivo" solo porque alguien nombra su directorio NO es lo mismo que uno citado por path exacto. El sweep juzga por strength, no por vivo/muerto binario.
- **Dir-ref genérico ≠ consumidor** (`docs/process/` pelado en un skill); **dir-ref específico SÍ** cuando el dir es corpus de lectura runtime (ej. `docs/archive/.../snapshot-pre-multibrand-pm-redesign/` que los PM-skills grepean como prior-art).
- **Excluir los outputs del scanner del corpus Y de las fuentes** (DOCS-GRAPH.md cita todos los paths → revive huérfanos circularmente). Ídem el propio scanner + su test (fixtures con paths literales).
- **Gotcha gitignored-pointer:** citar con backticks un artifact gitignored (`docs/process/DOCS-GRAPH.md`) desde un skill pasa el pointer-scan en el árbol donde el generator corrió y ROMPE en main (file ausente). Refs a auto-gen gitignored van SIN backticks (el pointer-scan solo parsea backticked) o apuntan al comando que lo genera.

## Relacionado

- `scripts/scan_docs_graph.py` + `scripts/tests/test_scan_docs_graph.py` — la herramienta
- `legacy/2026-06-10-docs-sweep/INVENTORY.md` — el barrido ejecutado
- `docs/learnings/tooling/2026-06-09-sourced-check-andlist-errexit.md` — smoke negativo del check 19
