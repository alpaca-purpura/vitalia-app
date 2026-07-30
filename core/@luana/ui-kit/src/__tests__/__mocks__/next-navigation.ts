// canon: design-system-canon.md §2.1-§2.2 · story-origin: core-ds-foundation
/**
 * Test stub for `next/navigation`.
 *
 * `@luana/ui-kit` consumes Next App Router hooks (useRouter/usePathname/useParams)
 * as a PEER provided by the consuming Next app — `next` is NOT a dependency of the
 * lib itself. The vitest env therefore has no `next/navigation` module to resolve.
 *
 * vitest.config aliases `next/navigation` to this stub so vite's import-analysis
 * resolves the path; individual tests still override behaviour with `vi.mock(...)`.
 *
 * These no-op defaults only run if a test forgets to vi.mock — they keep the module
 * resolvable and inert.
 */

export function useRouter() {
  return {
    push: () => {},
    replace: () => {},
    back: () => {},
    forward: () => {},
    refresh: () => {},
    prefetch: () => {},
  };
}

export function usePathname(): string {
  return "/";
}

export function useParams<T extends Record<string, string | string[]> = Record<string, string | string[]>>(): T {
  return {} as T;
}

export function useSearchParams(): URLSearchParams {
  return new URLSearchParams();
}
