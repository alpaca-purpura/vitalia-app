# REVIEW — Proceso v5 (coherencia spec→done) · revisión profunda pre-código

> **Estado:** ✅ RATIFICADO + **IMPLEMENTADO** (2026-06-05 · ver `process-coherence-v5-2026-06.md` §10). Este doc queda como **registro de la revisión 3-lentes + decisiones** (el HANDOFF + VERIFIERS scaffolding se borraron — git es el respaldo; los verificadores viven en `validate_machinery_consistency.py` CHECK 12-27). **Owner:** `/pm-luana`. **Fecha:** 2026-06-05. **Para:** Chris ratifica este REVIEW (+ las 3 micro-decisiones del §8 del diseño) ANTES de que se toque cualquier archivo (Phase 2/3).
>
> **Insumo:** `process-coherence-v5-2026-06.md` (8 piezas) + `HANDOFF-process-v5-implementation.md` + `harness-backlog.md` (HB-52/53/54 + sweep).
> **Método:** verify-first contra el FS (la auditoría sobreestima) → 3 lentes (CONN · SOLID · regresión) → veredicto por pieza → cierre de micro-decisiones.
>
> **Veredicto global:** el diseño es **sólido y genuinamente anti-Frankenstein** (7 re-usos + 1 artefacto que consolida; cero eje/estado/agente/fase nueva). **6 de 8 piezas necesitan WIRING-FIX** (cerrar el lazo: falta un productor-que-mantenga-vivo, o un consumidor-que-lea-precondición, o re-apuntar una referencia que queda muerta) — NINGUNA necesita rediseño ni matarse. 2 piezas limpias (5.1, 5.8). Los fixes SON la disciplina anti-isla aplicada al propio harness.

---

## 0 · Phase 0 — verify-first (resultado, no se da por cierto el diseño)

### Slots de reuso (7/7 confirmados en FS)

| Slot que el diseño dice "reusa" | Existe en FS | Evidencia |
|---|---|---|
| demo gate `#37 §5` + `demo_signoff` schema | ✅ | `definition-of-done-live-verify.md:155-169` |
| dev-team developed-boundary (kit Layer-10) | ✅ | `dev-team/SKILL.md:863` (Step 4.6 HARD) + gate bash `507-527` + `autonomous_mode` Step 0.7 `155-171` |
| `04-validators §technical_gates` | ✅ | `04-validators-template.yaml:29` (+ `verification_nature`, `business_rules`, `playwright_visual_scope`). **Sin subkey `mutation`** (lo agrega W3 — esperado) |
| mutmut nombrado opt-in | ✅ | `#37 §2:136` |
| cockpit `/harness` (HB-26) | ✅ | `app/harness/page.tsx` + `app/api/harness/route.ts` + `lib/harness-backlog.ts` (+ tests) |
| `cap_doctor` | ✅ | `scripts/cap_doctor.py` |
| § Matriz de cobertura (seed del ledger) | ✅ | `01-spec-template.md` + `spec-mapa-funcional.md` |

Extra confirmado: `checkpoint-template.md` ya tiene `defer_audit`, `dod_live_verified`, `demo_signoff:` (L47) — `chris_verify` es campo NUEVO (W2, esperado). `validate_machinery_consistency.py` = 11 `check_*` + `main()→int` + `sys.exit(main())` (Phase 2 appendea CHECKs acá). `harness-backlog.ts` = parser PURO (`HarnessItem`/`HarnessEstado`/`HarnessSeveridad`, sin `carril`).

### 3 fantasmas — confirmados purgados (no resucitan)

- **HB-27** `platform-context.ts` existe → purgado OK.
- **HB-49** `app/api/stories/route.ts:52` tiene `catch` + `parse_error` badge → purgado OK.
- **HB-46** `04-validators-template.yaml:122` cmd real sin `--max-warnings 0` → purgado OK.

### Drift nuevo registrado (overestimate = señal de calidad)

