// canon: design-system-canon.md §2.1-§2.2 · story-origin: core-ds-foundation
/**
 * Ambient module shim for `next/navigation`.
 *
 * `@luana/ui-kit` consumes the Next App Router hooks as a PEER provided by the
 * consuming Next app — `next` is NOT a dependency of the lib (see peerDependencies).
 * Without `next` installed in the lib's own node_modules, `tsc --noEmit` cannot
 * resolve the `next/navigation` type declarations. This shim declares the minimal
 * surface the lib uses so the package type-checks standalone.
 *
 * In a real Next app the actual `next/navigation` types take precedence (the app
 * provides the real `next` package); this shim is inert there.
 */

declare module "next/navigation" {
  export interface AppRouterInstance {
    push(href: string, options?: { scroll?: boolean }): void;
    replace(href: string, options?: { scroll?: boolean }): void;
    back(): void;
    forward(): void;
    refresh(): void;
    prefetch(href: string): void;
  }

  export function useRouter(): AppRouterInstance;
  export function usePathname(): string;
  export function useParams<
    T extends Record<string, string | string[]> = Record<string, string | string[]>,
  >(): T;
  export function useSearchParams(): URLSearchParams;
}
