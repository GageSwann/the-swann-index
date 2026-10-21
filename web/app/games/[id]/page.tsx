import type { Metadata } from "next"
import { notFound } from "next/navigation"
import { Suspense } from "react"

import { AltLadder } from "@/components/game/alt-ladder"
import { GameHeader } from "@/components/game/game-header"
import { MarginChart } from "@/components/game/margin-chart"
import { OddsBoard } from "@/components/game/odds-board"
import { PredictionHistory } from "@/components/game/prediction-history"
import { RatingTrendChart } from "@/components/game/rating-trend-chart"
import { TaleOfTape } from "@/components/game/tale-of-tape"
import { PickBadge } from "@/components/board/pick-badge"
import { PageHeading } from "@/components/layout/page-heading"
import { getGame, getMeta, getTeam, getWeekGames } from "@/lib/api/queries"

type Props = PageProps<"/games/[id]">

/** Prerender this week's games; any other game renders on first visit and is cached. */
export async function generateStaticParams() {
  const meta = await getMeta()
  const board = await getWeekGames(meta.season, Math.max(1, meta.week))
  return board.games.map((g) => ({ id: String(g.id) }))
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const center = await getGame(Number((await params).id)).catch(() => null)
  if (!center) return { title: "Game" }
  const g = center.game
  return { title: `${g.away.school} ${g.neutral ? "vs" : "at"} ${g.home.school}` }
}

export default function GamePage(props: Props) {
  return (
    <Suspense fallback={<PageHeading title="Game center">Loading the game.</PageHeading>}>
      <GameCenterView {...props} />
    </Suspense>
  )
}

async function GameCenterView({ params }: Props) {
  const id = Number((await params).id)
  if (!Number.isInteger(id)) notFound()
  const center = await getGame(id)
  if (!center) notFound()
  const { game } = center
  const [home, away] = await Promise.all([
    getTeam(game.home.slug, game.season).catch(() => null),
    getTeam(game.away.slug, game.season).catch(() => null),
  ])
  const p = game.prediction

  return (
    <div className="space-y-10">
      <h1 className="sr-only">
        {game.away.school} {game.neutral ? "vs" : "at"} {game.home.school}
      </h1>
      <GameHeader game={game} home={home} away={away} />
      {p && p.picks.length > 0 && (
        <div className="space-y-2">
          {p.picks.map((pick) => (
            <PickBadge key={`${pick.market}-${pick.side}`} pick={pick} game={game} />
          ))}
        </div>
      )}
      {p && center.markets ? (
        <>
          <OddsBoard center={center} />
          <section aria-labelledby="margin-heading" className="space-y-3">
            <h2 id="margin-heading" className="text-2xl font-semibold font-stretch-condensed">
              Margin distribution
            </h2>
            <MarginChart
              home={game.home}
              away={game.away}
              margin={p.proj_home - p.proj_away}
              sigma={p.sigma_margin}
              marketSpread={game.market?.spread ?? null}
              ladder={center.markets.alt_spreads}
            />
          </section>
          <AltLadder center={center} />
        </>
      ) : (
        <p className="text-muted-foreground">
          {game.result
            ? "TSI didn't publish a prediction for this game (predictions began Oct 20, 2026)."
            : "TSI hasn't published a prediction for this game yet. It appears after the next daily run once the game is within eight days."}
        </p>
      )}
      {home && away && (
        <>
          <TaleOfTape home={home} away={away} />
          <section aria-labelledby="trend-heading" className="space-y-3">
            <h2 id="trend-heading" className="text-2xl font-semibold font-stretch-condensed">
              Rating trends
            </h2>
            <RatingTrendChart
              home={{ team: game.home, history: home.history }}
              away={{ team: game.away, history: away.history }}
            />
          </section>
        </>
      )}
      <PredictionHistory game={game} history={center.history} />
    </div>
  )
}
