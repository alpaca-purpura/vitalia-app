/**
 * lane-auth.mjs — seed a Chrome DevTools MCP lane profile with a real Clerk session (HB-89).
 *
 * The Chrome DevTools MCP launches Chrome against a persistent per-lane profile
 * (~/.cache/chrome-devtools-mcp/luana-${brand}-${LUANA_LANE}). That profile is never
 * signed into Clerk → authenticated writes (POST/PATCH) the lane's MCP attempts redirect
 * to /sign-in. This script drives a HEADLESS Playwright persistent context against that
 * SAME profile dir, performs the exact @clerk/testing programmatic signIn used by the e2e
 * harness (vitalia/frontend/e2e/setup/clerk.setup.ts), then closes — the persistent context
 * flushes its cookie jar to disk natively (no SQLite surgery). Next time the MCP opens that
 * profile, the Clerk session cookies are already present.
 *
 * Invoked by scripts/lane-auth.sh with cwd = ${brand}/frontend (so node_modules resolve).
 * Required env (loaded by the wrapper from ${brand}/.env.dev):
 *   LANE_PROFILE_DIR  (resolved by the wrapper)
 *   E2E_BASE_URL
 *   E2E_CLERK_USER_EMAIL
 *   CLERK_SECRET_KEY                    (used by @clerk/testing to mint the sign-in token)
 *   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
 *   E2E_TENANT_ID                       (optional — informational)
 *
 * Mirrors the signIn ticket flow + waits from clerk.setup.ts verbatim.
 */
import { chromium } from "@playwright/test";
import {
  clerk,
  clerkSetup,
  setupClerkTestingToken,
} from "@clerk/testing/playwright";
import fs from "fs";
import path from "path";

const SIGNIN_RETRIES = 2;
const SIGNIN_BACKOFF_MS = 3_000;

function reqEnv(name) {
  const v = process.env[name];
  if (!v || v.trim() === "") {
    console.error(`[lane-auth] missing required env var: ${name}`);
    process.exit(2);
  }
  return v;
}

const profileDir = reqEnv("LANE_PROFILE_DIR");
const baseURL = reqEnv("E2E_BASE_URL");
const email = reqEnv("E2E_CLERK_USER_EMAIL");
reqEnv("CLERK_SECRET_KEY"); // consumed internally by @clerk/testing
reqEnv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY");

const markerFile = path.join(profileDir, ".lane-auth.ok");

async function main() {
  // clerkSetup() fetches the testing token via CLERK_SECRET_KEY (bypasses Turnstile + bot
  // heuristics) — same first step as clerk.setup.ts `setup("clerk setup")`.
  await clerkSetup();

  fs.mkdirSync(profileDir, { recursive: true });

  // Persistent context = the MCP's profile dir. Headless: we only need to flush cookies.
  const context = await chromium.launchPersistentContext(profileDir, {
    headless: true,
    baseURL,
  });

  let page;
  try {
    page = context.pages()[0] ?? (await context.newPage());

    await setupClerkTestingToken({ page });

    let lastErr;
    for (let attempt = 1; attempt <= SIGNIN_RETRIES + 1; attempt++) {
      try {
        // Visit /sign-in to bootstrap Clerk in the browser (sets __clerk_db_jwt dev cookie
        // + loads Clerk SDK) — verbatim from clerk.setup.ts.
        await page.goto("/sign-in", { waitUntil: "networkidle", timeout: 60_000 });

        // Ticket strategy (sign-in token) — @clerk/testing mints a server-side signInToken
        // via CLERK_SECRET_KEY, then triggers Clerk.client.signIn.create({strategy:'ticket'})
        // + setActive, waiting for window.Clerk.user automatically.
        await clerk.signIn({ page, emailAddress: email });

        // Navigate to root to trigger middleware acceptance + verify session is active.
        await page.goto("/", { waitUntil: "networkidle", timeout: 60_000 });

        const currentUrl = page.url();
        if (currentUrl.includes("/sign-in")) {
          throw new Error(
            `Post-signIn navigation landed on /sign-in (session not active): ${currentUrl}`,
          );
        }

        await page.waitForFunction(
          () => {
            const w = window;
            return Boolean(w.Clerk?.loaded) && Boolean(w.Clerk?.user);
          },
          null,
          { timeout: 30_000 },
        );

        // Persistent context flushes cookies to disk on close. Drop a freshness marker.
        fs.writeFileSync(markerFile, new Date().toISOString());
        console.log(`[lane-auth] lane profile seeded with Clerk session (attempt ${attempt})`);
        console.log(`[lane-auth] profile: ${profileDir}`);
        return;
      } catch (err) {
        lastErr = err;
        const msg = err instanceof Error ? err.message : String(err);
        console.warn(`[lane-auth] attempt ${attempt} failed: ${msg}`);
        try {
          await page.evaluate(async () => {
            await window.Clerk?.signOut?.();
          });
        } catch {
          /* best-effort */
        }
        if (attempt <= SIGNIN_RETRIES) {
          await new Promise((r) => setTimeout(r, SIGNIN_BACKOFF_MS * attempt));
        }
      }
    }
    throw new Error(
      `Clerk lane auth failed after ${SIGNIN_RETRIES + 1} attempts: ${String(lastErr)}`,
    );
  } finally {
    // Close flushes the cookie jar to the persistent profile dir natively.
    await context.close();
  }
}

main().catch((err) => {
  console.error(`[lane-auth] fatal: ${err instanceof Error ? err.stack : String(err)}`);
  process.exit(1);
});
