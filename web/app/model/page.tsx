import type { Metadata } from "next"
import type { ReactNode } from "react"

import { PageHeading } from "@/components/layout/page-heading"
import { AccuracyTable } from "@/components/model/accuracy-table"
import { BookBacktest } from "@/components/model/book-backtest"
import { CalibrationChart } from "@/components/charts/lazy"
import { MarketChecks } from "@/components/model/market-checks"
import { Methodology } from "@/components/model/methodology"
import { SeasonChart } from "@/components/charts/lazy"
import { VersionHistory } from "@/components/model/version-history"
import { getModelReport } from "@/lib/api/queries"
import { percent } from "@/lib/format/numbers"
import { formatUpdated } from "@/lib/format/time"
import { pageMeta } from "@/lib/metadata"

export const metadata: Metadata = pageMeta({
  title: "Model",
  description:
    "How TSI rates teams and predicts games, and how accurate it has been against the closing line and Elo, with calibration and the Book replayed.",
})

export default async function ModelPage() {
  const report = await getModelReport()
  const backtest = report.backtest
  const tables = backtest?.report
  const validate = tables?.periods.find((p) => p.label.startsWith("Validate 20"))
  const firstValidate = validate?.label.match(/\d{4}/)?.[0] ?? "2023"

  return (
    <div className="space-y-12">
      <div>
        <PageHeading title="How good is TSI?">
          Every number below is out of sample: each game was predicted using only what was known
          before kickoff, then checked against the final score and the closing betting line.
        </PageHeading>
        {validate && (
          <section
            aria-label="Validation headline"
            className="rounded-md border border-border bg-card p-5"
          >
            <dl className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-4">
              <Stat label="TSI miss per game" value={`${validate.predictive_mae.toFixed(2)} pts`} />
              <Stat label="Vegas closing line" value={`${validate.vegas_mae.toFixed(2)} pts`} />
              <Stat label="Elo baseline" value={`${validate.elo_mae.toFixed(2)} pts`} />
              <Stat label="Winners picked" value={percent(validate.predictive_su)} />
            </dl>
            <p className="mt-4 text-sm text-muted-foreground">
              {validate.label}, {validate.games.toLocaleString()} FBS games. The closing line is the
              bar to clear; TSI is within half a point of it and well ahead of Elo.
            </p>
          </section>
        )}
      </div>

      {tables ? (
        <>
          <Section id="accuracy" title="Report card">
            <AccuracyTable rows={tables.periods} live={report.live} />
            {report.live.games === 0 && (
              <p className="text-sm text-muted-foreground">
                Live scoring of {report.season}&apos;s published predictions starts once the first
                predicted games are final.
              </p>
            )}
            <SeasonChart rows={tables.by_season} firstValidate={firstValidate} />
          </Section>

          <Section id="calibration" title="Are the probabilities honest?">
            <div className="grid items-start gap-8 md:grid-cols-[minmax(0,24rem)_1fr]">
              <CalibrationChart bins={tables.calibration} />
              <MarketChecks ats={tables.ats} totals={tables.totals} />
            </div>
          </Section>

          <Section id="book" title="The Book, replayed">
            <BookBacktest rows={tables.book} points={tables.book_units} />
          </Section>
        </>
      ) : (
        <p className="text-muted-foreground">
          The backtest report isn&apos;t available yet. It appears after the next saved backtest
          run.
        </p>
      )}

      <Methodology />

      <Section id="versions" title="Model versions">
        <VersionHistory versions={report.versions} />
        {backtest && (
          <p className="text-xs text-muted-foreground">
            Latest backtest {formatUpdated(backtest.run_at)}
            {backtest.git_sha && ` from commit ${backtest.git_sha}`}. Each version is tuned on
            2015–22 and judged on 2023–25 only.
          </p>
        )}
      </Section>
    </div>
  )
}

function Section({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <section aria-labelledby={`${id}-heading`} className="space-y-4">
      <h2 id={`${id}-heading`} className="text-2xl font-semibold font-stretch-condensed">
        {title}
      </h2>
      {children}
    </section>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="text-3xl font-bold font-stretch-condensed">{value}</dd>
    </div>
  )
}
