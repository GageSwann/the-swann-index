"use client"

import { ReferenceLine } from "recharts"

import { type LineSeries, LineSeriesChart } from "@/components/charts/line-series-chart"
import type { AccuracyRow } from "@/lib/api/types"

const SERIES: LineSeries[] = [
  { key: "predictive_mae", label: "TSI", tone: "accent" },
  { key: "vegas_mae", label: "Vegas", tone: "text", dash: "6 4" },
  { key: "elo_mae", label: "Elo", tone: "muted", dash: "2 3" },
]

/**
 * Prediction error by season for TSI, the closing line and Elo (lower is better). Train
 * seasons sit left of the line, validation right; the current season is partial.
 */
export function SeasonChart({
  rows,
  firstValidate,
}: {
  rows: AccuracyRow[]
  firstValidate: string
}) {
  const last = rows[rows.length - 1]?.label
  const values = rows.flatMap((r) => [r.predictive_mae, r.vegas_mae, r.elo_mae])
  const lo = Math.floor(Math.min(...values))
  const hi = Math.ceil(Math.max(...values))

  return (
    <div className="space-y-2">
      <LineSeriesChart
        caption="Average miss on the final margin, in points, by season."
        data={rows}
        xKey="label"
        series={SERIES}
        format={(v) => v.toFixed(2)}
        title={(label) => (label === last ? `${label} (so far)` : label)}
        margin={{ top: 22 }}
        xAxis={{
          tickFormatter: (v: string) => (v === last ? `${v}*` : v),
          interval: "preserveStartEnd",
          minTickGap: 8,
        }}
        yAxis={{
          width: 36,
          domain: [lo, hi],
          ticks: Array.from({ length: hi - lo + 1 }, (_, i) => lo + i),
        }}
        overlay={(theme) => (
          <ReferenceLine
            x={firstValidate}
            stroke={theme.muted}
            strokeWidth={1}
            label={{ value: "Validation →", position: "top", fill: theme.muted, fontSize: 12 }}
          />
        )}
      />
      <p className="text-xs text-muted-foreground">
        * {last} so far, simulated day by day with the same no-look-ahead rules.
      </p>
    </div>
  )
}
