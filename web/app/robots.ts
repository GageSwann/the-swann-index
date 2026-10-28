import type { MetadataRoute } from "next"

import { ALLOW_INDEXING, SITE_URL } from "@/lib/site"

/** Crawlers stay out until the owner sets ALLOW_INDEXING=1 (decision #86). */
export default function robots(): MetadataRoute.Robots {
  return ALLOW_INDEXING
    ? {
        rules: { userAgent: "*", allow: "/", disallow: "/api/" },
        sitemap: `${SITE_URL}/sitemap.xml`,
      }
    : { rules: { userAgent: "*", disallow: "/" } }
}
