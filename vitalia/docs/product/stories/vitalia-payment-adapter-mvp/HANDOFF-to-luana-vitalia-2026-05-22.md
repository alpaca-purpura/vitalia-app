<!-- voseo-allowed: reference doc cites technical instructions per vitalia/.claude/rules/hipaa-lite.md + cherry-pick procedures -->

# HANDOFF — vitalia-payment-adapter-mvp → sesión luana-vitalia

> **From:** worktree efímero `~/Proyectos/luana-vitalia-vitalia-payment-adapter-mvp/` (branch `wip/vitalia-vitalia-payment-adapter-mvp`)
>
> **To:** sesión paralela `~/Proyectos/luana-vitalia/` (branch `wip/vitalia`)
>
> **Date:** 2026-05-22T15:00:00Z
>
> **Author:** `/po` Opus 4.7 en sesión Chris-ratify-batch
>
> **Status:** HANDOFF complete. Worktree efímero scheduled for cleanup. Branch `wip/vitalia-vitalia-payment-adapter-mvp` queda vivo en GitHub 30d (cron `cleanup-wip.yml` auto-elimina).

---

## § 1 — Por qué este handoff existe

La sesión efímera `wip/vitalia-vitalia-payment-adapter-mvp` (born from `origin/main@fa92171`) refinó la story `vitalia-payment-adapter-mvp` produciendo spec v3 + cluster classification durante 2026-05-22T13:50→15:00 UTC.

Durante el cierre se descubrió que la sesión paralela `wip/vitalia` (sesión `luana-vitalia/`) ya tenía la story RE-CONTEXTUALIZADA post-bigbang shell-organism 2026-05-21:
- `phase: AWAITING_PO_DRAFT_RE_PRIORITIZED` (en wip/vitalia)
- `cross_phase_2_consumers: [vitalia-fase2-valeria-agenda, vitalia-fase2-adrian-embudo, vitalia-fase2-adrian-propuestas, vitalia-fase2-config-cuenta]`
- Listada bajo "Service-stories laterales (refining → refined cuando Fase 2 lo necesite)" en brand checkpoint

Mi trabajo NO superseded la story — la complementa. PERO mergear directo a main generaría conflict cross-session porque ambas branches modificaron `vitalia/docs/product/checkpoint.md` con paradigmas distintos (Olas vs Fase 1+2).

**Solución cementada con Chris:** transferir trabajo a wip/vitalia vía cherry-pick selectivo controlado por la sesión paralela, no merge automático.

---

## § 2 — Trabajo VALIOSO para transferir (cherry-pick selectivo)

### § 2.1 — `01-spec.md` v3 (file NEW, sin overlap, transferir limpio)

**Path:** `vitalia/docs/product/stories/vitalia-payment-adapter-mvp/01-spec.md`

**Resumen:**
- 14 Gherkin scenarios (6 happy + 1 negative + 4 edge + 3 adversarial) cementados AI-resistant
- Decisiones tácticas ratificadas Chris 2026-05-22:
  - **Gateway scope:** multi-gateway Strategy MVP (MercadoPago + Stripe LIVE; Culqi defer Slice 2)
  - **Selection mechanism:** `tenant.payment_gateway` per-tenant config (paciente NO elige)
  - **Failure recovery:** downgrade graceful retry 3x con tenacity backoff 1s/4s/16s → escalate admin via inbox
  - **Refund:** solo admin panel (NO Adrián tool `refund_booking`)
  - **Confirmation notif:** Adrián auto WhatsApp event-driven + recordatorio 24h
  - **Webhook security:** HMAC + timestamp 5min window (per hipaa-lite.md)
  - **Idempotency:** keys per booking_id + cron sweeper dup detection
  - **Currency:** `tenant.country` lookup table (no override per-booking)
