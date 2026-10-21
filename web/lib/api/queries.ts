import "server-only"

import { cacheLife, cacheTag } from "next/cache"

import { apiClient, orNull, required } from "./client"
import * as tags from "./tags"
import type {
  GameCenter,
  Ledger,
  Matchup,
  Meta,
  ModelReport,
  RankingType,
  Rankings,
  SeasonType,
  TeamProfile,
  TeamRef,
  WeekBoard,
} from "./types"

// One cached function per API endpoint. Arguments are part of each cache key; every
// entry is tagged `tsi` plus a narrower tag (lib/api/tags.ts) for targeted refreshes.

export async function getMeta(): Promise<Meta> {
  "use cache"
  cacheLife("tsi")
  cacheTag(tags.ALL, tags.META)
  return required("/meta/current", await apiClient().GET("/meta/current"))
}

export async function getRankings(
  options: { season?: number; week?: number; type?: RankingType } = {},
): Promise<Rankings | null> {
  "use cache"
  cacheLife("tsi")
  cacheTag(tags.ALL, tags.RANKINGS)
  const { season, week, type = "power" } = options
  const result = await apiClient().GET("/rankings", {
    params: { query: { season, week, type } },
  })
  return orNull("/rankings", result)
}

export async function getTeams(season?: number): Promise<TeamRef[]> {
  "use cache"
  cacheLife("tsi")
  cacheTag(tags.ALL, tags.TEAMS)
  return required("/teams", await apiClient().GET("/teams", { params: { query: { season } } }))
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
): Promise<WeekBoard> {
  "use cache"
  cacheLife("tsi")
  cacheTag(tags.ALL, tags.week(season, week))
  const result = await apiClient().GET("/weeks/{season}/{week}/games", {
    params: { path: { season, week }, query: { season_type: seasonType } },
  })
  return required(`/weeks/${season}/${week}/games`, result)
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

export async function getLedger(season?: number): Promise<Ledger> {
  "use cache"
  cacheLife("tsi")
  cacheTag(tags.ALL, tags.LEDGER)
  const result = await apiClient().GET("/book/ledger", { params: { query: { season } } })
  return required("/book/ledger", result)
}

export async function getModelReport(season?: number): Promise<ModelReport> {
  "use cache"
  cacheLife("tsi")
  cacheTag(tags.ALL, tags.REPORT)
  const result = await apiClient().GET("/model/report", { params: { query: { season } } })
  return required("/model/report", result)
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
