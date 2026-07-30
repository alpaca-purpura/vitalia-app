// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s0-TBD
/**
 * Agents SSoT — Vitalia (F1-S0)
 *
 * Origen: Chris ratificado 2026-05-22 (lista canónica nombre + rol + color + paths).
 * Imágenes ubicadas en `public/agents/{slug}/{thumbnail,transparent}.{png,jpeg}`.
 *
 * Consumed by:
 *   - /test-stack/primitives (showcase F1-S0 baseline)
 *   - F1-S1+ TopBar / ValeriaRail / Ribbon agent tabs
 *   - Brand Studio voice presets
 *   - Sales agent specialist routing
 *
 * NO usar este módulo para PHI ni datos sensibles. Es metadata de identidad
 * agéntica (público no-PHI per vitalia/.claude/rules/hipaa-lite.md).
 */

export type AgentSlug =
  | "lisa"
  | "valeria"
  | "adrian"
  | "lucas"
  | "camila"
  | "mateo";

export interface AgentMeta {
  /** Identifier slug for routing / CSS classes (bg-agent-{slug}) */
  slug: AgentSlug;
  /** Display name */
  name: string;
  /** Role / responsibility description (one-liner from Chris ratify) */
  role: string;
  /** Brand color hex — also defined as HSL CSS var --agent-{slug} */
  colorHex: string;
  /** Path to square cropped portrait (avatar small/medium) */
  thumbnail: string;
  /** Path to full transparent body (hero usage, larger viewport) */
  transparent: string;
}

export const AGENTS: Record<AgentSlug, AgentMeta> = {
  lisa: {
    slug: "lisa",
    name: "Lisa",
    role: "Especialista en tu marca y en la estructuración de una buena oferta comercial a través de metodologías como el offer ladder",
    colorHex: "#00D084",
    thumbnail: "/agents/lisa/thumbnail.png",
    transparent: "/agents/lisa/transparent.png",
  },
  valeria: {
    slug: "valeria",
    name: "Valeria",
    role: "Líder y coordinadora general, con quien conversas en el día a día y hace todo por ti",
    colorHex: "#7b2d91",
    thumbnail: "/agents/valeria/thumbnail.png",
    transparent: "/agents/valeria/transparent.png",
  },
  adrian: {
    slug: "adrian",
    name: "Adrián",
    role: "Agente Closer integral que maximiza la facturación combinando la calificación inmediata de leads entrantes con la reactivación estratégica de oportunidades estancadas hasta concretar la venta",
    colorHex: "#01b2f8",
    thumbnail: "/agents/adrian/thumbnail.png",
    transparent: "/agents/adrian/transparent.jpeg",
  },
  lucas: {
    slug: "lucas",
    name: "Lucas",
    role: "Estratega Growth, actualizado con las últimas tendencias para viralizar y enganchar usuarios para hacer crecer marcas y conseguir leads de calidad",
    colorHex: "#111111",
    thumbnail: "/agents/lucas/thumbnail.png",
    transparent: "/agents/lucas/transparent.png",
  },
  camila: {
    slug: "camila",
    name: "Camila",
    role: "Aumenta el CLTV y Engagement, especialista post-venta, mide satisfacción del cliente, monitorea redes y la actividad de los clientes para reactivar",
    colorHex: "#180d95",
    thumbnail: "/agents/camila/thumbnail.png",
    transparent: "/agents/camila/transparent.png",
  },
  mateo: {
    slug: "mateo",
    name: "Mateo",
    role: "Especialista en tecnología y diseño basado en IA, hace la vida más sencilla al personal con propuestas de diseño geniales que funcionan",
    colorHex: "#fee209",
    thumbnail: "/agents/mateo/thumbnail.png",
    transparent: "/agents/mateo/transparent.png",
  },
};

/** Ordered list for iteration (UI ribbon order) */
export const AGENT_LIST: AgentMeta[] = [
  AGENTS.valeria,
  AGENTS.lisa,
  AGENTS.adrian,
  AGENTS.lucas,
  AGENTS.camila,
  AGENTS.mateo,
];
