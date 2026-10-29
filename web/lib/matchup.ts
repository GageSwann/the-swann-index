import "server-only"

import { getMatchup } from "@/lib/api/queries"
import type { Matchup } from "@/lib/api/types"

/** The matchup page lives in its query string (`?away=…&home=…&neutral=1`): shareable. */
export type MatchupPick = { away?: string; home?: string; neutral: boolean }

type Query = Record<string, string | string[] | undefined> | URLSearchParams

export function readPick(query: Query): MatchupPick {
  const get = (key: string) => {
    const v = query instanceof URLSearchParams ? query.get(key) : query[key]
    return (Array.isArray(v) ? v[0] : v) || undefined
  }
  return { away: get("away"), home: get("home"), neutral: get("neutral") === "1" }
}

export function matchupQuery({ away, home, neutral }: MatchupPick): string {
  const q = new URLSearchParams()
  if (away) q.set("away", away)
  if (home) q.set("home", home)
  if (neutral) q.set("neutral", "1")
  return q.toString()
}

/** TSI's price for two different picked teams; null when incomplete or unknown. */
export async function pricedMatchup({ away, home, neutral }: MatchupPick): Promise<Matchup | null> {
  if (!away || !home || away === home) return null
  return getMatchup(home, away, neutral).catch(() => null)
}
