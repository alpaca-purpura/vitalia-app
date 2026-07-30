# Proceso v5 — Coherencia spec→done (DISEÑO · ✅ BUILT 2026-06-05)

> **Estado:** ✅ **IMPLEMENTADO** (ver §10 · 5 waves, commits `21c141e3`→W5, CHECK 12-27). Registro único del rediseño. **Owner:** Chris + `/pm-luana`. **Fecha:** 2026-06-05. **Origen:** sesión harness-polish (Chris paró el dev para pulir el harness con el aprendizaje actual). **Naturaleza:** anti-Frankenstein — **re-secuencia + formaliza + hace-vivo** maquinaria existente; un solo artefacto nuevo (CIL) que **consolida** dispersión. **Backlog:** HB-52 · HB-53 · HB-54.
>
> **Al aplicarse, este diseño se PLIEGA a** `lifecycle.md` · `.claude/rules/story-closure-gate.md`(+detalle) · `.claude/rules/definition-of-done-live-verify.md` (#37) · `capability-protocol.md` · skills `{dev-team, auditor, pm-{brand}, architect, po-ux}` · `04-validators` template · `harness-backlog.md`→CIL · cockpit. Después queda como **registro de diseño** (igual que `pm-redesign-2026-05.md`). **No introduce un eje nuevo** al modelo 4-ejes (shrink-only de `lifecycle.md` se respeta).

---

## 1 · El problema (7 dolores · anclados en el caso inbox)

`vitalia-fase2-adrian-inbox` los probó todos: "developed+verde" era falso (crasheaba live → volvió a developing); el architect dijo "BE ya shippeó" = parcialmente falso (stubs `[]`/404); ~8-9 rounds de Chris para subsanar; reconciliación de docs hecha a mano (`scope_amendment`); una historia entera faltante descubierta tarde; **cero** learnings.md; HB-50 (200 sin commit) lo tapó la UI optimista.

| # | Dolor | Fix (pieza) |
|---|---|---|
| 1 | Coherencia spec→done rota / fantasmas en docs | §5.1 verify-first + §5.4 reconcile |
| 2 | Historias gigantes dejan funcionalidad sin construir | §5.2 ledger + §5.3 scope dinámico |
| 3 | No sé QUÉ quedó sin implementar | §5.2 ledger vivo (columna deferred visible) |
| 4 | Say-do gap (mis correcciones deben entrar) | §5.3 G + §5.4 reconcile |
| 5 | No hay dónde se acumulen los aprendizajes | §5.7 CIL + stop semanal |
| 6 | Probar yo post-dev, pre-auditor, con docs al día | §5.3 G (re-secuencia el demo gate) + §5.4 R |
| 7 | Auditor literalista revierte lo que pedí | §5.5 auditor guardián lee reconciliado |

---

## 2 · Principios (la vara)

1. **Verify-first es ley** — ninguna afirmación (en docs, backlog, checkpoint, cap) se da por cierta sin chequear el FS/código. La auditoría SOBREESTIMA (HLP §6.1).
2. **Verificación REAL ≠ 200** — verificar = ejercer la acción real (writes) + leer logs + confirmar efecto. Mocks sobre mocks = falso verde (rule #37 + test-design-doctrine).
3. **El piso del scope es el happy path** — funcionalidad nueva no llega a `done` sin su core/flujo completo construido. Las ramas se difieren **visibles**, nunca como gaps mudos.
4. **Re-secuenciar antes que agregar** — cada mejora reusa un slot existente; agregar un mecanismo nuevo exige matar/consolidar otro.
5. **Los docs == la realidad antes del auditor** — el auditor es guardián de arquitectura sobre la verdad reconciliada, no juez de un spec stale.

---

## 3 · El flujo completo (spine)

```
idea → refining → refined → ready → developing → developed
  │  po-ux 2-rondas: § Mapa funcional + § Matriz de cobertura  (= SEED del ledger vivo)
  │  architect: 03-arch con CONTRATO REAL BE↔FE + verification_nature por cap
  │            + superficies mutation-críticas marcadas + 04-validators(technical_gates) + 06-tickets
  │  dev-team: TDD red→green→refactor
  ▼
developed  ── BOUNDARY DURO ──────────────────────────────────────────────
  │  validators GREEN + dod_evidence + demo-script.md
  │  + ★ MUTATION GATE diff-scoped en superficies críticas (HB-54)
  │
  ├─ autonomous_mode: true ───────────────────────────────────► corre a done
  │
  ▼ (default = pausa-y-ofrece)
★ G · CHRIS-VERIFY LOOP        (state:developed · phase:AWAIT_CHRIS_VERIFY)
  │  dev-team te entrega el KIT (demo-script + dev-app live + LEDGER built/→story/⏳now)
  │  ejercés live → anotás correcciones/observaciones (incl. lo que recién se ve andando)
  │  scope dinámico: fuera-de-scope → implementar-ahora (corto+necesario) | spawn historia(s) acá
  │  PISO HARD: funcionalidad nueva → core/happy-path construido sí o sí
  │  iterate dev ⇄ Chris → "satisfecho" = chris_verify_signoff
  ▼
★ R · RECONCILE  (/pm-{brand})  — 01-spec/03-arch/04-validators/cap ⟵ realidad + cambios ratificados
  │  el ledger congela qué entró (✅) y qué quedó DEFERRED (→ historia(s) nueva(s) visibles)
  ▼
reviewing  (/auditor — guardián de arquitectura)
  │  lee docs RECONCILIADOS + chris_verify_signoff → NO revierte scope que Chris ratificó
  │  Phase D gherkin-matrix · verifica mutation gate · ejerce ≥1 write live
  │  CHANGES_REQUESTED → fix-loop (incl. survivors del mutation gate)
  ▼
done  (/pm-{brand} merge — 07-merge + cap promovida [§5.8 qué-hago, no versión] + archive)
  ▼
★ L · story-closure RUTEA aprendizajes → CIL (4 carriles)  →  stop semanal /mejora-semanal
```

---

## 4 · Las piezas

### 5.1 · Verify-first como ley   `[REUSE — ya es HLP §6.1; se eleva a principio cross-proceso]`
Toda skill que afirme estado (pm/architect/dev-team/auditor) chequea contra el FS antes de escribirlo. Overestimates se registran (señal de calidad). **Mata:** docs/backlog que afirman cosas que no existen (esta sesión purgó 3 fantasmas: HB-27/46/49).

### 5.2 · Ledger de cobertura vivo   `[MAKE-LIVING — la § Matriz ya existe; se vuelve viva + visible]`
La `§ Matriz de cobertura` del `01-spec.md` (cement 2026-05-31) es el **seed**. Durante developing→G se mantiene viva con un **estado por scenario/branch**:

```
| Bif/RN/AC/SC | estado            | dónde |
|--------------|-------------------|-------|
| ...          | ✅ construido      | test/ruta |
| ...          | → historia {id}   | spawn en G |
| ...          | ⏳ implementar-ahora| (corto+necesario) |
```

- **Piso HARD:** si `cap_change_type: new`, los scenarios del **happy path** DEBEN estar `✅`. No se puede `done` con el core diferido.
- Es la respuesta literal a "no sé qué quedó sin implementar": la columna `→ historia` ES la lista de lo NO construido, visible.
- En `R` se congela y alimenta la cap + las historias spawneadas. **Mata:** el gap invisible.

### 5.3 · G · Chris-verify loop   `[RE-SEQUENCE — el demo gate #37 §5 + kit Layer-10 ya existen; se MUEVEN antes del auditor + se vuelven loop]`
- **Trigger:** default **pausa-y-ofrece** para stories `type ∈ {ui-story, service-story, agentic-story}` con parte funcional. Excepción: `autonomous_mode: true` (Chris lo pide) → corre a done sin pausa. `bugfix` no pausa salvo pedido.
- **Sin estado nuevo:** `state: developed` + `phase: AWAIT_CHRIS_VERIFY`. WIP cap relax como `defer_audit` (no cuenta contra `developed ≤1` mientras espera a Chris).
- **El kit** (ya lo produce dev-team en el developed-boundary, rule #37 Layer 10): `demo-script.md` + `dod_evidence` + dev-app live + el **ledger**.
- **El loop:** Chris ejerce → anota → dev incorpora → repite hasta `chris_verify_signoff`.
- **El demo_signoff de #37 §5 se MUEVE de F a G** (no se duplica — un solo signoff, antes).

```yaml
# checkpoint.md
state: developed
phase: AWAIT_CHRIS_VERIFY        # o AUTONOMOUS si autonomous_mode:true
chris_verify:
  required: true                 # false sólo si autonomous_mode o bugfix sin pedido
  signoff: null                  # → {by: chris, date, result: SATISFIED|SATISFIED_WITH_FOLLOWUPS}
  rounds: []                     # cada corrección anotada + cómo se resolvió o a qué historia fue
```

### 5.4 · R · Reconcile   `[FORMALIZE — inbox lo hizo a mano como scope_amendment]`
Tras `chris_verify_signoff`, `/pm-{brand}` reconcilia **antes** de soltar al auditor:
- `01-spec.md` (mapa funcional + matriz + Gherkin) ⟵ realidad construida + cambios ratificados.
- `03-arch.md` (contrato BE↔FE REAL, no imaginado — HB-42/44), `04-validators.yaml`, la cap.
- El ledger congela `deferred` → crea/linkea las historias spawneadas en G.
- Resultado: **docs == realidad** → el auditor no pelea contra un spec viejo. **Mata:** el auditor revirtiendo lo que Chris pidió.

### 5.5 · Auditor = guardián de arquitectura   `[CLARIFY-ROLE — auditor v5 ya existe; se fija su input]`
- Lee el spec **RECONCILIADO** + `chris_verify_signoff`. Un cambio de scope ratificado por Chris **es el spec ahora**, no una desviación a revertir.
- Guarda los **invariantes**: DDD/tenant/PHI/anti-orphan(CONN)/contrato BE↔FE/no-mirror/arquitectura — NO "¿coincide con el spec pre-iteración?".
- Phase D gherkin-matrix (MISSING→CHANGES_REQUESTED) + verifica el **mutation gate** + ejerce ≥1 write live. Carril R (Responsable) fix-and-own sigue vigente.

### 5.6 · Mutation gate diff-scoped   `[REUSE+WIRE — mutmut ya nombrado opt-in en #37 §2; se cablea + scope]`  (HB-54)
De Uncle Bob harness-sdd, robando la **disciplina** (no su mutador toy):
- **Scope = SOLO líneas nuevas/modificadas** del diff de la story (afford­able). Tool: **mutmut** (BE) / **Stryker** (FE).
- **Dónde:** `/architect` marca superficies **mutation-críticas** por `verification_nature` (commit/persistencia [HB-50] · dinero/pricing · gates PHI · state machines · transforms de contrato [HB-42/44]). En esas: **hard** (umbral pragmático: matar todos los mutantes sobre líneas nuevas). Resto: **advisory** (status quo — anti-costo).
- **Survivor → loop-back:** reporte (línea + mutación + test-gap en prosa) = CHANGES_REQUESTED al fix-loop existente (dev-team escribe el test RED). Es la evidencia objetiva que **mata "tests verdes mockeados"** → endurece el kit de G.
- **★ Survivors en código HEREDADO** (fuera del diff) = NO bloquean; rutean al **carril L4 del CIL** (capability-desfasada). Mutar el diff de una story nueva destapa auto test-debt de caps viejas.
- **Dónde vive:** `04-validators § technical_gates.mutation` (opt-in por nature) + `#37 §2` + `test-design-doctrine`.

### 5.7 · CIL · Ledger de Mejora Continua + stop semanal   `[NEW (1 artefacto) — CONSOLIDA dispersión]`
El harness-backlog "es solo notas y no traslada aprendizajes". El CIL es su **evolución** (no un tracker que compite): owner `/pm-luana`, transversal `docs/process/`, se anota **donde estés**, se **homologa** en el stop semanal (merge→main→sync) — sin worktree especial.

**4 carriles:**
| Carril | Qué | Origen |
|---|---|---|
| **L1 · harness** | proceso → reforzar skill/rule/agent/hook | **= harness-backlog actual, tipado** |
| **L2 · producto/skills-arq** | aprendizaje de producto → skills/arquitectura/domain docs | story-closure |
| **L3 · deuda técnica** | deuda de código/infra pura | dev/auditor |
| **L4 · capability-desfasada** | caps con reglas viejas, hoy stale | **auto-detect**: cap_doctor + cap-anterior-a-cement-date + survivors heredados (§5.6) |

**Cada entrada CARGA el aprendizaje** (no solo nota): `problema → causa raíz → cómo se resolvió → acción de refuerzo → carril`.
**Alimentación:** `L · story-closure` rutea cada problema al carril (relaja learnings.md per-story a "un lugar donde se acumulen" — cero archivo huérfano).
**Stop semanal:** ritual `/mejora-semanal` lee los 4 carriles, los muestra, Chris remedia todo + marca "anotado". **Reúsa el board `/harness` del cockpit (HB-26)** extendido a 4 carriles = la pantalla del stop. **Mata:** los finding-keys dispersos + el "no hay dónde reforzar".

### 5.8 · Cap = qué tengo (no versión)   `[FIX — HB-52]`  (W1, líder)
- **(A) ahora:** `ScenariosSection.tsx` — cap sin scenarios muestra `description`/`what_you_can_do` + caja + estado real. **Cero jerga** `v3.x/F.3/migrará`.
- **(B) graduado:** backfill `what_you_can_do`/`scenarios` en las ~39 caps `stub` de vitalia.
- **Invariante:** "✨ Qué puedo hacer" SIEMPRE responde función, nunca versión. La cap reflejada en `done` incluye lo construido **y** lo deferred (del ledger §5.2).

---

## 6 · Ledger anti-over-engineering

| Pieza | Naturaleza | Reusa | Mata |
|---|---|---|---|
| 5.1 verify-first | principio | HLP §6.1 | docs-fantasma |
| 5.2 ledger vivo | make-living | § Matriz | gap invisible |
| 5.3 G Chris-verify | re-sequence | demo gate #37 §5 + kit Layer-10 | "developed=listo" ciego |
| 5.4 R reconcile | formalize | scope_amendment manual | auditor revierte asks |
| 5.5 auditor guardián | clarify-role | auditor v5 | auditor literalista |
| 5.6 mutation gate | reuse+wire | mutmut opt-in #37 §2 | tests verdes mockeados |
| 5.7 CIL | **1 nuevo (consolida)** | harness-backlog + cockpit /harness + cap_doctor | finding-keys dispersos |
| 5.8 cap=qué-tengo | fix | cap YAML + cockpit | ruido de versión |

**Neto:** 7 re-usos/formalizaciones + 1 artefacto nuevo que consolida. Cero eje nuevo, cero estado nuevo, cero agente nuevo, cero fase nueva (G vive como `phase` de developed).

---

## 7 · Plan de aplicación (fold-in map · wave dedicada, NO mid-feature)

| Pieza | Edita |
|---|---|
| 5.2 ledger | `01-spec` template + `po-ux`/`po` (estados del ledger) + `auditor` Phase D (congela en matriz) |
| 5.3 G | `dev-team` Step 5 (pausa-y-ofrece en vez de auto-handoff salvo `autonomous_mode`) + `story-closure-gate`(.md+detalle) + #37 (mueve demo_signoff a G) + `checkpoint` template (`chris_verify`) |
| 5.4 R | `pm-{brand}` (nuevo paso reconcile pre-auditor) + `story-closure-gate` (fase R entre developed y reviewing) |
| 5.5 auditor | `auditor` SKILL (input reconciliado + "no revertir scope ratificado") + `auditor-{be,fe,agentic}.md` |
| 5.6 mutation | `04-validators` template (`technical_gates.mutation`) + `architect` (marca nature) + `test-design-doctrine` + `#37 §2` + auditor verifica + scripts mutmut/Stryker wiring |
| 5.7 CIL | `harness-backlog.md`→tipado L1 + `docs/process/continuous-improvement.md` (índice 4 carriles) + skill `/mejora-semanal` + cockpit `/harness` 4-lanes + `learning-capture.md` (ruteo) |
| 5.8 cap | `ScenariosSection.tsx` (A) + backfill caps (B) + cockpit cap-drawer |

**Orden de waves** (post-ratificación de este diseño): **W1** 5.8(A) cap-display (tu semilla, barato) · **W2** 5.3+5.4+5.5 spine G/R/auditor (el corazón) · **W3** 5.6 mutation gate · **W4** 5.7 CIL + stop + cockpit · **W5** 5.2 ledger vivo + 5.8(B) backfill. Cada wave: verify-first + diff ratificable + commit por pathspec.

---

## 8 · Decisiones abiertas (micro)
- Naming del ritual: `/mejora-semanal` (default propuesto) · `/stop-semanal` · extender `/harness-audit-2026`.
- Umbral mutation exacto en superficies críticas: "matar todos los mutantes sobre líneas nuevas" (propuesto) vs un % < 100 si hay falsos-positivos por mutantes equivalentes.
- ¿El ledger §5.2 se renderiza en el cockpit (vista por story) o vive sólo en el `01-spec.md`/checkpoint?

---

## 9 · Referencias
- `docs/process/lifecycle.md` — modelo 4-ejes (este diseño NO agrega eje)
- `.claude/rules/story-closure-gate.md` (+ `docs/rules-detail/`) — fases A-F (R se inserta entre A-developed y B-audit)
- `.claude/rules/definition-of-done-live-verify.md` — #37 (demo gate §5 se mueve a G; §2 technical_gates aloja mutation)
- `docs/process/spec-mapa-funcional.md` — § Matriz (seed del ledger)
- `docs/process/capability-protocol.md` — cap schema (qué-hago)
- `docs/process/harness-lifecycle.md` — HLP (el CIL es su evolución; verify-first §6.1)
- `docs/process/harness-backlog.md` — HB-52/53/54 (capturas) → L1 del CIL
- Uncle Bob harness-sdd `betta-tech/harness-sdd@uncle-bob-harness` — origen del mutation gate (disciplina, no código)

---

## 10 · Implementación — v5 BUILT (2026-06-05 · sesión autónoma /pm-luana)

Diseño RATIFICADO (Chris) + IMPLEMENTADO end-to-end. Este doc queda como **registro único** del rediseño (HANDOFF + VERIFIERS scaffolding borrados — git es el respaldo; `REVIEW-process-v5.md` queda como registro de la revisión 3-lentes + decisiones). Cada pieza con consumidor + verificador (CHECK con negative-test "con dientes").

| Wave | Pieza | Commit | Verificador (validate_machinery) |
|---|---|---|---|
| W1 | 5.8 cap-display sin jerga | `21c141e3` | CHECK 12 |
| W2 | 5.3/5.4/5.5 spine G/R/auditor | `b80bf2d3` | CHECK 13-18 (★ 15 deadlock-guard · 16 anti-dup signoff) |
| W3 | 5.6 mutation gate diff-scoped | `271be98c` | CHECK 19-21 (★ 20 degrade-advisory) |
| W4 | 5.7 CIL 4 carriles + /harnesses-improvement | `e5a9552e` | CHECK 22-24 + cockpit vitest carril |
| W5 | 5.2 ledger vivo + cleanup | (este) | CHECK 25-27 (★ 26 productor) |

**Micro-decisiones §8 ratificadas Chris:** ritual = `/harnesses-improvement` (+ deep-sweep `harness-audit-2026` reachable, NO borrado: sirve) · mutation 100% líneas-nuevas + escape equivalente · ledger SSoT spec/checkpoint + cockpit read-only.

**Drifts verify-first (Phase 0) + resolución:**
- D-A (eslint baseline `--max-warnings 0` en #37/template vs gate real) → tracked L1, fuera de scope v5.
- D-B (mutmut/Stryker ausentes) → `mutation_gate.py` DEGRADA advisory (W3).
- D-C (parser severidad≠carril) → `carril` additive en harness-backlog.ts (W4).
- **D-D (`what_you_can_do` no existe)** → **resuelto por REUSO de `user_facing_description`** (anti-dup: NO se agregó campo nuevo). Backfill de caps stub = ruteado a **CIL carril L4** (cap_doctor auto-detecta stubs) — NO mass-invent (verify-first).
- D-E (`demo_signoff` repoint cross-brand) → consolidado a `chris_verify.signoff` (W2, 7 sitios).

**Cleanup (mandato Chris "no archivos inutilizados"):** borrados `HANDOFF-process-v5-implementation.md` + `VERIFIERS-process-v5.md` (scaffolding cumplido; los verificadores viven en `validate_machinery_consistency.py` CHECK 12-27). Workflow `harness-audit-2026` NO borrado (salvage = reachable vía `/harnesses-improvement`).

**Estado machinery:** `make machinery-check` = 69 checks · 0 fallos (16 CHECKs nuevos del proceso v5, cada uno con negative-test verificado).
