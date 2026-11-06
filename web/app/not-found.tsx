import Link from "next/link"

import { PageHeading } from "@/components/layout/page-heading"

export default function NotFound() {
  return (
    <PageHeading title="Page not found">
      There&apos;s no page at this address. Check the link, or go to the{" "}
      <Link
        href="/rankings"
        className="underline decoration-muted-foreground underline-offset-4 hover:decoration-foreground"
      >
        power rankings
      </Link>
      .
    </PageHeading>
  )
}
