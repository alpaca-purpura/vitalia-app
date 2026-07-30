// canon: design-system-canon.md §2.1-§2.2 · story-origin: core-ds-foundation
/**
 * EntitySubNavBar.test.tsx — Validator F-7 for the canon N3 nav bar (@luana/ui-kit).
 *
 * Covers:
 *   - WAI-ARIA role=tablist + role=tab
 *   - Master mode (entity=null): root leaf ACTIVE, only root leaf visible
 *   - Workspace mode (entity set): root leaf inactive peer + full leaves
 *   - Root-pill present + navigates rootHref (router.push) when clicked
 *   - ‹ back-arrow present on the root leaf
 *   - Roving tabindex (arrow keys / Home / End move focus)
 *   - Add-affordance calls onAddAffordance (not router.push)
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

// Mock next/navigation — the ui-kit test env has no Next runtime.
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => "/tenant-abc/collection/entity-001/datos",
  useParams: () => ({ leaf: "datos" }),
}));

import { EntitySubNavBar } from "../EntitySubNavBar";

// ── Fixtures ────────────────────────────────────────────────────────────────

const entity = {
  id: "entity-001",
  name: "Tech B2B Mid-Market",
  avatarUrl: null,
};

const leaves = [
  { id: "datos", label: "Datos", href: "/tenant-abc/collection/entity-001/datos" },
  { id: "buyer-a1b2", label: "Ana García", href: "/tenant-abc/collection/entity-001/buyer-a1b2" },
  { id: "buyer-c3d4", label: "Carlos Ruiz", href: "/tenant-abc/collection/entity-001/buyer-c3d4" },
];

const addAffordance = { id: "__add__", label: "+ buyer", href: "", isAddAffordance: true };

function renderDetail(props?: Partial<React.ComponentProps<typeof EntitySubNavBar>>) {
  return render(
    <EntitySubNavBar
      rootHref="/tenant-abc/collection"
      rootLabel="ICPs"
      entity={entity}
      leaves={leaves}
      activeLeaf="datos"
      {...props}
    />,
  );
}

// ── Tests ───────────────────────────────────────────────────────────────────

describe("EntitySubNavBar (canon @luana/ui-kit)", () => {
  describe("workspace/detail mode (entity set)", () => {
    it("renders a nav with role=tablist", () => {
      renderDetail();
      expect(screen.getByRole("tablist")).toBeInTheDocument();
    });

    it("renders the root leaf + all content leaves as tab buttons", () => {
      renderDetail();
      const tabs = screen.getAllByRole("tab");
      expect(tabs).toHaveLength(4); // root + 3 content
      expect(tabs[0]).toHaveTextContent("ICPs");
      expect(tabs[1]).toHaveTextContent("Datos");
      expect(tabs[2]).toHaveTextContent("Ana García");
      expect(tabs[3]).toHaveTextContent("Carlos Ruiz");
    });

    it("marks the active content leaf aria-selected=true and root not active", () => {
      renderDetail({ activeLeaf: "buyer-a1b2" });
      const tabs = screen.getAllByRole("tab");
      expect(tabs[0]).toHaveAttribute("aria-selected", "false"); // root
      expect(tabs[1]).toHaveAttribute("aria-selected", "false"); // datos
      expect(tabs[2]).toHaveAttribute("aria-selected", "true"); // buyer-a1b2
    });

    it("renders the entity name in the identity area", () => {
      renderDetail();
      expect(screen.getByText("Tech B2B Mid-Market")).toBeInTheDocument();
    });
  });

  describe("master mode (entity=null)", () => {
    it("renders ONLY the root leaf as the single tab", () => {
      renderDetail({ entity: null, activeLeaf: null });
      const tabs = screen.getAllByRole("tab");
      expect(tabs).toHaveLength(1);
      expect(tabs[0]).toHaveTextContent("ICPs");
    });

    it("root leaf is aria-selected=true (active) in master mode", () => {
      renderDetail({ entity: null, activeLeaf: null });
      expect(screen.getByTestId("entity-leaf-root")).toHaveAttribute("aria-selected", "true");
    });

    it("does NOT render content leaves in master mode", () => {
      renderDetail({ entity: null, activeLeaf: null });
      expect(screen.queryByText("Datos")).toBeNull();
      expect(screen.queryByText("Ana García")).toBeNull();
    });

    it("shows the placeholder in master mode when provided", () => {
      renderDetail({ entity: null, activeLeaf: null, placeholder: "Selecciona un ICP" });
      expect(screen.getByText("Selecciona un ICP")).toBeInTheDocument();
    });
  });

  describe("root-pill", () => {
    it("renders the root leaf as a button (not a link) with data-root-leaf", () => {
      renderDetail();
      const root = screen.getByTestId("entity-leaf-root");
      expect(root.tagName).toBe("BUTTON");
      expect(root).toHaveAttribute("role", "tab");
      expect(root).toHaveAttribute("data-root-leaf", "true");
    });

    it("renders the ‹ back-arrow on the root leaf", () => {
      renderDetail();
      expect(screen.getByTestId("entity-leaf-root")).toHaveTextContent("‹");
    });

    it("navigates to rootHref (router.push) when the root-pill is clicked", () => {
      mockPush.mockClear();
      renderDetail();
      fireEvent.click(screen.getByTestId("entity-leaf-root"));
      expect(mockPush).toHaveBeenCalledWith("/tenant-abc/collection");
    });

    it("does NOT render an <a> link pointing to rootHref (root is a tab)", () => {
      renderDetail();
      const rootLink = Array.from(document.querySelectorAll("a")).find(
        (a) => a.getAttribute("href") === "/tenant-abc/collection",
      );
      expect(rootLink).toBeUndefined();
    });
  });

  describe("roving tabindex + keyboard navigation", () => {
    it("only the focused tab has tabindex=0 (active leaf at mount)", () => {
      renderDetail({ activeLeaf: "datos" });
      const tabs = screen.getAllByRole("tab");
      expect(tabs[0]).toHaveAttribute("tabindex", "-1"); // root
      expect(tabs[1]).toHaveAttribute("tabindex", "0"); // datos (focused)
      expect(tabs[2]).toHaveAttribute("tabindex", "-1");
    });

    it("ArrowRight moves focus to the next tab", () => {
      renderDetail({ activeLeaf: "datos" });
      const nav = screen.getByRole("tablist");
      const tabs = screen.getAllByRole("tab");
      tabs[1]?.focus();
      fireEvent.keyDown(nav, { key: "ArrowRight" });
      expect(tabs[2]).toHaveAttribute("tabindex", "0");
    });

    it("ArrowLeft moves focus to the previous tab", () => {
      renderDetail({ activeLeaf: "buyer-a1b2" });
      const nav = screen.getByRole("tablist");
      const tabs = screen.getAllByRole("tab");
      tabs[2]?.focus();
      fireEvent.keyDown(nav, { key: "ArrowLeft" });
      expect(tabs[1]).toHaveAttribute("tabindex", "0");
    });

    it("Home moves focus to the first tab (root leaf)", () => {
      renderDetail({ activeLeaf: "buyer-c3d4" });
      const nav = screen.getByRole("tablist");
      const tabs = screen.getAllByRole("tab");
      tabs[3]?.focus();
      fireEvent.keyDown(nav, { key: "Home" });
      expect(tabs[0]).toHaveAttribute("tabindex", "0");
    });

    it("End moves focus to the last tab", () => {
      renderDetail({ activeLeaf: "datos" });
      const nav = screen.getByRole("tablist");
      const tabs = screen.getAllByRole("tab");
      tabs[1]?.focus();
      fireEvent.keyDown(nav, { key: "End" });
      expect(tabs[3]).toHaveAttribute("tabindex", "0");
    });

    it("ArrowRight wraps from the last tab to the first (root)", () => {
      renderDetail({ activeLeaf: "buyer-c3d4" });
      const nav = screen.getByRole("tablist");
      const tabs = screen.getAllByRole("tab");
      tabs[3]?.focus();
      fireEvent.keyDown(nav, { key: "ArrowRight" });
      expect(tabs[0]).toHaveAttribute("tabindex", "0");
    });
  });

  describe("add affordance", () => {
    it("renders the add affordance in workspace mode", () => {
      renderDetail({ leaves: [...leaves, addAffordance] });
      expect(screen.getByText("+ buyer")).toBeInTheDocument();
    });

    it("calls onAddAffordance (not router.push) when the affordance is clicked", () => {
      mockPush.mockClear();
      const onAddAffordance = vi.fn();
      renderDetail({ leaves: [...leaves, addAffordance], onAddAffordance });
      fireEvent.click(screen.getByTestId("entity-leaf-add-affordance"));
      expect(onAddAffordance).toHaveBeenCalledTimes(1);
    });

    it("does NOT render the add affordance in master mode", () => {
      renderDetail({ entity: null, activeLeaf: null, leaves: [...leaves, addAffordance] });
      expect(screen.queryByTestId("entity-leaf-add-affordance")).toBeNull();
    });
  });

  describe("content leaf navigation", () => {
    it("router.push (soft nav) is called when a content leaf is clicked", () => {
      mockPush.mockClear();
      renderDetail();
      const tabs = screen.getAllByRole("tab");
      fireEvent.click(tabs[2]); // Ana García
      expect(mockPush).toHaveBeenCalledWith("/tenant-abc/collection/entity-001/buyer-a1b2");
    });
  });

  describe("entityIdentitySlot (canon §6.3 — identity = selector)", () => {
    const customSlot = <div data-testid="custom-picker">Picker</div>;

    it("back-compat: absent slot → static identity renders, no slot wrapper", () => {
      renderDetail();
      expect(screen.getByText("Tech B2B Mid-Market")).toBeTruthy();
      expect(screen.queryByTestId("entity-identity-slot")).toBeNull();
    });

    it("renders the custom node INSTEAD of the static identity when provided (workspace mode)", () => {
      renderDetail({ entityIdentitySlot: customSlot });
      expect(screen.getByTestId("entity-identity-slot")).toBeTruthy();
      expect(screen.getByTestId("custom-picker")).toBeTruthy();
      // Static identity block is replaced (name + aria-label gone)
      expect(screen.queryByText("Tech B2B Mid-Market")).toBeNull();
      expect(document.querySelector('[aria-label="Editando: Tech B2B Mid-Market"]')).toBeNull();
    });

    it("does NOT affect the tablist — slot is not a tab", () => {
      renderDetail({ entityIdentitySlot: customSlot });
      const tabs = screen.getAllByRole("tab");
      expect(tabs).toHaveLength(4); // root + 3 content leaves, unchanged
    });

    it("master mode (entity=null): slot NOT rendered even when provided", () => {
      renderDetail({ entity: null, activeLeaf: null, entityIdentitySlot: customSlot });
      expect(screen.queryByTestId("entity-identity-slot")).toBeNull();
      expect(screen.queryByTestId("custom-picker")).toBeNull();
    });
  });
});
