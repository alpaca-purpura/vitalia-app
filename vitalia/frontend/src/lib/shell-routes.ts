// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase2-s7-TBD
/**
 * shell-routes.ts — Sub-sub-tab (N3-static) routing catalog for ADR-vitalia-004 v1.1.
 *
 * AGENT_SUBSUBTABS: maps `{agent}.{subtab}` → ordered array of N3 sub-sub-tab descriptors.
 * Only entries with N3-static routes (page.tsx files) live here. Subtabs without N3
 * (dispatcher-rendered or placeholder) are NOT listed.
 *
 * Consumed by:
 *   - SubSubTabsBar (components/shared/shell-organism/SubSubTabsBar.tsx)
 *     → renders the N3 navigation strip between SubTabsBar and page content
 *   - Architecture fitness test (src/__tests__/architecture/test_agent_subsubtabs_ssot.test.ts)
 *
 * Naming convention: SubSubTabMeta mirrors SubTabMeta from agent-catalog.ts.
 *
 * ADR reference: ADR-vitalia-004 v1.1 — N3-static SubSubTabsBar pattern.
 * ANTI-PATTERN GUARD: Sub-sub-tabs MUST be static segments (e.g. /lisa/marca/identidad).
 * NEVER use Shadcn <Tabs> body inside a sub-tab view to group conceptually discrete
 * sub-sections — that is the Nivel 4 anti-pattern prohibited by ADR-vitalia-004 v1.1.
 *
 * T-4 vitalia-fase2-lisa-marca
 * spec_anchor: ADR-vitalia-004 v1.1 § 3.1.1 + 03-arch.md § T-4
 * downstream-regression-na: brand-local vitalia shell catalog; no cross-brand consumers
 */

/**
 * DEFAULT_LANDING_SUBPATH — SSoT del subpath de aterrizaje post-login del shell.
 *
 * Bug #1 fix (vitalia-bugfix-shell-nav-scroll-errors T-1): la agenda migró de
 * `valeria/agenda` → `mateo/agenda` (paradigm-map-zones T-5, v1.2 2026-05-30) pero
 * 3 redirects siguieron apuntando a `valeria/agenda`. Como `isValidAgent('valeria')
 * === false` (Valeria es supervisora sidebar, NO ribbon agent), esa ruta cae en el
 * dinámico `[agent]/layout.tsx` → `notFound()` → 404.
 *
 * `mateo/agenda` SÍ es ruta estática real (SHIPPED_STATIC_SUBTABS en agent-catalog.ts)
 * que renderiza `mateo/agenda/page.tsx` directamente sin pasar por isValidAgent.
 *
 * Un único const consumido por los 3 redirects evita que vuelva a driftear:
 *   - app/page.tsx (root landing post-login)
 *   - (shell-organism)/page.tsx (/{tenantId} → default)
 *   - (shell-organism)/layout.tsx (redirect cross-tenant inválido → primer tenant válido)
 *
 * NOTA: NO incluye el `/{tenantId}` prefix — el caller lo antepone
 * (`/${tenantId}/${DEFAULT_LANDING_SUBPATH}`).
 */
export const DEFAULT_LANDING_SUBPATH = "mateo/agenda" as const;

/**
 * BARE_TENANT_PATH — matches a path that is EXACTLY one tenant-UUID segment
 * (e.g. `/e69a691d-070e-5caf-a053-6e74642ec100`), optional trailing slash.
 *
 * UUID-only on purpose: never matches `/sign-in`, `/sign-out`, `/marketing`,
 * `/public`, etc. (those are non-UUID single segments).
 */
export const BARE_TENANT_PATH = /^\/([0-9a-f-]{36})\/?$/i;

/**
 * Returns the edge-redirect target for a BARE tenant path
 * (`/{uuid}` → `/{uuid}/${DEFAULT_LANDING_SUBPATH}`), or `null` if `pathname`
 * is not a bare tenant path.
 *
 * Bug #1 hardening (vitalia-bugfix-shell-nav-scroll-errors): proxy.ts consumes
 * this to redirect at the EDGE (HTTP 307) instead of letting the Server Component
 * `(shell-organism)/page.tsx` do an in-route-group `redirect()`. That in-group
 * redirect triggers a Next.js 16.2.3 client-Router soft-navigation that throws
 * "Rendered more hooks than during the previous render" (~40% flake). A fresh
 * edge redirect makes the browser load the destination cleanly. See proxy.ts.
 */
export function bareTenantLandingRedirect(pathname: string): string | null {
  const match = pathname.match(BARE_TENANT_PATH);
  return match ? `/${match[1]}/${DEFAULT_LANDING_SUBPATH}` : null;
}

