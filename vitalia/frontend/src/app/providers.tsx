// cap: __shared__
// story-origin: TBD
"use client";

import { ClerkProvider } from "@clerk/nextjs";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { useState } from "react";

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 1000 * 60 * 5, // 5 min default stale time
            retry: 2,
            refetchOnWindowFocus: false,
          },
        },
      }),
  );

  return (
    <ClerkProvider>
      <QueryClientProvider client={queryClient}>
        {/* ThemeProvider: next-themes SSR-safe. attribute="data-theme" sets <html data-theme="...">
         * defaultTheme="light" — no OS system theme (D1). storageKey namespaced (D4).
         * suppressHydrationWarning on <html lang="es"> in layout.tsx handles hydration mismatch.
         * See: vitalia-fase1-design-tokens-theme 03-arch.md § 2.1 + 03-arch.md § 2.2
         */}
        <ThemeProvider
          attribute="data-theme"
          defaultTheme="light"
          enableSystem={false}
          storageKey="vitalia-theme"
        >
          {children}
        </ThemeProvider>
      </QueryClientProvider>
    </ClerkProvider>
  );
}
