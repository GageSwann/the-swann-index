import { notFound } from "next/navigation"

import { PageHeading } from "@/components/layout/page-heading"
import { DivisionNav } from "@/components/ui/division-nav"
import { getMeta, getRankings, getWeekGames } from "@/lib/api/queries"
import { DIVISION_NAME, type DivisionView } from "@/lib/divisions"

import { BoardView } from "./board-view"
import { WeekNav } from "./week-nav"

function weekHref(season: number, week: number, division: DivisionView = "fbs"): string {
  return `/week/${season}/${week}${division === "fbs" ? "" : `/${division}`}`
}

/**
 * One week's matchup board for a division (decision #113): every game with a team of that
 * division ("all": FBS or FCS). Card ranks are the division's own (FBS ranks in "all").
 */
export async function WeekPage({
  season,
  week,
  division,
}: {
  season: number
  week: number
  division: DivisionView
}) {
  if (!Number.isInteger(season) || !Number.isInteger(week) || week < 1) notFound()

  const [board, rankings, meta] = await Promise.all([
    getWeekGames(season, week, "regular", division),
    getRankings({ season, division: division === "fcs" ? "fcs" : "fbs" }).catch(() => null),
    getMeta(),
  ])
  const ranks = Object.fromEntries((rankings?.teams ?? []).map((t) => [t.team.id, t.rank]))
  const isCurrent = meta.season === season && meta.week === week
  const teams = division === "all" ? "an FBS or FCS team" : `an ${DIVISION_NAME[division]} team`

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <PageHeading title={`Week ${week}, ${season}`}>
          {isCurrent ? "This week's games. " : ""}TSI&apos;s projected score and win probability for
          every game with {teams}, next to the betting market.
          {division !== "fbs" && " TSI Plays are FBS-vs-FBS games only."}
        </PageHeading>
        <div className="mb-6 flex flex-wrap items-center gap-3">
          <DivisionNav
            current={division}
            label="Games shown"
            hrefs={{
              fbs: weekHref(season, week),
              fcs: weekHref(season, week, "fcs"),
              all: weekHref(season, week, "all"),
            }}
          />
          <WeekNav season={season} week={week} division={division} />
        </div>
      </div>
      {board.games.length === 0 ? (
        <p className="text-muted-foreground">
          No games with {teams} are scheduled for week {week}.
        </p>
      ) : (
        <BoardView games={board.games} ranks={ranks} />
      )}
    </>
  )
}
