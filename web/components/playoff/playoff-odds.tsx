import Link from "next/link"

import { TeamLink } from "@/components/team/team-link"
import { TeamLogo } from "@/components/team/team-logo"
import { HeadCell } from "@/components/ui/head-cell"
import type { PlayoffTeam } from "@/lib/api/types"
import type { Division } from "@/lib/divisions"
import { chance } from "@/lib/format/numbers"
import { american } from "@/lib/format/odds"
import { cfb } from "@/lib/routes"

type Column = { key: keyof PlayoffTeam; label: string; help: string }

const SEMIS: Column = { key: "semifinal_prob", label: "Semis", help: "Reaches the semifinals" }
const FINAL: Column = { key: "final_prob", label: "Final", help: "Reaches the championship game" }

const COLUMNS: Record<Division, Column[]> = {
  fbs: [
    { key: "playoff_prob", label: "Playoff", help: "Makes the 12-team field" },
    { key: "bye_prob", label: "Bye", help: "A top-four seed (first-round bye)" },
    SEMIS,
    FINAL,
    { key: "champion_prob", label: "Title", help: "Wins the national title" },
  ],
  fcs: [
    { key: "playoff_prob", label: "Playoff", help: "Makes the 24-team field" },
    { key: "bye_prob", label: "Bye", help: "A top-eight seed (first-round bye)" },
    { key: "quarterfinal_prob", label: "Quarters", help: "Reaches the quarterfinals" },
    SEMIS,
    FINAL,
    { key: "champion_prob", label: "Title", help: "Wins the FCS title" },
  ],
}

// Once the real field is set (#157), everyone listed is in it: no Playoff or Bye column.
const SET_FIELD = new Set<keyof PlayoffTeam>(["playoff_prob", "bye_prob"])

/** Every team with a real chance, likeliest first: round-by-round odds and fair title odds. */
export function PlayoffOdds({
  teams,
  division = "fbs",
  official = false,
}: {
  teams: PlayoffTeam[]
  division?: Division
  official?: boolean
}) {
  const columns = official
    ? COLUMNS[division].filter((c) => !SET_FIELD.has(c.key))
    : COLUMNS[division]
  return (
    <>
      <PhoneOdds teams={teams} official={official} />
      <div className="overflow-x-auto rounded-md border border-border max-sm:hidden">
        <table className="w-full min-w-[720px] text-sm">
          <thead className="bg-card text-muted-foreground">
            <tr className="border-b border-border">
              <HeadCell>Team</HeadCell>
              <HeadCell align="right">Record</HeadCell>
              <HeadCell align="right" title="Today's Résumé rank, TSI's stand-in for the committee">
                Résumé
              </HeadCell>
              {columns.map((r) => (
                <HeadCell key={r.key} align="right" title={r.help}>
                  {r.label}
                </HeadCell>
              ))}
              <HeadCell
                align="right"
                title="Fair odds to win the title: the chance as American odds, no vig"
              >
                Title odds
              </HeadCell>
            </tr>
          </thead>
          <tbody>
            {teams.map((t) => (
              <tr key={t.team.slug} className="border-b border-border last:border-0">
                <td className="px-3 py-2">
                  <TeamLink team={t.team} />
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {t.wins}-{t.losses}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {t.rank_resume ? `#${t.rank_resume}` : "—"}
                </td>
                {columns.map((r) => (
                  <td key={r.key} className="px-3 py-2 text-right tabular-nums">
                    {chance(t[r.key] as number)}
                  </td>
                ))}
                <td className="px-3 py-2 text-right tabular-nums">
                  {t.fair_odds.title == null ? "—" : american(t.fair_odds.title)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

/**
 * Phones only (#165): one row per team (logo, name, record), then the two chances that
 * matter most (making the field, or the semifinals once it's set; the title) and the fair
 * title odds. The full table with every round is on wider screens.
 */
function PhoneOdds({ teams, official }: { teams: PlayoffTeam[]; official: boolean }) {
  const first = official
    ? { key: "semifinal_prob" as const, label: "Semis" }
    : { key: "playoff_prob" as const, label: "Playoff" }
  const grid = "grid grid-cols-[minmax(0,1fr)_3.25rem_3.25rem_3.75rem] items-center gap-2 px-3"
  return (
    <div className="overflow-hidden rounded-md border border-border sm:hidden">
      <div
        className={`${grid} border-b border-border bg-card py-1.5 text-xs text-muted-foreground`}
      >
        <span>Team</span>
        <span className="text-right">{first.label}</span>
        <span className="text-right">Title</span>
        <span className="text-right" title="Fair odds to win the title, no vig">
          Odds
        </span>
      </div>
      <ol className="divide-y divide-border">
        {teams.map((t) => (
          <li key={t.team.slug}>
            <Link
              href={cfb.team(t.team.slug)}
              className={`${grid} min-h-12 py-1.5 active:bg-muted`}
            >
              <span className="flex min-w-0 items-center gap-2">
                <TeamLogo team={t.team} size={24} />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium">{t.team.school}</span>
                  <span className="block text-xs text-muted-foreground tabular-nums">
                    {t.wins}-{t.losses}
                    {t.rank_resume ? <span className="ml-2">Résumé #{t.rank_resume}</span> : null}
                  </span>
                </span>
              </span>
              <span className="text-right text-sm tabular-nums">{chance(t[first.key])}</span>
              <span className="text-right text-sm font-semibold tabular-nums">
                {chance(t.champion_prob)}
              </span>
              <span className="text-right text-xs text-muted-foreground tabular-nums">
                {t.fair_odds.title == null ? "—" : american(t.fair_odds.title)}
              </span>
            </Link>
          </li>
        ))}
      </ol>
    </div>
  )
}
