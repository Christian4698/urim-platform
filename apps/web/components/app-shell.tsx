"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { appConfig } from "@urim/config";
import { StatusPill } from "@urim/ui";
import { navigationItems } from "../lib/navigation";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Navigation principale">
        <div className="brand">
          <strong>{appConfig.appName}</strong>
          <span>Moteur {appConfig.engineName}</span>
        </div>

        <nav className="nav-list">
          {navigationItems.map((item) => {
            const isActive =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

            return (
              <Link
                aria-current={isActive ? "page" : undefined}
                className={isActive ? "nav-link nav-link-active" : "nav-link"}
                href={item.href}
                key={item.href}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <p className="sidebar-note">
          Phase 1 : aucun flux fournisseur, aucune prédiction réelle, aucune mise réelle.
        </p>
      </aside>

      <main className="main-area">
        <div className="topbar">
          <div className="topbar-title">
            <strong>Console URIM</strong>
            <span>Locale {appConfig.defaultLocale} · Devise {appConfig.defaultCurrency}</span>
          </div>
          <StatusPill tone="warning">PLACEHOLDER — Phase future</StatusPill>
        </div>
        <div className="content">{children}</div>
      </main>
    </div>
  );
}
