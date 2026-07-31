# Vitalia — Brand overlay

> **Auto-cargado** cuando cwd cae dentro `vitalia/...`. Coexiste con root `CLAUDE.md` (no duplica — extiende).

**Brand:** Vitalia. **Vertical:** Salud + Bienestar electivo LatAm (clínicas que requieren marketing + captación, NO emergencias).

## Product vision (pointer)

→ `vitalia/docs/product/vision.md` (full vision: verticales Tier 1-3, HIPAA-lite 6 países, competidores, diferenciadores, 3 personas, GTM).

**TL;DR:** SaaS multitenant para profesionales clínicos electivos LatAm (dental cosmético, estética, oftalmología refractiva, psicología, psiquiatría, dermatología, nutrición clínica, fisioterapia, capilar, fertilidad). Diferenciadores clave: (1) agente IA captador vertical Instagram/WhatsApp, (2) reservas prepagadas + Mercado Pago, (3) recurrence engine post-tratamiento, (4) compliance multi-país out-of-the-box, (5) omnichannel voice/voz personalizado por perfil paciente.

## Verticales target (quick reference)

| Tier | Verticales | LTV típico | Diferencial captación |
|---|---|---|---|
| **Tier 1 (MVP)** | Odontología cosmética · Medicina estética · Oftalmología refractiva | USD 5K-25K | Instagram pre/post + WhatsApp agente IA |
| **Tier 2 (6-12 meses)** | Psicología · Psiquiatría · Dermatología · Nutrición clínica | USD 1.5K-8K | Recurrencia automatizada (semanal/mensual) |
| **Tier 3 (12-24 meses)** | Fisioterapia · Medicina capilar · Fertilidad | USD 600-25K | Paquetes pre-pagados + turismo médico |

Verticales DESCARTADOS: emergencias, cardiología, oncología, traumatología pediátrica (no electivo, no marketing-decisivo).

## Brand-specific gates

### HIPAA-lite multi-país (HARD)

Vitalia DEBE cumplir 6 jurisdicciones simultáneas para tenants LatAm: **AR (Ley 25.326 + 26.529) · MX (LFPDPPP + NOM-024) · CO (Ley 1581 + Res. 1995) · PE (Ley 29733 + 26842 + RENHICE) · CL (Ley 19.628 + 20.584) · BR (LGPD + Lei Prontuário)**.

Obligaciones SaaS day-1:
1. Consentimiento informado digital con timestamp + firma electrónica
2. Retención 10-20 años HCE (varía país)
3. Derecho acceso/rectificación/supresión (ARCO / Habeas Data) endpoints API + UI
4. Encripción at-rest AES-256 + in-transit TLS 1.3
5. Logs auditoría inmutables (quién/qué/cuándo/dónde)
6. RBAC roles profesional (médico tratante / asistente / admin / paciente)
7. Firma electrónica/digital validez legal HCE
8. DPO/Responsable tratamiento per tenant
9. Brecha datos notificación obligatoria (BR + CO + PE)

**Implementación:** módulo `core/luana-core-compliance/` con policies por país-tenant + auditoría inmutable + DSAR endpoints + retention policies. Vitalia consume via Extension SDK.

### Brand-specific anti-patterns

- ❌ Hardcodear políticas retención (varía 5-20 años por país) — siempre desde `tenant.compliance_policy`
- ❌ Aceptar consentimiento sin firma electrónica + timestamp (rompe AR Ley 26.529 + MX NOM-024)
- ❌ Exportar HCE sin logs auditoría del exportador (rompe todos los 6 países)
- ❌ Mostrar datos paciente cross-tenant (rompe Habeas Data CO + LFPDPPP MX agravado por salud sensible)
- ❌ Logs con datos sensibles no sanitizados (PII clínica > PII general)
- ❌ Recordatorios automatizados a paciente sin opt-in explícito previo (rompe consentimiento informado)
- ❌ Voseo en UI clinical (paciente LatAm neutro — voseo OK solo si tenant es AR puro)

## Brand-specific commands

```bash
WS=$(git rev-parse --show-toplevel)

# Dev stack vitalia
make dev-vitalia                                      # docker compose vitalia (BE :8002 + FE :3002)
docker logs luana-dev-vitalia_backend_dev-1 --tail 100
docker logs luana-dev-vitalia_frontend_dev-1 --tail 100

# BE tests
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/{module}/ -v
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/ -x -q

# FE tests
cd ${WS}/vitalia/frontend && npx tsc --noEmit
cd ${WS}/vitalia/frontend && npx vitest run src/features/{module}/
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke

# Alembic (workdir /workspace/vitalia/backend + venv /workspace/.venv — HB-37 ground-truth)
docker exec luana-dev-vitalia_backend_dev-1 bash -c "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic current"
docker exec luana-dev-vitalia_backend_dev-1 bash -c "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic upgrade head"

# Health
curl http://127.0.0.1:8002/health
```

## Design system SSoT (★ cargar ANTES de tocar `vitalia/frontend/src/**`)

Skill `vitalia-design-system` = índice cargable del shell-organism + átomos/moléculas + tokens + **5 especialistas + Valeria supervisora** (★ v1.2 2026-05-30: Lisa · Mateo · Adrián · Lucas · Camila en Ribbon; Valeria = sidebar supervisor; Mateo = Operar/Mi Día con `--agent-mateo: #FEE209`). NO duplica; apunta a fuentes. `/architect` lo lista en `must_load_skills` de todo ticket FE; `builder-frontend` lo carga (su único canal — no hereda este overlay); `auditor-frontend` lo usa en cat 9/13. SSoT que indexa: `vitalia/docs/architecture/{design-system.md, SHELL-DESIGN-CONTRACT.md}` + `vitalia/frontend/src/app/globals.css` + `tailwind.config.ts` + `src/lib/shell-routes.ts`. ⚠️ `core/@luana/design-tokens` solo exporta z-index — tokens de color viven en `globals.css`.

