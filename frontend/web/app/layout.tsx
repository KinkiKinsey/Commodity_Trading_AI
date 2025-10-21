import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { ClientProviders } from "./providers";

type RootLayoutProps = {
  children: ReactNode;
};

export const metadata: Metadata = {
  title: "RingShell",
  description: "AI-driven commodity intelligence platform"
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="zh-CN">
      <body>
        <ClientProviders>{children}</ClientProviders>
      </body>
    </html>
  );
}
