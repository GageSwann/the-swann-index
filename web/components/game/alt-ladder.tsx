import type { FairMarkets, FairTwoWay, TeamRef } from "@/lib/api/types"
import { percent } from "@/lib/format/numbers"
import { american, teamSpread, totalLine } from "@/lib/format/odds"
import { cn } from "@/lib/utils"
import { HeadCell } from "@/components/ui/head-cell"

type Props = {
  markets: FairMarkets
  home: TeamRef
  marketSpread?: number | null // Vegas lines to highlight; none for hypothetical games
  marketTotal?: number | null
}

/** TSI's chance at every number around the line: spreads (home view) and totals. */
export function AltLadder({
  markets,
  home: homeTeam,
  marketSpread = null,
  marketTotal = null,
}: Props) {
  const home = homeTeam.abbreviation ?? homeTeam.school

  return (
    <section aria-labelledby="ladder-heading" className="space-y-3">
      <h2 id="ladder-heading" className="text-2xl font-semibold font-stretch-condensed">
        Alternate lines
      </h2>
      <div className="grid gap-4 md:grid-cols-2">
        <Ladder
          caption={`${homeTeam.school} spread`}
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
        Chance from TSI&apos;s score distribution, which puts extra weight on key numbers like 3 and
        7. On a whole-number line the chance (and fair price) is for games that don&apos;t land
        exactly on it; Push is how often one does
        {marketSpread !== null || marketTotal !== null
          ? ". The Vegas line is highlighted (nearest rung)."
          : "."}
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
  rungs: FairTwoWay[]
  label: (line: number) => string
  probLabel: string
  highlight: number | null
}) {
  const pushes = rungs.some((r) => r.push >= 0.005)
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
            {pushes && <HeadCell align="right">Push</HeadCell>}
            <HeadCell align="right">Fair</HeadCell>
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
              {pushes && (
                <td className="px-3 py-1.5 text-right text-muted-foreground">
                  {r.push >= 0.005 ? percent(r.push, 0) : "—"}
                </td>
              )}
              <td className="px-3 py-1.5 text-right">{american(r.first.fair)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
