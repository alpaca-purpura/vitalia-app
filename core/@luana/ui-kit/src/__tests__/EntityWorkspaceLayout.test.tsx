// canon: design-system-canon.md §2.1-§2.2 · story-origin: core-ds-foundation
/**
 * EntityWorkspaceLayout.test.tsx — Validator F-7 for the canon N3 workspace layout.
 *
 * Covers:
 *   - master mode (entity=null) renders children + only the root leaf (leaves not active)
 *   - detail mode (entity set) renders EntitySubNavBar with the leaves
 *   - skeleton store-free: isLoading renders a skeleton with NO store provider wrapping
 *   - activeLeaf is URL-derived (useParams), never from a store
 */

import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

// Mock next/navigation — URL-derivation of activeLeaf + router for the nav bar.
// `mockLeaf` lets each test control the [leaf] segment that useParams returns.
let mockLeaf: string | undefined = "datos";
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useParams: () => ({ leaf: mockLeaf }),
  useRouter: () => ({ push: mockPush }),
  usePathname: () => `/tenant-abc/collection/entity-001/${mockLeaf ?? ""}`,
}));

import { EntityWorkspaceLayout } from "../EntityWorkspaceLayout";

// ── Fixtures ────────────────────────────────────────────────────────────────

const entity = { id: "entity-001", name: "Tech B2B Mid-Market", avatarUrl: null };

const leaves = [
  { id: "datos", label: "Datos", href: "/tenant-abc/collection/entity-001/datos" },
  { id: "buyer-a1b2", label: "Ana García", href: "/tenant-abc/collection/entity-001/buyer-a1b2" },
];

const baseProps = {
  rootHref: "/tenant-abc/collection",
  rootLabel: "ICPs",
  leaves,
};

// ── Tests ───────────────────────────────────────────────────────────────────