| ID | Drift | Disposición |
|---|---|---|
| **D-A** | `#37 §2:136` (baseline) + `04-validators:30` (token `eslint_max_warnings_0`) siguen declarando `--max-warnings 0`, contradice el gate-runner real (`eslint src/` 0-errores, warnings ratchet-toleradas). Lineage HB-46 (cmd ya purgado, pero la DECLARACIÓN baseline persiste) | **No bloquea v5.** → CIL L1/L4 al construir el CIL (W4) |
| **D-B** | `mutmut` NO en venv ni `pyproject.toml`; Stryker NO en `package.json`. El tool está GENUINAMENTE ausente hoy | **Prerequisito de W3:** la degradación-advisory + el wrapper diff-scope NO son opcionales — son lo primero de la wave |
| **D-C** | `harness-backlog.ts` modela `severidad`, no `carril`. CIL 4-lanes = dimensión ortogonal | **W4 additive** (agrega `carril`, conserva `severidad` — OCP), no reescribe |
| **D-D** | `what_you_can_do` **NO existe** en el schema de cap (grep vacío en `capability-protocol.md` + cockpit `types.ts`). El diseño 5.8 lo asume | **W1(A)** fallback usa `description` (sí existe, confirmado HB-52); **W5(B)** AGREGA el campo al schema + cockpit types ANTES del backfill |
| **D-E** | `demo_signoff` (que 5.3.ii mueve F→G) lo leen **4 pm skills** (Fase F REFUSE, ej. `pm-vitalia:251`) + #37 §5 + checkpoint template | el repoint a `chris_verify.signoff` es **cross-brand** (pm-{vitalia,nicolify,comunify,lupulo}) — W2 lo trata como un solo campo en 7 sitios |

---

## 1 · Lente 3a — CONEXIÓN (anti-isla CONN aplicada AL HARNESS)

Por cada pieza: **productor → consumidor → enforcement** + ¿huérfano? Las 4 contenciones CONN (**C**onsumed · **O**n-map · **N**avigable · **N**otarized) aplicadas a los artefactos del propio harness.

| Pieza | Productor (escribe) | Consumidor (lee) | Enforcement (dónde) | Hueco CONN detectado |
|---|---|---|---|---|
| **5.1 verify-first** | toda skill que afirma estado | downstream + registro de overestimates | HLP §6.1 (principio) | Sin teeth mecánicas — es disciplina. Aceptable: los verificadores por-wave (Phase 2) + los CHECKs SON sus teeth. **OK** |
| **5.2 ledger** | po-ux seed (§Matriz) **+ ❓ dev-team mantiene la columna `estado` viva** | G (Chris lee el kit), R (pm congela deferred), auditor Phase D | 01-spec template + auditor Phase D + piso HARD (`cap_change_type:new`→happy-path `✅`) | **🔴 FALTA PRODUCTOR**: si nadie actualiza `estado` durante developing, el ledger nace en `refined` y llega STALE a G → G lee una foto vieja. El Phase-2-map solo cubre "auditor LEE" + "po-ux SEED". Falta el step dev-team que lo mantiene vivo |
| **5.3 G Chris-verify** | dev-team produce el kit + **PAUSA** | Chris (ejerce/anota), dev-team (incorpora) | dev-team Step 5 re-secuenciado + checkpoint `chris_verify` + WIP-cap relax | **🔴 3 huecos** (ver Lente 3c · es la pieza de mayor riesgo): (i) `phase:AWAIT_CHRIS_VERIFY` debe ser WIP-cap-exento en 3 lugares; (ii) `demo_signoff` F→G deja **referencia muerta** en Fase F; (iii) auditor debe ramificar autonomous vs signoff |
| **5.4 R reconcile** | `/pm-{brand}` reconcilia spec/arch/validators/cap | auditor (lee reconciliado) + historias spawneadas | pm-{brand} nuevo step + story-closure fase R | **🟡 R es soft-skippable**: sin un marcador `reconciled: true` que el auditor lea como PRECONDICIÓN, el pm puede saltar R y el auditor lee docs stale (rompe CHECK 5.5) |
| **5.5 auditor guardián** | (clarify-role) | el verdict | auditor SKILL input + auditor-{be,fe,agentic}.md | **🟡 hueco sutil**: "no revertir scope ratificado" necesita `chris_verify.signoff.rounds` como **allowlist**. Un scope-delta que NO está en `rounds` SIGUE siendo finding. Sin esto, "no revertir scope ratificado" degenera en "no revertir NINGÚN scope" (agujero) |
| **5.6 mutation** | architect marca superficies + dev-team corre mutmut/Stryker diff-scoped | survivor→CHANGES_REQUESTED (fix-loop); survivor heredado→CIL L4 | `04-validators §technical_gates.mutation` + #37 §2 + test-design-doctrine + auditor verifica | **🔴 2 huecos**: (i) el writer survivor-heredado→**L4 no existe** (¿dónde se escribe?); (ii) tool ausente (D-B) → si hard-falla rompe `ci-parity`/gate-runner |
| **5.7 CIL** | story-closure L rutea; dev/auditor (L3); auto-detect (L4) | `/mejora-semanal` + cockpit /harness 4-lanes | harness-backlog→L1 tipado + continuous-improvement.md + skill + cockpit + learning-capture routing | **🟡 riesgo anti-dup**: continuous-improvement.md NO debe ser un 5º store que compite con harness-backlog + learnings/. Debe ser **índice/router** sobre 4 hogares EXISTENTES |
| **5.8 cap** | (A) ScenariosSection fallback; (B) backfill `what_you_can_do` | Chris (cap-drawer) | test ScenariosSection (cero string de versión) | **🟢 wiring chico**: ScenariosSection hoy recibe solo `{ scenarios }` (L11) → para fallback necesita recibir `description`/`what_you_can_do` del cap; CapDrawer debe pasarlo. Confirmar que `what_you_can_do` está en el schema de cap (si no, A usa `description`, B agrega el campo) |

