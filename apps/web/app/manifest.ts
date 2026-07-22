import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "URIM — Sports Intelligence Platform",
    short_name: "URIM",
    description: "Intelligence sportive probabiliste, traçable et responsable.",
    start_url: "/",
    display: "standalone",
    background_color: "#05070b",
    theme_color: "#05070b",
    lang: "fr-CD",
    icons: [
      {
        src: "/brand/icons/urim-app-icon-1024.png",
        sizes: "1024x1024",
        type: "image/png",
        purpose: "any"
      }
    ]
  };
}
