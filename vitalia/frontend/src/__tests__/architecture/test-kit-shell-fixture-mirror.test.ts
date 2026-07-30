/**
 * arch: @luana/ui-kit shell DEMO fixture stays a faithful mirror of vitalia's catalog.
 *
 * WHY: the kit Storybook (core/@luana/ui-kit) renders the REAL kit components, but the
 * kit is brand-agnostic (RN-2) and CANNOT import a brand. So its demo fixture
 * (stories/_shell-fixtures.tsx) hand-mirrors vitalia's catalog/colors so the catalog
 * reads like the real app ("lo más real"). That mirror is a SNAPSHOT — nothing wires
 * it to vitalia's SSoT. This test is the drift guard (decision: snapshot + drift check,
 * 2026-06-22): if vitalia's catalog/colors change and the kit demo wasn't updated, this
 * FAILS — pointing the author to update core/@luana/ui-kit/stories/_shell-fixtures.tsx
 * (+ .storybook/preview.css for colors).
 *
 * Direction: vitalia is the SSoT; the kit demo must reflect it. Scope = the structural
 * surface that visibly drifts (ribbon order · tabLabels · sub-tab labels · N3 keys ·
 * agent color tokens). Avatars/logo are literal file copies — presence only, not content
 * (known gap; binary equality is out of scope).
 *
 * This lives in vitalia (not the kit) because the kit may not depend on a brand; vitalia
 * MAY read sibling packages in the monorepo. It reads the kit files as TEXT (no import →
 * no cross-package runtime coupling), expected values derived from vitalia's LIVE catalog.
 *
 * HIPAA-lite: no-phi-scope — dev guard over UI catalog metadata.
 * downstream-regression-na: dev-only drift guard; no runtime consumers.
 */

import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  AGENT_CATALOG,
  AGENT_RIBBON_ORDER,
  RIBBON_SUBTABS,
} from "@/lib/agent-catalog";
import { AGENT_SUBSUBTABS } from "@/lib/shell-routes";

const WS = resolve(__dirname, "../../../../.."); // up to luana-vitalia/
const KIT = resolve(WS, "core/@luana/ui-kit");

const fixture = readFileSync(resolve(KIT, "stories/_shell-fixtures.tsx"), "utf8");
const previewCss = readFileSync(resolve(KIT, ".storybook/preview.css"), "utf8");
const globalsCss = readFileSync(
  resolve(WS, "vitalia/frontend/src/app/globals.css"),
  "utf8",
);

const FIX = "core/@luana/ui-kit/stories/_shell-fixtures.tsx";

describe("arch: kit shell DEMO fixture mirrors vitalia catalog (drift guard)", () => {
  it("vitalia ribbon order in kit fixture deep-equals vitalia AGENT_RIBBON_ORDER", () => {
    // The kit fixture is brand-keyed (BRAND_FIXTURES): vitalia's ribbon order lives in
    // the VITALIA_RIBBON_ORDER literal (DEMO_RIBBON_ORDER aliases it for back-compat).
    const m = fixture.match(/VITALIA_RIBBON_ORDER[^=]*=\s*\[([^\]]+)\]/);
    expect(m, `${FIX}: VITALIA_RIBBON_ORDER not found`).not.toBeNull();
    const kitOrder = (m![1].match(/"([^"]+)"/g) ?? []).map((s) => s.replace(/"/g, ""));
    expect(
      kitOrder,
      `Ribbon order drift — update VITALIA_RIBBON_ORDER in ${FIX} to match vitalia`,
    ).toEqual([...AGENT_RIBBON_ORDER]);
  });

  it("each ribbon agent's tabLabel is present in the kit fixture", () => {
    // Only ribbon agents — valeria's tabLabel is vestigial in vitalia and intentionally
    // different in the demo (supervisor, not a ribbon tab).
    for (const slug of AGENT_RIBBON_ORDER) {
      const label = AGENT_CATALOG[slug].tabLabel;
      expect(
        fixture.includes(`tabLabel: "${label}"`),
        `tabLabel drift for "${slug}" — vitalia="${label}" missing in ${FIX}`,
      ).toBe(true);
    }
  });

  it("each ribbon agent's sub-tab labels are present in the kit fixture", () => {
    for (const slug of AGENT_RIBBON_ORDER) {
      for (const st of RIBBON_SUBTABS[slug]) {
        expect(
          fixture.includes(`label: "${st.label}"`),
          `sub-tab label drift "${st.label}" (${slug}.${st.id}) missing in ${FIX}`,
        ).toBe(true);
      }
    }
  });

  it("every vitalia N3 (sub-sub-tab) key is present in the kit fixture", () => {
    for (const key of Object.keys(AGENT_SUBSUBTABS)) {
      expect(
        fixture.includes(`"${key}":`),
        `N3 key drift "${key}" missing in ${FIX} (DEMO_SUBSUBTABS_BY_KEY)`,
      ).toBe(true);
    }
  });

  it("agent color tokens (light HSL) in kit preview.css match vitalia globals.css", () => {
    const readToken = (css: string, token: string): string | null => {
      // First match = :root (light) value; ignores trailing /* hex */ comment.
      const m = css.match(new RegExp(`${token}:\\s*([^;]+);`));
      return m ? m[1].trim() : null;
    };
    for (const slug of [...AGENT_RIBBON_ORDER, "valeria"]) {
      const token = `--agent-${slug}`;
      const vitaliaVal = readToken(globalsCss, token);
      const kitVal = readToken(previewCss, token);
      expect(vitaliaVal, `${token} not in vitalia globals.css`).not.toBeNull();
      expect(
        kitVal,
        `color drift ${token}: vitalia="${vitaliaVal}" vs kit preview.css="${kitVal}" — sync .storybook/preview.css`,
      ).toBe(vitaliaVal);
    }
  });
});
