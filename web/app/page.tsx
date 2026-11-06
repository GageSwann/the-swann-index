import { type HomePicks, HomeView } from "@/components/home/home-view"
import { PageHeading } from "@/components/layout/page-heading"
import { getGamesOfWeek, getMeta, getRankings } from "@/lib/api/queries"
import type { GameSummary, RankedTeam, RankingType } from "@/lib/api/types"
import type { Division } from "@/lib/divisions"
import { formatDay, formatKickoff } from "@/lib/format/time"

const DIVISIONS: Division[] = ["fbs", "fcs"]
const TYPES: RankingType[] = ["power", "resume"]

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
  const [rankings, week] = await Promise.all([
    Promise.all(
      DIVISIONS.flatMap((division) =>
        TYPES.map((type) => getRankings({ type, division }).catch(() => null)),
      ),
    ),
    getGamesOfWeek().catch(() => null),
  ])
  const ranking = (d: Division, t: RankingType): RankedTeam[] =>
    rankings[DIVISIONS.indexOf(d) * TYPES.length + TYPES.indexOf(t)]?.teams ?? []

  const rails = Object.fromEntries(
    DIVISIONS.map((d) => [d, { power: ranking(d, "power"), resume: ranking(d, "resume") }]),
  ) as Record<Division, Record<RankingType, RankedTeam[]>>

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

  return (
    <>
      <PageHeading title="Games of the week">
        Week {meta.week}, {meta.season}: the games TSI picked to watch, and the Top 25 in FBS and
        FCS.
      </PageHeading>
      <HomeView rails={rails} picks={picks} />
    </>
  )
}

function kickoff(game: GameSummary): string | null {
  if (!game.kickoff) return null
  return `${formatDay(game.kickoff)}, ${formatKickoff(game.kickoff, game.kickoff_tbd)}`
}
