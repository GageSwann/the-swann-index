import { type HomePicks, HomeView } from "@/components/home/home-view"
import { PageHeading } from "@/components/layout/page-heading"
import { getGamesOfWeek, getMeta, getTopRankings } from "@/lib/api/queries"
import type { RankingType, TopTeam } from "@/lib/api/types"
import type { Division } from "@/lib/divisions"
import { weekName } from "@/lib/format/season"
import { formatUpdated, gameWhen } from "@/lib/format/time"

const DIVISIONS: Division[] = ["fbs", "fcs"]
const TYPES: RankingType[] = ["resume", "power"]

/**
 * College football's home (Phase 13.4, #141; at /cfb since #182, the site's own home is for
 * every sport): the games of the week, picked by the nightly run with Sunday's rankings and
 * held all week, and both divisions' Top 25. The full rankings are at /rankings.
 */
export default async function CfbHomePage() {
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
          return [t, { pick, when: pick ? gameWhen(pick.game) : null }]
        }),
      ),
    ]),
  ) as HomePicks
  // The week and when the rankings were last updated (owner, #160; was in the header).
  const updated = tops[0]?.as_of ?? meta.ratings_updated_at
  const status = {
    week: weekName(meta),
    season: meta.season,
    updated: updated ? formatUpdated(updated) : null,
  }

  return (
    <>
      {/* The page's heading is in the home toolbar (#197). */}
      <HomeView rails={rails} picks={picks} status={status} />
    </>
  )
}