- § 1.5 backend-only + FE consumers map (alignment shell-organism P5)
- § 3 out-of-scope 3 sub-secciones (payment defer + cobro NO remoto + FE responsabilidad)
- § 5 acceptance criteria con `graders` ejecutables (contract_test paths + state_check db/events_outbox/audit_log + tool_calls + llm_rubric)
- § 6 cross-cutting hipaa-lite + tenant isolation + observability + Prometheus metrics
- § 8 verification commands (smoke pytest)

**Recomendación cherry-pick:**

```bash
# Desde wip/vitalia worktree (~/Proyectos/luana-vitalia/):
cd ~/Proyectos/luana-vitalia
git fetch origin wip/vitalia-vitalia-payment-adapter-mvp

# Cherry-pick file específico (sin tocar otros archivos):
git checkout origin/wip/vitalia-vitalia-payment-adapter-mvp -- vitalia/docs/product/stories/vitalia-payment-adapter-mvp/01-spec.md

# Verificar contenido:
head -50 vitalia/docs/product/stories/vitalia-payment-adapter-mvp/01-spec.md

# Si OK → stage + commit en wip/vitalia:
git add vitalia/docs/product/stories/vitalia-payment-adapter-mvp/01-spec.md
git commit -m "docs(vitalia/payment-adapter-mvp): import 01-spec.md v3 from ephemeral worktree

Spec v3 ratificado Chris 2026-05-22T14:30Z con 14 Gherkin scenarios + decisiones
tácticas (gateway scope multi-gateway Strategy MVP, failure recovery downgrade graceful,
refund admin panel only, confirmation Adrián auto WhatsApp). Cherry-pick desde
wip/vitalia-vitalia-payment-adapter-mvp (ephemeral worktree closed).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

### § 2.2 — `checkpoint.md` story — decisiones tácticas verbatim

**Path:** `vitalia/docs/product/stories/vitalia-payment-adapter-mvp/checkpoint.md`

**Conflict de paradigmas:** mi versión cementó `state: refined + ratified_by_chris: true + spec_v3`. La versión en wip/vitalia tiene `state: refining + phase: AWAITING_PO_DRAFT_RE_PRIORITIZED + cross_phase_2_consumers: [4 stories]`.

**Recomendación:** NO cherry-pick automático. La sesión paralela `/pm-vitalia` actualiza el checkpoint manualmente cuando refine la story integrando:

- **De mi versión preservar:**
  - `gateway_scope_cemented_2026_05_22:` bloque completo (gateway scope + selection + failure_recovery + refund + notification)
  - `ratification_details:` (sections_ratified list)
  - `shell_organism_alignment:` (P5 principle)
  - Bitácora entries 2026-05-22T13:50→15:00Z (history preservada)

- **De wip/vitalia preservar:**
  - `phase` actualizado per paradigm Fase 2
  - `cross_phase_2_consumers` (las 4 stories cross)
  - `blocked_reason` reframed por Fase 2

- **Decidir:** ¿`state` queda en `refining` (paradigm wip/vitalia — re-priorizada) o pasa a `refined` (mi paradigm — spec ratificado)?
  - Si la sesión paralela considera spec v3 suficiente para arrancar /architect cuando Fase 2 lo requiera → `refined`
  - Si quiere re-ratificación con context Fase 2 nuevo → mantener `refining`

---

## § 3 — Trabajo OBSOLETO (NO transferir)

### § 3.1 — `vitalia/docs/product/checkpoint.md` brand-level

**Mi cambio:** agregué sección `functional_clusters` con 7 clusters shell-organism + mapping de stories. La idea era válida pero las stories que citan son las viejas (`vitalia-slice-1-pipeline`, `vitalia-slice-1-inbox`, `vitalia-slice-1-agenda`) — todas REFACTORED o ARCHIVED en wip/vitalia.

**Verdict:** OBSOLETO. La sesión paralela ya tiene el modelo Fase 1+2 superior que reemplaza Olas + clusters. NO cherry-pick este archivo.

**Si la sesión paralela quiere salvar la IDEA de functional_clusters:** podría reescribirla apuntando a las stories Fase 1/2 nuevas:

```yaml
functional_clusters:
  venta_adrian:
    stories_primary:
      - vitalia-fase2-adrian-inbox        # F2-S3
      - vitalia-fase2-adrian-embudo       # F2-S4
      - vitalia-fase2-adrian-outbound     # F2-S5
      - vitalia-fase2-adrian-propuestas   # F2-S6
    stories_supporting:
      - vitalia-payment-adapter-mvp       # service-story lateral (refining)
  operar_valeria:
    stories_primary:
      - vitalia-fase2-valeria-agenda      # F2-S1
      - vitalia-fase2-valeria-pacientes   # F2-S2
    stories_supporting:
      - vitalia-payment-adapter-mvp
      - vitalia-fiscal-emission-pe
  # ... resto agentes ...
