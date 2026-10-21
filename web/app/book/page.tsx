import type { Metadata } from "next"

import { BookSummary } from "@/components/book/book-summary"
import { PickLedger } from "@/components/book/pick-ledger"
import { TierTable } from "@/components/book/tier-table"
import { UnitsChart } from "@/components/book/units-chart"
import { PageHeading } from "@/components/layout/page-heading"
import { getLedger, getMeta } from "@/lib/api/queries"

export const metadata: Metadata = { title: "TSI Book" }

export default async function BookPage() {
  const meta = await getMeta()
  const ledger = await getLedger(meta.season)
  const graded = ledger.picks.filter((p) => p.status === "graded").length
  const open = ledger.picks.length - graded

  return (
    <div className="space-y-10">
      <div>
        <PageHeading title="TSI Book">
          Paper picks where TSI&apos;s numbers disagree with the betting market, {meta.season}{" "}
          season. Every pick is published before kickoff, never edited, and graded against the final
          score.
        </PageHeading>
        <BookSummary records={ledger.records} open={open} />
      </div>

      {graded > 0 && (
        <>
          <section aria-labelledby="units-heading" className="space-y-3">
            <h2 id="units-heading" className="text-2xl font-semibold font-stretch-condensed">
              Units over time
            </h2>
            <UnitsChart points={ledger.cumulative} />
          </section>
          <section aria-labelledby="tier-heading" className="space-y-3">
            <h2 id="tier-heading" className="text-2xl font-semibold font-stretch-condensed">
              Record by market and tier
            </h2>
            <TierTable records={ledger.records} />
          </section>
        </>
      )}

      <section aria-labelledby="picks-heading" className="space-y-3">
        <h2 id="picks-heading" className="text-2xl font-semibold font-stretch-condensed">
          Picks
        </h2>
        {ledger.picks.length > 0 ? (
          <PickLedger picks={ledger.picks} />
        ) : (
          <p className="text-muted-foreground">
            No picks published yet this season. They appear here as soon as the nightly run finds an
            edge.
          </p>
        )}
      </section>

      <section aria-labelledby="how-heading" className="max-w-[70ch] space-y-3">
        <h2 id="how-heading" className="text-2xl font-semibold font-stretch-condensed">
          How the Book picks
        </h2>
        <ul className="list-disc space-y-2 pl-5 text-muted-foreground">
          <li>
            TSI prices every game, then compares its numbers with the median line across
            sportsbooks. Its view is shrunk toward the market first: on spreads TSI has shown no
            edge over closing lines, so spread picks are rare; on totals it has beaten opening
            lines.
          </li>
          <li>
            A pick needs at least 1.5 points of win-probability edge at the price (★), 3 for ★★ and
            5 for ★★★. Moneylines need 3, 5 and 8.
          </li>
          <li>
            Results use 1 unit per pick at the listed price (−110 when the market gives none). The ¼
            Kelly column sizes each stake by its edge on a 100-unit bankroll, capped at 3 units.
          </li>
          <li>
            Closing-line value (CLV) is how far the market moved toward TSI&apos;s side by kickoff.
            Steady positive CLV is the best sign the edges are real.
          </li>
          <li>
            &ldquo;Open&rdquo; picks can still change or disappear before kickoff; the last one
            published before kickoff is locked and graded.
          </li>
        </ul>
      </section>
    </div>
  )
}
