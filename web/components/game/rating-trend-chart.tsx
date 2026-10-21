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

type Series = { team: TeamRef; history: RatingPoint[] }

const dateLabel = new Intl.DateTimeFormat("en-US", {
  timeZone: "America/New_York",
  month: "short",
  day: "numeric",
})

/**
 * Both teams' TSI rating after each daily run. Home is solid, away dashed (identity is
 * never color alone); if the two team colors look alike, away falls back to neutral.
 */
export function RatingTrendChart({ home, away }: { home: Series; away: Series }) {
  const theme = useChartTheme()
  const byDay = new Map<string, { day: string; home?: number; away?: number }>()
  for (const [key, s] of [
    ["home", home],
    ["away", away],
  ] as const) {
    for (const p of s.history) {
      const day = dateLabel.format(new Date(p.as_of))
      byDay.set(day, { ...(byDay.get(day) ?? { day }), [key]: p.rating })
    }
  }
  const data = [...byDay.values()]
  if (data.length === 0) return null

  const colors = theme && seriesColors(home.team, away.team, theme)
  const name = (t: TeamRef) => t.abbreviation ?? t.school

  return (
    <figure className="space-y-2">
      <figcaption className="flex flex-wrap items-center gap-x-5 gap-y-1 text-sm text-muted-foreground">
        <span>TSI rating after each daily update (points vs. an average FBS team).</span>
        {colors && (
          <span className="flex gap-4" aria-hidden>
            <Key color={colors.away} dashed label={away.team.school} />
            <Key color={colors.home} label={home.team.school} />
          </span>
        )}
      </figcaption>
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
                domain={["auto", "auto"]}
              />
              {(["away", "home"] as const).map((key) => (
                <Line
                  key={key}
                  dataKey={key}
                  name={key === "home" ? home.team.school : away.team.school}
                  stroke={colors[key]}
                  strokeWidth={2}
                  strokeDasharray={key === "away" ? "6 4" : undefined}
                  dot={false}
                  activeDot={{ r: 4, stroke: theme.surface, strokeWidth: 2, fill: colors[key] }}
                  isAnimationActive={false}
                  connectNulls
                  label={endLabel(
                    data.length,
                    key === "home" ? name(home.team) : name(away.team),
                    theme,
                    colors[key],
                  )}
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

function seriesColors(home: TeamRef, away: TeamRef, theme: ChartTheme) {
  const h = teamColor(home, theme.mode)
  const a = teamColor(away, theme.mode)
  return { home: h, away: separation(h, a) < 15 ? theme.muted : a }
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
