import type { MetadataRoute } from "next"

import { getMeta, getTeams } from "@/lib/api/queries"
import { SITE_URL } from "@/lib/site"

/** Main pages, the current week and every FBS and FCS team page (used once indexing is on). */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [meta, teams] = await Promise.all([getMeta(), getTeams({ division: "all" })])
  const week = `/week/${meta.season}/${Math.max(1, meta.week)}`
  const pages = [
    "",
    "/rankings/fcs",
    "/rankings/all",
    "/week",
    week,
    `${week}/fcs`,
    "/playoff",
    "/playoff/fcs",
    "/matchup",
  ]
  return [
    ...pages.map((path) => ({ url: `${SITE_URL}${path}`, changeFrequency: "daily" as const })),
    ...teams.map((t) => ({
      url: `${SITE_URL}/teams/${t.slug}`,
      changeFrequency: "daily" as const,
    })),
  ]
}
