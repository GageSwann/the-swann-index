"use client"

import dynamic from "next/dynamic"

// Charts load after the page paints (decision #87): Recharts and its dependencies are
// ~130 KB, and the charts render nothing on the server anyway (they wait for the theme).
// Each placeholder reserves the chart's height (caption + plot) so nothing below jumps.
// Import charts from here, not from their own modules.

function placeholder(className: string) {
  function ChartPlaceholder() {
    return <div aria-hidden className={className} />
  }
  return ChartPlaceholder
}

export const MarginChart = dynamic(
  () => import("@/components/game/margin-chart").then((m) => m.MarginChart),
  { ssr: false, loading: placeholder("h-[300px] sm:h-[284px]") },
)

export const RatingTrendChart = dynamic(
  () => import("@/components/charts/rating-trend-chart").then((m) => m.RatingTrendChart),
  { ssr: false, loading: placeholder("h-[276px] sm:h-[260px]") },
)
