import { type HomePicks, HomeView } from "@/components/home/home-view"
import { PageHeading } from "@/components/layout/page-heading"
import { getGamesOfWeek, getMeta, getTopRankings } from "@/lib/api/queries"
import type { GameSummary, RankingType, TopTeam } from "@/lib/api/types"
import type { Division } from "@/lib/divisions"
import { weekLabel } from "@/lib/format/season"
import { formatDay, formatKickoff, formatUpdated } from "@/lib/format/time"

const DIVISIONS: Division[] = ["fbs", "fcs"]
const TYPES: RankingType[] = ["resume", "power"]

/**
 * Home (Phase 13.4, #141): the games of the week, picked by the nightly run with Sunday's
 * rankings and held all week, and both divisions' Top 25. The full rankings are at /rankings.
 */
export default async function HomePage() {
  const meta = await getMeta().catch(() => null)
  if (!meta) {
    return (
      <PageHeading title="The Swann Index">
        The TSI API didn&apos;t answer. Rankings and games appear once it&apos;s back.
      </PageHeading>
    )
  }
  // Each division's Power and Résumé Top 25 in one small read (#155), not full rankings.
  const [tops, week] = await Promise.all([
    Promise.all(DIVISIONS.map((division) => getTopRankings(division).catch(() => null))),
    getGamesOfWeek().catch(() => null),
  ])
  const rails = Object.fromEntries(
    DIVISIONS.map((d, i) => [d, { power: tops[i]?.power ?? [], resume: tops[i]?.resume ?? [] }]),
  ) as Record<Division, Record<RankingType, TopTeam[]>>

  const picks = Object.fromEntries(
    DIVISIONS.map((d) => [
      d,
      Object.fromEntries(
        TYPES.map((t) => {
          const pick = week?.picks.find((p) => p.division === d && p.ranking_type === t) ?? null
          return [t, { pick, when: pick ? kickoff(pick.game) : null }]
        }),
      ),
    ]),
  ) as HomePicks
  // The week and when the rankings were last updated (owner, #160; was in the header).
  const updated = tops[0]?.as_of ?? meta.ratings_updated_at
  const status = `${weekLabel(meta)}.${updated ? ` Updated ${formatUpdated(updated)}.` : ""}`

  return (
    <>
      {/* No visible heading (owner): the page opens on the ranking switch and the games. */}
      <h1 className="sr-only">The Swann Index: games of the week and Top 25</h1>
      <HomeView rails={rails} picks={picks} status={status} />
    </>
  )
}

function kickoff(game: GameSummary): string | null {
  if (!game.kickoff) return null
  return `${formatDay(game.kickoff)}, ${formatKickoff(game.kickoff, game.kickoff_tbd)}`
}
