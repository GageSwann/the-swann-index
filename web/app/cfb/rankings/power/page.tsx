import type { Metadata } from "next"

import { RankingsPage } from "@/components/rankings/rankings-page"
import { pageMeta } from "@/lib/metadata"

export const metadata: Metadata = pageMeta({
  title: "Power rankings",
  description: "TSI Power rankings for every FBS team, updated daily.",
})

/** The FBS Power rankings at their own address (#205), so the page arrives showing Power. */
export default function FbsPowerRankingsPage() {
  return <RankingsPage division="fbs" type="power" />
}
