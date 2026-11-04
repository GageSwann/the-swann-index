import Link from "next/link"

import type { DivisionView } from "@/lib/divisions"

const LAST_REGULAR_WEEK = 16

/** Previous / next week links (regular season weeks 1–16), staying in the division. */
export function WeekNav({
  season,
  week,
  division = "fbs",
}: {
  season: number
  week: number
  division?: DivisionView
}) {
  const suffix = division === "fbs" ? "" : `/${division}`
  return (
    <nav aria-label="Weeks" className="flex items-center gap-2 text-sm">
      {week > 1 ? (
        <Link
          href={`/week/${season}/${week - 1}${suffix}`}
          className="rounded-md border border-border bg-card px-3 py-1.5 hover:text-primary"
        >
          ‹ Week {week - 1}
        </Link>
      ) : null}
      {week < LAST_REGULAR_WEEK ? (
        <Link
          href={`/week/${season}/${week + 1}${suffix}`}
          className="rounded-md border border-border bg-card px-3 py-1.5 hover:text-primary"
        >
          Week {week + 1} ›
        </Link>
      ) : null}
    </nav>
  )
}
