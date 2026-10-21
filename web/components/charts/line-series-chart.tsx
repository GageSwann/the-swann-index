"use client"

import type { ReactNode } from "react"
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  type XAxisProps,
  YAxis,
  type YAxisProps,
} from "recharts"

import { axisStyle, type ChartTheme, useChartTheme } from "@/lib/chart-theme"

import { ChartCaption, seriesTooltip } from "./chart-parts"

/** A series: a data key, its legend label, a theme tone and an optional dash pattern. */
export type LineSeries = {
  key: string
  label: string
  tone: "accent" | "text" | "muted"
  dash?: string
}

type Props = {
  caption: ReactNode
  data: object[]
  xKey: string
  series: LineSeries[]
  format: (value: number) => string // tooltip values
  title?: (label: string) => ReactNode // tooltip heading
  xAxis?: Partial<XAxisProps>
  yAxis?: Partial<YAxisProps>
  overlay?: (theme: ChartTheme) => ReactNode // reference lines etc.
  className?: string // chart height
  margin?: { top?: number; right?: number; bottom?: number; left?: number }
}

/**
 * Several series over one x-axis with the site's chart styling: recessive grid and axes,
 * 2 px lines in theme tones, a legend in the caption and a crosshair tooltip.
 */
export function LineSeriesChart(props: Props) {
  const theme = useChartTheme()
  const { series, format, title } = props
  const color = (s: LineSeries) => (theme ? theme[s.tone] : "")

  return (
    <figure className="space-y-2">
      <ChartCaption
        legend={theme ? series.map((s) => ({ label: s.label, color: color(s), dash: s.dash })) : []}
      >
        {props.caption}
      </ChartCaption>
      <div className={props.className ?? "h-64 w-full"}>
        {theme && (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={props.data}
              margin={{ top: 10, right: 16, bottom: 4, left: 0, ...props.margin }}
            >
              <CartesianGrid vertical={false} stroke={theme.grid} strokeWidth={1} />
              <XAxis dataKey={props.xKey} {...axisStyle(theme)} {...props.xAxis} />
              <YAxis width={44} {...axisStyle(theme)} {...props.yAxis} />
              {props.overlay?.(theme)}
              {series.map((s) => (
                <Line
                  key={s.key}
                  dataKey={s.key}
                  name={s.label}
                  stroke={color(s)}
                  strokeWidth={2}
                  strokeDasharray={s.dash}
                  dot={false}
                  activeDot={{ r: 4, stroke: theme.surface, strokeWidth: 2, fill: color(s) }}
                  isAnimationActive={false}
                />
              ))}
              <Tooltip
                cursor={{ stroke: theme.muted, strokeWidth: 1 }}
                content={seriesTooltip(format, title)}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </figure>
  )
}
