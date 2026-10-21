import Link from "next/link"

const LAST_REGULAR_WEEK = 16

/** Previous / next week links (regular season weeks 1–16). */
export function WeekNav({ season, week }: { season: number; week: number }) {
  return (
    <nav aria-label="Weeks" className="flex items-center gap-2 text-sm">
      {week > 1 ? (
        <Link
          href={`/week/${season}/${week - 1}`}
          className="rounded-md border border-border bg-card px-3 py-1.5 hover:text-primary"
        >
          ‹ Week {week - 1}
        </Link>
      ) : null}
      {week < LAST_REGULAR_WEEK ? (
        <Link
          href={`/week/${season}/${week + 1}`}
          className="rounded-md border border-border bg-card px-3 py-1.5 hover:text-primary"
        >
          Week {week + 1} ›
        </Link>
      ) : null}
    </nav>
  )
}
