/**
 * prohibitedPhraseDetector.test.ts — Vitest unit tests para utilidades de detección.
 *
 * T-9 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-9 deliverables + 03-arch.md D2-voice
 *
 * Tests cubiertos:
 *   1. detectProhibitedPhrases — texto vacío, lista vacía, match exacto, case-insensitive, multiple matches, sin match
 *   2. hashVoiceBlocks — determinístico, diferente entrada = diferente hash, orden de claves estable
 *
 * Anti-creep: NO health_voice_validator. Solo substring scan. No LLM call.
 * downstream-regression-na: brand-local vitalia FE util tests; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { detectProhibitedPhrases, hashVoiceBlocks } from "../prohibitedPhraseDetector";
import type { DetectedPhrase } from "../prohibitedPhraseDetector";

// ── Fixtures ───────────────────────────────────────────────────────────────────

const makePhrase = (
  id: string,
  phrase: string,
  severity: "low" | "medium" | "high" = "medium",
  suggestedAlternative = "",
) => ({ id, phrase, suggestedAlternative, severity, countryScope: "PE", isSeed: true });

const PHRASE_GARANTIZAMOS = makePhrase("ph-001", "te garantizamos que te curas", "high", "Te acompañamos en el proceso de recuperación");
const PHRASE_CURA_SEGURA = makePhrase("ph-002", "cura segura", "high", "Tratamiento efectivo");
const PHRASE_MILAGRO = makePhrase("ph-003", "milagro", "medium", "Resultado excepcional");
const PHRASE_SIN_DOLOR = makePhrase("ph-004", "sin dolor", "low", "Procedimiento cómodo");

// ── detectProhibitedPhrases ────────────────────────────────────────────────────

describe("detectProhibitedPhrases — entradas vacías", () => {
  it("retorna array vacío cuando inputText es cadena vacía", () => {
    const result = detectProhibitedPhrases("", [PHRASE_GARANTIZAMOS]);
    expect(result).toEqual([]);
  });

  it("retorna array vacío cuando lista de frases es vacía", () => {
    const result = detectProhibitedPhrases("Te garantizamos que te curas.", []);
    expect(result).toEqual([]);
  });

  it("retorna array vacío cuando ambos son vacíos", () => {
    const result = detectProhibitedPhrases("", []);
    expect(result).toEqual([]);
  });
});

describe("detectProhibitedPhrases — detección exacta", () => {
  it("detecta frase exacta presente en el texto", () => {
    const result = detectProhibitedPhrases(
      "Te garantizamos que te curas completamente.",
      [PHRASE_GARANTIZAMOS],
    );
    expect(result).toHaveLength(1);
    expect(result[0].phraseId).toBe("ph-001");
    expect(result[0].matchedText).toBe("te garantizamos que te curas");
    expect(result[0].severity).toBe("high");
  });

  it("detecta frase de una sola palabra", () => {
    const result = detectProhibitedPhrases(
      "Nuestro tratamiento es un milagro para el paciente.",
      [PHRASE_MILAGRO],
    );
    expect(result).toHaveLength(1);
    expect(result[0].phraseId).toBe("ph-003");
  });
});

describe("detectProhibitedPhrases — case-insensitive", () => {
  it("detecta frase con mayúsculas diferentes al patrón (case-insensitive)", () => {
    const result = detectProhibitedPhrases(
      "TE GARANTIZAMOS QUE TE CURAS completamente.",
      [PHRASE_GARANTIZAMOS],
    );
    expect(result).toHaveLength(1);
    expect(result[0].phraseId).toBe("ph-001");
  });

  it("detecta frase mixta (CamelCase)", () => {
    const result = detectProhibitedPhrases(
      "Tenemos Una Cura Segura Para Ti.",
      [PHRASE_CURA_SEGURA],
    );
    expect(result).toHaveLength(1);
  });
});

describe("detectProhibitedPhrases — múltiples matches", () => {
  it("detecta múltiples frases prohibidas en el mismo texto", () => {
    const text = "Te garantizamos que te curas con nuestro milagro terapéutico sin dolor.";
    const phrases = [PHRASE_GARANTIZAMOS, PHRASE_MILAGRO, PHRASE_SIN_DOLOR];

    const result = detectProhibitedPhrases(text, phrases);
    expect(result).toHaveLength(3);

    const ids = result.map((d: DetectedPhrase) => d.phraseId);
    expect(ids).toContain("ph-001");
    expect(ids).toContain("ph-003");
    expect(ids).toContain("ph-004");
  });

  it("detecta solo las frases presentes (no falsos positivos)", () => {
    const text = "Ofrecemos tratamiento efectivo con resultados comprobados.";
    const phrases = [PHRASE_GARANTIZAMOS, PHRASE_CURA_SEGURA, PHRASE_MILAGRO];

    const result = detectProhibitedPhrases(text, phrases);
    expect(result).toHaveLength(0);
  });
});

describe("detectProhibitedPhrases — payload de resultado", () => {
  it("incluye suggestedAlternative en el resultado", () => {
    const result = detectProhibitedPhrases(
      "Cura segura para todos.",
      [PHRASE_CURA_SEGURA],
    );
    expect(result[0].suggestedAlternative).toBe("Tratamiento efectivo");
  });

  it("incluye severity correcta en el resultado", () => {
    const result = detectProhibitedPhrases(
      "Procedimiento sin dolor garantizado.",
      [PHRASE_SIN_DOLOR],
    );
    expect(result[0].severity).toBe("low");
  });

  it("maneja frase con campo phrase vacío (skip)", () => {
    const phraseWithEmpty = { ...PHRASE_GARANTIZAMOS, phrase: "" };
    const result = detectProhibitedPhrases(
      "Te garantizamos que te curas.",
      [phraseWithEmpty],
    );
    // phrase vacío es skipped
    expect(result).toHaveLength(0);
  });
});

// ── hashVoiceBlocks ────────────────────────────────────────────────────────────

describe("hashVoiceBlocks — determinismo", () => {
  it("produce el mismo hash para el mismo input", () => {
    const blocks = { identity: "Somos especialistas en salud", asi_hablo: "Con calidez" };
    expect(hashVoiceBlocks(blocks)).toBe(hashVoiceBlocks(blocks));
  });

  it("produce el mismo hash independientemente del orden de las claves", () => {
    const blocksA = { identity: "Clínica Lima", asi_hablo: "Con cuidado" };
    const blocksB = { asi_hablo: "Con cuidado", identity: "Clínica Lima" };

    // hashVoiceBlocks ordena las claves antes de hashear
    expect(hashVoiceBlocks(blocksA)).toBe(hashVoiceBlocks(blocksB));
  });

  it("produce hashes diferentes para inputs diferentes", () => {
    const blocksA = { identity: "Clínica Lima" };
    const blocksB = { identity: "Clínica Arequipa" };

    expect(hashVoiceBlocks(blocksA)).not.toBe(hashVoiceBlocks(blocksB));
  });

  it("retorna string hexadecimal", () => {
    const hash = hashVoiceBlocks({ identity: "test" });
    expect(typeof hash).toBe("string");
    expect(hash).toMatch(/^[0-9a-f]+$/);
  });
});

describe("hashVoiceBlocks — entradas edge case", () => {
  it("hash de objeto vacío es un string consistente", () => {
    const h1 = hashVoiceBlocks({});
    const h2 = hashVoiceBlocks({});
    expect(h1).toBe(h2);
  });

  it("maneja valores undefined en los bloques", () => {
    const blocks: Record<string, string | undefined> = {
      identity: "Clínica Lima",
      asi_hablo: undefined,
    };
    // No debe lanzar excepción
    expect(() => hashVoiceBlocks(blocks)).not.toThrow();
    const hash = hashVoiceBlocks(blocks);
    expect(typeof hash).toBe("string");
  });

  it("hash diferente cuando cambia valor de clave", () => {
    const base = { identity: "Clínica A", asi_hablo: "Con calidez" };
    const modified = { identity: "Clínica B", asi_hablo: "Con calidez" };
    expect(hashVoiceBlocks(base)).not.toBe(hashVoiceBlocks(modified));
  });
});
