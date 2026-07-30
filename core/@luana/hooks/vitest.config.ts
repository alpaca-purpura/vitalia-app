import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    globals: true,
    exclude: ["tests/_deferred/**", "node_modules/**"],
  },
});
