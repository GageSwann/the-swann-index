"use client"

import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import type { TeamRef, TwoWay } from "@/lib/api/types"
import { useChartTheme } from "@/lib/chart-theme"
import { percent } from "@/lib/format/numbers"
import { teamSpread } from "@/lib/format/odds"

type Props = {
  home: TeamRef
  away: TeamRef
  margin: number // TSI mean home margin
  sigma: number // from the published snapshot
  marketSpread: number | null // home view (negative = home favored)
  ladder: TwoWay[] // API cover probabilities, used for the tooltip
}

/**
 * Where TSI expects the final margin to land: a normal curve with the snapshot's mean
 * and σ (drawing only; every probability shown comes from the API's ladder). Positive x
 * means the home team wins by that much.
 */
export function MarginChart({ home, away, margin, sigma, marketSpread, ladder }: Props) {
  const theme = useChartTheme()
  const lo = Math.floor(margin - 3 * sigma)
  const hi = Math.ceil(margin + 3 * sigma)
  // Whole-point margins, so hovering lands on real final margins and on ladder rungs.
  const data = Array.from({ length: hi - lo + 1 }, (_, i) => {
    const x = lo + i
    return { x, density: Math.exp(-0.5 * ((x - margin) / sigma) ** 2) }
  })
  // Ticks every 10 points, kept off the edges so end labels aren't clipped.
  const ticks: number[] = []
  for (let t = Math.ceil((lo + 4) / 10) * 10; t <= hi - 4; t += 10) ticks.push(t)
  const homeName = home.abbreviation ?? home.school
  const awayName = away.abbreviation ?? away.school

  return (
    <figure className="space-y-2">
      <figcaption className="text-sm text-muted-foreground">
        Likely final margins. Right of the &ldquo;Tie&rdquo; line {homeName} wins; left of it{" "}
        {awayName} wins. Hover for TSI&apos;s chance to cover each number.
      </figcaption>
      <div className="h-64 w-full">
        {theme && (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 22, right: 12, bottom: 4, left: 12 }}>
              <CartesianGrid vertical={false} stroke={theme.grid} strokeWidth={1} />
              <XAxis
                dataKey="x"
                type="number"
                domain={[lo, hi]}
                ticks={ticks}
                interval="equidistantPreserveStart"
                minTickGap={12}
                tick={{ fill: theme.muted, fontSize: 12 }}
                stroke={theme.grid}
                tickFormatter={(v: number) =>
                  v === 0 ? "0" : v > 0 ? `${homeName} +${v}` : `${awayName} +${-v}`
                }
              />
              <YAxis hide domain={[0, 1.08]} />
              <Area
                type="monotone"
                dataKey="density"
                stroke={theme.accent}
                strokeWidth={2}
                fill={theme.accent}
                fillOpacity={0.1}
                isAnimationActive={false}
                activeDot={{ r: 4, stroke: theme.surface, strokeWidth: 2, fill: theme.accent }}
              />
              <ReferenceLine
                x={0}
                stroke={theme.muted}
                strokeWidth={1}
                label={{ value: "Tie", position: "top", fill: theme.muted, fontSize: 12 }}
              />
              {marketSpread !== null && (
                <ReferenceLine
                  x={-marketSpread}
                  stroke={theme.text}
                  strokeWidth={1}
                  label={{ value: "Vegas", position: "top", fill: theme.text, fontSize: 12 }}
                />
              )}
              <Tooltip
                cursor={{ stroke: theme.muted, strokeWidth: 1 }}
                content={({ active, label }) =>
                  active && typeof label === "number" ? (
                    <MarginTip x={label} homeName={homeName} awayName={awayName} ladder={ladder} />
                  ) : null
                }
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </figure>
  )
}

function MarginTip({
  x,
  homeName,
  awayName,
  ladder,
}: {
  x: number
  homeName: string
  awayName: string
  ladder: TwoWay[]
}) {
  // Home covers spread s when margin > -s, so margin x lines up with the rung s = -x.
  const rung = ladder.find((r) => r.line === -x)
  const outcome = x === 0 ? "Tie" : x > 0 ? `${homeName} by ${x}` : `${awayName} by ${-x}`
  return (
    <div className="rounded-md border border-border bg-popover px-3 py-2 text-sm shadow-sm">
      <p className="text-muted-foreground">{outcome}</p>
      {rung && (
        <p>
          <span className="font-semibold">{percent(rung.first.prob, 0)}</span>{" "}
          <span className="text-muted-foreground">
            {homeName} covers {teamSpread(rung.line ?? 0)}
          </span>
        </p>
      )}
    </div>
  )
}
