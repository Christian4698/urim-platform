export type NavigationIcon = "home" | "dashboard" | "system" | "modules" | "settings";

export const navigationItems = [
  { href: "/", label: "Accueil", icon: "home" },
  { href: "/dashboard", label: "Dashboard", icon: "dashboard" },
  { href: "/donnees-sportives", label: "Données sportives", icon: "system" },
  { href: "/disponibilite", label: "Disponibilité", icon: "system" },
  { href: "/modules", label: "Modules", icon: "modules" },
  { href: "/parametres", label: "Paramètres", icon: "settings" }
] as const satisfies ReadonlyArray<{
  href: string;
  label: string;
  icon: NavigationIcon;
}>;
