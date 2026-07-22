import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const routes = ["", "/dashboard", "/disponibilite", "/modules", "/parametres"];
  return routes.map((route) => ({
    url: `https://urim.pro${route}`,
    lastModified: new Date("2026-07-22T00:00:00.000Z"),
    changeFrequency: route === "" ? "weekly" : "monthly",
    priority: route === "" ? 1 : 0.8
  }));
}
