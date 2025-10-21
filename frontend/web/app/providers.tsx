"use client";

import type { ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { IntlProvider } from "@/lib/i18n/IntlContext";
import { queryClient } from "@/lib/queryClient";

export function ClientProviders({ children }: { children: ReactNode }) {
  return (
    <IntlProvider>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </IntlProvider>
  );
}

