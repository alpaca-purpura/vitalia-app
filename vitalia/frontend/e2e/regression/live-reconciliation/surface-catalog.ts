// cap: ops.live-reconciliation-sweep
// story-origin: vitalia-cockpit-live-reconciliation
/**
 * surface-catalog.ts — Catalogo de superficies navegables derivado del SSoT.
 *
 * Deriva las superficies desde:
 *   1. RIBBON_SUBTABS + AGENT_SUBSUBTABS (shell-routes.ts + agent-catalog.ts)
 *   2. Rutas app/**\/page.tsx conocidas (estáticas declaradas)
 *   3. 3 externas anotadas (admin Streamlit / public clinica / onboarding wizard)
 *
 * NUNCA hardcodea la lista de rutas shell — la lee del SSoT.
 *
 * Type Surface:
 *   capId?:      cap_id asociado (null si no hay mapeo directo)
 *   agent:       slug del agente ribbon (o "auth"|"public"|"infra")
 *   subtab?:     slug del sub-tab (si aplica)
 *   subsubtab?:  slug del sub-sub-tab N3-static (si aplica)
 *   route:       ruta con :tenantId sustituido por placeholder "$TENANT_ID"
 *   kind:        'shell' (barrido profundo) | 'external-annotated' (solo anotar)
 *
 * Heurística agent/subtab → cap_id:
 *   - valeria.agenda       → "scheduling.valeria-agenda"
 *   - lisa.marca           → "brand_studio.lisa-marca"
 *   - lisa.marca.identidad → "brand_studio.lisa-marca"  (subsubtab del mismo cap)
 *   - auth                 → "auth.sign-in-sign-up-pages"
 *   - shell-organism root  → "shell-organism.routing"
 *   - config.*             → null (no cap específica aún)
 *   - infra                → null (infra-only, no cap nav directa)
 *
 * downstream-regression-na: brand-local vitalia sweep harness; no cross-brand consumers
 * voseo-allowed: internal dev tooling docs
 */

