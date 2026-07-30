#!/usr/bin/env python3
"""
generate_portfolio.py — Auto-gen docs/portfolio/ desde brand SSoT.

Lee:
- docs/architecture/luana-platform/01-core-audit.md (catálogo brands)
- {brand}/docs/product/checkpoint.md (frontmatter YAML state global brand)
- {brand}/docs/product/BACKLOG.md (extract counts por estado heuristic)
- docs/promotion-protocol/proposals/*.md (proposals abiertas)

Genera (idempotente, overwrite):
- docs/portfolio/PORTFOLIO.md (índice 11 universos en grilla)
- docs/portfolio/{brand}.md (1-pagers por brand) — solo regen si checkpoint cambia
- docs/portfolio/luana.md (1-pager core)

Uso:
    python3 scripts/generate_portfolio.py            # full regen
    python3 scripts/generate_portfolio.py --check    # diff dry-run, exit 1 si stale
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_PORTFOLIO = REPO_ROOT / "docs" / "portfolio"
DOCS_PROMOTION_PROPOSALS = REPO_ROOT / "docs" / "promotion-protocol" / "proposals"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_config as _hc  # noqa: E402 — own script dir put on sys.path above

# Catálogo de universos (1 engine + N brands). STRUCTURAL fields (slug/vertical/status/kind)
# se DERIVAN del seam project.config.yaml (brands[]) — el brand-enum tiene UN solo hogar (W5b ·
# charter §3 DRY): agregar una brand = config en el seam, no editar este script. La NARRATIVA de
# portfolio (cliente/diferenciacion) es contenido single-consumer cohesivo con el renderer (NO
# vive en el seam compartido, que solo aloja slots CORE-consumidos). Agregar una brand nueva =
# (1) entrada en project.config.yaml brands[] + (2) su positioning acá.
_PORTFOLIO_NARRATIVE: dict[str, dict[str, str]] = {
    "luana": {"cliente": "—", "diferenciacion": "27 paquetes luana-core-* + Extension SDK EP-1..EP-18 + cross-cutting concerns"},
    "nicolify": {"cliente": "Agencias marketing, software boutique, consultoras", "diferenciacion": "CRM ciclo largo · portal cliente · propuestas/contratos · horas facturables"},
    "vitalia": {"cliente": "Clínicas médicas, dentales, estéticas", "diferenciacion": "Reservas prepagadas · historial médico · HIPAA-lite · seguimiento post-tratamiento"},
    "comunify": {"cliente": "Coaches, creadores contenido, infoproductores", "diferenciacion": "Escalera valor · bóveda autoridad · motor comunidad · embudos venta"},
    "lupulo": {"cliente": "Restaurantes, bares, cafeterías", "diferenciacion": "Reservas mesa · pedidos digitales · integración KDS via agentes IA"},
    "saasora": {"cliente": "Startups tech, micro-SaaS, software", "diferenciacion": "Onboarding automatizado · subscripciones Stripe · dashboards Churn/MRR · changelogs"},
    "inmoflow": {"cliente": "Brokers, agencias inmobiliarias", "diferenciacion": "Integración portales · mapas interactivos · lead routing por zona · calculadoras financieras"},
    "retailly": {"cliente": "Tiendas online, marcas físicas", "diferenciacion": "Catálogos dinámicos · cart recovery · integración logística · cross-selling checkout"},
    "fixia": {"cliente": "Plomeros, electricistas, HVAC, contractors", "diferenciacion": "Técnicos en campo · cotización on-site · reseñas locales SEO automatizadas"},
    "guestly": {"cliente": "Hoteles boutique, rentas vacacionales, tours", "diferenciacion": "Motor reservas estacional · sync OTAs (Airbnb/Booking) · guest experience"},
    "fitflow": {"cliente": "Gimnasios, estudios yoga, boxes", "diferenciacion": "Facturación recurrente · control aforo · calendario clases · waivers"},
}
_NARRATIVE_FALLBACK = {"cliente": "—", "diferenciacion": "—"}


def _build_universes() -> list[dict[str, Any]]:
    """Build the universe catalog: the engine (luana) + every brand from the seam.

    slug/vertical/status/kind come from project.config.yaml brands[] (ONE home for the enum);
    cliente/diferenciacion from the local narrative map (cohesive presentation content).
    """
    brands = _hc.get("brands")
    rows: list[dict[str, Any]] = [
        {
            "slug": "luana",
            "kind": "core",
            "vertical": "Engine compartido (no consumidor)",
            "status_default": "active",
            **_PORTFOLIO_NARRATIVE["luana"],
        }
    ]
    for b in brands.get("active", []):
        rows.append(
            {
                "slug": b["slug"],
                "kind": "brand",
                "vertical": b["vertical"],
                "status_default": b["status"],
                **_PORTFOLIO_NARRATIVE.get(b["slug"], _NARRATIVE_FALLBACK),
            }
        )
    for b in brands.get("pending_bootstrap", []):
        rows.append(
            {
                "slug": b["slug"],
                "kind": "brand",
                "vertical": b["vertical"],
                "status_default": "pending-bootstrap",
                **_PORTFOLIO_NARRATIVE.get(b["slug"], _NARRATIVE_FALLBACK),
            }
        )
    return rows


UNIVERSES: list[dict[str, Any]] = _build_universes()

STATUS_EMOJI = {
    "active": "🟢",
    "shipped": "✅",
    "placeholder": "🟡",
    "pending-bootstrap": "⏳",
    "blocked": "🚧",
}


def parse_frontmatter(content: str) -> dict[str, Any]:
    """Extract YAML frontmatter from markdown. Returns {} if absent or malformed."""
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    fm: dict[str, Any] = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm


def read_brand_checkpoint(slug: str) -> dict[str, Any]:
    """Read {brand}/docs/product/checkpoint.md frontmatter."""
    path = REPO_ROOT / slug / "docs" / "product" / "checkpoint.md"
    if not path.exists():
        return {}
    return parse_frontmatter(path.read_text(encoding="utf-8"))


def count_proposals_by_state() -> dict[str, int]:
    """Count promotion proposals grouped by state."""
    counts = {"proposed": 0, "under_review": 0, "accepted": 0, "rejected": 0, "migrated": 0}
    if not DOCS_PROMOTION_PROPOSALS.exists():
        return counts
    for proposal_file in DOCS_PROMOTION_PROPOSALS.glob("*.md"):
        if proposal_file.stem.startswith("EXAMPLE"):
            continue  # Ejemplos no cuentan
        fm = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
        state = fm.get("state", "proposed")
        counts[state] = counts.get(state, 0) + 1
    return counts


def render_portfolio_md(today: str) -> str:
    """Render docs/portfolio/PORTFOLIO.md (índice grilla 11 universos)."""
    lines = [
        "<!-- AUTO-GENERATED por scripts/generate_portfolio.py — NO editar a mano -->",
        "<!-- Para regenerar: make portfolio -->",
        "",
        "# Portfolio Luana — 11 universos",
        "",
        "> Vista master del portfolio. Pointer-first: cada entrada apunta a SSoT vivo en `docs/portfolio/{slug}.md` (1-pager) y `{brand}/docs/product/checkpoint.md` (state actual).",
        ">",
        "> **Filosofía:** este file no contiene contenido — solo punteros. El detalle vive donde nace.",
        "",
        "---",
        "",
    ]

    # Núcleo
    luana = UNIVERSES[0]
    lines += [
        "## Núcleo",
        "",
        "| Slug | Tipo | Estado | 1-pager | SSoT live |",
        "|---|---|---|---|---|",
        f"| {luana['slug']} | {luana['kind']} | {STATUS_EMOJI['active']} active | [docs/portfolio/{luana['slug']}.md](./{luana['slug']}.md) | [docs/product/](../product/) + [docs/core-modules/](../core-modules/) |",
        "",
    ]

    # Brands shipped
    shipped = [u for u in UNIVERSES if u["kind"] == "brand" and u["status_default"] == "shipped"]
    if shipped:
        lines += [
            "## Brands shipped",
            "",
            "| Slug | Vertical | Estado actual | 1-pager | SSoT live |",
            "|---|---|---|---|---|",
        ]
        for u in shipped:
            cp = read_brand_checkpoint(u["slug"])
            status_actual = cp.get("status", u["status_default"])
            emoji = STATUS_EMOJI.get(status_actual, "")
            lines.append(
                f"| {u['slug']} | {u['vertical']} | {emoji} {status_actual} | "
                f"[{u['slug']}.md](./{u['slug']}.md) | "
                f"[{u['slug']}/docs/product/](../../{u['slug']}/docs/product/) |"
            )
        lines.append("")

    # Brands placeholder
    placeholder = [u for u in UNIVERSES if u["kind"] == "brand" and u["status_default"] == "placeholder"]
    if placeholder:
        lines += [
            "## Brands placeholder",
            "",
            "| Slug | Vertical | Estado actual | 1-pager | SSoT live |",
            "|---|---|---|---|---|",
        ]
        for u in placeholder:
            cp = read_brand_checkpoint(u["slug"])
            status_actual = cp.get("status", u["status_default"])
            emoji = STATUS_EMOJI.get(status_actual, "")
            lines.append(
                f"| {u['slug']} | {u['vertical']} | {emoji} {status_actual} | "
                f"[{u['slug']}.md](./{u['slug']}.md) | "
                f"[{u['slug']}/docs/product/](../../{u['slug']}/docs/product/) |"
            )
        lines.append("")

    # Brands pendientes bootstrap
    pending = [u for u in UNIVERSES if u["kind"] == "brand" and u["status_default"] == "pending-bootstrap"]
    if pending:
        lines += [
            "## Brands pendientes bootstrap",
            "",
            "| Slug | Vertical | Estado | Bootstrap target |",
            "|---|---|---|---|",
        ]
        for u in pending:
            lines.append(
                f"| {u['slug']} | {u['vertical']} | {STATUS_EMOJI['pending-bootstrap']} pending | "
                f"template `_pm-sistema-template/` |"
            )
        lines.append("")

    # Promotion proposals
    proposals = count_proposals_by_state()
    total_open = proposals["proposed"] + proposals["under_review"] + proposals["accepted"]
    lines += [
        "---",
        "",
        "## Promotion proposals",
        "",
        "> Patrones brand candidatos a lift a luana-core. Lifecycle: proposed → under_review → accepted/rejected → migrated.",
        "",
        f"- **Open:** {total_open} (proposed: {proposals['proposed']}, under_review: {proposals['under_review']}, accepted: {proposals['accepted']})",
        f"- **Migrated:** {proposals['migrated']}",
        f"- **Rejected (archive):** {proposals['rejected']}",
        "",
        "Ver [docs/promotion-protocol/proposals/](../promotion-protocol/proposals/).",
        "",
        "---",
        "",
        f"**Última regen:** {today} (auto via `make portfolio`).",
        "",
    ]
    return "\n".join(lines)


def render_brand_1pager(u: dict[str, Any], today: str) -> str:
    """Render docs/portfolio/{slug}.md 1-pager para brand."""
    slug = u["slug"]
    cp = read_brand_checkpoint(slug)
    status_actual = cp.get("status", u["status_default"])

    if u["kind"] == "core":
        return render_luana_1pager(today, status_actual)

    return f"""---
