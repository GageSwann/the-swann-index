import type { MetadataRoute } from "next"

import { getMeta, getTeams } from "@/lib/api/queries"
import { cfb } from "@/lib/routes"
import { SITE_URL } from "@/lib/site"

/** Main pages, the current week and every FBS and FCS team page (used once indexing is on). */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [meta, teams] = await Promise.all([getMeta(), getTeams({ division: "all" })])
  const season = meta.season
  const week = Math.max(1, meta.week)
  const pages = [
    cfb.home,
    cfb.rankings(),
    cfb.rankings("fbs", "power"),
    cfb.rankings("fcs"),
    cfb.rankings("fcs", "power"),
    cfb.rankings("all"),
    cfb.schedule(),
    cfb.schedule(season, week),
    cfb.schedule(season, week, "fcs"),
    cfb.playoffs(),
    cfb.playoffs("fcs"),
  ]
  return [
    ...pages.map((path) => ({ url: `${SITE_URL}${path}`, changeFrequency: "daily" as const })),
    ...teams.map((t) => ({
      url: `${SITE_URL}${cfb.team(t.slug)}`,
      changeFrequency: "daily" as const,
    })),
  ]
}
