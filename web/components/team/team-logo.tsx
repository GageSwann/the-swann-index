import Image from "next/image"

import type { TeamRef } from "@/lib/api/types"
import { teamColorVars } from "@/lib/format/color"
import { cn } from "@/lib/utils"

/**
 * A team's logo on a white tile ringed in the team's color (owner, 2026-11-06): the white
 * keeps dark marks (navy, black, purple) visible on the black theme, and the ring makes the
 * tile read as a badge in both themes instead of a bare white square. The ring is the
 * contrast-checked team color for the current theme (lib/format/color.ts, `--light`).
 * Replaces the thin color tick that sat before team names.
 */
export function TeamLogo({
  team,
  size,
  priority = false,
  className,
}: {
  team: TeamRef
  size: number // the tile's width and height, in px
  priority?: boolean
  className?: string
}) {
  const logo = Math.round(size * 0.78)
  return (
    <span
      aria-hidden
      className={cn(
        "tsi-team-light inline-flex shrink-0 items-center justify-center bg-white ring-(--light)",
        size >= 40 ? "rounded-md ring-[1.5px]" : "rounded-sm ring-1",
        className,
      )}
      style={{ ...teamColorVars(team), width: size, height: size }}
    >
      {team.logo_url && (
        <Image
          src={team.logo_url}
          alt=""
          width={logo}
          height={logo}
          className="object-contain"
          style={{ width: logo, height: logo }}
          priority={priority}
        />
      )}
    </span>
  )
}
