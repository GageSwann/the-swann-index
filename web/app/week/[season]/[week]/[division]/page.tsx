import type { Metadata } from "next"
import { notFound, redirect } from "next/navigation"
import { Suspense } from "react"

import { WeekPage } from "@/components/board/week-page"
import { PageHeading } from "@/components/layout/page-heading"
import { getMeta } from "@/lib/api/queries"
import type { DivisionView } from "@/lib/divisions"
import { pageMeta } from "@/lib/metadata"

type Props = PageProps<"/week/[season]/[week]/[division]">

const VIEWS = ["fcs", "all"] as const satisfies DivisionView[]

/** Prerender the current week's FCS and combined boards; others render on first visit. */
export async function generateStaticParams() {
  const meta = await getMeta()
  const current = { season: String(meta.season), week: String(Math.max(1, meta.week)) }
  return VIEWS.map((division) => ({ ...current, division }))
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { season, week, division } = await params
  const which = division === "fcs" ? "FCS" : "FBS and FCS"
  return pageMeta({
    title: `Week ${week}, ${season}: ${which} games`,
    description: `TSI's projected scores and win probabilities for week ${week}'s ${which} games, next to the betting market.`,
  })
}

export default function DivisionWeekPage(props: Props) {
  return (
    <Suspense
      fallback={<PageHeading title="This week">Loading the week&apos;s games.</PageHeading>}
    >
      <Board {...props} />
    </Suspense>
  )
}

async function Board({ params }: Props) {
  const { season, week, division } = await params
  if (division === "fbs") redirect(`/week/${season}/${week}`)
  if (!(VIEWS as readonly string[]).includes(division)) notFound()
  return (
    <WeekPage season={Number(season)} week={Number(week)} division={division as DivisionView} />
  )
}
