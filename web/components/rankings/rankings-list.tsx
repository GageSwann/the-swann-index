import Link from "next/link"

import type { RankedTeam, RankingType } from "@/lib/api/types"
import { teamColorVars } from "@/lib/format/color"
import { chance, record, signed } from "@/lib/format/numbers"

import { TeamLogo } from "../team/team-logo"
import { RankChange } from "./rank-change"

/**
 * Phones only (owner, 2026-11-23, #164): the rankings as a compact list instead of the wide
 * table. One row per team (rank, logo, name with its record under it, the ranking's key
 * number, the move since Sunday), the whole row opening the team page. The full table with
 * every column and sorting is on wider screens.
 */
export function RankingsList({
  teams,
  type,
  since,
}: {
  teams: RankedTeam[]
  type: RankingType
  since: string | null
}) {
  const resume = type === "resume"
  return (
    <div className="overflow-hidden rounded-md border border-border">
      <div className="grid grid-cols-[2rem_minmax(0,1fr)_4rem_2.5rem] items-center gap-2 border-b border-border bg-card px-3 py-2 text-xs text-muted-foreground">
        <span>#</span>
        <span>Team</span>
        <span className="text-right" title={resume ? "Strength of record" : "Rating"}>
          {resume ? "SOR" : "Rating"}
        </span>
        <span className="text-right" title={since ? `Move since ${since}` : undefined}>
          {since ? "Δ" : ""}
        </span>
      </div>
      <ol>
        {teams.map((t) => (
          <li
            key={t.team.id}
            className="tsi-team-light tsi-row-light border-b border-border last:border-0"
            style={teamColorVars(t.team)}
          >
            <Link
              href={`/teams/${t.team.slug}`}
              className="grid min-h-13 grid-cols-[2rem_minmax(0,1fr)_4rem_2.5rem] items-center gap-2 px-3 py-1.5 active:bg-muted"
            >
              <span className="text-base font-semibold tabular-nums">{t.rank}</span>
              <span className="flex min-w-0 items-center gap-2.5">
                <TeamLogo team={t.team} size={28} />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium">{t.team.school}</span>
                  <span className="block truncate text-xs text-muted-foreground tabular-nums">
                    {record(t.wins, t.losses, t.ties)}
                    {t.team.conference && <span className="ml-2">{t.team.conference}</span>}
                  </span>
                </span>
              </span>
              <span className="text-right text-sm tabular-nums">
                {resume ? (t.sor == null ? "—" : chance(t.sor, 1)) : signed(t.rating)}
              </span>
              <span className="text-right text-xs">
                {since && t.previous_rank !== null && (
                  <RankChange rank={t.rank} previous={t.previous_rank} />
                )}
              </span>
            </Link>
          </li>
        ))}
      </ol>
    </div>
  )
}
