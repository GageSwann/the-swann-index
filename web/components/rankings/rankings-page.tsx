import { PageHeading } from "@/components/layout/page-heading"
import { DivisionNav } from "@/components/ui/division-nav"
import { getRankings } from "@/lib/api/queries"
import type { RankingType } from "@/lib/api/types"
import type { DivisionView } from "@/lib/divisions"
import { formatShortDay, formatUpdated } from "@/lib/format/time"
import { cfb } from "@/lib/routes"

import { RankingsView } from "./rankings-view"

const TITLE: Record<DivisionView, string> = {
  fbs: "Rankings",
  fcs: "FCS rankings",
  all: "FBS and FCS rankings",
}

/**
 * One division's rankings page (decision #113): `/cfb/rankings` is FBS,
 * `/cfb/rankings/fcs` and `/cfb/rankings/all` the others. "All" is Power only: Résumé ranks stay
 * within a division. Each ranking has its own address (#205): Résumé at the division's page,
 * Power at `/power` under it, so the page arrives already showing it (no switch on load).
 */
export async function RankingsPage({
  division,
  type = "resume",
}: {
  division: DivisionView
  type?: RankingType
}) {
  const [power, resume] = await Promise.all([
    getRankings({ type: "power", division }).catch(() => null),
    division === "all"
      ? Promise.resolve(null)
      : getRankings({ type: "resume", division }).catch(() => null),
  ])
  // The division links keep the ranking shown (#205).
  const hrefs: Record<DivisionView, string> = {
    fbs: cfb.rankings("fbs", type),
    fcs: cfb.rankings("fcs", type),
    all: cfb.rankings("all"),
  }
  const nav = <DivisionNav current={division} hrefs={hrefs} label="Rankings division" />

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
        {/* Phones: the list's Δ heading and the movers panel say it (#164). */}
        {since && (
          <span className="max-sm:hidden"> Arrows show each team&apos;s move since {since}.</span>
        )}
      </PageHeading>
      {power.teams.length === 0 ? (
        <>
          <div className="mb-4">{nav}</div>
          <p className="max-w-[70ch] text-muted-foreground">
            FCS teams are ranked from the first nightly update after they started being rated
            individually (November 4, 2026). Check back after the next update.
          </p>
        </>
      ) : (
        <RankingsView
          nav={nav}
          power={power.teams}
          resume={resume?.teams ?? null}
          since={since}
          division={division}
          type={division === "all" ? "power" : type}
          benchmarkRank={resume?.benchmark_rank ?? null}
        />
      )}
    </>
  )
}
