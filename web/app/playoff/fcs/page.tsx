import type { Metadata } from "next"

import { PlayoffPage } from "@/components/playoff/playoff-page"
import { pageMeta } from "@/lib/metadata"

export const metadata: Metadata = pageMeta({
  title: "FCS playoff",
  description:
    "TSI's FCS playoff odds and projected 24-team bracket from 10,000 simulated seasons, with fair odds for the FCS title.",
})

export default function Page() {
  return <PlayoffPage division="fcs" />
}