slug: {slug}
kind: brand
status: {status_actual}
vertical: "{u['vertical']}"
last_updated: {today}
ssot_live:
  - {slug}/docs/product/
  - {slug}/docs/domains/
  - {slug}/docs/learnings/
  - {slug}/docs/architecture/
owner: /pm-{slug}
---

# {slug.capitalize()} — {u['vertical']}

> 1-pager pointer. Detalle vivo en `{slug}/docs/`.

## Vertical

{u['vertical']}

## Cliente objetivo

{u['cliente']}

## Diferenciación core

{u['diferenciacion']}

## Estado

`{status_actual}`

## Surfaces

| Tipo | Path |
|---|---|
| Backlog | [{slug}/docs/product/BACKLOG.md](../../{slug}/docs/product/BACKLOG.md) |
| Releases | [{slug}/docs/product/releases/](../../{slug}/docs/product/releases/) |
| Stories | [{slug}/docs/product/stories/](../../{slug}/docs/product/stories/) |
| Capabilities | [{slug}/docs/product/capabilities/](../../{slug}/docs/product/capabilities/) |
| Modules | [{slug}/docs/product/modules/](../../{slug}/docs/product/modules/) |
| Domains | [{slug}/docs/domains/](../../{slug}/docs/domains/) |
| Learnings | [{slug}/docs/learnings/](../../{slug}/docs/learnings/) |
| Architecture (ADRs locales) | [{slug}/docs/architecture/](../../{slug}/docs/architecture/) |
| Brand config | [{slug}/config/](../../{slug}/config/) |
| Code BE | [{slug}/backend/](../../{slug}/backend/) |
| Code FE | [{slug}/frontend/](../../{slug}/frontend/) |

