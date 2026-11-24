import type { Metadata } from "next"
import { notFound } from "next/navigation"
import { Suspense } from "react"

import { PageHeading } from "@/components/layout/page-heading"
import { RankingsPage } from "@/components/rankings/rankings-page"
import { pageMeta } from "@/lib/metadata"

type Props = PageProps<"/cfb/rankings/[division]/power">

/** FCS Power at its own address (#205); "all" is Power already, FBS has `/cfb/rankings/power`. */
export function generateStaticParams() {
  return [{ division: "fcs" }]
}

export const metadata: Metadata = pageMeta({
  title: "FCS Power rankings",
  description: "TSI Power rankings for every FCS team, updated daily.",
})

export default function DivisionPowerRankingsPage(props: Props) {
  return (
    <Suspense fallback={<PageHeading title="Rankings">Loading the rankings.</PageHeading>}>
      <View {...props} />
    </Suspense>
  )
}

async function View({ params }: Props) {
  const { division } = await params
  if (division !== "fcs") notFound()
  return <RankingsPage division="fcs" type="power" />
}
