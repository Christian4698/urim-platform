import type { Metadata } from "next";
import { appConfig } from "@urim/config";
import { AppShell } from "../components/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  applicationName: appConfig.appName,
  title: `${appConfig.appName} — Dashboard`,
  description: `${appConfig.appName}, dashboard Phase 1 du moteur ${appConfig.engineName}.`,
  icons: {
    icon: [
      { url: "/brand/icons/urim-favicon.svg", type: "image/svg+xml" },
      { url: "/brand/icons/urim-favicon.png", sizes: "512x512", type: "image/png" }
    ],
    apple: [
      {
        url: "/brand/icons/urim-app-icon-1024.png",
        sizes: "1024x1024",
        type: "image/png"
      }
    ]
  }
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang={appConfig.defaultLocale}>
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
