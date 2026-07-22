import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/" },
    sitemap: "https://urim.pro/sitemap.xml",
    host: "https://urim.pro"
  };
}
