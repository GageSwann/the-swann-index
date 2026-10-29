import { getGame } from "@/lib/api/queries"
import { formatDay } from "@/lib/format/time"
import { OG_SIZE, ogImage, ogMessage } from "@/lib/og/frame"
import { TwoTeamCard } from "@/lib/og/two-team-card"

export const alt = "TSI's projected score and win probability for this game"
export const size = OG_SIZE
export const contentType = "image/png"

/** Game link preview: the final score once it's over, else TSI's projection. */
export default async function Image({ params }: { params: Promise<{ id: string }> }) {
  const center = await getGame(Number((await params).id)).catch(() => null)
  if (!center) return ogMessage("Game not found")
  const { game } = center
  const p = game.prediction
  const final = game.result?.final === true
  const day = game.kickoff ? formatDay(game.kickoff) : "Date TBA"
  const context = final
    ? `Final | ${day}${p ? ` | TSI had ${game.home.abbreviation ?? game.home.school} ${Math.round(p.proj_home)}-${Math.round(p.proj_away)}` : ""}`
    : `${day} | TSI projection`

  return ogImage(
    <TwoTeamCard
      context={context}
      away={game.away}
      home={game.home}
      awayScore={final ? game.result?.away_points : p?.proj_away}
      homeScore={final ? game.result?.home_points : p?.proj_home}
      neutral={game.neutral}
      homeWinProb={final ? null : p?.home_win_prob}
    />,
  )
}
