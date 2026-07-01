"use client";

import Image from "next/image";
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
          <Image
            alt={`${appConfig.appName} logo`}
            className="brand-logo"
            height={99}
            priority
            src="/brand/logo/urim-logo-horizontal.svg"
            width={220}
          />
          <span>Sports Intelligence Platform · Moteur {appConfig.engineName}</span>
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
            <div className="topbar-heading">
              <Image
                alt=""
                aria-hidden="true"
                className="topbar-symbol"
                height={44}
                src="/brand/logo/urim-symbol.svg"
                width={28}
              />
              <strong>Console URIM</strong>
            </div>
            <span>Locale {appConfig.defaultLocale} · Devise {appConfig.defaultCurrency}</span>
          </div>
          <StatusPill tone="warning">PLACEHOLDER — Phase future</StatusPill>
        </div>
        <div className="content">{children}</div>
      </main>
    </div>
  );
}
