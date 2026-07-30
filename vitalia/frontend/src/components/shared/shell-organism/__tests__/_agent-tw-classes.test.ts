/**
 * _agent-tw-classes.ts unit tests — F1-S8 T-2 (TDD mandatory per tdd-mandatory.md)
 *
 * SC-1 gherkin coverage: agentTextClassSubTab returns text-agent-{slug} for standard agents
 * SC-1/lucas exception: agentTextClassSubTab('lucas') === 'text-foreground'
 * SC-1/config exception: agentTextClassSubTab('config') === 'text-foreground'
 * Exhaustive: all RibbonTabSlug values handled
 *
 * spec_anchor: 01-spec.md § Active state Lucas exception + § D18/D19 · 03-arch.md § 2.2
 */

import { describe, it, expect } from "vitest";
import {
  agentTextClassSubTab,
  agentBgClass,
  agentBgSoftClass,
  agentTextClass,
} from "../_agent-tw-classes";

// ──────────────────────────────────────────────────────────────────────────────
// F1-S8 T-2 — agentTextClassSubTab (new helper)
// ──────────────────────────────────────────────────────────────────────────────

describe("agentTextClassSubTab — standard agents return text-agent-{slug} (F1-S8 T-2)", () => {
  it("agentTextClassSubTab('lisa') === 'text-agent-lisa'", () => {
    expect(agentTextClassSubTab("lisa")).toBe("text-agent-lisa");
  });

  it("agentTextClassSubTab('valeria') === 'text-agent-valeria'", () => {
    expect(agentTextClassSubTab("valeria")).toBe("text-agent-valeria");
  });

  it("agentTextClassSubTab('adrian') === 'text-agent-adrian'", () => {
    expect(agentTextClassSubTab("adrian")).toBe("text-agent-adrian");
  });

  it("agentTextClassSubTab('camila') === 'text-agent-camila'", () => {
    expect(agentTextClassSubTab("camila")).toBe("text-agent-camila");
  });

  it("agentTextClassSubTab('mateo') === 'text-foreground' (exception D20 — WCAG AA)", () => {
    // T-V2 lift fix-loop: #FEE209 amarillo sobre bg-agent-mateo-soft = 1.21 (AA fail)
    // — destapado por axe real post edge-redirect. Excepción análoga a lucas/config.
    expect(agentTextClassSubTab("mateo")).toBe("text-foreground");
  });
});

describe("agentTextClassSubTab — Lucas exception: text-foreground (F1-S8 T-2 D18)", () => {
  it("agentTextClassSubTab('lucas') === 'text-foreground' (near-black hex #111111 causes contrast issue on rgba-10%-black bg-agent-lucas-soft)", () => {
    expect(agentTextClassSubTab("lucas")).toBe("text-foreground");
  });

  it("agentTextClassSubTab('lucas') differs from agentTextClass('lucas') (different semantic — preserved F1-S6)", () => {
    expect(agentTextClassSubTab("lucas")).not.toBe(agentTextClass("lucas"));
    expect(agentTextClass("lucas")).toBe("text-agent-lucas");
  });
});

describe("agentTextClassSubTab — Config exception: text-foreground (F1-S8 T-2 D19)", () => {
  it("agentTextClassSubTab('config') === 'text-foreground' (Config is not an agent — bg-muted neutral per mockup)", () => {
    expect(agentTextClassSubTab("config")).toBe("text-foreground");
  });
});

describe("agentTextClassSubTab — no dynamic class string construction (Tailwind JIT safe)", () => {
  it("returns only static class names (no template literals with runtime values)", () => {
    // All 7 RibbonTabSlug values should return known static Tailwind class strings
    const allReturns = [
      agentTextClassSubTab("lisa"),
      agentTextClassSubTab("valeria"),
      agentTextClassSubTab("adrian"),
      agentTextClassSubTab("lucas"),
      agentTextClassSubTab("camila"),
      agentTextClassSubTab("mateo"),
      agentTextClassSubTab("config"),
    ];
    // Each return is one of the static class strings — no arbitrary/dynamic values
    for (const cls of allReturns) {
      expect(cls).toMatch(
        /^(text-agent-(lisa|valeria|adrian|lucas|camila|mateo)|text-foreground)$/,
      );
    }
  });
});

// ──────────────────────────────────────────────────────────────────────────────
// F1-S6/S7 regression guard — existing helpers not broken by T-2 extension
// ──────────────────────────────────────────────────────────────────────────────

describe("agentBgClass, agentBgSoftClass, agentTextClass — F1-S6 regression guard", () => {
  it("agentBgClass('valeria') === 'bg-agent-valeria' (unchanged)", () => {
    expect(agentBgClass("valeria")).toBe("bg-agent-valeria");
  });

  it("agentBgSoftClass('lucas') === 'bg-agent-lucas-soft' (unchanged)", () => {
    expect(agentBgSoftClass("lucas")).toBe("bg-agent-lucas-soft");
  });

  it("agentTextClass('lisa') === 'text-agent-lisa' (unchanged)", () => {
    expect(agentTextClass("lisa")).toBe("text-agent-lisa");
  });

  it("agentTextClass('lucas') === 'text-agent-lucas' (F1-S6 — preserved, different from SubTab variant)", () => {
    expect(agentTextClass("lucas")).toBe("text-agent-lucas");
  });
});
