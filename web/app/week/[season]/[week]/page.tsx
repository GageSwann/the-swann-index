import type { Metadata } from "next"
import { notFound } from "next/navigation"
import { Suspense } from "react"

import { BoardView } from "@/components/board/board-view"
import { WeekNav } from "@/components/board/week-nav"
import { PageHeading } from "@/components/layout/page-heading"
import { getMeta, getRankings, getWeekGames } from "@/lib/api/queries"

type Props = PageProps<"/week/[season]/[week]">

/** Prerender the current week; other weeks render on first visit and are cached. */
export async function generateStaticParams() {
  const meta = await getMeta()
  return [{ season: String(meta.season), week: String(Math.max(1, meta.week)) }]
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { season, week } = await params
  return { title: `Week ${week}, ${season}` }
}

export default function WeekPage(props: Props) {
  return (
    <Suspense
      fallback={<PageHeading title="This week">Loading the week&apos;s games.</PageHeading>}
    >
      <Board {...props} />
    </Suspense>
  )
}

async function Board({ params }: Props) {
  const raw = await params
  const season = Number(raw.season)
  const week = Number(raw.week)
  if (!Number.isInteger(season) || !Number.isInteger(week) || week < 1) notFound()

  const [board, rankings, meta] = await Promise.all([
    getWeekGames(season, week),
    getRankings({ season }).catch(() => null),
    getMeta(),
  ])
  const ranks = Object.fromEntries((rankings?.teams ?? []).map((t) => [t.team.id, t.rank]))
  const isCurrent = meta.season === season && meta.week === week

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <PageHeading title={`Week ${week}, ${season}`}>
          {isCurrent ? "This week's games. " : ""}TSI&apos;s projected score and win probability for
          every game with an FBS team, next to the betting market.
        </PageHeading>
        <div className="mb-6">
          <WeekNav season={season} week={week} />
        </div>
      </div>
      {board.games.length === 0 ? (
        <p className="text-muted-foreground">
          No games with an FBS team are scheduled for week {week}.
        </p>
      ) : (
        <BoardView games={board.games} ranks={ranks} />
      )}
    </>
  )
}
