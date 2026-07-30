/**
 * keys-to-camel.ts — Deep snake_case → camelCase key transform for API responses.
 *
 * Origen 2026-06-04 (live-verify vitalia-fase2-adrian-embudo): los DTOs BE de `crm`
 * son snake_case (sin alias camelCase) y los view-models FE son camelCase. Sin esta
 * transformación en el borde, el FE castea el JSON snake crudo como tipo camel →
 * todo campo multi-palabra llega `undefined` (board crasheaba en `buyingSignals.slice`).
 *
 * Convención del codebase: "snake API → camelCase view-model, el FE mapea en el borde"
 * (igual que inbox ConversationListItem + lucas-recommendation). NO se toca fetchClient
 * global (lo consumen features que SÍ esperan snake) — se aplica solo en los fetch del
 * feature que usa view-models camelCase.
 *
 * Determinista, sin dependencias. Recursa objetos planos + arrays; deja primitivas,
 * Date y null intactos. NO transforma valores, solo keys.
 */

/** Convierte una key `snake_case` (o `SCREAMING_SNAKE`) a `camelCase`. */
function snakeKeyToCamel(key: string): string {
  return key.replace(/_([a-z0-9])/g, (_, c: string) => c.toUpperCase());
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value) &&
    Object.prototype.toString.call(value) === "[object Object]"
  );
}

/**
 * Recorre `input` y devuelve una copia con todas las keys de objeto en camelCase.
 * Genérico por conveniencia del call-site (`keysToCamel<BoardResponse>(raw)`); el
 * caller es responsable de que la forma resultante matchee el tipo declarado.
 */
export function keysToCamel<T = unknown>(input: unknown): T {
  if (Array.isArray(input)) {
    return input.map((item) => keysToCamel(item)) as T;
  }
  if (isPlainObject(input)) {
    const out: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(input)) {
      out[snakeKeyToCamel(key)] = keysToCamel(value);
    }
    return out as T;
  }
  return input as T;
}

/** Convierte una key `camelCase` a `snake_case`. */
function camelKeyToSnake(key: string): string {
  return key.replace(/([A-Z])/g, (c) => `_${c.toLowerCase()}`);
}

/**
 * Inversa de keysToCamel — para REQUEST payloads: el BE Pydantic es snake_case
 * sin alias camelCase, así que un body camelCase se IGNORA silencioso (campo
 * extra) y "persiste nada" sin error. Origen: config-cuenta PATCH legalName →
 * 200 pero legal_name null (2026-06-11).
 */
export function keysToSnake<T = unknown>(input: unknown): T {
  if (Array.isArray(input)) {
    return input.map((item) => keysToSnake(item)) as T;
  }
  if (isPlainObject(input)) {
    const out: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(input)) {
      out[camelKeyToSnake(key)] = keysToSnake(value);
    }
    return out as T;
  }
  return input as T;
}
