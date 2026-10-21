import type { Metadata } from "next"

import { PageHeading } from "@/components/layout/page-heading"

export const metadata: Metadata = { title: "Model" }

export default function ModelPage() {
  return (
    <PageHeading title="How the model works">
      What TSI measures, how it predicts games, and how accurate it has been. This page is being
      built.
    </PageHeading>
  )
}
