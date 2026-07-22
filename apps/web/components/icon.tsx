import type { SVGProps } from "react";

export type IconName =
  | "arrow"
  | "dashboard"
  | "home"
  | "menu"
  | "modules"
  | "refresh"
  | "settings"
  | "shield"
  | "system"
  | "x";

const paths: Record<IconName, string[]> = {
  arrow: ["M5 12h14", "m13 6 6 6-6 6"],
  dashboard: ["M4 4h6v6H4z", "M14 4h6v10h-6z", "M4 14h6v6H4z", "M14 18h6v2h-6z"],
  home: ["m3 11 9-8 9 8", "M5 10v10h14V10", "M9 20v-6h6v6"],
  menu: ["M4 7h16", "M4 12h16", "M4 17h16"],
  modules: ["M4 4h6v6H4z", "M14 4h6v6h-6z", "M4 14h6v6H4z", "M14 14h6v6h-6z"],
  refresh: ["M20 11a8 8 0 1 0-2.34 5.66", "M20 4v7h-7"],
  settings: [
    "M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z",
    "M19.4 15a1.7 1.7 0 0 0 .34 1.88l.04.04-2 3.46-.06-.02a1.7 1.7 0 0 0-1.8-.36l-.68.4a1.7 1.7 0 0 0-.86 1.63V22h-4v-.08a1.7 1.7 0 0 0-.86-1.53l-.68-.39a1.7 1.7 0 0 0-1.8.36l-.06.02-2-3.46.04-.04A1.7 1.7 0 0 0 4.6 15l-.68-.4A1.7 1.7 0 0 0 2 14.68v-4a1.7 1.7 0 0 0 1.92.08l.68-.4a1.7 1.7 0 0 0 .34-1.88l-.04-.04 2-3.46.06.02a1.7 1.7 0 0 0 1.8.36l.68-.4A1.7 1.7 0 0 0 10.3 3.4V3h4v.4a1.7 1.7 0 0 0 .86 1.53l.68.4a1.7 1.7 0 0 0 1.8-.36l.06-.02 2 3.46-.04.04a1.7 1.7 0 0 0-.34 1.88l.68.4a1.7 1.7 0 0 0 1.92-.08v4A1.7 1.7 0 0 0 20 14.6Z"
  ],
  shield: ["M12 3 4.5 6v5.5c0 4.6 3 7.6 7.5 9.5 4.5-1.9 7.5-4.9 7.5-9.5V6z", "m9 12 2 2 4-4"],
  system: ["M4 5h16v11H4z", "M8 20h8", "M12 16v4"],
  x: ["M6 6l12 12", "M18 6 6 18"]
};

export function Icon({ name, ...props }: { name: IconName } & SVGProps<SVGSVGElement>) {
  return (
    <svg
      aria-hidden="true"
      fill="none"
      focusable="false"
      viewBox="0 0 24 24"
      {...props}
    >
      {paths[name].map((path) => (
        <path
          d={path}
          key={path}
          stroke="currentColor"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="1.75"
        />
      ))}
    </svg>
  );
}
