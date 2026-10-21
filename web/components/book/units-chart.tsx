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

import type { UnitsPoint } from "@/lib/api/types"
import { useChartTheme } from "@/lib/chart-theme"
import { units } from "@/lib/format/picks"

const dayLabel = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  timeZone: "UTC",
})

const SERIES = [
  { key: "units", label: "1u flat", dashed: false },
  { key: "kelly_units", label: "¼ Kelly", dashed: true },
] as const

/** Running profit after each game day: flat stakes (solid amber) and ¼ Kelly (dashed). */
export function UnitsChart({ points }: { points: UnitsPoint[] }) {
  const theme = useChartTheme()
  if (points.length < 2) {
    return (
      <p className="text-sm text-muted-foreground">
        The running total appears once picks from two game days are graded.
      </p>
    )
  }
  const data = points.map((p) => ({ ...p, day: dayLabel.format(new Date(p.date)) }))
  const color = (dashed: boolean) => (theme ? (dashed ? theme.muted : theme.accent) : "")

  return (
    <figure className="space-y-2">
      <figcaption className="flex flex-wrap items-center gap-x-5 gap-y-1 text-sm text-muted-foreground">
        <span>Units won to date (1 unit = one standard bet).</span>
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
                    stroke={color(s.dashed)}
                    strokeWidth="2"
                    strokeDasharray={s.dashed ? "5 3" : undefined}
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
            <LineChart data={data} margin={{ top: 10, right: 16, bottom: 4, left: 0 }}>
              <CartesianGrid vertical={false} stroke={theme.grid} strokeWidth={1} />
              <XAxis dataKey="day" tick={{ fill: theme.muted, fontSize: 12 }} stroke={theme.grid} />
              <YAxis
                width={52}
                tick={{ fill: theme.muted, fontSize: 12 }}
                stroke={theme.grid}
                tickFormatter={(v: number) => units(v)}
                allowDecimals={false}
              />
              <ReferenceLine y={0} stroke={theme.muted} strokeWidth={1} />
              {SERIES.map((s) => (
                <Line
                  key={s.key}
                  dataKey={s.key}
                  name={s.label}
                  stroke={color(s.dashed)}
                  strokeWidth={2}
                  strokeDasharray={s.dashed ? "6 4" : undefined}
                  dot={false}
                  activeDot={{ r: 4, stroke: theme.surface, strokeWidth: 2, fill: color(s.dashed) }}
                  isAnimationActive={false}
                />
              ))}
              <Tooltip
                cursor={{ stroke: theme.muted, strokeWidth: 1 }}
                content={({ active, label, payload }) =>
                  active ? (
                    <div className="rounded-md border border-border bg-popover px-3 py-2 text-sm shadow-sm">
                      <p className="text-muted-foreground">Through {label}</p>
                      {payload?.map((row) => (
                        <p key={String(row.dataKey)}>
                          <span className="font-semibold">{units(Number(row.value))}</span>{" "}
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
    </figure>
  )
}
