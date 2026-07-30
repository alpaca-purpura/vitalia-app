// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s6-TBD
/**
 * _mock-messages.ts — Mock data SSoT for Valeria chat shell (F1-S6).
 *
 * T-V2 (platform-lift-shell-chrome-ui-kit): recreated after chrome deletion.
 * File kept in shell-organism (not chrome) because chat-store.test.ts imports
 * it via @/components/shared/shell-organism/_mock-messages. Kept here to
 * preserve e2e/test import paths without touching the test file.
 *
 * spec_anchor: 01-spec.md § 5.3 + § 6 + § 8 · 03-arch.md § 2.6
 *
 * IDs stable ('1'..'6') — NOT crypto.randomUUID() — Playwright golden snapshots
 * determinism depends on stable IDs.
 *
 * Spanish neutro LatAm verified (tuteo, no voseo):
 * - "Tienes" (not "Tenés"), "ábrela" (not "abrilos"), "¿Quieres" (not "¿Querés")
 * Per .claude/rules/spanish-text.md glosario compliance.
 * # voseo-allowed: glosario reference in comments, not user-facing strings
 *
 * Anti-PHI: "Marina Pérez" + "Dr. Juan García" are fictional names from the
 * ratified mockup (Chris 2026-05-24). Not real patient data. Zero PHI.
 * Per vitalia/.claude/rules/hipaa-lite.md: PHI scope = not_applicable (shell chrome UI mock).
 *
 * downstream-regression-na: brand-local shell data; no cross-brand consumers
 */

import type { AgentSlug } from "@/lib/agent-catalog";
import type { ChatMessage } from "@/stores/chat-store";

/**
 * 6 fixed mock messages for the Valeria chat shell.
 *
 * Order per spec § 5.3:
 * 1. bot (valeria) — morning briefing
 * 2. user — question about Google reviews
 * 3. delegate — Valeria → Camila (Mantener mode)
 * 4. bot (camila) — review response
 * 5. user — confirmation
 * 6. thinking (camila) — opening patient voice section
 */
export const MOCK_MESSAGES: readonly ChatMessage[] = [
  {
    id: "1",
    role: "bot",
    agent: "valeria",
    content:
      "¡Buenos días! Tienes 8 turnos hoy y 3 pacientes esperando confirmar mañana. ¿Por dónde empezamos?",
    time: "09:01",
  },
  {
    id: "2",
    role: "user",
    content: "¿Cómo están las reseñas Google esta semana?",
    time: "09:02",
  },
  {
    id: "3",
    role: "delegate",
    fromAgent: "valeria",
    toAgent: "camila",
    delegateMode: "Mantener",
  },
  {
    id: "4",
    role: "bot",
    agent: "camila",
    content:
      "Esta semana ingresaron +3 reseñas Google (2 de 5★ y 1 de 4★). El score subió de 4.6 a 4.7. Hay una reseña destacable de Marina Pérez sobre Dr. Juan García que sugiero pinear en landing. ¿La abro?",
    time: "09:02",
  },
  {
    id: "5",
    role: "user",
    content: "Sí, ábrela.",
    time: "09:03",
  },
  {
    id: "6",
    role: "thinking",
    agent: "camila",
    content: "Camila está abriendo Voz del paciente…",
  },
] as const;

/**
 * Canned bot responses per agent — deterministic rotation via `count % len`.
 *
 * F1-S6 only hardcodes Valeria (4 responses). Other agents get empty arrays;
 * store falls back to valeria responses when array is empty.
 * F2-S* will add real responses when wiring WebSocket sales_agent.
 *
 * All strings Spanish neutro LatAm (tuteo, no voseo):
 * - "Quieres" not "Querés"
 * - "tienes" not "tenés"
 */
export const MOCK_RESPONSES_BY_AGENT: Record<
  AgentSlug,
  ReadonlyArray<{ content: string }>
> = {
  valeria: [
    {
      content:
        "Mañana tienes 12 turnos confirmados y 4 pendientes. ¿Quieres que envíe recordatorios?",
    },
    {
      content:
        "Esta semana cerraste 23 turnos. Promedio diario: 4.6. Día más cargado: jueves (7 turnos).",
    },
    {
      content:
        "Te confirmo: agendé el turno para Marina Pérez el viernes a las 10:30. ¿Algo más?",
    },
    {
      content:
        "Faltan 3 pacientes por confirmar para mañana. ¿Quieres que los contacte ahora por WhatsApp?",
    },
  ],
  lisa: [],
  adrian: [],
  lucas: [],
  camila: [],
  mateo: [],
} as const;
