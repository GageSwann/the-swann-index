import Link from "next/link"

import type { TeamRef } from "@/lib/api/types"

import { TeamLogo } from "./team-logo"

/**
 * Logo + school name, linking to the team page. The logo's ring carries the team's color
 * (team colors are accents, never text).
 */
export function TeamLink({ team }: { team: TeamRef }) {
  return (
    <Link
      href={`/teams/${team.slug}`}
      className="group inline-flex min-w-0 items-center gap-2 font-medium"
    >
      <TeamLogo team={team} size={26} className="mx-0.5" />
      <span className="truncate underline-offset-4 group-hover:underline">{team.school}</span>
    </Link>
  )
}