describe("EntityWorkspaceLayout (canon @luana/ui-kit)", () => {
  describe("master mode (entity=null)", () => {
    it("renders the children/leaf-content slot", () => {
      mockLeaf = undefined;
      render(
        <EntityWorkspaceLayout {...baseProps} entity={null}>
          <div data-testid="master-grid">Grid of entities</div>
        </EntityWorkspaceLayout>,
      );
      expect(screen.getByTestId("entity-workspace-content")).toBeInTheDocument();
      expect(screen.getByTestId("master-grid")).toBeInTheDocument();
    });

    it("renders only the root leaf as a tab (content leaves not present)", () => {
      mockLeaf = undefined;
      render(
        <EntityWorkspaceLayout {...baseProps} entity={null}>
          <div>content</div>
        </EntityWorkspaceLayout>,
      );
      const tabs = screen.getAllByRole("tab");
      expect(tabs).toHaveLength(1);
      expect(tabs[0]).toHaveTextContent("ICPs");
      // content leaves are NOT rendered (and therefore not active)
      expect(screen.queryByText("Datos")).toBeNull();
      expect(screen.queryByText("Ana García")).toBeNull();
    });
  });

  describe("detail mode (entity set)", () => {
    it("mounts EntitySubNavBar with the full leaf set", () => {
      mockLeaf = "datos";
      render(
        <EntityWorkspaceLayout {...baseProps} entity={entity}>
          <div data-testid="leaf-page">Datos content</div>
        </EntityWorkspaceLayout>,
      );
      expect(screen.getByTestId("entity-sub-nav-bar")).toBeInTheDocument();
      const tabs = screen.getAllByRole("tab");
      expect(tabs).toHaveLength(3); // root + 2 content leaves
      expect(tabs[1]).toHaveTextContent("Datos");
      expect(tabs[2]).toHaveTextContent("Ana García");
    });

    it("marks the URL-derived active leaf aria-selected=true", () => {
      mockLeaf = "buyer-a1b2";
      render(
        <EntityWorkspaceLayout {...baseProps} entity={entity}>
          <div>content</div>
        </EntityWorkspaceLayout>,
      );
      const tabs = screen.getAllByRole("tab");
      // root + datos + buyer-a1b2; buyer-a1b2 (idx 2) is active
      expect(tabs[2]).toHaveAttribute("aria-selected", "true");
      expect(tabs[1]).toHaveAttribute("aria-selected", "false");
    });

    it("renders the entity name in the nav bar", () => {
      mockLeaf = "datos";
      render(
        <EntityWorkspaceLayout {...baseProps} entity={entity}>
          <div>content</div>
        </EntityWorkspaceLayout>,
      );
      expect(screen.getByText("Tech B2B Mid-Market")).toBeInTheDocument();
    });
  });

  describe("skeleton store-free (G2)", () => {
    it("renders a skeleton when isLoading — with NO store provider wrapping it", () => {
      mockLeaf = "datos";
      // Rendered bare (no Provider) — proves the skeleton path subscribes to no store.
      render(
        <EntityWorkspaceLayout {...baseProps} entity={null} isLoading>
          <div>content</div>
        </EntityWorkspaceLayout>,
      );
      expect(screen.getByTestId("entity-sub-nav-skeleton")).toBeInTheDocument();
      // The real nav bar is NOT mounted while loading
      expect(screen.queryByTestId("entity-sub-nav-bar")).toBeNull();
      // No tabs rendered in the skeleton path
      expect(screen.queryAllByRole("tab")).toHaveLength(0);
    });

    it("renders the workspace layout wrapper", () => {
      mockLeaf = "datos";
      render(
        <EntityWorkspaceLayout {...baseProps} entity={null} isLoading>
          <div>content</div>
        </EntityWorkspaceLayout>,
      );
      expect(screen.getByTestId("entity-workspace-layout")).toBeInTheDocument();
    });
  });

  describe("activeLeaf override prop (static route segments — vitalia pattern)", () => {
    it("uses activeLeaf prop over URL-derived param when provided", () => {
      // URL param has 'datos' but prop says 'buyer-a1b2' → prop wins
      mockLeaf = "datos";
      render(
        <EntityWorkspaceLayout {...baseProps} entity={entity} activeLeaf="buyer-a1b2">
          <div>content</div>
        </EntityWorkspaceLayout>,
      );
      const tabs = screen.getAllByRole("tab");
      // root + datos + buyer-a1b2; prop 'buyer-a1b2' (idx 2) should be active
      expect(tabs[2]).toHaveAttribute("aria-selected", "true");
      expect(tabs[1]).toHaveAttribute("aria-selected", "false");
    });

    it("falls back to URL-derived param when activeLeaf prop not provided", () => {
      mockLeaf = "datos";
      render(
        <EntityWorkspaceLayout {...baseProps} entity={entity}>
          <div>content</div>
        </EntityWorkspaceLayout>,
      );
      const tabs = screen.getAllByRole("tab");
      // URL param 'datos' (idx 1) should be active
      expect(tabs[1]).toHaveAttribute("aria-selected", "true");
    });

    it("handles null activeLeaf prop (master/loading state)", () => {
      mockLeaf = "datos";
      render(
        <EntityWorkspaceLayout {...baseProps} entity={entity} activeLeaf={null}>
          <div>content</div>
        </EntityWorkspaceLayout>,
      );
      const tabs = screen.getAllByRole("tab");
      // null override → no content leaf active, root is active
      expect(tabs[0]).toHaveAttribute("aria-selected", "true");
      expect(tabs[1]).toHaveAttribute("aria-selected", "false");
    });
  });

  describe("entityIdentitySlot forwarding (canon §6.3 — mirror of onAddAffordance)", () => {
    const customSlot = <div data-testid="custom-picker">Picker</div>;

    it("forwards the slot verbatim to EntitySubNavBar (detail mode)", () => {
      mockLeaf = "datos";
      render(
        <EntityWorkspaceLayout {...baseProps} entity={entity} entityIdentitySlot={customSlot}>
          <div>content</div>
        </EntityWorkspaceLayout>,
      );
      const navBar = screen.getByTestId("entity-sub-nav-bar");
      expect(navBar).toBeTruthy();
      expect(screen.getByTestId("custom-picker")).toBeTruthy();
      // Static identity replaced by the slot
      expect(screen.queryByText("Tech B2B Mid-Market")).toBeNull();
    });

    it("back-compat: absent slot → static identity renders unchanged", () => {
      mockLeaf = "datos";
      render(
        <EntityWorkspaceLayout {...baseProps} entity={entity}>
          <div>content</div>
        </EntityWorkspaceLayout>,
      );
      expect(screen.getByText("Tech B2B Mid-Market")).toBeTruthy();
      expect(screen.queryByTestId("entity-identity-slot")).toBeNull();
    });

    it("master mode (entity=null): slot NOT rendered even when provided", () => {
      mockLeaf = undefined;
      render(
        <EntityWorkspaceLayout {...baseProps} entity={null} entityIdentitySlot={customSlot}>
          <div>content</div>
        </EntityWorkspaceLayout>,
      );
      expect(screen.queryByTestId("custom-picker")).toBeNull();
    });
  });
});
