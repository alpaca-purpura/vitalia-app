import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    environment: "happy-dom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
    exclude: ["e2e/**", "node_modules/**", "widget/**"],
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
    coverage: {
      provider: "v8",
      reporter: ["text", "json"],
      // Focus coverage on testable logic — exclude type-only files and Next.js pages (SSR)
      include: [
        "src/features/vitalia/schemas/**",
        "src/features/vitalia/api/**",
        "src/features/fidelizacion/store/**",
        "src/features/fidelizacion/types/**",
        "src/features/fidelizacion/copy.ts",
        "src/features/valeria/lib/**",
        "src/features/valeria/store/**",
        "src/features/valeria/hooks/**",
        "src/lib/**",
        "src/components/shared/**",
      ],
      exclude: [
        "src/features/vitalia/types/**",
        "src/features/vitalia/index.ts",
        // Hooks use Clerk + React Query — covered in T-fe-3+ component integration tests
        "src/features/vitalia/api/use-*.ts",
        // Fidelizacion hooks use Clerk + React Query — covered in component integration tests
        "src/features/fidelizacion/api/use-*.ts",
        // Shell/copilot rail use Clerk — covered by E2E (T-infra-8)
        "src/components/shared/shell/**",
        "src/components/shared/copilot-rail/**",
        "src/components/shared/phi/AuditedSection.tsx",
        "**/*.d.ts",
        "**/node_modules/**",
      ],
      thresholds: {
        statements: 20,
        branches: 20,
        functions: 20,
        lines: 20,
      },
    },
  },
});