```

Decisión queda en la sesión paralela `/pm-vitalia`.

---

## § 4 — Commits afectados en wip/vitalia-vitalia-payment-adapter-mvp

```
620b837f docs(vitalia/payment-adapter-mvp): insert story en cluster venta_adrian — dual taxonomy
d8493d59 docs(vitalia/payment-adapter-mvp): spec v2 ratificada — refining→refined + defer /architect
fa921711 feat(vitalia): Ola 2 Slice 1 — marketing (squash-merge wip/vitalia)   ← born from
```

**Files modificados acumulados:**

| File | Status | Cherry-pick recomendado |
|---|---|---|
| `vitalia/docs/product/stories/vitalia-payment-adapter-mvp/01-spec.md` | NEW v3 | ✅ SÍ — clean transfer |
| `vitalia/docs/product/stories/vitalia-payment-adapter-mvp/checkpoint.md` | MODIFIED | ⚠️ MANUAL MERGE — overlap con wip/vitalia paradigm |
| `vitalia/docs/product/stories/vitalia-payment-adapter-mvp/HANDOFF-to-luana-vitalia-2026-05-22.md` | NEW | 📝 OPCIONAL — vive como history reference |
| `vitalia/docs/product/checkpoint.md` | MODIFIED (functional_clusters NEW section) | ❌ NO — obsoleto, cita stories refactored |

---

## § 5 — Comandos completos para integrar trabajo

### Variante A — Cherry-pick limpio (solo spec v3 + HANDOFF doc)

```bash
# Desde wip/vitalia worktree (~/Proyectos/luana-vitalia/):
cd ~/Proyectos/luana-vitalia
git status --short                                        # verify tree clean
git fetch origin wip/vitalia-vitalia-payment-adapter-mvp

# Cherry-pick los 2 files limpios:
git checkout origin/wip/vitalia-vitalia-payment-adapter-mvp -- \
  vitalia/docs/product/stories/vitalia-payment-adapter-mvp/01-spec.md \
  vitalia/docs/product/stories/vitalia-payment-adapter-mvp/HANDOFF-to-luana-vitalia-2026-05-22.md

git status --short                                        # verify 2 files staged

git commit -m "$(cat <<'EOF'
docs(vitalia/payment-adapter-mvp): import spec v3 + HANDOFF doc from ephemeral worktree

Spec v3 ratificado Chris 2026-05-22 con 14 Gherkin scenarios + decisiones tácticas
(gateway scope multi-gateway Strategy MVP MercadoPago+Stripe LIVE / failure recovery
downgrade graceful tenacity 3x / refund admin panel only / Adrián auto confirmation
WhatsApp + recordatorio 24h / webhook HMAC + 5min window / idempotency per booking_id).

§ 1.5 backend-only + FE consumers map (alignment shell-organism P5).
§ 3 out-of-scope 3 sub-secciones expandidas (payment defer + cobro NO remoto +
FE responsabilidad stories Fase 1/2).

HANDOFF doc preserva history transferencia desde worktree efímero
wip/vitalia-vitalia-payment-adapter-mvp closed 2026-05-22T15:00Z.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"

