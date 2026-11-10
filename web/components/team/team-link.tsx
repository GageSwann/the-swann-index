import Link from "next/link"

import type { TeamRef } from "@/lib/api/types"

import { TeamLogo } from "./team-logo"

/**
 * Logo + school name, linking to the team page. The logo's ring carries the team's color
 * (team colors are accents, never text). A `rank` goes between the logo and the name:
 * (logo) #25 BYU (Phase 13.7).
 */
export function TeamLink({ team, rank }: { team: TeamRef; rank?: number | null }) {
  return (
    <Link
      href={`/teams/${team.slug}`}
      className="group inline-flex min-w-0 items-center gap-2 font-medium"
    >
      <TeamLogo team={team} size={26} className="mx-0.5" />
      {/* One text run: the rank sits a normal space from the name, not the flex gap. */}
      {/* The underline covers the rank too, like the home page cards. */}
      <span className="truncate underline-offset-4 group-hover:underline">
        {rank != null && (
          <>
            <span className="text-xs text-muted-foreground tabular-nums">#{rank}</span>{" "}
          </>
        )}
        {team.school}
      </span>
    </Link>
  )
}
