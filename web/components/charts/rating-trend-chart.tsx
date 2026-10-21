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
import { axisStyle, type ChartTheme, useChartTheme } from "@/lib/chart-theme"
import { separation, teamColor } from "@/lib/format/color"
import { signed } from "@/lib/format/numbers"
import { formatMonthDay } from "@/lib/format/time"

import { ChartCaption, seriesTooltip } from "./chart-parts"

type TrendSeries = { team: TeamRef; history: RatingPoint[] }
type Row = { day: string } & Record<string, number | string>

const DASHES = [undefined, "6 4"]
const tooltip = seriesTooltip((v) => signed(v))

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
      const day = formatMonthDay(p.as_of)
      byDay.set(day, { ...(byDay.get(day) ?? { day }), [`s${i}`]: p.rating })
    }
  })
  const data = [...byDay.values()]
  if (data.length === 0) return null

  const ticks = ratingTicks(series.flatMap((s) => s.history.map((p) => p.rating)))
  const colors = theme && seriesColors(series, theme)

  return (
    <figure className="space-y-2">
      <ChartCaption
        legend={colors?.map((color, i) => ({
          label: series[i].team.school,
          color,
          dash: DASHES[i],
        }))}
      >
        TSI rating after each daily update (points vs. an average FBS team).
      </ChartCaption>
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
              <XAxis dataKey="day" {...axisStyle(theme)} />
              <YAxis
                width={44}
                {...axisStyle(theme)}
                tickFormatter={(v: number) => signed(v, 0)}
                domain={[ticks[0], ticks[ticks.length - 1]]}
                ticks={ticks}
              />
              {series.map((s, i) => (
                <Line
                  key={s.team.slug}
                  dataKey={`s${i}`}
                  name={s.team.school}
                  stroke={colors[i]}
                  strokeWidth={2}
                  strokeDasharray={DASHES[i]}
                  dot={data.length === 1}
                  activeDot={{ r: 4, stroke: theme.surface, strokeWidth: 2, fill: colors[i] }}
                  isAnimationActive={false}
                  connectNulls
                  label={endLabel(
                    data.length,
                    s.team.abbreviation ?? s.team.school,
                    theme,
                    colors[i],
                  )}
                />
              ))}
              <Tooltip cursor={{ stroke: theme.muted, strokeWidth: 1 }} content={tooltip} />
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
function ratingTicks(values: number[]): number[] {
  const lo = Math.min(...values) - 2
  const hi = Math.max(...values) + 2
  const step = hi - lo <= 10 ? 2 : hi - lo <= 25 ? 5 : 10
  const ticks: number[] = []
  for (let t = step * Math.floor(lo / step); t < hi + step; t += step) ticks.push(t)
  return ticks
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
