import Link from "next/link"
import type { ReactNode } from "react"

import { WinProbBar } from "@/components/board/win-prob-bar"
import { TeamLogo } from "@/components/team/team-logo"
import { BorderLightRings, borderLightVars } from "@/components/ui/border-light"
import type { TeamProfile, TeamRef } from "@/lib/api/types"
import { points, record } from "@/lib/format/numbers"
import { cn } from "@/lib/utils"

type Side = {
  team: TeamRef
  profile: TeamProfile | null
  score: number | null | undefined
  shown?: ReactNode // replaces the score (e.g. switched by the game's phase, 13.5)
}

type Props = {
  away: Side
  home: Side
  neutral: boolean
  context: ReactNode // first line: kickoff, status, or "Hypothetical"
  note?: ReactNode // above the win-probability bar
  homeWinProb?: number | null
}

/**
 * The scoreboard panel of the game center: both teams with
 * records and ranks, the score (projected or final), and the win-probability bar. It is
 * the page's focal point, so it carries the border light in both teams' colors (#137).
 */
export function ScoreBoard({ away, home, neutral, context, note, homeWinProb }: Props) {
  return (
    <section
      aria-label="Matchup"
      className="tsi-border-light space-y-5 rounded-md border border-border bg-card p-5"
      style={borderLightVars(away.team, home.team)}
    >
      <BorderLightRings />
      <p className="text-sm text-muted-foreground">{context}</p>
      <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-3 sm:gap-6">
        <TeamScore side={away} />
        <span className="text-sm text-muted-foreground">{neutral ? "vs" : "at"}</span>
        <TeamScore side={home} alignEnd />
      </div>
      {homeWinProb != null && (
        <div className="space-y-2">
          {note && <p className="text-sm text-muted-foreground">{note}</p>}
          <WinProbBar homeProb={homeWinProb} home={home.team} away={away.team} />
        </div>
      )}
    </section>
  )
}

function TeamScore({ side, alignEnd = false }: { side: Side; alignEnd?: boolean }) {
  const { team, profile, score, shown } = side
  const r = profile?.ratings
  const ranks = r
    ? [r.rank_power && `#${r.rank_power} power`, r.rank_resume && `#${r.rank_resume} résumé`]
        .filter(Boolean)
        .join(", ")
    : ""
  return (
    <div className={cn("flex min-w-0 flex-col", alignEnd && "items-end text-right")}>
      <Link
        href={`/teams/${team.slug}`}
        // Phones: logo above the name, so long names ("Florida International") get the
        // column's full width; from `sm` up they sit side by side.
        className={cn(
          "flex min-w-0 flex-col gap-2 sm:flex-row sm:items-center sm:gap-3",
          alignEnd ? "items-end sm:flex-row-reverse" : "items-start",
        )}
      >
        <TeamLogo team={team} size={48} />
        <span className="max-w-full text-xl leading-tight font-bold [overflow-wrap:anywhere] font-stretch-condensed hover:underline sm:text-3xl">
          {team.school}
        </span>
      </Link>
      <p className="mt-1 text-sm text-muted-foreground">
        {profile ? record(profile.wins, profile.losses, profile.ties) : ""}
        {ranks && `, ${ranks}`}
      </p>
      <p className="mt-2 text-4xl font-bold font-stretch-condensed proportional-nums sm:text-5xl">
        {shown ?? (score == null ? "–" : points(score))}
      </p>
    </div>
  )
}
