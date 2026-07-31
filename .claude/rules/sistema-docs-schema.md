# Brand Docs Schema — R1+R2+R3+R4

> **Slim pointer (W1-Phase2 eviction 2026-06-09 · tier: project — el modelo 4-ejes es CORE en `lifecycle`).** Detalle completo (schema ASCII, how-to-apply, gitignored inventory, enforcement) en `docs/rules-detail/brand-docs-schema.md`. Aplica a `vitalia/docs/`.

4 reglas hard (1-liners — atomics/outcomes MUERTOS, no reintroducir):
- **R1** — `{brand}/docs/` raíz = SOLO sub-directorios; ningún `.md` suelto.
- **R2** — story `done` → `git mv` a `{brand}/docs/archive/{year}/stories/{id}` en el MISMO commit del 07-merge.
- **R3** — auto-gen (`BACKLOG.*`, portfolio, scans) = gitignored OUTPUT; modificar la SOURCE + regen, NUNCA editar manual.
- **R4** — toda story nace con `chris-input.md` + `checkpoint.md` juntos (pre-commit §16 bloquea).
