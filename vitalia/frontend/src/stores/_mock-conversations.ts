// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s5-TBD
// _mock-conversations.ts — mock data F1-S5 (no API real hasta Fase 2)
// HIPAA-lite: cero PHI (sin patient names, diagnoses, dosages ni identifiers médicos)

export type MockConversation = {
  id: string;
  title: string;
  meta: string; // ej. "14:32 · 8 mensajes"
  group: "today" | "yesterday" | "this_week";
  active?: boolean;
};

export const MOCK_CONVERSATIONS: MockConversation[] = [
  {
    id: "1",
    title: "Resumen reseñas Google semana",
    meta: "14:32 · 8 mensajes",
    group: "today",
  },
  {
    id: "2",
    title: "Ideas campaña Día de la Madre",
    meta: "11:18 · 12 mensajes",
    group: "today",
  },
  {
    id: "3",
    title: "Reporte ocupación martes",
    meta: "09:45 · 5 mensajes",
    group: "today",
  },
  {
    id: "4",
    title: "Borrador respuesta a reseña 3⭐",
    meta: "Ayer 19:02 · 4 msgs",
    group: "yesterday",
  },
  {
    id: "5",
    title: "Tutorial agenda online turnos",
    meta: "Ayer 15:30 · 7 msgs",
    group: "yesterday",
  },
  {
    id: "6",
    title: "Plan ofertas mes mayo",
    meta: "Lun · 11 mensajes",
    group: "this_week",
  },
  {
    id: "7",
    title: "Métricas conversión landing",
    meta: "Lun · 6 mensajes",
    group: "this_week",
  },
  {
    id: "8",
    title: "Revisar copy WhatsApp bienvenida",
    meta: "Dom · 9 mensajes",
    group: "this_week",
  },
];