import type { RIBBON_SUBTABS } from "../../../src/lib/agent-catalog";
import { AGENT_RIBBON_ORDER } from "../../../src/lib/agent-catalog";

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface Surface {
  /** Cap ID in format "module.slug" — null if no direct cap mapping */
  capId: string | null;
  /** Agent slug (ribbon agent, "auth", "public", "infra", "test-stack") */
  agent: string;
  /** Sub-tab slug (if applicable) */
  subtab?: string;
  /** Sub-sub-tab slug N3-static (if applicable) */
  subsubtab?: string;
  /** Route with tenantId as literal "$TENANT_ID" placeholder */
  route: string;
  /** 'shell' = deep sweep | 'external-annotated' = annotate only, no deep scan */
  kind: "shell" | "external-annotated";
  /** Human-readable label for reporting */
  label: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Cap-ID heuristic mapping table
// Maps "agent.subtab" (or "agent.subtab.subsubtab") → cap_id
// ─────────────────────────────────────────────────────────────────────────────

const CAP_MAP: Record<string, string> = {
  // shell-organism structure caps (foundation)
  "shell-organism.root": "shell-organism.routing",
  "shell-organism.ribbon": "shell-organism.ribbon",
  "shell-organism.sub-tabs": "shell-organism.sub-tabs",
  // valeria
  "valeria.agenda": "scheduling.valeria-agenda",
  "valeria.pacientes": "patients.patient-records-medical-history",
  // lisa
  "lisa.marca": "brand_studio.lisa-marca",
  "lisa.marca.identidad": "brand_studio.lisa-marca",
  "lisa.marca.voz-y-tono": "brand_studio.lisa-marca",
  "lisa.marca.presencia": "brand_studio.lisa-marca",
  "lisa.doctores": "clinics.clinics-brand-extension",
  "lisa.servicios": "offer_studio.medical-services-offer-preset",
  "lisa.compliance": "compliance.compliance-hipaa-lite-audit",
  // adrian
  "adrian.inbox": "sales_agent.inbox-handler-mode-occ",
  "adrian.embudo": "sales_agent.adrian-3-tools-mvp",
  "adrian.outbound": "marketing.bowtie-funnel-5-stages",
  "adrian.propuestas": "sales_agent.state-overlay-langgraph",
  // lucas
  "lucas.lanzar": "marketing.lucas-stage-recommendations",
  "lucas.envuelo": "marketing.attribution-matrix-4-origins",
  "lucas.recursos": "marketing.bowtie-funnel-5-stages",
  "lucas.resultados": "marketing.attribution-matrix-4-origins",
  "lucas.mercado": "marketing.lucas-recommendation-tool",
  // camila
  "camila.voz": "patients.nps-tracking",
  "camila.reactivar": "treatments.treatment-followup-workflow",
  "camila.multiplicar": "marketing.referrals-leaderboard",
  "camila.reputacion": "patients.nps-tracking",
  // config
  "config.cuenta": "iam.luana-core-adoption",
  "config.conexiones": "connections.oauth-meta-google-ads",
  "config.avanzado": "iam.iam-scaffold-slice-1",
  // auth
  "auth.sign-in": "auth.sign-in-sign-up-pages",
  "auth.sign-up": "auth.sign-in-sign-up-pages",
} as const;

/**
 * surfaceToCapId — heurística agent/subtab → cap_id.
 *
 * Lookup order:
 *   1. Exact match "agent.subtab.subsubtab" (N3-static)
 *   2. Exact match "agent.subtab"
 *   3. Exact match "agent" (solo agent, sin subtab)
 *   4. null (no mapping known)
 */
export function surfaceToCapId(s: Surface): string | null {
  if (s.capId !== null) return s.capId; // pre-computed override
  const key3 = `${s.agent}.${s.subtab ?? ""}.${s.subsubtab ?? ""}`;
  const key2 = `${s.agent}.${s.subtab ?? ""}`;
  const key1 = s.agent;
  return CAP_MAP[key3] ?? CAP_MAP[key2] ?? CAP_MAP[key1] ?? null;
}

// ─────────────────────────────────────────────────────────────────────────────
// Surface enumeration
// ─────────────────────────────────────────────────────────────────────────────

/**
 * enumerateNavigableSurfaces — deriva superficies del SSoT en runtime.
 *
 * Requiere un tenantId para construir rutas concretas.
 * El placeholder "$TENANT_ID" se sustituye por el tenantId real en sweep.spec.ts.
 */
export function enumerateNavigableSurfaces(
  tenantId: string = "$TENANT_ID",
): Surface[] {
  const surfaces: Surface[] = [];

  // ── 1. Auth surfaces ────────────────────────────────────────────────────
  surfaces.push({
    capId: "auth.sign-in-sign-up-pages",
    agent: "auth",
    route: "/sign-in",
    kind: "shell",
    label: "Iniciar sesión",
  });

  // ── 2. Shell-organism root (redirect to default agent/subtab) ───────────
  surfaces.push({
    capId: "shell-organism.routing",
    agent: "shell-organism",
    route: `/${tenantId}`,
    kind: "shell",
    label: "Shell organism — raíz tenant",
  });

  // ── 3. Agent ribbon subtabs (RIBBON_SUBTABS × AGENT_RIBBON_ORDER) ───────
  // Import dynamically to stay runtime-safe (browser + node compatible)
  const agentCatalogModule = _loadAgentCatalog();
  const ribbonSubtabs = agentCatalogModule.RIBBON_SUBTABS;
  const agentSubsubtabs = _loadShellRoutes().AGENT_SUBSUBTABS;

  for (const agentSlug of AGENT_RIBBON_ORDER) {
    const subtabs = (ribbonSubtabs as typeof RIBBON_SUBTABS)[agentSlug] ?? [];

    for (const subtab of subtabs) {
      // Sub-tab base surface
      const baseSurface: Surface = {
        capId: CAP_MAP[`${agentSlug}.${subtab.id}`] ?? null,
        agent: agentSlug,
        subtab: subtab.id,
        route: `/${tenantId}/${agentSlug}/${subtab.id}`,
        kind: "shell",
        label: `${agentCatalogModule.AGENT_CATALOG[agentSlug]?.tabLabel ?? agentSlug} → ${subtab.label}`,
      };
      surfaces.push(baseSurface);

      // Sub-sub-tabs N3-static (if any)
      const key = `${agentSlug}.${subtab.id}` as `${string}.${string}`;
      const subsubtabs =
        (agentSubsubtabs as Record<string, readonly { id: string; label: string; icon: string }[]>)[key] ?? [];
      for (const sst of subsubtabs) {
        surfaces.push({
          capId:
            CAP_MAP[`${agentSlug}.${subtab.id}.${sst.id}`] ??
            CAP_MAP[`${agentSlug}.${subtab.id}`] ??
            null,
          agent: agentSlug,
          subtab: subtab.id,
          subsubtab: sst.id,
          route: `/${tenantId}/${agentSlug}/${subtab.id}/${sst.id}`,
          kind: "shell",
          label: `${agentCatalogModule.AGENT_CATALOG[agentSlug]?.tabLabel ?? agentSlug} → ${subtab.label} → ${sst.label}`,
        });
      }
    }
  }

  // ── 4. Config subtabs ────────────────────────────────────────────────────
  const configSubtabs =
    (ribbonSubtabs as typeof RIBBON_SUBTABS)["config"] ?? [];
  for (const subtab of configSubtabs) {
    surfaces.push({
      capId: CAP_MAP[`config.${subtab.id}`] ?? null,
      agent: "config",
      subtab: subtab.id,
      route: `/${tenantId}/config/${subtab.id}`,
      kind: "shell",
      label: `Configurar → ${subtab.label}`,
    });
  }

  // ── 5. External-annotated surfaces (no deep sweep) ───────────────────────
  surfaces.push({
    capId: "admin.admin-streamlit-service",
    agent: "admin",
    route: "http://vitalia-admin.vitalialat.com",
    kind: "external-annotated",
    label: "Admin Streamlit (subdominio externo)",
  });
  surfaces.push({
    capId: "public_landing.public-clinic-landing",
    agent: "public",
    route: "/public/$CLINIC_SLUG",
    kind: "external-annotated",
    label: "Landing pública clínica (/public/[clinic-slug])",
  });
  surfaces.push({
    capId: "onboarding.clinic-onboarding-3step",
    agent: "onboarding",
    route: "/onboarding/wizard",
    kind: "external-annotated",
    label: "Onboarding wizard (/onboarding/wizard)",
  });

  return surfaces;
}

// ─────────────────────────────────────────────────────────────────────────────
// Dynamic loaders — keeps this file importable in both Node (scripts) and
// Playwright browser context (where static top-level imports work fine).
// ─────────────────────────────────────────────────────────────────────────────

function _loadAgentCatalog(): typeof import("../../../src/lib/agent-catalog") {
  // In Playwright, static imports are resolved by the bundler.
  // In Node (called by build script), path is resolved relative to __dirname.
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  return require("../../../src/lib/agent-catalog");
}

function _loadShellRoutes(): typeof import("../../../src/lib/shell-routes") {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  return require("../../../src/lib/shell-routes");
}
