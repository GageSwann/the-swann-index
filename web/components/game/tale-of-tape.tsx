import type { TeamProfile } from "@/lib/api/types"
import { record, signed } from "@/lib/format/numbers"
import { cn } from "@/lib/utils"

type Stat = {
  label: string
  value: (t: TeamProfile) => number | null | undefined
  show: (v: number, t: TeamProfile) => string
  better: "high" | "low"
}

const STATS: Stat[] = [
  { label: "Power rank", value: (t) => t.ratings?.rank_power, show: (v) => `#${v}`, better: "low" },
  {
    label: "Résumé rank",
    value: (t) => t.ratings?.rank_resume,
    show: (v) => `#${v}`,
    better: "low",
  },
  { label: "Rating", value: (t) => t.ratings?.rating, show: (v) => signed(v), better: "high" },
  { label: "Offense", value: (t) => t.ratings?.off_rating, show: (v) => signed(v), better: "high" },
  { label: "Defense", value: (t) => t.ratings?.def_rating, show: (v) => signed(v), better: "high" },
  {
    label: "Schedule strength",
    value: (t) => t.ratings?.sos,
    show: (v) => signed(v),
    better: "high",
  },
  {
    label: "Record",
    value: (t) => t.wins / Math.max(1, t.wins + t.losses + t.ties),
    show: (_, t) => record(t.wins, t.losses, t.ties),
    better: "high",
  },
]

/** Side-by-side season numbers (this season only); the better side of each row is bold. */
export function TaleOfTape({ home, away }: { home: TeamProfile; away: TeamProfile }) {
  return (
    <section aria-labelledby="tape-heading" className="space-y-3">
      <h2 id="tape-heading" className="text-2xl font-semibold font-stretch-condensed">
        Tale of the tape
      </h2>
      <div className="overflow-x-auto rounded-md border border-border">
        <table className="w-full text-sm">
          <thead className="bg-card">
            <tr className="border-b border-border">
              <th scope="col" className="w-2/5 px-3 py-2 text-left font-semibold">
                {away.team.school}
              </th>
              <th scope="col" className="px-3 py-2 text-center font-medium text-muted-foreground">
                <span className="sr-only">Stat</span>
              </th>
              <th scope="col" className="w-2/5 px-3 py-2 text-right font-semibold">
                {home.team.school}
              </th>
            </tr>
          </thead>
          <tbody>
            {STATS.map((s) => {
              const a = s.value(away)
              const h = s.value(home)
              const winner =
                a == null || h == null || a === h
                  ? null
                  : a > h === (s.better === "high")
                    ? "away"
                    : "home"
              return (
                <tr key={s.label} className="border-b border-border last:border-0">
                  <td className={cn("px-3 py-2", winner === "away" && "font-bold")}>
                    {a == null ? "—" : s.show(a, away)}
                  </td>
                  <th
                    scope="row"
                    className="px-3 py-2 text-center font-normal text-muted-foreground"
                  >
                    {s.label}
                  </th>
                  <td className={cn("px-3 py-2 text-right", winner === "home" && "font-bold")}>
                    {h == null ? "—" : s.show(h, home)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted-foreground">
        Ratings are points per game vs. an average FBS team, from this season&apos;s games only.
      </p>
    </section>
  )
}
