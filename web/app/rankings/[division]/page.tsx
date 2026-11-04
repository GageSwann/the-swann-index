import type { Metadata } from "next"
import { notFound, redirect } from "next/navigation"
import { Suspense } from "react"

import { PageHeading } from "@/components/layout/page-heading"
import { RankingsPage } from "@/components/rankings/rankings-page"
import type { DivisionView } from "@/lib/divisions"
import { pageMeta } from "@/lib/metadata"

type Props = PageProps<"/rankings/[division]">

const VIEWS = ["fcs", "all"] as const satisfies DivisionView[]

export function generateStaticParams() {
  return VIEWS.map((division) => ({ division }))
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { division } = await params
  return division === "fcs"
    ? pageMeta({
        title: "FCS rankings",
        description: "TSI Power and Résumé rankings for every FCS team, updated daily.",
      })
    : pageMeta({
        title: "FBS and FCS rankings",
        description: "Every FBS and FCS team on one TSI rating scale, updated daily.",
      })
}

export default function DivisionRankingsPage(props: Props) {
  return (
    <Suspense fallback={<PageHeading title="Rankings">Loading the rankings.</PageHeading>}>
      <View {...props} />
    </Suspense>
  )
}

async function View({ params }: Props) {
  const { division } = await params
  if (division === "fbs") redirect("/")
  if (!(VIEWS as readonly string[]).includes(division)) notFound()
  return <RankingsPage division={division as DivisionView} />
}