/**
 * TENANT_UUID — a single tenant-UUID segment (no leading slash). Used to
 * validate the tenant resolved from Clerk publicMetadata BEFORE building a
 * root-landing redirect. Mirrors BARE_TENANT_PATH's UUID shape so the edge
 * never 307s to a non-UUID (e.g. a Clerk Org id `org_xxx`) that would 500 the
 * shell layout. See MEMORY.md::no-clerk-organizations.
 */
const TENANT_UUID = /^[0-9a-f-]{36}$/i;

/**
 * isAuthedRootPath — true iff `pathname` is the EXACT site root (`/`).
 *
 * Scoped HARD on purpose: the root edge-redirect (root-login-redirect-softnav)
 * must fire ONLY for `/` so we never resolve the tenant (a Clerk Backend API
 * call) on every request. Any path with a segment (`/sign-in`, `/{uuid}/...`,
 * `/marketing`) returns false and falls through to the normal flow.
 */
export function isAuthedRootPath(pathname: string): boolean {
  return pathname === "/";
}

/**
 * rootLandingRedirect — builds the edge-redirect target for an authenticated
 * user hitting the site root (`/`): `/{tenantId}/${DEFAULT_LANDING_SUBPATH}`.
 *
 * Bug fix (vitalia-bugfix-root-login-redirect-softnav): Clerk afterSignIn sends
 * the user client-side to `/`, where the Server Component `app/page.tsx` did an
 * in-render `redirect()` INTO the `(shell-organism)` route group whose layout is
 * `dynamic({ssr:false})`. That soft-navigation triggers Next 16's
 * "Rendered more hooks than during the previous render" (~40% flake → hung
 * render until a manual refresh). Doing the redirect at the EDGE (HTTP 307)
 * before `app/page.tsx` renders eliminates the soft-nav: the browser loads the
 * destination with a fresh request → the Router mounts cleanly. Same pattern as
 * `bareTenantLandingRedirect` / `shellInRenderRedirectTarget`. See proxy.ts +
 * learning 2026-06-03-next16-softnav-redirect-rendered-more-hooks.
 *
 * Returns `null` when no tenant is resolved OR the resolved tenant is not a UUID
 * — in that case the proxy lets `app/page.tsx` run its full fallback
 * (fetchUserTenants → no_tenants_assigned / network-error handling). We never
 * 307 to a non-UUID (would 500 the shell layout). `app/page.tsx` stays as the
 * defensive fallback for the cold-publicMetadata / non-UUID edge.
 *
 * @param tenantId - tenant UUID resolved from Clerk `publicMetadata.tenant_id`
 *                   (server-side, via clerkClient) — `null`/`undefined`/`""`
 *                   when not yet provisioned or unresolvable at the edge.
 */
export function rootLandingRedirect(
  tenantId: string | null | undefined,
): string | null {
  if (!tenantId || !TENANT_UUID.test(tenantId)) {
    return null;
  }
  return `/${tenantId}/${DEFAULT_LANDING_SUBPATH}`;
}

// ── Edge redirects para los redirect() in-render del shell (T-V2 lift 2026-06-11) ──
//
// El censo del lift (platform-lift-shell-chrome-ui-kit T-V2) encontró que el
// supuesto del hardening "0 redirects in-render fuera del landing" era FALSO:
// existen 4 redirect() server in-render intra-route-group (lisa/marca → identidad,
// [agent] bare → defaultSubtab, staff/[doctor-id] → perfil, embudo/[leadId] →
// resumen). Con el chrome consumido del kit, el trigger del learning
// 2026-06-03-next16-softnav-redirect-rendered-more-hooks pasó de flaky (~40%)
// a DETERMINISTA → mover TODOS al edge (mismo patrón Decisión A). Los
// page.tsx con redirect() quedan como fallback defensivo (tenant no-UUID).

const UUID_SEG = "[0-9a-f-]{36}";

/** N3-static defaults: ruta sin leaf → leaf default (SSoT junto a AGENT_SUBSUBTABS). */
const N3_DEFAULT_LEAF: ReadonlyArray<readonly [RegExp, string]> = [
  [new RegExp(`^/(${UUID_SEG})/lisa/marca/?$`, "i"), "identidad"],
  [new RegExp(`^/(${UUID_SEG})/lisa/staff/(${UUID_SEG})/?$`, "i"), "perfil"],
  [new RegExp(`^/(${UUID_SEG})/adrian/embudo/(${UUID_SEG})/?$`, "i"), "resumen"],
  // T-1 vitalia-fase2-config-cuenta — config.cuenta N3-static default leaf
  [new RegExp(`^/(${UUID_SEG})/config/cuenta/?$`, "i"), "datos"],
  // T-6 vitalia-fase2-lisa-servicios — lisa.servicios N3-static default leaf
  [new RegExp(`^/(${UUID_SEG})/lisa/servicios/?$`, "i"), "catalogo"],
  // G2-F5 vitalia-fase2-lisa-servicios — bare [offer-id] workspace → resumen leaf.
  // Edge-redirect (HTTP 307) so the soft-nav never hits the Server Component
  // redirect() in-render, which throws the Next 16.2.x perf-measure / Router error
  // (learning 2026-06-03-next16-softnav-redirect). Same shape as adrian/embudo/{uuid}.
  [new RegExp(`^/(${UUID_SEG})/lisa/servicios/(${UUID_SEG})/?$`, "i"), "resumen"],
];

