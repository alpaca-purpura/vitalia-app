# Harness refactor program (2026-06-08 → 2026-06-09) — learnings de cierre (CIL L2)

> Programa W0→W10 COMPLETO. SSoT del programa: `docs/process/harness-refactor-charter-2026-06-08.md` §6 + `harness-refactor-w{n}/W{n}-OUTPUT.md`. Acá solo los learnings durables (carril L2).

## Los 8 durables de la fase B (W1→W8) — confirmados de punta a punta

1. **VERIFICAR > memoria** — date-aware; correr el gate; verificar el CONSUMIDOR, no la auto-descripción del productor.
2. **VALIDATE-después-de-aplicar** — el body de una rule/skill/template puede ser load-bearing string de `validate_machinery_consistency.py`; verde-prosa ≠ verde-gate.
3. **PATH-STABILITY es el super-power** — symlink/copy mantienen el path consumer-visible → blast radius colapsa al source (W7: 0 repoints de 29 paths asserted).
4. **`git mv` de un file editado-en-working-tree** stagea el blob ORIGINAL; verificar `git show :<path>`.
5. **`tier:core` se GANA por proxy-grep**, no por intención (rules 18→21 · skills 0 · agents 1 · hooks 5).
6. **PROPAGACIÓN-GREP** — al mover una doctrina, grepear el consumidor por el token VIEJO; el SSoT nunca se propaga solo.
7. **Self-docs del kit describen el SEAM genéricamente** — el ejemplo negativo ES un token.
8. **"Purged" es scope-qualified** — verificar QUÉ capa retiró el concepto antes de borrar un trigger vivo.

## Nuevos de la sesión de cierre (W9/W10 + colas)

9. **El restart-smoke se prueba PASIVAMENTE en la siguiente sesión fresca** — no hace falta un harness de prueba: el system-reminder de inicio de la sesión siguiente ES la evidencia de qué cargó always-on (las 21 rules symlinkeadas llegaron con cuerpo completo → Option-C confirmado).
10. **`claude -p` headless = banco de pruebas A/B para mecanismos de carga de CC.** Una rule creada mid-sesión es inobservable en la sesión actual (snapshot al inicio); una sesión headless fresca con sondas de evidencia-citada (canary + control positivo + control de confound) resuelve en minutos lo que el issue-tracker (#16299) dejó abierto meses. Patrón: canary `paths:` + control sin-`paths:` igualmente-untracked + control always-on conocido + sonda POSTREAD con `--allowedTools Read`.
11. **`globs:` frontmatter es mecanismo MUERTO; `paths:` está VIVO** (2026-06-09): rules con `globs:` cargaban always-on igual (3 casos reales); convertidas a `paths:` dejan de cargar por default e inyectan post-Read de path que matchea. Caveat #23478 vigente: no dispara en write puro → solo convention-rules.
12. **Un sync-check LSP paga su costo el día 1** — CHECK 30 (template↔instancias PM) cazó en su PRIMER run que `pm-comunify`/`pm-lupulo` nunca recibieron la § Auto-chain rule cementada 2 semanas antes. La replicación manual de doctrina a N instancias SIEMPRE deja una atrás; el check concept-based es la única red real.
13. **El DoD de extracción debe ser un invariante mecánico, no una medición de sesión** — CHECK 29 (proxy-clean en cada commit) convierte el "cheap W8" en gate permanente: el kit no puede volver a contaminarse silenciosamente.
14. **Eviction sin pérdida = overlap-check primero** — antes de shrinkear un stub always-on a pointer, medir solapamiento body↔references (acá fue ~0: los stubs eran COMPLEMENTO, no duplicado → mover verbatim, no borrar).
