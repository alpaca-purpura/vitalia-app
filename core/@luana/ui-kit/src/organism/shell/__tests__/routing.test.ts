// cap: platform.lift-shell-chrome-ui-kit
import { describe, it, expect } from "vitest";
import {
  extractAgentFromPath,
  extractSubtabFromPath,
  isValidAgent,
  isValidSubtab,
} from "../routing";

/**
 * RED-first TDD for the generic routing helpers (T-K1).
 *
 * Helpers are catalog-driven: the brand passes its own agent slug-set and
 * sub-tab map by argument. The kit ships zero hardcoded brand slugs/labels.
 *
 * Path shape (brand-agnostic, mirrors the shell route group):
 *   /{tenantId}/{agent}/{subtab}/...
 * segment[0] = tenant, segment[1] = agent, segment[2] = subtab.
 */

// Synthetic generic catalog — NO brand tokens.
const AGENT_SLUGS = ["alpha", "beta", "gamma"] as const;
type AgentSlug = (typeof AGENT_SLUGS)[number];

// Special non-agent tab that still routes (mirrors brand "config"/"supervisor").
const SPECIAL_TABS = ["settings"] as const;

const SUBTABS_BY_AGENT: Record<string, readonly string[]> = {
  alpha: ["overview", "detail"],
  beta: ["board"],
  gamma: [],
  settings: ["general", "members"],
};

const opts = {
  agentSlugs: AGENT_SLUGS as readonly string[],
  specialTabs: SPECIAL_TABS as readonly string[],
  subtabsByAgent: SUBTABS_BY_AGENT,
};

describe("extractAgentFromPath", () => {
  it("returns the agent slug from segment[1]", () => {
    expect(extractAgentFromPath("/tenant-123/alpha/overview", opts)).toBe("alpha");
  });

  it("recognizes a special (non-agent) tab", () => {
    expect(extractAgentFromPath("/tenant-123/settings/general", opts)).toBe("settings");
  });

  it("returns null for an unknown segment", () => {
    expect(extractAgentFromPath("/tenant-123/unknown/x", opts)).toBeNull();
  });

  it("returns null for a bare tenant path (no agent segment)", () => {
    expect(extractAgentFromPath("/tenant-123", opts)).toBeNull();
  });

  it("tolerates a trailing slash and query-free path", () => {
    expect(extractAgentFromPath("/tenant-123/beta/board/", opts)).toBe("beta");
  });
});

describe("extractSubtabFromPath", () => {
  it("returns the subtab slug from segment[2]", () => {
    expect(extractSubtabFromPath("/tenant-123/alpha/detail")).toBe("detail");
  });

  it("returns null when there is no subtab segment", () => {
    expect(extractSubtabFromPath("/tenant-123/alpha")).toBeNull();
  });

  it("returns null for a bare tenant path", () => {
    expect(extractSubtabFromPath("/tenant-123")).toBeNull();
  });

  it("ignores deeper segments (returns only segment[2])", () => {
    expect(extractSubtabFromPath("/tenant-123/alpha/detail/sub")).toBe("detail");
  });
});

describe("isValidAgent", () => {
  it("true for a known agent slug", () => {
    expect(isValidAgent("alpha", opts)).toBe(true);
  });

  it("true for a special tab", () => {
    expect(isValidAgent("settings", opts)).toBe(true);
  });

  it("false for an unknown slug", () => {
    expect(isValidAgent("nope", opts)).toBe(false);
  });

  it("false for null / empty", () => {
    expect(isValidAgent(null, opts)).toBe(false);
    expect(isValidAgent("", opts)).toBe(false);
  });
});

describe("isValidSubtab", () => {
  it("true when subtab belongs to the agent", () => {
    expect(isValidSubtab("alpha", "overview", opts)).toBe(true);
  });

  it("true for a special tab's subtab", () => {
    expect(isValidSubtab("settings", "members", opts)).toBe(true);
  });

  it("false when the subtab does not belong to the agent", () => {
    expect(isValidSubtab("alpha", "board", opts)).toBe(false);
  });

  it("false for an unknown agent", () => {
    expect(isValidSubtab("nope", "overview", opts)).toBe(false);
  });

  it("false when the agent has no subtabs", () => {
    expect(isValidSubtab("gamma", "anything", opts)).toBe(false);
  });
});
