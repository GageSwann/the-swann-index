import type { Metadata } from "next"
import { Suspense } from "react"

import { PageHeading } from "@/components/layout/page-heading"
import { MatchupView } from "@/components/matchup/matchup-view"
import { matchupQuery, pricedMatchup, readPick } from "@/lib/matchup"
import { pageMeta } from "@/lib/metadata"

type Props = PageProps<"/matchup">

export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const pick = readPick(await searchParams)
  const m = await pricedMatchup(pick)
  if (!m) {
    return pageMeta({
      title: "Matchup",
      description: "How TSI would price any two FBS teams if they played today.",
      image: "/api/og/matchup",
    })
  }
  return pageMeta({
    title: `${m.away.school} ${pick.neutral ? "vs" : "at"} ${m.home.school} (hypothetical)`,
    description: `If they played today, TSI projects ${m.away.school} ${Math.round(m.proj_away)}, ${m.home.school} ${Math.round(m.proj_home)} (${m.home.school} ${Math.round(m.home_win_prob * 100)}% to win).`,
    image: `/api/og/matchup?${matchupQuery(pick)}`,
  })
}

export default function MatchupPage({ searchParams }: Props) {
  return (
    <div className="space-y-10">
      <PageHeading title="Matchup">
        Pick any two FBS teams to see how TSI would price the game if it were played today.
      </PageHeading>
      <Suspense fallback={<p className="text-muted-foreground">Loading teams.</p>}>
        <PickedMatchup searchParams={searchParams} />
      </Suspense>
    </div>
  )
}

async function PickedMatchup({ searchParams }: Pick<Props, "searchParams">) {
  return <MatchupView pick={readPick(await searchParams)} />
}
