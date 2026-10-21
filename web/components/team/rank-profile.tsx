import type { RankedTeam } from "@/lib/api/types"
import { signed } from "@/lib/format/numbers"

type Row = { label: string; rank: number | null | undefined; value?: string }

/**
 * Where the team ranks among rated FBS teams: power, résumé, offense, defense. Bar
 * length is the share of teams it ranks ahead of (ranks come from the API).
 */
export function RankProfile({ row, count }: { row: RankedTeam; count: number }) {
  const rows: Row[] = [
    { label: "Power", rank: row.rank_power, value: signed(row.rating) },
    { label: "Résumé", rank: row.rank_resume },
    { label: "Offense", rank: row.off_rank, value: signed(row.off_rating) },
    { label: "Defense", rank: row.def_rank, value: signed(row.def_rating) },
  ]
  return (
    <section aria-labelledby="profile-heading" className="space-y-3">
      <h2 id="profile-heading" className="text-2xl font-semibold font-stretch-condensed">
        Profile
      </h2>
      <ul className="space-y-3">
        {rows.map((r) => (
          <li key={r.label} className="grid grid-cols-[4.5rem_1fr_9rem] items-center gap-3">
            <span className="text-sm text-muted-foreground">{r.label}</span>
            <span aria-hidden className="h-2.5 rounded-full bg-muted">
              {r.rank != null && (
                <span
                  className="block h-full rounded-full bg-primary"
                  style={{ width: `${(100 * (count - r.rank + 1)) / count}%` }}
                />
              )}
            </span>
            <span className="text-right text-sm tabular-nums">
              {r.rank != null ? (
                <>
                  <span className="font-semibold">#{r.rank}</span>
                  <span className="text-muted-foreground"> of {count}</span>
                </>
              ) : (
                "—"
              )}
              {r.value && <span className="ml-2 text-muted-foreground">({r.value})</span>}
            </span>
          </li>
        ))}
      </ul>
      <p className="text-xs text-muted-foreground">
        Ranks among the {count} rated FBS teams. Offense and defense are points per game better than
        an average FBS unit.
      </p>
    </section>
  )
}
