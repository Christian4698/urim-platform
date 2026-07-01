"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { appConfig } from "@urim/config";
import { StatusBadge } from "./dashboard-ui";
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
          <span>Sports Intelligence Platform · Internal intelligence console</span>
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
                <span className="nav-link-indicator" aria-hidden="true" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-note">
          <StatusBadge tone="cyan">Read-only skeleton</StatusBadge>
          <p>No provider feed, no real prediction, no stake execution.</p>
        </div>
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
            <span>
              Kairos engine · Locale {appConfig.defaultLocale} · Currency{" "}
              {appConfig.defaultCurrency}
            </span>
          </div>
          <div className="topbar-status">
            <StatusBadge tone="cyan">Kairos Signal · Read-only</StatusBadge>
            <StatusBadge tone="warning">Provider disabled</StatusBadge>
          </div>
        </div>
        <div className="content">{children}</div>
      </main>
    </div>
  );
}
