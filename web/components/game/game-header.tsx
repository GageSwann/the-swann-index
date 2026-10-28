import Image from "next/image"
import Link from "next/link"

import { WinProbBar } from "@/components/board/win-prob-bar"
import type { GameSummary, TeamProfile, TeamRef } from "@/lib/api/types"
import { record } from "@/lib/format/numbers"
import { formatDay, formatKickoff } from "@/lib/format/time"
import { cn } from "@/lib/utils"

type Props = { game: GameSummary; home: TeamProfile | null; away: TeamProfile | null }

/** Both teams, records and ranks, kickoff, projected (or final) score, win probability. */
export function GameHeader({ game, home, away }: Props) {
  const p = game.prediction
  const final = game.result?.final === true
  const when = game.kickoff
    ? `${formatDay(game.kickoff)}, ${formatKickoff(game.kickoff, game.kickoff_tbd)}`
    : "Date to be announced"

  return (
    <section aria-label="Matchup" className="space-y-5 rounded-md border border-border bg-card p-5">
      <p className="text-sm text-muted-foreground">
        {when}
        {game.neutral && ". Neutral site"}
        {game.notes && `. ${game.notes}`}
        {final ? ". Final" : p?.locked ? ". In progress" : ""}
      </p>
      <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-3 sm:gap-6">
        <Side
          team={game.away}
          profile={away}
          score={final ? game.result?.away_points : p?.proj_away}
        />
        <span className="text-sm text-muted-foreground">{game.neutral ? "vs" : "at"}</span>
        <Side
          team={game.home}
          profile={home}
          score={final ? game.result?.home_points : p?.proj_home}
          alignEnd
        />
      </div>
      {p && (
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">
            {final
              ? `TSI projected ${game.away.school} ${Math.round(p.proj_away)}, ${game.home.school} ${Math.round(p.proj_home)}.`
              : "Projected score and win probability from TSI's latest prediction."}
          </p>
          <WinProbBar homeProb={p.home_win_prob} home={game.home} away={game.away} />
        </div>
      )}
    </section>
  )
}

function Side({
  team,
  profile,
  score,
  alignEnd = false,
}: {
  team: TeamRef
  profile: TeamProfile | null
  score?: number | null
  alignEnd?: boolean
}) {
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
        <span className="flex size-12 shrink-0 items-center justify-center rounded-md bg-white">
          {team.logo_url && (
            <Image
              src={team.logo_url}
              alt=""
              width={40}
              height={40}
              className="size-10 object-contain"
            />
          )}
        </span>
        <span className="max-w-full text-xl leading-tight font-bold [overflow-wrap:anywhere] font-stretch-condensed hover:underline sm:text-3xl">
          {team.school}
        </span>
      </Link>
      <p className="mt-1 text-sm text-muted-foreground">
        {profile ? record(profile.wins, profile.losses, profile.ties) : ""}
        {ranks && `, ${ranks}`}
      </p>
      <p className="mt-2 text-4xl font-bold font-stretch-condensed proportional-nums sm:text-5xl">
        {score == null ? "–" : Math.round(score)}
      </p>
    </div>
  )
}
