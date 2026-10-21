import type { Metadata } from "next"

import { PageHeading } from "@/components/layout/page-heading"

export const metadata: Metadata = { title: "This week" }

export default function WeekPage() {
  return (
    <PageHeading title="This week">
      Every game this week with TSI&apos;s projected score, win probability and the market line. The
      matchup board is being built.
    </PageHeading>
  )
}
