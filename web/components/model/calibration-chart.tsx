"use client"

import {
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts"

import type { CalibrationBin } from "@/lib/api/types"
import { useChartTheme } from "@/lib/chart-theme"
import { percent } from "@/lib/format/numbers"

const pct = (v: number) => `${Math.round(v * 100)}%`

/**
 * Reliability diagram: when TSI gave the favorite X% to win, how often did it win? Points
 * on the diagonal are perfectly calibrated; bigger dots stand for more games.
 */
export function CalibrationChart({ bins }: { bins: CalibrationBin[] }) {
  const theme = useChartTheme()
  return (
    <figure className="space-y-2">
      <figcaption className="text-sm text-muted-foreground">
        Favorite&apos;s predicted win chance vs. how often it actually won (validation 2023–25). The
        diagonal is perfect calibration.
      </figcaption>
      <div className="aspect-square max-h-80 w-full max-w-sm">
        {theme && (
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 10, right: 16, bottom: 20, left: 0 }}>
              <CartesianGrid stroke={theme.grid} strokeWidth={1} />
              <XAxis
                type="number"
                dataKey="predicted"
                domain={[0.5, 1]}
                ticks={[0.5, 0.6, 0.7, 0.8, 0.9, 1]}
                tickFormatter={pct}
                tick={{ fill: theme.muted, fontSize: 12 }}
                stroke={theme.grid}
                label={{
                  value: "Predicted",
                  position: "bottom",
                  offset: 2,
                  fill: theme.muted,
                  fontSize: 12,
                }}
              />
              <YAxis
                type="number"
                dataKey="observed"
                domain={[0.5, 1]}
                ticks={[0.5, 0.6, 0.7, 0.8, 0.9, 1]}
                tickFormatter={pct}
                tick={{ fill: theme.muted, fontSize: 12 }}
                stroke={theme.grid}
                width={44}
              />
              <ZAxis type="number" dataKey="games" range={[60, 260]} />
              <ReferenceLine
                segment={[
                  { x: 0.5, y: 0.5 },
                  { x: 1, y: 1 },
                ]}
                stroke={theme.muted}
                strokeDasharray="4 4"
              />
              <Scatter
                data={bins}
                fill={theme.accent}
                stroke={theme.surface}
                strokeWidth={2}
                isAnimationActive={false}
              />
              <Tooltip
                cursor={false}
                content={({ active, payload }) => {
                  const b = payload?.[0]?.payload as CalibrationBin | undefined
                  return active && b ? (
                    <div className="rounded-md border border-border bg-popover px-3 py-2 text-sm shadow-sm">
                      <p className="text-muted-foreground">
                        Favorite at {b.bin} ({b.games} games)
                      </p>
                      <p>
                        Predicted <span className="font-semibold">{percent(b.predicted)}</span>, won{" "}
                        <span className="font-semibold">{percent(b.observed)}</span>
                      </p>
                    </div>
                  ) : null
                }}
              />
            </ScatterChart>
          </ResponsiveContainer>
        )}
      </div>
    </figure>
  )
}
