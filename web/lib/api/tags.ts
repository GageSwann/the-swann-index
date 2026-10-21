// Cache tags (doc 02 "Caching & revalidation"). Every TSI read carries `ALL`, so the
// nightly run can refresh everything at once; the narrower tags allow targeted refreshes.
export const ALL = "tsi"
export const META = "meta"
export const RANKINGS = "rankings"
export const TEAMS = "teams"
export const LEDGER = "ledger"
export const REPORT = "report"

export const week = (season: number, week: number) => `week-${season}-${week}`
export const team = (slug: string) => `team-${slug}`
export const game = (id: number) => `game-${id}`