/** Agente bare (`/{uuid}/{agent}`) → su defaultSubtab (espejo de [agent]/page.tsx). */
const BARE_AGENT_PATH = new RegExp(`^/(${UUID_SEG})/([a-z]+)/?$`, "i");

/** defaultSubtab por agente — espejo del AGENT_CATALOG (mantener sincronizado;
 *  el fallback in-render de [agent]/page.tsx cubre cualquier drift). */
const AGENT_DEFAULT_SUBTAB: Readonly<Record<string, string>> = {
  lisa: "marca",
  valeria: "agenda",
  adrian: "inbox",
  lucas: "lanzar",
  camila: "voz",
  mateo: "agenda",
};

/**
 * Returns the edge-redirect target for shell paths whose page.tsx would do an
 * in-render `redirect()` (N3-static default leaf / bare agent default subtab),
 * or `null` when `pathname` needs no redirect.
 */
export function shellInRenderRedirectTarget(pathname: string): string | null {
  for (const [re, leaf] of N3_DEFAULT_LEAF) {
    if (re.test(pathname)) {
      return `${pathname.replace(/\/$/, "")}/${leaf}`;
    }
  }
  const agentMatch = pathname.match(BARE_AGENT_PATH);
  if (agentMatch) {
    const agent = agentMatch[2].toLowerCase();
    const subtab = AGENT_DEFAULT_SUBTAB[agent];
    if (subtab) {
      return `/${agentMatch[1]}/${agent}/${subtab}`;
    }
  }
  return null;
}

export interface SubSubTabMeta {
  /** URL segment identifier — kebab-case static segment (e.g., "identidad", "voz-y-tono"). */
  id: string;
  /** Visible label — Spanish neutro LatAm, sin voseo. */
  label: string;
  /** Emoji icon for the sub-sub-tab. */
  icon: string;
}

/**
 * Sub-sub-tab catalog — keyed by `{agent}.{subtab}` composite.
 *
 * Only entries that have actual static page.tsx routes live here.
 * When a new story adds N3-static routing, extend this record — do NOT hardcode
 * sub-sub-tab lists inside any component (arch test enforces this file as SSoT).
 *
 * Current entries:
 *   - lisa.marca → 3 sub-sub-tabs: identidad · voz-y-tono · presencia (T-4 F2-S7)
 *   - lisa.servicios → 2 sub-sub-tabs: catalogo · escalera (T-6 lisa-servicios)
 *   - config.cuenta → 3 sub-sub-tabs: datos · preferencias · responsable (T-1 config-cuenta)
 */
export const AGENT_SUBSUBTABS: Partial<
  Record<`${string}.${string}`, readonly SubSubTabMeta[]>
> = {
  "lisa.marca": [
    { id: "identidad", label: "Identidad", icon: "🏥" },
    { id: "voz-y-tono", label: "Voz y tono", icon: "🎙️" },
    { id: "presencia", label: "Presencia", icon: "📍" },
  ],
  // T-6 vitalia-fase2-lisa-servicios — Servicios N3-static sub-sub-tabs
  "lisa.servicios": [
    { id: "catalogo", label: "Catálogo", icon: "📋" },
    { id: "escalera", label: "Escalera", icon: "🪜" },
  ],
  // T-1 vitalia-fase2-config-cuenta — Mi cuenta N3-static sub-sub-tabs
  "config.cuenta": [
    { id: "datos", label: "Datos", icon: "🏢" },
    { id: "preferencias", label: "Preferencias", icon: "⚙️" },
    { id: "responsable", label: "Responsable", icon: "🔐" },
  ],
} as const;

/**
 * Returns the sub-sub-tabs for a given agent.subtab combo, or null if none.
 * Used by SubSubTabsBar and page.tsx redirects.
 */
export function getSubSubTabs(
  agent: string,
  subtab: string,
): readonly SubSubTabMeta[] | null {
  const key = `${agent}.${subtab}` as `${string}.${string}`;
  return AGENT_SUBSUBTABS[key] ?? null;
}

/**
 * Returns the default (first) sub-sub-tab id for a given agent.subtab combo.
 * Returns null if no sub-sub-tabs exist for this combo.
 */
export function getDefaultSubSubTab(
  agent: string,
  subtab: string,
): string | null {
  const subsubtabs = getSubSubTabs(agent, subtab);
  return subsubtabs?.[0]?.id ?? null;
}
