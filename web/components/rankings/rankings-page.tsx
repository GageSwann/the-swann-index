import { PageHeading } from "@/components/layout/page-heading"
import { DivisionNav } from "@/components/ui/division-nav"
import { getRankings } from "@/lib/api/queries"
import type { DivisionView } from "@/lib/divisions"
import { formatShortDay, formatUpdated } from "@/lib/format/time"

import { RankingsView } from "./rankings-view"

const RANKINGS_HREF: Record<DivisionView, string> = {
  fbs: "/",
  fcs: "/rankings/fcs",
  all: "/rankings/all",
}

const TITLE: Record<DivisionView, string> = {
  fbs: "Rankings",
  fcs: "FCS rankings",
  all: "FBS and FCS rankings",
}

/**
 * One division's rankings page (decision #113): `/` is FBS, `/rankings/fcs` and
 * `/rankings/all` the others. "All" is Power only: Résumé ranks stay within a division.
 */
export async function RankingsPage({ division }: { division: DivisionView }) {
  const [power, resume] = await Promise.all([
    getRankings({ type: "power", division }).catch(() => null),
    division === "all"
      ? Promise.resolve(null)
      : getRankings({ type: "resume", division }).catch(() => null),
  ])
  const nav = <DivisionNav current={division} hrefs={RANKINGS_HREF} label="Rankings division" />

  if (power === null || (division !== "all" && resume === null)) {
    return (
      <>
        <PageHeading title={TITLE[division]}>
          Rankings aren&apos;t available right now: the TSI API didn&apos;t return them. They appear
          after the first daily ratings run of the season.
        </PageHeading>
        {nav}
      </>
    )
  }

  // Movement compares with the latest Sunday poll before this run (Phase 12.5, #134).
  const since = power.previous_as_of ? formatShortDay(power.previous_as_of) : null

  return (
    <>
      <PageHeading title={TITLE[division]}>
        Week {power.week}, {power.season}. Updated {formatUpdated(power.as_of)}.
        {since && ` Arrows show each team's move since ${since}.`}
      </PageHeading>
      <div className="mb-4">{nav}</div>
      {power.teams.length === 0 ? (
        <p className="max-w-[70ch] text-muted-foreground">
          FCS teams are ranked from the first nightly update after they started being rated
          individually (November 4, 2026). Check back after the next update.
        </p>
      ) : (
        <RankingsView
          power={power.teams}
          resume={resume?.teams ?? null}
          since={since}
          division={division}
          benchmarkRank={resume?.benchmark_rank ?? null}
        />
      )}
    </>
  )
}