**Síntesis CONN:** los huecos son todos del MISMO tipo — **el lazo no cierra**: falta un productor (5.2), una precondición leída (5.4, 5.5), un re-apuntado de referencia muerta (5.3.ii), o un writer de destino (5.6.i). Es exactamente la isla que CONN previene, aplicada al harness. Ninguno requiere repensar la pieza; todos se cierran agregando el extremo faltante del cable + su CHECK (Phase 2).

---

## 2 · Lente 3b — SOLID-para-harness

| Principio | Veredicto | Detalle |
|---|---|---|
| **SRP** | ✅ con 1 guardia | El diseño NO mete el mutation gate dentro del closure-gate (vive en su slot 04-validators) — correcto. **Guardia:** el CIL puede violar SRP si se vuelve god-doc. Mantener CIL = router, L1 en su hogar actual (harness-backlog), no un store nuevo |
| **OCP** | ✅ | Extiende vía slim-stub + `references/`/`rules-detail/` (#37 §2 aloja mutation, no reescribe #37). `validate_machinery` += CHECKs (additive). `harness-backlog.ts` += `carril` conservando `severidad` (D-C) |
| **LSP** | ⚠️ | La cadena pasa de `dev-team→auditor` a `dev-team→[G:Chris]→[R:pm]→auditor`. El contrato anti-telephone (`<verdict> → <path>`) se preserva PERO el auditor debe aceptar DOS inputs sustituibles: with-signoff (default) y autonomous-attested. **Fix:** auditor ramifica en `autonomous_mode` (precondición chequeada, no asumida) |
| **ISP** | ✅ | slim stubs respetados — el ledger no obliga a po-ux a cargar el mutation gate; checkpoint YAML es field-addressable (cada skill lee solo su campo) |
| **DIP** | ✅ con 1 guardia | skills dependen de SSoT (lifecycle/capability-protocol/#37), no de internals. **Guardia:** el ruteo del CIL debe DEPENDER de la taxonomía de `learning-capture.md` (abstracción), NO forkearla |
| **Anti-dup** | ⚠️ | 2 puntos a vigilar: (a) CIL vs harness-backlog/learnings — CONSOLIDA, no duplica (ver SRP); (b) `demo_signoff` debe **MOVERSE** a un solo campo (`chris_verify.signoff`), NO quedar duplicado F+G — re-apuntar #37 §5 + pm Fase F + G al MISMO campo |

**Síntesis SOLID:** el diseño es estructuralmente sano. Las 2 advertencias (LSP-branch del auditor, anti-dup del signoff + CIL) son los mismos huecos CONN vistos desde otra cara. Ningún principio se rompe; se respetan agregando las precondiciones explícitas.

---

## 3 · Lente 3c — SEGURIDAD DE REGRESIÓN (blast radius + verificador, por pieza)

> "Que mejorar uno NO rompa otro." Cada pieza: qué comportamiento EXISTENTE podría romper + el verificador que prueba no-regresión.

| Pieza | Blast radius (qué podría romper) | Verificador no-regresión (Phase 2) | Riesgo |
|---|---|---|---|
| **5.1** | ninguno (principio) | este mismo Phase 0 + registro de overestimates | 🟢 |
| **5.2** | el template 01-spec cambia → specs viejos sin columna `estado` | CHECK: matriz tiene columna `estado` + auditor la lee. **Backward-compat: NO retro-enforzar** en stories archivadas/in-flight (legacy sin columna = no enforced) | 🟡 |
| **5.3** | **(a)** WIP-cap deadlock: `AWAIT_CHRIS_VERIFY` es `state:developed` → la regla dev-team "REFUSE pickup si MISMO MÓDULO en {developing,developed,reviewing}" (`SKILL.md:12`) BLOQUEA otra story del módulo mientras Chris tarda. **(b)** pre-commit dod-evidence-gate (#37 Layer 6) bloquea transición a `developed` sin `dod_evidence` — compatible (el kit ya trae dod_evidence en developed) pero verificar. **(c)** WIP-cap v2 `developed≤1` | CHECK: dev-team REFUSE-rule + WIP-cap v2 + pre-commit Section 12 reconocen `AWAIT_CHRIS_VERIFY` como parked (igual que `defer_audit`). **Negative test:** story en AWAIT_CHRIS_VERIFY NO debe bloquear pickup de otra story mismo-módulo | 🔴 **alto** |
| **5.4** | story-closure fases A-F ganan una R entre developed y audit → state-machine | CHECK: pm reconcile-step existe pre-auditor + marcador `reconciled:true` que el auditor lee. Confirmar: NO eje/estado nuevo (R = step dentro de developed→reviewing) | 🟡 |
| **5.5** | un auditor que ya no flaggea scope-drift podría dejar pasar over-reach REAL | CHECK: auditor input cita "reconciliado+signoff" + lógica `rounds`-as-allowlist (delta fuera de rounds = finding) | 🟡 |
| **5.6** | si hard-falla con tool ausente (D-B) → rompe `ci-parity`/gate-runner | CHECK: `technical_gates.mutation` + architect marca nature + **DEGRADE-ADVISORY si tool ausente** (negative test: tool ausente → advisory, NO fail). Prerequisito: degrade + wrapper diff-scope (mutmut no diff-scopea nativo — necesita `git diff` + filtro de líneas) | 🔴 **alto** |
| **5.7** | el parser cockpit `/harness` (HB-26) se rompe al tipar a 4 lanes (D-C); learnings per-story huérfanos | CHECK: cockpit parser test extendido (sigue verde con `carril` additive) + 4-lane render. NO borrar los paths canónicos de learning-capture (CIL los INDEXA) | 🟡 |
| **5.8** | cambio de firma de ScenariosSection rompe render de CapDrawer | test: ScenariosSection fallback renderiza `description` + CERO string de versión; CapDrawer pasa el prop | 🟢 (1-2 archivos) |

**Síntesis regresión:** 2 piezas de riesgo ALTO (5.3 G por el deadlock WIP-cap; 5.6 mutation por el hard-fail-on-absent-tool). Ambas tienen mitigación clara y mecánica (exención WIP-cap + negative test; degrade-advisory + negative test). El resto es 🟡/🟢 con verificador directo. **Recomendación dura: ninguna pieza se marca "hard" hasta que su negative-test pase** (especialmente 5.6: advisory-everywhere primero, hard-on-critical como follow-on una vez probado el tooling).

---

## 4 · Veredicto por pieza

| Pieza | Veredicto | Fix requerido antes de build (si aplica) |
|---|---|---|
| **5.1 verify-first** | ✅ **COHERENTE** | — (principio; teeth = verificadores por-wave) |
| **5.2 ledger vivo** | ⚠️ **NEEDS-FIX** | Agregar PRODUCTOR: step dev-team que mantiene `estado` vivo durante developing (no solo seed po-ux + read auditor) + backward-compat (no retro-enforzar) |
| **5.3 G Chris-verify** | ⚠️ **NEEDS-FIX (alto)** | (i) `AWAIT_CHRIS_VERIFY` WIP-cap-exento en dev-team REFUSE + WIP-cap v2 + pre-commit S12; (ii) re-apuntar `demo_signoff` F→G a UN campo `chris_verify.signoff` (Fase F + #37 §5 + pm skill); (iii) auditor ramifica autonomous vs signoff. Negative-test del deadlock obligatorio |
| **5.4 R reconcile** | ⚠️ **NEEDS-FIX (menor)** | Marcador `reconciled:true` que el auditor lee como precondición. Confirmar cero estado/eje nuevo |
| **5.5 auditor guardián** | ⚠️ **NEEDS-FIX (sutil)** | `signoff.rounds` = allowlist de cambios ratificados; delta fuera de rounds = finding |
| **5.6 mutation gate** | ⚠️ **NEEDS-FIX (costo/regresión)** | Prerequisito D-B: degrade-advisory + wrapper diff-scope ANTES de marcar hard. Definir writer survivor-heredado→L4. Recomendado fásico (advisory W3, hard-critical follow-on) |
| **5.7 CIL** | ⚠️ **NEEDS-FIX (anti-dup/SRP)** | CIL = router/índice, NO 5º store. L1 en harness-backlog (+columna `carril`/tag, conserva `severidad`). L2/L3/L4 → hogares existentes (taxonomía learning-capture — DIP). Parser cockpit additive |
| **5.8 cap=qué-tengo** | ✅ **COHERENTE** | Wiring chico: firma ScenariosSection + CapDrawer pasa prop + confirmar `what_you_can_do` en schema. Buena semilla W1 |

**Neto:** 2 ✅ · 6 ⚠️ needs-fix. **Todos los needs-fix son wiring (cerrar el lazo CONN), no rediseño.** El diseño NO tiene piezas que matar, fusionar de más, ni mecanismos paralelos. Confirma el anti-Frankenstein.

---

## 5 · Impacto en el plan de waves (los fixes se pliegan, no agregan waves)

- **W1** (5.8 cap-display): ✅ listo. Sumar: confirmar `what_you_can_do` en schema + firma ScenariosSection. Sin sorpresas.
- **W2** (5.3+5.4+5.5 spine): absorbe los fixes 🔴/🟡 de G/R/auditor. **La WIP-cap-exención de `AWAIT_CHRIS_VERIFY` es el ítem #1** (sin él, deadlock). Los verificadores Phase 2 de W2 deben incluir el negative-test del deadlock + el `reconciled:true` + el `rounds`-allowlist.
- **W3** (5.6 mutation): **primero el degrade-advisory + wrapper diff-scope** (D-B), luego hard-on-critical. Definir writer→L4 (depende de que L4 del CIL exista → leve dependencia W4; resolver con un placeholder de destino en W3, poblado en W4).
- **W4** (5.7 CIL): parser additive (D-C) + CIL como router. Resuelve el destino L4 que W3 dejó apuntado.
- **W5** (5.2 ledger vivo + backfill): sumar el PRODUCTOR dev-team (mantener `estado` vivo) — es el fix de 5.2.

Cero waves nuevas. Una dependencia leve W3→W4 (destino L4) resuelta con placeholder.

---

## 6 · Cierre de las 3 micro-decisiones (§8 del diseño) — ✅ RATIFICADO Chris 2026-06-05

| # | Decisión | ✅ Ratificado | Nota |
|---|---|---|---|
| **0** | Verdict del REVIEW | **Ratifico, arrancá Phase 2** | los 6 needs-fix son wiring-CONN, no rediseño |
| **1** | Naming del ritual semanal | **`/harnesses-improvement`** | NO `/mejora-semanal`. **Mandato extra:** rescatar de `/harness-audit-2026` lo que sirva → plegarlo a `/harnesses-improvement`; **borrar `/harness-audit-2026`** si queda redundante (anti-skill-muerta: "la idea no es tener skills que no use"). W4 ejecuta el salvage+merge+delete + actualiza referencias (`harness-lifecycle.md`, `.claude/workflows/harness-audit.js`, MEMORY) |
| **2** | Umbral mutation en superficies críticas | **100% líneas-nuevas + escape equivalente documentado** | 1 línea de justificación por mutante-equivalente, patrón ratchet `KNOWN_*` shrink-only (mismo que arch-fitness allowlist) |
| **3** | ¿Ledger §5.2 dónde vive? | **SSoT en `01-spec.md`/checkpoint + cockpit read-only** | invariante PARADIGM "el cockpit LEE no genera"; render = W5, opcional |

---

## 7 · Gate — qué ratificás (STOP hasta tu OK)

1. **El REVIEW** (3 lentes · 8 veredictos · 6 wiring-fixes identificados). ¿De acuerdo en que los needs-fix son wiring-CONN y no rediseño?
2. **Las 3 micro-decisiones** del §6 (recomendaciones arriba — ratificá o cambiá).
3. **El orden fásico de 5.6** (advisory-everywhere W3 → hard-on-critical follow-on) y la **prioridad #1 de W2** (WIP-cap-exención de `AWAIT_CHRIS_VERIFY`).

**Sin tu ✓ no se toca código** (Phase 2 verificadores → Phase 3 waves). Al ratificar, arranco Phase 2 (verificadores PRIMERO, negative-test con dientes por wave) como manda el HANDOFF.
