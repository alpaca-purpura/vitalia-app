/**
 * RED tests — hooks (T-infra-7 TDD)
 * Tests written BEFORE implementation (TDD RED-first).
 */

import { describe, it, expect } from "vitest";

// These imports will fail until hooks are implemented (RED state)
import { agentNameByRole } from "@/components/shared/agents/agent-names";

describe("agentNameByRole", () => {
  it("returns name for valeria role", () => {
    expect(agentNameByRole("valeria")).toBe("Valeria");
  });

  it("returns name for adrian role", () => {
    expect(agentNameByRole("adrian")).toBe("Adrián");
  });

  it("returns name for lucas role", () => {
    expect(agentNameByRole("lucas")).toBe("Lucas");
  });

  it("returns fallback for unknown role", () => {
    const result = agentNameByRole("unknown-role");
    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
  });
});
