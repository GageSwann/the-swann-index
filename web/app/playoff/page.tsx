import type { Metadata } from "next"

import { PlayoffPage } from "@/components/playoff/playoff-page"
import { pageMeta } from "@/lib/metadata"

export const metadata: Metadata = pageMeta({
  title: "Playoff",
  description:
    "TSI's College Football Playoff odds and projected 12-team bracket from 10,000 simulated seasons, with fair odds for the national title.",
})

export default function Page() {
  return <PlayoffPage division="fbs" />
}
