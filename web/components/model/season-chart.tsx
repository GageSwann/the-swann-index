"use client"

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import type { AccuracyRow } from "@/lib/api/types"
import { type ChartTheme, useChartTheme } from "@/lib/chart-theme"

const SERIES = [
  { key: "predictive_mae", label: "TSI", dash: undefined },
  { key: "vegas_mae", label: "Vegas", dash: "6 4" },
  { key: "elo_mae", label: "Elo", dash: "2 3" },
] as const

const color = (key: string, t: ChartTheme) =>
  key === "predictive_mae" ? t.accent : key === "vegas_mae" ? t.text : t.muted

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
  const theme = useChartTheme()
  const last = rows[rows.length - 1]?.label
  const values = rows.flatMap((r) => [r.predictive_mae, r.vegas_mae, r.elo_mae])
  const lo = Math.floor(Math.min(...values))
  const hi = Math.ceil(Math.max(...values))
  const ticks = Array.from({ length: hi - lo + 1 }, (_, i) => lo + i)

  return (
    <figure className="space-y-2">
      <figcaption className="flex flex-wrap items-center gap-x-5 gap-y-1 text-sm text-muted-foreground">
        <span>Average miss on the final margin, in points, by season.</span>
        {theme && (
          <span className="flex gap-4" aria-hidden>
            {SERIES.map((s) => (
              <span key={s.key} className="flex items-center gap-1.5">
                <svg width="18" height="4">
                  <line
                    x1="0"
                    y1="2"
                    x2="18"
                    y2="2"
                    stroke={color(s.key, theme)}
                    strokeWidth="2"
                    strokeDasharray={s.dash}
                  />
                </svg>
                {s.label}
              </span>
            ))}
          </span>
        )}
      </figcaption>
      <div className="h-64 w-full">
        {theme && (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={rows} margin={{ top: 22, right: 16, bottom: 4, left: 0 }}>
              <CartesianGrid vertical={false} stroke={theme.grid} strokeWidth={1} />
              <XAxis
                dataKey="label"
                tick={{ fill: theme.muted, fontSize: 12 }}
                stroke={theme.grid}
                tickFormatter={(v: string) => (v === last ? `${v}*` : v)}
                interval="preserveStartEnd"
                minTickGap={8}
              />
              <YAxis
                width={36}
                tick={{ fill: theme.muted, fontSize: 12 }}
                stroke={theme.grid}
                domain={[lo, hi]}
                ticks={ticks}
              />
              <ReferenceLine
                x={firstValidate}
                stroke={theme.muted}
                strokeWidth={1}
                label={{ value: "Validation →", position: "top", fill: theme.muted, fontSize: 12 }}
              />
              {SERIES.map((s) => (
                <Line
                  key={s.key}
                  dataKey={s.key}
                  name={s.label}
                  stroke={color(s.key, theme)}
                  strokeWidth={2}
                  strokeDasharray={s.dash}
                  dot={false}
                  activeDot={{
                    r: 4,
                    stroke: theme.surface,
                    strokeWidth: 2,
                    fill: color(s.key, theme),
                  }}
                  isAnimationActive={false}
                />
              ))}
              <Tooltip
                cursor={{ stroke: theme.muted, strokeWidth: 1 }}
                content={({ active, label, payload }) =>
                  active ? (
                    <div className="rounded-md border border-border bg-popover px-3 py-2 text-sm shadow-sm">
                      <p className="text-muted-foreground">
                        {label}
                        {label === last && " (so far)"}
                      </p>
                      {payload?.map((row) => (
                        <p key={String(row.dataKey)}>
                          <span className="font-semibold">{Number(row.value).toFixed(2)}</span>{" "}
                          <span className="text-muted-foreground">{row.name}</span>
                        </p>
                      ))}
                    </div>
                  ) : null
                }
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
      <p className="text-xs text-muted-foreground">
        * {last} so far, simulated day by day with the same no-look-ahead rules.
      </p>
    </figure>
  )
}
