import type { Metadata, Viewport } from "next";
import { appConfig } from "@urim/config";
import { AppShell } from "../components/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://urim.pro"),
  applicationName: appConfig.appName,
  title: {
    default: "URIM — Sports Intelligence Platform",
    template: "%s | URIM"
  },
  description:
    "Plateforme d’intelligence sportive probabiliste, traçable et responsable. État système public et modules URIM.",
  keywords: [
    "URIM",
    "intelligence sportive",
    "analyse probabiliste",
    "Kairos",
    "traçabilité sportive"
  ],
  authors: [{ name: "General Tech Consult" }],
  creator: "General Tech Consult",
  publisher: "General Tech Consult",
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    locale: "fr_CD",
    siteName: "URIM",
    title: "URIM — Sports Intelligence Platform",
    description:
      "Une infrastructure d’intelligence sportive conçue pour la prudence, la traçabilité et l’explicabilité.",
    url: "https://urim.pro",
    images: [
      {
        url: "/brand/icons/urim-app-icon-1024.png",
        width: 1024,
        height: 1024,
        alt: "URIM"
      }
    ]
  },
  twitter: {
    card: "summary",
    title: "URIM — Sports Intelligence Platform",
    description: "Intelligence sportive probabiliste, traçable et responsable.",
    images: ["/brand/icons/urim-app-icon-1024.png"]
  },
  robots: { index: true, follow: true },
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
  },
  manifest: "/manifest.webmanifest",
  category: "technology"
};

export const viewport: Viewport = {
  colorScheme: "dark",
  themeColor: "#05070b",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html data-scroll-behavior="smooth" lang={appConfig.defaultLocale}>
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
