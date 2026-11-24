import type { TeamRef } from "@/lib/api/types"
import { cfb } from "@/lib/routes"
import { SPORTS } from "@/lib/sports"

/**
 * The header's team search (owner, 2026-11-24, #193): every FBS and FCS team with its Résumé
 * rank in its division. The site serves the list once as a cached file (`/cfb/search-index`,
 * refreshed with the nightly run); matching runs in the browser, so typing never calls the
 * API. Plain data and pure functions only (shared by the server route and the client box).
 */
export type SearchSport = "cfb" // CBB and CBASE join when their team pages exist
export type SearchTeam = { sport: SearchSport; team: TeamRef; rank: number | null }

/** The team's page in its own sport: the same school can have one per sport (owner). */
export function teamHref(entry: SearchTeam): string {
  return cfb.team(entry.team.slug)
}

/** The sport's short name shown on each result ("CFB"), from the header's sport list. */
export function sportLabel(sport: SearchSport): string {
  return SPORTS.find((s) => s.key === sport)?.label ?? sport.toUpperCase()
}

export const MAX_RESULTS = 8

/** Lower case, no accents or punctuation, single spaces: "San José St." → "san jose st". */
export function normalize(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
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
