import { TeamLink } from "@/components/team/team-link"
import { HeadCell } from "@/components/ui/head-cell"
import type { PlayoffTeam } from "@/lib/api/types"
import { chance } from "@/lib/format/numbers"
import { american } from "@/lib/format/odds"

const ROUNDS: { key: keyof PlayoffTeam; label: string; help: string }[] = [
  { key: "playoff_prob", label: "Playoff", help: "Makes the 12-team field" },
  { key: "bye_prob", label: "Bye", help: "A top-four seed (first-round bye)" },
  { key: "semifinal_prob", label: "Semis", help: "Reaches the semifinals" },
  { key: "final_prob", label: "Final", help: "Reaches the championship game" },
  { key: "champion_prob", label: "Title", help: "Wins the national title" },
]

/** Every team with a real chance, likeliest first: round-by-round odds and fair title odds. */
export function PlayoffOdds({ teams }: { teams: PlayoffTeam[] }) {
  return (
    <div className="overflow-x-auto rounded-md border border-border">
      <table className="w-full min-w-[720px] text-sm">
        <thead className="bg-card text-muted-foreground">
          <tr className="border-b border-border">
            <HeadCell>Team</HeadCell>
            <HeadCell align="right">Record</HeadCell>
            <HeadCell align="right" title="Today's Résumé rank, TSI's stand-in for the committee">
              Résumé
            </HeadCell>
            {ROUNDS.map((r) => (
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
              {ROUNDS.map((r) => (
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
  )
}