## Ownership

- `/pm-{slug}` (skill) — owner backlog, releases, stories
- `/pm` (master) — visibility cross-portfolio

## Drill-down

`cat {slug}/docs/product/checkpoint.md` para state actual.
"""


def render_luana_1pager(today: str, status: str) -> str:
    """Render docs/portfolio/luana.md 1-pager core."""
    proposals = count_proposals_by_state()
    return f"""---
slug: luana
kind: core
status: {status}
last_updated: {today}
ssot_live:
  - docs/product/
  - docs/core-modules/
  - docs/promotion-protocol/
  - docs/architecture/luana-platform/
owner: /pm-luana
---

# Luana — core engine

> El núcleo compartido del portfolio. NO es brand consumidora — es la "constitución" sobre la que las 10 brands construyen.

## Razón de existir

Acelerar dev cross-brand. Cada brand aporta aprendizaje → core captura abstracciones reutilizables → nuevas brands arrancan ya con superpoderes acumulados.

## Surfaces

| Tipo | Path | Descripción |
|---|---|---|
| Engine packages | [`core/luana-core-*`](../../core/) | 26 paquetes Python + TS publicables |
| Extension SDK | `core/luana-core-extension-sdk/` | EP-1..EP-18 contracts |
| Cross-cutting concerns | [`docs/core-modules/`](../core-modules/) | 22 transversales |
| Promotion protocol | [`docs/promotion-protocol/`](../promotion-protocol/) | brand→core lift gate |

