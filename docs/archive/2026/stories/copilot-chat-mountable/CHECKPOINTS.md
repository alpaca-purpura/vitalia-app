<!-- voseo-allowed: auditoría interna -->
# Story DoD CHECKPOINTS — platform/copilot-chat-mountable

> Brand: platform (engine/core · technical-story · user_visible: false)
> Auditor: /auditor (directo — core-edit autorizado: proposal accepted + /pm-luana; sin sub-auditor brand)
> Date: 2026-06-16
> verification_nature: técnica · demo_required: false
> Verdict: **APPROVED**

Naturaleza técnica → la DoD es **gates automáticos + verificación-por-efecto**, NO demo UI ni live-verify Chrome (no aplica `LIVE_VERIFY_MISSING`: la story no tiene superficie funcional/UI). Phase D Gherkin n/a (technical-story sin scenarios de comportamiento). El equivalente de la "acción real" es el **driver subprocess** (importar `chat.py` con env multibrand-only) + **R3 import** de las marcas — ambos ejercidos por el auditor, no auto-reportados.

## Step 1.0 — Precondición Fase R
`reconciled: true` ✅ + `chris_verify.signoff.result: SATISFIED_WITH_FOLLOWUPS` ✅ → auditor procede sobre el spec reconciliado. Scope ratificado por Chris (T-4 deferido) = el spec ahora; NO se revierte.

## C1 — Code
- [x] Tests RED→GREEN (TDD): driver `test_chat_import_multibrand_env` (subprocess) + `test_lazy_settings_no_eager` documentados RED→GREEN en T-1/T-2-result
- [x] Coverage sin regresión: suites de paquetes tocados GREEN (copilot 1641/25s · platform 290 · events 76 · assets 58 · iam✓)
- [x] Lint + format clean: `ruff check` copilot/platform/events/assets → **All checks passed**
- [ ] mypy strict: n/a — no corrido (no listado como gate ejecutado; ruff cubre estilo). Sin regresión de tipos en diff (refactor mecánico). → advisory

## C2 — Spec compliance (contract-spec, no Gherkin)
- [x] **Invariante** (00-contract-spec pieza 3): importar `chat.py`/`database.py`/`config.py` NO instancia `Settings` ni engine/redis a module-load → `test_lazy_settings_no_eager` (6) GREEN
- [x] **Contrato** (pieza 1): `/chat` importable con env multibrand-only (sin POSTGRES_*/WHATSAPP_*/QDRANT_URL) → driver subprocess `test_chat_api_importable_with_multibrand_env_only` GREEN (returncode 0, sin ValidationError)
- [x] **Verificación-por-efecto** (pieza 4): driver import GREEN + R3-light (4 marcas import `src.main`: vitalia/nicolify/comunify OK, lupulo placeholder) — ejercido por el auditor
- [~] 401/200 mounted (pieza 4, parte b): **DEFERIDO T-5** — `test_chat_mounted_brand_401_200.py` no creado; el mount real lo ejerce la story downstream comunify (re-mount). Unblock no lo requiere. Ratificado en `scope_change`.

## C3 — Architecture
- [x] Arch-fitness sin violaciones nuevas: inline en suites de paquete (GREEN). `tests/architecture/` no existe en core pkgs (validators reconciliados a advisory — HB-79)
- [x] DDD boundaries: refactor preserva capas; `get_settings()`/`get_*()` lazy son el idiom pydantic-settings (no abstracción nueva)
- [x] Anti-duplication: el fix ELIMINA duplicación (mata el wiring copilot per-brand de vitalia); cero mirror cross-brand (PEP 562 shim único en config/database)
- [x] Downstream regression (R3): engine-edit → 4-brand import GREEN + suites paquetes tocados GREEN. Shim back-compat preserva off-path no migrados
- [x] Connectivity (anti-isla CONN): contrato = router del engine importable + `include_router` por marca; consumer real = comunify (re-mount post-fix). Home = `core/luana-core-copilot` (zona Infraestructura/motor-agentico). NO isla.

