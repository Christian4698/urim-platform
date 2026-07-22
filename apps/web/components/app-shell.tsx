"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { navigationItems, type NavigationIcon } from "../lib/navigation";
import { Icon } from "./icon";
import { StatusBadge } from "./dashboard-ui";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [navigationOpen, setNavigationOpen] = useState(false);
  const currentPage =
    navigationItems.find((item) =>
      item.href === "/" ? pathname === "/" : pathname.startsWith(item.href)
    )?.label ?? "URIM";

  return (
    <div className="app-shell">
      <a className="skip-link" href="#contenu-principal">
        Aller au contenu
      </a>

      <button
        aria-label="Fermer la navigation"
        className={navigationOpen ? "sidebar-backdrop is-visible" : "sidebar-backdrop"}
        onClick={() => setNavigationOpen(false)}
        tabIndex={navigationOpen ? 0 : -1}
        type="button"
      />

      <aside
        aria-label="Navigation principale"
        className={navigationOpen ? "sidebar is-open" : "sidebar"}
      >
        <div className="sidebar-header">
          <Link aria-label="URIM — Accueil" className="brand" href="/">
            <Image
              alt="URIM"
              className="brand-logo"
              height={72}
              priority
              src="/brand/logo/urim-logo-horizontal.svg"
              width={180}
            />
            <span>Sports Intelligence Platform</span>
          </Link>
          <button
            aria-label="Fermer le menu"
            className="icon-button sidebar-close"
            onClick={() => setNavigationOpen(false)}
            type="button"
          >
            <Icon height={20} name="x" width={20} />
          </button>
        </div>

        <nav className="nav-list">
          <span className="nav-label">Espace URIM</span>
          {navigationItems.map((item) => {
            const isActive =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

            return (
              <Link
                aria-current={isActive ? "page" : undefined}
                className={isActive ? "nav-link nav-link-active" : "nav-link"}
                href={item.href}
                key={item.href}
                onClick={() => setNavigationOpen(false)}
              >
                <Icon
                  className="nav-icon"
                  height={19}
                  name={item.icon as NavigationIcon}
                  width={19}
                />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-note">
          <div className="sidebar-note-heading">
            <Icon height={18} name="shield" width={18} />
            <strong>Périmètre sécurisé</strong>
          </div>
          <p>Lecture système uniquement. Aucun fournisseur, pari réel, live ou prédiction active.</p>
          <StatusBadge tone="success">Secrets hors frontend</StatusBadge>
        </div>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button
              aria-expanded={navigationOpen}
              aria-label="Ouvrir le menu"
              className="icon-button mobile-menu"
              onClick={() => setNavigationOpen(true)}
              type="button"
            >
              <Icon height={21} name="menu" width={21} />
            </button>
            <div className="topbar-title">
              <span>Console URIM</span>
              <strong>{currentPage}</strong>
            </div>
          </div>
          <div className="topbar-status" aria-label="État des fonctions sensibles">
            <span className="environment-pill">
              <span aria-hidden="true" className="status-dot" />
              Plateforme publique
            </span>
            <StatusBadge tone="neutral">v0.1.0</StatusBadge>
          </div>
        </header>

        <main className="content" id="contenu-principal" tabIndex={-1}>
          {children}
        </main>

        <footer className="app-footer">
          <span>© 2026 General Tech Consult</span>
          <span>URIM · Intelligence probabiliste, traçable et prudente</span>
        </footer>
      </div>
    </div>
  );
}