## Promotion proposals (live)

- Proposed: {proposals['proposed']}
- Under review: {proposals['under_review']}
- Accepted (lift programado): {proposals['accepted']}
- Migrated (cerrados OK): {proposals['migrated']}
- Rejected (archive): {proposals['rejected']}

## State portfolio

- 26 packages extraídos
- 4 brands consumidoras (3 shipped: Nicolify, Vitalia, Comunify + 1 placeholder: Lupulo)
- 6 pendientes bootstrap (SaaSora, InmoFlow, Retailly, Fixia, Guestly, FitFlow)

## Ownership

- `/pm-luana` (skill) — owner promotion gate, semver, breaking changes, EPs
- `/pm` (master) — orquesta visibility cross-portfolio

## Drill-down

- Roadmap platform: `docs/product/outcomes/`
- Promotion candidates: `docs/promotion-protocol/proposals/`
- Plan multibrand original: `docs/architecture/luana-platform/01-core-audit.md`
- Purge audit: `docs/architecture/luana-platform/02-core-purge-audit.md`
"""


def regen_all(check_only: bool = False) -> int:
    """Regen full portfolio. Returns 0 if no changes (or check OK), 1 if stale."""
    today = date.today().isoformat()
    DOCS_PORTFOLIO.mkdir(parents=True, exist_ok=True)

    files_to_write: dict[Path, str] = {
        DOCS_PORTFOLIO / "PORTFOLIO.md": render_portfolio_md(today),
    }
    for u in UNIVERSES:
        files_to_write[DOCS_PORTFOLIO / f"{u['slug']}.md"] = render_brand_1pager(u, today)

    stale = False
    for path, content in files_to_write.items():
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        if existing.strip() != content.strip():
            stale = True
            if not check_only:
                path.write_text(content, encoding="utf-8")
                print(f"regen: {path.relative_to(REPO_ROOT)}")
            else:
                print(f"stale: {path.relative_to(REPO_ROOT)}")

    if check_only and stale:
        print("\nERROR: portfolio is stale. Run: python3 scripts/generate_portfolio.py", file=sys.stderr)
        return 1
    if not stale and not check_only:
        print("portfolio: nothing to regen (already fresh)")
    return 0


if __name__ == "__main__":
    check = "--check" in sys.argv
    sys.exit(regen_all(check_only=check))
