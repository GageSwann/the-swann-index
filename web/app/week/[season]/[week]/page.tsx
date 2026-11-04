import type { Metadata } from "next"
import { Suspense } from "react"

import { WeekPage } from "@/components/board/week-page"
import { PageHeading } from "@/components/layout/page-heading"
import { getMeta } from "@/lib/api/queries"
import { pageMeta } from "@/lib/metadata"

type Props = PageProps<"/week/[season]/[week]">

/** Prerender the current week; other weeks render on first visit and are cached. */
export async function generateStaticParams() {
  const meta = await getMeta()
  return [{ season: String(meta.season), week: String(Math.max(1, meta.week)) }]
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { season, week } = await params
  return pageMeta({
    title: `Week ${week}, ${season}`,
    description: `TSI's projected scores and win probabilities for every week ${week} game, next to the betting market, with this week's TSI plays.`,
  })
}

export default function WeekRoute(props: Props) {
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
  return <WeekPage season={Number(raw.season)} week={Number(raw.week)} division="fbs" />
}
