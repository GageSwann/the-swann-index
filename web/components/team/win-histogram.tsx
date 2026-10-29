import { chance } from "@/lib/format/numbers"

const SHOWN = 0.0005 // win totals less likely than this are left off the ends
const LABELED = 0.03 // bars at least this likely carry their percentage

/**
 * The distribution of final win totals as plain HTML bars (server-rendered, no chart
 * library): one bar per total, height proportional to its chance, the likeliest
 * labeled. A visually hidden table carries the same numbers for screen readers.
 */
export function WinHistogram({ dist, school }: { dist: number[]; school: string }) {
  const totals = dist.map((p, wins) => ({ wins, p })).filter(({ p }) => p >= SHOWN)
  if (totals.length === 0) return null
  const lo = totals[0].wins
  const hi = totals[totals.length - 1].wins
  const shown = dist.slice(lo, hi + 1).map((p, i) => ({ wins: lo + i, p }))
  const top = Math.max(...shown.map(({ p }) => p))

  return (
    <figure className="space-y-2">
      <figcaption className="text-sm text-muted-foreground">
        Chance of each final win total, from 10,000 simulated seasons.
      </figcaption>
      <div aria-hidden className="flex h-44 items-end gap-0.5 border-b border-border">
        {shown.map(({ wins, p }) => (
          <div
            key={wins}
            className="flex h-full flex-1 flex-col items-center justify-end gap-1"
            title={`${wins} wins: ${chance(p)}`}
          >
            {p >= LABELED && (
              <span className="text-xs text-muted-foreground tabular-nums">{chance(p)}</span>
            )}
            <div
              className="w-full max-w-12 rounded-t-sm bg-primary"
              style={{ height: `${(p / top) * 80}%` }}
            />
          </div>
        ))}
      </div>
      <div aria-hidden className="flex gap-0.5">
        {shown.map(({ wins }) => (
          <span key={wins} className="flex-1 text-center text-xs text-muted-foreground">
            {wins}
          </span>
        ))}
      </div>
      <p aria-hidden className="text-center text-xs text-muted-foreground">
        Final wins
      </p>
      <table className="sr-only">
        <caption>{school}: chance of each final win total</caption>
        <thead>
          <tr>
            <th scope="col">Wins</th>
            <th scope="col">Chance</th>
          </tr>
        </thead>
        <tbody>
          {shown.map(({ wins, p }) => (
            <tr key={wins}>
              <td>{wins}</td>
              <td>{chance(p)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  )
}
