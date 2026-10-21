import type { Metadata } from "next"

import { PageHeading } from "@/components/layout/page-heading"

export const metadata: Metadata = { title: "TSI Book" }

export default function BookPage() {
  return (
    <PageHeading title="TSI Book">
      Paper picks where TSI disagrees with the market, graded after every game. The ledger is being
      built.
    </PageHeading>
  )
}
