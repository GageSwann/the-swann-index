import type { ReactNode } from "react"
import type { TooltipContentProps } from "recharts"

/** One legend entry: a short line in the series' color and dash pattern. */
export type LegendItem = { label: string; color: string; dash?: string }

/**
 * A chart's caption: what it shows, then a legend whenever there are two or more series
 * (identity is never color alone: dashes differ too).
 */
export function ChartCaption({ children, legend }: { children: ReactNode; legend?: LegendItem[] }) {
  return (
    <figcaption className="flex flex-wrap items-center gap-x-5 gap-y-1 text-sm text-muted-foreground">
      <span>{children}</span>
      {legend && legend.length > 1 && (
        <span className="flex gap-4" aria-hidden>
          {legend.map((item) => (
            <span key={item.label} className="flex items-center gap-1.5">
              <svg width="18" height="4">
                <line
                  x1="0"
                  y1="2"
                  x2="18"
                  y2="2"
                  stroke={item.color}
                  strokeWidth="2"
                  strokeDasharray={item.dash}
                />
              </svg>
              {item.label}
            </span>
          ))}
        </span>
      )}
    </figcaption>
  )
}

/** The popover every chart tooltip uses. */
export function TooltipBox({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-md border border-border bg-popover px-3 py-2 text-sm shadow-sm">
      {children}
    </div>
  )
}

/**
 * Tooltip content for line charts: a title, then one row per series with a color swatch,
 * the formatted value and the series name.
 */
export function seriesTooltip(
  format: (value: number) => string,
  title: (label: string) => ReactNode = (label) => label,
) {
  function SeriesTooltip({ active, label, payload }: TooltipContentProps) {
    if (!active) return null
    return (
      <TooltipBox>
        <p className="text-muted-foreground">{title(String(label))}</p>
        {payload?.map((row) => (
          <p key={String(row.dataKey)} className="flex items-center gap-2">
            <span
              aria-hidden
              className="inline-block h-0.5 w-3"
              style={{ backgroundColor: String(row.color) }}
            />
            <span className="font-semibold">{format(Number(row.value))}</span>
            <span className="text-muted-foreground">{row.name}</span>
          </p>
        ))}
      </TooltipBox>
    )
  }
  return SeriesTooltip
}
