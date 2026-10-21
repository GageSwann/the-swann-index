import Image from "next/image"
import Link from "next/link"

import type { TeamRef } from "@/lib/api/types"
import { teamColorVars } from "@/lib/format/color"

/**
 * Logo + school name, linking to the team page. A thin tick in the team's color
 * (contrast-checked per theme) sits before the logo: team colors are accents, never text.
 */
export function TeamLink({ team }: { team: TeamRef }) {
  return (
    <Link
      href={`/teams/${team.slug}`}
      className="group inline-flex min-w-0 items-center gap-2 font-medium"
    >
      <span
        aria-hidden
        className="h-5 w-0.75 shrink-0 rounded-full bg-[var(--team-light)] dark:bg-[var(--team-dark)]"
        style={teamColorVars(team)}
      />
      {/* Logos sit on a light chip so dark marks (navy, black, purple) stay visible at night. */}
      <span className="flex size-6.5 shrink-0 items-center justify-center rounded-sm bg-white">
        {team.logo_url && (
          <Image
            src={team.logo_url}
            alt=""
            width={20}
            height={20}
            className="size-5 object-contain"
          />
        )}
      </span>
      <span className="truncate underline-offset-4 group-hover:underline">{team.school}</span>
    </Link>
  )
}
