// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * last-viewed-conv.ts — remembers the last conversation the operator was looking at.
 *
 * UI-AUDIT #1: entering the Inbox should re-open the conversation you last viewed
 * (or the newest one on a first visit). We persist ONLY the conversation UUID in
 * localStorage, scoped per tenant.
 *
 * HIPAA-lite: a conversation id is a UUID hash (NOT PHI) — safe to persist client-side.
 * NEVER store names/phone/email/diagnosis here (see inbox-store.ts PHI constraint).
 *
 * SSR-safe: every accessor guards `typeof window`.
 *
 * downstream-regression-na: brand-local FE util; no cross-brand consumers
 */

const KEY_PREFIX = "vitalia:inbox:lastConv:";

function key(tenantId: string): string {
  return `${KEY_PREFIX}${tenantId}`;
}

/** Returns the last-viewed conversation UUID for this tenant, or null. */
export function getLastViewedConv(tenantId: string): string | null {
  if (typeof window === "undefined" || !tenantId) return null;
  try {
    return window.localStorage.getItem(key(tenantId));
  } catch {
    return null;
  }
}

/** Persists the last-viewed conversation UUID for this tenant. */
export function setLastViewedConv(tenantId: string, convId: string): void {
  if (typeof window === "undefined" || !tenantId || !convId) return;
  try {
    window.localStorage.setItem(key(tenantId), convId);
  } catch {
    // Storage unavailable (private mode / quota) — non-fatal, auto-select falls
    // back to the newest conversation.
  }
}
