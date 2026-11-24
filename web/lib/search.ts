import type { TeamRef } from "@/lib/api/types"

/**
 * The header's team search (owner, 2026-11-24, #193): every FBS and FCS team with its Résumé
 * rank in its division. The site serves the list once as a cached file (`/cfb/search-index`,
 * refreshed with the nightly run); matching runs in the browser, so typing never calls the
 * API. Plain data and pure functions only (shared by the server route and the client box).
 */
export type SearchTeam = { team: TeamRef; rank: number | null }

export const MAX_RESULTS = 8

/** Lower case, no accents or punctuation, single spaces: "San José St." → "san jose st". */
export function normalize(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, " ")
    .trim()
}

/** How well a name fits the query: 0 = the whole name, then its start, then a word's start. */
function fit(name: string, query: string): number | null {
  if (!name) return null
  if (name === query) return 0
  if (name.startsWith(query)) return 1
  if (` ${name}`.includes(` ${query}`)) return 2
  return null
}

/**
 * Teams matching the query, best first: school name (whole, then its start, then a word's
 * start), then mascot or abbreviation ("utes", "byu"). Ties go to ranked teams by rank, then
 * the name. Contains-anywhere matches ("tah") are left out: they mostly add noise.
 */
export function searchTeams(teams: SearchTeam[], query: string): SearchTeam[] {
  const q = normalize(query)
  if (!q) return []
  const scored: { entry: SearchTeam; score: number }[] = []
  for (const entry of teams) {
    const { school, mascot, abbreviation } = entry.team
    const bySchool = fit(normalize(school), q)
    const byOther = [fit(normalize(mascot ?? ""), q), fit(normalize(abbreviation ?? ""), q)]
      .filter((s): s is number => s !== null)
      .map((s) => s + 3)
    const score = Math.min(bySchool ?? Infinity, ...byOther)
    if (score !== Infinity) scored.push({ entry, score })
  }
  scored.sort(
    (a, b) =>
      a.score - b.score ||
      (a.entry.rank ?? Infinity) - (b.entry.rank ?? Infinity) ||
      a.entry.team.school.localeCompare(b.entry.team.school),
  )
  return scored.slice(0, MAX_RESULTS).map((s) => s.entry)
}