git push origin wip/vitalia
```

### Variante B — Re-refine completo (descartar spec v3, escribir nuevo bajo paradigm Fase 2)

Si la sesión paralela considera que el spec v3 está demasiado anclado al modelo pre-bigbang y prefiere reescribir bajo paradigm Fase 2 (con cross_phase_2_consumers como input principal en lugar de "agenda crear turno → POST /api/v1/vitalia/bookings"):

```bash
# Desde wip/vitalia worktree:
cd ~/Proyectos/luana-vitalia

# Solo IMPORTAR el HANDOFF doc + decisiones tácticas como reference; descartar spec v3:
git checkout origin/wip/vitalia-vitalia-payment-adapter-mvp -- \
  vitalia/docs/product/stories/vitalia-payment-adapter-mvp/HANDOFF-to-luana-vitalia-2026-05-22.md

git commit -m "..."
git push origin wip/vitalia

# Luego /pm-vitalia + /po refinan vitalia-payment-adapter-mvp from scratch bajo paradigm Fase 2,
# citando las decisiones tácticas del HANDOFF doc como input.
```

### Variante C — Descartar TODO (no transferir nada)

Si el contenido NO se considera útil:

```bash
# Sólo borrar branch wip/* en GitHub:
git push origin --delete wip/vitalia-vitalia-payment-adapter-mvp
```

NO recomendado — el spec v3 tiene decisiones cementadas con Chris que ahorra re-litigar.

---

## § 6 — Branch wip/vitalia-vitalia-payment-adapter-mvp lifecycle

**Status post-handoff:**
- Worktree local: borrado (cleanup 2026-05-22T15:00Z manual desde ~/Proyectos/luana-platform/)
- Branch local en `luana-platform/`: borrado (`git branch -d wip/vitalia-vitalia-payment-adapter-mvp`)
- Branch remoto `origin/wip/vitalia-vitalia-payment-adapter-mvp`: **VIVE 30 días más** como reference. Cron `cleanup-wip.yml` auto-elimina si >30d sin commits.
- Comando para borrar manual antes:
  ```bash
  git push origin --delete wip/vitalia-vitalia-payment-adapter-mvp
  ```

**Cuándo borrar:** después de que la sesión paralela haya cherry-pick lo que necesite (Variante A, B, o C). NO borrar antes — perdés el reference si querés volver a inspeccionar.

---

## § 7 — Resumen ejecutivo TL;DR

| Aspecto | Decisión |
|---|---|
| Story state final (en wip/*) | `refined` (paradigm pre-bigbang, mi sesión) |
| Story state SSoT actual (wip/vitalia) | `refining + AWAITING_PO_DRAFT_RE_PRIORITIZED` (paradigm post-bigbang) |
| Spec v3 ratificado por Chris | ✅ SÍ, value preserved para Fase 2 cross_consumers |
| Cluster classification mía | ❌ obsoleta (cita stories refactored) |
| Recomendación transferencia | Variante A — cherry-pick `01-spec.md` v3 + HANDOFF doc, descartar mis brand checkpoint mods |
| Worktree efímero | Cleanup manual ahora |
| Branch remoto | Vivo 30d, descartar después de cherry-pick |

---

## § 8 — References

- Spec v3: `vitalia/docs/product/stories/vitalia-payment-adapter-mvp/01-spec.md` (en wip/vitalia-vitalia-payment-adapter-mvp)
- Checkpoint version mía: idem path (en wip/vitalia-vitalia-payment-adapter-mvp)
- Checkpoint version sesión paralela: idem path (en wip/vitalia — diferente)
- Shell-organism baseline: `vitalia/docs/product/stories/vitalia-shell-organism/00-session-baseline.md`
- Stories Fase 1/2 cross-consumers: `vitalia/docs/product/stories/vitalia-fase{1,2}-*/checkpoint.md` (en wip/vitalia)
- Brand checkpoint version sesión paralela: `vitalia/docs/product/checkpoint.md` (en wip/vitalia, modelo Fase 1+2)
