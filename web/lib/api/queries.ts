import "server-only"

import { cacheLife, cacheTag } from "next/cache"

import { apiClient, orNull, required } from "./client"
import * as tags from "./tags"
import type {
  GameCenter,
  GamesOfWeek,
  Matchup,
  Meta,
  Playoff,
  RankingType,
  Rankings,
  SeasonType,
  TeamProfile,
  TeamRef,
  WeekBoard,
} from "./types"
import type { Division, DivisionView } from "@/lib/divisions"

// One cached function per API endpoint. Arguments are part of each cache key; every
// entry is tagged `tsi` plus a narrower tag (lib/api/tags.ts) for targeted refreshes.

export async function getMeta(): Promise<Meta> {
  "use cache"
  cacheLife("tsi")
  cacheTag(tags.ALL, tags.META)
  return required("/meta/current", await apiClient().GET("/meta/current"))
}

export async function getRankings(
  options: { season?: number; week?: number; type?: RankingType; division?: DivisionView } = {},
): Promise<Rankings | null> {
  "use cache"
  cacheLife("tsi")
  cacheTag(tags.ALL, tags.RANKINGS)
  const { season, week, type = "power", division = "fbs" } = options
  const result = await apiClient().GET("/rankings", {
    params: { query: { season, week, type, division } },
  })
  return orNull("/rankings", result)
}

/** Teams of a division (or "all": FBS and FCS), alphabetical: the matchup tool's picker. */
export async function getTeams(
  options: { season?: number; division?: DivisionView } = {},
): Promise<TeamRef[]> {
  "use cache"
  cacheLife("tsi")
  cacheTag(tags.ALL)
  const { season, division = "fbs" } = options
  return required(
    "/teams",
    await apiClient().GET("/teams", { params: { query: { season, division } } }),
  )
}

export async function getTeam(slug: string, season?: number): Promise<TeamProfile | null> {
  "use cache"
  cacheLife("tsi")
  cacheTag(tags.ALL, tags.team(slug))
  const result = await apiClient().GET("/teams/{slug}", {
    params: { path: { slug }, query: { season } },
  })
  return orNull(`/teams/${slug}`, result)
}

export async function getWeekGames(
  season: number,
  week: number,
  seasonType: SeasonType = "regular",
  division: DivisionView = "fbs",
): Promise<WeekBoard> {
  "use cache"
  cacheLife("tsi")
  cacheTag(tags.ALL, tags.week(season, week))
  const result = await apiClient().GET("/weeks/{season}/{week}/games", {
    params: { path: { season, week }, query: { season_type: seasonType, division } },
  })
  return required(`/weeks/${season}/${week}/games`, result)
}

/** This poll week's games of the week (picked with Sunday's rankings, held all week). */
export async function getGamesOfWeek(): Promise<GamesOfWeek> {
  "use cache"
  cacheLife("tsi")
  cacheTag(tags.ALL)
  return required("/games-of-week", await apiClient().GET("/games-of-week"))
}

export async function getGame(id: number): Promise<GameCenter | null> {
  "use cache"
  cacheLife("tsi")
  cacheTag(tags.ALL, tags.game(id))
  const result = await apiClient().GET("/games/{game_id}", {
    params: { path: { game_id: id } },
  })
  return orNull(`/games/${id}`, result)
}

/** Hypothetical game; `null` if either slug is unknown. Same teams twice is a caller bug. */
export async function getMatchup(
  home: string,
  away: string,
  neutral = false,
): Promise<Matchup | null> {
  "use cache"
  cacheLife("hours") // the API recomputes from its hourly cache of live inputs
  cacheTag(tags.ALL)
  const result = await apiClient().GET("/matchup", {
    params: { query: { home, away, neutral } },
  })
  return orNull("/matchup", result)
}

/** CFP or FCS playoff odds and a projected bracket; null outside the regular season. */
export async function getPlayoff(
  division: Division = "fbs",
  season?: number,
): Promise<Playoff | null> {
  "use cache"
  cacheLife("tsi")
  cacheTag(tags.ALL, tags.PLAYOFF)
  const result = await apiClient().GET("/playoff", { params: { query: { season, division } } })
  return orNull("/playoff", result)
}
