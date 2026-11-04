import { HeadCell } from "@/components/ui/head-cell"
import type { AdjustedScore, AdjustmentReport } from "@/lib/api/types"
import { describeAdjustment } from "@/lib/format/adjustments"
import { percent } from "@/lib/format/numbers"
import { cn } from "@/lib/utils"

const CELL = "px-3 py-2 text-right tabular-nums"

/**
 * Did the manual adjustments help (decision #105)? On every finished game whose official
 * prediction was adjusted, the raw model and the adjusted prediction are scored against
 * the result, overall and per adjustment. Lower error is better; the better one is bold.
 */
export function AdjustmentReportView({
  report,
  season,
}: {
  report: AdjustmentReport
  season: number
}) {
  const s = report.overall
  if (s.games === 0) {
    return (
      <p className="max-w-[70ch] text-sm text-muted-foreground">
        No finished {season} game has had a manually adjusted prediction yet. When one does, the raw
        model and the adjusted prediction are scored here side by side.
      </p>
    )
  }
  return (
    <div className="space-y-4">
      <div className="rounded-md border border-border">
        <table className="w-full text-sm">
          <thead className="bg-card text-muted-foreground">
            <tr className="border-b border-border">
              <HeadCell>
                <span className="sr-only">Prediction</span>
              </HeadCell>
              <HeadCell align="right" title="Average miss on the final margin, in points">
                Margin error
              </HeadCell>
              <HeadCell align="right" title="Average miss on the combined score, in points">
                Total error
              </HeadCell>
              <HeadCell align="right" title="Predicted winner won (straight up)">
                Winners
              </HeadCell>
            </tr>
          </thead>
          <tbody>
            <Row label="Raw model" s={s} side="raw" />
            <Row label="Adjusted" s={s} side="adjusted" />
          </tbody>
        </table>
      </div>
      <p className="max-w-[70ch] text-sm text-muted-foreground">
        {s.games} finished {s.games === 1 ? "game" : "games"} with an adjusted prediction in{" "}
        {season}. The adjustment moved the margin closer to the result in {s.helped}, further from
        it in {s.hurt}
        {s.same > 0 && `, and barely changed it in ${s.same}`}. Small samples: a single game can
        swing these numbers.
      </p>
      {report.adjustments.length > 0 && (
        <div className="rounded-md border border-border">
          <table className="w-full text-sm">
            <thead className="bg-card text-muted-foreground">
              <tr className="border-b border-border">
                <HeadCell>Adjustment</HeadCell>
                <HeadCell align="right">Games</HeadCell>
                <HeadCell align="right" title="Average margin miss: raw model, then adjusted">
                  Margin error
                </HeadCell>
              </tr>
            </thead>
            <tbody>
              {report.adjustments.map(({ adjustment, score }) => (
                <tr key={adjustment.id} className="border-b border-border last:border-0">
                  <th scope="row" className="px-3 py-2 text-left font-normal">
                    {describeAdjustment(adjustment)}
                  </th>
                  <td className={CELL}>{score.games}</td>
                  <td className={cn(CELL, "whitespace-nowrap")}>
                    {fixed(score.raw_mae)} → <Better s={score} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function Row({ label, s, side }: { label: string; s: AdjustedScore; side: "raw" | "adjusted" }) {
  const raw = side === "raw"
  const pick = (r: number | null, a: number | null) => (raw ? r : a)
  // Lower error wins; higher winner rate wins. Ties: neither is bold.
  const bold = (r: number | null, a: number | null, higher = false) =>
    r != null && a != null && r !== a && (raw ? higher === r > a : higher === a > r)
  return (
    <tr className="border-b border-border last:border-0">
      <th scope="row" className="px-3 py-2 text-left font-medium whitespace-nowrap">
        {label}
      </th>
      <td className={cn(CELL, bold(s.raw_mae, s.adjusted_mae) && "font-bold")}>
        {fixed(pick(s.raw_mae, s.adjusted_mae))}
      </td>
      <td className={cn(CELL, bold(s.raw_total_mae, s.adjusted_total_mae) && "font-bold")}>
        {fixed(pick(s.raw_total_mae, s.adjusted_total_mae))}
      </td>
      <td className={cn(CELL, bold(s.raw_su, s.adjusted_su, true) && "font-bold")}>
        {pct(pick(s.raw_su, s.adjusted_su))}
      </td>
    </tr>
  )
}

function Better({ s }: { s: AdjustedScore }) {
  const better = s.raw_mae != null && s.adjusted_mae != null && s.adjusted_mae < s.raw_mae
  return <span className={cn(better && "font-bold")}>{fixed(s.adjusted_mae)}</span>
}

function fixed(v: number | null): string {
  return v == null ? "—" : v.toFixed(2)
}

function pct(v: number | null): string {
  return v == null ? "—" : percent(v)
}
