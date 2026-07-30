# Paper-rule vs wired-enforcement — por qué Rule #37 (live-verify) no se cumple

- **Fecha:** 2026-06-03
- **Tipo:** tooling / harness (cross-brand)
- **Origen:** diagnóstico `/pm-luana` 2026-06-03. Chris reportó que historias UI llegan al auditor sin E2E live sobre `dev-app.vitalialat.com`, que el auditor tampoco lo caza, y que el mecanismo de mejora del harness "no está presente" (lo descubre él a mano).
- **Refs:** `.claude/rules/definition-of-done-live-verify.md` (Critical Rule #37) · harness-backlog HB-38..41

## Qué pasó

Dos historias UI de vitalia (adrian-embudo, adrian-inbox) avanzaron sin la verificación live obligatoria de la DoD #37:
- **adrian-inbox** fue marcada `developed` **en falso** por el build autónomo. La cazó un SELF-REVIEW ad-hoc (`SELF-REVIEW-compliance.md`: "NO está listo para `/auditor`"), no un gate. Su matriz: 10/10 Gherkin SC = MISSING e2e real; AC-3 roto (endpoint compound nunca cableado).
- **adrian-embudo** quedó en `developing` con solo BE live-smoke (endpoints reachable, GET 422/200), sin `dod_evidence` ni `demo_signoff`.

Conclusión: el sistema dependió de un self-review manual + el ojo de Chris, **no de un gate**.

## Root cause

Una rule escrita en `.claude/rules/` **no se cumple por existir**. Se cumple cuando se dan las TRES condiciones a la vez:

1. su instrucción está **embebida como paso duro** en el skill que la ejecuta (no "recomendado"),
2. hay un **gate en el límite `developed`/`reviewing`** (no solo en el merge final), y
3. el verificador independiente (auditor) la **ejerce** (≥1 write live), no la confía al self-report.

Rule #37 tenía las tres como ⏳ PENDING (enforcement layers 2/8/9). Resultado: el único gate real vivía en `pm-{brand}` Fase F (merge) — demasiado tarde, y saltable porque las stories ni llegaban ahí.

### Los 3 huecos (uno por rol) + el 4º meta

- **architect** declara `verification_nature`/`demo_required` (bien) pero la orden "UI → dev-team DEBE live-E2E + `dod_evidence`" está como "Uso (recomendado)" dirigida a sí mismo; `playwright_visual_scope` vive solo en references, no en `04-validators-template.yaml`; el `assignment` FE no fuerza `chrome-devtools-verify`.
- **dev-team** lista la live-verify como "obligación" en la sección DoD-endurecida, pero el Step 5 (`developing→developed`) solo chequea validators-green + gherkin-local-coverage. "NO cerrar por tests verdes mockeados" es texto, no código.
- **auditor** declara los checks de Phase D en `SKILL.md`, pero los agentes `auditor-frontend.md`/`auditor-backend.md` no tienen auto-FAIL `LIVE_VERIFY_MISSING`, no corren Chrome MCP, y la self-fix policy no lo empodera a hacerse cargo ni a responsabilizar al architect (root cause upstream).
- **meta:** no existe un reflex que, al detectar un gate saltado, capture HB+learning automáticamente. El loop de mejora del harness depende de que Chris lo note.

## La lección durable

- **"Paper rule"** = rule cuyo texto existe pero cuyos enforcement layers están PENDING. Test rápido: si la tabla de enforcement de una rule tiene filas ⏳, la rule **no está viva** — alguien la va a saltar sin error.
- Un gate de calidad debe vivir en el **límite donde el trabajo cambia de manos** (developed→reviewing), no solo en el merge final.
- El verificador independiente **ejerce** la acción crítica (write real + leer logs + confirmar efecto). Firmar sobre evidencia self-reported no es auditar.
- El loop de mejora del harness necesita un **reflex**: el que detecta el gate saltado captura el HB+learning en el momento.

## Cómo aplicar (cableado propuesto — ratificación Chris pendiente)

1. **architect**: paso duro — para `verification_nature ∈ {funcional, ambas}`, todo ticket FE/endpoint-con-consumer-FE lleva en `assignment.must_load_skills` `chrome-devtools-verify` (+`playwright-expert` si visual) y exit-criterion "live-verify dev-app + `dod_evidence`". Portar `playwright_visual_scope` al template.
2. **dev-team Step 5**: gate duro espejo del gherkin-Phase-D-local — REFUSE `developing→developed` si `demo_required: true`/`verification_nature` funcional y falta `dod_live_verified: true` + `dod_evidence` (≥1 write ejercido) + `demo-script.md`.
3. **auditor**: auto-FAIL `LIVE_VERIFY_MISSING` en verdict math de `auditor-frontend/backend.md`; ejercer ≥1 write crítico live; cuando el root cause es upstream → finding `## Upstream deficiency` nombrando el artefacto del architect + auto-capturar HB (reflex).
4. **reflex global**: regla "gate-skip detection → MUST append HB + learning antes de cerrar turn", cableada en auditor.
