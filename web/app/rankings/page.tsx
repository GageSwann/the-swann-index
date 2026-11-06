import type { Metadata } from "next"

import { RankingsPage } from "@/components/rankings/rankings-page"
import { pageMeta } from "@/lib/metadata"

export const metadata: Metadata = pageMeta({
  title: "Rankings",
  description: "TSI Power and Résumé rankings for every FBS team, updated daily.",
})

/** The full FBS rankings (on `/` until the home page took that spot, Phase 13.4). */
export default function FbsRankingsPage() {
  return <RankingsPage division="fbs" />
}
