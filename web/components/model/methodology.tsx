import type { ReactNode } from "react"

/** Plain-English method (docs 04 and 05), with the few formulas that define it. */
export function Methodology() {
  return (
    <section aria-labelledby="method-heading" className="max-w-[70ch] space-y-6">
      <h2 id="method-heading" className="text-2xl font-semibold font-stretch-condensed">
        How TSI works
      </h2>
      <Step title="1. Rate every offense and defense">
        <p>
          Each game becomes two lines of numbers: points per drive and success rate for each
          offense, with garbage time removed. A ridge regression then solves for every team&apos;s
          offense and defense at once, so 30 points against a great defense counts for more than 30
          against a weak one. Home field is worth about 3.2 points.
        </p>
        <Formula>rating = 0.726 × points-per-drive margin + 0.635 × success-rate margin</Formula>
        <p>
          This season-only rating drives the Power rankings: no preseason polls, no reputation.
          Teams with fewer than four games are marked provisional.
        </p>
      </Step>
      <Step title="2. Rank résumés separately">
        <p>
          Résumé asks how hard it would be for a typical #12 team to match a team&apos;s record
          against its schedule, using each opponent&apos;s current rating. It rewards wins, not
          margins, and changes as opponents&apos; seasons play out.
        </p>
      </Step>
      <Step title="3. Predict each game">
        <p>
          Predictions use a second, &ldquo;predictive&rdquo; rating that also knows the past: a
          preseason prior (last season, returning production, recruiting) and an Elo rating. A
          stacked regression, fit separately for each stage of the season, learns how much to trust
          each input. The prior carries the early weeks and fades to a small weight by midseason.
        </p>
        <Formula>
          margin = β₁·site + β₂·PPD gap + β₃·success gap + β₄·prior gap + β₅·Elo gap
        </Formula>
        <p>
          Game totals come from a similar stack built on pace, tempo and efficiency. Scores are
          (total ± margin) ÷ 2.
        </p>
      </Step>
      <Step title="4. Turn a forecast into odds">
        <p>
          Final margins land around the prediction with a spread of about 15 points (a normal curve,
          σ ≈ 15.4; totals σ ≈ 16.4, a little wider for high-scoring games). Every win probability,
          cover chance and fair price on the site comes from that curve.
        </p>
        <Formula>P(home wins) = Φ(predicted margin ÷ 15.4)</Formula>
      </Step>
      <Step title="5. Bet only where the edge survives">
        <p>
          The TSI Book doesn&apos;t take TSI&apos;s number at face value. It shrinks each
          disagreement toward the market by a trust factor k learned from opening lines: about 0.07
          for spreads (almost no trust) and 0.32 for totals.
        </p>
        <Formula>P(over) = Φ(k × (TSI total − line) ÷ σ)</Formula>
        <p>
          A pick needs 1.5 points of probability edge or more at the price. Market lines are never
          model inputs; they only size the edges.
        </p>
      </Step>
      <Step title="No look-ahead">
        <p>
          Every rating, prediction and backtest uses only games played before kickoff. Backtests
          replay each season day by day, the way the nightly run works, and published predictions
          are never edited.
        </p>
      </Step>
    </section>
  )
}

function Step({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">{title}</h3>
      <div className="space-y-2 text-muted-foreground">{children}</div>
    </div>
  )
}

function Formula({ children }: { children: ReactNode }) {
  return <p className="border-l-2 border-primary py-1 pl-3 text-foreground italic">{children}</p>
}
