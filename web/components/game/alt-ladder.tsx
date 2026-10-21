import type { GameCenter, TwoWay } from "@/lib/api/types"
import { percent } from "@/lib/format/numbers"
import { american, teamSpread, totalLine } from "@/lib/format/odds"
import { cn } from "@/lib/utils"
import { HeadCell } from "@/components/ui/head-cell"

/** TSI's chance at every number around the line: spreads (home view) and totals. */
export function AltLadder({ center }: { center: GameCenter }) {
  const { game, markets } = center
  if (!markets) return null
  const home = game.home.abbreviation ?? game.home.school
  const marketSpread = game.market?.spread ?? null
  const marketTotal = game.market?.total ?? null

  return (
    <section aria-labelledby="ladder-heading" className="space-y-3">
      <h2 id="ladder-heading" className="text-2xl font-semibold font-stretch-condensed">
        Alternate lines
      </h2>
      <div className="grid gap-4 md:grid-cols-2">
        <Ladder
          caption={`${game.home.school} spread`}
          rungs={markets.alt_spreads}
          label={(line) => `${home} ${teamSpread(line)}`}
          probLabel="Covers"
          highlight={marketSpread}
        />
        <Ladder
          caption="Game total"
          rungs={markets.alt_totals}
          label={(line) => `Over ${totalLine(line)}`}
          probLabel="Over"
          highlight={marketTotal}
        />
      </div>
      <p className="text-xs text-muted-foreground">
        Chance from TSI&apos;s score distribution; the Vegas line is highlighted (nearest rung).
      </p>
    </section>
  )
}

function Ladder({
  caption,
  rungs,
  label,
  probLabel,
  highlight,
}: {
  caption: string
  rungs: TwoWay[]
  label: (line: number) => string
  probLabel: string
  highlight: number | null
}) {
  const nearest =
    highlight === null
      ? null
      : rungs.reduce((best, r) =>
          Math.abs((r.line ?? 0) - highlight) < Math.abs((best.line ?? 0) - highlight) ? r : best,
        ).line
  return (
    <div className="max-h-[420px] overflow-auto rounded-md border border-border">
      <table className="w-full text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead className="sticky top-0 bg-card text-muted-foreground">
          <tr className="border-b border-border">
            <HeadCell>{caption}</HeadCell>
            <HeadCell align="right">{probLabel}</HeadCell>
            <HeadCell align="right">Fair</HeadCell>
            <HeadCell align="right">TSI Book</HeadCell>
          </tr>
        </thead>
        <tbody>
          {rungs.map((r) => (
            <tr
              key={r.line}
              className={cn(
                "border-b border-border last:border-0",
                r.line === nearest && "bg-primary/15 font-medium",
              )}
            >
              <th scope="row" className="px-3 py-1.5 text-left font-normal">
                {label(r.line ?? 0)}
                {r.line === nearest && <span className="ml-2 text-xs text-primary">Vegas</span>}
              </th>
              <td className="px-3 py-1.5 text-right">{percent(r.first.prob, 0)}</td>
              <td className="px-3 py-1.5 text-right">{american(r.first.fair)}</td>
              <td className="px-3 py-1.5 text-right">{american(r.first.book)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
