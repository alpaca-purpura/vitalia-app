import { fileURLToPath } from "node:url";

import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    // `next` is a runtime peer (provided by the consuming Next app), not a dep of
    // @luana/ui-kit. Alias `next/navigation` to a local stub so vite's import-analysis
    // resolves it in the test env; tests still override behaviour with vi.mock(...).
    alias: {
      "next/navigation": fileURLToPath(
        new URL("./src/__tests__/__mocks__/next-navigation.ts", import.meta.url),
      ),
      // (The `@luana/hooks` barrel alias was removed: the barrel no longer re-exports the
      // app-coupled `use-copilot-offset`, so it resolves cleanly in the test env — same
      // resolution as production. Keeping test==prod resolution avoids masking real bugs.)
    },
  },
});
