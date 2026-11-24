import type { Meta } from "@/lib/api/types"

/** Where the season is: "Week 13, 2026", "Bowl season 2026", "Preseason 2026". */
/** The week alone, for the home page's status line: "Week 13", "Bowl season", "Preseason". */
export function weekName(meta: Pick<Meta, "season_type" | "week">): string {
  if (meta.season_type === "postseason") return "Bowl season"
  return meta.week > 0 ? `Week ${meta.week}` : "Preseason"
}

export function weekLabel(meta: Pick<Meta, "season" | "season_type" | "week">): string {
  if (meta.season_type === "postseason") return `Bowl season ${meta.season}`
  return meta.week > 0 ? `Week ${meta.week}, ${meta.season}` : `Preseason ${meta.season}`
}
