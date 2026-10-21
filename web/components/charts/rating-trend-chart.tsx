"use client"

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import type { RatingPoint, TeamRef } from "@/lib/api/types"
import { type ChartTheme, useChartTheme } from "@/lib/chart-theme"
import { separation, teamColor } from "@/lib/format/color"
import { signed } from "@/lib/format/numbers"

export type TrendSeries = { team: TeamRef; history: RatingPoint[] }

type Row = { day: string } & Record<string, number | string>

const dateLabel = new Intl.DateTimeFormat("en-US", {
  timeZone: "America/New_York",
  month: "short",
  day: "numeric",
})

/**
 * TSI rating after each daily run for one or two teams. The first series is solid, the
 * second dashed (identity is never color alone); if the two team colors look alike, the
 * second falls back to neutral. The last run of each day stands for that day.
 */
export function RatingTrendChart({ series }: { series: TrendSeries[] }) {
  const theme = useChartTheme()
  const byDay = new Map<string, Row>()
  series.forEach((s, i) => {
    for (const p of s.history) {
      const day = dateLabel.format(new Date(p.as_of))
      byDay.set(day, { ...(byDay.get(day) ?? { day }), [`s${i}`]: p.rating })
    }
  })
  const data = [...byDay.values()]
  if (data.length === 0) return null

  const axis = ratingAxis(series.flatMap((s) => s.history.map((p) => p.rating)))
  const colors = theme && seriesColors(series, theme)
  const short = (t: TeamRef) => t.abbreviation ?? t.school

  return (
    <figure className="space-y-2">
      <figcaption className="flex flex-wrap items-center gap-x-5 gap-y-1 text-sm text-muted-foreground">
        <span>TSI rating after each daily update (points vs. an average FBS team).</span>
        {colors && series.length > 1 && (
          <span className="flex gap-4" aria-hidden>
            {series.map((s, i) => (
              <Key key={s.team.slug} color={colors[i]} dashed={i > 0} label={s.team.school} />
            ))}
          </span>
        )}
      </figcaption>
      {data.length === 1 && (
        <p className="text-sm text-muted-foreground">
          One daily update so far; the line fills in as the nightly runs add points.
        </p>
      )}
      <div className="h-56 w-full">
        {theme && colors && (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 10, right: 56, bottom: 4, left: 0 }}>
              <CartesianGrid vertical={false} stroke={theme.grid} strokeWidth={1} />
              <XAxis dataKey="day" tick={{ fill: theme.muted, fontSize: 12 }} stroke={theme.grid} />
              <YAxis
                width={44}
                tick={{ fill: theme.muted, fontSize: 12 }}
                stroke={theme.grid}
                tickFormatter={(v: number) => signed(v, 0)}
                domain={[axis.ticks[0], axis.ticks[axis.ticks.length - 1]]}
                ticks={axis.ticks}
              />
              {series.map((s, i) => (
                <Line
                  key={s.team.slug}
                  dataKey={`s${i}`}
                  name={s.team.school}
                  stroke={colors[i]}
                  strokeWidth={2}
                  strokeDasharray={i > 0 ? "6 4" : undefined}
                  dot={data.length === 1}
                  activeDot={{ r: 4, stroke: theme.surface, strokeWidth: 2, fill: colors[i] }}
                  isAnimationActive={false}
                  connectNulls
                  label={endLabel(data.length, short(s.team), theme, colors[i])}
                />
              ))}
              <Tooltip
                cursor={{ stroke: theme.muted, strokeWidth: 1 }}
                content={({ active, label, payload }) =>
                  active ? (
                    <div className="rounded-md border border-border bg-popover px-3 py-2 text-sm shadow-sm">
                      <p className="text-muted-foreground">{label}</p>
                      {payload?.map((row) => (
                        <p key={String(row.dataKey)} className="flex items-center gap-2">
                          <span
                            aria-hidden
                            className="inline-block h-0.5 w-3"
                            style={{ backgroundColor: String(row.color) }}
                          />
                          <span className="font-semibold">{signed(Number(row.value))}</span>
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

/**
 * Even y ticks (every 2, 5 or 10 points) with at least 2 points of padding, so
 * day-to-day noise doesn't fill the chart.
 */
function ratingAxis(values: number[]): { ticks: number[] } {
  const lo = Math.min(...values) - 2
  const hi = Math.max(...values) + 2
  const step = hi - lo <= 10 ? 2 : hi - lo <= 25 ? 5 : 10
  const ticks: number[] = []
  for (let t = step * Math.floor(lo / step); t < hi + step; t += step) ticks.push(t)
  return { ticks }
}

function seriesColors(series: TrendSeries[], theme: ChartTheme): string[] {
  const colors = series.map((s) => teamColor(s.team, theme.mode))
  if (colors.length > 1 && separation(colors[0], colors[1]) < 15) colors[1] = theme.muted
  return colors
}

/** Direct label at the last point: a dot plus the team's short name in text color. */
function endLabel(length: number, text: string, theme: ChartTheme, color: string) {
  function EndLabel(props: { x?: number | string; y?: number | string; index?: number }) {
    if (props.index !== length - 1) return null
    const x = Number(props.x)
    const y = Number(props.y)
    return (
      <g>
        <circle cx={x} cy={y} r={4} fill={color} stroke={theme.surface} strokeWidth={2} />
        <text x={x + 8} y={y + 4} fill={theme.text} fontSize={12}>
          {text}
        </text>
      </g>
    )
  }
  return EndLabel
}

function Key({ color, label, dashed = false }: { color: string; label: string; dashed?: boolean }) {
  return (
    <span className="flex items-center gap-1.5">
      <svg width="18" height="4" aria-hidden>
        <line
          x1="0"
          y1="2"
          x2="18"
          y2="2"
          stroke={color}
          strokeWidth="2"
          strokeDasharray={dashed ? "5 3" : undefined}
        />
      </svg>
      {label}
    </span>
  )
}