## Brand-specific skills

- `/pm-vitalia` — owner SSoT funcional Vitalia (outcomes/stories/capabilities/modules)
- `vitalia-design-system` — design system + shell organism SSoT cargable (FE builds + audits) ★
- `/po-ux` — refining stories UI std vitalia (CRUD/list/detail/form/dashboard)
- `/po` — refining stories service vitalia (orchestration sin UI tradicional)
- `/ux-agentico` — refining stories conversacionales (Valeria agenda, Camila copilot)
- `/architect` (con `<brand>: vitalia`) — ready package vitalia
- `/dev-team` (con `<brand>: vitalia`) — autonomous build vitalia
- `/auditor` (con `<brand>: vitalia`) — review vitalia

## Prior-art sources (refining — actualizado 2026-07-31, repo standalone single-brand)

**Prior-art scan OBLIGATORIO** (anti-duplication-refining). Fuentes en ESTE repo (no hay otras marcas):

| Source | Path | Cuándo consultar |
|---|---|---|
| `core/luana-core-*/` engine (27 packages) | `core/luana-core-*/src/luana_core_*/` | SIEMPRE — consumir vía import, NUNCA recrear |
| `vitalia/` propio (archive + capabilities + learnings) | `vitalia/docs/archive/*/stories/`, `vitalia/docs/product/capabilities/`, `vitalia/docs/learnings/` | SIEMPRE — aplicar aprendizajes propios |
| Learnings transversales | `docs/learnings/` | SIEMPRE — patterns técnicos cross-engine |
| Snapshot arqueológico (read-only) | `docs/archive/2026/snapshot-pre-multibrand-pm-redesign/` | Referencia histórica patterns shipped pre-reorg. NO live work — frozen 2026-05-15 |
| Herencia multimarca archivada | `docs/archive/2026/multibrand-legacy/` | Referencia histórica docs multimarca (las otras marcas viven en luana-platform, no acá) |

## Brand checkpoint pointer

```bash
cat vitalia/docs/product/checkpoint.md            # State brand actual
cat vitalia/docs/product/BACKLOG.md               # Backlog auto-gen (NO editar manual)
ls vitalia/docs/product/stories/                  # Stories activas
ls vitalia/docs/archive/2026/stories/             # Stories done
```

## Bidirectional code↔cap mapping (cement 2026-05-28 v3.2)

Toda story que toque `cap_change_type ∈ {new, extend}` sobre cap user_visible:true MUST poblar bloques v3.2 en cap YAML al merge Fase F.3: `scenarios[]` + `access` + `business_rules`. Archivos de código nuevos MUST tener header `# cap: <module>.<slug>` (Python) o `// cap: ...` (TS/TSX) en líneas 1-3.

```bash
# Levantar cockpit y abrir tab Functionality (vista narrada del producto)
make cockpit-up                                    # cockpit vendored (:4002) → http://localhost:4002/functionality

# Crear una cap NUEVA (HB-51 · NUNCA hand-author el YAML)
make new-cap BRAND=vitalia MODULE=inbox SLUG=adrian-inbox AREA=adrian.inbox

# Health report code↔cap de un vistazo (G1-G6 + schema · debe dar 0 antes del merge)
make cap-doctor BRAND=vitalia

# Regenerar índices code↔cap (auto-corre en pre-commit Section 5c/5d/5e)
python3 scripts/generate_code_to_cap_index.py --brand vitalia        # + resolved_cap_to_files
python3 scripts/validate_code_cap_bidirectional.py --brand vitalia   # G1-G6 HARD para vitalia (5e/4e)

# Outputs gitignored R3 v2:
ls vitalia/docs/product/capabilities/_*.json       # status + code-index + bidirectional
```

> **HB-51 (cement 2026-06-05):** el formato/estado de una cap está enforced por 8 capas determinísticas (resolver two-way `cap_id↔functional_area` + `make new-cap` generator + schema pydantic + 6 gates G1-G6 HARD en pre-commit/pre-push + `make cap-doctor`). Un header `# cap:` → cap inexistente, o una caja del cockpit vacía, ahora **fallan el commit** (vitalia HARD). SSoT: `docs/process/cap-deterministic-enforcement.md`.

SSoT: `docs/process/capability-protocol.md` § Sec 11-13 (v3.2 cement).

## Voz vitalia

Spanish neutro LatAm (sin voseo) EXCEPTO output de sales_agent que respeta voz tenant (puede ser AR voseo si tenant AR). Tono: profesional cálido. NUNCA infantil, NUNCA hospitalario frío. Brand voice owner: `brand-expert` skill aplicado a config tenant.

## Bootstrap vitalia (fresh clone)

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}
cp vitalia/.env.dev.template vitalia/.env.dev
make dev-vitalia
docker exec luana-dev-vitalia_backend_dev-1 bash -c "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic upgrade head"
curl http://127.0.0.1:8002/health
```

## Referencias

- `vitalia/docs/product/vision.md` — full vision (verticales + HIPAA-lite + competidores + personas + GTM)
- `vitalia/docs/architecture/` — ADRs brand-specific
- `vitalia/docs/learnings/` — captured learnings vitalia
- `core/luana-core-compliance/` — HIPAA-lite engine (prior-art: § Prior-art sources)
- `.claude/rules/anti-duplication-refining.md` — enforcement prior-art scan
- `.claude/rules/claude-md-overlay.md` — schema de este overlay