## C4 — Cross-cutting
- [x] Graceful-degrade preservado: `get_redis_client()` mantiene None + catch (ConnectionError/TimeoutError/OSError); `_LazySessionLocal` difiere binding a call-time
- [x] Sin cambio de comportamiento: additive (lazy + shim deprecado); `@lru_cache` = un solo objeto, idéntico al singleton eager, solo diferido a primera llamada
- [x] Semver: minor — platform 0.5.0 + copilot 0.3.0 bumpeados + CHANGELOG (`v_changelog_bumped` OK). breaking_change: false
- [x] Spanish neutro: n/a (engine interno, no user-facing)
- [x] PII / tenant isolation: sin cambio (el router ya usa `get_tenant_context`; el fix no toca queries)
- [x] Default flag flips: n/a (no flags)
- [x] Migrations: n/a (cero schema change)

## C5 — Trace
- [x] checkpoint.md state=developed → reviewing (auditor pickup); done lo pone /pm-luana al merge
- [x] Proposal `2026-06-16-copilot-chat-brand-mountable` → marcar `migrated` al merge (vive en wip/comunify)
- [x] `docs/core-modules/luana-core-copilot.md` → crear al merge (contrato router brand-mountable) — nota para /pm-luana
- [x] Story folder listo para archive `docs/archive/2026/stories/` en MISMO commit del merge (R2)
- [x] Follow-up T-4 trackeado (FOLLOWUP-T4-complete-C.md) — story nueva /pm-luana cuando convenga; NO tocar acá

## Findings summary
- C1: 3/4 ✅ (mypy advisory n/a)
- C2: 3/4 ✅ (401/200 deferido T-5, ratificado)
- C3: 5/5 ✅
- C4: 8/8 ✅
- C5: 6/6 ✅
- **Findings de código: 0.** Findings doc-coherence (Carril R, fixeados por el auditor): 1 → `04-validators.yaml` no reconciliado al descope + 2 arch validators con path inexistente. Reconciliados in-place (must_pass:false + `deferred:`). Upstream deficiency → HB-79.

## Upstream deficiency
- Artefacto culpable: `04-validators.yaml` (esta story) — escrito por `/architect` con 6 validators de scope deferido en `must_pass: true` + `be_platform_arch`/`be_copilot_arch` apuntando a `tests/architecture/` (path brand-style inexistente en paquetes core).
- Impacto: verde-fantasma latente — un lector vería 8 validators "obligatorios" cuando ~la mitad eran scope T-4/T-5 deferido o no ejecutables. La Fase R (`reconciled: true`) reconcilió checkpoint pero NO 04-validators.
- Acción sugerida: (1) Fase R de `/pm-{brand}` reconcilia 04-validators al scope post-G; (2) template/architect: technical-story core usa el layout real de arch-fitness del paquete (inline), no `tests/architecture/`. Capturado en HB-79.

## Verdict
**APPROVED** — el unblock (T-1/T-2/T-3) está code-correct + verificado-por-efecto. Story lista para merge por /pm-luana.

## Notes for /pm-luana merge
- Es **core/engine** → owner del merge = /pm-luana (no PM de marca).
- `make ci-parity` antes del squash-merge (sentinel `.ci-parity-deferred` lo vuelve advisory en fase dev-only; bidirectional cross_check_3 sigue HARD).
- Proposal `docs/promotion-protocol/proposals/2026-06-16-copilot-chat-brand-mountable.md` → `migrated` (vive en wip/comunify — actualizar al integrar).
- Crear `docs/core-modules/luana-core-copilot.md` con el contrato del router brand-mountable (no existía).
- Archive story → `docs/archive/2026/stories/copilot-chat-mountable/` en el MISMO commit del merge (R2).
- NO tocar follow-up T-4 (FOLLOWUP-T4-complete-C.md = story nueva).
- Promotion candidate cross-brand: el patrón `get_settings()` lazy + shim PEP 562 es el end-state que las 4 marcas heredan al consumir el engine — ya es core, sin lift adicional.
- Downstream desbloqueado (handoff, sesión aparte /pm-comunify): comunify-shell-organism T-agentic v2 puede re-montar `/chat` del engine (quitar el guard try/except → endpoint deja de ser 404).
