/**
 * clerk.setup.ts — Vitalia Clerk auth setup project (canonical pattern)
 *
 * Adapted from nicolify/frontend/e2e/setup/clerk.setup.ts per playwright-expert SSoT.
 *
 * Lifecycle:
 *  1. clerkSetup() — fetch testing token via CLERK_SECRET_KEY (bypasses Turnstile + bot heuristics)
 *  2. isAuthFileFresh() — 4h mtime + cf_bm expiry + Clerk session cookie gates
 *  3. signIn via @clerk/testing programmatic API (password strategy)
 *  4. Wait for window.Clerk.loaded + window.Clerk.session before saving storageState
 *  5. Retry 3x linear backoff on failure with sign-out between attempts
 *
 * Run:
 *   E2E_BASE_URL=http://localhost:3002 \
 *   E2E_CLERK_USER_EMAIL=dr.demo@vitalialat.com \
 *   E2E_CLERK_USER_PASSWORD='DrDemo2026!' \
 *   E2E_TENANT_ID=e69a691d-070e-5caf-a053-6e74642ec100 \
 *   npx playwright test --project=setup
 *
 * Output: vitalia/frontend/playwright/.clerk/user.json (gitignored)
 */
import {
  clerk,
  clerkSetup,
  setupClerkTestingToken,
} from "@clerk/testing/playwright";
import { test as setup } from "@playwright/test";
import fs from "fs";
import path from "path";

setup.describe.configure({ mode: "serial" });

const authFile = path.join(__dirname, "../../playwright/.clerk/user.json");
const FRESH_WINDOW_MS = 4 * 60 * 60 * 1000;
const CF_BM_SAFETY_MARGIN_S = 5 * 60;
const SIGNIN_RETRIES = 2;
const SIGNIN_BACKOFF_MS = 3_000;

function isAuthFileFresh(): boolean {
  if (!fs.existsSync(authFile)) return false;
  try {
    const stat = fs.statSync(authFile);
    const ageMs = Date.now() - stat.mtimeMs;
    if (ageMs > FRESH_WINDOW_MS) return false;

    const raw = JSON.parse(fs.readFileSync(authFile, "utf-8")) as {
      cookies?: Array<{ name: string; expires?: number }>;
    };
    const cookies = raw.cookies ?? [];
    if (cookies.length === 0) return false;

    const nowS = Math.floor(Date.now() / 1000);
    const cfBm = cookies.find((c) => c.name === "__cf_bm");
    if (cfBm?.expires && cfBm.expires - nowS < CF_BM_SAFETY_MARGIN_S)
      return false;

    const clerkSession = cookies.find(
      (c) => c.name.startsWith("__session") || c.name.startsWith("__client"),
    );
    if (!clerkSession) return false;

    return true;
  } catch {
    return false;
  }
}

function wipeAuthFile(): void {
  if (fs.existsSync(authFile)) {
    fs.unlinkSync(authFile);
    console.log("[clerk.setup] wiped stale auth file");
  }
}

setup("clerk setup", async () => {
  await clerkSetup();
});

setup("authenticate", async ({ page }) => {
  setup.setTimeout(180_000);

  if (isAuthFileFresh()) {
    console.log("[clerk.setup] auth file fresh — skipping re-auth");
    return;
  }

  wipeAuthFile();
  fs.mkdirSync(path.dirname(authFile), { recursive: true });

  await setupClerkTestingToken({ page });

  const email = process.env.E2E_CLERK_USER_EMAIL!;

  let lastErr: unknown;
  for (let attempt = 1; attempt <= SIGNIN_RETRIES + 1; attempt++) {
    try {
      // Visit /sign-in to bootstrap Clerk in the browser (sets __clerk_db_jwt dev cookie + loads Clerk SDK).
      await page.goto("/sign-in", {
        waitUntil: "networkidle",
        timeout: 60_000,
      });

      // Use ticket strategy (sign-in token) — bypasses two-step email/password UI flow.
      // @clerk/testing creates a server-side signInToken via CLERK_SECRET_KEY, then
      // page.evaluate triggers Clerk.client.signIn.create({strategy:'ticket', ticket:token})
      // + setActive. Waits for window.Clerk.user automatically (more reliable than session).
      await clerk.signIn({ page, emailAddress: email });

      // Navigate to dashboard root to trigger middleware acceptance + verify session is active.
      await page.goto("/", { waitUntil: "networkidle", timeout: 60_000 });

      // Sanity check: confirm we are NOT on /sign-in (would mean session not established).
      const currentUrl = page.url();
      if (currentUrl.includes("/sign-in")) {
        throw new Error(
          `Post-signIn navigation landed on /sign-in (session not active): ${currentUrl}`,
        );
      }

      await page.waitForFunction(
        () => {
          const w = window as unknown as {
            Clerk?: { session?: unknown; user?: unknown; loaded?: boolean };
          };
          return Boolean(w.Clerk?.loaded) && Boolean(w.Clerk?.user);
        },
        null,
        { timeout: 30_000 },
      );

      await page.context().storageState({ path: authFile });
      console.log(`[clerk.setup] auth state saved (attempt ${attempt})`);
      return;
    } catch (err) {
      lastErr = err;
      const msg = err instanceof Error ? err.message : String(err);
      console.warn(`[clerk.setup] attempt ${attempt} failed: ${msg}`);
      try {
        await page.evaluate(async () => {
          const w = window as unknown as {
            Clerk?: { signOut?: () => Promise<void> };
          };
          await w.Clerk?.signOut?.();
        });
      } catch {
        /* best-effort */
      }
      wipeAuthFile();
      if (attempt <= SIGNIN_RETRIES) {
        await new Promise((r) => setTimeout(r, SIGNIN_BACKOFF_MS * attempt));
      }
    }
  }
  throw new Error(
    `Clerk auth failed after ${SIGNIN_RETRIES + 1} attempts: ${String(lastErr)}`,
  );
});
