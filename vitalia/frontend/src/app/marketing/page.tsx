// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * /marketing — Server Component page for the marketing module.
 *
 * Architecture per 03-arch-fe.md § Page:
 *   - Server Component (no "use client" — metadata export possible)
 *   - nuqs server-side parsing via NuqsAdapter (set in providers.tsx)
 *   - Auth guard via Clerk auth() server-side
 *   - Delegates all interactivity to MarketingLayout (Client Component)
 *
 * Gherkin SC-MK-03: ?tab= URL param defaults to "attraction" (nuqs server-side).
 *
 * downstream-regression-na: brand-local FE page; no cross-brand consumers
 */
import type { Metadata } from "next";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { MarketingLayout, MARKETING_COPY } from "@/features/marketing";

export const metadata: Metadata = {
  title: `${MARKETING_COPY.pageTitle} — Vitalia`,
  description: MARKETING_COPY.pageSubtitle,
};

/**
 * Marketing page — delegates rendering to MarketingLayout (Client Component).
 * Server Component: auth verified server-side, no client overhead for auth.
 */
export default async function MarketingPage() {
  const { userId } = await auth();
  if (!userId) redirect("/sign-in");

  return (
    <main
      className="flex flex-col h-full overflow-hidden"
      aria-label={MARKETING_COPY.pageTitle}
    >
      <MarketingLayout />
    </main>
  );
}
