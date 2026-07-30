# Célula · P2 · DEVHUB (ex "Cockpit SDLC") — ⚠ CONGELADA (DH-11, 2026-07-04)

> **GRADUADA a repo propio: `~/Proyectos/devhub` (`alpacapurpura/devhub`).** Esta célula es
> fuente READ-ONLY del port gradual — nada nuevo se desarrolla aquí. Fichas DH-12+ viven allá.

Célula de producto **estanca** (I-69): visión, roadmap y ledger propios. Norte = [`VISION.md`](./VISION.md) · registro = [`LEDGER.md`](./LEDGER.md) (fichas `DH-NN`). Ecosistema: `tooling/strategy/PRODUCT-VISION.md §1.3`.

**Qué es:** el sistema de **gestión del desarrollo** — visualiza y gestiona el ciclo de vida completo del software (multi-sistema, multi-proyecto, multi-rol).

**Código:** `go/` (binario, UI embebida vía `go:embed` — build `go/build.sh`) + `ui/` (Next.js — se compila con `go/build-ui.sh`). ⚠ El binario y el CLI aún se llaman `cockpit` (rename comercial = pendiente, DH-01). Corte físico de P1 completo (CK-08, 2026-07-02): Cockpit corre como binario/app independiente (`products/cockpit/`, puerto 4100) — cero import cruzado, cero alias, cero route-group compartido con DevHub. Historia de la extracción: `products/cockpit/LEDGER.md` (CK-01..CK-08).
