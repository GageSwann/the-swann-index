import Image from "next/image"

import type { TeamRef } from "@/lib/api/types"
import { teamColorVars } from "@/lib/format/color"
import { cn } from "@/lib/utils"

// CFBD hosts every logo pre-sized, in a light and a dark version (`/logos/<px>/<id>.png`,
// `/logos-dark/<px>/<id>.png`), so the site picks the size it needs and loads it as is:
// no Vercel image transformations (#169).
const SIZES = [32, 48, 64, 96, 128, 256, 500]
const RATED = new Set(["fbs", "fcs"]) // every rated team has a dark logo (checked 2026-11-23)

function sized(url: string, px: number, dark: boolean): string {
  const size = SIZES.find((s) => s >= px) ?? 500
  return url.replace("/logos/500/", `${dark ? "/logos-dark/" : "/logos/"}${size}/`)
}

/**
 * A team's logo. Light theme: on a white tile ringed in the team's color (owner,
 * 2026-11-06). Dark theme: the team's dark-background logo on its own, no tile (owner,
 * 2026-11-23, #169), the way sports apps show them; teams without a dark logo (unrated
 * opponents) keep the white tile so dark marks stay visible.
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
  const url = team.logo_url
  const darkLogo = !!url && url.includes("/logos/500/") && RATED.has(team.division ?? "")
  // Without a tile (dark theme) the logo fills the whole space: no padding to leave.
  const img = (src: string, extra: string, dim: number) => (
    <Image
      src={src}
      alt=""
      width={dim}
      height={dim}
      unoptimized
      priority={priority}
      className={cn("object-contain", extra)}
      style={{ width: dim, height: dim }}
    />
  )
  return (
    <span
      aria-hidden
      className={cn(
        "tsi-team-light inline-flex shrink-0 items-center justify-center bg-white ring-(--light)",
        size >= 40 ? "rounded-md ring-[1.5px]" : "rounded-sm ring-1",
        darkLogo && "dark:bg-transparent dark:ring-0",
        className,
      )}
      style={{ ...teamColorVars(team), width: size, height: size }}
    >
      {url &&
        (darkLogo ? (
          <>
            {img(sized(url, logo * 2, false), "dark:hidden", logo)}
            {img(sized(url, size * 2, true), "hidden dark:block", size)}
          </>
        ) : (
          img(url.includes("/logos/500/") ? sized(url, logo * 2, false) : url, "", logo)
        ))}
    </span>
  )
}
