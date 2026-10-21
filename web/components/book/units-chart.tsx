"use client"

import { ReferenceLine } from "recharts"

import { type LineSeries, LineSeriesChart } from "@/components/charts/line-series-chart"
import type { UnitsPoint } from "@/lib/api/types"
import { units } from "@/lib/format/picks"
import { formatCalendarDate } from "@/lib/format/time"

const SERIES: LineSeries[] = [
  { key: "units", label: "1u flat", tone: "accent" },
  { key: "kelly_units", label: "¼ Kelly", tone: "muted", dash: "6 4" },
]

/**
 * Running profit after each game day: flat stakes (solid amber) and ¼ Kelly (dashed).
 * Within one season the axis shows days; across seasons, one tick per year.
 */
export function UnitsChart({ points }: { points: UnitsPoint[] }) {
  if (points.length < 2) {
    return (
      <p className="text-sm text-muted-foreground">
        The running total appears once picks from two game days are graded.
      </p>
    )
  }
  const data = points.map((p) => ({ ...p, day: formatCalendarDate(p.date) }))
  const year = (i: number) => data[i].date.slice(0, 4)
  const yearTicks =
    year(0) === year(data.length - 1)
      ? null
      : data.filter((_, i) => i === 0 || year(i) !== year(i - 1)).map((d) => d.day)

  return (
    <LineSeriesChart
      caption="Units won to date (1 unit = one standard bet)."
      data={data}
      xKey="day"
      series={SERIES}
      format={units}
      title={(label) => `Through ${label}`}
      xAxis={{
        ticks: yearTicks ?? undefined,
        tickFormatter: (v: string) => (yearTicks ? v.slice(-4) : v.replace(/, \d{4}$/, "")),
      }}
      yAxis={{ width: 52, tickFormatter: (v: number) => units(v), allowDecimals: false }}
      overlay={(theme) => <ReferenceLine y={0} stroke={theme.muted} strokeWidth={1} />}
    />
  )
}
